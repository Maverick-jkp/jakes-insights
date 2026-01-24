#!/usr/bin/env python3
"""
Update hugo.toml to remove old categories (lifestyle, finance, education)
and add redirects for old category URLs.
"""

import re

hugo_config_path = "hugo.toml"

# Read the file
with open(hugo_config_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove old category menu items (lifestyle, finance, education)
# Match [[languages.X.menu.main]] blocks with these categories
old_categories_patterns = [
    r'\s*\[\[languages\.en\.menu\.main\]\]\s+name = "🌱 Lifestyle"[^\[]*',
    r'\s*\[\[languages\.en\.menu\.main\]\]\s+name = "💰 Finance"[^\[]*',
    r'\s*\[\[languages\.en\.menu\.main\]\]\s+name = "📖 Education"[^\[]*',
    r'\s*\[\[languages\.ko\.menu\.main\]\]\s+name = "🌱 라이프"[^\[]*',
    r'\s*\[\[languages\.ko\.menu\.main\]\]\s+name = "💰 금융"[^\[]*',
    r'\s*\[\[languages\.ko\.menu\.main\]\]\s+name = "📖 교육"[^\[]*',
    r'\s*\[\[languages\.ja\.menu\.main\]\]\s+name = "🌱 ライフ"[^\[]*',
    r'\s*\[\[languages\.ja\.menu\.main\]\]\s+name = "💰 金融"[^\[]*',
    r'\s*\[\[languages\.ja\.menu\.main\]\]\s+name = "📖 教育"[^\[]*',
]

for pattern in old_categories_patterns:
    content = re.sub(pattern, '', content, flags=re.MULTILINE)

# Remove old category buttons from params.profileMode
old_buttons_patterns = [
    r'\s*\[\[params\.profileMode\.buttons\]\]\s+name = "🌱 Lifestyle"[^\[]*',
    r'\s*\[\[params\.profileMode\.buttons\]\]\s+name = "💰 Finance"[^\[]*',
    r'\s*\[\[params\.profileMode\.buttons\]\]\s+name = "📖 Education"[^\[]*',
]

for pattern in old_buttons_patterns:
    content = re.sub(pattern, '', content, flags=re.MULTILINE)

# Add redirects at the end of the file
redirects = """
# Category Redirects (Migration: 8 → 5 categories)
# Added: 2026-01-25
[mediaTypes]
  [mediaTypes."text/netlify"]
    suffixes = [""]

[outputFormats.REDIRECTS]
  mediaType = "text/netlify"
  baseName = "_redirects"
  isPlainText = true
  notAlternative = true

# Old category URLs redirect to new categories
[[redirects]]
  from = "/categories/education/*"
  to = "/categories/tech/:splat"
  status = 301

[[redirects]]
  from = "/categories/finance/*"
  to = "/categories/business/:splat"
  status = 301

[[redirects]]
  from = "/categories/lifestyle/*"
  to = "/categories/society/:splat"
  status = 301

[[redirects]]
  from = "/*/categories/education/*"
  to = "/:1/categories/tech/:splat"
  status = 301

[[redirects]]
  from = "/*/categories/finance/*"
  to = "/:1/categories/business/:splat"
  status = 301

[[redirects]]
  from = "/*/categories/lifestyle/*"
  to = "/:1/categories/society/:splat"
  status = 301
"""

# Remove old redirects section if it exists
content = re.sub(r'\n# Category Redirects.*$', '', content, flags=re.DOTALL)

# Add new redirects
content = content.rstrip() + '\n' + redirects

# Write back
with open(hugo_config_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Updated hugo.toml:")
print("   - Removed 3 old categories from menus (lifestyle, finance, education)")
print("   - Added URL redirects for SEO (301 permanent redirects)")
print("   - Migration complete!")
