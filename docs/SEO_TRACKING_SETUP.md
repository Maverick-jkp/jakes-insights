# SEO Performance Tracking Setup Guide

**Version**: 1.0
**Date**: 2026-02-05
**Owner**: Jake Park

---

## 🎯 Goal

Track SEO performance metrics from Google Search Console to make data-driven content decisions.

---

## 📊 Metrics to Track

### Per Post
- **Impressions**: How many times post appeared in search results
- **Clicks**: How many users clicked through
- **CTR**: Click-through rate (clicks / impressions)
- **Average Position**: Average ranking position in search results

### Aggregate
- **Top 10 posts**: By traffic (clicks)
- **Top performing categories**: By CTR
- **Trending topics**: Week-over-week growth
- **Low performers**: Posts with high impressions but low CTR

---

## 🔧 Setup Steps

### Step 1: Enable Google Search Console API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: "jakes-tech-insights-seo"
3. Enable "Google Search Console API"
4. Create credentials:
   - Type: Service Account
   - Name: "seo-tracker"
   - Role: Viewer
5. Download JSON key file
6. Save as: `config/gsc-service-account.json`

### Step 2: Grant Access in GSC

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Select property: `https://jakeinsight.com`
3. Settings → Users and permissions → Add user
4. Email: `[service-account-email]@[project-id].iam.gserviceaccount.com`
5. Permission: Full (for read access)

### Step 3: Add to .env

```bash
# Google Search Console API
GSC_SERVICE_ACCOUNT_FILE=config/gsc-service-account.json
GSC_PROPERTY_URL=https://jakeinsight.com
```

### Step 4: Install Python Package

```bash
pip install google-api-python-client google-auth
```

---

## 📝 Script Structure

### File: `scripts/seo_tracker.py`

```python
#!/usr/bin/env python3
"""
SEO Performance Tracker

Fetches performance data from Google Search Console API.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
from datetime import datetime, timedelta
from pathlib import Path

class SEOTracker:
    def __init__(self, service_account_file, property_url):
        """Initialize GSC API client"""
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )
        self.service = build('searchconsole', 'v1', credentials=credentials)
        self.property_url = property_url

    def get_performance_data(self, start_date, end_date, dimensions=['page']):
        """
        Fetch performance data for date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            dimensions: List of dimensions ['page', 'query', 'country', 'device']

        Returns:
            List of performance data rows
        """
        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': dimensions,
            'rowLimit': 25000  # Max rows
        }

        response = self.service.searchanalytics().query(
            siteUrl=self.property_url,
            body=request
        ).execute()

        return response.get('rows', [])

    def get_top_posts(self, days=30, limit=10):
        """Get top performing posts by clicks"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        data = self.get_performance_data(start_date, end_date, ['page'])

        # Sort by clicks
        sorted_data = sorted(data, key=lambda x: x['clicks'], reverse=True)

        return sorted_data[:limit]

    def analyze_post_performance(self, url):
        """Get detailed performance for specific post"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        # Get page performance
        data = self.get_performance_data(start_date, end_date, ['page'])

        # Find matching URL
        for row in data:
            if row['keys'][0] == url:
                return {
                    'impressions': row['impressions'],
                    'clicks': row['clicks'],
                    'ctr': row['ctr'],
                    'position': row['position']
                }

        return None

    def generate_weekly_report(self):
        """Generate weekly SEO performance report"""
        # This week
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        # Last week (for comparison)
        last_week_end = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        last_week_start = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')

        this_week = self.get_performance_data(start_date, end_date, ['page'])
        last_week = self.get_performance_data(last_week_start, last_week_end, ['page'])

        # Calculate totals
        this_week_clicks = sum(row['clicks'] for row in this_week)
        last_week_clicks = sum(row['clicks'] for row in last_week)

        growth = ((this_week_clicks - last_week_clicks) / last_week_clicks * 100) if last_week_clicks > 0 else 0

        report = {
            'period': f'{start_date} to {end_date}',
            'total_clicks': this_week_clicks,
            'week_over_week_growth': f'{growth:.1f}%',
            'top_posts': sorted(this_week, key=lambda x: x['clicks'], reverse=True)[:10]
        }

        return report


def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()

    tracker = SEOTracker(
        service_account_file=os.getenv('GSC_SERVICE_ACCOUNT_FILE'),
        property_url=os.getenv('GSC_PROPERTY_URL')
    )

    # Generate report
    report = tracker.generate_weekly_report()

    print("=" * 80)
    print("SEO PERFORMANCE REPORT")
    print("=" * 80)
    print(f"Period: {report['period']}")
    print(f"Total Clicks: {report['total_clicks']}")
    print(f"Week-over-Week Growth: {report['week_over_week_growth']}")
    print()
    print("Top 10 Posts:")
    for i, post in enumerate(report['top_posts'], 1):
        url = post['keys'][0]
        clicks = post['clicks']
        impressions = post['impressions']
        ctr = post['ctr'] * 100
        print(f"{i}. {url}")
        print(f"   Clicks: {clicks} | Impressions: {impressions} | CTR: {ctr:.2f}%")
        print()


if __name__ == '__main__':
    main()
```

