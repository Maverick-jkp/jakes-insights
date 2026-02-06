# Analytics Setup for A/B Testing

## Purpose
Configure Google Analytics 4 (GA4) to track A/B test variants and measure performance.

---

## Prerequisites

- Google Analytics 4 property created
- GA4 tracking code installed on site
- Admin access to GA4 property

---

## Step 1: Create Custom Dimensions

### Navigate to Admin

1. Go to GA4 Admin panel
2. Select your property
3. Click "Custom definitions"
4. Click "Create custom dimension"

---

### Create ab_test_id Dimension

**Settings**:
- **Dimension name**: `ab_test_id`
- **Scope**: Event
- **Description**: A/B test identifier
- **Event parameter**: `ab_test_id`

**Click "Save"**

---

### Create ab_variant Dimension

**Settings**:
- **Dimension name**: `ab_variant`
- **Scope**: Event
- **Description**: A/B test variant assignment (A/B/C)
- **Event parameter**: `ab_variant`

**Click "Save"**

---

## Step 2: Modify Hugo Templates

### Add Meta Tags to Head

**File**: `layouts/partials/head.html`

```html
{{ if .Params.ab_test_id }}
  <meta name="ab_test_id" content="{{ .Params.ab_test_id }}">
  <meta name="ab_variant" content="{{ .Params.ab_variant }}">
{{ end }}
```

**Why**:
- Makes test metadata available to JavaScript
- Enables dynamic GA4 event tracking
- No hardcoded values

---

## Step 3: Update GA4 Tracking Code

### Enhanced Measurement Script

**File**: `layouts/partials/analytics.html`

```html
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  // Extract A/B test metadata from meta tags
  const abTestId = document.querySelector('meta[name="ab_test_id"]')?.content || 'none';
  const abVariant = document.querySelector('meta[name="ab_variant"]')?.content || 'none';

  // Send page view with custom parameters
  gtag('event', 'page_view', {
    'ab_test_id': abTestId,
    'ab_variant': abVariant
  });

  // Basic config
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

**Replace `G-XXXXXXXXXX` with your actual GA4 measurement ID**

---

## Step 4: Verify Tracking

### Test in Browser Console

1. Open any post with A/B test metadata
2. Open browser DevTools (F12)
3. Go to Console tab
4. Run:

```javascript
// Check meta tags exist
console.log('Test ID:', document.querySelector('meta[name="ab_test_id"]')?.content);
console.log('Variant:', document.querySelector('meta[name="ab_variant"]')?.content);

// Check dataLayer
console.log('DataLayer:', window.dataLayer);
```

**Expected output**:
```
Test ID: title_style
Variant: B
DataLayer: [{...}, {event: 'page_view', ab_test_id: 'title_style', ab_variant: 'B'}]
```

---

### Verify in GA4 DebugView

1. Install GA4 Debugger Chrome extension
2. Enable debug mode
3. Visit test post
4. Go to GA4 → Reports → Realtime → View events
5. Check for `page_view` event with custom parameters:
   - `ab_test_id`
   - `ab_variant`

---

## Step 5: Create Exploration Report

### Navigate to Explore

1. Go to GA4 → Explore
2. Click "Blank" to create new exploration

---

### Configure Dimensions

**Add custom dimensions**:
- ab_test_id
- ab_variant
- Page title
- Page path

**Drag to Rows**: ab_test_id, ab_variant

---

### Configure Metrics

**Add metrics**:
- Views
- Engaged sessions
- Average engagement time
- Event count
- Conversions (if configured)

**Drag to Values**: Views, Average engagement time

---

### Apply Filters

**Filter by ab_test_id**:
- Dimension: ab_test_id
- Condition: is not exactly "none"

**Why**: Exclude pages without A/B tests

---

### Example Report Structure

| ab_test_id | ab_variant | Views | Avg Engagement Time | Bounce Rate |
|------------|------------|-------|---------------------|-------------|
| title_style | A | 1,245 | 45s | 62% |
| title_style | B | 1,198 | 67s | 48% |
| word_count | A | 542 | 38s | 71% |
| word_count | B | 531 | 89s | 42% |
| word_count | C | 518 | 125s | 35% |

---

## Step 6: Set Up Comparison

### Create Segment for Variant A

1. Click "+" next to Segments
2. Select "Custom segment"
3. Add condition:
   - Dimension: ab_variant
   - Condition: is exactly "A"
4. Name: "Variant A"
5. Save

### Create Segment for Variant B

Repeat steps above with condition "is exactly B"

---

### Apply Comparison

1. Select both segments
2. GA4 automatically shows side-by-side comparison
3. Metrics displayed with % difference

---

## Step 7: Export Data for Statistical Analysis

### Export to Google Sheets

1. In Exploration report, click "Share"
2. Select "Export to Google Sheets"
3. Opens new Google Sheet with data

---

### Export to CSV

1. Click "Share" → "Download CSV"
2. Save locally
3. Use in Python for statistical testing

**Python import**:
```python
import pandas as pd

