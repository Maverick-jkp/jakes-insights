---
name: ab-test-manager
description: A/B test management for title styles, content length, image placement, and CTA positions. Use when starting new tests, analyzing results, checking test status, or managing test configurations. Includes variant assignment, metadata injection, and performance tracking.
---

# A/B Test Manager Skill

Manage A/B tests for optimizing blog content performance through controlled experiments.

---

## When to Use This Skill

**Activate this skill when:**
- User requests "ab test", "a/b test", "start test", or "analyze test"
- Need to create new A/B test configurations
- Managing active tests (start/stop/modify)
- Analyzing test results and declaring winners
- Checking test status or variant distribution
- Injecting test metadata into posts

**Do NOT use this skill for:**
- Generating content → Use `content-generation` skill
- Validating content quality → Use `quality-validation` skill
- Hugo operations → Use `hugo-operations` skill

**Examples:**
- "Start a new A/B test for title styles"
- "Analyze current test results"
- "Check test status"
- "Declare winner for word count test"

---

## Skill Boundaries

**This skill handles:**
- ✅ A/B test configuration management
- ✅ Variant assignment (deterministic hashing)
- ✅ Test metadata injection into frontmatter
- ✅ Result tracking and analysis
- ✅ Winner declaration
- ✅ Test status monitoring

**Defer to other skills:**
- ❌ Content generation → Use `content-generation` skill
- ❌ Quality validation → Use `quality-validation` skill
- ❌ Hugo operations → Use `hugo-operations` skill
- ❌ Analytics integration → Manual GA4 setup

---

## Dependencies

**Required Python packages:**
- `json` (stdlib) - Configuration management
- `hashlib` (stdlib) - Deterministic variant assignment
- `pathlib` (stdlib) - File operations
- `random` (stdlib) - Variant selection

**Installation:**
No additional packages needed - uses Python stdlib only.

**Verification:**
```bash
python -c "import json, hashlib, random; print('✓ All dependencies available')"
```

**Note**: This skill does NOT require Claude API (no API costs).

---

## Quick Start

```bash
# View test summary
python scripts/ab_test_manager.py summary

# Activate a test
python scripts/ab_test_manager.py activate title_style

# Deactivate a test
python scripts/ab_test_manager.py deactivate title_style
```

---

## Available A/B Tests

### 1. Title Style Test

**Test ID**: `title_style`
**Variants**:
- **Variant A**: Informative (original style)
- **Variant B**: Clickbait (engaging/curiosity-driven)

**Example**:
- A: "Understanding Machine Learning Algorithms"
- B: "The Ultimate Guide to Machine Learning Algorithms"

**Metrics to track**:
- Click-through rate (CTR)
- Time on page
- Bounce rate
- Social shares

---

### 2. Content Length Test

**Test ID**: `word_count`
**Variants**:
- **Variant A**: 800 words (quick read)
- **Variant B**: 1500 words (standard)
- **Variant C**: 2500 words (comprehensive)

**Adjustment for Japanese**:
- A: 3,200 characters
- B: 6,000 characters
- C: 10,000 characters

**Metrics to track**:
- Time on page
- Scroll depth
- Completion rate
- SEO rankings

---

### 3. Image Placement Test

**Test ID**: `image_placement`
**Variants**:
- **Variant A**: Top (hero image only)
- **Variant B**: Section (images throughout)

**Metrics to track**:
- Time on page
- Scroll depth
- Image load impact
- User engagement

**Status**: Currently inactive

---

## A/B Test Decision Tree

**What do you need to do?**

### 1. Start New Test

**Goal**: Begin testing new hypothesis

**Path A: Use existing test definition**

```bash
# Activate pre-configured test
python scripts/ab_test_manager.py activate title_style
```

**Path B: Create custom test**

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts')))
from ab_test_manager import ABTestManager

manager = ABTestManager()
manager.create_test(
    test_name="cta_position",
    variants={
        "A": "top",
        "B": "bottom",
        "C": "floating"
    },
    active=True
)
```

**When to use**:
- Start of new optimization phase
- Hypothesis validated through research
- Sufficient traffic for statistical significance

---

### 2. Check Test Status

**Goal**: See active tests and variant distribution

```bash
python scripts/ab_test_manager.py summary
```

**Output**:
```
📊 A/B Test Summary
==================================================
Total Tests: 3
Active Tests: 2
Total Assignments: 47

