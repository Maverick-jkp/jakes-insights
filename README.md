# Jake's Insights

In-depth tech analysis and data-driven reports in English and Korean.

[![Hugo](https://img.shields.io/badge/Hugo-FF4088?logo=hugo)](https://gohugo.io/)
[![Claude API](https://img.shields.io/badge/Claude-Sonnet%204.6-8B5CF6)](https://anthropic.com/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Automated-2088FF?logo=github-actions)](https://github.com/features/actions)
[![Cloudflare Pages](https://img.shields.io/badge/Cloudflare-Pages-F38020?logo=cloudflare)](https://pages.cloudflare.com/)

**Live site**: https://jakeinsight.com

---

## Overview

Jake's Insights is an AI-powered bilingual tech blog with a fully automated content pipeline. Topics are sourced daily from community feeds (Hacker News, Dev.to, Lobsters, ProductHunt), drafted and edited by Claude, then deployed automatically to Cloudflare Pages.

**10 posts/day** (EN + KO) — fully automated from topic discovery to deployment.

---

## Architecture

```
Community Sources (HN, Dev.to, Lobsters, ProductHunt)
         │
         ▼
   Topic Queue          State machine: pending → in_progress → completed
         │
         ▼
  Content Generation    Draft Agent → Editor Agent (Claude Sonnet 4.6)
         │
         ▼
   Quality Gate         Word count (800–2000), AI phrase detection, SEO
         │
         ▼
   Git Commit           Auto-commit to main branch
         │
         ▼
  Cloudflare Pages      Auto-deploy on push → https://jakeinsight.com
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/Maverick-jkp/jakes-insights.git
cd jakes-insights

# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY='your-claude-api-key'

# Generate posts locally
python scripts/generate_posts.py --count 3

# Preview site (Hugo required: brew install hugo)
/opt/homebrew/bin/hugo server -D
```

---

## Project Structure

```
jakes-insights/
├── .github/workflows/
│   ├── daily-content.yml       # Daily content generation (7 PM KST)
│   ├── daily-keywords.yml      # Keyword curation (4 PM KST)
│   ├── playwright-tests.yml    # E2E tests
│   └── test.yml                # Unit tests
├── content/
│   ├── en/tech/                # English posts
│   └── ko/tech/                # Korean posts
├── layouts/                    # Hugo templates
├── assets/css/                 # Custom CSS
├── scripts/
│   ├── generate_posts.py       # Content generation
│   ├── topic_queue.py          # Queue management
│   ├── quality_gate.py         # Quality validation
│   └── ai_reviewer.py          # AI self-review
├── data/topics_queue.json      # Topic queue state
├── hugo.toml                   # Hugo config
└── .claude/                    # Claude Code docs & skills
```

---

## Automation

### Daily Schedule (GitHub Actions)

| Time (KST) | Job | Description |
|------------|-----|-------------|
| 4:00 PM | `daily-keywords.yml` | Curate 10 topics from community sources |
| 7:00 PM | `daily-content.yml` | Generate 10 posts (EN 5 + KO 5) |

### Manual Trigger

1. Go to **Actions** tab on GitHub
2. Select **Daily Content Generation**
3. Click **Run workflow**

---

## Content Standards

| Metric | Requirement |
|--------|-------------|
| Word count | 800–2,000 words |
| Structure | 3–4 sections (## headings) |
| Language | EN and KO |
| Category | Tech only |
| Subtopics | ai, security, devtools, cloud, data, web, mobile |

---

## Required GitHub Secrets

Go to **Settings → Secrets → Actions** and add:

```
ANTHROPIC_API_KEY    Claude API key for content generation
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Static site generator | Hugo |
| Theme | Custom (PaperMod base) |
| AI model | Claude Sonnet 4.6 |
| Hosting | Cloudflare Pages |
| CI/CD | GitHub Actions |
| Language | Python 3.11+ |

---

## Scripts Reference

```bash
# Topic queue
python scripts/topic_queue.py stats            # Queue status
python scripts/topic_queue.py cleanup 24       # Fix stuck topics (24h+)

# Content
python scripts/generate_posts.py --count 3     # Generate 3 posts
python scripts/quality_gate.py                 # Run quality checks

# Local dev
/opt/homebrew/bin/hugo server -D               # Start dev server
/opt/homebrew/bin/hugo --minify                # Production build
```

---

## License

MIT

---

*Last updated: 2026-03-03*
