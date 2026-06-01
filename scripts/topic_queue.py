#!/usr/bin/env python3
"""
Topic Queue Manager with State Machine

States:
- pending: Ready to be processed
- in_progress: Currently being processed
- completed: Successfully processed
- failed: Failed processing (will be retried)

Usage:
    from topic_queue import reserve_topics, mark_completed, mark_failed

    topics = reserve_topics(count=3)
    for topic in topics:
        try:
            # Process topic...
            mark_completed(topic['id'])
        except Exception as e:
            mark_failed(topic['id'], str(e))
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))
from utils.validation import (
    validate_keyword,
    validate_category,
    validate_language,
    validate_priority,
    validate_status,
    validate_topic_data
)


# Tokens that appear in many keywords but don't define the topic. Used to skip
# them when computing topic-noun overlap between two keywords.
_TOPIC_NOUN_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "for", "to", "of", "in", "on", "at",
    "by", "from", "with", "into", "vs", "vs.", "versus", "is", "are", "was",
    "the", "this", "that", "how", "what", "why", "when", "where", "which",
    "do", "does", "did", "best", "top", "new", "guide", "tutorial", "review",
    "complete", "real", "actual", "actually", "worth", "use", "using", "used",
    "via", "without", "with", "single", "solo", "developer", "developers",
    "user", "users", "free", "tier", "pro", "plan", "plans", "open", "source",
    "self", "hosted", "hosting", "local", "remote", "first", "second", "third",
    "before", "after", "vs", "versus", "between", "compared", "comparison",
    "test", "tests", "testing", "tested", "month", "year", "week", "day",
    "hour", "minute", "second", "2024", "2025", "2026", "2027",
    # Generic tech adjectives — not specific topics
    "api", "apis", "app", "apps", "tool", "tools", "cli", "ide", "cloud",
    "data", "code", "build", "builds", "run", "runs", "log", "logs",
    "size", "speed", "cost", "costs", "price", "prices", "memory", "cpu",
    "disk", "network", "latency", "performance", "benchmark", "experiment",
    "production", "development", "prod", "dev",
    # Generic verbs and prepositions that survived the basic filter
    "not", "fix", "fixing", "fixed", "solve", "solving", "solved", "issue",
    "issues", "problem", "problems", "working", "broken", "error", "errors",
    "running", "starting", "stopping", "installing", "installed", "setup",
    "configure", "configured", "config", "configuration",
    # Korean stopwords (very small set — we deliberately keep tech nouns)
    "그", "이", "저", "는", "은", "이", "가", "을", "를", "에", "의",
    "비교", "후기", "실제", "실전", "방법", "사용", "사용법", "개발자",
})


def _extract_topic_nouns(keyword: str) -> set:
    """Pull the meaningful tokens out of a keyword for overlap comparison.

    Lowercased, alphanumerics + CJK only, stopwords removed, very short tokens
    (1-2 chars) dropped. Returns a set so overlap is set-intersection.
    """
    s = keyword.lower()
    s = "".join(c if (c.isalnum() or c.isspace() or ord(c) > 127) else " " for c in s)
    tokens = {t for t in s.split() if len(t) > 2 and t not in _TOPIC_NOUN_STOPWORDS}
    return tokens


def _collect_recent_noun_sets(topics: list, days: int = 7) -> list:
    """Return the noun-set of every topic completed within the last `days`.

    Used to enforce "don't ship another weaviate post within 7 days of the
    last one." Pulls from `completed_at` (preferred) or `reserved_at`.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out = []
    for t in topics:
        if t.get('status') != 'completed':
            continue
        ts_str = t.get('completed_at') or t.get('reserved_at')
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            continue
        if ts < cutoff:
            continue
        out.append(_extract_topic_nouns(t['keyword']))
    return out


def _find_overlapping_set(candidate: set, others: list, min_overlap: int = 1):
    """Return the intersection set if `candidate` shares a meaningful noun
    with any set in `others`. None if no overlap reaches the threshold.

    Strategy: even a single shared noun like 'weaviate' or 'claude' is enough
    to block, because once we've stripped generic stopwords (api, ide, tool,
    benchmark, etc.) what's left is almost always a proper-noun product name
    or a specific technical concept. The 5/30 incident was two weaviate posts
    on the same day even though their other words differed — that's exactly
    what min_overlap=1 (post-stopword) catches.

    False positives are still possible (e.g., two posts that both mention
    "docker" but on unrelated topics). Acceptable trade-off because each
    workflow run reserves 4x count topics, so a blocked topic just defers
    to a later run.
    """
    if not candidate:
        return None
    for other in others:
        intersection = candidate & other
        if len(intersection) >= min_overlap:
            return intersection
    return None


