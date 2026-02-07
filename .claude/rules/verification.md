# Pre-Action Verification Checklist

**Before attempting to "fix" ANY reported issue:**

```bash
# Step 1: Verify problem exists locally
git status
git diff

# Step 2: Check if already fixed in remote repository
git fetch origin
git show origin/main:path/to/file | grep "search-term"

# Step 3: Verify environment files exist
ls -la .env
ls -la .git/config

# Step 4: If issue involves environment variables, verify they exist
grep "VARIABLE_NAME" .env

# Step 5: Check documented procedures FIRST
# Example: .claude/docs/commands.md line 20 shows how to load .env
# DO NOT improvise - follow documented method
```

## CRITICAL RULES

1. ❌ **NEVER assume** user's report means issue currently exists - verify first
2. ❌ **NEVER improvise** solutions when documented procedures exist
3. ❌ **NEVER claim** files/keys/tools are missing without checking
4. ✅ **ALWAYS verify** current state before attempting any fix
5. ✅ **ALWAYS follow** documented procedures exactly as written
6. ✅ **ALWAYS check** if issue already resolved in previous session

**If verification shows issue is already fixed**: Report findings, do NOT redo the work.
