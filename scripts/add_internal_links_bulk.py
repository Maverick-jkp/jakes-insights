#!/usr/bin/env python3
"""
Bulk add Related Posts sections to all existing posts that lack them.
Runs internal_linker.py logic across all EN and KO content.
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from internal_linker import InternalLinker

CONTENT_DIR = Path("content")
SKIP_FILES = {"_index.md", "about.md", "privacy.md", "all-posts.md", "contact.md"}


def already_has_related(content: str) -> bool:
    return bool(re.search(r'## Related Posts|## 관련 글', content))


def main():
    linker = InternalLinker()
    updated = 0
    skipped_already = 0
    skipped_short = 0
    failed = 0

    files = []
    for lang in ["en", "ko"]:
        lang_path = CONTENT_DIR / lang
        if not lang_path.exists():
            continue
        for md_file in sorted(lang_path.rglob("*.md")):
            if md_file.name in SKIP_FILES:
                continue
            files.append((lang, md_file))

    print(f"Processing {len(files)} files...\n")

    for lang, md_file in files:
        try:
            content = md_file.read_text(encoding="utf-8")

            if already_has_related(content):
                skipped_already += 1
                continue

            # Skip very short posts
            word_count = len(content.split())
            if word_count < 200:
                skipped_short += 1
                continue

            fm = linker._extract_frontmatter(content)
            category = fm.get("categories", [None])[0] if fm.get("categories") else md_file.parent.name
            tags = fm.get("tags", [])

            rel_path = str(md_file.relative_to(CONTENT_DIR))
            new_content = linker.add_related_posts(content, category, tags, lang, rel_path)

            if new_content != content:
                md_file.write_text(new_content, encoding="utf-8")
                print(f"  ✅ {md_file.relative_to(CONTENT_DIR)}")
                updated += 1
            else:
                skipped_already += 1

        except Exception as e:
            print(f"  ❌ {md_file.name}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"  Updated:          {updated}")
    print(f"  Already had links: {skipped_already}")
    print(f"  Too short:        {skipped_short}")
    print(f"  Failed:           {failed}")


if __name__ == "__main__":
    main()
