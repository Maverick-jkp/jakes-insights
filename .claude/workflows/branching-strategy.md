# Branching Strategy

**Single Source of Truth for Git Branch Management**

---

## Branch Strategy Decision

### When to Create Branches

| Complexity | Branch Required | Ticket File | Notes |
|-----------|----------------|-------------|-------|
| Simple (1-2h) | Yes | No | Prompt sufficient |
| Medium (half day) | Yes | Optional | Create ticket if complex |
| Complex (1+ day) | Yes | Yes | Document with ticket |

### Branch Patterns

**Independent Tasks (Parallel Work)**:
- Each task creates its own feature branch
- No file conflicts between branches
- Can work simultaneously in separate sessions

**Dependent Tasks (Sequential Work)**:
- Option A: Sequential branches (task-1 → task-2)
- Option B: Shared branch for related work

**Ticket Files** (Optional):
- Location: `.claude/tasks/active/TASK_XXX.md`
- After completion: Move to `.claude/tasks/archive/YYYY-MM/`

---

## Branch Naming Convention

```
feature/[work-name]    - New features
fix/[issue-name]       - Bug fixes
docs/[doc-name]        - Documentation
refactor/[target]      - Refactoring
test/[test-name]       - Test work
```

**Examples**:
- `feature/task-5-ads-integration`
- `feature/dark-mode`
- `feature/performance`
- `fix/image-placeholder-bug`
- `docs/update-readme`

---

## Parallel vs Sequential Decision

### Decision Matrix

| Condition | Parallel | Sequential |
|-----------|----------|------------|
| Different files modified | ✓ | |
| Same file modified | | ✓ |
| No dependencies | ✓ | |
| A → B dependency | | ✓ |
| Independent testing | ✓ | |
| Integration testing needed | | ✓ |

### Parallel Work Conditions

**When to work in parallel**:
- ✓ Different files modified
- ✓ No dependencies between tasks
- ✓ Can test independently
- ✓ No shared resources

**Benefits**:
- Faster execution
- Better token limit management (separate sessions)
- Independent work contexts
- Reduced conflict risk

### Sequential Work Conditions

**When to work sequentially**:
- Same file modifications
- Task A's output is Task B's input
- Integration testing required
- Shared resources/state

---

## Multi-Session Branch Workflow

### Principle: Always Use Branches

Since users run multiple Claude sessions simultaneously, working directly on main creates **conflict risks**.

### Starting Work

**1. User Specifies Branch**:
```
User: "Work on feature/task-5 branch"
→ Switch to that branch and work
```

**2. User Doesn't Specify Branch** (Most Common):
```
User: "Start Task 5"

Claude: "To prevent conflicts with other sessions,
I recommend creating a feature/task-5 branch.

Proceed with branch? Or work on main?"
```

**3. Based on User Response**:
- "Use branch" / "Yes" → Create branch and work
- "Use main" / "Just do it" → Work on main (user aware of risk)

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

---

## Integration Workflow (Master Only)

### Review All Feature Branches

```bash
# Fetch all branches
git fetch --all

# Review each branch
git checkout feature/branch-name
git log --oneline
git diff main...feature/branch-name
pytest  # Run tests
```

### Check for Conflicts

```bash
# Simulate merge
git checkout main
git merge feature/branch-name --no-commit --no-ff

# If conflicts:
git merge --abort
# → Discuss with agent and resolve

# If no conflicts:
git merge --abort  # Cancel simulation
```

### Sequential Integration

```bash
git checkout main

# Merge branches in order
git merge feature/branch-1
pytest  # Integration test

git merge feature/branch-2
pytest  # Integration test

git merge feature/branch-3
pytest  # Final integration test
```

### Final Deployment

```bash
# Final verification
pytest --cov=scripts --cov-report=term
hugo  # Build check
hugo server  # Manual test if needed

# Push to main
git push origin main

# Clean up branches (optional)
git push origin --delete feature/branch-1
git branch -d feature/branch-1
```

---

## Example: User Authentication System

**Scenario**: Complex multi-task feature requiring CTO and QA agents.

### Task Breakdown

```
TASK_001: Architecture Design (CTO)
  Branch: feature/auth-architecture
  Type: Documentation only (no code)

TASK_002: Backend API (CTO) - Depends on TASK_001
  Branch: feature/auth-backend
  Dependency: TASK_001 design

TASK_003: Tests (QA) - Depends on TASK_002
  Branch: feature/auth-tests
  Dependency: TASK_002 API
```

### Execution Plan

```
Session 1 (Master): Monitoring

Session 2 (CTO): TASK_001 (architecture docs)
  → Complete → End session

Session 3 (CTO): TASK_002 (API implementation)
  → Complete → End session

Session 4 (QA): TASK_003 (tests)
  → Complete → End session
```

### Integration (Master)

```bash
git checkout main
git merge feature/auth-architecture  # Docs
git merge feature/auth-backend       # API
git merge feature/auth-tests         # Tests
pytest  # Final verification
git push origin main
```

---

## Common Pitfalls

### 1. Parallel Work on Same File

**Problem**:
- Task 1: Modifies `layouts/baseof.html` (dark mode)
- Task 2: Modifies `layouts/baseof.html` (SEO)
- Result: Merge conflict

**Solution**:
- Change to sequential work
- OR split into smaller units (use partials)

### 2. Missing Dependencies

**Problem**:
- Task 1: Changes API schema
- Task 2: Updates code using API
- Parallel execution → Task 2 fails

**Solution**:
- Task 1 first, Task 2 after (sequential)

### 3. Non-Master Agent Merging

**Problem**:
- CTO merges their branch to main
- Integration verification skipped

**Solution**:
- Only Master has merge rights
- Other agents: commit and report back

---

## Absolute Rules

1. **No Direct main Branch Work**
   - Always create feature branch
   - Exception: Emergency hotfix (requires user approval)

2. **Master Only for Final Merge**
   - Other agents work only (no commit/push to main)
   - Master reviews and integrates all work

3. **Tests Must Pass**
   - Verify all tests pass before integration
   - Request rework if tests fail

4. **Branch Cleanup**
   - Delete merged branches (local and remote)
   - Keep main clean

---

## References

- **Master Agent Guide**: `.claude/agents/MASTER.md`
- **Feature Workflow**: `.claude/workflows/feature-workflow.md`
- **Ticket Template**: `.claude/templates/task-template.md`

---

**Last Updated**: 2026-01-20
**Version**: 1.0
**Maintained By**: Tech Lead
