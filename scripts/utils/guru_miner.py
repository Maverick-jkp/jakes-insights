#!/usr/bin/env python3
"""
Guru Insights Miner

Extracts insights from industry thought leaders:
- Lenny's Newsletter (Product/PM)
- a16z Blog (VC/Startups)
- Pragmatic Engineer (Engineering)

Usage:
    from utils.guru_miner import GuruMiner

    miner = GuruMiner(anthropic_api_key)
    insights = miner.get_insights("React Server Components")
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.content_fetcher import ContentFetcher
from utils.security import safe_print, mask_secrets

try:
    import requests
except ImportError:
    print("Error: requests package not installed")
    sys.exit(1)

try:
    from anthropic import Anthropic
except ImportError:
    print("Error: anthropic package not installed")
    sys.exit(1)

try:
    import feedparser
except ImportError:
    print("Warning: feedparser not installed - RSS feeds disabled")
    print("Install with: pip install feedparser")
    feedparser = None


class GuruMiner:
    """Mine insights from industry thought leaders"""

    # RSS feeds of tech thought leaders
    GURU_FEEDS = {
        "lenny": "https://www.lennysnewsletter.com/feed",
        "a16z": "https://a16z.com/feed/",
        "pragmatic": "https://newsletter.pragmaticengineer.com/feed",
    }

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize guru miner.

        Args:
            anthropic_api_key: Anthropic API key for insight extraction
        """
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self.anthropic_api_key:
            safe_print("⚠️  ANTHROPIC_API_KEY not set - Guru mining disabled")
            self.enabled = False
            return

        if not feedparser:
            safe_print("⚠️  feedparser not installed - Guru mining disabled")
            self.enabled = False
            return

        self.enabled = True
        self.fetcher = ContentFetcher()
        self.client = Anthropic(api_key=self.anthropic_api_key)
        self.model = "claude-sonnet-4-6"

    def search_rss_feed(self, feed_url: str, keyword: str, max_results: int = 3) -> List[Dict]:
        """
        Search RSS feed for relevant articles.

        Args:
            feed_url: RSS feed URL
            keyword: Search keyword
            max_results: Max articles to return

        Returns:
            List of articles with title, link, summary
        """
        if not self.enabled:
            return []

        try:
            feed = feedparser.parse(feed_url)

            if not feed.entries:
                return []

            keyword_lower = keyword.lower()
            results = []

            for entry in feed.entries[:20]:  # Check recent 20
                title = entry.get('title', '').lower()
                summary = entry.get('summary', '').lower()
                content = entry.get('content', [{}])[0].get('value', '').lower()

                # Check relevance
                if (keyword_lower in title or
                    keyword_lower in summary or
                    keyword_lower in content):

                    results.append({
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', '')[:500]
                    })

                    if len(results) >= max_results:
                        break

            return results

        except Exception as e:
            safe_print(f"⚠️  RSS feed error: {mask_secrets(str(e)[:100])}")
            return []

    def extract_guru_insights(self, articles: List[Dict], keyword: str) -> Optional[str]:
        """
        Extract insights from guru articles.

        Args:
            articles: List of article dicts
            keyword: Original keyword

        Returns:
            Extracted insights or None
        """
        if not articles:
            return None

        try:
            # Build context
            context_parts = []

            for i, article in enumerate(articles, 1):
                context_parts.append(f"## Article {i}: {article['title']}")
                context_parts.append(f"Source: {article['link']}")
                context_parts.append(f"Summary: {article['summary']}\n")

            context = "\n".join(context_parts)

            # Extract insights
            prompt = f"""The following are recent articles from industry thought leaders about "{keyword}":

{context}

Extract 2-3 key insights that would be valuable for writing about {keyword}.
Focus on:
- Unique perspectives or counterintuitive takes
- Specific data or examples mentioned
- Practical implications or predictions

Format as bullet points starting with:
- "According to [Author/Source]..."
- "Industry leaders note that..."
- "[Source] reports that..."

Keep it concise - 1-2 sentences per insight."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            insights = response.content[0].text.strip()
            return insights

        except Exception as e:
            safe_print(f"⚠️  Guru insight extraction error: {mask_secrets(str(e)[:100])}")
            return None

    def get_insights(self, keyword: str) -> Optional[str]:
        """
        Get insights from industry gurus.

        Main entry point that:
        1. Searches RSS feeds of thought leaders
        2. Finds relevant recent articles
        3. Extracts key insights

        Args:
            keyword: Topic/keyword to search for

        Returns:
            Formatted insights or None
        """
        if not self.enabled:
            return None

        safe_print(f"\n🎓 Guru Mining: Gathering thought leader insights for '{keyword}'")

        all_articles = []

        # Search each feed
        for source_name, feed_url in self.GURU_FEEDS.items():
            safe_print(f"  📡 Searching {source_name}...")
            articles = self.search_rss_feed(feed_url, keyword, max_results=2)

            if articles:
                safe_print(f"     Found {len(articles)} relevant article(s)")
                all_articles.extend(articles)
            else:
                safe_print(f"     No matches")

        if not all_articles:
            safe_print(f"  ⚠️  No guru content found")
            return None

        # Extract insights
        safe_print(f"  🤖 Extracting insights with Claude...")
        insights = self.extract_guru_insights(all_articles[:5], keyword)  # Max 5 articles

        if insights:
            safe_print(f"  ✅ Guru insights extracted ({len(insights)} chars)")
            return f"# Industry Thought Leader Insights\n\n{insights}\n"
        else:
            safe_print(f"  ⚠️  Failed to extract insights")
            return None


def main():
    """Test guru miner"""
    import argparse

    parser = argparse.ArgumentParser(description='Mine guru insights')
    parser.add_argument('keyword', help='Keyword to search for')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')

    args = parser.parse_args()

    miner = GuruMiner()

    if not miner.enabled:
        print("❌ Guru miner not available (missing dependencies)")
        sys.exit(1)

    insights = miner.get_insights(args.keyword)

    if insights:
        if args.output:
            Path(args.output).write_text(insights, encoding='utf-8')
            print(f"\n✓ Saved to: {args.output}")
        else:
            print("\n" + "="*80)
            print(insights)
            print("="*80)
    else:
        print("\n❌ No insights found")
        sys.exit(1)


if __name__ == '__main__':
    main()
