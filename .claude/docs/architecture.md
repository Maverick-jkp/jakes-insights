# System Architecture

**Version**: 6.0
**Last Updated**: 2026-01-23
**Purpose**: Content generation pipeline and system components

---

## Content Generation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Topic Queue State Machine                    │
│                   (data/topics_queue.json)                       │
│                                                                   │
│   pending → in_progress → completed                              │
│                ↓                                                  │
│              failed (retry)                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Draft Agent (Claude API - Sonnet 4.5)              │
│                  System Prompt: EN/KO/JA specific               │
│                  max_tokens: 12000                              │
│                  Prompt Caching: Enabled (20% cost reduction)   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│             Editor Agent (Claude API - Sonnet 4.5)              │
│                  Refinement: Tone, Structure, SEO               │
│                  max_tokens: 12000                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Quality Gate (quality_gate.py)                │
│   - Word count: 800-2000 (EN/KO), 3000-7500 chars (JA)         │
│   - AI phrase blacklist check                                   │
│   - SEO validation (meta description, keywords)                 │
│   - Image check (WARNING only)                                  │
│   - References check                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 AI Reviewer (ai_reviewer.py)                     │
│   5-Criteria Scoring:                                           │
│   - Authenticity (human tone)                                   │
│   - Value (practical insights)                                  │
│   - Engagement (structure)                                      │
│   - Technical Accuracy                                          │
│   - SEO Quality                                                 │
│   Result: APPROVE (≥8.0) / REVISE (6.0-7.9) / REJECT (<6.0)    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Git Commit (Markdown Files)                   │
│   Location: content/{en,ko,ja}/{category}/{date}-{slug}.md     │
│   Frontmatter: title, date, categories, tags, image, etc.      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│          GitHub Actions (.github/workflows/daily-content.yml)   │
│   Schedule: 6 AM, 12 PM, 6 PM KST (may delay 15-60 min)        │
│   Steps: pytest → generate → quality gate → create PR          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Cloudflare Pages (Auto-deploy on merge)            │
│   URL: https://jakeinsight.com                                  │
│   Build: hugo --minify                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Topic Queue State Machine

Topics in `data/topics_queue.json` flow through these states:

1. **pending** - Ready to be processed (default for new topics)
2. **in_progress** - Currently being generated (reserved by `reserve_topics()`)
3. **completed** - Successfully published (marked by `mark_completed()`)
4. **failed** - Generation failed (marked by `mark_failed()`, will retry)

**Key Functions** (in `scripts/topic_queue.py`):
- `reserve_topics(count=3)` - Move pending → in_progress, return reserved topics
- `mark_completed(topic_id)` - Move in_progress → completed
- `mark_failed(topic_id, error)` - Move in_progress → failed (auto-retry later)
- `cleanup(hours=24)` - Reset stuck in_progress topics (manual recovery)

**Duplicate Prevention**: Queue automatically skips keywords already completed for same language.

---

## Python Scripts

| Script | Purpose | Key Functions | When to Run |
|--------|---------|---------------|-------------|
| `topic_queue.py` | Topic state management | `reserve_topics()`, `mark_completed()`, `cleanup()` | Always (imported by others) |
| `generate_posts.py` | Content generation | `generate_post()` (Draft + Editor agents) | Manual or automated (3x daily) |
| `quality_gate.py` | Validation checks | `validate_content()`, `check_ai_phrases()` | After generation (automated) |
| `ai_reviewer.py` | 5-criteria scoring | `review_content()`, provides recommendations | Optional (manual review) |
| `keyword_curator.py` | Keyword research | Fetches Google Trends, human filtering required | Weekly (Fridays 5 PM KST) |
| `affiliate_config.py` | Affiliate link management | `detect_product_mentions()`, `generate_affiliate_link()` | Imported by generate_posts.py |

---

## Hugo Templates

```
layouts/
├── index.html                    # Homepage (Bento grid, theme toggle)
├── _default/
│   ├── single.html              # Article page (TOC, related posts, references)
│   ├── list.html                # Generic list page
│   └── baseof.html              # Base template
├── categories/
│   └── list.html                # Category-specific list (thumbnails)
├── partials/
│   ├── head.html                # <head> section (meta tags, SEO)
│   ├── footer.html              # Footer
│   └── ...
└── shortcodes/                  # Custom shortcodes (if any)
```

**Theme**: PaperMod (in `themes/PaperMod/`, Git submodule)
- **Do NOT modify theme directly**
- Override by creating matching file in `layouts/`
- Example: `layouts/_default/single.html` overrides theme's single.html

---

## Data Files

- **`data/topics_queue.json`** - Topic queue with state machine (main data source)
- **`generated_files.json`** - Tracks files created by automation (for cleanup)
- **`quality_report.json`** - Latest quality gate results (pass/fail details)
- **`ai_review_report.json`** - Latest AI review scores and recommendations

---

## Configuration Files

- **`hugo.toml`** - Hugo config (languages, menus, params, SEO)
- **`requirements.txt`** - Python dependencies
- **`.env`** - API keys (NOT in git, see `.env.example`)
- **`pytest.ini`** - Test configuration (coverage threshold: 48%)
- **`.coveragerc`** - Coverage.py settings

---

## Content Files Structure

```
content/
├── en/          # English posts
│   ├── tech/
│   ├── business/
│   ├── lifestyle/
│   ├── society/
│   ├── entertainment/
│   ├── sports/
│   ├── finance/
│   └── education/
├── ko/          # Korean posts (same structure)
└── ja/          # Japanese posts (same structure)
```

**Post Format**: Markdown with YAML frontmatter
```yaml
---
title: "Post Title"
date: 2026-01-22T18:00:00+09:00  # KST timezone required
categories: ["tech"]
tags: ["keyword1", "keyword2"]
description: "120-160 char meta description"
image: "https://images.unsplash.com/photo-..."
imageCredit: "Photo by [Name](https://unsplash.com/@username)"
lang: "en"
---

Content here...
```

---

**For detailed commands**: See `.claude/docs/commands.md`
**For quality standards**: See `.claude/docs/quality-standards.md`
**For troubleshooting**: See `.claude/docs/troubleshooting.md`