Test Details:

  title_style (✅ ACTIVE)
    Assignments: 25
    Distribution:
      Variant A: 13
      Variant B: 12

  word_count (✅ ACTIVE)
    Assignments: 22
    Distribution:
      Variant A: 8
      Variant B: 7
      Variant C: 7
```

**When to use**:
- Daily monitoring
- Before generating new content
- Verify test running correctly

---

### 3. Analyze Results

**Goal**: Determine winning variant

**Step 1: Gather analytics data**
- Go to Google Analytics 4
- Filter by custom dimension: `ab_test_id` and `ab_variant`
- Export metrics (CTR, time on page, bounce rate)

**Step 2: Calculate statistical significance**
- Use Chi-square test for CTR
- Use t-test for continuous metrics
- Require p-value < 0.05

**Step 3: Declare winner**
```python
# Document in data/ab_test_results.json
{
  "test_id": "title_style",
  "winner": "B",
  "confidence": 0.95,
  "improvement": "+23% CTR",
  "date": "2026-02-05"
}
```

**When to use**:
- After 2+ weeks of data collection
- Minimum 100 pageviews per variant
- Statistical significance achieved

---

### 4. Stop Test

**Goal**: End test and apply winning variant

```bash
# Deactivate test
python scripts/ab_test_manager.py deactivate title_style

# Apply winner to all new posts
# Update content generation settings
```

**When to use**:
- Winner declared
- Insufficient traffic (inconclusive)
- Business decision to change direction

---

## Test Configuration

### File Structure

**Configuration**: `data/ab_tests.json`
**Results**: `data/ab_test_results.json`

**ab_tests.json format**:
```json
{
  "title_style": {
    "name": "Title Style Test",
    "variants": {
      "A": "informative",
      "B": "clickbait"
    },
    "active": true,
    "split": 0.5
  }
}
```

**ab_test_results.json format**:
```json
{
  "tests": [
    {
      "post_id": "uuid-1234",
      "test_name": "title_style",
      "variant": "B",
      "assigned_at": "2026-02-05T10:00:00+09:00"
    }
  ],
  "last_updated": "2026-02-05T10:00:00+09:00"
}
```

---

## Variant Assignment

### Deterministic Hashing

**Method**: MD5 hash of `post_id + test_name`
**Benefit**: Same post always gets same variant (consistency)

```python
hash_value = int(hashlib.md5(f"{post_id}_{test_name}".encode()).hexdigest(), 16)
random.seed(hash_value)
variant = random.choice(variants)
```

**Why deterministic?**
- Re-running same post preserves variant
- Prevents variant flipping
- Enables A/B/C testing (3+ variants)

---

## Metadata Injection

### Hugo Frontmatter Integration

**Before**:
```yaml
---
title: "Understanding AI"
date: 2026-02-05
---
```

**After** (with A/B test):
```yaml
---
title: "The Ultimate Guide to Understanding AI"
date: 2026-02-05
ab_test_id: "title_style"
ab_variant: "B"
---
```

**Usage in templates**:
```html
<!-- layouts/_default/single.html -->
{{ if .Params.ab_test_id }}
  <meta name="ab_test_id" content="{{ .Params.ab_test_id }}">
  <meta name="ab_variant" content="{{ .Params.ab_variant }}">
{{ end }}
```

**Analytics integration**:
```javascript
// Send to GA4 as custom dimension
gtag('event', 'page_view', {
  'ab_test_id': document.querySelector('meta[name="ab_test_id"]').content,
  'ab_variant': document.querySelector('meta[name="ab_variant"]').content
});
```

---

## Integration with Content Generation

### Step-by-step workflow

**1. Generate post with A/B test**:
```python
from ab_test_manager import ABTestManager

manager = ABTestManager()

# Assign variant
post_id = "uuid-1234"
variant = manager.assign_variant(post_id, "title_style")

# Generate appropriate content based on variant
if variant == "B":
    title = manager.generate_title_variants(original_title, lang="en")["B"]
```

**2. Inject metadata**:
```python
frontmatter = manager.add_test_metadata(frontmatter, "title_style", variant)
```

**3. Save and track**:
- Post saved with test metadata
- Assignment recorded in `ab_test_results.json`
- Analytics picks up custom dimensions

---

## Common Operations

### Create New Test

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts')))
from ab_test_manager import ABTestManager

manager = ABTestManager()
manager.create_test(
    test_name="cta_position",
    variants={
        "A": "top",
        "B": "middle",
        "C": "bottom"
    },
    active=True
)
```

