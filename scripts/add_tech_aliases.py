#!/usr/bin/env python3
"""
Add Hugo `aliases` to each post that was migrated out of the retired /tech/
section, so Hugo generates the old /tech/<slug>/ redirect pages at build time.

Why: Cloudflare Pages Free plan silently applies only the first ~100 rules in
_redirects. We had 837 individual /tech/ -> /<cat>/ rules; everything past the
cutoff 404'd (surfaced by GSC + GA4 404 spike). Moving these redirects into
Hugo aliases removes them from _redirects entirely, permanently fixing the cap.

Idempotent: skips a post if the alias is already present.
"""
import re
import os
import sys
from collections import defaultdict

REDIRECTS = "static/_redirects"
SRC_RE = re.compile(r'^(/(?:ko/)?tech/\S+)\s+(\S+)\s+301')


def resolve(dst: str) -> str:
    p = dst.strip('/').strip()
    if p.startswith('ko/'):
        return 'content/ko/' + p[len('ko/'):] + '.md'
    return 'content/en/' + p + '.md'


def build_mapping():
    mapping = defaultdict(set)
    with open(REDIRECTS, encoding='utf-8') as f:
        for line in f:
            m = SRC_RE.match(line.strip())
            if not m:
                continue
            old, new = m.group(1), m.group(2)
            target = resolve(new)
            if old.startswith('/ko/'):
                # KO posts: store BOTH the bare /tech/ path and the /ko/tech/ path.
                # Local Hugo (v0.156) auto-prefixes the language, so /tech/ ->
                # /ko/tech/; Cloudflare Pages' Hugo does NOT auto-prefix, so the
                # explicit /ko/tech/ entry is what lands there. Emitting both means
                # the correct /ko/tech/ page is produced regardless of Hugo version.
                mapping[target].add(old[len('/ko'):])  # /tech/...
                mapping[target].add(old)               # /ko/tech/...
            else:
                mapping[target].add(old)
    return mapping


def inject(path: str, aliases: set) -> str:
    """Return 'added' | 'skipped' | error string."""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    if not text.startswith('---'):
        return f"ERROR no YAML front matter: {path}"
    # locate closing --- of front matter
    end = text.find('\n---', 3)
    if end == -1:
        return f"ERROR unterminated front matter: {path}"
    fm = text[3:end]           # between the fences
    body = text[end:]          # starts with \n---

    existing = set()
    m = re.search(r'^aliases:\s*\n((?:\s*-\s*.+\n)+)', fm, re.M)
    if m:
        existing = set(re.findall(r'-\s*"?([^"\n]+?)"?\s*$', m.group(1), re.M))

    to_add = sorted(a for a in aliases if a not in existing)
    if not to_add:
        return 'skipped'

    if m:
        # append new items into existing aliases block
        block = m.group(0).rstrip('\n')
        addition = ''.join(f'  - "{a}"\n' for a in to_add)
        fm = fm[:m.start()] + block + '\n' + addition + fm[m.end():]
    else:
        # add a fresh aliases block at end of front matter
        addition = 'aliases:\n' + ''.join(f'  - "{a}"\n' for a in to_add)
        if not fm.endswith('\n'):
            fm += '\n'
        fm += addition

    with open(path, 'w', encoding='utf-8') as f:
        f.write('---' + fm + body)
    return 'added'


def main():
    dry = '--dry-run' in sys.argv
    mapping = build_mapping()
    added = skipped = errors = 0
    for path, aliases in sorted(mapping.items()):
        if not os.path.isfile(path):
            print(f"MISSING FILE: {path}")
            errors += 1
            continue
        if dry:
            print(f"WOULD EDIT {path}  aliases={sorted(aliases)}")
            continue
        res = inject(path, aliases)
        if res == 'added':
            added += 1
        elif res == 'skipped':
            skipped += 1
        else:
            print(res)
            errors += 1
    print(f"\nadded={added} skipped={skipped} errors={errors} total={len(mapping)}")


if __name__ == '__main__':
    main()
