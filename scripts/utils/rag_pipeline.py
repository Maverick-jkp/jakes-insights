#!/usr/bin/env python3
"""
RAG Pipeline - Retrieval-Augmented Generation

Fetches recent articles/documentation about a topic, summarizes them,
and provides context for content generation.

Usage:
    from utils.rag_pipeline import RAGPipeline

    rag = RAGPipeline(brave_api_key, anthropic_api_key)
    context = rag.get_context("React Server Components")
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent to path for imports
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


class RAGPipeline:
    """RAG pipeline for content enrichment"""

    def __init__(self, brave_api_key: Optional[str] = None, anthropic_api_key: Optional[str] = None):
        """
        Initialize RAG pipeline.

        Args:
            brave_api_key: Brave Search API key
            anthropic_api_key: Anthropic API key for summarization
        """
        self.brave_api_key = brave_api_key or os.environ.get("BRAVE_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")

        if not self.brave_api_key:
            safe_print("⚠️  BRAVE_API_KEY not set - RAG pipeline disabled")
            self.enabled = False
            return

        if not self.anthropic_api_key:
            safe_print("⚠️  ANTHROPIC_API_KEY not set - RAG pipeline disabled")
            self.enabled = False
            return

        self.enabled = True
        self.fetcher = ContentFetcher()

        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.anthropic_api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def search_brave(self, query: str, count: int = 10, freshness: str = "py") -> List[Dict]:
        """
        Search Brave for recent articles.

        Args:
            query: Search query
            count: Number of results (max 20)
            freshness: Time filter (pd=past day, pw=past week, pm=past month, py=past year)

        Returns:
            List of result dicts with 'title', 'url', 'description'
        """
        if not self.enabled:
            return []

        try:
            url = "https://api.search.brave.com/res/v1/web/search"

            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.brave_api_key
            }

            params = {
                "q": query,
                "count": min(count, 20),
                "freshness": freshness,
                "text_decorations": False,
                "search_lang": "en"
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract web results
            results = []
            web_results = data.get("web", {}).get("results", [])

            for result in web_results:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "description": result.get("description", ""),
                })

            return results

        except Exception as e:
            safe_print(f"⚠️  Brave Search error: {mask_secrets(str(e)[:100])}")
            return []

    def summarize_content(self, content: str, source_url: str) -> Optional[str]:
        """
        Summarize fetched content using Claude.

        Args:
            content: Markdown content to summarize
            source_url: Source URL for attribution

        Returns:
            Summary text (200-300 words) or None if failed
        """
        if not self.enabled:
            return None

        try:
            # Truncate very long content
            if len(content) > 15000:
                content = content[:15000] + "\n\n[... truncated ...]"

            prompt = f"""Summarize the following article in 200-300 words. Focus on:
- Key facts, data, and findings
- Technical details or specific information
- Unique insights or perspectives
- Recent developments or updates

DO NOT:
- Use phrases like "This article discusses..." or "The author explains..."
- Include your opinions or interpretations
- Repeat generic information

Source: {source_url}

Article content:
{content}

Provide a concise, factual summary focusing on specific information that would be useful for writing about this topic."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            summary = response.content[0].text.strip()
            return summary

        except Exception as e:
            safe_print(f"⚠️  Summarization error: {mask_secrets(str(e)[:100])}")
            return None

    def get_context(self, keyword: str, max_sources: int = 5) -> Optional[str]:
        """
        Get RAG context for a keyword/topic.

        This is the main entry point for the RAG pipeline:
        1. Search Brave for recent articles
        2. Fetch and convert top results to markdown
        3. Summarize each article
        4. Combine summaries into a context block

        Args:
            keyword: Topic/keyword to search for
            max_sources: Maximum number of sources to include

        Returns:
            Formatted context string with summaries and sources, or None if disabled/failed
        """
        if not self.enabled:
            return None

        safe_print(f"\n🔍 RAG Pipeline: Gathering context for '{keyword}'")

        # Step 1: Search Brave
        safe_print(f"  📡 Searching Brave for recent articles...")
        search_results = self.search_brave(keyword, count=max_sources * 2)  # Get extra in case some fail

        if not search_results:
            safe_print(f"  ⚠️  No search results found")
            return None

        safe_print(f"  ✓ Found {len(search_results)} search results")

        # Step 2: Fetch content
        urls = [r["url"] for r in search_results[:max_sources * 2]]  # Try up to 2x max in case failures
        content_dict = self.fetcher.fetch_multiple(urls, max_urls=max_sources * 2)

        if not content_dict:
            safe_print(f"  ⚠️  Failed to fetch any content")
            return None

        safe_print(f"  ✓ Successfully fetched {len(content_dict)} articles")

        # Step 3: Summarize each
        summaries = []
        safe_print(f"  🤖 Summarizing articles with Claude...")

        for i, (url, content) in enumerate(list(content_dict.items())[:max_sources]):
            safe_print(f"     {i+1}/{min(len(content_dict), max_sources)}: {url[:60]}...")

            summary = self.summarize_content(content, url)

            if summary:
                # Find matching search result for title
                title = next((r["title"] for r in search_results if r["url"] == url), "Article")

                summaries.append({
                    "title": title,
                    "url": url,
                    "summary": summary
                })
                safe_print(f"        ✓ Summarized ({len(summary)} chars)")
            else:
                safe_print(f"        ✗ Failed to summarize")

        if not summaries:
            safe_print(f"  ⚠️  No summaries generated")
            return None

        # Step 4: Format context
        context_parts = [
            f"# Recent Information About: {keyword}",
            "",
            f"The following summaries are from {len(summaries)} recent sources:",
            ""
        ]

        for i, item in enumerate(summaries, 1):
            context_parts.append(f"## Source {i}: {item['title']}")
            context_parts.append(f"URL: {item['url']}")
            context_parts.append("")
            context_parts.append(item['summary'])
            context_parts.append("")

        context_parts.append("---")
        context_parts.append("")
        context_parts.append("When writing, incorporate relevant facts and cite sources by URL.")
        context_parts.append("Use the format: \"According to [source description](URL)...\"")

        context = "\n".join(context_parts)

        safe_print(f"  ✅ RAG context ready: {len(context)} chars from {len(summaries)} sources")

        return context


def main():
    """Test RAG pipeline"""
    import argparse

    parser = argparse.ArgumentParser(description='Test RAG pipeline')
    parser.add_argument('keyword', help='Keyword to search for')
    parser.add_argument('--max-sources', type=int, default=3, help='Max sources (default: 3)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')

    args = parser.parse_args()

    rag = RAGPipeline()

    if not rag.enabled:
        print("❌ RAG pipeline not available (missing API keys)")
        sys.exit(1)

    context = rag.get_context(args.keyword, max_sources=args.max_sources)

    if context:
        if args.output:
            Path(args.output).write_text(context, encoding='utf-8')
            print(f"\n✓ Saved to: {args.output}")
        else:
            print("\n" + "="*80)
            print(context)
            print("="*80)
    else:
        print("\n❌ Failed to generate context")
        sys.exit(1)


if __name__ == '__main__':
    main()
