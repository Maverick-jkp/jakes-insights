# Statistical Testing for A/B Tests

## Purpose
Proper statistical methods for determining A/B test winners.

---

## Required Concepts

### 1. Hypothesis Testing

**Null hypothesis (H₀)**: No difference between variants
**Alternative hypothesis (H₁)**: Variants perform differently

**Goal**: Reject H₀ with high confidence (p < 0.05)

---

### 2. P-value

**Definition**: Probability that observed difference occurred by chance

**Interpretation**:
- p < 0.05 → Statistically significant (winner declared)
- p ≥ 0.05 → Not significant (keep testing or declare inconclusive)

---

### 3. Statistical Significance

**Standard threshold**: 95% confidence (p < 0.05)
**Conservative threshold**: 99% confidence (p < 0.01)

**Why it matters**:
- Prevents false positives
- Ensures results reproducible
- Business decisions based on evidence

---

## Test Selection

### For CTR (Click-Through Rate)

**Test**: Chi-square test
**Data type**: Categorical (clicked vs not clicked)

**Formula**:
```
χ² = Σ((Observed - Expected)² / Expected)
```

**Python example**:
```python
from scipy.stats import chi2_contingency

# Data format: [[clicked_A, not_clicked_A], [clicked_B, not_clicked_B]]
data = [
    [120, 880],  # Variant A: 120 clicks, 880 non-clicks
    [150, 850]   # Variant B: 150 clicks, 850 non-clicks
]

chi2, p_value, dof, expected = chi2_contingency(data)
print(f"P-value: {p_value}")
if p_value < 0.05:
    print("✅ Statistically significant")
else:
    print("❌ Not significant")
```

---

### For Continuous Metrics (Time on Page, Bounce Rate)

**Test**: Independent t-test
**Data type**: Continuous (seconds, percentages)

**Python example**:
```python
from scipy.stats import ttest_ind

# Time on page (seconds)
variant_a = [45, 67, 34, 89, 56, ...]  # 100+ samples
variant_b = [78, 91, 62, 105, 88, ...] # 100+ samples

t_stat, p_value = ttest_ind(variant_a, variant_b)
print(f"P-value: {p_value}")
if p_value < 0.05:
    print("✅ Statistically significant")
else:
    print("❌ Not significant")
```

---

## Sample Size Requirements

### Minimum Sample Size

**Rule of thumb**:
- **CTR test**: 100+ pageviews per variant
- **Time on page**: 50+ samples per variant
- **3+ variants**: Increase by 50% per additional variant

**Why?**
- Small samples → high variance → false positives
- Large samples → reliable results → confident decisions

---

### Sample Size Calculator

**For CTR**:
```python
import math

def sample_size_ctr(baseline_ctr, min_detectable_effect, power=0.8, alpha=0.05):
    """
    baseline_ctr: Current CTR (e.g., 0.05 = 5%)
    min_detectable_effect: Minimum improvement to detect (e.g., 0.01 = 1% absolute increase)
    power: Statistical power (default 0.8 = 80%)
    alpha: Significance level (default 0.05 = 5%)
    """
    from scipy.stats import norm

    z_alpha = norm.ppf(1 - alpha/2)
    z_beta = norm.ppf(power)

    p1 = baseline_ctr
    p2 = baseline_ctr + min_detectable_effect
    p_avg = (p1 + p2) / 2

    n = ((z_alpha + z_beta)**2 * 2 * p_avg * (1 - p_avg)) / (p2 - p1)**2
    return math.ceil(n)

# Example: Detect 1% absolute CTR increase from 5% baseline
n = sample_size_ctr(baseline_ctr=0.05, min_detectable_effect=0.01)
print(f"Required sample size per variant: {n}")
```

---

## Analysis Workflow

### Step 1: Data Collection

**Minimum duration**: 2 weeks
**Rationale**: Accounts for day-of-week effects

**Export from GA4**:
1. Filter by custom dimension: `ab_test_id=title_style`
2. Break down by `ab_variant`
3. Export metrics: Pageviews, CTR, Time on page, Bounce rate

---

### Step 2: Data Validation

**Check for**:
- ✅ Equal exposure (similar pageviews per variant)
- ✅ No external events (holidays, viral posts)
- ✅ Sufficient sample size (100+ per variant)

**If unequal**:
- Investigate assignment logic
- Check if traffic source biased
- Consider weighting results

---

### Step 3: Statistical Testing

**For CTR**:
```python
from scipy.stats import chi2_contingency

# Variant A: 120 clicks / 1000 views = 12% CTR
# Variant B: 150 clicks / 1000 views = 15% CTR

data = [
    [120, 880],  # Variant A
    [150, 850]   # Variant B
]

chi2, p_value, dof, expected = chi2_contingency(data)

print(f"Chi-square: {chi2:.2f}")
print(f"P-value: {p_value:.4f}")

if p_value < 0.05:
    improvement = ((150/1000) - (120/1000)) / (120/1000) * 100
    print(f"✅ Winner: Variant B (+{improvement:.1f}% CTR)")
else:
    print("❌ No significant difference")
```

