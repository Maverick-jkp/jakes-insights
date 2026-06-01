#!/usr/bin/env python3
"""
One-shot migration: collapse the old (categories=tech, subtopic-* tag) + the
side-income directory into the new five top-level categories.

New categories:
  - ai          (subtopic "ai")
  - productivity (subtopic "devtools" or "web")
  - tech-economy (subtopic "cloud", "data", "security", "mobile", or untagged tech)
  - buying-guide (no existing posts — placeholder, populated by new posts only)
  - side-income (everything currently under content/{en,ko}/side-income/)

What this script does for each post:
  1. Reads frontmatter
  2. Decides the new category from current subtopic / path
  3. Rewrites `categories: ["tech"]` (or the side-income equivalent) to the new
     category — Hugo's taxonomy entry
  4. MOVES the file from content/{lang}/tech/ to content/{lang}/<new>/
  5. Preserves the date-prefixed slug so the *trailing* URL path stays the same
     (e.g. /tech/2026-05-30-foo/ becomes /ai/2026-05-30-foo/). The full URL DOES
     change, but the slug part does not, which keeps redirect generation simple.

Outputs a redirect map suitable for appending to static/_redirects so we
preserve every old URL.

Run with --dry-run first to see the plan; then run without it to actually
move files.
"""

from __future__ import annotations

import argparse
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional, Tuple


SUBTOPIC_TO_NEW_CATEGORY = {
    "ai": "ai",
    "devtools": "productivity",
    "web": "productivity",
    "cloud": "tech-economy",
    "data": "tech-economy",
    "security": "tech-economy",
    "mobile": "tech-economy",
    # The side-income subtopics all collapse into the side-income category.
    "freelancing": "side-income",
    "saas": "side-income",
    "digital": "side-income",
    "digital-products": "side-income",
    "passive": "side-income",
    "content": "side-income",
    "jobs": "side-income",
    "general": "side-income",
    "ai-income": "side-income",
}

# If a tech post has no subtopic tag at all, treat it as tech-economy. None of
# the new buying-guide content exists yet; that category starts empty.
DEFAULT_NEW_CATEGORY_FOR_TECH = "tech-economy"
DEFAULT_NEW_CATEGORY_FOR_SIDE_INCOME = "side-income"


def detect_subtopic(text: str) -> Optional[str]:
    """Return the first subtopic-* tag found in frontmatter, or None."""
    m = re.search(r'^tags:\s*\[(.*?)\]', text, re.MULTILINE)
    if not m:
        return None
    sub_match = re.search(r'subtopic-(\w[\w-]*)', m.group(1))
    if not sub_match:
        return None
    return sub_match.group(1)


# Hand-picked keyword fallbacks. If the subtopic tag is missing or maps to the
# wrong bucket, these keywords (anywhere in title/filename/tags) override it.
# Order matters: the first list to match wins.
KEYWORD_FALLBACKS = [
    # AI: any post whose title or filename calls out an AI product, technique,
    # or vendor → AI bucket. Catches "cursor-ai-editor" that the subtopic
    # tagger mislabeled as devtools.
    ("ai", [
        "chatgpt", "gpt-", "gpt4", "gpt-4", "claude", "gemini", "anthropic",
        "openai", "midjourney", "stable-diffusion", "stable diffusion",
        "llama", "mistral", "ollama", "rag ", "rag-", "embedding", "vector-db",
        "fine-tuning", "fine tuning", "llm ", "llm-", "ai-editor", "ai editor",
        "ai-coding", "ai coding", "prompt-engineering", "프롬프트",
        "ai-", "-ai-", " ai ", "인공지능",
    ]),
    # Productivity tools: Notion / Slack / docs / "productivity"
    ("productivity", [
        "notion", "slack", "linear", "asana", "trello", "obsidian",
        "google-docs", "google docs", "todo", "노션", "슬랙",
    ]),
    # Buying-decision posts: "vs", "worth it", "review", "best"
    # (kept narrow so we don't sweep in random comparison engineering posts)
    ("buying-guide", [
        "worth-it", "worth it", "값어치", "살까", "살만한", "구매-가이드", "구매 가이드",
    ]),
]


