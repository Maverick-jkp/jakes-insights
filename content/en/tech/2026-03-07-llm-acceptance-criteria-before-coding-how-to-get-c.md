---
title: "LLM Acceptance Criteria Before Coding: Get Correct Code From AI Agents"
date: 2026-03-07T19:40:08+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-ai", "llm", "acceptance", "criteria", "Python"]
description: "Stop AI agents from shipping silent bugs. Define LLM acceptance criteria before coding to catch flaws like dropped token validation that code review misses."
image: "/images/20260307-llm-acceptance-criteria-before.webp"
technologies: ["Python", "JavaScript", "Node.js", "FastAPI", "Claude"]
faq:
  - question: "what are LLM acceptance criteria before coding and how do they help get correct code from AI agents"
    answer: "LLM acceptance criteria before coding are explicit pass/fail conditions you define before asking an AI agent to write any code, ensuring the model generates against testable requirements rather than just producing plausible-looking output. This approach mirrors test-driven development (TDD) and measurably reduces ambiguous or incomplete AI-generated code. Without these criteria, AI agents tend to satisfy only the happy path and silently skip edge cases."
  - question: "why does AI generated code fail in production even when it looks correct"
    answer: "AI coding agents predict tokens that statistically resemble correct code based on training patterns, rather than reasoning about logical correctness. This means they can produce code that passes a quick manual review but contains subtle bugs, such as dropped validation logic under specific race conditions. Even leading agents score only 45–72% on real-world software tasks, meaning roughly 1 in 4 outputs is incorrect or incomplete."
  - question: "how to use LLM acceptance criteria before coding to get correct code from AI agents like Cursor or GitHub Copilot"
    answer: "Define explicit, testable acceptance criteria before prompting your AI coding agent, specifying exact pass/fail conditions including edge cases and error handling requirements. Tools like Cursor (0.46+), Aider (0.50+), and Claude Code support system-prompt-level criteria injection, making this approach scalable across a team. Structured prompting with testable criteria consistently outperforms both ad-hoc prompting and post-generation review for catching logic errors."
  - question: "what is vibe coding and why is it risky for production software"
    answer: "Vibe coding is a term coined in 2025 describing the practice of trusting AI-generated code without systematic verification, relying on the output looking correct rather than confirming it is correct. While this approach can work for throwaway scripts, it is unreliable for production code because AI agents optimize for plausibility, not logical accuracy. Teams using this method at scale have reported production incidents caused by subtle bugs that bypassed code review."
  - question: "does writing acceptance criteria before prompting an AI coding agent actually improve code quality"
    answer: "Yes, research and practitioner experience confirm that structured prompting with predefined acceptance criteria outperforms both ad-hoc prompting and post-generation review for catching logic errors in AI-generated code. Defining criteria upfront forces the model to address edge cases and explicit requirements it would otherwise skip. This workflow is especially effective when criteria are injected at the system-prompt level in tools like Cursor, Aider, or Claude Code."
---

AI agents write plausible code, not correct code. That distinction cost a full sprint last quarter. The agent produced a working-looking authentication module that passed a quick manual review — but silently dropped refresh token validation under specific race conditions. Production caught it. Code review didn't.

This tutorial is for developers and engineers already using AI coding agents (Cursor, GitHub Copilot, Aider, Claude Code) who want to stop playing "spot the subtle bug" and start getting reliable output the first time. By the end, you'll have a systematic workflow for defining LLM acceptance criteria before coding begins.

**What you'll get:**
- A repeatable framework for writing acceptance criteria AI agents can actually use
- Prompt templates you can steal and adapt today
- A comparison of structured prompting vs. alternatives
- Real code examples showing the before/after difference

---

> **Key Takeaways**
> - LLM acceptance criteria before coding means defining explicit pass/fail conditions *before* asking an AI agent to write any code — this measurably reduces ambiguous output.
> - AI agents generate statistically likely code, not logically verified code. Without acceptance criteria, they satisfy the happy path and quietly skip edge cases.
> - Structured prompting with testable criteria outperforms both ad-hoc prompting and post-generation review for catching logic errors in AI-generated code.
> - The workflow mirrors TDD: write your criteria first, then let the agent generate code against them.
> - Tools like Cursor (0.46+), Aider (0.50+), and Claude Code support system-prompt-level acceptance criteria injection, making this scalable across a team.

