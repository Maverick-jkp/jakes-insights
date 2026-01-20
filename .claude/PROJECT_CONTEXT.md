# Jake's Tech Insights - Project Overview

**Type**: Hugo-based multilingual automated blog
**Languages**: English (EN), Korean (KO), Japanese (JA)
**Deployment**: Cloudflare Pages (https://jakes-tech-insights.pages.dev)
**Purpose**: Automated content generation with AdSense monetization

---

## Quick Links

### Project Documentation
- **Automation System**: [docs/AUTOMATION_CONTEXT.md](docs/AUTOMATION_CONTEXT.md) - Complete automation architecture
- **Claude Guidelines**: [docs/CLAUDE_GUIDELINES.md](docs/CLAUDE_GUIDELINES.md) - Work principles and common issues
- **Work Log**: [docs/WORK_LOG.md](docs/WORK_LOG.md) - Recent changes and decisions

### Agent Workflows
- **Master Agent**: [.claude/agents/MASTER.md](.claude/agents/MASTER.md) - Task decomposition and integration
- **Feature Workflow**: [.claude/workflows/feature-workflow.md](.claude/workflows/feature-workflow.md) - Development process
- **Branching Strategy**: [.claude/workflows/branching-strategy.md](.claude/workflows/branching-strategy.md) - Git branch management
- **Instructions**: [.claude/instructions.md](.claude/instructions.md) - Quick reference for Claude

---

## Tech Stack

**Core**: Hugo v0.154.5+extended, PaperMod theme (submodule)
**Automation**: Python, Claude API, GitHub Actions
**Deployment**: Cloudflare Pages (auto-deploy on push)

---

## Project Structure

```
jakes-insights/
├── .claude/              # Agent definitions and workflows
│   ├── agents/          # MASTER, DESIGNER, CTO, QA
│   └── workflows/       # feature-workflow, branching-strategy
├── content/             # Language-specific content
│   ├── en/{category}/   # English posts
│   ├── ko/{category}/   # Korean posts
│   └── ja/{category}/   # Japanese posts
├── docs/                # Complete documentation
├── layouts/             # Custom Hugo templates
├── scripts/             # Automation scripts
│   ├── generate_posts.py
│   ├── topic_queue.py
│   └── quality_gate.py
└── data/                # Topic queue and state
```

---

## Categories

**Tech** - Technology, AI, coding
**Business** - Startups, funding, marketing
**Lifestyle** - Digital nomad, trends

---

**Last Updated**: 2026-01-20
**Note**: This is an index. See docs/ folder for detailed documentation.
