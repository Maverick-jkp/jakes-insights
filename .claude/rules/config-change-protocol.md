# Configuration Change Protocol

**Purpose**: Prevent documentation drift when config values change
**Created**: 2026-02-07 (after URL memory failure incident)

---

## 🔴 MANDATORY: When Changing ANY Config Value

### Step 1: Update Source of Truth
```bash
# Example: Changing domain/URL
vim hugo.toml  # or config.toml
# Update baseURL = 'https://new-domain.com'
```

### Step 2: Update Documentation (ALL)
```bash
# Update primary docs
vim CLAUDE.md              # Lines with old URL
vim README.md              # Any URL references
vim .claude/docs/*.md      # Architecture, deployment docs

# Find ALL remaining references
grep -r "old-url.com" . --exclude-dir=.git
grep -r "old-value" . --exclude-dir=.git
```

### Step 3: Verification
```bash
# Verify no hardcoded values remain in active docs
grep -r "jakes-tech-insights.pages.dev" CLAUDE.md README.md .claude/docs/

# Commit with clear message
git add .
git commit -m "docs: Update all references after [config] change

- Updated hugo.toml: [specific change]
- Updated CLAUDE.md, README.md, .claude/docs/
- Verified no outdated references remain
"
```

---

## 🎯 Common Config Values to Track

| Value | Source of Truth | Docs to Update |
|-------|----------------|----------------|
| **Domain/URL** | `hugo.toml` → baseURL | CLAUDE.md, README.md, architecture.md |
| **API Keys** | `.env` | security.md, troubleshooting.md |
| **Build Commands** | `package.json` / scripts/ | commands.md, development.md |
| **Deployment Target** | `.github/workflows/` | architecture.md, deployment docs |
| **Hugo Path** | System-specific | CLAUDE.md, commands.md, quickstart.md |

---

## 📝 Documentation Update Template

When updating docs after config change:

```markdown
<!-- Before -->
- Live Site: https://old-domain.com

<!-- After (Option A: Direct reference) -->
- Live Site: https://new-domain.com

<!-- After (Option B: Config reference - RECOMMENDED) -->
- Live Site: See `baseURL` in hugo.toml (currently: new-domain.com)
- Note: Always verify current value in hugo.toml

<!-- After (Option C: Automated) -->
- Live Site: {{< config "baseURL" >}}  # Hugo shortcode
```

**Recommended**: Option B or C to prevent future drift

---

## 🚨 Red Flags (What Went Wrong This Time)

❌ **Jan 24**: Changed hugo.toml → jakeinsight.com
❌ **Jan 24**: Updated robots.txt, deployment files
❌ **Feb 3**: Updated README.md (10 days late!)
❌ **Feb 7**: CLAUDE.md still outdated (14 days!)

✅ **Should have been**:
- Single commit updating ALL references
- Verification step with grep
- Documentation update checklist

---

## 🔧 Claude-Specific Prevention

### Before Using Config Values in Responses:

```bash
# 1. Check source of truth first
grep baseURL hugo.toml

# 2. Use that value, NOT what's in CLAUDE.md
# Even if CLAUDE.md is outdated

# 3. Report discrepancy if found
"Note: CLAUDE.md shows X, but hugo.toml shows Y. Using Y (source of truth)."
```

### Session Start Verification:
```bash
# Always verify critical values
grep baseURL hugo.toml
grep ANTHROPIC_API_KEY .env
which hugo  # /opt/homebrew/bin/hugo
```

---

## 📊 Incident Report: URL Memory Failure

**Date**: 2026-02-07
**Issue**: Claude repeatedly used outdated URL (jakes-tech-insights.pages.dev)
**Root Cause**: CLAUDE.md not updated when domain changed 14 days prior
**Impact**: Incorrect URLs in responses, 404 errors
**Prevention**: This protocol document + immediate fixes

**Full Analysis**: `.claude/sessions/2026-02-07/url-memory-failure-analysis.md`

---

## ✅ Immediate Actions Taken

1. [x] Root cause analysis completed
2. [ ] Update CLAUDE.md lines 38, 137 → jakeinsight.com
3. [ ] Update .claude/docs/architecture.md line 68
4. [ ] Verify no other outdated URLs in active docs
5. [ ] Add this protocol to .claude/rules/
6. [ ] Update CLAUDE.md to reference this protocol

---

## 🔄 Quarterly Audit (Future)

**Every 3 months**, run this verification:

```bash
# 1. Extract current config values
grep baseURL hugo.toml
grep ANTHROPIC_API_KEY .env

# 2. Search for outdated references
grep -r "jakes-tech-insights.pages.dev" . --exclude-dir=.git
grep -r "old-api-key" . --exclude-dir=.git

# 3. Update any found discrepancies
# 4. Document in changelog
```

---

**Last Updated**: 2026-02-07
**Next Audit**: 2026-05-07
