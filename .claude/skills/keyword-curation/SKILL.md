---
name: keyword-curation
description: Community-sourced keyword research and topic queue state management (pending → in_progress → completed). Use when curating new keywords from community sources (HackerNews, Dev.to, Lobsters, ProductHunt), adding topics to queue, checking queue status, or fixing stuck topics. Includes duplicate prevention and priority management (1-10 scale).
---

# Keyword Curation Skill

Community-sourced (HackerNews, Dev.to, Lobsters, ProductHunt) keyword research and topic queue state management for content generation.

---

## When to Use This Skill

**Activate this skill when:**
- User requests "keywords", "topic queue", "curate keywords", or "add topic"
- Need to fetch trending keywords from community sources (HN, Dev.to, Lobsters, ProductHunt)
- Managing topic queue (check status, add/remove topics)
- Fixing stuck topics (in_progress for 24+ hours)
- Checking queue health (pending count, priority distribution)

**Do NOT use this skill for:**
- Generating content from keywords → Use `content-generation` skill
- Validating content quality → Use `quality-validation` skill
- Hugo operations → Use `hugo-operations` skill

**Examples:**
- "Curate new keywords"
- "Add topic to queue"
- "Check queue status"
- "Fix stuck topics"

---

## Skill Boundaries

**This skill handles:**
- ✅ Community keyword fetching (HackerNews, Dev.to, Lobsters, ProductHunt)
- ✅ Topic queue state management (pending/in_progress/completed)
- ✅ Manual topic addition with priority
- ✅ Stuck topic cleanup (24+ hours)
- ✅ Queue health monitoring
- ✅ Duplicate prevention

**Defer to other skills:**
- ❌ Content generation → Use `content-generation` skill
- ❌ Quality validation → Use `quality-validation` skill
- ❌ Hugo operations → Use `hugo-operations` skill
- ❌ Automated curation → GitHub Actions workflow

---

## Dependencies

**Required Python packages:**
- `anthropic` - Claude API for keyword selection
- `requests` - HTTP requests to community APIs
- `python-dotenv` - Environment variable loading

**Installation:**
```bash
pip install -r requirements.txt
```

**Note**: Requires `ANTHROPIC_API_KEY`. `BRAVE_API_KEY` is optional (used for reference fetching).

---

## Quick Start

```bash
# View queue status
python scripts/topic_queue.py stats

# Curate new keywords (auto mode, 10 trend keywords)
python scripts/keyword_curator.py --count 10 --auto

# Fix stuck topics
python scripts/topic_queue.py cleanup 24
```

---

## Topic Queue State Machine

### States

```
pending → in_progress → completed
             ↓
           failed (retry)
```

1. **pending** - Ready to be processed
2. **in_progress** - Currently generating
3. **completed** - Successfully published
4. **failed** - Generation failed (will auto-retry)

### File Structure

**Location**: `data/topics_queue.json`

**Format**:
```json
{
  "topics": [
    {
      "id": "uuid-1234",
      "keyword": "AI trends 2026",
      "category": "tech",
      "language": "en",
      "priority": 8,
      "status": "pending",
      "created_at": "2026-01-23T18:00:00+09:00"
    }
  ]
}
```

---

## Queue Management Decision Tree

**What do you need to do with the topic queue?**

### 1. Check Queue Status

**Goal**: See how many topics are pending/in progress/completed

→ **Command**: `python scripts/topic_queue.py stats`
→ **Output**: Total, pending, in_progress, completed counts
→ **When to use**: Before generating content, health check

**Healthy queue indicators**:
- ✅ Pending: 10-20 topics (daily 10 keywords in, 10 posts out)
- ✅ In progress: 0-3 topics
- ✅ Completed: Growing steadily

**Unhealthy indicators**:
- ⚠️ Pending <5 → Need to curate keywords
- ⚠️ In progress >3 → Topics stuck, run cleanup
- ⚠️ Pending >50 → Backlog piling up

---

### 2. Add Topics Manually

**Goal**: Add specific keyword to queue

**Path A: Single topic (recommended)**

→ **Method**: Python code snippet
```python
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
```

**Path B: Bulk add from list**

→ **Method**: Use keyword curator with manual filtering
→ **See decision #3**

**Validation**:
- Category must be one of 8 valid
- Language must be en/ko/ja
- Priority 1-10 (10 = highest)
- Duplicates automatically prevented

---

### 3. Curate Keywords from Community Sources

**Goal**: Add 10 trending tech keywords to queue (EN 5 + KO 5)

→ **Command**: `python scripts/keyword_curator.py --count 10 --auto`
→ **Process**: Fully automated (Claude selects from ~100 community candidates)
→ **When to use**: Daily automation, or manually when queue is low

**Curation flow**:
1. Script fetches ~25 top posts from each source (HN, Dev.to, Lobsters, ProductHunt)
2. Claude selects 10 tech-relevant keywords (EN 5 + KO 5)
3. Non-tech keywords auto-filtered (sports, entertainment, weather)
4. Brave Search fetches references per keyword
5. Keywords added to queue (duplicates auto-prevented)

**Filtering criteria**:
- ✅ **Keep** if: Tech-related (AI, cloud, dev tools, cybersecurity, OSS)
- ❌ **Auto-rejected**: Sports, entertainment, weather, person names

---

### 4. Fix Stuck Topics

**Goal**: Reset topics stuck in "in_progress" for 24+ hours

**Symptom**: `python scripts/topic_queue.py stats` shows in_progress >3

→ **Command**: `python scripts/topic_queue.py cleanup 24`
→ **Action**: Resets status from `in_progress` → `pending`
→ **When to use**: After generation failures, before retry

