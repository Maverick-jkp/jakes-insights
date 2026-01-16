#!/usr/bin/env python3
"""
Test script for topic queue system

Tests:
1. Reserve topics (pending → in_progress)
2. Mark completed (in_progress → completed)
3. Mark failed (in_progress → pending with retry count)
4. Stats display
5. Cleanup stuck topics
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from topic_queue import (
    reserve_topics,
    mark_completed,
    mark_failed,
    get_stats,
    cleanup_stuck_topics
)


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_reserve_and_complete():
    """Test: Reserve topics and mark as completed"""
    print_section("Test 1: Reserve and Complete")

    # Show initial stats
    print("Initial stats:")
    stats = get_stats()
    print(f"  Pending: {stats['pending']}")
    print(f"  In Progress: {stats['in_progress']}")
    print(f"  Completed: {stats['completed']}")

    # Reserve 3 topics
    print("\nReserving 3 topics...")
    topics = reserve_topics(count=3)

    for i, topic in enumerate(topics, 1):
        print(f"\n{i}. {topic['id']}")
        print(f"   Keyword: {topic['keyword']}")
        print(f"   Category: {topic['category']}")
        print(f"   Language: {topic['lang']}")
        print(f"   Status: {topic['status']}")

    # Mark first 2 as completed
    print("\n\nMarking first 2 as completed...")
    for topic in topics[:2]:
        mark_completed(topic['id'])
        print(f"  ✓ {topic['id']}")

    # Show updated stats
    print("\nUpdated stats:")
    stats = get_stats()
    print(f"  Pending: {stats['pending']}")
    print(f"  In Progress: {stats['in_progress']}")
    print(f"  Completed: {stats['completed']}")


def test_failure_and_retry():
    """Test: Mark topic as failed (should go back to pending)"""
    print_section("Test 2: Failure and Retry")

    # Reserve 1 topic
    print("Reserving 1 topic...")
    topics = reserve_topics(count=1)
    topic = topics[0]

    print(f"\nReserved: {topic['id']}")
    print(f"Status: {topic['status']}")
    print(f"Retry count: {topic['retry_count']}")

    # Mark as failed
    print("\nMarking as failed...")
    mark_failed(topic['id'], "Simulated API error")

    # Try to reserve again (should get the same topic back)
    print("\nReserving again (should get failed topic back)...")
    topics = reserve_topics(count=1)
    retry_topic = topics[0]

    print(f"\nReserved: {retry_topic['id']}")
    print(f"Status: {retry_topic['status']}")
    print(f"Retry count: {retry_topic['retry_count']}")
    print(f"Last error: {retry_topic.get('last_error', 'N/A')}")


def test_priority_ordering():
    """Test: Topics are reserved by priority"""
    print_section("Test 3: Priority Ordering")

    print("Reserving 5 topics (should be ordered by priority)...")
    topics = reserve_topics(count=5)

    for i, topic in enumerate(topics, 1):
        print(f"{i}. [{topic['priority']}] {topic['id']} - {topic['keyword']}")


def test_stats():
    """Test: Display comprehensive stats"""
    print_section("Test 4: Queue Statistics")

    stats = get_stats()

    print(f"Total topics: {stats['total']}\n")

    print("By Status:")
    print(f"  Pending: {stats['pending']}")
    print(f"  In Progress: {stats['in_progress']}")
    print(f"  Completed: {stats['completed']}")

    print("\nBy Category:")
    for category, count in stats['by_category'].items():
        print(f"  {category.capitalize()}: {count}")

    print("\nBy Language:")
    for lang, count in stats['by_language'].items():
        print(f"  {lang.upper()}: {count}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("  TOPIC QUEUE SYSTEM - TEST SUITE")
    print("="*60)

    try:
        test_reserve_and_complete()
        test_failure_and_retry()
        test_priority_ordering()
        test_stats()

        print("\n" + "="*60)
        print("  ✓ ALL TESTS COMPLETED")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
