#!/usr/bin/env python3
"""
Dev.to Cross-Posting Publisher

Cross-posts English blog posts to Dev.to with canonical URLs.
Implements 3-day delay strategy for SEO safety.

Usage:
    python scripts/devto_publisher.py                     # Publish all eligible
    python scripts/devto_publisher.py --dry-run            # Preview without publishing
    python scripts/devto_publisher.py --file content/en/tech/2026-02-07-post.md
    python scripts/devto_publisher.py --delay-days 0       # No delay (testing)
"""

import os
import sys
import re
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from utils.security import safe_print, mask_secrets

try:
    import frontmatter
except ImportError:
    safe_print("Error: python-frontmatter not installed")
    safe_print("Install with: pip install python-frontmatter")
    sys.exit(1)

try:
    import requests
except ImportError:
    safe_print("Error: requests not installed")
    safe_print("Install with: pip install requests")
    sys.exit(1)


BASE_URL = "https://jakeinsight.com"
DEVTO_API_URL = "https://dev.to/api/articles"
MAX_ARTICLES_PER_RUN = 10
MAX_RETRIES = 3
TRACKING_FILE = Path("data/devto_published.json")


class HugoToDevtoConverter:
    """Converts Hugo markdown posts to Dev.to API format."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")

    def convert(self, filepath: Path) -> dict:
        """Convert a Hugo markdown file to Dev.to article data."""
        post = frontmatter.load(filepath)
        meta = post.metadata
        body = post.content

        title = meta.get("title", "")
        description = meta.get("description", "")
        categories = meta.get("categories", [])
        tags = meta.get("tags", [])
        image = meta.get("image", "")

        # Build canonical URL (same pattern as google_indexing.py)
        canonical_url = self._build_canonical_url(filepath, categories)

        # Convert body
        body = self._convert_image_urls(body)
        body = self._convert_internal_links(body)
        body = self._strip_unsplash_credit(body)
        body = self._strip_hero_image(body)

        # Build main_image URL
        main_image = None
        if image and not image.startswith("http") and "placeholder" not in image:
            main_image = f"{self.base_url}{image}"
        elif image and image.startswith("http"):
            main_image = image

        # Map tags
        devto_tags = self._map_tags(categories, tags)

        return {
            "article": {
                "title": title,
                "body_markdown": body.strip(),
                "published": True,
                "tags": devto_tags,
                "canonical_url": canonical_url,
                "description": description[:200] if description else "",
                "main_image": main_image,
            }
        }

    def _build_canonical_url(self, filepath: Path, categories: list) -> str:
        """Build canonical URL from filepath."""
        slug = filepath.stem  # e.g., 2026-02-07-waymo-world-model
        category = categories[0] if categories else filepath.parent.name
        return f"{self.base_url}/{category}/{slug}/"

    def _convert_image_urls(self, body: str) -> str:
        """Convert relative image URLs to absolute."""
        # Match markdown images: ![alt](/images/xxx.jpg)
        body = re.sub(
            r'!\[([^\]]*)\]\((/images/[^)]+)\)',
            lambda m: f'![{m.group(1)}]({self.base_url}{m.group(2)})',
            body
        )
        return body

    def _convert_internal_links(self, body: str) -> str:
        """Convert internal links to absolute URLs."""
        # Match [text](/en/category/slug/) pattern
        body = re.sub(
            r'\[([^\]]+)\]\(/en/([^)]+)\)',
            lambda m: f'[{m.group(1)}]({self.base_url}/{m.group(2)})',
            body
        )
        # Match [text](/category/slug/) without /en/ prefix
        body = re.sub(
            r'\[([^\]]+)\]\((/(?:tech|business|lifestyle|society|entertainment)/[^)]+)\)',
            lambda m: f'[{m.group(1)}]({self.base_url}{m.group(2)})',
            body
        )
        return body

    def _strip_unsplash_credit(self, body: str) -> str:
        """Remove Unsplash credit line."""
        body = re.sub(
            r'\n\*Photo by \[.*?\]\(.*?\) on \[Unsplash\]\(.*?\)\*\n?',
            '\n',
            body
        )
        return body

    def _strip_hero_image(self, body: str) -> str:
        """Remove hero image at the start of body (already set via main_image)."""
        body = re.sub(
            r'^!\[.*?\]\(.*?\)\s*\n',
            '',
            body.lstrip()
        )
        return body

    def _map_tags(self, categories: list, tags: list) -> list:
        """Map Hugo categories/tags to Dev.to tags (max 4, lowercase)."""
        raw_tags = []
        if categories:
            raw_tags.append(categories[0])
        raw_tags.extend(tags)

        clean_tags = []
        seen = set()
        for tag in raw_tags:
            normalized = re.sub(r'[^a-z0-9-]', '', tag.lower().replace(' ', '-'))
            normalized = normalized[:30]
            if normalized and normalized not in seen:
                seen.add(normalized)
                clean_tags.append(normalized)

        return clean_tags[:4]


class PublishedArticleTracker:
    """Tracks articles published to Dev.to."""

    def __init__(self, tracking_file: Path = TRACKING_FILE):
        self.tracking_file = tracking_file
        self.data = self._load()

    def _load(self) -> dict:
        """Load tracking data."""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                safe_print("  Warning: Tracking file corrupted, starting fresh")
        return {
            "published_articles": {},
            "failed_articles": {},
            "last_run": None,
            "stats": {"total_published": 0, "total_failed": 0, "total_skipped": 0}
        }

    def save(self):
        """Save tracking data."""
        self.data["last_run"] = datetime.now(timezone.utc).isoformat()
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tracking_file, 'w') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def is_published(self, filepath: str) -> bool:
        """Check if article was already published."""
        return filepath in self.data["published_articles"]

    def mark_published(self, filepath: str, devto_response: dict, canonical_url: str, title: str):
        """Record successful publication."""
        self.data["published_articles"][filepath] = {
            "devto_article_id": devto_response.get("id"),
            "devto_url": devto_response.get("url", ""),
            "canonical_url": canonical_url,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "title": title,
            "status": "published"
        }
        self.data["stats"]["total_published"] = len(self.data["published_articles"])
        # Remove from failed if it was there
        self.data["failed_articles"].pop(filepath, None)

    def mark_failed(self, filepath: str, error: str):
        """Record failed publication."""
        existing = self.data["failed_articles"].get(filepath, {})
        retry_count = existing.get("retry_count", 0) + 1
        self.data["failed_articles"][filepath] = {
            "error": error[:500],
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "retry_count": retry_count
        }
        self.data["stats"]["total_failed"] = len(self.data["failed_articles"])


class DevtoPublisher:
    """Publishes articles to Dev.to via API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/vnd.forem.api-v1+json",
            "User-Agent": "JakesInsights/1.0"
        }

    def publish_article(self, article_data: dict) -> dict:
        """Publish an article to Dev.to with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    DEVTO_API_URL,
                    headers=self.headers,
                    json=article_data,
                    timeout=30
                )

                if response.status_code == 201:
                    return response.json()

                if response.status_code == 429:
                    wait_time = 2 ** (attempt + 1)
                    safe_print(f"    Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Other errors
                error_msg = f"HTTP {response.status_code}: {response.text[:300]}"
                if attempt < MAX_RETRIES - 1:
                    safe_print(f"    Error: {error_msg}, retrying...")
                    time.sleep(2)
                    continue
                raise Exception(error_msg)

            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    safe_print(f"    Timeout, retrying ({attempt + 1}/{MAX_RETRIES})...")
                    time.sleep(2)
                    continue
                raise Exception("Request timed out after all retries")

            except requests.exceptions.ConnectionError as e:
                raise Exception(f"Connection error: {mask_secrets(str(e))}")

        raise Exception("Max retries exceeded")


def get_eligible_posts(delay_days: int = 3) -> list:
    """Find EN posts eligible for cross-posting (older than delay_days)."""
    content_dir = Path("content/en")
    if not content_dir.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=delay_days)
    eligible = []

    skip_files = {"_index.md", "all-posts.md", "privacy.md", "about.md"}

    for md_file in content_dir.rglob("*.md"):
        if md_file.name in skip_files:
            continue

        try:
            post = frontmatter.load(md_file)
            meta = post.metadata

            # Skip drafts
            if meta.get("draft", False):
                continue

            # Parse date
            date_val = meta.get("date")
            if not date_val:
                continue

            if isinstance(date_val, str):
                # Handle ISO format with timezone
                post_date = datetime.fromisoformat(date_val)
            elif isinstance(date_val, datetime):
                post_date = date_val
            else:
                continue

            # Ensure timezone-aware
            if post_date.tzinfo is None:
                post_date = post_date.replace(tzinfo=timezone.utc)
            else:
                post_date = post_date.astimezone(timezone.utc)

            if post_date <= cutoff:
                eligible.append((md_file, post_date))

        except Exception:
            continue

    # Sort by date ascending (oldest first)
    eligible.sort(key=lambda x: x[1])
    return [fp for fp, _ in eligible]


def main():
    parser = argparse.ArgumentParser(description="Cross-post to Dev.to")
    parser.add_argument("--dry-run", action="store_true", help="Preview without publishing")
    parser.add_argument("--file", type=str, help="Specific file to publish")
    parser.add_argument("--delay-days", type=int, default=3, help="Delay in days (default: 3)")
    args = parser.parse_args()

    # Check API key
    api_key = os.environ.get("DEVTO_API_KEY", "")
    if not api_key and not args.dry_run:
        safe_print("DEVTO_API_KEY not set. Skipping cross-posting.")
        sys.exit(0)

    safe_print(f"\n{'='*60}")
    safe_print(f"  Dev.to Cross-Posting Publisher")
    safe_print(f"{'='*60}\n")

    converter = HugoToDevtoConverter()
    tracker = PublishedArticleTracker()

    # Determine files to process
    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            safe_print(f"Error: File not found: {filepath}")
            sys.exit(1)
        files_to_process = [filepath]
    else:
        files_to_process = get_eligible_posts(delay_days=args.delay_days)

    if not files_to_process:
        safe_print("No eligible posts found.")
        tracker.save()
        sys.exit(0)

    # Filter already published
    new_files = [f for f in files_to_process if not tracker.is_published(str(f))]
    skipped = len(files_to_process) - len(new_files)
    tracker.data["stats"]["total_skipped"] = skipped

    if not new_files:
        safe_print(f"All {len(files_to_process)} eligible posts already published.")
        tracker.save()
        sys.exit(0)

    # Limit per run
    batch = new_files[:MAX_ARTICLES_PER_RUN]
    safe_print(f"Found {len(new_files)} new posts, processing {len(batch)} this run")
    if skipped:
        safe_print(f"Skipped {skipped} already published\n")

    if args.dry_run:
        safe_print("[DRY RUN] No articles will be published\n")

    # Initialize publisher
    publisher = None
    if not args.dry_run:
        publisher = DevtoPublisher(api_key)

    published = 0
    failed = 0

    for i, filepath in enumerate(batch, 1):
        safe_print(f"[{i}/{len(batch)}] {filepath.name}")

        try:
            article_data = converter.convert(filepath)
            title = article_data["article"]["title"]
            canonical = article_data["article"]["canonical_url"]
            tags = article_data["article"]["tags"]

            safe_print(f"  Title: {title}")
            safe_print(f"  Canonical: {canonical}")
            safe_print(f"  Tags: {tags}")
            safe_print(f"  Body length: {len(article_data['article']['body_markdown'])} chars")

            if args.dry_run:
                safe_print(f"  [DRY RUN] Would publish\n")
                continue

            # Publish
            response = publisher.publish_article(article_data)
            devto_url = response.get("url", "N/A")
            safe_print(f"  Published: {devto_url}")
            tracker.mark_published(str(filepath), response, canonical, title)
            published += 1

            # Small delay between posts
            if i < len(batch):
                time.sleep(2)

        except Exception as e:
            error_msg = mask_secrets(str(e))
            safe_print(f"  Failed: {error_msg}")
            tracker.mark_failed(str(filepath), error_msg)
            failed += 1

        safe_print("")

    # Save tracking data
    tracker.save()

    # Summary
    safe_print(f"{'='*60}")
    safe_print(f"  Summary")
    safe_print(f"{'='*60}")
    if args.dry_run:
        safe_print(f"  [DRY RUN] {len(batch)} posts previewed")
    else:
        safe_print(f"  Published: {published}")
        safe_print(f"  Failed: {failed}")
        safe_print(f"  Total on Dev.to: {tracker.data['stats']['total_published']}")
    safe_print("")


if __name__ == "__main__":
    main()
