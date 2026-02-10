#!/usr/bin/env python3
"""
A/B Test Manager for Jake's Tech Insights
Manages A/B tests for title styles, content length, image placement, and CTA positions
"""

import json
import random
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class ABTestManager:
    def __init__(self):
        self.tests_file = Path("data/ab_tests.json")
        self.results_file = Path("data/ab_test_results.json")
        self.load_tests()
        self.load_results()

    def load_tests(self):
        """Load A/B test configurations"""
        if self.tests_file.exists():
            with open(self.tests_file, 'r', encoding='utf-8') as f:
                self.tests = json.load(f)
        else:
            # Initialize with default tests
            self.tests = {
                "title_style": {
                    "name": "Title Style Test",
                    "variants": {
                        "A": "informative",
                        "B": "clickbait"
                    },
                    "active": True,
                    "split": 0.5
                },
                "word_count": {
                    "name": "Content Length Test",
                    "variants": {
                        "A": "800",
                        "B": "1500",
                        "C": "2500"
                    },
                    "active": True,
                    "split": 0.33
                },
                "image_placement": {
                    "name": "Image Position Test",
                    "variants": {
                        "A": "top",
                        "B": "section"
                    },
                    "active": False,
                    "split": 0.5
                }
            }
            self.save_tests()

    def load_results(self):
        """Load A/B test results"""
        if self.results_file.exists():
            with open(self.results_file, 'r', encoding='utf-8') as f:
                self.results = json.load(f)
        else:
            self.results = {
                "tests": [],
                "last_updated": datetime.now().isoformat()
            }

    def save_tests(self):
        """Save A/B test configurations"""
        with open(self.tests_file, 'w', encoding='utf-8') as f:
            json.dump(self.tests, f, indent=2, ensure_ascii=False)

    def save_results(self):
        """Save A/B test results"""
        self.results['last_updated'] = datetime.now().isoformat()
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

    def create_test(self, test_name: str, variants: Dict[str, str], active: bool = True):
        """Create new A/B test"""
        split = 1.0 / len(variants)
        self.tests[test_name] = {
            "name": test_name,
            "variants": variants,
            "active": active,
            "split": split
        }
        self.save_tests()
        print(f"✅ Created test: {test_name} with {len(variants)} variants")

    def assign_variant(self, post_id: str, test_name: str) -> Optional[str]:
        """Assign variant to post based on test configuration"""
        if test_name not in self.tests:
            return None

        test = self.tests[test_name]
        if not test.get('active', False):
            return None

        # Use hash of post_id for consistent assignment
        hash_value = int(hashlib.md5(f"{post_id}_{test_name}".encode()).hexdigest(), 16)
        random.seed(hash_value)

        variants = list(test['variants'].keys())
        variant = random.choice(variants)

        # Record assignment
        self.results['tests'].append({
            "post_id": post_id,
            "test_name": test_name,
            "variant": variant,
            "assigned_at": datetime.now().isoformat()
        })
        self.save_results()

        return variant

    def should_run_test(self, test_name: str) -> bool:
        """Decide if test should run (50% probability for active tests)"""
        if test_name not in self.tests:
            return False

        test = self.tests[test_name]
        if not test.get('active', False):
            return False

        # 50% chance to run the test
        return random.random() < 0.5

    def generate_title_variants(self, original_title: str, lang: str = 'en') -> Dict[str, str]:
        """
        Generate title variants for A/B testing
        Variant A: Informative (original)
        Variant B: Clickbait (engaging/curiosity-driven)
        """

        # Clickbait patterns by language
        patterns = {
            'en': [
                "The Ultimate Guide to {}",
                "Everything You Need to Know About {}",
                "{}: The Complete Guide",
                "How {} Will Change Your Life",
                "The Secret Behind {}",
                "Why {} Matters More Than Ever",
                "5 Things You Didn't Know About {}",
                "{}: What the Experts Won't Tell You"
            ],
            'ko': [
                "{}의 모든 것: 완벽 가이드",
                "{}에 대해 알아야 할 모든 것",
                "{}가 당신의 삶을 바꾸는 방법",
                "{}의 숨겨진 비밀",
                "전문가들이 말하지 않는 {}의 진실",
                "{}가 중요한 5가지 이유",
                "당신이 몰랐던 {}의 모든 것"
            ],
        }

        # Extract core topic from original title
        core_topic = original_title
        # Remove common prefixes
        for prefix in ["Understanding ", "Introduction to ", "Guide to ", "How to ", "What is "]:
            if original_title.startswith(prefix):
                core_topic = original_title[len(prefix):]
                break

        # Generate clickbait variant
        clickbait_patterns = patterns.get(lang, patterns['en'])
        clickbait_title = random.choice(clickbait_patterns).format(core_topic)

        return {
            "A": original_title,  # Informative
            "B": clickbait_title  # Clickbait
        }

    def add_test_metadata(self, frontmatter: str, test_id: str, variant: str) -> str:
        """Add A/B test metadata to Hugo frontmatter"""
        # Insert before the closing ---
        lines = frontmatter.split('\n')

        # Find the position to insert (before closing ---)
        insert_pos = -2  # Before closing --- and empty line

        # Add test metadata
        test_metadata = f'ab_test_id: "{test_id}"\nab_variant: "{variant}"'
        lines.insert(insert_pos, test_metadata)

        return '\n'.join(lines)

    def get_target_word_count(self, variant: str, lang: str = 'en') -> int:
        """Get target word count based on variant"""
        variant_to_count = {
            "A": 800,
            "B": 1500,
            "C": 2500
        }

        base_count = variant_to_count.get(variant, 1500)

        return base_count

    def get_active_tests(self) -> List[str]:
        """Get list of active test names"""
        return [name for name, test in self.tests.items() if test.get('active', False)]

    def get_test_summary(self) -> Dict:
        """Get summary of all tests and their results"""
        summary = {
            "total_tests": len(self.tests),
            "active_tests": len(self.get_active_tests()),
            "total_assignments": len(self.results.get('tests', [])),
            "tests": {}
        }

        # Count assignments per test
        for test_name in self.tests:
            assignments = [r for r in self.results.get('tests', []) if r['test_name'] == test_name]
            variant_counts = {}
            for assignment in assignments:
                variant = assignment['variant']
                variant_counts[variant] = variant_counts.get(variant, 0) + 1

            summary["tests"][test_name] = {
                "active": self.tests[test_name].get('active', False),
                "total_assignments": len(assignments),
                "variant_distribution": variant_counts
            }

        return summary