**Why topics get stuck**:
- Generation script crashed mid-run
- API errors during content creation
- Manual interruption (Ctrl+C)

**After cleanup**:
- Run content generation again
- Topics will be picked up fresh

---

### 5. View Queue Contents

**Goal**: See full list of topics with details

→ **Command**: `cat data/topics_queue.json | jq '.topics'`
→ **Or**: `cat data/topics_queue.json | jq '.topics[] | select(.status=="pending")'`
→ **When to use**: Debug, verify topics added

**Filter by status**:
```bash
# Pending only
jq '.topics[] | select(.status=="pending")' data/topics_queue.json

# In progress only
jq '.topics[] | select(.status=="in_progress")' data/topics_queue.json

# By category
jq '.topics[] | select(.category=="tech")' data/topics_queue.json
```

---

### 6. Remove Topic

**Goal**: Delete specific topic from queue

→ **Not recommended** (no built-in command)
→ **Workaround**: Manually edit `data/topics_queue.json`
→ **Better approach**: Let it complete or fail naturally

**If you must remove**:
1. Open `data/topics_queue.json`
2. Find topic by keyword or ID
3. Delete entire topic object
4. Save file
5. Verify: `python scripts/topic_queue.py stats`

---

## Queue Operations

### View Status

```bash
python scripts/topic_queue.py stats

# Output:
# Total topics: 74
# Pending: 14
# In progress: 0
# Completed: 60
```

### Add Topic

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts')))
from topic_queue import add_topic

add_topic(
    keyword="Your Keyword",
    category="tech",  # or business, lifestyle, etc.
    language="en",    # or ko, ja
    priority=8        # 1-10 (10 = highest)
)
```

### Cleanup Stuck Topics

```bash
# Reset topics stuck for 24+ hours
python scripts/topic_queue.py cleanup 24
```

---

## Keyword Curation

### Community Sources

**All free, no auth required**:
- **HackerNews**: Firebase API (top/new stories, 25 items)
- **Dev.to**: REST API (top articles, 25 items)
- **Lobsters**: JSON feed (recent posts, 25 items)
- **ProductHunt**: Atom RSS (today's launches, 25 items)

### Curation Process

```bash
# Automated (daily via GitHub Actions at 4 PM KST)
python scripts/keyword_curator.py --count 10 --auto

# Manual run (same, no prompts)
python scripts/keyword_curator.py --count 10 --auto
```

**Flow**: ~100 community candidates → Claude selects 10 (EN 5 + KO 5) → Brave Search adds references → queue

### Filtering Criteria

**Auto-kept if**:
- ✅ Tech-related (AI, cloud, dev tools, cybersecurity, open source, startups)
- ✅ Not already in queue

**Auto-rejected if**:
- ❌ Sports, entertainment, weather, person names
- ❌ Non-tech keywords (prompt + post-processing filter)

---

## Categories

**Valid category** (tech-only strategy):

1. **tech** - Technology, AI, software, cloud, cybersecurity, dev tools
7. **finance** - Investing, economics
8. **education** - Learning, courses

---

## Priority System

| Priority | When to Use |
|----------|-------------|
| 10 | Urgent / breaking news |
| 8-9 | High interest / trending |
| 5-7 | Normal / standard |
| 3-4 | Low interest / backup |

**Default**: 8 (trending keywords from community sources)

---

## Queue Health Monitoring

### Ideal Queue State

**Pending topics**: 10-20
- Too few (< 5): Risk of queue empty
- Too many (> 50): Backlog piling up

**In progress**: 0-3
- 0 = Good (no active generation)
- > 3 = Stuck (needs cleanup)

**Completed**: Growing by 10/day (1 run × 10 posts)

---

## Common Issues

### Issue 1: Queue Empty

**Symptom**: 0 pending topics

**Fix**:
```bash
# Immediate: Curate keywords
python scripts/keyword_curator.py --count 10 --auto
```

### Issue 2: Topics Stuck

**Symptom**: Topics in `in_progress` for hours/days

**Fix**:
```bash
# View stuck topics
python scripts/topic_queue.py stats

# Reset (24+ hours)
python scripts/topic_queue.py cleanup 24
```

---

## Automation

**GitHub Actions**: `.github/workflows/daily-keywords.yml`
**Schedule**: Daily, 4 PM KST
**Count**: 10 keywords per run (EN 5 + KO 5)
**Sources**: HackerNews, Dev.to, Lobsters, ProductHunt (~100 candidates → 10 selected)

**Content Generation**: `.github/workflows/daily-content.yml`
**Schedule**: 7 PM KST
**Consumption**: 10 topics/day (1 run × 10 posts)

---

## Advanced Topics

For detailed information, see:
- **Queue Management**: `resources/queue-management.md` - State machine, operations
- **Curation Guide**: `resources/curation-guide.md` - Keyword selection, filtering
- **Best Practices**: `resources/best-practices.md` - Maintenance, distribution

---

## Testing

```bash
# Test add topic
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts')))
from topic_queue import add_topic

add_topic(
    keyword="Test Keyword",
    category="tech",
    language="en",
    priority=5
)
print("✅ Topic added")
EOF

# Verify
python scripts/topic_queue.py stats
```

---

## Related Skills

- **content-generation**: Uses queue for post generation
- **quality-validation**: Validates generated content
- **hugo-operations**: Previews generated posts

---

## References

- **Architecture**: `.claude/docs/architecture.md`
- **Development**: `.claude/docs/development.md`
- **Commands**: `.claude/docs/commands.md`

---

**Skill Version**: 1.3
**Last Updated**: 2026-01-24
**Maintained By**: Jake's Tech Insights project
