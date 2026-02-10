#!/usr/bin/env python3
"""
Internal Linker - Automatically add internal links to related posts

This script:
1. Finds related posts based on category and tags
2. Generates "Related Posts" section
3. Adds internal links to improve SEO and user engagement

Usage:
    from internal_linker import InternalLinker
    linker = InternalLinker()
    updated_content = linker.add_related_posts(content, category, tags, lang)
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter


class InternalLinker:
    def __init__(self, content_dir: str = "content"):
        """Initialize internal linker with content directory"""
        self.content_dir = Path(content_dir)
        self.posts_cache = self._build_posts_index()

    def _build_posts_index(self) -> Dict[str, List[Dict]]:
        """Build index of all posts grouped by language"""
        index = {"en": [], "ko": []}

        for lang in ["en", "ko"]:
            lang_dir = self.content_dir / lang
            if not lang_dir.exists():
                continue

            # Scan all categories
            for category_dir in lang_dir.iterdir():
                if not category_dir.is_dir():
                    continue

                category = category_dir.name

                # Scan all posts in category
                for post_file in category_dir.glob("*.md"):
                    try:
                        with open(post_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Extract frontmatter
                        frontmatter = self._extract_frontmatter(content)
                        if not frontmatter:
                            continue

                        # Skip draft posts
                        if frontmatter.get('draft', False):
                            continue

                        # Build post metadata
                        post_meta = {
                            "title": frontmatter.get('title', ''),
                            "category": category,
                            "tags": frontmatter.get('tags', []),
                            "date": frontmatter.get('date', ''),
                            "file_path": str(post_file.relative_to(self.content_dir)),
                            "url_path": self._get_url_path(post_file, lang, category)
                        }

                        index[lang].append(post_meta)

                    except Exception as e:
                        print(f"⚠️  Error indexing {post_file}: {e}")
                        continue

        # Sort by date (newest first)
        for lang in index:
            index[lang].sort(key=lambda x: x.get('date', ''), reverse=True)

        print(f"✅ Indexed {sum(len(posts) for posts in index.values())} posts")
        print(f"   EN: {len(index['en'])}, KO: {len(index['ko'])}")

        return index

    def _extract_frontmatter(self, content: str) -> Dict:
        """Extract YAML frontmatter from markdown content"""
        # Match frontmatter between --- delimiters
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return {}

        frontmatter_text = match.group(1)
        frontmatter = {}

        # Simple YAML parsing (basic fields only)
        for line in frontmatter_text.split('\n'):
            if ':' not in line:
                continue

            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Handle lists (tags, categories)
            if value.startswith('[') and value.endswith(']'):
                # Parse list: ["tag1", "tag2"]
                value = [tag.strip(' "\'') for tag in value.strip('[]').split(',')]
            # Handle booleans
            elif value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            # Handle quoted strings
            elif value.startswith('"') and value.endswith('"'):
                value = value.strip('"')

            frontmatter[key] = value

        return frontmatter

    def _get_url_path(self, file_path: Path, lang: str, category: str) -> str:
        """Generate URL path for a post"""
        # Example: content/en/tech/2026-01-28-arc-raiders.md
        # -> /en/tech/arc-raiders/
        filename = file_path.stem  # Remove .md extension

        # Remove date prefix (YYYY-MM-DD-)
        filename = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', filename)

        return f"/{lang}/{category}/{filename}/"

    def find_related_posts(self, category: str, tags: List[str], lang: str,
                           current_file: str = None, limit: int = 5) -> List[Dict]:
        """Find related posts based on category and tags"""
        posts = self.posts_cache.get(lang, [])

        if not posts:
            return []

        # Score each post by relevance
        scored_posts = []

        for post in posts:
            # Skip current post
            if current_file and post['file_path'] == current_file:
                continue

            score = 0

            # Same category: +10 points
            if post['category'] == category:
                score += 10

            # Shared tags: +5 points per tag
            post_tags = post.get('tags', [])
            shared_tags = set(tags) & set(post_tags)
            score += len(shared_tags) * 5

            if score > 0:
                scored_posts.append((score, post))

        # Sort by score (highest first)
        scored_posts.sort(key=lambda x: x[0], reverse=True)

        # Return top N posts
        return [post for score, post in scored_posts[:limit]]

    def generate_related_section(self, related_posts: List[Dict], lang: str) -> str:
        """Generate 'Related Posts' section in markdown"""
        if not related_posts:
            return ""

        # Language-specific headers
        headers = {
            "en": "## Related Posts",
            "ko": "## 관련 글",
        }

        header = headers.get(lang, "## Related Posts")
        lines = ["\n", header, "\n"]

        for post in related_posts:
            title = post.get('title', 'Untitled')
            url = post.get('url_path', '#')
            lines.append(f"- [{title}]({url})")

        lines.append("\n")
        return "\n".join(lines)

    def add_related_posts(self, content: str, category: str, tags: List[str],
                          lang: str, current_file: str = None) -> str:
        """Add related posts section to content"""
        # Find related posts
        related_posts = self.find_related_posts(category, tags, lang, current_file)

        if not related_posts:
            return content

        # Generate related section
        related_section = self.generate_related_section(related_posts, lang)

        # Check if content already has related section
        if re.search(r'## Related Posts|## 관련 글', content):
            # Replace existing section
            content = re.sub(
                r'(## Related Posts|## 관련 글).*?(?=\n##|\Z)',
                related_section,
                content,
                flags=re.DOTALL
            )
        else:
            # Append before references section (if exists)
            if '## References' in content or '## 참고자료' in content:
                # Insert before references
                content = re.sub(
                    r'(## References|## 참고자료)',
                    f'{related_section}\\1',
                    content,
                    count=1
                )
            else:
                # Append at the end
                content += related_section

        return content


# CLI interface
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Add internal links to blog posts")
    parser.add_argument('--file', type=str, help="Specific file to process")
    parser.add_argument('--category', type=str, help="Category for filtering")
    parser.add_argument('--lang', type=str, choices=['en', 'ko'], help="Language")
    parser.add_argument('--rebuild-index', action='store_true', help="Rebuild posts index")
    parser.add_argument('--dry-run', action='store_true', help="Preview without writing")
    args = parser.parse_args()

    linker = InternalLinker()

    if args.rebuild_index:
        print("✅ Posts index rebuilt")
        return

    if args.file:
        # Process single file
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract metadata
        frontmatter = linker._extract_frontmatter(content)
        category = frontmatter.get('category', args.category)
        tags = frontmatter.get('tags', [])
        lang = args.lang or file_path.parts[1]  # Get from path: content/en/...

        # Add related posts
        updated_content = linker.add_related_posts(
            content, category, tags, lang, str(file_path.relative_to("content"))
        )

        if args.dry_run:
            print("\n" + "="*60)
            print("PREVIEW")
            print("="*60)
            print(updated_content)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ Updated: {file_path}")
    else:
        print("Usage: python internal_linker.py --file path/to/post.md")
        print("   or: python internal_linker.py --rebuild-index")


if __name__ == "__main__":
    main()
