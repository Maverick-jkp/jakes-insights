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
        'ガイド', 'チュートリアル', 'インストール', '設定', '完全ガイド'
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
        'announces', 'launches', 'releases', 'unveils', 'introduces',
        'acquires', 'acquisition', 'funding', 'investment', 'raises',
        'breaking', 'update', 'news', 'just released', 'now available',
        '발표', '출시', '공개', '인수', '투자', '펀딩', '업데이트',
        '発表', 'リリース', '公開', '買収', '投資', 'アップデート'
    ]

    # Content type configurations
    CONTENT_TYPE_CONFIG = {
        'tutorial': {
            'word_count': {
                'en': (2500, 3500),
                'ko': (2500, 3500),
                'ja': (7500, 10500)  # Japanese requires more characters
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
                'en': (1500, 2000),
                'ko': (1500, 2000),
                'ja': (4500, 6000)
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
                'ja': (2400, 3600)
            },
            'prompt_template': 'news',
            'priority': 0.8,
            'requires': [
                'facts',
                'context',
                'impact'
            ],
            'description': 'Concise news article with key facts and context'
        }
    }

    def classify(self, topic: str, keywords: List[str], category: str) -> str:
        """
        Classify content type based on topic, keywords, and category.

        Args:
            topic: The topic/title of the content
            keywords: List of keywords
            category: Content category (tech, business, etc.)

        Returns:
            'tutorial' | 'analysis' | 'news'
        """
        topic_lower = topic.lower()
        keywords_str = ' '.join(keywords).lower()

        # Check for Tutorial indicators (15%)
        is_tutorial = (
            any(indicator in topic_lower for indicator in self.TUTORIAL_INDICATORS) or
            any(tech in keywords_str for tech in self.COMPLEX_TECH)
        )

        if is_tutorial:
            return 'tutorial'

        # Check for News indicators (25%)
        is_news = any(indicator in topic_lower for indicator in self.NEWS_INDICATORS)

        if is_news:
            return 'news'

        # Default to Analysis (60%)
        return 'analysis'

    def get_config(self, content_type: str, language: str = 'en') -> Dict:
        """
        Get configuration for a specific content type.

        Args:
            content_type: 'tutorial' | 'analysis' | 'news'
            language: 'en' | 'ko' | 'ja'

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
        """
        Get target distribution for content types.

        Returns:
            Dictionary with percentages for each type
        """
        return {
            'tutorial': 0.15,
            'analysis': 0.60,
            'news': 0.25
        }

    def get_target_counts(self, total_posts: int) -> Dict[str, int]:
        """
        Calculate target counts for each content type.

        Args:
            total_posts: Total number of posts to generate

        Returns:
            Dictionary with target counts for each type
        """
        distribution = self.get_distribution()

        return {
            'tutorial': round(total_posts * distribution['tutorial']),
            'analysis': round(total_posts * distribution['analysis']),
            'news': round(total_posts * distribution['news'])
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
