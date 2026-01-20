# Troubleshooting Guide

## Common Issues and Solutions

This document provides solutions to frequently encountered issues when working with Jake's Tech Insights.

## Issue 1: Hugo Server Not Showing New Content

### Symptoms
- New posts generated successfully
- Files exist in `content/en/`, `content/ko/`, or `content/ja/`
- Posts not visible when browsing `localhost:1313`
- No errors in Hugo server output

### Cause
Hugo server caches content and may not detect new file changes immediately.

### Solution

**Option 1: Restart Hugo Server**
```bash
# Stop server (Ctrl+C)
# Restart with drafts enabled
hugo server -D

# Or with custom Hugo binary
~/hugo_bin server -D
```

**Option 2: Force Rebuild**
```bash
# Clear public directory
rm -rf public/

# Rebuild and serve
hugo server -D
```

**Option 3: Check Draft Status**
```yaml
# Ensure draft is false in frontmatter
draft: false
```

## Issue 2: Workflow Files Not Pushing to GitHub

### Symptoms
- Git push succeeds for content files
- Workflow files (`.github/workflows/*.yml`) not appearing in remote repository
- No error messages during push

### Cause
GitHub requires special permission scope for pushing workflow files via API or token.

### Solution

**Option 1: Push All Files Together**
```bash
# Add all files including workflows
git add .

# Commit
git commit -m "Add workflows and content"

# Push
git push origin main
```

**Option 2: Create Workflow via GitHub UI**
1. Go to repository on GitHub.com
2. Click "Actions" tab
3. Click "New workflow"
4. Click "set up a workflow yourself"
5. Paste workflow YAML content
6. Commit directly to main branch

**Option 3: Update GitHub Token Permissions**
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate new token with `workflow` scope enabled
3. Update local git credentials with new token

## Issue 3: Stuck Topics in Queue

### Symptoms
- Topics remain in `in_progress` status indefinitely
- New topics not being processed
- Queue appears "stuck"

### Cause
Topics reserved but generation script crashed or was interrupted before completion.

### Solution

**Run Cleanup Command:**
```bash
# Clean up topics stuck for more than 24 hours
python scripts/topic_queue.py cleanup 24

# More aggressive: 12 hours
python scripts/topic_queue.py cleanup 12
```

**Manual Reset:**
```bash
# Edit data/topics_queue.json
# Find stuck topic and change status:
{
  "id": "001-en-tech-ai-coding",
  "status": "in_progress",  # Change to "pending"
  "reserved_at": "2026-01-15T..."  # Remove this field
}
```

**Check Queue Stats:**
```bash
# View current queue state
python scripts/topic_queue.py stats

# Output shows:
# - Total topics
# - Pending/In Progress/Completed counts
# - Topics stuck > 24 hours
```

## Issue 4: Content Truncation

### Symptoms
- Posts end mid-sentence
- Word count below target (< 800 words)
- Japanese posts extremely short (< 1,000 characters)
- Quality gate failures

### Cause
Insufficient `max_tokens` allocation for Claude API completion.

### Solution

**Already Implemented (Day 5):**
```python
# In scripts/generate_posts.py
max_tokens=12000  # Increased from 4000 → 8000 → 12000
```

**Verify Configuration:**
```python
# Check generate_posts.py contains:
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=12000,  # Must be 12000
    # ...
)
```

**If Issue Persists:**
1. Check API response for truncation warnings
2. Verify prompt length isn't consuming too many tokens
3. Consider using prompt caching for system prompts

**Cost Impact:**
- 12K tokens: ~$0.09/post
- Prevents truncation, ensures completion
- See `docs/MONETIZATION.md` for cost analysis

## Issue 5: Posts Hidden on Production

### Symptoms
- Posts visible locally with `hugo server`
- Missing on Cloudflare Pages deployment
- No build errors in Cloudflare logs

### Causes and Solutions

**Cause 1: Missing Timezone**

Posts interpreted as "future posts" due to timezone mismatch.

**Solution:**
```yaml
# Add timezone to all post dates
date: 2026-01-17T12:00:00+09:00  # Note the +09:00
```

