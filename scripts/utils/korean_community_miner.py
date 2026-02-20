#!/usr/bin/env python3
"""
Korean Community Miner

Extracts insights from Korean tech communities:
- GeekNews (HN의 한국판)
- Velog (개발자 블로그)
- Tech company blogs (Toss, Kakao, etc.)

Usage:
    from utils.korean_community_miner import KoreanCommunityMiner

    miner = KoreanCommunityMiner(anthropic_api_key)
    insights = miner.get_insights("React")
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

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
    print("Warning: feedparser not installed")
    feedparser = None


class KoreanCommunityMiner:
    """Mine insights from Korean tech communities"""

    # Korean tech company blog RSS feeds
    COMPANY_FEEDS = {
        "toss": "https://toss.tech/rss.xml",
        "kakao": "https://tech.kakao.com/feed/",
        "woowahan": "https://techblog.woowahan.com/feed/",
        "naver": "https://d2.naver.com/d2.atom",
        "line": "https://engineering.linecorp.com/ko/feed/",
    }

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize Korean community miner"""
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self.anthropic_api_key:
            safe_print("⚠️  ANTHROPIC_API_KEY not set - Korean community mining disabled")
            self.enabled = False
            return

        if not feedparser:
            safe_print("⚠️  feedparser not installed - Korean community mining disabled")
            self.enabled = False
            return

        self.enabled = True
        self.fetcher = ContentFetcher()
        self.client = Anthropic(api_key=self.anthropic_api_key)
        self.model = "claude-sonnet-4-6"

    def search_geeknews(self, keyword: str) -> List[Dict]:
        """
        Search GeekNews RSS feed.

        Args:
            keyword: Search keyword

        Returns:
            List of relevant articles
        """
        if not self.enabled:
            return []

        try:
            # GeekNews main RSS
            rss_url = "https://news.hada.io/rss"
            feed = feedparser.parse(rss_url)

            keyword_lower = keyword.lower()
            results = []

            for entry in feed.entries[:30]:  # Check recent 30
                title = entry.get('title', '').lower()
                summary = entry.get('summary', '').lower()

                if keyword_lower in title or keyword_lower in summary:
                    results.append({
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', '')[:500]
                    })

                    if len(results) >= 3:
                        break

            return results

        except Exception as e:
            safe_print(f"⚠️  GeekNews error: {mask_secrets(str(e)[:100])}")
            return []

    def search_company_blogs(self, keyword: str) -> List[Dict]:
        """
        Search Korean tech company blogs.

        Args:
            keyword: Search keyword

        Returns:
            List of relevant articles
        """
        if not self.enabled:
            return []

        results = []
        keyword_lower = keyword.lower()

        for company, feed_url in self.COMPANY_FEEDS.items():
            try:
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:10]:  # Recent 10 per feed
                    title = entry.get('title', '').lower()
                    summary = entry.get('summary', '').lower()

                    if keyword_lower in title or keyword_lower in summary:
                        results.append({
                            'source': company,
                            'title': entry.get('title', ''),
                            'link': entry.get('link', ''),
                            'summary': entry.get('summary', '')[:500]
                        })

                        break  # Max 1 per company

            except Exception:
                continue

        return results[:3]  # Max 3 total

    def extract_insights(self, articles: List[Dict], keyword: str) -> Optional[str]:
        """
        Extract insights from Korean articles.

        Args:
            articles: List of articles
            keyword: Original keyword

        Returns:
            Extracted insights
        """
        if not articles:
            return None

        try:
            # Build context
            context_parts = []

            for i, article in enumerate(articles, 1):
                source = article.get('source', 'GeekNews')
                context_parts.append(f"## {source}: {article['title']}")
                context_parts.append(f"Link: {article['link']}")
                context_parts.append(f"{article['summary']}\n")

            context = "\n".join(context_parts)

            # Extract insights
            prompt = f"""다음은 한국 tech 커뮤니티/블로그에서 "{keyword}"에 대한 최근 글들입니다:

{context}

이 글들에서 핵심 인사이트 2-3개를 추출해주세요.
중점:
- 한국 개발자들의 독특한 관점이나 경험
- 글로벌과 다른 한국 특유의 상황
- 실무에서의 구체적 사례

다음 형식으로:
- "한국 개발자 커뮤니티에서는..."
- "국내 기업 사례로는..."
- "한국 tech 블로그 분석에 따르면..."

간결하게 - 각 인사이트는 1-2문장."""

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
            safe_print(f"⚠️  Korean insight extraction error: {mask_secrets(str(e)[:100])}")
            return None

    def get_insights(self, keyword: str) -> Optional[str]:
        """
        Get insights from Korean tech community.

        Args:
            keyword: Topic/keyword

        Returns:
            Formatted insights or None
        """
        if not self.enabled:
            return None

        safe_print(f"\n🇰🇷 Korean Community Mining: '{keyword}'")

        # Search GeekNews
        safe_print(f"  📰 Searching GeekNews...")
        geeknews_articles = self.search_geeknews(keyword)
        safe_print(f"     Found {len(geeknews_articles)} relevant article(s)")

        # Search company blogs
        safe_print(f"  🏢 Searching Korean tech company blogs...")
        company_articles = self.search_company_blogs(keyword)
        safe_print(f"     Found {len(company_articles)} relevant article(s)")

        all_articles = geeknews_articles + company_articles

        if not all_articles:
            safe_print(f"  ⚠️  No Korean community content found")
            return None

        # Extract insights
        safe_print(f"  🤖 Extracting insights with Claude...")
        insights = self.extract_insights(all_articles[:5], keyword)

        if insights:
            safe_print(f"  ✅ Korean community insights extracted ({len(insights)} chars)")
            return f"# Korean Tech Community Insights\n\n{insights}\n"
        else:
            safe_print(f"  ⚠️  Failed to extract insights")
            return None


def main():
    """Test Korean community miner"""
    import argparse

    parser = argparse.ArgumentParser(description='Mine Korean community insights')
    parser.add_argument('keyword', help='Keyword to search for')
    parser.add_argument('--output', '-o', help='Output file')

    args = parser.parse_args()

    miner = KoreanCommunityMiner()

    if not miner.enabled:
        print("❌ Korean community miner not available")
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
