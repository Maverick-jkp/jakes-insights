# Quick Command Reference

## Claude Plugins

**System plugins** installed at `~/.claude/plugins/`:
- context7, code-review, security-guidance, ralph-loop, playwright

```bash
# List installed plugins
./scripts/manage_plugins.sh list

# Show plugin paths
./scripts/manage_plugins.sh path

# Open in Finder
./scripts/manage_plugins.sh open
```

## Hugo Commands

**CRITICAL**: Always use full path `/opt/homebrew/bin/hugo`

```bash
# Development server with live reload
/opt/homebrew/bin/hugo server -D

# Production build with minification
/opt/homebrew/bin/hugo --minify

# Check version
/opt/homebrew/bin/hugo version
```

## Python Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Generate 3 blog posts
python scripts/generate_posts.py --count 3

# Run quality validation
python scripts/quality_gate.py

# Run tests
pytest

# Clean stuck topics (older than 24h)
python scripts/topic_queue.py cleanup 24
```

## Git Commands

```bash
# Check status
git status

# View changes
git diff

# Commit with message
git commit -m "feat: description"

# Push to remote
git push origin main

# Fetch latest from remote
git fetch origin
```

## Environment Setup

```bash
# Load environment variables
export $(cat .env | xargs)

# Verify API keys
grep "ANTHROPIC_API_KEY" .env
grep "UNSPLASH_ACCESS_KEY" .env

# Check GitHub Actions status
gh run list --limit 5
```

## Full Reference

See `.claude/docs/commands.md` for comprehensive command documentation.