**For Time on Page**:
```python
from scipy.stats import ttest_ind

# Variant A: avg 45s
# Variant B: avg 67s

variant_a_times = [...]  # List of times (seconds)
variant_b_times = [...]

t_stat, p_value = ttest_ind(variant_a, variant_b)

if p_value < 0.05:
    print(f"✅ Winner: Variant B (+{67-45}s avg time)")
else:
    print("❌ No significant difference")
```

---

### Step 4: Winner Declaration

**Document in `data/ab_test_results.json`**:
```json
{
  "test_id": "title_style",
  "start_date": "2026-01-20",
  "end_date": "2026-02-05",
  "winner": "B",
  "metrics": {
    "ctr": {
      "variant_a": 0.12,
      "variant_b": 0.15,
      "improvement": "+25%",
      "p_value": 0.003,
      "significant": true
    },
    "time_on_page": {
      "variant_a": 45,
      "variant_b": 67,
      "improvement": "+49%",
      "p_value": 0.001,
      "significant": true
    }
  },
  "sample_size": {
    "variant_a": 1000,
    "variant_b": 1000
  },
  "confidence": 0.95
}
```

---

## Common Pitfalls

### 1. Peeking Too Early

**Problem**: Checking results daily and stopping when p < 0.05 first appears
**Why bad**: Increases false positive rate
**Solution**: Set sample size upfront, wait for target before analyzing

---

### 2. Multiple Testing

**Problem**: Testing 10 metrics, declaring winner if ANY is significant
**Why bad**: 10 tests × 5% error rate = 40% chance of false positive
**Solution**: Use Bonferroni correction (p < 0.05/10 = 0.005)

---

### 3. Ignoring Practical Significance

**Problem**: p < 0.05 but only +0.1% CTR improvement
**Why bad**: Statistically significant ≠ business relevant
**Solution**: Set minimum detectable effect (e.g., +5% CTR)

---

### 4. Unequal Sample Sizes

**Problem**: Variant A: 1000 views, Variant B: 100 views
**Why bad**: Biased results, low statistical power
**Solution**: Ensure equal traffic split (50/50)

---

## Tools and Libraries

### Python

**scipy.stats**:
- `chi2_contingency()` - CTR testing
- `ttest_ind()` - Continuous metrics
- `norm.ppf()` - Sample size calculation

**statsmodels**:
- `proportions_ztest()` - Alternative for CTR
- `power_proportions_2indep()` - Power analysis

**Installation**:
```bash
pip install scipy statsmodels
```

---

### Online Calculators

**Sample size**:
- https://www.evanmiller.org/ab-testing/sample-size.html

**Significance test**:
- https://www.evanmiller.org/ab-testing/chi-squared.html

**Why use?**:
- Quick checks without coding
- Visual understanding
- Verify Python results

---

## Practical Example

### Scenario: Title Style Test

**Hypothesis**: Clickbait titles increase CTR

**Setup**:
- Variant A: Informative titles (control)
- Variant B: Clickbait titles (treatment)
- Metric: CTR (clicks to post / total views)
- Duration: 2 weeks
- Sample size: 1000 views per variant

**Data collection**:
```python
# Week 1: 500 views per variant
# Week 2: 500 views per variant
# Total: 1000 views per variant

variant_a = {"views": 1000, "clicks": 120}  # 12% CTR
variant_b = {"views": 1000, "clicks": 150}  # 15% CTR
```

**Analysis**:
```python
from scipy.stats import chi2_contingency

data = [
    [120, 880],  # A: clicked, not clicked
    [150, 850]   # B: clicked, not clicked
]

chi2, p_value, dof, expected = chi2_contingency(data)
print(f"P-value: {p_value:.4f}")  # 0.0089

if p_value < 0.05:
    improvement = (0.15 - 0.12) / 0.12 * 100
    print(f"✅ Winner: Variant B")
    print(f"Improvement: +{improvement:.1f}% CTR")
    print(f"Confidence: 95%")
```

**Result**:
- Winner: Variant B (clickbait)
- Improvement: +25% CTR (12% → 15%)
- P-value: 0.0089 (< 0.05)
- Decision: Apply clickbait titles to all future posts

---

## References

- **Chi-square test**: https://en.wikipedia.org/wiki/Chi-squared_test
- **T-test**: https://en.wikipedia.org/wiki/Student%27s_t-test
- **Sample size**: https://www.evanmiller.org/ab-testing/sample-size.html
- **Evan Miller's blog**: https://www.evanmiller.org/ (excellent A/B testing resources)

---

**Last Updated**: 2026-02-05
