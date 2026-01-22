# Troubleshooting Guide

**Version**: 6.0
**Last Updated**: 2026-01-23
**Purpose**: Common error solutions

---

## Hugo Not Found

**Error**: `hugo: command not found`

**Solution**: Use full path
```bash
/opt/homebrew/bin/hugo server -D

# Or add to PATH (in ~/.zshrc or ~/.bashrc)
export PATH="/opt/homebrew/bin:$PATH"
```

---

## API Key Issues

**Error**: `anthropic.APIKeyError`

**Solution**: Check API key is set
```bash
# Verify key is set (shows first 10 chars only)
echo $ANTHROPIC_API_KEY | head -c 10

# Load from .env file
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('✅ OK' if os.getenv('ANTHROPIC_API_KEY') else '❌ MISSING')"

# Set manually (temporary)
export ANTHROPIC_API_KEY='sk-ant-...'
```

---

## Queue Stuck

**Symptom**: Topics stay in `in_progress` for hours

**Solution**: Reset stuck topics
```bash
# View current state
python scripts/topic_queue.py stats

# OR check JSON directly
cat data/topics_queue.json | python -m json.tool | grep -A 5 "in_progress"

# Reset topics stuck for 24+ hours
python scripts/topic_queue.py cleanup 24

# Verify reset
python scripts/topic_queue.py stats
```

---

## Quality Gate Failures

### Word count too low

**Error**: `Word count 650 below minimum 800`

**Solution**: Increase `max_tokens` in `generate_posts.py`
```python
# Currently at line ~1100
max_tokens=12000  # Increase to 14000 if needed
```

### AI phrases detected

**Error**: `Found blacklisted phrase: "revolutionary"`

**Solution**: Update system prompt to avoid phrase
```python
# In generate_posts.py, add to prompt:
"Never use these words: revolutionary, game-changer, cutting-edge"
```

### Missing references

**Error**: `No References section found`

**Solution**: Editor agent prompt includes references
```python
# In generate_posts.py, Editor agent section:
"Ensure ## References section with 2+ external links"
```

---

## GitHub Actions Delays

**Symptom**: Scheduled workflow runs 15-60 min late

**Explanation**: This is **normal GitHub Actions behavior**
- High load periods cause delays (esp. 12 PM KST slot)
- Content is not time-sensitive, delays are acceptable
- Historical data: 6 AM slot = 25 min delay, 12 PM = 57 min delay

**Solution**: Accept delays or reschedule to off-peak times (e.g., 3 AM UTC)

See `.claude/session-state.json` → `automation_issues` for detailed analysis.

---

## Hugo Build Errors

**Error**: `WARN: found no layout file for "HTML" for kind "page"`

**Solution**: Check template exists
```bash
# List available templates
ls -la layouts/_default/

# Verify template syntax
/opt/homebrew/bin/hugo --debug
```

**Error**: `Error: error building site: failed to render pages`

**Solution**: Check frontmatter YAML syntax
```bash
# Validate YAML in recent posts
python -c "
import yaml
from pathlib import Path
for f in Path('content/en/tech').glob('*.md'):
    with open(f) as file:
        content = file.read()
        if '---' in content:
            frontmatter = content.split('---')[1]
            try:
                yaml.safe_load(frontmatter)
            except Exception as e:
                print(f'❌ {f}: {e}')
"
```

---

**For all commands**: See `.claude/docs/commands.md`
**For architecture details**: See `.claude/docs/architecture.md`
**For development tasks**: See `.claude/docs/development.md`