---

## Background & Context

AI coding agents went mainstream fast. GitHub Copilot crossed 1.8 million paid users by late 2025. By Q1 2026, tools like Cursor, Aider, and Claude Code had pushed AI-assisted development into production workflows at companies of every size. The benchmark race intensified: as of March 2026, leading agents score between 45–72% on SWE-bench Verified, the industry-standard measure of real-world software task completion.

That number matters. Even at 72%, roughly 1 in 4 tasks produces incorrect or incomplete output.

The core problem, documented clearly by analysts at Katana Quant and confirmed by teams using these tools at scale: LLMs don't reason about correctness. They predict tokens that *look like* correct code based on training patterns. "Vibe coding" — the term coined in 2025 for trusting AI output without verification — works for throwaway scripts. It breaks in production.

The fix isn't better models. It's better inputs. Defining LLM acceptance criteria before coding forces the model to generate against explicit, testable conditions rather than vibes. That's the workflow that bridges the gap between "plausible" and "correct."

**Prerequisites:** Familiarity with at least one AI coding agent, basic understanding of unit testing concepts, and a project where you've already felt the pain of incorrect AI output.

---

## Comparing Approaches to AI Code Quality

| Feature | LLM Acceptance Criteria (Pre-coding) | Post-Generation Code Review | Ad-Hoc Prompting |
|---|---|---|---|
| **Error catch rate** | High — catches logic gaps before generation | Medium — human reviewer dependent | Low — model decides what matters |
| **Time cost** | Medium upfront, low downstream | High — iterative back-and-forth | Low upfront, high downstream |
| **Repeatability** | Structured, team-shareable | Inconsistent across reviewers | Inconsistent per session |
| **Edge case coverage** | Explicit — you define them | Implicit — reviewer may miss them | Minimal — model skips them |
| **Scalability** | High — inject into system prompts | Low — doesn't scale across agents | Low — per-prompt tribal knowledge |
| **Tooling support** | Cursor, Aider, Claude Code | All tools | All tools |

Post-generation review catches obvious bugs but misses subtle logic errors — especially in concurrency, authentication flows, and data transformation chains. Ad-hoc prompting is fast but produces inconsistent results even for identical tasks. Pre-coding acceptance criteria creates a specification the model generates *against*, not just *toward*.

This approach isn't a silver bullet. It adds upfront work. For truly throwaway scripts or exploratory prototypes, the overhead may not be worth it. But for anything touching auth, payments, or data integrity — the cost of skipping it is higher than the cost of writing the spec.

---

## Step-by-Step Implementation Guide

### Prerequisites
- Python 3.11+ or Node.js 20+ (for code examples)
- An AI coding agent: Cursor 0.46+, Aider 0.50+, or Claude Code (March 2026 release)
- `pytest` (Python) or `jest` (JavaScript) installed
- 20 minutes and one real feature to implement

---

### Step 1: Write Your Acceptance Criteria Document First

Before opening your AI agent, create an `ACCEPTANCE.md` file in your feature branch. Structure it around three categories: happy path, edge cases, and failure modes.

```markdown
# Acceptance Criteria: User Authentication Token Refresh

## Happy Path
- Given a valid refresh token, return a new access token within 200ms
- New access token must expire in 15 minutes
- Old refresh token must be invalidated after use (single-use enforcement)

## Edge Cases
- Expired refresh token returns HTTP 401, not 500
- Concurrent requests with the same refresh token: only one succeeds, others return 401
- Missing Authorization header returns 400 with message "Authorization header required"

## Failure Modes
- Database connection failure returns 503, not an unhandled exception
- Malformed JWT returns 400 with message "Invalid token format"

## Out of Scope
- Password reset flows
- OAuth provider tokens
```

This document is your contract. The model generates against it. You test against it.

---

### Step 2: Inject Criteria Into Your Agent Prompt

Don't paste criteria as an afterthought. Lead with them. The model's attention is front-loaded — what comes first shapes what it generates.

