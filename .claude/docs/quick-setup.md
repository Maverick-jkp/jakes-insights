# Quick Setup Guide (New PC)

**Last Updated**: 2026-02-14
**Setup Time**: ~5 minutes (for required APIs only)

---

## Prerequisites

```bash
# Required tools
- Python 3.11+
- Hugo (via Homebrew on macOS)
- Git

# Check versions
python --version  # Should be 3.11+
/opt/homebrew/bin/hugo version  # Hugo should be installed
git --version
```

---

## 1. Install Hugo (macOS)

```bash
# Install via Homebrew
brew install hugo

# Verify installation
/opt/homebrew/bin/hugo version

# ⚠️ IMPORTANT: Hugo is at /opt/homebrew/bin/hugo (NOT in PATH)
# Always use full path: /opt/homebrew/bin/hugo
```

---

## 2. Clone Repository

```bash
git clone https://github.com/Maverick-jkp/jakes-tech-insights.git
cd jakes-tech-insights
```

---

## 3. Setup Python Environment

```bash
# Install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import anthropic; print('✅ Dependencies installed')"
```

---

## 4. Configure API Keys (REQUIRED)

### Step 1: Copy .env.example

```bash
cp .env.example .env
```

### Step 2: Get Required API Keys

You need **3 required APIs** to run content generation:

| API | Purpose | Get From | Cost |
|-----|---------|----------|------|
| **Anthropic (Claude)** | Content generation | https://console.anthropic.com/settings/keys | Pay-as-you-go |
| **Unsplash** | Featured images | https://unsplash.com/developers | Free (50 req/hr) |
| **Brave Search** | Keyword research & RAG | https://brave.com/search/api/ | Free tier available |

### Step 3: Add Keys to .env

```bash
# Edit .env file
vim .env  # or use any text editor

# Add your API keys:
ANTHROPIC_API_KEY=sk-ant-api03-xxx
UNSPLASH_ACCESS_KEY=xxx
BRAVE_API_KEY=BSAxxxxx
```

### Step 4: Verify Configuration

```bash
# Test API keys
python scripts/generate_posts.py --count 1

# Should see:
#   ✓ ANTHROPIC_API_KEY: Configured
#   ✓ UNSPLASH_ACCESS_KEY: Configured
#   🖼️  Unsplash API enabled
```

---

## 5. Test Local Development

```bash
# Start Hugo development server
/opt/homebrew/bin/hugo server -D

# Visit: http://localhost:1313
```

---

## 6. Optional APIs (Can Skip Initially)

These are **NOT required** for basic content generation:

### Dev.to Cross-Posting (Optional)

```bash
# Get API key from: https://dev.to/settings/extensions
DEVTO_API_KEY=xxx
```

### Google Indexing API (Optional)

```bash
# Setup service account at: https://console.cloud.google.com/apis/credentials
# Save JSON to: credentials/google-indexing-credentials.json
GOOGLE_INDEXING_CREDENTIALS=credentials/google-indexing-credentials.json
```

### Google Search Console API (Optional)

```bash
# Setup service account at: https://console.cloud.google.com/apis/credentials
# Save JSON to: config/gsc-service-account.json
GSC_SERVICE_ACCOUNT_FILE=config/gsc-service-account.json
GSC_PROPERTY_URL=https://jakeinsight.com
```

---

## 7. Generate First Post

```bash
# Generate 1 test post
python scripts/generate_posts.py --count 1

# Check output
ls -la content/en/  # Should see new post
ls -la content/ko/  # Korean version
```

---

## 8. GitHub Actions Setup (For Automation)

If you want to deploy to production with GitHub Actions:

```bash
# 1. Fork repository on GitHub
# 2. Go to: Settings → Secrets and variables → Actions
# 3. Add repository secrets:

ANTHROPIC_API_KEY       # Your Claude API key
UNSPLASH_ACCESS_KEY     # Your Unsplash API key
BRAVE_API_KEY           # Your Brave Search API key (optional but recommended)
DEVTO_API_KEY           # Your Dev.to API key (optional)
GOOGLE_INDEXING_CREDENTIALS  # Service account JSON (optional)
```

---

## 9. Verify Everything Works

```bash
# Run tests
pytest

# Generate content
python scripts/generate_posts.py --count 1

# Build site
/opt/homebrew/bin/hugo --minify

# Check output
ls -la public/  # Should see built site
```

---

## Quick Command Reference

```bash
# Content generation
python scripts/generate_posts.py --count 5

# Local development
/opt/homebrew/bin/hugo server -D

# Production build
/opt/homebrew/bin/hugo --minify

# Run tests
pytest

# Check topic queue
python scripts/topic_queue.py status

# Clean stuck topics (if needed)
python scripts/topic_queue.py cleanup 24
```

---

## Troubleshooting

### "hugo: command not found"

```bash
# Hugo is at /opt/homebrew/bin/hugo
# Use full path or add to PATH:
export PATH="/opt/homebrew/bin:$PATH"
```

### "ANTHROPIC_API_KEY not found"

```bash
# Verify .env file exists and has correct key
cat .env | grep ANTHROPIC_API_KEY

# Load .env in current shell (if needed)
export $(cat .env | xargs)

# Or run with explicit env:
ANTHROPIC_API_KEY=xxx python scripts/generate_posts.py --count 1
```

### "UNSPLASH_ACCESS_KEY not found"

```bash
# Check .env file
cat .env | grep UNSPLASH_ACCESS_KEY

# Script will work but skip images if missing
# To enable images, add key to .env
```

### "BRAVE_API_KEY not found"

```bash
# Brave API is optional but recommended
# Keyword curation will fall back to Claude-only mode without it
# Add to .env to enable:
BRAVE_API_KEY=BSAxxxxx
```

---

## What's Different from Old Setup?

| Feature | Old (2025) | New (2026-02) | Status |
|---------|------------|---------------|--------|
| Search API | Google Custom Search | Brave Search | ✅ Active |
| Content Pipeline | Single-language | Bilingual (EN/KO) | ✅ Active |
| Image Source | Unsplash | Unsplash | ✅ Same |
| AI Model | Claude Sonnet 3.5 | Claude Sonnet 4.5 | ✅ Updated |
| Deployment | Cloudflare Pages | Cloudflare Pages | ✅ Same |
| Domain | jakes-tech-insights.pages.dev | jakeinsight.com | ✅ Updated |

---

## API Cost Estimates (for 5 posts/day)

| API | Usage | Cost/Month (Estimated) |
|-----|-------|------------------------|
| **Claude (Anthropic)** | ~150k tokens/day | $15-30/month |
| **Unsplash** | 5 images/day | Free (50/hr limit) |
| **Brave Search** | 10 queries/day | Free tier |
| **Dev.to** | 5 posts/day | Free |
| **Google Indexing** | 5 URLs/day | Free |

**Total**: ~$15-30/month (just Claude API)

---

## Next Steps

1. ✅ Setup complete - You can now generate content
2. Read `.claude/docs/development.md` for detailed workflows
3. Check `.claude/docs/troubleshooting.md` if issues occur
4. Review `.claude/docs/quality-standards.md` for content guidelines

---

**Need help?** Check:
- `.claude/docs/troubleshooting.md` - Common issues
- `.claude/docs/commands.md` - All commands
- `.claude/docs/architecture.md` - System overview