class TopicQueue:
    def __init__(self, queue_file: str = "data/topics_queue.json"):
        self.queue_file = Path(queue_file)
        self._ensure_queue_file()

    def _ensure_queue_file(self):
        """Create queue file if it doesn't exist"""
        if not self.queue_file.exists():
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_queue({"topics": []})

    def _load_queue(self) -> Dict:
        """Load queue from file"""
        with open(self.queue_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_queue(self, data: Dict):
        """Save queue to file"""
        with open(self.queue_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def reserve_topics(self, count: int = 3, priority_min: int = 1) -> List[Dict]:
        """
        Reserve topics by moving them from pending to in_progress.

        Prevents two kinds of duplication:
        1. Exact keyword+lang already completed (existing behavior).
        2. Topic-overlap with anything published in the last 7 days, in either
           language. This is new: previously the queue could ship two "weaviate"
           posts on the same day because their keywords differed in wording
           but the core noun set was identical, and Google flagged the cluster
           as low-value duplication.
        """
        data = self._load_queue()

        # Get completed keywords to prevent exact duplicates (existing)
        completed_keywords = {
            (t['keyword'].lower(), t.get('lang', t.get('language', 'en'))): t['id']
            for t in data['topics']
            if t['status'] == 'completed'
        }

        # Collect core nouns from topics completed in the last 7 days (any lang).
        # We compare against this set during reservation, AND incrementally
        # against topics we reserve in this same batch, so a single 10-post
        # run can't ship two weaviate posts either.
        recent_noun_sets = _collect_recent_noun_sets(data['topics'], days=7)

        # Find available topics sorted by priority (high to low) and created_at
        # Note: Only 'pending' status is used (unified from 'available' on 2026-01-25)
        available = [
            t for t in data['topics']
            if t['status'] == 'pending' and t.get('priority', 5) >= priority_min
        ]
        available.sort(key=lambda x: (-x.get('priority', 5), x.get('created_at', '')))

        reserved = []
        reserved_noun_sets = []
        now = datetime.now(timezone.utc).isoformat()

        # We look at up to 4x count to give the dedup filter room to work
        for topic in available[:count * 4]:
            topic_lang = topic.get('lang', topic.get('language', 'en'))
            topic_key = (topic['keyword'].lower(), topic_lang)
            if topic_key in completed_keywords:
                print(f"⚠️  Skipping duplicate keyword: {topic['keyword']} ({topic_lang}) — already completed as {completed_keywords[topic_key]}")
                continue

            # Topic-overlap dedup (the new check)
            nouns = _extract_topic_nouns(topic['keyword'])
            overlap_with = _find_overlapping_set(nouns, recent_noun_sets + reserved_noun_sets, min_overlap=1)
            if overlap_with is not None:
                print(f"⚠️  Skipping topic-overlap: {topic['keyword']} — shares {overlap_with} with recent/batch")
                continue

            errors = validate_topic_data(topic)
            if errors:
                print(f"⚠️  Skipping invalid topic {topic.get('id', 'unknown')}: {errors}")
                continue

            topic['status'] = 'in_progress'
            topic['reserved_at'] = now
            topic['retry_count'] = topic.get('retry_count', 0)
            reserved.append(topic)
            reserved_noun_sets.append(nouns)

            if len(reserved) >= count:
                break

        self._save_queue(data)
        return reserved

    def mark_completed(self, topic_id: str):
        """Mark a topic as completed"""
        data = self._load_queue()

        for topic in data['topics']:
            if topic['id'] == topic_id:
                topic['status'] = 'completed'
                topic['completed_at'] = datetime.now(timezone.utc).isoformat()
                break

        self._save_queue(data)

    def mark_failed(self, topic_id: str, error_message: str = ""):
        """
        Mark a topic as failed and move back to pending for retry

        Args:
            topic_id: Topic ID
            error_message: Error description
        """
        data = self._load_queue()

        for topic in data['topics']:
            if topic['id'] == topic_id:
                topic['status'] = 'pending'  # Rollback to pending
                topic['retry_count'] = topic.get('retry_count', 0) + 1
                topic['last_error'] = error_message
                topic['last_failed_at'] = datetime.now(timezone.utc).isoformat()

                # Remove reservation timestamp
                topic.pop('reserved_at', None)
                break

        self._save_queue(data)

    def cleanup_stuck_topics(self, hours: int = 24):
        """
        Reset topics stuck in in_progress state for too long

        Args:
            hours: Number of hours before considering a topic stuck
        """
        data = self._load_queue()
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(hours=hours)

        for topic in data['topics']:
            if topic['status'] == 'in_progress':
                reserved_at_str = topic.get('reserved_at', '')
                if reserved_at_str:
                    reserved_at = datetime.fromisoformat(reserved_at_str)
                    if reserved_at < threshold:
                        topic['status'] = 'pending'
                        topic['retry_count'] = topic.get('retry_count', 0) + 1
                        topic['last_error'] = f"Stuck in progress for {hours}+ hours"
                        topic.pop('reserved_at', None)

        self._save_queue(data)

    def add_topic(self, keyword: str, category: str, lang: str,
                  priority: int = 5, metadata: Optional[Dict] = None):
        """
        Add a new topic to the queue

        Args:
            keyword: Topic keyword/title
            category: Category (tech) - tech-only strategy
            lang: Language code (en/ko)
            priority: Priority 1-10 (higher = more important)
            metadata: Additional metadata dict

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        error = validate_keyword(keyword)
        if error:
            raise ValueError(f"Invalid keyword: {error}")

        error = validate_category(category)
        if error:
            raise ValueError(error)

        error = validate_language(lang)
        if error:
            raise ValueError(error)

        error = validate_priority(priority)
        if error:
            raise ValueError(error)

        data = self._load_queue()

        # Generate ID
        topic_id = f"{len(data['topics']) + 1:03d}-{lang}-{category}-{keyword[:20].replace(' ', '-').lower()}"

        topic = {
            "id": topic_id,
            "keyword": keyword,
            "category": category,
            "lang": lang,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "retry_count": 0
        }

        if metadata:
            topic.update(metadata)

        # Final validation of complete topic
        errors = validate_topic_data(topic)
        if errors:
            raise ValueError(f"Topic validation failed: {', '.join(errors)}")

        data['topics'].append(topic)
        self._save_queue(data)
        return topic_id

    def get_stats(self) -> Dict:
        """Get queue statistics"""
        data = self._load_queue()
        stats = {
            "total": len(data['topics']),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "by_category": {"tech": 0},
            "by_language": {"en": 0, "ko": 0}
        }

        for topic in data['topics']:
            status = topic.get('status', 'pending')
            stats[status] = stats.get(status, 0) + 1

            category = topic.get('category', 'tech')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

            lang = topic.get('lang', 'en')
            stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1

        return stats


# Global instance
_queue = None

def get_queue() -> TopicQueue:
    """Get or create global queue instance"""
    global _queue
    if _queue is None:
        _queue = TopicQueue()
    return _queue


# Convenience functions
def reserve_topics(count: int = 3, priority_min: int = 1) -> List[Dict]:
    """Reserve topics for processing"""
    return get_queue().reserve_topics(count, priority_min)


def mark_completed(topic_id: str):
    """Mark topic as completed"""
    get_queue().mark_completed(topic_id)


def mark_failed(topic_id: str, error_message: str = ""):
    """Mark topic as failed"""
    get_queue().mark_failed(topic_id, error_message)


def cleanup_stuck_topics(hours: int = 24):
    """Clean up stuck topics"""
    get_queue().cleanup_stuck_topics(hours)


def add_topic(keyword: str, category: str, lang: str,
              priority: int = 5, metadata: Optional[Dict] = None) -> str:
    """Add new topic to queue"""
    return get_queue().add_topic(keyword, category, lang, priority, metadata)


def get_stats() -> Dict:
    """Get queue statistics"""
    return get_queue().get_stats()


if __name__ == "__main__":
    # CLI interface
    import sys

    if len(sys.argv) < 2:
        print("Usage: python topic_queue.py [stats|cleanup|reserve]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "stats":
        stats = get_stats()
        print(json.dumps(stats, indent=2))

    elif command == "cleanup":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        cleanup_stuck_topics(hours)
        print(f"Cleaned up topics stuck for {hours}+ hours")

    elif command == "reserve":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        topics = reserve_topics(count)
        print(json.dumps(topics, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
