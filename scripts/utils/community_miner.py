#!/usr/bin/env python3
"""
Community Miner - Extract Developer Insights from Communities

Mines HackerNews and Dev.to for real developer experiences, discussions,
and insights related to a topic.

Usage:
    from utils.community_miner import CommunityMiner

    miner = CommunityMiner(anthropic_api_key)
    insights = miner.get_insights("React Server Components")
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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


class CommunityMiner:
    """Mine developer insights from HackerNews and Dev.to"""

    def __init__(self, anthropic_api_key: Optional[str] = None, devto_api_key: Optional[str] = None):
        """
        Initialize community miner.

        Args:
            anthropic_api_key: Anthropic API key for insight extraction
            devto_api_key: Dev.to API key (optional, public API works without it)
        """
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.devto_api_key = devto_api_key or os.environ.get("DEVTO_API_KEY")

        if not self.anthropic_api_key:
            safe_print("⚠️  ANTHROPIC_API_KEY not set - Community mining disabled")
            self.enabled = False
            return

        self.enabled = True

        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.anthropic_api_key)
        self.model = "claude-sonnet-4-6"

    def search_hackernews(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search HackerNews using Algolia API.

        Args:
            query: Search query
            max_results: Maximum number of stories to return

        Returns:
            List of stories with comments
        """
        if not self.enabled:
            return []

        try:
            # Search for stories
            search_url = "https://hn.algolia.com/api/v1/search"
            params = {
                "query": query,
                "tags": "story",
                "hitsPerPage": max_results,
                "numericFilters": f"created_at_i>{int((datetime.now() - timedelta(days=365)).timestamp())}"  # Past year
            }

            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            hits = data.get("hits", [])

            stories = []
            for hit in hits:
                story_id = hit.get("objectID")
                title = hit.get("title", "")
                url = hit.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                points = hit.get("points", 0)
                num_comments = hit.get("num_comments", 0)

                # Skip if no comments
                if num_comments < 3:
                    continue

                # Get top comments
                comments = self._get_hn_comments(story_id, max_comments=5)

                if comments:
                    stories.append({
                        "id": story_id,
                        "title": title,
                        "url": url,
                        "points": points,
                        "comments": comments
                    })

            return stories

        except Exception as e:
            safe_print(f"⚠️  HN search error: {mask_secrets(str(e)[:100])}")
            return []

    def _get_hn_comments(self, story_id: str, max_comments: int = 5) -> List[str]:
        """
        Get top comments for a HN story.

        Args:
            story_id: Story ID
            max_comments: Max comments to return

        Returns:
            List of comment texts
        """
        try:
            # Get story item with comments
            item_url = f"https://hn.algolia.com/api/v1/items/{story_id}"
            response = requests.get(item_url, timeout=10)
            response.raise_for_status()

            data = response.json()
            children = data.get("children", [])

            # Extract top-level comments (sorted by points)
            comments = []
            for child in children[:max_comments]:
                text = child.get("text")
                if text and len(text) > 50:  # Skip very short comments
                    # Remove HTML tags
                    import re
                    text = re.sub(r'<[^>]+>', '', text)
                    text = text.strip()
                    comments.append(text)

            return comments

        except Exception as e:
            return []

    def search_devto(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search Dev.to articles.

        Args:
            query: Search query
            max_results: Maximum number of articles to return

        Returns:
            List of articles with comments
        """
        if not self.enabled:
            return []

        try:
            # Search articles
            search_url = "https://dev.to/api/articles"
            params = {
                "per_page": max_results * 2,  # Get extras in case some have no comments
                "top": 30  # Top articles from past month
            }

            headers = {}
            if self.devto_api_key:
                headers["api-key"] = self.devto_api_key

            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            articles_data = response.json()

            # Filter by query relevance
            articles = []
            query_lower = query.lower()

            for article in articles_data:
                title = article.get("title", "")
                description = article.get("description", "")
                tags = " ".join(article.get("tag_list", []))

                # Check relevance
                if (query_lower in title.lower() or
                    query_lower in description.lower() or
                    query_lower in tags.lower()):

                    article_id = article.get("id")
                    comments_count = article.get("comments_count", 0)

                    # Skip if no comments
                    if comments_count < 2:
                        continue

                    # Get comments
                    comments = self._get_devto_comments(article_id, max_comments=5)

                    if comments:
                        articles.append({
                            "id": article_id,
                            "title": title,
                            "url": article.get("url", ""),
                            "comments": comments
                        })

                        if len(articles) >= max_results:
                            break

            return articles

        except Exception as e:
            safe_print(f"⚠️  Dev.to search error: {mask_secrets(str(e)[:100])}")
            return []

    def _get_devto_comments(self, article_id: int, max_comments: int = 5) -> List[str]:
        """
        Get comments for a Dev.to article.

        Args:
            article_id: Article ID
            max_comments: Max comments to return

        Returns:
            List of comment texts
        """
        try:
            comments_url = f"https://dev.to/api/comments?a_id={article_id}"

            headers = {}
            if self.devto_api_key:
                headers["api-key"] = self.devto_api_key

            response = requests.get(comments_url, headers=headers, timeout=10)
            response.raise_for_status()

            comments_data = response.json()

            # Extract comment bodies
            comments = []
            for comment in comments_data[:max_comments]:
                body = comment.get("body_markdown") or comment.get("body_html", "")
                if body and len(body) > 50:
                    # Remove markdown formatting
                    import re
                    body = re.sub(r'[#*`\[\]]', '', body)
                    body = body.strip()
                    comments.append(body)

            return comments

        except Exception as e:
            return []

    def extract_insights(self, discussions: Dict[str, List[Dict]]) -> Optional[str]:
        """
        Extract developer insights from discussions using Claude.

        Args:
            discussions: Dict with 'hn' and 'devto' keys containing discussion lists

        Returns:
            Extracted insights text or None
        """
        if not self.enabled:
            return None

        try:
            # Build context from discussions
            context_parts = []

            # HackerNews discussions
            hn_discussions = discussions.get("hn", [])
            if hn_discussions:
                context_parts.append("# HackerNews Discussions\n")
                for i, story in enumerate(hn_discussions, 1):
                    context_parts.append(f"## Story {i}: {story['title']}")
                    context_parts.append(f"URL: {story['url']}\n")
                    context_parts.append("Top Comments:")
                    for j, comment in enumerate(story['comments'][:3], 1):
                        context_parts.append(f"{j}. {comment[:500]}...")  # Truncate long comments
                    context_parts.append("")

            # Dev.to discussions
            devto_discussions = discussions.get("devto", [])
            if devto_discussions:
                context_parts.append("# Dev.to Discussions\n")
                for i, article in enumerate(devto_discussions, 1):
                    context_parts.append(f"## Article {i}: {article['title']}")
                    context_parts.append(f"URL: {article['url']}\n")
                    context_parts.append("Comments:")
                    for j, comment in enumerate(article['comments'][:3], 1):
                        context_parts.append(f"{j}. {comment[:500]}...")
                    context_parts.append("")

            if not context_parts:
                return None

            context = "\n".join(context_parts)

            # Extract insights with Claude
            prompt = f"""Analyze the following developer discussions and extract key insights:

{context}

Extract:
1. **Common experiences or patterns** mentioned by developers
2. **Practical tips or solutions** shared
3. **Challenges or pitfalls** discussed
4. **Real-world use cases** or examples

Format as 3-5 concise bullet points starting with:
- "Developers mention..."
- "A common pattern is..."
- "One challenge discussed..."
- "Practical tip: ..."

Focus on specific, actionable insights - NOT generic observations.
Each point should be 1-2 sentences maximum.
"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            insights = response.content[0].text.strip()
            return insights

        except Exception as e:
            safe_print(f"⚠️  Insight extraction error: {mask_secrets(str(e)[:100])}")
            return None

    def get_insights(self, keyword: str) -> Optional[str]:
        """
        Get community insights for a keyword/topic.

        Main entry point that:
        1. Searches HackerNews and Dev.to
        2. Collects discussions and comments
        3. Extracts insights using Claude

        Args:
            keyword: Topic/keyword to search for

        Returns:
            Formatted insights string or None
        """
        if not self.enabled:
            return None

        safe_print(f"\n💬 Community Mining: Gathering insights for '{keyword}'")

        # Search HackerNews
        safe_print(f"  🟠 Searching HackerNews...")
        hn_stories = self.search_hackernews(keyword, max_results=3)
        safe_print(f"     Found {len(hn_stories)} relevant discussions")

        # Search Dev.to
        safe_print(f"  🟣 Searching Dev.to...")
        devto_articles = self.search_devto(keyword, max_results=3)
        safe_print(f"     Found {len(devto_articles)} relevant articles")

        if not hn_stories and not devto_articles:
            safe_print(f"  ⚠️  No community discussions found")
            return None

        # Extract insights
        safe_print(f"  🤖 Extracting insights with Claude...")
        discussions = {
            "hn": hn_stories,
            "devto": devto_articles
        }

        insights = self.extract_insights(discussions)

        if insights:
            safe_print(f"  ✅ Community insights extracted ({len(insights)} chars)")
            return f"# Developer Community Insights\n\n{insights}\n"
        else:
            safe_print(f"  ⚠️  Failed to extract insights")
            return None


def main():
    """Test community miner"""
    import argparse

    parser = argparse.ArgumentParser(description='Mine community insights')
    parser.add_argument('keyword', help='Keyword to search for')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')

    args = parser.parse_args()

    miner = CommunityMiner()

    if not miner.enabled:
        print("❌ Community miner not available (missing API keys)")
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
        print("\n❌ Failed to extract insights")
        sys.exit(1)


if __name__ == '__main__':
    main()
