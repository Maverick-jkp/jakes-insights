# Common Development Tasks

**Version**: 6.0
**Last Updated**: 2026-01-23
**Purpose**: Step-by-step guides for common tasks

---

## 1. Generate Content for Specific Keyword

```bash
# Add topic to queue
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

# View queue
python scripts/topic_queue.py stats

# Generate (will pick highest priority pending)
python scripts/generate_posts.py --count 1
```

---

## 2. Fix Stuck Topics

If topics are stuck in `in_progress` for 24+ hours:

```bash
# View stuck topics
python scripts/topic_queue.py stats

# Reset stuck topics (24+ hours)
python scripts/topic_queue.py cleanup 24

# Verify
python scripts/topic_queue.py stats
```

---

## 3. Test Content Generation Locally

```bash
# Set API key
export ANTHROPIC_API_KEY='your-key'

# Generate 1 post
python scripts/generate_posts.py --count 1

# Check quality
python scripts/quality_gate.py

# Preview
/opt/homebrew/bin/hugo server -D
```

---

## 4. Update System Prompts

Prompts are in `scripts/generate_posts.py`:

- **English**: Lines ~63-450
- **Korean**: Lines ~450-850
- **Japanese**: Lines ~850-1250

After editing:
```bash
# Test with 1 post
python scripts/generate_posts.py --count 1

# Check output quality
cat content/en/tech/2026-01-22-*.md

# Run quality gate
python scripts/quality_gate.py
```

---

## 5. Add New Category

1. **Update `hugo.toml`**: Add menu items for EN/KO/JA (lines ~30-180)
   ```toml
   [[languages.en.menu.main]]
     name = "🆕 NewCategory"
     url = "/categories/newcategory/"
     weight = 11
   ```

2. **Update validation**: Edit `scripts/utils/validation.py`
   ```python
   VALID_CATEGORIES = [
       "tech", "business", "lifestyle",
       "society", "entertainment", "sports",
       "finance", "education", "newcategory"  # Add here
   ]
   ```

3. **Create directories**:
   ```bash
   mkdir -p content/en/newcategory
   mkdir -p content/ko/newcategory
   mkdir -p content/ja/newcategory
   ```

4. **Test**:
   ```bash
   /opt/homebrew/bin/hugo server -D
   ```

---

## 6. Run Full Pipeline Test

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

## 7. Manually Trigger GitHub Actions

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

**For all commands**: See `.claude/docs/commands.md`
**For troubleshooting**: See `.claude/docs/troubleshooting.md`
**For quality standards**: See `.claude/docs/quality-standards.md`
