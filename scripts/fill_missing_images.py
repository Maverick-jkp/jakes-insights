#!/usr/bin/env python3
"""
Fill missing images for posts with image: ""
Downloads unique images from Unsplash, avoiding duplicates via MD5 hash check.
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

import requests

# Load env
from dotenv import load_dotenv
load_dotenv()

UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
IMAGES_DIR = Path("static/images")
CONTENT_DIR = Path("content")


def get_existing_hashes():
    """Get MD5 hashes of all existing images."""
    hashes = set()
    for img in IMAGES_DIR.glob("*.jpg"):
        with open(img, "rb") as f:
            hashes.add(hashlib.md5(f.read()).hexdigest())
    return hashes


def extract_info(md_path):
    """Extract keyword, category, date from a post file."""
    text = md_path.read_text(encoding="utf-8")

    # Get category from frontmatter
    cat_match = re.search(r'categories: \["(.+?)"\]', text)
    category = cat_match.group(1) if cat_match else "tech"

    # Get title for search query
    title_match = re.search(r'^title: "(.+?)"', text, re.MULTILINE)
    title = title_match.group(1) if title_match else ""

    # Get date
    date_match = re.search(r'^date: (\d{4}-\d{2}-\d{2})', text, re.MULTILINE)
    date_str = date_match.group(1).replace("-", "") if date_match else "20260101"

    # Get keyword from filename
    fname = md_path.stem  # e.g. 2026-01-24-전남대
    keyword = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', fname)

    return keyword, category, title, date_str


def search_unsplash(query, existing_hashes, per_page=5):
    """Search Unsplash and return first non-duplicate result."""
    headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}

    resp = requests.get(
        "https://api.unsplash.com/search/photos",
        params={"query": query, "per_page": per_page, "orientation": "landscape"},
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])

    for photo in results:
        # Download and check hash
        img_url = photo["urls"]["regular"] + "&w=1200&q=85&fm=jpg"
        img_resp = requests.get(img_url, timeout=15)
        img_resp.raise_for_status()

        img_hash = hashlib.md5(img_resp.content).hexdigest()
        if img_hash not in existing_hashes:
            # Trigger download tracking (Unsplash API terms)
            dl_url = photo.get("links", {}).get("download_location")
            if dl_url:
                requests.get(dl_url, headers=headers, timeout=5)

            return img_resp.content, img_hash, {
                "photographer": photo["user"]["name"],
                "photographer_url": photo["user"]["links"]["html"],
                "unsplash_url": photo["links"]["html"],
            }

    return None, None, None


def build_query(keyword, category, title):
    """Build English search query from keyword/title."""
    # Simple translation map for common CJK terms
    translations = {
        "tech": "technology digital", "business": "business corporate",
        "society": "society community", "entertainment": "entertainment media",
        "sports": "sports athletic",
    }

    # Try ASCII words from title first
    ascii_words = []
    for word in title.split():
        try:
            word.encode("ascii")
            if len(word) > 2:
                ascii_words.append(word)
        except UnicodeEncodeError:
            pass

    base = translations.get(category, "technology")
    if ascii_words:
        return " ".join(ascii_words[:3]) + " " + base.split()[0]
    return base


def main():
    if not UNSPLASH_KEY:
        print("ERROR: UNSPLASH_ACCESS_KEY not set")
        sys.exit(1)

    # Find posts with empty image
    empty_posts = []
    for md_file in CONTENT_DIR.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        if re.search(r'^image: ""', text, re.MULTILINE):
            empty_posts.append(md_file)

    print(f"Found {len(empty_posts)} posts with empty images")

    if not empty_posts:
        return

    existing_hashes = get_existing_hashes()
    print(f"Existing images: {len(existing_hashes)} unique hashes")

    fixed = 0
    failed = 0

    for md_file in sorted(empty_posts):
        keyword, category, title, date_str = extract_info(md_file)
        query = build_query(keyword, category, title)

        print(f"\n[{fixed+failed+1}/{len(empty_posts)}] {md_file.name}")
        print(f"  Query: {query}")

        img_data, img_hash, credit = search_unsplash(query, existing_hashes)

        if not img_data:
            # Fallback: pure category search
            print(f"  Retrying with category only: {category}")
            img_data, img_hash, credit = search_unsplash(category, existing_hashes, per_page=10)

        if not img_data:
            print(f"  FAILED - no unique image found")
            failed += 1
            continue

        # Save image
        slug = re.sub(r'[^\w\s-]', '', keyword, flags=re.UNICODE).replace(' ', '-')[:30]
        filename = f"{date_str}-{slug}.jpg"
        filepath = IMAGES_DIR / filename

        filepath.write_bytes(img_data)
        existing_hashes.add(img_hash)

        # Update post frontmatter
        text = md_file.read_text(encoding="utf-8")
        image_path = f"/images/{filename}"
        text = re.sub(r'^image: ""', f'image: "{image_path}"', text, count=1, flags=re.MULTILINE)

        # Add credit if not already present
        if credit and "Photo by" not in text:
            credit_line = f"\n\n---\n\n*Photo by [{credit['photographer']}]({credit['photographer_url']}) on [Unsplash]({credit['unsplash_url']})*\n"
            text = text.rstrip() + credit_line

        md_file.write_text(text, encoding="utf-8")

        size_kb = len(img_data) / 1024
        print(f"  OK: {filename} ({size_kb:.0f}KB)")
        fixed += 1

    print(f"\n{'='*50}")
    print(f"Fixed: {fixed}/{len(empty_posts)}")
    if failed:
        print(f"Failed: {failed}")


if __name__ == "__main__":
    main()
