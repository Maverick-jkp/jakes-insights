# Root Cause Analysis: Claude Failed to Remember Correct Domain URL

**Date**: 2026-02-07
**Issue**: Claude repeatedly used outdated URL (jakes-tech-insights.pages.dev) instead of correct domain (jakeinsight.com)
**Impact**: User frustration, repeated corrections needed despite domain change weeks ago

---

## Executive Summary

Claude failed to remember the correct domain URL because:
1. **CLAUDE.md contained outdated URL in 2 locations** (lines 38, 137)
2. **Documentation wasn't updated when domain changed** (Jan 24, 2026)
3. **No single source of truth** for dynamic values like URLs
4. **17+ documentation files contained old URL**, creating conflicting information
5. **README.md was updated but CLAUDE.md wasn't**, despite CLAUDE.md being the primary reference

The root cause is a **documentation maintenance gap**: when domain changed, only operational files (hugo.toml, README.md, robots.txt) were updated, but the documentation files that Claude reads at session start were not updated.

---

## Timeline of Domain Change

```
2026-01-24 06:02  | Commit 1b13052: Update domain to jakeinsight.com
                  | - Updated: hugo.toml (baseURL)
                  | - Updated: static/robots.txt (sitemap URL)
                  | - NOT updated: CLAUDE.md
                  |
2026-01-24        | Commit bc6f134: Add 301 redirect
                  | - Added: static/_redirects (old → new domain)
                  |
2026-01-25        | Commit 47850c4: Add About pages
                  | - About pages use new domain
                  |
2026-02-03        | Commit 84c646f: Update live site URL in README
                  | - Updated: README.md line 58, 410
                  | - Still NOT updated: CLAUDE.md
                  |
2026-02-07        | User reports: Claude keeps using old URL
                  | - CLAUDE.md lines 38, 137 still show old URL
                  | - .claude/docs/architecture.md line 68 still shows old URL
```

**Key Finding**: Domain changed **14 days ago** (Jan 24), but documentation files Claude reads at session start were never updated.

---

## Files Containing Outdated URL

### Critical Files (Read at Session Start)
1. **CLAUDE.md** - Line 38, 137 - **PRIMARY ISSUE**
2. **.claude/docs/architecture.md** - Line 68 - Deployment section

### Documentation Files (On-Demand)
3. docs/TECH_STACK.md - Line 31
4. docs/PROJECT_OVERVIEW.md - Line 316
5. docs/HUGO_CONFIG.md - Line 12, 304
6. docs/MONETIZATION.md - Line 231