```toml
# In hugo.toml
timeZone = 'Asia/Seoul'
```

**Cause 2: Draft Status**

Posts marked as draft are hidden in production.

**Solution:**
```yaml
# Ensure draft is false
draft: false
```

**Cause 3: Future Dates**

Post date is ahead of current server time.

**Solution:**
```bash
# Check post date vs. current date
date  # Current server date

# Ensure post date is not in future
# Adjust if necessary
```

## Issue 6: Broken Thumbnails

### Symptoms
- Post cards show broken image icons
- Images fail to load on homepage/category pages
- Console shows 404 errors for images

### Causes and Solutions

**Cause 1: SVG Files Named as JPG**

SVG files saved with `.jpg` extension.

**Solution:**
```bash
# Use actual JPEG images from Unsplash
python scripts/fetch_images_for_posts.py

# Or manually download and replace
# Save as actual .jpg files, not .svg
```

**Cause 2: Incorrect Image Paths**

Frontmatter points to non-existent image location.

**Solution:**
```yaml
# Correct path (relative to static/)
image: "/images/thumbnails/my-image.jpg"

# File should exist at:
# static/images/thumbnails/my-image.jpg
```

**Cause 3: Missing Images**

Image files not committed to repository.

**Solution:**
```bash
# Check if images exist
ls static/images/thumbnails/

# Add missing images
git add static/images/thumbnails/*.jpg
git commit -m "Add missing thumbnails"
git push
```

## Issue 7: Category Pages Broken

### Symptoms
- Category pages show no styling
- Full post content displayed in cards (extremely long)
- Images appearing in card previews
- Missing category descriptions

### Cause
CSS class conflicts and missing content filtering.

### Solution

**Already Fixed (Day 6):**
- Renamed `.post-content` to `.card-content` in layouts
- Added `{{ .Summary | plainify | truncate 120 }}` for text-only excerpts
- Added multilingual category descriptions
- Fixed CSS conflicts in `custom.css`

**Verify Fix:**
```bash
# Check layouts/categories/list.html contains:
{{ .Summary | plainify | truncate 120 }}

# Not:
{{ .Content }}
```

## Issue 8: Latest Widget Showing Only 2 Items

### Symptoms
- Latest widget shows 2 posts instead of 3
- Scrollbar appears in widget
- Featured post duplicated in Latest

### Cause
Incorrect range logic including featured post.

### Solution

**Already Fixed (Day 6):**
```html
<!-- Correct: Skip featured post -->
{{ range after 1 (first 4 $currentLangPages) }}
  <!-- Shows posts 2-4 -->
{{ end }}
```

**Verify Fix:**
```bash
# Check layouts/index.html contains:
{{ range after 1 (first 4 $currentLangPages) }}
```

## Issue 9: Reading Time Incorrect

### Symptoms
- Reading time shows "33 min" or "44 min" for short posts
- Unrealistic time estimates

### Cause
Hugo's built-in reading time calculation using full HTML content.

### Solution

**Already Fixed (Day 6):**
- Removed reading time display from all-posts page
- Deleted `.post-card-footer` section

**Verify Fix:**
```bash
# layouts/_default/all-posts.html should NOT contain:
.post-card-footer
.reading-time
{{ .ReadingTime }}
```

## Issue 10: Floating Menu Missing

### Symptoms
- No navigation menu on category/post pages
- Users can't navigate back to homepage

### Cause
Missing floating menu implementation in layouts.

### Solution

**Already Fixed (Day 6):**
- Added floating menu to all page types
- Hamburger icon with links to home, all posts, categories

**Verify Fix:**
```bash
# Check these files contain floating menu:
layouts/categories/list.html
layouts/_default/single.html
layouts/_default/all-posts.html
```

## Workflow Debugging

### GitHub Actions Not Triggering

**Check Workflow Syntax:**
```bash
# Validate YAML syntax
yamllint .github/workflows/daily-content.yml
```

**Check Schedule Format:**
```yaml
# Correct cron format
schedule:
  - cron: '0 3 * * *'  # 12 PM KST (3 AM UTC)
```

**Check Branch Protection:**
- Workflows may be disabled on protected branches
- Check repository settings > Actions > General