```python
# Example: Aider-style system prompt injection
# Run from CLI or paste into agent system prompt field

SYSTEM_PROMPT = """
You are a backend engineer implementing the following feature.
Generate code that satisfies ALL acceptance criteria below before writing any logic.
If a criterion is ambiguous, ask for clarification rather than assuming.

ACCEPTANCE CRITERIA:
{criteria_content}

CONSTRAINTS:
- Python 3.11, FastAPI 0.110+
- No external auth libraries (implement JWT validation directly)
- All edge cases must have corresponding unit tests
- Raise specific exceptions, never generic Exception
"""

# Load your criteria file and inject
with open("ACCEPTANCE.md", "r") as f:
    criteria_content = f.read()

final_prompt = SYSTEM_PROMPT.format(criteria_content=criteria_content)
```

---

### Step 3: Request Tests Before Implementation

Ask the agent to write tests *first*. This forces it to operationalize your criteria before writing code that could bias the test design.

```python
# Prompt pattern: tests before implementation
PROMPT_PHASE_1 = """
Using the acceptance criteria provided, write pytest test cases only.
Do not implement the feature yet.
Each acceptance criterion must map to at least one test function.
Name tests descriptively: test_[criterion_description]
"""

# Expected output structure from agent:
# test_valid_refresh_token_returns_new_access_token()
# test_expired_token_returns_401_not_500()
# test_concurrent_requests_only_one_succeeds()
# test_missing_auth_header_returns_400()
```

Review these tests *before* asking for the implementation. If a test is missing or wrong, fix it now — not after 200 lines of generated code assume the wrong contract.

---

### Step 4: Generate Implementation Against Your Tests

Now ask for the implementation. The test suite becomes the acceptance gate.

```python
PROMPT_PHASE_2 = """
Now implement the token refresh endpoint.
All tests from Phase 1 must pass.
If the implementation requires changing a test, explain why before changing it.
"""

# After generation, run tests immediately:
# pytest tests/test_auth_refresh.py -v
# 
# Expected: all tests pass on first or second attempt
# Red flag: agent suggests modifying tests to make them pass
```

---

### Step 5: Validate the Failure Modes Explicitly

Happy path tests pass easily. Failure modes are where AI agents cut corners. Run this manually or add it to CI:

```bash
# Test failure mode: database unavailable
# Spin up a mock that fails, confirm 503 not unhandled exception

pytest tests/test_auth_refresh.py -v -k "failure"

# Expected output:
# test_database_failure_returns_503 PASSED
# test_malformed_jwt_returns_400 PASSED
#
# If these fail, the agent cut corners on error handling
# Go back to Step 2 with explicit error-handling criteria added
```

---

## Code Examples & Real-World Use Cases

### Basic Example: Criteria Template Function

```python
def build_agent_prompt(feature_name: str, criteria_path: str, stack: str) -> str:
    """
    Build a structured prompt from an acceptance criteria file.
    
    Why: Keeps criteria in version control, not buried in chat history.
    Use this at the start of any AI coding session.
    """
    with open(criteria_path, "r") as f:
        criteria = f.read()
    
    return f"""
Feature: {feature_name}
Stack: {stack}

ACCEPTANCE CRITERIA (non-negotiable):
{criteria}

Instructions:
1. Write failing tests first
2. Implement until all tests pass  
3. Do not modify tests to pass — modify code
4. Flag any criterion you can't satisfy with the current stack
"""
```

The function loads criteria from a file — version-controlled, reviewable by teammates — and wraps it in a structured prompt that sets clear rules. The "do not modify tests" instruction is load-bearing. Without it, agents will sometimes rewrite tests to match their buggy implementation rather than fix the actual logic.

### Advanced Example: CI Integration

```yaml
# .github/workflows/ai-generated-code-gate.yml
# Runs acceptance criteria validation on any PR flagged as AI-generated

name: AI Code Acceptance Gate

on:
  pull_request:
    branches: [main]

jobs:
  acceptance-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Check for ACCEPTANCE.md
        run: |
          # Require criteria doc for AI-generated PRs
          if git log --format="%s" -1 | grep -q "\[ai-generated\]"; then
            if [ ! -f "ACCEPTANCE.md" ]; then
              echo "ERROR: AI-generated PR missing ACCEPTANCE.md"
              exit 1
            fi
          fi
      
      - name: Run acceptance tests
        run: pytest tests/ -v --tb=short
        
      - name: Verify failure mode coverage
        run: |
          # Confirm failure mode tests exist
          pytest tests/ -v -k "failure or error or invalid" --collect-only | grep "test session starts"
```

