#!/usr/bin/env python3
"""
Content Type Classifier

Automatically classifies topics into Tutorial, Analysis, or News
based on keywords and patterns.

Usage:
    from scripts.utils.content_classifier import ContentClassifier

    classifier = ContentClassifier()
    content_type = classifier.classify(topic, keywords, category)
    config = classifier.get_config(content_type)
"""

from typing import Dict, List, Tuple


class ContentClassifier:
    """Classifies content into Tutorial, Analysis, or News types"""

    # Tutorial indicators (15% of content)
    TUTORIAL_INDICATORS = [
        'how to', 'guide', 'tutorial', 'step by step', 'walkthrough',
        'implementation', 'setup', 'install', 'configure', 'deployment',
        'complete guide', 'getting started', 'quick start',
        '가이드', '튜토리얼', '설치', '구성', '배포', '완전 가이드', '완벽 가이드',
    ]

    # Complex tech topics that warrant tutorials
    COMPLEX_TECH = [
        'kubernetes', 'docker', 'terraform', 'ansible', 'jenkins',
        'aws', 'azure', 'gcp', 'cloud', 'microservices', 'architecture',
        'rag', 'fine-tuning', 'fine tuning', 'mlops', 'ml ops',
        'devops', 'ci/cd', 'cicd', 'deployment', 'infrastructure',
        'database', 'postgresql', 'mongodb', 'redis', 'elasticsearch'
    ]

    # News indicators (25% of content)
    NEWS_INDICATORS = [
        'announces', 'announced', 'launching', 'released', 'unveils', 'introduces',
        'acquires', 'acquired', 'acquisition', 'funding round', 'investment',
        'raises $', 'raised $', 'breaking news', 'just released', 'now available',
        'confirmed', 'confirms', 'revealed', 'reveals',
        '발표했다', '출시했다', '공개했다', '인수했다', '투자 유치', '펀딩',
    ]

    # Comparison indicators — head-to-head matchups (was getting buried in 'analysis')
    COMPARISON_INDICATORS = [
        ' vs ', ' vs. ', ' versus ', 'compared to', 'comparison',
        'difference between', 'or which', 'which is better',
        'pros and cons', 'side by side', 'head to head',
        ' 비교', '차이', '어느 게', '어떤 게', '뭐가 나은', '뭐가 더',
    ]

    # Troubleshoot indicators — "something broke, how do I fix it"
    TROUBLESHOOT_INDICATORS = [
        'not working', 'doesn\'t work', 'fails', 'failing', 'error', 'errors',
        'broken', 'crash', 'crashes', 'crashing', 'won\'t start', 'stuck',
        'fix', 'solve', 'resolve', 'debugging', 'troubleshoot',
        '안 됨', '안돼', '안 돼', '실패', '에러', '오류', '고장', '해결', '안 돌아',
    ]

    # Content type configurations
    CONTENT_TYPE_CONFIG = {
        'tutorial': {
            'word_count': {
                'en': (1200, 1800),
                'ko': (1200, 1800),
            },
            'prompt_template': 'tutorial',
            'priority': 1.5,
            'requires': [
                'code_examples',
                'comparison_table',
                'step_guide',
                'best_practices'
            ],
            'description': 'In-depth tutorial with code, tables, and step-by-step guide'
        },
        'analysis': {
            'word_count': {
                'en': (900, 1400),
                'ko': (900, 1400),
            },
            'prompt_template': 'analysis',
            'priority': 1.0,
            'requires': [
                'comparison_list',
                'insights',
                'context'
            ],
            'description': 'Standard analysis with structured sections and comparison'
        },
        'news': {
            'word_count': {
                'en': (800, 1200),
                'ko': (800, 1200),
            },
            'prompt_template': 'news',
            'priority': 0.8,
            'requires': [
                'facts',
                'context',
                'impact'
            ],
            'description': 'Concise news article with key facts and context'
        },
        'comparison': {
            'word_count': {
                'en': (1000, 1400),
                'ko': (1000, 1400),
            },
            'prompt_template': 'comparison',
            'priority': 1.2,
            'requires': [
                'comparison_table',
                'verdict',
                'failure_modes',
            ],
            'description': 'Head-to-head comparison with verdict-first structure and matrix'
        },
        'troubleshoot': {
            'word_count': {
                'en': (900, 1300),
                'ko': (900, 1300),
            },
            'prompt_template': 'troubleshoot',
            'priority': 1.3,
            'requires': [
                'symptom',
                'quick_fix',
                'verification_steps',
                'prevention',
            ],
            'description': 'Diagnostic article with symptom → likely causes → fixes'
        },
    }

    def classify(self, topic: str, keywords: List[str], category: str) -> str:
        """
        Classify content type based on topic, keywords, and category.

        Returns one of: 'tutorial', 'analysis', 'news', 'comparison', 'troubleshoot'.

        Why two extra types: previously ~90% of generated posts ended up as
        'analysis' regardless of intent, so the site looked uniform to crawlers.
        Most posts that scored as 'analysis' were actually head-to-head matchups
        (X vs Y) or fix-this-broken-thing pieces; routing them to dedicated
        templates yields visibly different article structures (verdict-first
        tables for comparison, symptom-first quick-fix blocks for troubleshoot),
        which is a stronger signal for both readers and Google.
        """
        topic_lower = topic.lower()
        keywords_str = ' '.join(keywords).lower()

        # Tutorial classification only for tech (tech-only strategy)
        allow_tutorial = category == 'tech'

        tutorial_score = 0
        for indicator in self.TUTORIAL_INDICATORS:
            if indicator in topic_lower:
                if indicator in ['guide', 'tutorial', 'how to', 'step by step', 'walkthrough', '가이드']:
                    tutorial_score += 3
                else:
                    tutorial_score += 1
        if any(tech in keywords_str for tech in self.COMPLEX_TECH):
            tutorial_score += 1

        news_score = 0
        for indicator in self.NEWS_INDICATORS:
            if indicator in topic_lower:
                if indicator in ['announces', 'announced', 'launching', 'launched', 'released', 'acquires', 'acquired', 'raises $', 'raised $', 'confirms', '발표했다', '출시했다']:
                    news_score += 3
                elif indicator in ['unveils', 'introduces', 'reveals']:
                    news_score += 2
                else:
                    news_score += 1

        comparison_score = 0
        for indicator in self.COMPARISON_INDICATORS:
            if indicator in topic_lower:
                # " vs " is the strongest comparison signal
                if indicator in [' vs ', ' vs. ', ' versus ', '비교']:
                    comparison_score += 3
                else:
                    comparison_score += 1

        troubleshoot_score = 0
        for indicator in self.TROUBLESHOOT_INDICATORS:
            if indicator in topic_lower:
                if indicator in ['not working', 'doesn\'t work', 'error', 'fix', '안 됨', '에러', '해결']:
                    troubleshoot_score += 3
                else:
                    troubleshoot_score += 1

        # Decision precedence: strongest signal wins.
        # News is most time-sensitive, so it takes priority when tied.
        scores = {
            'news': news_score,
            'troubleshoot': troubleshoot_score,
            'comparison': comparison_score,
            'tutorial': tutorial_score if allow_tutorial else 0,
        }
        best_type, best_score = max(scores.items(), key=lambda kv: kv[1])

        if best_score >= 3:
            return best_type

        # Weak signals: news with a year word still counts as news
        if news_score >= 1 and any(year in topic_lower for year in ['2024', '2025', '2026', 'latest', 'new']):
            return 'news'

        # Weak comparison signal still routes to comparison if there's any "vs"-like word
        if comparison_score >= 1:
            return 'comparison'

        # Default to Analysis
        return 'analysis'

    def get_config(self, content_type: str, language: str = 'en') -> Dict:
        """
        Get configuration for a specific content type.

        Args:
            content_type: 'tutorial' | 'analysis' | 'news'
            language: 'en' | 'ko'

        Returns:
            Configuration dictionary with word_count, prompt_template, etc.
        """
        if content_type not in self.CONTENT_TYPE_CONFIG:
            raise ValueError(f"Invalid content type: {content_type}")

        config = self.CONTENT_TYPE_CONFIG[content_type].copy()

        # Get language-specific word count
        if language in config['word_count']:
            config['word_count'] = config['word_count'][language]
        else:
            config['word_count'] = config['word_count']['en']  # Default to English

        return config

    def get_distribution(self) -> Dict[str, float]:
        """Target distribution across the 5 content types."""
        return {
            'tutorial': 0.10,
            'analysis': 0.40,
            'news': 0.20,
            'comparison': 0.15,
            'troubleshoot': 0.15,
        }

    def get_target_counts(self, total_posts: int) -> Dict[str, int]:
        """Calculate target counts for each content type."""
        distribution = self.get_distribution()
        return {
            content_type: round(total_posts * pct)
            for content_type, pct in distribution.items()
        }

    def should_generate_type(
        self,
        content_type: str,
        current_counts: Dict[str, int],
        total_posts: int
    ) -> bool:
        """
        Check if we should generate more content of this type.

        Args:
            content_type: Type to check
            current_counts: Current counts for each type
            total_posts: Total posts planned

        Returns:
            True if we should generate this type
        """
        targets = self.get_target_counts(total_posts)
        current = current_counts.get(content_type, 0)
        target = targets.get(content_type, 0)

        return current < target