### GitHub Actions Failing

**Check Logs:**
1. Go to repository > Actions tab
2. Click on failed workflow run
3. Expand failed step to see error details

**Common Failures:**

**API Key Missing:**
```yaml
# Ensure secret is set in repository settings
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Python Dependencies:**
```yaml
# Ensure requirements.txt is up to date
pip install -r requirements.txt
```

**Hugo Version:**
```yaml
# Ensure compatible Hugo version
- name: Setup Hugo
  uses: peaceiris/actions-hugo@v2
  with:
    hugo-version: '0.120.0'
```

## Quality Gate Failures

### Word Count Too Low

**Error:**
```
FAIL: Word count too low (750 words, minimum 800)
```

**Solution:**
- Increase `max_tokens` in generate_posts.py
- Adjust target word count in prompts
- Regenerate post

### AI Phrases Detected

**Warning:**
```
WARN: AI phrases detected: "revolutionary", "game-changer"
```

**Solution:**
- Warnings don't block deployment (by design)
- Review post manually if needed
- Update Editor Agent prompt to avoid these phrases

### Missing Frontmatter

**Error:**
```
FAIL: Missing required frontmatter: description
```

**Solution:**
```yaml
# Add missing field to frontmatter
description: "Meta description here (120-160 chars)"
```

## AI Reviewer Issues

### Low Scores

**Output:**
```json
{
  "recommendation": "REVISE",
  "average_score": 6.5
}
```

**Solution:**
- Review suggestions in `ai_review_report.json`
- Manually edit post based on feedback
- Or regenerate with improved prompts

### Reviewer Fails to Run

**Error:**
```
FileNotFoundError: No posts found to review
```

**Solution:**
```bash
# Ensure posts exist in content directories
ls content/en/**/*.md
ls content/ko/**/*.md
ls content/ja/**/*.md

# Or specify file explicitly
python scripts/ai_reviewer.py --file content/en/tech/2026-01-17-my-post.md
```

## General Debugging Tips

### Enable Verbose Logging

```bash
# Hugo verbose mode
hugo server -D --verbose

# Python scripts with debug logging
python scripts/generate_posts.py --debug
```

### Check File Permissions

```bash
# Ensure scripts are executable
chmod +x scripts/*.py

# Ensure data directory is writable
chmod 755 data/
```

### Verify Environment Variables

```bash
# Check API key is set
echo $ANTHROPIC_API_KEY

# If empty, set it
export ANTHROPIC_API_KEY="your-key-here"
```

### Clear Caches

```bash
# Clear Hugo cache
hugo --gc

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
```

## Getting Help

If issues persist after trying these solutions:

1. **Check Logs:**
   - Hugo: `hugo server --verbose`
   - GitHub Actions: Actions tab > Workflow run > Logs
   - Python scripts: Add `--debug` flag if available

2. **Review Documentation:**
   - `docs/` directory for specific topics
   - `PROJECT_CONTEXT.md` for system overview

3. **Check Git History:**
   ```bash
   # See recent changes
   git log --oneline -10

   # See what changed in specific file
   git log -p path/to/file
   ```

4. **Test in Isolation:**
   - Test queue system: `python scripts/test_queue.py`
   - Test single post generation: `python scripts/generate_posts.py --count 1`
   - Test quality gate: `python scripts/quality_gate.py`

## Prevention Tips

### Before Generating Content

- [ ] Verify queue has pending topics: `python scripts/topic_queue.py stats`
- [ ] Check API key is set: `echo $ANTHROPIC_API_KEY`
- [ ] Ensure Hugo server is running: `hugo server -D`

### Before Deploying

- [ ] Run quality gate: `python scripts/quality_gate.py`
- [ ] Check all images load: Browse site locally
- [ ] Verify frontmatter: Check `draft: false` and timezone
- [ ] Test on mobile: Use browser dev tools

### Before Pushing to GitHub

- [ ] Review git status: `git status`
- [ ] Check for sensitive data: No API keys in commits
- [ ] Verify workflows: `.github/workflows/*.yml` are valid YAML
- [ ] Test locally first: Don't rely on GitHub Actions for testing
