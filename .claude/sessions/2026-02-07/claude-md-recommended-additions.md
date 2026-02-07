# CLAUDE.md Recommended Additions

**Date**: 2026-02-07
**Purpose**: Specific text to add to CLAUDE.md (copy-paste ready)
**Total addition**: +18 lines (147 → 165 lines)

---

## Addition 1: Project Skills Section
**Location**: After "Quick Commands" section (after line 59)
**Lines to add**: 10

```markdown
---

## Project Skills

**Available**: keyword-curation, ab-test-manager, hugo-operations, quality-validation, content-generation

**Usage**: Claude Code auto-invokes via Skill tool based on task context
**Index**: See `.claude/session-state.json` → skills_index
**Documentation**: `.claude/skills/{skill-name}/SKILL.md` (loaded on-demand)

**Why skills exist**: Progressive disclosure - task-specific knowledge loaded only when needed

---
```

---

## Addition 2: Config Change Protocol Reference
**Location**: After "Important Links" section (after line 141)
**Lines to add**: 5

```markdown
---

## Before Changing Config Values

**CRITICAL**: When changing domain, API keys, build commands, or deployment targets:
1. **Read first**: `.claude/rules/config-change-protocol.md`
2. **Update source of truth**: hugo.toml, .env, etc.
3. **Cascade to all docs**: CLAUDE.md, README.md, .claude/docs/*
4. **Verify**: Run `grep -r "old-value" . --exclude-dir=.git`

---
```

---

## Addition 3: Important Links Verification Notes
**Location**: Modify existing "Important Links" section (lines 135-141)
**Change type**: Modify existing lines

**Current**:
```markdown
## Important Links

- **Live Site**: https://jakeinsight.com (verify: `grep baseURL hugo.toml`)
- **GitHub**: https://github.com/Maverick-jkp/jakes-tech-insights
- **Hugo Docs**: https://gohugo.io/documentation/
- **Claude API**: https://docs.anthropic.com/en/api/
```

**New** (modify line 137):
```markdown
## Important Links

- **Live Site**: https://jakeinsight.com ⚠️ **Always verify**: `grep baseURL hugo.toml` (source of truth)
- **GitHub**: https://github.com/Maverick-jkp/jakes-tech-insights
- **Hugo Docs**: https://gohugo.io/documentation/
- **Claude API**: https://docs.anthropic.com/en/api/

**Note**: If CLAUDE.md value differs from hugo.toml, hugo.toml is correct.
```

**Lines added**: +3 (one for warning emoji, one for note, one for spacing)

---

## Summary of Changes

| Section | Action | Lines | Priority |
|---------|--------|-------|----------|
| Project Skills | ADD after Quick Commands | +10 | High |
| Config Change Protocol | ADD after Important Links | +5 | Critical |
| Important Links | MODIFY existing + add note | +3 | High |
| **Total** | | **+18** | |

---

## New CLAUDE.md Structure (165 lines)

```
CLAUDE.md
├── Header (version, last updated)         [5 lines]
├── Mandatory First Action                 [10 lines]
├── Pre-Action Verification                [8 lines]
├── Project Overview                       [8 lines]
├── Quick Commands                         [15 lines]
├── 🆕 Project Skills                      [10 lines] ← NEW
├── Key Files                              [12 lines]
├── Documentation Index                    [20 lines]
├── Common Tasks                           [10 lines]
├── System Architecture (overview)         [8 lines]
├── Content Quality (quick reference)      [8 lines]
├── Important Links (with verification)    [9 lines]  ← MODIFIED (+3)
├── 🆕 Config Change Protocol Reference    [5 lines]  ← NEW
└── Footer (version history)               [5 lines]
```

**Total**: 165 lines (was 147, added 18)

---

## Version Update

**Update line 3**:
```markdown
**Version**: 6.2 - Skills awareness + config protocol
```

**Update line 4**:
```markdown
**Last Updated**: 2026-02-07
```

**Update footer (line 147)**:
```markdown
**Version**: 6.2 (2026-02-07) - Added skills section and config change protocol
```

---

## Implementation Checklist

- [ ] Add "Project Skills" section (10 lines) after Quick Commands
- [ ] Add "Config Change Protocol" section (5 lines) after Important Links
- [ ] Modify "Important Links" section (add verification note, +3 lines)
- [ ] Update version to 6.2 (header)
- [ ] Update last updated date to 2026-02-07 (header)
- [ ] Update version history (footer)
- [ ] Verify total line count = 165 lines
- [ ] Test: Read CLAUDE.md and verify it's still scannable
- [ ] Commit: "docs: Add skills section and config change protocol to CLAUDE.md (v6.2)"

---

## Rationale

### Why Add Project Skills?
- **Current issue**: Claude doesn't know skills exist unless told
- **Benefit**: Awareness enables better tool selection
- **Progressive disclosure**: Just lists skills, full docs in .claude/skills/

### Why Add Config Change Protocol?
- **Current issue**: 14-day documentation drift after domain change
- **Benefit**: Prevents future config/doc desync
- **Reference approach**: Points to protocol, doesn't duplicate it

### Why Modify Important Links?
- **Current issue**: Hardcoded URLs can go stale
- **Benefit**: Emphasizes source of truth (hugo.toml)
- **Behavior change**: Encourages verification before using

---

## Expected Impact

**Before (v6.1)**:
- Claude unaware of 5 project skills (unless session context mentions them)
- No reminder about config change protocol
- URLs treated as static values

**After (v6.2)**:
- Claude aware of 5 skills → better tool selection
- Config change protocol visible → fewer drift incidents
- URLs marked as "verify first" → fewer stale references

**Token cost**: +200 tokens (+10% of CLAUDE.md, +0.1% of session budget)
**Cognitive load**: Minimal (sections are scannable, action-oriented)
**Maintenance burden**: Low (skills rarely change, protocol is stable)

---

## Alternative Considered: .claude/context/ Directory

**Idea**: Create `.claude/context/config-values.json` with extracted hugo.toml values

**Pros**:
- Single source of truth
- Automated extraction possible
- Clean separation of concerns

**Cons**:
- Another file to maintain
- Requires sync script
- Adds complexity

**Decision**: Not implementing now. Current approach (verification notes) is simpler and achieves the same goal.

**Future consideration**: If config drift happens again after implementing v6.2, revisit this approach.

---

## Testing Plan

After implementing changes:

1. **Readability test**: Open CLAUDE.md in editor, verify it's still scannable
2. **Token count test**: Verify total size ≈ 165 lines
3. **Skills awareness test**: Start new session, ask "what skills are available?" (should mention 5 skills)
4. **Config protocol test**: Simulate domain change, verify protocol is followed
5. **30-day evaluation**: Track documentation drift incidents

**Success criteria**:
- Zero config drift incidents in next 90 days
- Skills section referenced in >50% of relevant sessions
- CLAUDE.md remains readable and scannable

---

**Document Status**: Ready for implementation
**Review Status**: Awaiting user approval
**Implementation Time**: ~10 minutes
