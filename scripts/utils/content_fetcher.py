#!/usr/bin/env python3
"""
Content Fetcher - RAG Pipeline Component

Fetches web content from URLs and converts to markdown for RAG processing.
Handles HTML parsing, content extraction, and markdown conversion.

Usage:
    from utils.content_fetcher import ContentFetcher

    fetcher = ContentFetcher()
    markdown = fetcher.fetch_url("https://example.com/article")
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional, Dict, List
from urllib.parse import urlparse, urljoin

try:
    import requests
except ImportError:
    print("Error: requests package not installed")
    print("Install with: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 package not installed")
    print("Install with: pip install beautifulsoup4")
    sys.exit(1)

try:
    import html2text
except ImportError:
    print("Error: html2text package not installed")
    print("Install with: pip install html2text")
    sys.exit(1)


class ContentFetcher:
    """Fetch and convert web content to markdown"""

    def __init__(self, timeout: int = 15, max_length: int = 50000):
        """
        Initialize content fetcher.

        Args:
            timeout: Request timeout in seconds
            max_length: Maximum content length to process
        """
        self.timeout = timeout
        self.max_length = max_length

        # Configure html2text converter
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = True  # Don't include images in markdown
        self.converter.ignore_emphasis = False
        self.converter.body_width = 0  # Don't wrap lines
        self.converter.unicode_snob = True
        self.converter.skip_internal_links = True

        # User agent to avoid blocks
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }

    def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch content from URL and convert to markdown.

        Args:
            url: URL to fetch

        Returns:
            Markdown content or None if failed
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                print(f"⚠️  Invalid URL: {url}")
                return None

            # Fetch content
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type.lower():
                print(f"⚠️  Not HTML content: {content_type}")
                return None

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract main content
            content_html = self._extract_main_content(soup)

            if not content_html:
                print(f"⚠️  No content extracted from: {url}")
                return None

            # Convert to markdown
            markdown = self.converter.handle(str(content_html))

            # Clean up markdown
            markdown = self._clean_markdown(markdown)

            # Truncate if too long
            if len(markdown) > self.max_length:
                markdown = markdown[:self.max_length] + "\n\n[... content truncated ...]"

            return markdown

        except requests.Timeout:
            print(f"⚠️  Timeout fetching: {url}")
            return None
        except requests.RequestException as e:
            print(f"⚠️  Error fetching {url}: {str(e)[:100]}")
            return None
        except Exception as e:
            print(f"⚠️  Unexpected error for {url}: {str(e)[:100]}")
            return None

    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """
        Extract main article content from HTML.

        Tries multiple strategies to find the main content.

        Args:
            soup: BeautifulSoup object

        Returns:
            BeautifulSoup object with main content or None
        """
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer',
                         'aside', 'iframe', 'form', 'button']):
            tag.decompose()

        # Remove common noise classes/ids
        noise_patterns = [
            'advertisement', 'ad-', 'sidebar', 'related', 'comments',
            'social', 'share', 'cookie', 'popup', 'modal', 'newsletter'
        ]

        for pattern in noise_patterns:
            for element in soup.find_all(class_=re.compile(pattern, re.I)):
                element.decompose()
            for element in soup.find_all(id=re.compile(pattern, re.I)):
                element.decompose()

        # Strategy 1: Look for <article> tag
        article = soup.find('article')
        if article and len(article.get_text(strip=True)) > 200:
            return article

        # Strategy 2: Look for main content tags
        for tag_name in ['main', 'article', 'div']:
            for class_pattern in ['article', 'post', 'content', 'entry', 'story']:
                content = soup.find(tag_name, class_=re.compile(class_pattern, re.I))
                if content and len(content.get_text(strip=True)) > 200:
                    return content

        # Strategy 3: Find div with most text
        divs = soup.find_all('div')
        if divs:
            # Sort by text length
            divs_with_text = [(div, len(div.get_text(strip=True))) for div in divs]
            divs_with_text.sort(key=lambda x: x[1], reverse=True)

            # Return the div with most text if it's substantial
            if divs_with_text and divs_with_text[0][1] > 500:
                return divs_with_text[0][0]

        # Strategy 4: Return body if nothing else works
        return soup.body if soup.body else soup

    def _clean_markdown(self, markdown: str) -> str:
        """
        Clean up converted markdown.

        Args:
            markdown: Raw markdown text

        Returns:
            Cleaned markdown
        """
        # Remove excessive blank lines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Remove navigation breadcrumbs
        markdown = re.sub(r'[\n\s]*»[\n\s]*', ' > ', markdown)
        markdown = re.sub(r'Home\s*>\s*', '', markdown, flags=re.I)

        # Remove common footer text
        footer_patterns = [
            r'Copyright © \d{4}.*',
            r'All rights reserved.*',
            r'Privacy Policy.*',
            r'Terms of Service.*',
            r'Subscribe to.*newsletter.*',
        ]
        for pattern in footer_patterns:
            markdown = re.sub(pattern, '', markdown, flags=re.I | re.MULTILINE)

        # Remove email signup prompts
        markdown = re.sub(r'Sign up.*email.*', '', markdown, flags=re.I)
        markdown = re.sub(r'Subscribe.*updates.*', '', markdown, flags=re.I)

        # Strip leading/trailing whitespace
        markdown = markdown.strip()

        return markdown

    def fetch_multiple(self, urls: List[str], max_urls: int = 5) -> Dict[str, str]:
        """
        Fetch multiple URLs and return as dict.

        Args:
            urls: List of URLs to fetch
            max_urls: Maximum number of URLs to process

        Returns:
            Dict mapping URL to markdown content
        """
        results = {}

        for i, url in enumerate(urls[:max_urls]):
            print(f"  📄 Fetching {i+1}/{min(len(urls), max_urls)}: {url[:60]}...")

            markdown = self.fetch_url(url)
            if markdown:
                results[url] = markdown
                print(f"     ✓ Fetched {len(markdown)} chars")
            else:
                print(f"     ✗ Failed")

        return results


def main():
    """Test content fetcher"""
    import argparse

    parser = argparse.ArgumentParser(description='Fetch and convert web content to markdown')
    parser.add_argument('url', help='URL to fetch')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')

    args = parser.parse_args()

    fetcher = ContentFetcher()
    markdown = fetcher.fetch_url(args.url)

    if markdown:
        if args.output:
            Path(args.output).write_text(markdown, encoding='utf-8')
            print(f"✓ Saved to: {args.output}")
        else:
            print(markdown)
    else:
        print("✗ Failed to fetch content")
        sys.exit(1)


if __name__ == '__main__':
    main()
