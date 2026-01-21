# Agent Mistakes Log

## Purpose
This file records every workflow violation to prevent repeating past mistakes.
All agents MUST review this file at session start.

---

## 2026-01-22: Designer committed without creating report

**What happened**: Designer agent completed homepage layout redesign but committed changes directly without creating a work report first.

**Rule broken**:
- STEP 3: Create Work Report FIRST
- STEP 4: NEVER commit or push

**Impact**:
- Workflow disrupted
- No documentation of changes
- User had to remind about protocol
- Time wasted on process correction

**Root cause**:
1. Did not read DESIGNER.md before starting work
2. Skipped documentation review step
3. Assumed "good work = can commit immediately"
4. Confused with Master's authority (only Master commits)

**Prevention measures taken**:
1. Added CRITICAL WORKFLOW RULES section to all agent docs
2. Added ASCII warning boxes for visual emphasis
3. Added session start checklist (7 steps)
4. Created this mistakes-log.md file
5. Fixed contradictory rules in DESIGNER.md
6. Removed duplicate sections to reduce cognitive load

**Lesson learned**:
- Rules existed but were not visually prominent
- Need checklist format, not just text instructions
- Specialized agents (Designer/CTO/QA) NEVER commit
- Only Master has commit authority

---

## How to Use This File

**Before starting ANY work**:
1. Read this file completely
2. Check if your planned action appears in past mistakes
3. If similar situation exists, follow prevention measures
4. If uncertain, ASK first, don't proceed

**After making a mistake**:
1. Document it here immediately
2. Explain what happened, why, and impact
3. Identify root cause
4. List prevention measures
5. Commit this file update

---

**Last Updated**: 2026-01-22
**Maintained By**: All agents