Teams shipping AI-generated features daily use this workflow to enforce criteria documentation as a merge requirement. PRs tagged `[ai-generated]` in the commit message must include `ACCEPTANCE.md` and pass a test suite covering failure modes — not just happy paths. Reports from engineering teams adopting similar gates indicate a meaningful reduction in production incidents from AI-generated code within the first month.

---

## Best Practices & Tips

### Common Pitfalls to Avoid

- **Pitfall 1: Vague criteria like "should handle errors gracefully"**
  Solution: Write specific, testable conditions. "Returns HTTP 503 with body `{"error": "service_unavailable"}` when database is unreachable" is testable. "Handles errors gracefully" is not.

- **Pitfall 2: Writing criteria after you've already started prompting**
  Solution: Treat criteria like a spec ticket. No agent prompt until `ACCEPTANCE.md` exists and is committed. This removes the temptation to fit criteria around what the agent already produced.

- **Pitfall 3: Letting the agent modify tests to make them pass**
  Solution: Explicitly prohibit test modification in your prompt. If the agent needs to change a test, it must explain the conflict first — that's a criteria ambiguity, not a code fix.

### When This Doesn't Work

Pre-coding criteria works best when the feature scope is well-defined. It struggles when you're genuinely exploring — when you don't yet know what the right behavior *should* be. In those cases, vibe coding a rough prototype first is reasonable. Just don't ship that prototype. Once you understand what you're building, write the criteria and regenerate properly.

It also adds friction for small, isolated changes — a config tweak, a one-line fix. Apply judgment. The overhead pays off at the feature level, not the line level.

### Optimization Tips

- **Reuse criteria templates:** Build a `/criteria-templates` folder in your repo. Auth, CRUD endpoints, background jobs — each gets a base template you extend per feature.
- **Security by default:** Always include auth boundary criteria explicitly. AI agents default to optimistic trust assumptions — they assume the token is valid, the user exists. Write the negative cases or they won't exist.
- **Scalability:** Inject criteria via system prompts in Cursor's `.cursorrules` file so every session in that repo starts with your standards already loaded.

### Production Readiness Checklist

- [ ] `ACCEPTANCE.md` committed before any agent prompt sent
- [ ] Tests written and reviewed *before* implementation generated
- [ ] Failure modes covered by at least one test each
- [ ] Agent prompt explicitly prohibits test modification
- [ ] CI gate enforces criteria doc presence on AI-tagged PRs
- [ ] Edge cases reviewed by a human, not just the agent

---

## Conclusion & Next Steps

The gap between "plausible" and "correct" in AI-generated code is real, measurable, and closeable. LLM acceptance criteria before coding is the most reliable way to close it — not by trusting the model more, but by giving it a contract to generate against. Even at the best current benchmark scores, 1 in 4 AI-generated tasks produces incorrect output. Criteria don't fix the model. They constrain its failure surface.

Start with one feature this week. Write the `ACCEPTANCE.md` first, ask for tests before implementation, and watch how much review time you reclaim. The upfront cost is 20 minutes. The downstream cost of skipping it is a production incident at 2am.

**Key reminders:**
- Criteria first, always — no exceptions for "small" features
- Tests before implementation — every time
- Failure modes are not optional
- Version-control your criteria, not just your code

Try the criteria template from Step 1 on your next AI coding task. Then check: what edge case did the agent miss when you *didn't* specify it upfront?

---

*References: [Best AI Coding Agents Ranked (2026)](https://www.morphllm.com/ai-coding-agent) | [Your LLM Doesn't Write Correct Code](https://blog.katanaquant.com/p/your-llm-doesnt-write-correct-code) | [Vibe Coding — Wikipedia](https://en.wikipedia.org/wiki/Vibe_coding)*

## References

1. [Best AI Coding Agents Ranked: 15 Tools Tested with Real Benchmarks (2026)](https://www.morphllm.com/ai-coding-agent)
2. [Your LLM Doesn't Write Correct Code. It Writes Plausible Code.](https://blog.katanaquant.com/p/your-llm-doesnt-write-correct-code)
3. [Vibe coding - Wikipedia](https://en.wikipedia.org/wiki/Vibe_coding)


---

*Photo by [Morgan Petroski](https://unsplash.com/@morganpetroskiphoto) on [Unsplash](https://unsplash.com/photos/mila-building-at-daytime--s3YpZgtHqE)*
