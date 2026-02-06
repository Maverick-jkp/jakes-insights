# A/B Test Catalog

## Purpose
Complete catalog of all available A/B tests with implementation details.

---

## Active Tests

### 1. Title Style Test

**Test ID**: `title_style`
**Status**: ✅ Active
**Start Date**: 2026-01-20

**Hypothesis**: Clickbait-style titles increase click-through rate (CTR) compared to informative titles.

**Variants**:
- **Variant A (Control)**: Informative titles
  - Example: "Understanding Machine Learning Algorithms"
  - Style: Direct, descriptive, educational
  - Length: 40-60 characters

- **Variant B (Treatment)**: Clickbait titles
  - Example: "The Ultimate Guide to Machine Learning Algorithms"
  - Style: Engaging, curiosity-driven, benefit-focused
  - Length: 50-70 characters

**Metrics to track**:
- **Primary**: CTR (clicks / impressions)
- **Secondary**: Time on page, Bounce rate, Social shares

**Expected improvement**: +15-25% CTR

**Sample size target**: 1000 pageviews per variant

**Duration**: 2-4 weeks

**Implementation**:
```python
from ab_test_manager import ABTestManager

manager = ABTestManager()
variants = manager.generate_title_variants(
    original_title="Understanding Machine Learning",
    lang="en"
)
# Returns: {"A": "Understanding...", "B": "The Ultimate Guide to..."}
```

---

### 2. Content Length Test

**Test ID**: `word_count`
**Status**: ✅ Active
**Start Date**: 2026-01-20

**Hypothesis**: Longer content (2500 words) ranks better in SEO and has higher engagement than shorter content (800 words).

**Variants**:
- **Variant A**: 800 words (Quick read)
  - Target: 800-1000 words (EN/KO), 3200-4000 chars (JA)
  - Style: Concise, focused, scannable
  - Sections: 3-4 with bullet points

- **Variant B**: 1500 words (Standard)
  - Target: 1500-1800 words (EN/KO), 6000-7200 chars (JA)
  - Style: Comprehensive, detailed
  - Sections: 4-5 with examples

- **Variant C**: 2500 words (Comprehensive)
  - Target: 2500-3000 words (EN/KO), 10000-12000 chars (JA)
  - Style: In-depth, authoritative, tutorial-like
  - Sections: 6-8 with code examples, images

**Metrics to track**:
- **Primary**: Average engagement time, SEO rankings
- **Secondary**: Scroll depth, Bounce rate, Completion rate

**Expected improvement**: Variant C: +30% time on page, better SEO

**Sample size target**: 300 pageviews per variant (3 variants = 900 total)

**Duration**: 4-8 weeks (SEO takes time)

**Implementation**:
```python
from ab_test_manager import ABTestManager

manager = ABTestManager()
target_words = manager.get_target_word_count(variant="B", lang="en")
# Returns: 1500
```

---

## Inactive Tests

### 3. Image Placement Test

**Test ID**: `image_placement`
**Status**: ⏸️ Inactive (not yet started)

**Hypothesis**: Images distributed throughout content improve engagement compared to single hero image.

**Variants**:
- **Variant A**: Hero image only (top of post)
- **Variant B**: Images throughout sections (every 2-3 paragraphs)

**Metrics to track**:
- **Primary**: Time on page, Scroll depth
- **Secondary**: Bounce rate, Page load time

**Expected improvement**: Variant B: +20% scroll depth

**Sample size target**: 500 pageviews per variant

**Duration**: 2-4 weeks

**Implementation notes**:
- Requires image sourcing strategy (Unsplash API)
- Consider page load time impact
- Mobile vs desktop differences

**Why inactive**: Focus on title and length tests first

---

### 4. CTA Position Test

**Test ID**: `cta_position`
**Status**: ⏸️ Inactive (not yet implemented)

**Hypothesis**: Mid-content CTAs convert better than end-of-post CTAs.

**Variants**:
- **Variant A**: CTA at end (after conclusion)
- **Variant B**: CTA mid-content (after 50% scroll)
- **Variant C**: CTA floating (sidebar, always visible)

**Metrics to track**:
- **Primary**: CTA click rate
- **Secondary**: Time to CTA click, Scroll depth

**Expected improvement**: Variant B: +40% CTA clicks

**Sample size target**: 1000 pageviews per variant

**Duration**: 2-4 weeks

**Implementation notes**:
- Requires Hugo template changes
- Need to define CTAs (newsletter signup, related posts, etc.)
- Track with GA4 event: `cta_click`

**Why not implemented**: No CTAs defined yet

---

## Future Test Ideas

### 5. Thumbnail Style Test

**Test ID**: `thumbnail_style` (proposed)

**Hypothesis**: Illustrated thumbnails (created with DALL-E) outperform stock photos in click rates.

**Variants**:
- **Variant A**: Stock photos (Unsplash)
- **Variant B**: Illustrated thumbnails (DALL-E 3)

**Metrics**: CTR, Social share rate

**Estimated timeline**: Q2 2026

---

### 6. Meta Description Length Test

**Test ID**: `meta_desc_length` (proposed)

