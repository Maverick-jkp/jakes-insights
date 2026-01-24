# Category Migration: 8 → 6 Categories

## Migration Date
2026-01-25

## Old → New Category Mapping

| Old Category (8) | New Category (6) | Icon | Rationale |
|-----------------|------------------|------|-----------|
| tech            | tech             | 💻   | Keep as core category |
| education       | tech             | 💻   | Merge into Tech (EdTech focus) |
| business        | business         | 💼   | Merge Business + Finance |
| finance         | business         | 💼   | Merge Business + Finance |
| society         | society          | 🌍   | Merge Society + Lifestyle |
| lifestyle       | society          | 🌍   | Merge Society + Lifestyle |
| entertainment   | entertainment    | 🎬   | Keep as core category |
| sports          | sports           | ⚽   | Keep as core category |

## New Category Structure (6 Categories)

1. **💻 Tech** (tech)
   - Technology, AI, digital innovation
   - Educational technology, online learning
   - Absorbs: `education`

2. **💼 Business** (business)
   - Corporate news, startups, economy
   - Finance, markets, investments
   - Absorbs: `finance`

3. **🌍 Society** (society)
   - Social issues, cultural trends
   - Lifestyle, health, wellness
   - Absorbs: `lifestyle`

4. **🎬 Entertainment** (entertainment)
   - Movies, TV, music, celebrities
   - No changes

5. **⚽ Sports** (sports)
   - All sports content
   - No changes

## Migration Scripts Required

### 1. Content Directory Migration
```bash
# Move education posts to tech
find content/*/education -name "*.md" -exec sh -c 'mv "$1" "${1/education/tech}"' _ {} \;

# Move finance posts to business
find content/*/finance -name "*.md" -exec sh -c 'mv "$1" "${1/finance/business}"' _ {} \;

# Move lifestyle posts to society
find content/*/lifestyle -name "*.md" -exec sh -c 'mv "$1" "${1/lifestyle/society}"' _ {} \;
```

### 2. Frontmatter Updates
Update `categories: ["old"]` to `categories: ["new"]` in all migrated posts

### 3. URL Redirects (Hugo config)
```toml
[[redirects]]
  from = "/categories/education/*"
  to = "/categories/tech/:splat"

[[redirects]]
  from = "/categories/finance/*"
  to = "/categories/business/:splat"

[[redirects]]
  from = "/categories/lifestyle/*"
  to = "/categories/society/:splat"
```

## Impact Analysis

### Content Distribution (Projected)
- Tech: ~19 posts (13 tech + 6 education)
- Business: ~16 posts (7 business + 9 finance)
- Society: ~22 posts (12 society + 10 lifestyle)
- Entertainment: ~11 posts
- Sports: ~21 posts

### SEO Impact
- Consolidated categories = stronger authority per category
- Redirects preserve old URLs (no broken links)
- Better internal linking opportunities

### User Experience
- Clearer category distinctions
- Less decision fatigue (6 vs 8 choices)
- More consistent categorization

## Files to Update

### Templates
- [x] layouts/index.html
- [x] layouts/_default/list.html
- [x] layouts/_default/single.html
- [x] layouts/categories/list.html

### Scripts
- [x] scripts/keyword_curator.py (category list + validation)
- [x] scripts/generate_posts.py (if hardcoded categories exist)

### Config
- [x] config/_default/config.toml (add redirects)
- [x] config/_default/params.toml (if category list exists)

## Validation Checklist

- [ ] All posts migrated to new directories
- [ ] All frontmatter updated
- [ ] No broken internal links
- [ ] Keyword curator generates only new 6 categories
- [ ] Template menus show only 6 categories
- [ ] Old category URLs redirect properly
- [ ] Test content generation with new categories
