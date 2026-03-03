#!/usr/bin/env python3
"""
One-time script: Fix tags in all existing posts.
- Remove long keyword phrase as first tag
- subtopic:xxx → subtopic-xxx
- Remove "tech" generic tag
- Remove stop-word fragments (3 chars or less, stop words)
- Keep technologies and meaningful terms (max 5 tags)
"""
import re
import json
from pathlib import Path

STOP_WORDS = {
    'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or',
    'is', 'are', 'was', 'how', 'what', 'why', 'when', 'with', 'using',
    'set', 'get', 'use', 'via', 'new', 'its', 'has', 'can', 'vs', 'api',
    'tech',  # too generic
}

CONTENT_DIR = Path(__file__).parent.parent / "content"


def parse_tags_line(line: str):
    """Parse YAML tags line like: tags: ["foo", "bar", "baz"]"""
    match = re.match(r'^tags:\s*(\[.*\])\s*$', line.strip())
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except Exception:
        return None


def is_long_phrase(tag: str) -> bool:
    """True if tag is a long keyword phrase (more than 3 words)."""
    return len(tag.split()) > 3


def is_stop_fragment(tag: str) -> bool:
    """True if tag is a stop word or very short meaningless fragment."""
    t = tag.lower().strip()
    return t in STOP_WORDS or (len(t) <= 3 and not t.startswith("subtopic"))


def clean_tags(tags: list) -> list:
    """Clean tag list to SEO-friendly short tags."""
    cleaned = []
    seen = set()

    for tag in tags:
        t = tag.strip()

        # Fix subtopic: → subtopic-
        if t.lower().startswith("subtopic:"):
            t = "subtopic-" + t[9:]

        # Skip long keyword phrases
        if is_long_phrase(t):
            continue

        # Skip stop word fragments
        if is_stop_fragment(t):
            continue

        # Deduplicate (case-insensitive)
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)

        cleaned.append(t)

    return cleaned[:5]


def fix_file(path: Path) -> bool:
    """Fix tags in a single markdown file. Returns True if changed."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    changed = False
    new_lines = []
    in_frontmatter = False
    frontmatter_count = 0

    for line in lines:
        if line.strip() == "---":
            frontmatter_count += 1
            in_frontmatter = frontmatter_count == 1
            new_lines.append(line)
            continue

        if in_frontmatter and frontmatter_count >= 2:
            in_frontmatter = False

        if in_frontmatter and line.strip().startswith("tags:"):
            tags = parse_tags_line(line)
            if tags is not None:
                new_tags = clean_tags(tags)
                if new_tags != tags:
                    new_line = f'tags: {json.dumps(new_tags, ensure_ascii=False)}'
                    new_lines.append(new_line)
                    changed = True
                    continue

        new_lines.append(line)

    if changed:
        path.write_text("\n".join(new_lines), encoding="utf-8")

    return changed


def main():
    md_files = list(CONTENT_DIR.rglob("*.md"))
    md_files = [f for f in md_files if f.name != "_index.md"]

    changed_count = 0
    for f in sorted(md_files):
        if fix_file(f):
            changed_count += 1
            print(f"  fixed: {f.relative_to(CONTENT_DIR)}")

    print(f"\nDone: {changed_count}/{len(md_files)} files updated.")


if __name__ == "__main__":
    main()
