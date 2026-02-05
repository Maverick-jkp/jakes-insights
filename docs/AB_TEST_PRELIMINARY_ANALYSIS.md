# A/B Test Preliminary Analysis

**Created**: 2026-02-05
**Status**: Awaiting GSC data for performance metrics
**Test Period**: 2026-02-03 to 2026-02-04 (18 assignments)

---

## Executive Summary

**Current State**: 18 posts assigned to A/B test variants (11 Variant A, 7 Variant B)
**Test Focus**: Title style (Informative vs Clickbait)
**Next Action**: Collect 7-30 days of GSC performance data to determine winner

---

## Test Configuration

### Variant A: Informative Titles
**Style**: Direct, descriptive, keyword-focused
**Target**: Users searching for specific information
**Example Patterns**:
- Direct topic description
- Straightforward value proposition
- SEO keyword placement

### Variant B: Clickbait Titles
**Style**: Curiosity-driven, engaging, pattern-based
**Target**: Users browsing, impulsive clicks
**Example Patterns** (from [ab_test_manager.py:142-150](../scripts/ab_test_manager.py#L142-L150)):
- "5 Things You Didn't Know About {topic}"
- "{topic}: What the Experts Won't Tell You"
- "The Ultimate Guide to {topic}"
- "Everything You Need to Know About {topic}"
- "How {topic} Will Change Your Life"
- "The Secret Behind {topic}"

---

## Current Assignments

### Distribution
- **Variant A**: 11 posts (61%)
- **Variant B**: 7 posts (39%)

**Target**: 50/50 split (hash-based assignment should self-correct over time)

### Sample Posts

#### Variant B Examples (Clickbait Pattern)

**Post 1**: [cancer-san-diego](../content/en/tech/2026-02-04-cancer-san-diego.md)
- **Title**: "5 Things You Didn't Know About San Diego Biotech Breakthrough: Cancer Cells Self-Destruct"
- **Pattern**: "5 Things You Didn't Know About {}"
- **Topic**: Cancer research breakthrough
- **Language**: English
- **Category**: Tech

**Post 2**: [singles-inferno](../content/en/entertainment/2026-02-04-singles-inferno.md)
- **Title**: "Singles Inferno: What Tech Pros Can Learn From Netflix Show: What the Experts Won't Tell You"
- **Pattern**: "{}: What the Experts Won't Tell You"
- **Topic**: Reality TV + tech insights
- **Language**: English
- **Category**: Entertainment

**Post 3**: [big-pharma-molecular-glue](../content/en/tech/2026-02-04-big-pharma-molecular-glue.md)
- **Pattern**: Clickbait variant (file needs review for exact title)
- **Language**: English
- **Category**: Tech

#### Variant A Examples (Informative)

**Post 1**: [창원대](../content/ko/business/2026-02-03-창원대.md)
- **Pattern**: Informative Korean title
- **Language**: Korean
- **Category**: Business

**Post 2**: [戸田競艇](../content/ja/sports/2026-02-03-戸田競艇.md)
- **Pattern**: Informative Japanese title
- **Language**: Japanese
- **Category**: Sports

---

## Title Pattern Analysis

### Observed Clickbait Patterns in Use

Based on actual assignments:

1. **"5 Things You Didn't Know About {}"**
   - Used: cancer-san-diego post
   - Strength: Specific number creates clear expectation
   - Hook: "You Didn't Know" implies hidden insights

2. **"{}: What the Experts Won't Tell You"**
   - Used: singles-inferno post
   - Strength: Authority challenge, exclusive insights
   - Hook: Implies insider knowledge

### Pattern Characteristics

**Clickbait Variant B Strengths**:
- ✅ **Curiosity Gap**: Creates "need to know" impulse
- ✅ **Specific Numbers**: "5 Things" sets clear content expectation
- ✅ **Authority Hook**: "What Experts Won't Tell You" suggests exclusivity
- ✅ **Action Verbs**: "Discover", "Learn", "Change Your Life"

**Potential Risks**:
- ⚠️ **Overpromising**: If content doesn't deliver, bounce rate increases
- ⚠️ **SEO Keyword Dilution**: Pattern text may dilute keyword focus
- ⚠️ **Brand Perception**: May appear less authoritative

**Informative Variant A Strengths**:
- ✅ **SEO-Optimized**: Direct keyword placement
- ✅ **Clear Intent Match**: Users find exactly what they searched
- ✅ **Brand Authority**: Professional, trustworthy tone
- ✅ **Lower Bounce Risk**: Title accurately represents content

---

## Expected Outcomes (Hypothesis)

### Scenario 1: Variant B (Clickbait) Wins
**If CTR increases by 15-30%**:
- **Action**: Apply winning patterns to all future content
- **Implementation**: Update `generate_posts.py` title generation prompts
- **Expected Impact**: +20-30% traffic by Month 3

**Winning patterns to use**:
```python
clickbait_patterns = [
    "5 Things You Didn't Know About {topic}",
    "{topic}: What the Experts Won't Tell You",
    "The Ultimate Guide to {topic}",
    "How {topic} Will Change Your Life"
]
```

### Scenario 2: Variant A (Informative) Wins
**If CTR is similar or higher**:
- **Action**: Keep current informative title style
- **Reason**: SEO benefits + brand authority > clickbait CTR
- **Implementation**: No changes needed

### Scenario 3: Mixed Results
**If different patterns win for different categories**:
- **Action**: Category-specific title strategies
- **Example**:
  - Tech/Business: Informative (authority matters)
  - Entertainment/Lifestyle: Clickbait (curiosity works)
  - Education: Tutorial patterns ("How to", "Step-by-step")

---

## Metrics to Track (Once GSC Connected)

### Primary Metric: CTR (Click-Through Rate)
**Formula**: Clicks ÷ Impressions × 100
**Target**: Variant B should show 15%+ improvement to justify pattern change
**Minimum**: 7 days of data, 100+ impressions per variant

### Secondary Metrics

1. **Average Position**
   - Monitor if clickbait titles affect SEO ranking
   - Target: No degradation (maintain < 10.0 position)

2. **Bounce Rate** (from GA4, Phase 4 Week 7-8)
   - Critical: Clickbait titles may increase bounce if overpromising
   - Target: < 60% bounce rate

3. **Time on Page** (from GA4)
   - Validates if clickbait attracts right audience
   - Target: > 2 minutes avg

---

## Implementation Roadmap

### Step 1: Data Collection (Week 1-2)
- [x] A/B test assignments created (18 posts)
- [ ] GSC API setup completed (awaiting user manual config)
- [ ] Collect 30 days of performance data
- [ ] Run: `python scripts/analyze_ab_winners.py --days 30`

### Step 2: Analysis (Week 2-3)
- [ ] Review `analyze_ab_winners.py` output
- [ ] Check statistical confidence (need 30+ posts per variant)
- [ ] Validate with GA4 bounce rate data (if available)

### Step 3: Implementation (Week 3-4)
**If Variant B wins**:
- [ ] Update `scripts/generate_posts.py` title generation prompts
- [ ] Add winning patterns to system prompts
- [ ] Update `scripts/ab_test_manager.py` default patterns
- [ ] Test on 10 new posts

**If Variant A wins**:
- [ ] Document findings
- [ ] Keep current title generation
- [ ] Consider testing other elements (description, first paragraph)

### Step 4: Monitoring (Week 4+)
- [ ] Track CTR for 30 days post-implementation
- [ ] Verify traffic increase (+20-30% target)
- [ ] Monitor bounce rate (< 60% target)
- [ ] Adjust if needed

---

## Tools & Commands

### Run A/B Winner Analysis
```bash
# After GSC setup (requires 7-30 days of data)
python scripts/analyze_ab_winners.py

# Analyze specific test
python scripts/analyze_ab_winners.py --test title_style --days 30

# Save report
python scripts/analyze_ab_winners.py --output reports/ab_test_2026_02.txt
```

### View Current Assignments
```bash
# Summary
python scripts/ab_test_manager.py summary

# Raw data
cat data/ab_test_results.json | jq '.tests'

# Count by variant
cat data/ab_test_results.json | jq '.tests | group_by(.variant) | map({variant: .[0].variant, count: length})'
```

---

## Success Criteria

**Minimum Requirements**:
- ✅ 30+ posts per variant (currently: 11 vs 7, need more)
- ✅ 7+ days of GSC data
- ✅ 100+ impressions per post
- ✅ Statistical confidence: "medium" or "high"

**Decision Threshold**:
- **Adopt Variant B** if CTR improvement > 15% (high confidence)
- **Keep Variant A** if CTR difference < 5%
- **Continue testing** if 5-15% difference (medium confidence)

---

## Related Files

- **A/B Test Manager**: [scripts/ab_test_manager.py](../scripts/ab_test_manager.py)
- **Winner Analyzer**: [scripts/analyze_ab_winners.py](../scripts/analyze_ab_winners.py)
- **Test Assignments**: [data/ab_test_results.json](../data/ab_test_results.json)
- **SEO Tracker**: [scripts/seo_tracker.py](../scripts/seo_tracker.py)
- **GSC Setup Guide**: [docs/SEO_TRACKING_SETUP.md](SEO_TRACKING_SETUP.md)

---

## Next Steps

1. **User Action Required**: Complete GSC API setup (see `docs/SEO_TRACKING_SETUP.md`)
2. **Wait Period**: Allow 7-30 days for data collection
3. **Generate More Posts**: Increase to 30+ posts per variant for statistical confidence
4. **Run Analysis**: Execute `python scripts/analyze_ab_winners.py`
5. **Implement Winner**: Apply winning patterns to all future content

---

**Status**: ⏸️ **Awaiting GSC API setup + data collection**
**Expected Completion**: Week 2-3 of Phase 4
**Expected Impact**: +20-30% traffic increase by Month 3
