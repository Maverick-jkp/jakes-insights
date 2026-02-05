#!/usr/bin/env python3
"""
SEO Performance Tracker

Fetches performance data from Google Search Console API and generates reports.

Usage:
    python scripts/seo_tracker.py              # Weekly report
    python scripts/seo_tracker.py --days 30    # Last 30 days
    python scripts/seo_tracker.py --post-url <url>  # Specific post
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:
    print("Error: Google API client not installed")
    print("Install with: pip install google-api-python-client google-auth")
    sys.exit(1)


class SEOTracker:
    """Track SEO performance using Google Search Console API"""

    def __init__(self, service_account_file: str, property_url: str):
        """
        Initialize GSC API client.

        Args:
            service_account_file: Path to service account JSON key
            property_url: GSC property URL (e.g., https://jakeinsight.com)
        """
        if not Path(service_account_file).exists():
            raise FileNotFoundError(f"Service account file not found: {service_account_file}")

        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )

        self.service = build('searchconsole', 'v1', credentials=credentials)
        self.property_url = property_url

    def get_performance_data(
        self,
        start_date: str,
        end_date: str,
        dimensions: List[str] = ['page']
    ) -> List[Dict]:
        """
        Fetch performance data for date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            dimensions: List of dimensions ['page', 'query', 'country', 'device']

        Returns:
            List of performance data rows
        """
        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': dimensions,
            'rowLimit': 25000  # Max rows
        }

        try:
            response = self.service.searchanalytics().query(
                siteUrl=self.property_url,
                body=request
            ).execute()

            return response.get('rows', [])
        except Exception as e:
            print(f"Error fetching GSC data: {e}")
            return []

    def get_top_posts(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """
        Get top performing posts by clicks.

        Args:
            days: Number of days to look back
            limit: Number of top posts to return

        Returns:
            List of top posts with performance data
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        data = self.get_performance_data(start_date, end_date, ['page'])

        if not data:
            return []

        # Sort by clicks
        sorted_data = sorted(data, key=lambda x: x.get('clicks', 0), reverse=True)

        return sorted_data[:limit]

    def analyze_post_performance(self, url: str, days: int = 90) -> Optional[Dict]:
        """
        Get detailed performance for specific post.

        Args:
            url: Full URL of the post
            days: Number of days to analyze

        Returns:
            Performance metrics dict or None if not found
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        data = self.get_performance_data(start_date, end_date, ['page'])

        # Find matching URL
        for row in data:
            if row['keys'][0] == url:
                return {
                    'url': url,
                    'impressions': row['impressions'],
                    'clicks': row['clicks'],
                    'ctr': row['ctr'],
                    'position': row['position'],
                    'period': f'{start_date} to {end_date}'
                }

        return None

    def generate_weekly_report(self) -> Dict:
        """
        Generate weekly SEO performance report.

        Returns:
            Report dict with metrics and top posts
        """
        # This week
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        # Last week (for comparison)
        last_week_end = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        last_week_start = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')

        this_week = self.get_performance_data(start_date, end_date, ['page'])
        last_week = self.get_performance_data(last_week_start, last_week_end, ['page'])

        if not this_week:
            return {
                'error': 'No data available for this period',
                'period': f'{start_date} to {end_date}'
            }

        # Calculate totals
        this_week_clicks = sum(row.get('clicks', 0) for row in this_week)
        this_week_impressions = sum(row.get('impressions', 0) for row in this_week)
        last_week_clicks = sum(row.get('clicks', 0) for row in last_week)

        growth = ((this_week_clicks - last_week_clicks) / last_week_clicks * 100) if last_week_clicks > 0 else 0
        avg_ctr = (this_week_clicks / this_week_impressions * 100) if this_week_impressions > 0 else 0

        report = {
            'period': f'{start_date} to {end_date}',
            'total_clicks': this_week_clicks,
            'total_impressions': this_week_impressions,
            'average_ctr': avg_ctr,
            'week_over_week_growth': growth,
            'top_posts': sorted(this_week, key=lambda x: x.get('clicks', 0), reverse=True)[:10]
        }

        return report

    def get_category_performance(self, days: int = 30) -> Dict:
        """
        Analyze performance by content category.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with performance by category
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        data = self.get_performance_data(start_date, end_date, ['page'])

        # Group by category (extract from URL)
        categories = {}
        for row in data:
            url = row['keys'][0]
            # Extract category from URL: /tech/, /business/, etc.
            parts = url.split('/')
            category = 'other'
            for part in parts:
                if part in ['tech', 'business', 'lifestyle', 'society', 'entertainment', 'sports', 'finance', 'education']:
                    category = part
                    break

            if category not in categories:
                categories[category] = {
                    'clicks': 0,
                    'impressions': 0,
                    'posts': 0
                }

            categories[category]['clicks'] += row.get('clicks', 0)
            categories[category]['impressions'] += row.get('impressions', 0)
            categories[category]['posts'] += 1

        # Calculate CTR for each category
        for cat in categories:
            impr = categories[cat]['impressions']
            categories[cat]['ctr'] = (categories[cat]['clicks'] / impr * 100) if impr > 0 else 0

        return categories


def print_weekly_report(report: Dict):
    """Print formatted weekly report"""
    print("=" * 80)
    print("SEO PERFORMANCE REPORT")
    print("=" * 80)
    print(f"Period: {report['period']}")
    print(f"Total Clicks: {report['total_clicks']:,}")
    print(f"Total Impressions: {report['total_impressions']:,}")
    print(f"Average CTR: {report['average_ctr']:.2f}%")
    print(f"Week-over-Week Growth: {report['week_over_week_growth']:+.1f}%")
    print()
    print("Top 10 Posts by Clicks:")
    print("-" * 80)

    for i, post in enumerate(report['top_posts'], 1):
        url = post['keys'][0]
        clicks = post.get('clicks', 0)
        impressions = post.get('impressions', 0)
        ctr = post.get('ctr', 0) * 100
        position = post.get('position', 0)

        # Truncate URL for display
        display_url = url if len(url) <= 70 else url[:67] + "..."

        print(f"{i:2d}. {display_url}")
        print(f"    Clicks: {clicks:,} | Impressions: {impressions:,} | CTR: {ctr:.2f}% | Pos: {position:.1f}")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Track SEO performance from Google Search Console')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze (default: 7)')
    parser.add_argument('--post-url', type=str, help='Analyze specific post URL')
    parser.add_argument('--categories', action='store_true', help='Show performance by category')
    parser.add_argument('--top', type=int, default=10, help='Number of top posts to show (default: 10)')

    args = parser.parse_args()

    # Load credentials
    service_account_file = os.getenv('GSC_SERVICE_ACCOUNT_FILE')
    property_url = os.getenv('GSC_PROPERTY_URL')

    if not service_account_file or not property_url:
        print("Error: Missing GSC credentials in .env")
        print("Required:")
        print("  GSC_SERVICE_ACCOUNT_FILE=config/gsc-service-account.json")
        print("  GSC_PROPERTY_URL=https://jakeinsight.com")
        sys.exit(1)

    try:
        tracker = SEOTracker(service_account_file, property_url)

        if args.post_url:
            # Analyze specific post
            perf = tracker.analyze_post_performance(args.post_url, days=90)
            if perf:
                print(f"Performance for: {perf['url']}")
                print(f"Period: {perf['period']}")
                print(f"Clicks: {perf['clicks']:,}")
                print(f"Impressions: {perf['impressions']:,}")
                print(f"CTR: {perf['ctr']:.2%}")
                print(f"Average Position: {perf['position']:.1f}")
            else:
                print(f"No data found for URL: {args.post_url}")

        elif args.categories:
            # Category performance
            categories = tracker.get_category_performance(days=args.days)
            print(f"Category Performance (Last {args.days} days)")
            print("=" * 80)
            for cat, data in sorted(categories.items(), key=lambda x: x[1]['clicks'], reverse=True):
                print(f"{cat.capitalize()}")
                print(f"  Posts: {data['posts']} | Clicks: {data['clicks']:,} | CTR: {data['ctr']:.2f}%")

        else:
            # Weekly report (default)
            if args.days == 7:
                report = tracker.generate_weekly_report()
                if 'error' in report:
                    print(f"Error: {report['error']}")
                else:
                    print_weekly_report(report)
            else:
                # Custom days report
                top_posts = tracker.get_top_posts(days=args.days, limit=args.top)
                if top_posts:
                    print(f"Top {args.top} Posts (Last {args.days} days)")
                    print("=" * 80)
                    for i, post in enumerate(top_posts, 1):
                        url = post['keys'][0]
                        clicks = post.get('clicks', 0)
                        ctr = post.get('ctr', 0) * 100
                        print(f"{i}. {url}")
                        print(f"   Clicks: {clicks:,} | CTR: {ctr:.2f}%")
                else:
                    print("No data available for this period")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure service account JSON file exists at the specified path")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
