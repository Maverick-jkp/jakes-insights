# CLAUDE.md

**Version**: 7.0 - Bilingual pivot (EN/KO), quality-first strategy
**Last Updated**: 2026-02-10
**Pattern**: 350k LOC case (production-proven)

---

## ⚠️ MANDATORY FIRST ACTION

**Before ANY work, read these in order:**

1. **CLAUDE.md** (this file) - Overview & essentials
2. **`.claude/docs/[relevant].md`** - Details on-demand (see index below)
3. **`.claude/session-state.json`** - Current project state
4. **`.claude/mistakes-log.md`** - Past errors to avoid

---

## 🔴 PRE-ACTION VERIFICATION

**Before attempting any fix:**
1. Verify problem exists locally (`git status`, `git diff`)
2. Check if already fixed in remote (`git fetch origin`)
3. Follow documented procedures (`.claude/docs/troubleshooting.md`)
4. Never assume - always verify current state first

**Full checklist**: `.claude/rules/verification.md`

---

## Project Overview

**Jake's Tech Insights** - In-depth tech analysis and data-driven reports

- **Tech Stack**: Hugo, Python 3.x, Claude API (Sonnet 4.5), GitHub Actions
- **Languages**: English (EN), Korean (KO)
- **Deployment**: Cloudflare Pages (https://jakeinsight.com)
- **Automation**: Daily content generation, 5 posts/day (configured via GitHub Actions schedule)

---

## Quick Commands

```bash
# ⚠️ HOMEBREW TOOLS - ALWAYS USE FULL PATH (not in PATH!)
/opt/homebrew/bin/hugo server -D
/opt/homebrew/bin/hugo --minify
/opt/homebrew/bin/gh run list
/opt/homebrew/bin/gh run view <id> --log-failed

# Python
python scripts/generate_posts.py --count 3
pytest

# Git
git status
git commit -m "..."
```

**🚨 CRITICAL**: Homebrew binaries (`hugo`, `gh`) are NOT in PATH.
- ❌ `gh run list` → "command not found"
- ✅ `/opt/homebrew/bin/gh run list` → works

**Full reference**: `.claude/commands/quickstart.md`

---

## Key Files

```
content/{en,ko}/             # Blog posts (Markdown)
scripts/                     # Python automation
layouts/                     # Hugo templates
data/topics_queue.json       # Topic queue (state machine)
.claude/
  ├─ docs/                   # Detailed docs (on-demand)
  ├─ skills/                 # Task-specific (Week 2)
  └─ sessions/               # Per-session state (Week 4)
```

**Details**: `.claude/docs/architecture.md`

---

## 📚 Documentation Index

**Read on-demand based on your task:**

| Task | Read |
|------|------|
| **New PC setup (5 min)** | `.claude/docs/quick-setup.md` |
| Content pipeline details | `.claude/docs/architecture.md` |
| All command reference | `.claude/docs/commands.md` |
| Step-by-step guides | `.claude/docs/development.md` |
| Error solutions | `.claude/docs/troubleshooting.md` |
| Quality criteria | `.claude/docs/quality-standards.md` |
| UI/UX guidelines | `.claude/docs/design-system.md` |
| Security & costs | `.claude/docs/security.md` |

**Why on-demand loading?**
- Each doc is 60-200 lines (focused)
- Only load what you need
- Prevents context overload
- Based on 350k LOC production case (30-40% productivity gain)

---

## Common Tasks

| Task | Command | Details |
|------|---------|---------|
| Generate content | `python scripts/generate_posts.py --count 3` | `.claude/docs/development.md` §1 |
| Fix stuck topics | `python scripts/topic_queue.py cleanup 24` | `.claude/docs/development.md` §2 |
| Test locally | `/opt/homebrew/bin/hugo server -D` | `.claude/docs/development.md` §3 |
| Troubleshoot | See `.claude/docs/troubleshooting.md` | Hugo, API keys, etc. |

---

## System Architecture (Overview)

```
Topic Queue → Draft Agent → Editor Agent → Quality Gate → AI Review → Git Commit → GitHub Actions → Cloudflare Deploy
```

**Full diagram**: `.claude/docs/architecture.md`

---

## Content Quality (Quick Reference)

| Language | Word Count | Structure |
|----------|------------|-----------|
| English | 800-2,000 | 3-4 sections |
| Korean | 800-2,000 | 3-4 sections |

**Full standards**: `.claude/docs/quality-standards.md`

---

## Important Links

- **Live Site**: https://jakeinsight.com (verify: `grep baseURL hugo.toml`)
- **GitHub**: https://github.com/Maverick-jkp/jakes-tech-insights
- **Hugo Docs**: https://gohugo.io/documentation/
- **Claude API**: https://docs.anthropic.com/en/api/

---

---

**Entry point | Scale**: < 10k LOC | **Pattern**: Progressive disclosure (350k LOC proven)
**Version**: 7.0 (2026-02-10) - Bilingual pivot, quality-first