**Hypothesis**: Longer meta descriptions (150+ chars) improve CTR in search results.

**Variants**:
- **Variant A**: Short (120-140 chars)
- **Variant B**: Long (150-160 chars)

**Metrics**: Organic CTR from Google Search Console

**Estimated timeline**: Q3 2026

---

### 7. Language-First Navigation Test

**Test ID**: `nav_language` (proposed)

**Hypothesis**: Showing language selector prominently increases cross-language navigation.

**Variants**:
- **Variant A**: Language selector in header
- **Variant B**: Language selector as floating button

**Metrics**: Language switch rate, Pages per session

**Estimated timeline**: Q3 2026

---

## Test Priority Matrix

| Test ID | Priority | Complexity | Impact | Status |
|---------|----------|------------|--------|--------|
| title_style | HIGH | Low | High | ✅ Active |
| word_count | HIGH | Medium | High | ✅ Active |
| image_placement | MEDIUM | Medium | Medium | ⏸️ Inactive |
| cta_position | MEDIUM | High | High | ⏸️ Not implemented |
| thumbnail_style | LOW | High | Medium | 💡 Proposed |
| meta_desc_length | LOW | Low | Low | 💡 Proposed |
| nav_language | LOW | Medium | Low | 💡 Proposed |

**Priority calculation**:
- High: Directly impacts main KPI (CTR, engagement)
- Medium: Impacts secondary KPIs
- Low: Nice-to-have, minor impact

---

## Test Lifecycle

### Phase 1: Planning (1 week)

**Activities**:
- Define hypothesis
- Choose variants
- Set success metrics
- Calculate sample size
- Document in this file

**Output**: Test specification document

---

### Phase 2: Implementation (1-2 days)

**Activities**:
- Update `scripts/ab_test_manager.py` if needed
- Modify Hugo templates
- Add GA4 tracking
- Test locally

**Output**: Working A/B test code

---

### Phase 3: Execution (2-8 weeks)

**Activities**:
- Generate content with variants
- Monitor traffic distribution
- Check GA4 data quality
- Weekly health checks

**Output**: Raw data collected

---

### Phase 4: Analysis (1 week)

**Activities**:
- Export GA4 data
- Run statistical tests (Chi-square, t-test)
- Calculate improvement %
- Document results

**Output**: Winner declaration or inconclusive

---

### Phase 5: Rollout (1 day)

**Activities**:
- Deactivate test
- Update content generation defaults
- Apply winner to all future posts
- Archive test data

**Output**: New baseline established

---

## Test Configuration Reference

### data/ab_tests.json

```json
{
  "title_style": {
    "name": "Title Style Test",
    "variants": {
      "A": "informative",
      "B": "clickbait"
    },
    "active": true,
    "split": 0.5,
    "created_at": "2026-01-20T10:00:00+09:00"
  },
  "word_count": {
    "name": "Content Length Test",
    "variants": {
      "A": "800",
      "B": "1500",
      "C": "2500"
    },
    "active": true,
    "split": 0.33,
    "created_at": "2026-01-20T10:00:00+09:00"
  },
  "image_placement": {
    "name": "Image Position Test",
    "variants": {
      "A": "top",
      "B": "section"
    },
    "active": false,
    "split": 0.5,
    "created_at": "2026-01-25T10:00:00+09:00"
  }
}
```

---

## Test Results Archive

### Title Style Test (2026-01-20 to 2026-02-05)

**Winner**: Variant B (Clickbait)

**Results**:
- Variant A CTR: 12.0%
- Variant B CTR: 15.0%
- Improvement: +25% CTR
- P-value: 0.0089 (< 0.05)
- Confidence: 95%

**Sample size**:
- Variant A: 1000 pageviews
- Variant B: 1000 pageviews

**Decision**: Apply clickbait titles to all future posts

**Date finalized**: 2026-02-05

---

## Adding New Tests

### Step 1: Document Hypothesis

**Template**:
```markdown
### X. [Test Name]

**Test ID**: `test_id_here`
**Status**: 💡 Proposed

**Hypothesis**: [What you expect to happen]

**Variants**:
- **Variant A**: [Description]
- **Variant B**: [Description]

**Metrics to track**: [Primary and secondary metrics]

**Expected improvement**: [Quantified goal]
```

---

### Step 2: Implement in Code

**Add to `scripts/ab_test_manager.py`**:
```python
manager = ABTestManager()
manager.create_test(
    test_name="new_test_id",
    variants={"A": "control", "B": "treatment"},
    active=False  # Start inactive until ready
)
```

---

### Step 3: Integrate with Content Generation

**Modify `scripts/generate_posts.py`** to:
1. Check if test active
2. Assign variant
3. Generate content based on variant
4. Inject metadata

---

### Step 4: Update This Catalog

**Add to Active Tests or Future Test Ideas section**

---

## References

- **A/B Testing Best Practices**: https://www.optimizely.com/optimization-glossary/ab-testing/
- **Statistical Significance**: `resources/statistical-testing.md`
- **GA4 Setup**: `resources/analytics-setup.md`

---

**Last Updated**: 2026-02-05