---

## 📅 Usage

### Weekly Report
```bash
python scripts/seo_tracker.py
```

### Top Posts (Last 30 Days)
```python
from scripts.seo_tracker import SEOTracker
import os

tracker = SEOTracker(
    os.getenv('GSC_SERVICE_ACCOUNT_FILE'),
    os.getenv('GSC_PROPERTY_URL')
)

top_posts = tracker.get_top_posts(days=30, limit=10)
```

### Specific Post Analysis
```python
performance = tracker.analyze_post_performance('https://jakeinsight.com/tech/2026-02-04-cancer-san-diego/')
print(f"Clicks: {performance['clicks']}")
print(f"CTR: {performance['ctr']:.2%}")
```

---

## 🔄 Automation

### GitHub Actions: `.github/workflows/weekly-seo-report.yml`

```yaml
name: Weekly SEO Report

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC

jobs:
  seo-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install google-api-python-client google-auth

      - name: Generate SEO Report
        env:
          GSC_SERVICE_ACCOUNT_FILE: ${{ secrets.GSC_SERVICE_ACCOUNT }}
          GSC_PROPERTY_URL: https://jakeinsight.com
        run: |
          python scripts/seo_tracker.py > reports/seo-$(date +%Y-%m-%d).txt

      - name: Commit Report
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add reports/
          git commit -m "📊 Weekly SEO report - $(date +%Y-%m-%d)"
          git push
```

---

## 📈 Expected Insights

### What We'll Learn
1. **Best performing content types**: Tutorial vs Analysis vs News
2. **High CTR topics**: What titles/topics drive clicks
3. **Search intent patterns**: Which queries find our content
4. **Geographic distribution**: Where traffic comes from
5. **Device breakdown**: Mobile vs Desktop performance

### Actions Based on Data
- ✅ Generate more content on high-performing topics
- ✅ Improve titles for high-impression, low-CTR posts
- ✅ Update old content that's losing rankings
- ✅ Identify keyword gaps (high impressions, low rank)

---

## 💰 Cost

**Google Search Console API**: FREE ✅
- No API costs
- Rate limit: 1,200 queries/minute
- More than sufficient for our needs

---

## 🔒 Security

### Important
- ❌ NEVER commit `gsc-service-account.json` to Git
- ✅ Add to `.gitignore`: `config/gsc-service-account.json`
- ✅ Use GitHub Secrets for automation
- ✅ Limit service account to read-only access

### .gitignore Entry
```
# Google Search Console
config/gsc-service-account.json
```

---

## ✅ Checklist

- [ ] Google Cloud project created
- [ ] Search Console API enabled
- [ ] Service account created and key downloaded
- [ ] Access granted in GSC
- [ ] `.env` updated with credentials
- [ ] Python packages installed
- [ ] Script tested successfully
- [ ] .gitignore updated
- [ ] Weekly automation setup (optional)

---

## 🐛 Troubleshooting

### Error: "User does not have sufficient permissions"
**Solution**: Check service account has been added to GSC property with appropriate permissions.

### Error: "Invalid credentials"
**Solution**: Verify JSON key file path in `.env` is correct and file exists.

### Error: "Property not found"
**Solution**: Ensure `GSC_PROPERTY_URL` matches exactly with property in Search Console (include https://).

---

## 📚 Resources

- [Google Search Console API Docs](https://developers.google.com/webmaster-tools/v1/how-tos/search_analytics)
- [Python Client Library](https://github.com/googleapis/google-api-python-client)
- [Service Account Setup](https://cloud.google.com/iam/docs/service-accounts)

---

**Status**: Ready for implementation
**Next Step**: Create Google Cloud project and service account
