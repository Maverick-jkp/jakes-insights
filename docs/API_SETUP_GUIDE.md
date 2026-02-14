# API Setup Guide

## Critical: API Credentials Required

Your content generation requires the following API credentials to be configured:

1. ✅ **Brave Search API** - For keyword research and references
2. ✅ **Unsplash API** - For featured images
3. ✅ **Claude API** - For content generation

---

## 🔴 IMMEDIATE ACTION REQUIRED

### Step 1: Set Up Brave Search API (REQUIRED)

**Why Brave?** Google Custom Search API was deprecated for new users as of January 2026.

#### 1.1 Create Brave Search API Account
1. Go to https://brave.com/search/api/
2. Click **Sign Up**
3. Complete email verification
4. Navigate to Dashboard → **API Keys** section
5. Click **Create New Key**
6. **Copy the API Key** → This is your `BRAVE_API_KEY`

#### 1.2 Pricing & Limits
- **Free Tier**: 2,000 queries/month (~66 queries/day)
- **Overage Cost**: $0.55 per 1,000 queries
- **Expected Usage**: ~120 queries/month (well within free tier)

#### 1.3 Configure GitHub Secrets
1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Add the following repository secrets:
   - `BRAVE_API_KEY`: Your Brave Search API key
   - `UNSPLASH_ACCESS_KEY`: Your Unsplash Access Key (see Step 2)
   - `ANTHROPIC_API_KEY`: Your Claude API key

---

### Step 2: Set Up Unsplash API (Image Downloads)

#### 2.1 Create Unsplash Developer Account
1. Go to https://unsplash.com/developers
2. Register/Login
3. Create a new application
4. Copy your **Access Key** → This is your `UNSPLASH_ACCESS_KEY`

#### 2.2 Add to GitHub Secrets
1. Settings → Secrets and variables → Actions
2. Add new secret:
   - Name: `UNSPLASH_ACCESS_KEY`
   - Value: Your Unsplash Access Key

---

### Step 3: Set Up Claude API

#### 3.1 Create Anthropic Account
1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy your **API Key** → This is your `ANTHROPIC_API_KEY`

#### 3.2 Add to GitHub Secrets
1. Settings → Secrets and variables → Actions
2. Add new secret:
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your Anthropic API key

---

## 🧪 Testing Locally

### Test Keyword Curation
```bash
export ANTHROPIC_API_KEY="your-key"
export BRAVE_API_KEY="your-brave-api-key"

python scripts/keyword_curator.py --count 5
```

**Expected Output:**
- ✓ Should fetch trending topics from Google Trends
- ✓ Should search for references using Brave Search
- ✓ Should extract 2 references per keyword
- ✓ Should show "All 5 keywords have references!" message

**If you see warnings:**
- ⚠️ "Brave Search API key not found" → API key not set
- ⚠️ "X keywords have NO references" → Brave API quota exceeded or invalid credentials

### Test Content Generation
```bash
export ANTHROPIC_API_KEY="your-key"
export UNSPLASH_ACCESS_KEY="your-unsplash-key"

python scripts/generate_posts.py --count 1
```

**Expected Output:**
- ✓ Pre-flight check should show all API keys configured
- ✓ Should download real Unsplash images (not placeholders)
- ✓ Should include references section in generated posts
- ✓ Quality check should PASS with no warnings

---

## 🚨 Common Issues

### Issue 1: "No references generated"
**Cause:** Brave Search API credentials missing or invalid

**Fix:**
1. Verify `BRAVE_API_KEY` is set correctly
2. Check Brave Dashboard: Is API key active?
3. Check usage limits: Free tier is 2,000 queries/month

### Issue 2: "Placeholder images used"
**Cause:** `UNSPLASH_ACCESS_KEY` not configured

**Fix:**
1. Get Unsplash Access Key from https://unsplash.com/developers
2. Add to GitHub Secrets: `UNSPLASH_ACCESS_KEY`
3. Verify the key is valid by testing locally

### Issue 3: "API quota exceeded"
**Cause:** Brave Search has limits (2,000 queries/month on free tier)

**Temporary Fix:**
- Reduce keyword count: `--count 5` instead of `--count 15`

**Permanent Fix:**
- Monitor usage in Brave Dashboard
- Upgrade to paid tier if needed ($0.55/1,000 queries)

---

## 📊 Monitoring

### Check Workflow Logs
1. Go to Actions tab in GitHub
2. Click on "Daily Keyword Curation" workflow
3. Look for warnings:
   - "Brave Search API key not found"
   - "X keywords have NO references"

### Validate Generated Content
1. Check `data/topics_queue.json`
2. Look for `"references": []` (empty array = BAD)
3. Should see `"references": [{"title": "...", "url": "...", "source": "..."}]`

### Test Posts
1. Check generated posts in `content/*/tech/*.md`
2. Search for "## References" section
3. Verify images are NOT placeholder paths (`/images/placeholder-*.jpg`)

---

## ✅ Success Criteria

When properly configured, you should see:

1. ✅ Keywords have 1-2 references each in `topics_queue.json`
2. ✅ Posts include "## References" section with real URLs
3. ✅ Posts use downloaded Unsplash images (not placeholders)
4. ✅ No warnings in workflow logs about missing credentials
5. ✅ Quality gate passes with "All posts have references and real images!"

---

## 🔧 Emergency Fallback

If you can't configure Brave API immediately:

1. **Option A**: Use existing keywords from queue (already curated)
2. **Option B**: Manually add references to posts after generation
3. **Option C**: Generate keywords without references (not recommended - SEO impact)

**Long-term:** You MUST configure Brave Search API for sustainable content generation.

---

## 📝 Migration Notes

### Google Custom Search API → Brave Search API (2026-01-22)

**Why we switched:**
- Google Custom Search JSON API discontinued for new users
- All Google API requests returned 403 Forbidden
- Brave Search offers better pricing and higher quotas

**Benefits:**
- 20x more free queries (2,000/month vs 100/day)
- 11x cheaper ($0.55/1K vs $5/1K)
- Simpler setup (no Custom Search Engine required)
- Better privacy (no user tracking)

**For detailed migration report:** See `.claude/reports/active/brave-api-migration-success-2026-01-22.md`

---

**Last Updated:** 2026-02-14
