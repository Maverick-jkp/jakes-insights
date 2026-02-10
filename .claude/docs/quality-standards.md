# Content Quality Standards

**Version**: 6.0
**Last Updated**: 2026-01-23
**Purpose**: Content validation criteria and SEO requirements

---

## Word Count Requirements

| Language | Minimum | Target | Maximum |
|----------|---------|--------|---------|
| English  | 800     | 900-1,200 | 2,000 |
| Korean   | 800     | 900-1,200 | 2,000 |

---

## Structure Requirements

- 3-4 main sections (## headings)
- Introduction: 80-100 words (strong hook)
- Each section: 120-180 words (core insights only)
- Conclusion: 60-80 words (clear CTA)
- Must finish completely (no mid-sentence cutoffs)

---

## AI Phrase Blacklist

Quality gate **fails** if these phrases appear:

**English**:
- "revolutionary", "game-changer", "cutting-edge"
- "it's important to note", "in today's digital landscape"
- "in conclusion", "in summary" (unless in actual conclusion)

**Korean**:
- "물론", "혁신적", "게임체인저"
- "디지털 시대", "중요한 점은"

Full list: `scripts/quality_gate.py` lines ~50-100

---

## SEO Requirements

- **Meta description**: 120-160 characters
- **Keyword density**: 5-7 natural mentions (not forced)
- **Featured image**: Required (auto-fetched from Unsplash)
- **Image alt text**: Required (describes image content)
- **References section**: 2+ external links (reputable sources)
- **Internal links**: Related posts (Hugo template handles automatically)

---

## Image Requirements

- **Source**: Unsplash API (auto-generated with credits)
- **Format**: JPEG/PNG, optimized
- **Alt text**: Descriptive, includes keyword naturally
- **Credit**: Photo by [Name](https://unsplash.com/@username)

---

**For validation commands**: See `.claude/docs/commands.md`
**For architecture details**: See `.claude/docs/architecture.md`
