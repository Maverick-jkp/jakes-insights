#!/usr/bin/env python3
"""
Image Deduplication Utility
Finds and removes duplicate images based on MD5 hash.

Usage:
    python scripts/dedupe_images.py --dry-run   # Show duplicates without deleting
    python scripts/dedupe_images.py             # Remove duplicates
"""

import argparse
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Dict, List


def calculate_md5(filepath: Path) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def find_duplicates(images_dir: Path) -> Dict[str, List[Path]]:
    """
    Find duplicate images by MD5 hash.

    Returns:
        Dictionary mapping hash to list of file paths with that hash
    """
    hash_to_files = defaultdict(list)

    print(f"🔍 Scanning images in {images_dir}...")

    for image_file in images_dir.glob("*.jpg"):
        if image_file.is_file():
            file_hash = calculate_md5(image_file)
            hash_to_files[file_hash].append(image_file)

    # Filter to only duplicates
    duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}

    return duplicates


def update_image_references(
    content_dir: Path, old_file: Path, new_file: Path
) -> List[Path]:
    """
    Update markdown posts that reference old_file to point to new_file.
    Handles both frontmatter `image:` fields and inline `![...](path)` syntax.

    Returns list of post paths that were updated.
    """
    # Build path strings as they appear in posts (e.g. /images/foo.jpg)
    old_ref = f"/images/{old_file.name}"
    new_ref = f"/images/{new_file.name}"

    if old_ref == new_ref:
        return []

    updated = []
    for md_file in content_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        if old_ref not in text:
            continue
        new_text = text.replace(old_ref, new_ref)
        md_file.write_text(new_text, encoding="utf-8")
        updated.append(md_file)

    return updated


def dedupe_images(dry_run: bool = False):
    """
    Find and optionally remove duplicate images.

    Args:
        dry_run: If True, only show duplicates without deleting
    """
    images_dir = Path("static/images")

    if not images_dir.exists():
        print(f"❌ Images directory not found: {images_dir}")
        return

    duplicates = find_duplicates(images_dir)

    if not duplicates:
        print("✅ No duplicate images found!")
        return

    print(f"\n📊 Found {len(duplicates)} groups of duplicate images:")
    print()

    total_files = sum(len(files) for files in duplicates.values())
    files_to_remove = total_files - len(duplicates)  # Keep one from each group

    for file_hash, files in duplicates.items():
        # Sort by modification time (keep oldest)
        files.sort(key=lambda f: f.stat().st_mtime)

        print(f"Hash: {file_hash[:8]}... ({len(files)} files)")
        for i, filepath in enumerate(files):
            size_kb = filepath.stat().st_size / 1024
            keep = "✓ KEEP" if i == 0 else "✗ REMOVE" if not dry_run else "  (would remove)"
            print(f"  {keep:15} {filepath.name:50} ({size_kb:6.1f} KB)")

        print()

    print(f"📈 Summary:")
    print(f"   Total duplicate files: {total_files}")
    print(f"   Files to keep: {len(duplicates)}")
    print(f"   Files to remove: {files_to_remove}")

    if dry_run:
        print("\n⚠️  DRY RUN - No files deleted")
        print("   Run without --dry-run to remove duplicates")
        return

    # Update references and remove duplicates (keep first/oldest file)
    content_dir = Path("content")
    removed_count = 0
    for file_hash, files in duplicates.items():
        files.sort(key=lambda f: f.stat().st_mtime)
        kept_file = files[0]
        for filepath in files[1:]:  # Skip first (keep oldest)
            # Update posts referencing the file about to be deleted
            updated_posts = update_image_references(
                content_dir, filepath, kept_file
            )
            for post in updated_posts:
                print(f"📝 Updated reference in: {post}")
            try:
                filepath.unlink()
                removed_count += 1
                print(f"🗑️  Removed: {filepath.name}")
            except Exception as e:
                print(f"❌ Failed to remove {filepath.name}: {e}")

    print(f"\n✅ Removed {removed_count} duplicate files")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Find and remove duplicate images based on MD5 hash"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show duplicates without deleting files",
    )

    args = parser.parse_args()

    dedupe_images(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
