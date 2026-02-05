#!/usr/bin/env python3
"""
A/B Test Winner Analysis

Analyzes A/B test results from Google Search Console data to identify winning patterns.
Compares CTR, impressions, and clicks between title variants.

Usage:
    python scripts/analyze_ab_winners.py              # Analyze all tests
    python scripts/analyze_ab_winners.py --days 30    # Last 30 days
    python scripts/analyze_ab_winners.py --test title_style  # Specific test

Requirements:
    - GSC API credentials configured (see docs/SEO_TRACKING_SETUP.md)
    - At least 7 days of data for statistical significance
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

try:
    from seo_tracker import SEOTracker
except ImportError:
    print("Error: seo_tracker.py not found")
    sys.exit(1)


class ABWinnerAnalyzer:
    """Analyze A/B test winners from GSC data"""

    def __init__(self, service_account_file: str, property_url: str):
        """Initialize with GSC credentials"""
        self.tracker = SEOTracker(service_account_file, property_url)
        self.ab_results_file = Path("data/ab_test_results.json")
        self.load_ab_assignments()

    def load_ab_assignments(self):
        """Load A/B test assignments"""
        if not self.ab_results_file.exists():
            print("Error: No A/B test results found at data/ab_test_results.json")
            sys.exit(1)

        with open(self.ab_results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assignments = data.get('tests', [])

        # Create post_id -> variant mapping
        self.post_to_variant = {}
        for assignment in self.assignments:
            post_id = assignment['post_id']
            variant = assignment['variant']
            test_name = assignment['test_name']

            if post_id not in self.post_to_variant:
                self.post_to_variant[post_id] = {}

            self.post_to_variant[post_id][test_name] = variant

    def get_post_performance(self, days: int = 30) -> Dict[str, Dict]:
        """
        Get GSC performance data for all posts.

        Returns:
            Dict mapping URL to performance metrics
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        print(f"Fetching GSC data for {start_date} to {end_date}...")
        data = self.tracker.get_performance_data(start_date, end_date, ['page'])

        performance = {}
        for row in data:
            url = row['keys'][0]
            performance[url] = {
                'clicks': row.get('clicks', 0),
                'impressions': row.get('impressions', 0),
                'ctr': row.get('ctr', 0),
                'position': row.get('position', 0)
            }

        return performance

    def match_url_to_post_id(self, url: str) -> Optional[str]:
        """
        Extract post_id from URL.

        Examples:
            https://jakeinsight.com/tech/2026-02-04-cancer-san-diego/ -> 2026-02-04-cancer-san-diego
            https://jakeinsight.com/ko/business/2026-02-03-창원대/ -> 2026-02-03-창원대
        """
        # Remove domain and trailing slash
        path = url.replace('https://jakeinsight.com', '').rstrip('/')

        # Extract filename (last segment)
        parts = path.split('/')
        if len(parts) >= 2:
            post_id = parts[-1]
            return post_id

        return None

    def analyze_test(self, test_name: str, days: int = 30) -> Dict:
        """
        Analyze specific A/B test.

        Returns:
            Dict with winner analysis and statistics
        """
        # Get performance data from GSC
        performance = self.get_post_performance(days)

        # Group by variant
        variant_metrics = defaultdict(lambda: {
            'clicks': [],
            'impressions': [],
            'ctr': [],
            'position': [],
            'post_count': 0,
            'urls': []
        })

        matched_posts = 0
        unmatched_urls = []

        for url, metrics in performance.items():
            post_id = self.match_url_to_post_id(url)

            if not post_id or post_id not in self.post_to_variant:
                unmatched_urls.append(url)
                continue

            if test_name not in self.post_to_variant[post_id]:
                continue

            variant = self.post_to_variant[post_id][test_name]
            matched_posts += 1

            variant_metrics[variant]['clicks'].append(metrics['clicks'])
            variant_metrics[variant]['impressions'].append(metrics['impressions'])
            variant_metrics[variant]['ctr'].append(metrics['ctr'])
            variant_metrics[variant]['position'].append(metrics['position'])
            variant_metrics[variant]['post_count'] += 1
            variant_metrics[variant]['urls'].append(url)

        # Calculate aggregates
        results = {}
        for variant, data in variant_metrics.items():
            total_clicks = sum(data['clicks'])
            total_impressions = sum(data['impressions'])
            avg_ctr = (total_clicks / total_impressions) if total_impressions > 0 else 0
            avg_position = sum(data['position']) / len(data['position']) if data['position'] else 0

            results[variant] = {
                'post_count': data['post_count'],
                'total_clicks': total_clicks,
                'total_impressions': total_impressions,
                'avg_ctr': avg_ctr,
                'avg_position': avg_position,
                'urls': data['urls']
            }

        # Determine winner
        winner = None
        if results:
            winner = max(results.keys(), key=lambda v: results[v]['avg_ctr'])

        analysis = {
            'test_name': test_name,
            'period': f"{(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}",
            'matched_posts': matched_posts,
            'unmatched_urls_count': len(unmatched_urls),
            'variants': results,
            'winner': winner,
            'confidence': self.calculate_confidence(results) if len(results) >= 2 else 'insufficient_data'
        }

        return analysis

    def calculate_confidence(self, results: Dict) -> str:
        """
        Calculate statistical confidence level.

        Simplified confidence based on sample size and CTR difference.
        """
        if len(results) < 2:
            return 'insufficient_data'

        # Get two best variants by CTR
        sorted_variants = sorted(results.items(), key=lambda x: x[1]['avg_ctr'], reverse=True)

        if len(sorted_variants) < 2:
            return 'insufficient_data'

        best = sorted_variants[0][1]
        second = sorted_variants[1][1]

        # Check sample size
        if best['post_count'] < 5 or second['post_count'] < 5:
            return 'low (small sample)'

        # Calculate CTR difference
        ctr_diff = abs(best['avg_ctr'] - second['avg_ctr']) / second['avg_ctr'] if second['avg_ctr'] > 0 else 0

        if ctr_diff > 0.20:  # 20%+ difference
            return 'high'
        elif ctr_diff > 0.10:  # 10-20% difference
            return 'medium'
        else:
            return 'low (small difference)'

    def extract_title_patterns(self, test_name: str = 'title_style') -> Dict[str, List[str]]:
        """
        Extract title patterns used in each variant.

        Returns:
            Dict mapping variant to list of title patterns
        """
        patterns = defaultdict(list)

        # Read content files to extract titles
        content_dirs = [
            Path('content/en'),
            Path('content/ko'),
            Path('content/ja')
        ]

        for content_dir in content_dirs:
            if not content_dir.exists():
                continue

            for md_file in content_dir.rglob('*.md'):
                # Extract post_id from filename
                post_id = md_file.stem

                if post_id not in self.post_to_variant or test_name not in self.post_to_variant[post_id]:
                    continue

                variant = self.post_to_variant[post_id][test_name]

                # Read frontmatter to get title
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # Extract title from frontmatter
                    if content.startswith('---'):
                        frontmatter_end = content.find('---', 3)
                        if frontmatter_end != -1:
                            frontmatter = content[3:frontmatter_end]
                            for line in frontmatter.split('\n'):
                                if line.startswith('title:'):
                                    title = line.replace('title:', '').strip().strip('"')
                                    patterns[variant].append(title)
                                    break

        return dict(patterns)

    def generate_report(self, test_name: str = 'title_style', days: int = 30) -> str:
        """Generate comprehensive analysis report"""
        analysis = self.analyze_test(test_name, days)
        patterns = self.extract_title_patterns(test_name)

        report = []
        report.append("=" * 80)
        report.append("A/B TEST WINNER ANALYSIS")
        report.append("=" * 80)
        report.append(f"Test: {analysis['test_name']}")
        report.append(f"Period: {analysis['period']}")
        report.append(f"Matched Posts: {analysis['matched_posts']}")
        report.append(f"Unmatched URLs: {analysis['unmatched_urls_count']}")
        report.append("")

        if analysis['winner']:
            report.append(f"🏆 WINNER: Variant {analysis['winner']}")
            report.append(f"Confidence: {analysis['confidence']}")
        else:
            report.append("⚠️  No winner determined (insufficient data)")

        report.append("")
        report.append("VARIANT PERFORMANCE:")
        report.append("-" * 80)

        for variant in sorted(analysis['variants'].keys()):
            data = analysis['variants'][variant]
            report.append(f"\nVariant {variant}:")
            report.append(f"  Posts: {data['post_count']}")
            report.append(f"  Total Clicks: {data['total_clicks']:,}")
            report.append(f"  Total Impressions: {data['total_impressions']:,}")
            report.append(f"  Average CTR: {data['avg_ctr']:.2%}")
            report.append(f"  Average Position: {data['avg_position']:.1f}")

            # Show sample URLs
            if data['urls']:
                report.append(f"  Sample URLs:")
                for url in data['urls'][:3]:
                    report.append(f"    - {url}")

        # Add title patterns
        if patterns and test_name == 'title_style':
            report.append("")
            report.append("TITLE PATTERNS:")
            report.append("-" * 80)

            for variant, titles in patterns.items():
                report.append(f"\nVariant {variant} ({len(titles)} titles):")
                for title in titles[:5]:  # Show first 5
                    report.append(f"  - {title}")
                if len(titles) > 5:
                    report.append(f"  ... and {len(titles) - 5} more")

        # Add recommendations
        report.append("")
        report.append("RECOMMENDATIONS:")
        report.append("-" * 80)

        if analysis['winner'] and analysis['confidence'] not in ['insufficient_data', 'low (small sample)']:
            winner_data = analysis['variants'][analysis['winner']]
            ctr_improvement = winner_data['avg_ctr']

            report.append(f"✅ Apply Variant {analysis['winner']} pattern to all future content")
            report.append(f"✅ Expected CTR: {ctr_improvement:.2%}")

            if test_name == 'title_style' and analysis['winner'] in patterns:
                report.append(f"✅ Winning title patterns to use:")
                winning_titles = patterns[analysis['winner']]

                # Extract common patterns
                common_patterns = []
                if any("5 Things" in t for t in winning_titles):
                    common_patterns.append("  - '5 Things You Didn't Know About {topic}'")
                if any("What the Experts" in t for t in winning_titles):
                    common_patterns.append("  - '{topic}: What the Experts Won't Tell You'")
                if any("Ultimate Guide" in t for t in winning_titles):
                    common_patterns.append("  - 'The Ultimate Guide to {topic}'")

                for pattern in common_patterns:
                    report.append(pattern)
        else:
            report.append("⚠️  Continue testing (need more data for confident decision)")
            report.append(f"   Current sample size: {analysis.get('matched_posts', 0)} posts")
            report.append(f"   Recommended: 30+ posts per variant")

        report.append("")
        report.append("=" * 80)

        return '\n'.join(report)


def main():
    parser = argparse.ArgumentParser(description='Analyze A/B test winners from GSC data')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze (default: 30)')
    parser.add_argument('--test', type=str, default='title_style', help='Test name to analyze (default: title_style)')
    parser.add_argument('--output', type=str, help='Save report to file')

    args = parser.parse_args()

    # Load credentials
    service_account_file = os.getenv('GSC_SERVICE_ACCOUNT_FILE')
    property_url = os.getenv('GSC_PROPERTY_URL')

    if not service_account_file or not property_url:
        print("Error: Missing GSC credentials in .env")
        print("Required:")
        print("  GSC_SERVICE_ACCOUNT_FILE=config/gsc-service-account.json")
        print("  GSC_PROPERTY_URL=https://jakeinsight.com")
        print("\nSee docs/SEO_TRACKING_SETUP.md for setup instructions")
        sys.exit(1)

    try:
        analyzer = ABWinnerAnalyzer(service_account_file, property_url)
        report = analyzer.generate_report(args.test, args.days)

        print(report)

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(report, encoding='utf-8')
            print(f"\n✅ Report saved to {output_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure service account JSON file exists at the specified path")
        print("See docs/SEO_TRACKING_SETUP.md for setup instructions")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