### Session Reports/Archives (17 total markdown files)
7. .claude/archive/reports-history/active/*.md (7 files)
8. .claude/archive/reports-history/archive/2026-01/*.md (1 file)
9. .claude/archive/v5.0-before-refactor/CLAUDE.md
10. .claude/refactor-plan-week1.md
11. test_generation_report.md

### Operational Files (Already Updated ✅)
- hugo.toml - ✅ Updated Jan 24
- README.md - ✅ Updated Feb 3
- static/robots.txt - ✅ Updated Jan 24
- static/_redirects - ✅ Created Jan 24

---

## Why CLAUDE.md Wasn't Updated

**Investigation findings**:

1. **Commit 1b13052 (Jan 24)** changed only operational files:
   ```
   hugo.toml         | 2 +-  (baseURL changed)
   static/robots.txt | 2 +-  (sitemap URL changed)
   ```

2. **Commit 84c646f (Feb 3)** updated README.md:
   ```
   README.md | 4 ++--  (architecture diagram + support section)
   ```

3. **CLAUDE.md was last updated Jan 23** (Version 6.0 refactor), **before domain change**

**Root Cause**:
- Domain change commits **focused on operational functionality** (Hugo build, redirects)
- **Documentation maintenance was not part of the change scope**
- No checklist or procedure for updating documentation when config values change
- README.md update happened 10 days later (Feb 3), but CLAUDE.md still missed

---

## Documentation Hierarchy Analysis

Current hierarchy shows **conflicting priorities**:

```
Priority 1 (Always Read):
├── CLAUDE.md ❌ Contains old URL (lines 38, 137)
│   └── "Read this file first at session start"
│
Priority 2 (On-Demand):
├── .claude/docs/architecture.md ❌ Contains old URL (line 68)
│   └── "Read for deployment details"
│
Priority 3 (Reference):
├── README.md ✅ Contains correct URL (updated Feb 3)
│   └── "Read for project overview"
│
Source of Truth:
└── hugo.toml ✅ Contains correct URL (updated Jan 24)
    └── "Operational config for Hugo build"
```

**Problem**: Claude reads CLAUDE.md first (per instructions), which contains outdated URL. Even though hugo.toml has correct URL, Claude defaults to documentation over config files.

---

## Why Claude Used Wrong URL

**Behavioral analysis**:

1. **Session start protocol** (from CLAUDE.md line 11-16):
   ```
   Before ANY work, read these in order:
   1. CLAUDE.md (this file) ← Read first, contains old URL
   2. .claude/docs/[relevant].md
   3. .claude/session-state.json
   4. .claude/mistakes-log.md
   ```

2. **CLAUDE.md content** (lines 38, 137):
   ```
   Line 38:  - Deployment: Cloudflare Pages (https://jakes-tech-insights.pages.dev)
   Line 137: - Live Site: https://jakes-tech-insights.pages.dev
   ```

3. **Claude's reasoning**:
   - "CLAUDE.md is the entry point and single source of truth"
   - "If project overview says X, then X must be correct"
   - "User asked about live site → check CLAUDE.md → see old URL → use it"
   - Never verified against hugo.toml (the actual source of truth)

**Pattern**: Documentation-driven agent prioritized outdated docs over checking operational configs.

---

## Single Source of Truth Problem

**Current state**: Multiple files claim to be authoritative:

| File | Claims | URL Status | Authority Level |
|------|--------|------------|-----------------|
| hugo.toml | "Hugo config (baseURL)" | ✅ Correct | Operational (actual source) |
| CLAUDE.md | "Entry point, read first" | ❌ Outdated | Documentation (intended source) |
| README.md | "Project overview" | ✅ Correct | Public-facing |
| .claude/docs/architecture.md | "System architecture" | ❌ Outdated | Technical reference |

**Problem**: No clear designation of which file is authoritative for what information.

**For dynamic values like URLs**:
- **Should be**: hugo.toml → all docs reference this
- **Actually is**: Each file has own copy → drift over time

---

## Prevention Strategy

### 1. Establish Clear Hierarchy for Dynamic Values

**Rule**: Configuration files are source of truth, documentation references them.

```
┌─────────────────────────────────────────────────┐
│ Source of Truth (Config Files)                  │
│ - hugo.toml (baseURL, deployment URL)           │
│ - .env (API keys, secrets)                      │
│ - package.json (project metadata)               │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│ Documentation (References Config)               │
│ - CLAUDE.md: "See hugo.toml for live site URL"  │
│ - README.md: "Deployed at [baseURL from config]"│
│ - .claude/docs/*.md: Point to config files      │
└─────────────────────────────────────────────────┘
```

### 2. Update CLAUDE.md Immediately

**Action**: Replace hardcoded URLs with references to config.

**Before** (current):
```markdown
- **Deployment**: Cloudflare Pages (https://jakes-tech-insights.pages.dev)
- **Live Site**: https://jakes-tech-insights.pages.dev
```

**After** (recommended):
```markdown
- **Deployment**: Cloudflare Pages (custom domain configured)
- **Live Site**: See `baseURL` in hugo.toml (currently: jakeinsight.com)
- **Note**: Always check hugo.toml for current production URL
```

### 3. Documentation Update Checklist

**When changing domain/URL/API keys/any config value**:

```bash
# Step 1: Update source of truth
[ ] hugo.toml (or relevant config file)

# Step 2: Update operational files
[ ] robots.txt
[ ] _redirects
[ ] .env.example (if applicable)

# Step 3: Update documentation (MANDATORY)
[ ] CLAUDE.md
[ ] README.md
[ ] .claude/docs/architecture.md
[ ] .claude/docs/troubleshooting.md (if URLs in examples)

# Step 4: Search for hardcoded references
[ ] grep -r "old-value" . (exclude node_modules, .git)
[ ] Review and update each occurrence

# Step 5: Commit with clear message
[ ] git commit -m "chore: Update domain references across all docs"
```

### 4. Add Verification to CLAUDE.md

**Proposed addition** to CLAUDE.md (after line 26):

```markdown
## Dynamic Configuration Values

**CRITICAL**: Always check config files for current values, not documentation.

| Value | Source of Truth | Documentation Reference |
|-------|----------------|------------------------|
| Live Site URL | `hugo.toml` (baseURL) | This file may be outdated |
| API Keys | `.env` file | Never in documentation |
| Project Name | `hugo.toml` (title) | Sync with config |
| Domain | `hugo.toml` + `_redirects` | Config is authoritative |

**Before using any URL/domain in responses**:
1. Run: `grep baseURL hugo.toml`
2. Use that value, not what's in this doc
3. If outdated, note it but use config value
```

### 5. Automated Validation

**Proposed**: Add to .git/hooks/pre-commit (or GitHub Actions):

```bash
#!/bin/bash
# Check if baseURL in hugo.toml matches CLAUDE.md

HUGO_URL=$(grep "^baseURL" hugo.toml | cut -d"'" -f2)
CLAUDE_URLS=$(grep -E "https://[a-z0-9\.-]+" CLAUDE.md | grep -v "^#")

if echo "$CLAUDE_URLS" | grep -v "$HUGO_URL" | grep -q "jakes-tech-insights.pages.dev"; then
    echo "⚠️  WARNING: CLAUDE.md contains outdated URL"
    echo "   Current baseURL: $HUGO_URL"
    echo "   Found old URL in CLAUDE.md"
    echo "   Update CLAUDE.md before committing"
    # Don't fail, just warn
fi
```

---

## Recommended Documentation Structure

### Option A: Reference-Based (Recommended)

**CLAUDE.md** should NOT contain actual URLs, only references:

```markdown
## Important Links

- **Live Site**: Check `baseURL` in hugo.toml
- **GitHub**: https://github.com/Maverick-jkp/jakes-tech-insights
- **Deployment**: Cloudflare Pages (domain configured via hugo.toml)

**To find current live site URL**: `grep baseURL hugo.toml`
```

**Pros**:
- Never gets outdated
- Forces Claude to check actual config
- Single update point (hugo.toml)

**Cons**:
- Extra step to find URL
- Less convenient for quick reference

### Option B: Explicit Warning (Compromise)

Keep URLs but add prominent warning:

```markdown
## Important Links

⚠️ **WARNING**: URLs may be outdated. Always verify with `hugo.toml`.

- **Live Site**: https://jakeinsight.com *(last updated: 2026-01-24)*
- **Config Check**: `grep baseURL hugo.toml`
- **GitHub**: https://github.com/Maverick-jkp/jakes-tech-insights
```

**Pros**:
- Quick reference available
- Clear warning to verify
- Last updated date helps identify drift

**Cons**:
- Still requires manual updates
- Warning may be ignored

### Option C: Automated Sync (Advanced)

Add script to auto-update CLAUDE.md from hugo.toml:

```bash
# scripts/sync_docs.sh
#!/bin/bash
HUGO_URL=$(grep "^baseURL" hugo.toml | cut -d"'" -f2)
sed -i "s|https://jakes-tech-insights.pages.dev|$HUGO_URL|g" CLAUDE.md
sed -i "s|https://jakeinsight.com|$HUGO_URL|g" CLAUDE.md
```

**Pros**:
- Always in sync
- No manual updates needed

**Cons**:
- Adds complexity
- Must run after every hugo.toml change

---

## Immediate Action Items

### Priority 1: Fix CLAUDE.md (Immediate)

```bash
# Update CLAUDE.md lines 38, 137
sed -i '' 's|https://jakes-tech-insights.pages.dev|https://jakeinsight.com|g' CLAUDE.md
```

### Priority 2: Fix .claude/docs/architecture.md

```bash
# Update line 68
sed -i '' 's|https://jakes-tech-insights.pages.dev|https://jakeinsight.com|g' .claude/docs/architecture.md
```

### Priority 3: Update docs/*.md files

```bash
# Update all documentation files
find docs/ -name "*.md" -exec sed -i '' 's|https://jakes-tech-insights.pages.dev|https://jakeinsight.com|g' {} \;
```

### Priority 4: Add verification note to CLAUDE.md

Add after line 26 (Project Overview section):
```markdown
**Note**: URLs in this doc may drift. Always verify live site URL with: `grep baseURL hugo.toml`
```

---

## Long-Term Prevention Measures

### 1. Documentation Maintenance Protocol

Add to CLAUDE.md or .claude/docs/maintenance.md:

```markdown
## Documentation Maintenance Rules

### When Changing Config Values

**Scope**: Any change to domain, API endpoints, project name, etc.

**Required Updates** (in order):
1. Source file (hugo.toml, .env, etc.)
2. CLAUDE.md (or reference to source)
3. README.md
4. .claude/docs/*.md (if referenced)
5. Run: `grep -r "old-value" . | grep -v node_modules | grep -v .git`

**Commit Message Format**:
```
chore: Update [config-value] across all documentation

- Source: [file] changed from X to Y
- Updated: CLAUDE.md, README.md, architecture.md
- Verified: No remaining references to old value
```

### 2. Session Start Verification

Add to mistakes-log.md or create new protocol:

```markdown
## Session Start Protocol for URL References

**Before using any URL in responses**:
1. Run: `grep baseURL hugo.toml`
2. Verify CLAUDE.md matches (if not, note discrepancy)
3. Use hugo.toml value as source of truth
4. If CLAUDE.md outdated, mention in response but proceed with correct URL
```

### 3. Quarterly Documentation Audit

Add to project calendar:

```
Every 3 months:
1. Run: `grep -r "https://" . --include="*.md" | grep -v node_modules`
2. Verify all URLs match current config
3. Update CLAUDE.md "Last Updated" date
4. Document any drift in mistakes-log.md
```

---

## Lessons Learned

### 1. Documentation Drift is Inevitable

**Insight**: Even with good documentation practices, dynamic values drift over time unless explicitly maintained.

**Solution**: Reference config files instead of duplicating values.

### 2. "Read This First" Files Need Extra Scrutiny

**Insight**: CLAUDE.md is read at every session start. Outdated info here has highest impact.

**Solution**: Mark dynamic values clearly, add "last verified" dates.

### 3. Operational vs Documentation Updates

**Insight**: Domain change focused on making site work (hugo.toml, redirects), not on documentation.

**Solution**: Add "update documentation" as explicit step in change procedures.

### 4. Single Source of Truth Must Be Explicit

**Insight**: Multiple files claimed authority. Claude couldn't determine which to trust.

**Solution**: Clearly label config files as "source of truth", docs as "reference".

### 5. Human Assumption vs Agent Behavior

**Insight**: Humans would check hugo.toml when unsure. Claude trusts "read this first" docs.

**Solution**: Teach Claude to verify config files, not just trust documentation.

---

## Success Metrics

**After implementing fixes, measure**:

1. **Immediate** (1 week):
   - [ ] Zero outdated URLs in CLAUDE.md
   - [ ] Zero outdated URLs in .claude/docs/*.md
   - [ ] Claude uses correct URL in responses

2. **Short-term** (1 month):
   - [ ] No user corrections needed for URLs
   - [ ] Documentation maintenance in all config changes
   - [ ] Verification protocol followed in sessions

3. **Long-term** (3 months):
   - [ ] Quarterly audit shows zero drift
   - [ ] Config-reference pattern adopted for all dynamic values
   - [ ] No repeated mistakes for similar values (API endpoints, etc.)

---

## Appendix: Full List of Files Requiring Updates

### Critical (User-Facing)
1. CLAUDE.md - Lines 38, 137
2. .claude/docs/architecture.md - Line 68

### Documentation (Developer-Facing)
3. docs/TECH_STACK.md - Line 31
4. docs/PROJECT_OVERVIEW.md - Line 316
5. docs/HUGO_CONFIG.md - Lines 12, 304
6. docs/MONETIZATION.md - Line 231

### Archives (Optional, For Completeness)
7. test_generation_report.md - Line 149
8. .claude/archive/v5.0-before-refactor/CLAUDE.md - Lines 82, 225, 918
9. .claude/refactor-plan-week1.md - Line 155
10. .claude/archive/reports-history/active/master-sitemap-fix-session-2026-01-22.md - Lines 122, 125, 129
11. .claude/archive/reports-history/active/cto-seo-technical-fixes-2026-01-22.md - Multiple lines
12. .claude/archive/reports-history/active/cto-broken-images-fix-2026-01-21.md - Lines 13, 24, 147
13. .claude/archive/reports-history/active/master-daily-summary-2026-01-21-mac.md - Lines 137, 418
14. .claude/archive/reports-history/active/master-daily-summary-2026-01-21.md - Lines 44, 446
15. .claude/archive/reports-history/active/qa-seo-audit-2026-01-22.md - Lines 161, 162, 254, 444-447, 635
16. .claude/archive/reports-history/active/designer-adsense-redesign-proposal-2026-01-21.md - Line 27
17. .claude/archive/reports-history/archive/2026-01/cto-domain-investigation-2026-01-20.md - Lines 24, 31-34

**Note**: Archive files can be left as historical record, but active documentation must be updated.

---

**Report Compiled By**: Claude Sonnet 4.5
**Analysis Date**: 2026-02-07
**Files Analyzed**: 17 markdown files, hugo.toml, README.md, git history (50+ commits)
**Recommendation**: Implement Option A (Reference-Based) + Priority 1-4 immediate fixes
