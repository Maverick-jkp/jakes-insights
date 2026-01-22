# Command Reference

**Version**: 6.0
**Last Updated**: 2026-01-23
**Purpose**: All command-line operations reference

---

## Hugo Commands

**CRITICAL**: Hugo is installed at `/opt/homebrew/bin/hugo` (not in PATH).
Always use the full path:

```bash
# Start development server (with drafts)
/opt/homebrew/bin/hugo server -D

# Production build
/opt/homebrew/bin/hugo --minify

# Check version
/opt/homebrew/bin/hugo version

# Build and check errors
/opt/homebrew/bin/hugo --minify 2>&1 | grep -i error
```

---

## Python Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Required environment variables
export ANTHROPIC_API_KEY='your-key'
export UNSPLASH_ACCESS_KEY='your-key'  # For featured images

# Load from .env file (recommended)
# File location: /Users/jakepark/projects/jakes-tech-insights/.env
python -c "from dotenv import load_dotenv; load_dotenv()"
```

---

## Testing

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_topic_queue.py

# Run with verbose output
pytest -v

# Coverage report (HTML)
pytest --cov=scripts --cov-report=html
# View at htmlcov/index.html

# Quick validation (no API calls)
python scripts/topic_queue.py stats
```

---

## Content Generation Pipeline

```bash
# 1. Curate keywords (weekly, ~5 min manual filtering)
python scripts/keyword_curator.py --count 15

# 2. Generate posts (automated, uses topic queue)
python scripts/generate_posts.py --count 3

# 3. Run quality checks (automated in CI)
python scripts/quality_gate.py

# 4. AI review (optional, recommendation only)
python scripts/ai_reviewer.py

# 5. Local preview
/opt/homebrew/bin/hugo server -D
# Visit http://localhost:1313
```

---

## Topic Queue Management

```bash
# View queue statistics
python scripts/topic_queue.py stats

# Add topic manually
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts')))
from topic_queue import add_topic

add_topic(
    keyword="Your Keyword",
    category="tech",
    language="en",
    priority=8
)
print("✅ Topic added to queue")
EOF

# Cleanup stuck topics (24+ hours)
python scripts/topic_queue.py cleanup 24
```

---

## Git Workflow

```bash
# Check status
git status

# Check diff
git diff

# Check remote state (before assuming issues)
git fetch origin
git show origin/main:path/to/file

# Stage files
git add [files]

# Commit with co-authored message
git commit -m "$(cat <<'EOF'
[type]: [description]

[Optional details]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

# Push to remote
git push origin main
```

---

## Environment Verification

**Before claiming anything is "missing", ALWAYS run these:**

```bash
# Step 1: Verify problem exists locally
git status
git diff

# Step 2: Check if already fixed in remote repository
git fetch origin
git show origin/main:path/to/file | grep "search-term"

# Step 3: Verify environment files exist
ls -la .env
ls -la .git/config

# Step 4: If issue involves environment variables, verify they exist
grep "VARIABLE_NAME" .env

# Step 5: Load .env properly (documented method)
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('✅ OK' if os.getenv('ANTHROPIC_API_KEY') else '❌ MISSING')"
```

---

## GitHub Actions (Manual Trigger)

1. Go to **Actions** tab on GitHub
2. Select **Daily Content Generation**
3. Click **Run workflow**
4. Set parameters:
   - count: 3 (default)
   - skip_review: false
5. Click **Run workflow**
6. Wait for completion (~5 min)
7. Review PR created by workflow

---

## Full Pipeline Test

```bash
# 1. Check queue
python scripts/topic_queue.py stats

# 2. Generate
python scripts/generate_posts.py --count 1

# 3. Quality gate
python scripts/quality_gate.py

# 4. AI review (optional)
python scripts/ai_reviewer.py

# 5. Hugo build
/opt/homebrew/bin/hugo --minify

# 6. Preview
/opt/homebrew/bin/hugo server -D
```

---

**For architecture details**: See `.claude/docs/architecture.md`
**For troubleshooting**: See `.claude/docs/troubleshooting.md`
**For development tasks**: See `.claude/docs/development.md`