def keyword_fallback(post_path: Path, text: str) -> Optional[str]:
    """Try keyword-based classification when subtopic alone isn't trustworthy.

    Only inspects the filename slug and the frontmatter title/tags (NOT the
    body) so that incidental mentions of "AI" in the body of a non-AI post
    don't drag it into the AI bucket.
    """
    title_match = re.search(r'^title:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
    tags_match = re.search(r'^tags:\s*\[(.*?)\]', text, re.MULTILINE)
    title = title_match.group(1) if title_match else ""
    tags = tags_match.group(1) if tags_match else ""
    haystack = (post_path.stem + " " + title + " " + tags).lower()
    for category, words in KEYWORD_FALLBACKS:
        if any(w in haystack for w in words):
            return category
    return None


def decide_new_category(post_path: Path, text: str) -> str:
    """Pick the new top-level category for a post."""
    if "/side-income/" in str(post_path):
        return DEFAULT_NEW_CATEGORY_FOR_SIDE_INCOME

    # Keyword fallback runs FIRST so a wrong subtopic tag doesn't override an
    # obvious AI/productivity signal in the title.
    by_keyword = keyword_fallback(post_path, text)
    if by_keyword:
        return by_keyword

    subtopic = detect_subtopic(text)
    if subtopic and subtopic in SUBTOPIC_TO_NEW_CATEGORY:
        return SUBTOPIC_TO_NEW_CATEGORY[subtopic]
    return DEFAULT_NEW_CATEGORY_FOR_TECH


def rewrite_categories_field(text: str, new_category: str) -> str:
    """Replace the `categories: [...]` line in the frontmatter."""
    pattern = r'^categories:\s*\[.*?\]'
    replacement = f'categories: ["{new_category}"]'
    new_text, n = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if n == 0:
        # No categories line — insert it just after the title line.
        new_text = re.sub(
            r'^(title:.*?)$',
            rf'\1\ncategories: ["{new_category}"]',
            text,
            count=1,
            flags=re.MULTILINE,
        )
    return new_text


def old_url_path(post_path: Path) -> str:
    """Build the URL path that this file currently resolves to."""
    parts = post_path.parts
    try:
        content_idx = parts.index("content")
    except ValueError:
        return ""
    rel = parts[content_idx + 1:]
    lang = rel[0]
    section = rel[1]
    slug = post_path.stem  # e.g. 2026-05-30-foo
    if lang == "en":
        return f"/{section}/{slug}/"
    return f"/{lang}/{section}/{slug}/"


def new_url_path(post_path: Path, new_category: str) -> str:
    """Build the URL path the file will resolve to after migration."""
    parts = post_path.parts
    content_idx = parts.index("content")
    lang = parts[content_idx + 1]
    slug = post_path.stem
    if lang == "en":
        return f"/{new_category}/{slug}/"
    return f"/{lang}/{new_category}/{slug}/"


def plan_migration(repo_root: Path) -> list[Tuple[Path, Path, str, str, str]]:
    """Return a list of (old_path, new_path, new_category, old_url, new_url)."""
    plan: list[Tuple[Path, Path, str, str, str]] = []
    for post_path in sorted((repo_root / "content").rglob("*.md")):
        # Skip the section landing pages and standalone static pages
        if post_path.name == "_index.md":
            continue
        if post_path.stem in {"about", "contact", "privacy", "all-posts"}:
            continue
        text = post_path.read_text(encoding="utf-8")
        new_cat = decide_new_category(post_path, text)
        old_url = old_url_path(post_path)
        new_url = new_url_path(post_path, new_cat)
        if old_url == new_url:
            continue  # already in place
        # Build destination path: same lang, swap section to new_cat
        parts = list(post_path.parts)
        content_idx = parts.index("content")
        parts[content_idx + 2] = new_cat
        new_path = Path(*parts)
        plan.append((post_path, new_path, new_cat, old_url, new_url))
    return plan


def apply_migration(plan: list, repo_root: Path) -> None:
    for old_path, new_path, new_cat, _old_url, _new_url in plan:
        new_path.parent.mkdir(parents=True, exist_ok=True)
        text = old_path.read_text(encoding="utf-8")
        text = rewrite_categories_field(text, new_cat)
        new_path.write_text(text, encoding="utf-8")
        if new_path != old_path:
            old_path.unlink()


def write_redirects(plan: list, output_path: Path) -> None:
    """Append redirects (one per migrated post) so old URLs still resolve."""
    lines = ["", "# Auto-generated by migrate_categories.py — old URLs → new category routes"]
    for _o, _n, _c, old_url, new_url in plan:
        lines.append(f"{old_url} {new_url} 301")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Plan only, don't touch files")
    parser.add_argument("--redirects-out", default="migration_redirects.txt",
                        help="Where to write the generated redirect rules")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    plan = plan_migration(repo_root)

    counts = Counter(new_cat for _o, _n, new_cat, _ou, _nu in plan)
    by_lang = defaultdict(Counter)
    for _o, new_path, new_cat, _ou, _nu in plan:
        lang = new_path.parts[new_path.parts.index("content") + 1]
        by_lang[lang][new_cat] += 1

    print(f"Migration plan: {len(plan)} files to move")
    print()
    print("Per new category:")
    for cat, n in counts.most_common():
        print(f"  {cat:18} {n}")
    print()
    print("Per language × new category:")
    for lang, cnt in sorted(by_lang.items()):
        print(f"  {lang}:")
        for cat, n in cnt.most_common():
            print(f"    {cat:18} {n}")
    print()

    if args.dry_run:
        print("Sample (first 10):")
        for old_path, new_path, new_cat, old_url, new_url in plan[:10]:
            print(f"  {old_url}  →  {new_url}")
        print()
        print("(dry-run; nothing changed. Re-run without --dry-run to apply.)")
        return 0

    apply_migration(plan, repo_root)
    redirects_path = repo_root / args.redirects_out
    write_redirects(plan, redirects_path)
    print(f"✅ Moved {len(plan)} files.")
    print(f"✅ Wrote redirect rules to {redirects_path}")
    print()
    print("Next steps:")
    print(f"  1. Review {args.redirects_out} and append its contents to static/_redirects")
    print("  2. Update hugo.toml menus to point at the new categories")
    print("  3. Run a Hugo build to confirm the new layout renders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
