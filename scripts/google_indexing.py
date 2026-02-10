#!/usr/bin/env python3
"""
Google Indexing API Integration
Notifies Google Search Console immediately when new content is published.

Documentation: https://developers.google.com/search/apis/indexing-api/v3/quickstart
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials" / "google-indexing-credentials.json"
INDEXED_URLS_FILE = PROJECT_ROOT / "data" / "indexed_urls.json"
BASE_URL = "https://jakeinsight.com"

# Scopes for Google Indexing API
SCOPES = ["https://www.googleapis.com/auth/indexing"]


class GoogleIndexingAPI:
    """Wrapper for Google Indexing API operations."""

    def __init__(self, credentials_path: Path):
        """
        Initialize Google Indexing API client.

        Args:
            credentials_path: Path to service account JSON credentials
        """
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {credentials_path}\n"
                f"Please follow setup instructions in README.md"
            )

        self.credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path), scopes=SCOPES
        )
        self.service = build("indexing", "v3", credentials=self.credentials)

    def notify_url_updated(self, url: str) -> Dict:
        """
        Notify Google that a URL has been updated.

        Args:
            url: Full URL to notify

        Returns:
            API response dictionary
        """
        body = {"url": url, "type": "URL_UPDATED"}

        try:
            response = self.service.urlNotifications().publish(body=body).execute()
            print(f"✅ Indexed: {url}")
            return response
        except HttpError as e:
            print(f"❌ Failed to index {url}: {e}")
            return {"error": str(e)}

    def get_url_status(self, url: str) -> Dict:
        """
        Get the indexing status of a URL.

        Args:
            url: Full URL to check

        Returns:
            Status dictionary
        """
        try:
            response = (
                self.service.urlNotifications()
                .getMetadata(url=url)
                .execute()
            )
            return response
        except HttpError as e:
            return {"error": str(e)}

    def batch_notify(self, urls: List[str]) -> Dict[str, Dict]:
        """
        Notify multiple URLs in batch.

        Args:
            urls: List of full URLs to notify

        Returns:
            Dictionary mapping URLs to their responses
        """
        results = {}
        for url in urls:
            results[url] = self.notify_url_updated(url)
        return results


class IndexedURLTracker:
    """Track which URLs have been indexed."""

    def __init__(self, tracking_file: Path):
        """
        Initialize URL tracker.

        Args:
            tracking_file: Path to JSON file storing indexed URLs
        """
        self.tracking_file = tracking_file
        self.data = self._load()

    def _load(self) -> Dict:
        """Load indexed URLs from file."""
        if not self.tracking_file.exists():
            self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
            return {"indexed_urls": {}, "last_updated": None}

        with open(self.tracking_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        """Save indexed URLs to file."""
        with open(self.tracking_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def is_indexed(self, url: str) -> bool:
        """Check if URL has been indexed."""
        return url in self.data["indexed_urls"]

    def mark_indexed(self, url: str):
        """Mark URL as indexed."""
        self.data["indexed_urls"][url] = {
            "timestamp": datetime.now().isoformat(),
            "status": "indexed",
        }
        self.data["last_updated"] = datetime.now().isoformat()
        self._save()

    def get_recent_indexed(self, days: int = 7) -> List[str]:
        """Get URLs indexed in the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []

        for url, data in self.data["indexed_urls"].items():
            timestamp = datetime.fromisoformat(data["timestamp"])
            if timestamp >= cutoff:
                recent.append(url)

        return recent


def get_recent_posts(days: int = 1) -> List[str]:
    """
    Get URLs of recently published posts.

    Args:
        days: Number of days to look back

    Returns:
        List of full URLs for recent posts
    """
    content_dir = PROJECT_ROOT / "content"
    cutoff = datetime.now() - timedelta(days=days)
    recent_urls = []

    # Scan all language directories
    for lang_dir in ["en", "ko"]:
        lang_path = content_dir / lang_dir
        if not lang_path.exists():
            continue

        # Scan all category directories
        for category_dir in lang_path.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("."):
                continue

            # Find recent markdown files
            for md_file in category_dir.glob("*.md"):
                # Check modification time
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                if mtime >= cutoff:
                    # Build URL from file path
                    # e.g., content/en/tech/2026-02-03-article.md -> /tech/2026-02-03-article/
                    slug = md_file.stem  # Remove .md extension
                    category = category_dir.name

                    if lang_dir == "en":
                        url = f"{BASE_URL}/{category}/{slug}/"
                    else:
                        url = f"{BASE_URL}/{lang_dir}/{category}/{slug}/"

                    recent_urls.append(url)

    return recent_urls


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Notify Google Indexing API about new/updated URLs"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Look back N days for recent posts (default: 1)",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Index a specific URL instead of scanning recent posts",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-index even if already indexed",
    )
    parser.add_argument(
        "--status",
        type=str,
        help="Check indexing status of a specific URL",
    )

    args = parser.parse_args()

    # Check for credentials
    if not CREDENTIALS_FILE.exists():
        print("❌ Google Indexing API credentials not found!")
        print(f"   Expected location: {CREDENTIALS_FILE}")
        print("\n📖 Setup instructions:")
        print("   1. Go to https://console.cloud.google.com/")
        print("   2. Create a new project or select existing")
        print("   3. Enable Google Indexing API")
        print("   4. Create service account and download JSON key")
        print(f"   5. Save as: {CREDENTIALS_FILE}")
        print("   6. Add service account email to Search Console")
        sys.exit(1)

    # Initialize API and tracker
    api = GoogleIndexingAPI(CREDENTIALS_FILE)
    tracker = IndexedURLTracker(INDEXED_URLS_FILE)

    # Handle status check
    if args.status:
        print(f"🔍 Checking status: {args.status}")
        status = api.get_url_status(args.status)
        print(json.dumps(status, indent=2))
        return

    # Handle single URL indexing
    if args.url:
        if not args.force and tracker.is_indexed(args.url):
            print(f"⏭️  Already indexed: {args.url}")
            print("   Use --force to re-index")
        else:
            api.notify_url_updated(args.url)
            tracker.mark_indexed(args.url)
        return

    # Scan for recent posts
    print(f"🔍 Scanning for posts from last {args.days} day(s)...")
    recent_urls = get_recent_posts(args.days)

    if not recent_urls:
        print("ℹ️  No recent posts found")
        return

    print(f"📝 Found {len(recent_urls)} recent post(s)")

    # Filter out already indexed (unless force)
    if not args.force:
        urls_to_index = [url for url in recent_urls if not tracker.is_indexed(url)]
        already_indexed = len(recent_urls) - len(urls_to_index)

        if already_indexed > 0:
            print(f"⏭️  Skipping {already_indexed} already indexed URL(s)")

        recent_urls = urls_to_index

    if not recent_urls:
        print("✅ All recent posts already indexed")
        return

    # Notify Google
    print(f"📤 Indexing {len(recent_urls)} URL(s)...")
    results = api.batch_notify(recent_urls)

    # Track successful indexing
    success_count = 0
    for url, response in results.items():
        if "error" not in response:
            tracker.mark_indexed(url)
            success_count += 1

    print(f"\n✅ Successfully indexed {success_count}/{len(recent_urls)} URL(s)")

    # Show recent indexing stats
    recent_indexed = tracker.get_recent_indexed(7)
    print(f"📊 Total indexed in last 7 days: {len(recent_indexed)}")


if __name__ == "__main__":
    main()