def main():
    """CLI interface for A/B test manager"""
    import sys

    manager = ABTestManager()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python ab_test_manager.py summary       - Show test summary")
        print("  python ab_test_manager.py create <name> - Create new test")
        print("  python ab_test_manager.py activate <name> - Activate test")
        print("  python ab_test_manager.py deactivate <name> - Deactivate test")
        return

    command = sys.argv[1]

    if command == "summary":
        summary = manager.get_test_summary()
        print(f"\n📊 A/B Test Summary")
        print(f"=" * 50)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Active Tests: {summary['active_tests']}")
        print(f"Total Assignments: {summary['total_assignments']}")
        print(f"\nTest Details:")
        for test_name, details in summary['tests'].items():
            status = "✅ ACTIVE" if details['active'] else "⏸️  INACTIVE"
            print(f"\n  {test_name} ({status})")
            print(f"    Assignments: {details['total_assignments']}")
            if details['variant_distribution']:
                print(f"    Distribution:")
                for variant, count in details['variant_distribution'].items():
                    print(f"      Variant {variant}: {count}")

    elif command == "activate" and len(sys.argv) > 2:
        test_name = sys.argv[2]
        if test_name in manager.tests:
            manager.tests[test_name]['active'] = True
            manager.save_tests()
            print(f"✅ Activated test: {test_name}")
        else:
            print(f"❌ Test not found: {test_name}")

    elif command == "deactivate" and len(sys.argv) > 2:
        test_name = sys.argv[2]
        if test_name in manager.tests:
            manager.tests[test_name]['active'] = False
            manager.save_tests()
            print(f"⏸️  Deactivated test: {test_name}")
        else:
            print(f"❌ Test not found: {test_name}")

    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