def main():
    """Test the classifier"""
    classifier = ContentClassifier()

    # Test cases
    test_cases = [
        {
            'topic': 'How to Deploy Kubernetes Cluster on AWS',
            'keywords': ['kubernetes', 'aws', 'deployment'],
            'category': 'tech',
            'expected': 'tutorial'
        },
        {
            'topic': 'OpenAI Announces GPT-5 Release',
            'keywords': ['openai', 'gpt-5', 'announcement'],
            'category': 'tech',
            'expected': 'news'
        },
        {
            'topic': 'RAG vs Fine-tuning: Which Approach is Better?',
            'keywords': ['rag', 'fine-tuning', 'comparison'],
            'category': 'tech',
            'expected': 'analysis'
        },
        {
            'topic': '2026 AI Trends and Predictions',
            'keywords': ['ai', 'trends', 'predictions'],
            'category': 'tech',
            'expected': 'analysis'
        },
        {
            'topic': 'Complete Guide to Next.js 15',
            'keywords': ['nextjs', 'guide', 'tutorial'],
            'category': 'tech',
            'expected': 'tutorial'
        }
    ]

    print("Testing Content Classifier\n")
    print("=" * 80)

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        result = classifier.classify(
            test['topic'],
            test['keywords'],
            test['category']
        )

        status = "✅ PASS" if result == test['expected'] else "❌ FAIL"

        if result == test['expected']:
            passed += 1
        else:
            failed += 1

        print(f"\nTest {i}: {status}")
        print(f"Topic: {test['topic']}")
        print(f"Expected: {test['expected']}")
        print(f"Got: {result}")

        if result == test['expected']:
            config = classifier.get_config(result)
            print(f"Word count: {config['word_count']}")
            print(f"Requires: {', '.join(config['requires'])}")

    print("\n" + "=" * 80)
    print(f"\nResults: {passed} passed, {failed} failed")
    print(f"Accuracy: {passed}/{passed+failed} ({passed/(passed+failed)*100:.1f}%)")

    # Test distribution
    print("\n" + "=" * 80)
    print("\nTarget Distribution (42 posts/week):")
    targets = classifier.get_target_counts(42)
    for content_type, count in targets.items():
        pct = count / 42 * 100
        print(f"  {content_type.capitalize()}: {count} posts ({pct:.0f}%)")


if __name__ == '__main__':
    main()