df = pd.read_csv('ab_test_data.csv')
print(df.head())

# Filter by variant
variant_a = df[df['ab_variant'] == 'A']
variant_b = df[df['ab_variant'] == 'B']

# Calculate metrics
ctr_a = variant_a['clicks'].sum() / variant_a['views'].sum()
ctr_b = variant_b['clicks'].sum() / variant_b['views'].sum()

print(f"Variant A CTR: {ctr_a:.2%}")
print(f"Variant B CTR: {ctr_b:.2%}")
```

---

## Common Metrics to Track

### Primary Metrics

| Metric | Description | Good for |
|--------|-------------|----------|
| Views | Total pageviews | Traffic volume |
| CTR | Click-through rate | Title testing |
| Avg engagement time | Time on page | Content length testing |
| Bounce rate | % single-page sessions | Content quality |

---

### Secondary Metrics

| Metric | Description | Good for |
|--------|-------------|----------|
| Scroll depth | % of page scrolled | Content length |
| Event count | Total interactions | Engagement |
| Conversions | Goal completions | CTA testing |
| Social shares | Share button clicks | Title testing |

---

## Troubleshooting

### Issue 1: Custom Dimensions Not Showing

**Symptom**: ab_test_id/ab_variant not appearing in GA4

**Possible causes**:
- Custom dimensions not created correctly
- Event parameter names mismatch
- 24-hour delay for new dimensions

**Fix**:
1. Verify custom dimension creation (Admin → Custom definitions)
2. Check event parameter names match exactly: `ab_test_id`, `ab_variant`
3. Wait 24-48 hours for GA4 to process new dimensions
4. Use DebugView to verify events sending correctly

---

### Issue 2: Meta Tags Not Found

**Symptom**: JavaScript console shows `undefined` for meta tags

**Possible causes**:
- Hugo template not updated
- Post frontmatter missing ab_test fields
- Cache not cleared

**Fix**:
1. Verify head.html includes meta tag code
2. Check post frontmatter has:
   ```yaml
   ab_test_id: "title_style"
   ab_variant: "B"
   ```
3. Clear browser cache (Ctrl+Shift+R)
4. Rebuild Hugo site: `/opt/homebrew/bin/hugo --minify`

---

### Issue 3: Events Not Sending

**Symptom**: No page_view events in DebugView

**Possible causes**:
- GA4 tracking code not installed
- JavaScript errors blocking execution
- Ad blocker interfering

**Fix**:
1. Verify GA4 script tag present in HTML source
2. Check browser console for errors
3. Disable ad blockers
4. Test in incognito mode

---

## Best Practices

### 1. Consistent Naming

**Always use**:
- `ab_test_id` (not test_id, testId, etc.)
- `ab_variant` (not variant, version, etc.)

**Why**: Consistency enables automation

---

### 2. Version Control

**Commit tracking code changes**:
```bash
git add layouts/partials/analytics.html
git commit -m "feat: Add A/B test tracking to GA4"
```

**Why**: Rollback if issues occur

---

### 3. Test Before Deploy

**Local testing**:
1. Run Hugo locally: `/opt/homebrew/bin/hugo server -D`
2. Open test post
3. Verify meta tags in page source
4. Check browser console for dataLayer

**Why**: Catch errors before production

---

### 4. Document Tests

**In CLAUDE.md or wiki**:
- Test ID and description
- Start/end dates
- Metrics tracked
- Hypothesis

**Why**: Team alignment, future reference

---

## Advanced: GTM Integration (Optional)

### Use Google Tag Manager Instead

**Benefits**:
- No code changes needed for new tests
- A/B test configs managed in GTM UI
- More flexibility for non-developers

**Setup**:
1. Create GTM container
2. Add GA4 configuration tag
3. Create custom variables for ab_test_id, ab_variant
4. Update page_view event to include variables

**Trade-off**: Additional complexity, slight performance hit

---

## Automation

### GitHub Actions Integration (Future)

**Potential workflow**:
```yaml
name: A/B Test Report
on:
  schedule:
    - cron: '0 0 * * 1'  # Monday 9 AM KST

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - name: Fetch GA4 data
        run: python scripts/fetch_ga4_data.py

      - name: Analyze results
        run: python scripts/analyze_ab_tests.py

      - name: Send report
        run: python scripts/send_report.py
```

**Not implemented yet** - manual analysis for now

---

## References

- **GA4 Custom Dimensions**: https://support.google.com/analytics/answer/10075209
- **GA4 DebugView**: https://support.google.com/analytics/answer/7201382
- **GA4 Exploration**: https://support.google.com/analytics/answer/9327974

---

**Last Updated**: 2026-02-05
