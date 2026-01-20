# Claude Instructions - Quick Reference

**Read this file FIRST before starting any work.**

---

## Critical - Never Forget

### Hugo Local Server - Always Available

```
Binary: /opt/homebrew/bin/hugo
Version: 0.154.5+extended
Local Testing: MANDATORY before deployment
Default Port: 1313
```

**Commands**:
```bash
# Start Hugo server
/opt/homebrew/bin/hugo server --port 1313 --bind 0.0.0.0

# Test URLs
http://localhost:1313/ko/categories/tech/
http://localhost:1313/
```

**QA Process (REQUIRED for UI/Layout changes)**:
1. Start Hugo local server
2. Test changes visually in browser
3. Document results in QA docs
4. THEN commit and push

**Why This Matters**:
- UI changes CANNOT be validated by reading code alone
- Thumbnails, layouts, styling must be tested visually
- "I cannot run Hugo locally" is NEVER acceptable

---

## Essential Checklist (Before Any Work)

Follow this order:

1. **Read Guidelines**:
   - `docs/CLAUDE_GUIDELINES.md` - Work principles
   - `docs/AUTOMATION_CONTEXT.md` - System structure
   - `docs/WORK_LOG.md` - Recent work history

2. **Check Problem-Specific Sections**:
   - Image issues → CLAUDE_GUIDELINES.md "Unsplash Image Management"
   - Deployment issues → CLAUDE_GUIDELINES.md "Absolute Prohibitions"
   - API calculations → CLAUDE_GUIDELINES.md "Past Mistakes"

3. **Never Guess**:
   - In guidelines → Reference only
   - Not in guidelines → Read files, confirm, then add

---

## Core Principles

### Principle 1: Documentation First
```
Question received → Check guidelines → Found: reference | Not found: investigate + add
```

### Principle 2: Never Guess
```
Uncertain → "I'll check" → Read files → Accurate answer
```

### Principle 3: Prevent Duplication
```
Same logic repeated ❌
Reference link to guidelines ✅
```

---

## Common Questions Quick Reference

### Q: Why aren't images showing?
→ [CLAUDE_GUIDELINES.md § Unsplash Image Management](docs/CLAUDE_GUIDELINES.md)
- Missing placeholder files
- Run "Fix Placeholder Images" workflow

### Q: Do I need to run local server?
→ [CLAUDE_GUIDELINES.md § Absolute Prohibitions](docs/CLAUDE_GUIDELINES.md)
- ❌ Hugo local server not needed for deployment
- ✅ Git Push → Cloudflare auto-build

### Q: How many API calls?
→ [AUTOMATION_CONTEXT.md § API Usage](docs/AUTOMATION_CONTEXT.md)
- Keyword generation: Google API 30 calls
- Content generation: Claude API (unlimited company account)

### Q: How to prevent duplicate images?
→ [CLAUDE_GUIDELINES.md § Duplicate Prevention](docs/CLAUDE_GUIDELINES.md)
- Track in `used_images.json`
- Select unused images from Unsplash API results

---

## Git Branch Workflow (Multi-Session Environment)

### Principle: All Work on Branches

Users run multiple Claude sessions simultaneously. Working directly on main creates **conflict risks**.

### Starting Work

**1. User specifies branch**:
```
User: "Work on feature/task-5 branch"
→ Switch to that branch and work
```

**2. User doesn't specify branch (most common)**:
```
User: "Start Task 5"

Claude: "To prevent conflicts with other sessions,
I recommend creating a feature/task-5 branch.

Proceed with branch? Or work on main?"
```

**3. Based on user response**:
- "Use branch" / "Yes" → Create branch and work
- "Use main" / "Just do it" → Work on main (user aware of risk)

### Branch Naming
```
feature/[work-name]    - New features
fix/[issue-name]       - Bug fixes
docs/[doc-name]        - Documentation
refactor/[target]      - Refactoring
test/[test-name]       - Testing
```

**Examples**:
- `feature/task-5-ads-integration`
- `fix/image-placeholder-bug`
- `docs/update-readme`

### After Work Completion
```bash
# 1. Commit
git add -A
git commit -m "feat: description"

# 2. Push
git push origin feature/[branch-name]

# 3. Notify user
"Pushed to feature/[branch-name].
Merge to main?"
```

### Exceptions
- **Urgent fixes**: Only when user explicitly says "work on main directly"
- **Simple queries**: File reading, status checks don't need branch proposal

---

## Absolute Prohibitions

1. ❌ Start work without reading guidelines
2. ❌ Answer with guesses for speed
3. ❌ Repeat same logic explanations
4. ❌ Try to run Hugo local server for deployment
5. ❌ Say "I think..." or "probably..."
6. ❌ **Say "I cannot" definitively**:
   - **GitHub CLI**: `/opt/homebrew/bin/gh`
   - **Hugo**: See "Critical - Never Forget" section above
   - Command fails → Check PATH → Retry with full path
   - Not "can't do" but "find the way"
7. ❌ **Work on main when user didn't specify branch**:
   - Always propose branch work and get user confirmation

---

## Must Always Do

1. ✅ Check guidelines before work
2. ✅ Read files and confirm before answering
3. ✅ Provide reference links to guidelines
4. ✅ Document new discoveries immediately
5. ✅ "I'll check" → Investigate → Accurate answer

---

**Following these instructions prevents token waste and repeated work.**
**Read this file and CLAUDE_GUIDELINES.md before starting any work.**
