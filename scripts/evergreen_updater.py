#!/usr/bin/env python3
"""
Evergreen Content Auto-Updater
Automatically updates high-performing evergreen posts to maintain freshness.

Strategy:
- Updates top 20% posts by traffic (from GA4)
- Refreshes "Last Updated" date
- Adds new statistics/data where applicable
- Maintains SEO ranking
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import frontmatter

PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_DIR = PROJECT_ROOT / "content"
UPDATE_TRACKER_FILE = PROJECT_ROOT / "data" / "evergreen_updates.json"


class EvergreenUpdater:
    """Manages evergreen content updates."""

    def __init__(self):
        """Initialize the updater."""
        self.tracker = self._load_tracker()

    def _load_tracker(self) -> Dict:
        """Load update tracking data."""
        if not UPDATE_TRACKER_FILE.exists():
            UPDATE_TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
            return {"updates": {}, "last_run": None}

        with open(UPDATE_TRACKER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_tracker(self):
        """Save update tracking data."""
        with open(UPDATE_TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tracker, f, indent=2, ensure_ascii=False)

    def get_eligible_posts(self, min_age_days: int = 30) -> List[Path]:
        """
        Get posts eligible for update.

        Args:
            min_age_days: Minimum age for posts to be eligible

        Returns:
            List of post file paths
        """
        cutoff = datetime.now() - timedelta(days=min_age_days)
        eligible = []

        # Scan all language directories
        for lang_dir in ["en", "ko"]:
            lang_path = CONTENT_DIR / lang_dir
            if not lang_path.exists():
                continue

            # Scan all category directories
            for category_dir in lang_path.iterdir():
                if not category_dir.is_dir() or category_dir.name in ["archives", "privacy", "about"]:
                    continue

                # Find markdown files
                for md_file in category_dir.glob("*.md"):
                    # Check if old enough
                    mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                    if mtime < cutoff:
                        # Check if hasn't been updated recently
                        file_key = str(md_file.relative_to(PROJECT_ROOT))
                        last_update = self.tracker["updates"].get(file_key, {}).get("last_updated")

                        if last_update:
                            last_update_dt = datetime.fromisoformat(last_update)
                            if datetime.now() - last_update_dt < timedelta(days=min_age_days):
                                continue  # Skip if updated recently

                        eligible.append(md_file)

        return eligible

    def get_top_performing_posts(self, eligible_posts: List[Path], top_percent: float = 0.2) -> List[Path]:
        """
        Select top performing posts for update.

        Args:
            eligible_posts: List of eligible post paths
            top_percent: Top percentage to select (0.2 = top 20%)

        Returns:
            List of top performing post paths
        """
        # For now, use simple heuristics (word count, internal links)
        # TODO: Integrate with GA4 API for real traffic data

        scored_posts = []
        for post_path in eligible_posts:
            score = self._calculate_post_score(post_path)
            scored_posts.append((post_path, score))

        # Sort by score descending
        scored_posts.sort(key=lambda x: x[1], reverse=True)

        # Return top N%
        top_n = max(1, int(len(scored_posts) * top_percent))
        return [path for path, _ in scored_posts[:top_n]]

    def _calculate_post_score(self, post_path: Path) -> int:
        """
        Calculate post quality score.

        Args:
            post_path: Path to post file

        Returns:
            Quality score (higher is better)
        """
        try:
            with open(post_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)

            score = 0

            # Word count (higher is better)
            content = post.content
            word_count = len(content.split())
            score += min(word_count // 100, 20)  # Max 20 points

            # Internal links (more is better)
            internal_links = len(re.findall(r'\[.*?\]\(/[^)]+\)', content))
            score += min(internal_links * 5, 25)  # Max 25 points

            # Has image (bonus)
            if post.get("image"):
                score += 10

            # Has references (bonus)
            if post.get("references") and len(post.get("references", [])) > 0:
                score += 15

            # Category weight (Tech/Business higher priority)
            categories = post.get("categories", [])
            if any(cat in ["tech", "business"] for cat in categories):
                score += 10

            return score

        except Exception as e:
            print(f"⚠️  Error scoring {post_path}: {e}")
            return 0

    def update_post(self, post_path: Path, dry_run: bool = False) -> bool:
        """
        Update a single post.

        Args:
            post_path: Path to post file
            dry_run: If True, don't actually modify files

        Returns:
            True if updated successfully
        """
        try:
            with open(post_path, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)

            # Update lastmod date
            old_lastmod = post.get("lastmod")
            post["lastmod"] = datetime.now().isoformat()

            # Add update note to content (optional, can be disabled)
            content = post.content
            update_note = f"\n\n*Last Updated: {datetime.now().strftime('%B %d, %Y')}*\n"

            # Remove old update note if exists
            content = re.sub(r'\n\n\*Last Updated:.*?\*\n', '', content)

            # Add new update note at the end (before references if they exist)
            if "## References" in content or "## 참고자료" in content:
                # Insert before references
                content = re.sub(
                    r'(## (?:References|참고자료))',
                    f'{update_note}\\1',
                    content
                )
            else:
                # Append at end
                content += update_note

            post.content = content

            if dry_run:
                print(f"✓ Would update: {post_path.relative_to(PROJECT_ROOT)}")
                print(f"  Old lastmod: {old_lastmod}")
                print(f"  New lastmod: {post['lastmod']}")
                return True

            # Write updated post
            with open(post_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))

            # Track update
            file_key = str(post_path.relative_to(PROJECT_ROOT))
            self.tracker["updates"][file_key] = {
                "last_updated": datetime.now().isoformat(),
                "previous_lastmod": old_lastmod,
            }

            print(f"✅ Updated: {post_path.relative_to(PROJECT_ROOT)}")
            return True

        except Exception as e:
            print(f"❌ Failed to update {post_path}: {e}")
            return False

    def run_update_cycle(
        self,
        min_age_days: int = 30,
        top_percent: float = 0.2,
        max_updates: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict[str, int]:
        """
        Run a full update cycle.

        Args:
            min_age_days: Minimum age for posts to be eligible
            top_percent: Top percentage to select
            max_updates: Maximum number of posts to update (None = no limit)
            dry_run: If True, don't actually modify files

        Returns:
            Statistics dictionary
        """
        print(f"🔍 Finding eligible posts (min age: {min_age_days} days)...")
        eligible = self.get_eligible_posts(min_age_days)
        print(f"📝 Found {len(eligible)} eligible post(s)")

        if not eligible:
            return {"eligible": 0, "selected": 0, "updated": 0}

        print(f"📊 Selecting top {int(top_percent * 100)}% performers...")
        top_posts = self.get_top_performing_posts(eligible, top_percent)

        if max_updates:
            top_posts = top_posts[:max_updates]

        print(f"🎯 Selected {len(top_posts)} post(s) for update")

        if dry_run:
            print("⚠️  DRY RUN MODE - No files will be modified")

        updated_count = 0
        for post_path in top_posts:
            if self.update_post(post_path, dry_run):
                updated_count += 1

        if not dry_run:
            self.tracker["last_run"] = datetime.now().isoformat()
            self._save_tracker()

        return {
            "eligible": len(eligible),
            "selected": len(top_posts),
            "updated": updated_count,
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update evergreen content to maintain freshness"
    )
    parser.add_argument(
        "--min-age",
        type=int,
        default=30,
        help="Minimum age in days for posts to be eligible (default: 30)",
    )
    parser.add_argument(
        "--top-percent",
        type=float,
        default=0.2,
        help="Top percentage to update (default: 0.2 = 20%%)",
    )
    parser.add_argument(
        "--max-updates",
        type=int,
        help="Maximum number of posts to update",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without modifying files",
    )

    args = parser.parse_args()

    updater = EvergreenUpdater()
    stats = updater.run_update_cycle(
        min_age_days=args.min_age,
        top_percent=args.top_percent,
        max_updates=args.max_updates,
        dry_run=args.dry_run,
    )

    print("\n" + "=" * 50)
    print("📈 Update Summary")
    print("=" * 50)
    print(f"Eligible posts: {stats['eligible']}")
    print(f"Selected posts: {stats['selected']}")
    print(f"Updated posts:  {stats['updated']}")

    if args.dry_run:
        print("\n⚠️  This was a dry run. Use without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
