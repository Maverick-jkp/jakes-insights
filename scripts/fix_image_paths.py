#!/usr/bin/env python3
"""Update image frontmatter paths from .jpg/.jpeg/.png to .webp"""
import re
from pathlib import Path

content_dir = Path(__file__).parent.parent / "content"
changed = 0

for md in content_dir.rglob("*.md"):
    text = md.read_text(encoding="utf-8")
    # Match: image: "/images/foo.jpg" or image: /images/foo.jpg
    new_text = re.sub(
        r'(^image:\s*["\']?/images/[^"\'.\s]+)\.(jpg|jpeg|png)(["\']?\s*$)',
        r'\1.webp\3',
        text,
        flags=re.MULTILINE
    )
    if new_text != text:
        md.write_text(new_text, encoding="utf-8")
        changed += 1

print(f"Updated {changed} posts")