### Activate/Deactivate Test

```bash
# Activate
python scripts/ab_test_manager.py activate title_style

# Deactivate
python scripts/ab_test_manager.py deactivate title_style
```

### Get Test Summary

```bash
python scripts/ab_test_manager.py summary
```

---

## Best Practices

### Test Design

1. **One variable at a time**
   - Don't test title + length simultaneously
   - Isolate impact of single change

2. **Sufficient sample size**
   - Minimum 100 pageviews per variant
   - 2+ weeks of data collection

3. **Statistical significance**
   - p-value < 0.05 required
   - Use proper hypothesis testing

4. **Business relevance**
   - Test metrics that matter (CTR, engagement)
   - Not vanity metrics

---

### Implementation

1. **Deterministic assignment**
   - Use hashing for consistency
   - Same post = same variant

2. **Metadata tracking**
   - Always inject ab_test_id + ab_variant
   - Enables analytics filtering

3. **Documentation**
   - Record hypothesis before test
   - Document results after

4. **Winner application**
   - Update content generation rules
   - Apply to all future posts

---

## Common Issues

### Issue 1: No Variant Assigned

**Symptom**: Post has no ab_test_id in frontmatter

**Possible causes**:
- Test not active
- Assignment logic not called
- File save failed

**Fix**:
```bash
# Check test status
python scripts/ab_test_manager.py summary

# Verify test active
python scripts/ab_test_manager.py activate title_style
```

---

### Issue 2: Uneven Variant Distribution

**Symptom**: Variant A: 20, Variant B: 5

**Possible causes**:
- Hashing not random enough
- Low sample size
- Bug in assignment logic

**Fix**:
- Wait for more data (sample size issue)
- Verify hash function working correctly
- Check if certain post IDs bias distribution

---

### Issue 3: Analytics Not Tracking

**Symptom**: GA4 not showing custom dimensions

**Possible causes**:
- Custom dimensions not configured in GA4
- Meta tags not in HTML
- JS not sending data

**Fix**:
1. Configure custom dimensions in GA4
2. Verify meta tags exist: `view-source:https://yoursite.com/post`
3. Check browser console for GA4 events

---

## Analytics Setup

### Google Analytics 4 Configuration

**Step 1: Create custom dimensions**

| Dimension Name | Scope | Description |
|----------------|-------|-------------|
| ab_test_id | Event | Test identifier |
| ab_variant | Event | Variant assignment |

**Step 2: Modify tracking code**
```javascript
gtag('event', 'page_view', {
  'ab_test_id': document.querySelector('meta[name="ab_test_id"]')?.content || 'none',
  'ab_variant': document.querySelector('meta[name="ab_variant"]')?.content || 'none'
});
```

**Step 3: Create exploration report**
- Dimension: ab_test_id, ab_variant
- Metrics: Pageviews, Avg. time, Bounce rate, CTR
- Comparison: Variant A vs B vs C

---

## Automation

**No automated workflow yet** - manual triggering only

**Future enhancements**:
- GitHub Actions integration
- Automated winner declaration (statistical)
- Real-time dashboard

---

## Advanced Topics

For detailed information, see:
- **Statistical Methods**: `resources/statistical-testing.md` - Hypothesis testing, p-values
- **Analytics Integration**: `resources/analytics-setup.md` - GA4 configuration
- **Test Catalog**: `resources/test-catalog.md` - All available tests

---

## Testing

```bash
# Test manager initialization
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts')))
from ab_test_manager import ABTestManager

manager = ABTestManager()
print("✅ Manager initialized")

# Test variant assignment
variant = manager.assign_variant("test-post-123", "title_style")
print(f"✅ Assigned variant: {variant}")
EOF

# View results
python scripts/ab_test_manager.py summary
```

---

## Related Skills

- **content-generation**: Integrates A/B test variants
- **quality-validation**: Validates A/B test metadata
- **hugo-operations**: Previews posts with variants

---

## References

- **Architecture**: `.claude/docs/architecture.md`
- **Development**: `.claude/docs/development.md`
- **Commands**: `.claude/docs/commands.md`

---

**Skill Version**: 1.0
**Last Updated**: 2026-02-05
**Maintained By**: Jake's Tech Insights project
