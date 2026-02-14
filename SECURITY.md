# 🔒 Security Guidelines

## API Keys Protection

### ⚠️ CRITICAL: Never Commit API Keys to Git

**What happened before:**
- API keys were accidentally included in `GOOGLE_SEARCH_INTEGRATION.md`
- GitHub detected and blocked the commit
- Had to use `git filter-repo` to clean Git history

**Prevention rules:**

1. **API keys ONLY go in `.env` file**
   - `.env` is in `.gitignore` (never committed)
   - All API keys: Anthropic, Google, Unsplash

2. **Documentation files must use placeholders**
   ```bash
   # ✅ CORRECT - Use placeholders
   ANTHROPIC_API_KEY=your-anthropic-api-key-here
   BRAVE_API_KEY=your-brave-api-key-here

   # ❌ WRONG - Real keys
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
   BRAVE_API_KEY=BSA...xxxxx
   ```

3. **Before committing any new file:**
   ```bash
   # Check for API keys
   grep -r "sk-ant-" .
   grep -r "BSA" . --include="*.md"
   grep -r "api.*key.*=" . --include="*.md"
   ```

---

## Current API Keys Location

**✅ Safe (gitignored):**
- `.env` - All production API keys

**✅ Safe (template only):**
- `.env.example` - Placeholder examples

**❌ Never put keys in:**
- Documentation files (*.md)
- Config files (*.toml, *.json)
- Scripts (*.py, *.sh)

---

## Emergency: If API Key is Exposed

1. **Immediately revoke the exposed key**
   - Anthropic Console: https://console.anthropic.com/settings/keys
   - Brave Search: https://brave.com/search/api/ (Dashboard → API Keys)
   - Unsplash: https://unsplash.com/oauth/applications

2. **Generate new key**
   - Update `.env` with new key
   - Test locally

3. **Clean Git history** (if already committed)
   ```bash
   # Install git-filter-repo
   pip3 install git-filter-repo

   # Remove file from entire history
   git filter-repo --path FILENAME.md --invert-paths --force

   # Re-add remote and force push
   git remote add origin https://github.com/USERNAME/REPO.git
   git push --force origin main
   ```

---

## Current Working Files

**Scripts (code execution):**
- `scripts/keyword_curator.py` - Reads from `.env`
- `scripts/generate_posts.py` - Reads from `.env`

**Configuration:**
- `.env` - Production keys (gitignored)
- `.env.example` - Template (safe to commit)
- `hugo.toml` - No API keys

**Data:**
- `data/topics_queue.json` - No API keys

---

## Automation Workflow

```bash
# 1. Generate keywords (uses Brave Search API + Claude API)
python3 scripts/keyword_curator.py --count 15

# 2. Generate posts (uses Claude API + Unsplash API)
python3 scripts/generate_posts.py --count 3

# 3. Commit and deploy
git add content/ data/
git commit -m "Add new posts"
git push
```

All API keys are loaded from `.env` automatically - **never hardcode them!**

---

## Checklist Before Every Commit

- [ ] No API keys in documentation files
- [ ] `.env` is in `.gitignore`
- [ ] Only commit: code, content, data files
- [ ] Check `git diff` for sensitive data

---

## API Migration History

### 2026-01-22: Google Custom Search → Brave Search API
- **Reason**: Google Custom Search JSON API discontinued for new users
- **Impact**: GOOGLE_API_KEY and GOOGLE_CX no longer required
- **New API**: BRAVE_API_KEY (from https://brave.com/search/api/)
- **Security Note**: All previous Google API keys were rotated as precaution

---

**Last Updated:** 2026-02-14
**Recent Incidents:**
- 2026-01-22: BRAVE_API_KEY exposed in git history (resolved, key rotated)
- 2026-01-17: API keys in GOOGLE_SEARCH_INTEGRATION.md (resolved)
