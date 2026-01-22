# Security & Cost Optimization

**Version**: 6.0
**Last Updated**: 2026-01-23
**Purpose**: Security best practices and cost management

---

## API Keys

**Storage**:
- Local: `.env` file (NOT in git, see `.env.example`)
- GitHub Actions: Repository Secrets

**Required Secrets** (GitHub Settings → Secrets → Actions):
```
ANTHROPIC_API_KEY=sk-ant-...
UNSPLASH_ACCESS_KEY=...
```

---

## Pre-commit Validation

Recommended pattern checks (add to `.git/hooks/pre-commit`):
```bash
# Check for hardcoded keys
if git diff --cached | grep -E "(sk-ant-|ANTHROPIC_API_KEY=sk)"; then
    echo "❌ ERROR: API key detected in commit"
    exit 1
fi
```

---

## Past Incidents

See `.claude/session-state.json` → `security_incidents` for history.

**2026-01-22**: BRAVE_API_KEY exposed in git history (resolved, key rotated)

---

## Cost Optimization

### Claude API

- **Cost per post**: ~$0.09 (with prompt caching)
- **Daily cost**: $0.27 (3 posts/day)
- **Monthly cost**: ~$8.10

**Optimization**:
- Prompt caching enabled (20-25% reduction)
- `max_tokens=12000` (prevents truncation, minimizes retries)
- Structure-based prompts (3-4 sections, not strict word counts)

### Unsplash API

- **Free tier**: 50 requests/hour
- **Usage**: 9 requests/day (3 posts × 3 languages)
- **Cost**: $0/month

### Cloudflare Pages

- **Free tier**: Unlimited bandwidth, 500 builds/month
- **Usage**: ~90 builds/month (3 daily deploys)
- **Cost**: $0/month

**Total**: ~$8.10/month

---

**For architecture details**: See `.claude/docs/architecture.md`
**For troubleshooting**: See `.claude/docs/troubleshooting.md`
