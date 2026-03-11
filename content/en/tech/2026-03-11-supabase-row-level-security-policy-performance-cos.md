---
title: "Supabase RLS Policy Performance Cost and PgBouncer Conflict Fix"
date: 2026-03-11T20:01:43+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-security", "supabase", "row", "level", "JavaScript"]
description: "RLS policies can slash Supabase query throughput 40–60%. Fix the PgBouncer transaction mode conflict before it silently kills your production performance."
image: "/images/20260311-supabase-row-level-security-po.webp"
technologies: ["JavaScript", "PostgreSQL", "REST API", "Rust", "Go"]
faq:
  - question: "supabase row level security policy performance cost pgbouncer transaction mode conflict fix"
    answer: "The fix involves either switching to Supavisor in session mode (Supabase's newer connection pooler) instead of PgBouncer in transaction mode, or using SECURITY DEFINER wrapper functions that avoid relying on session-level state like current_setting(). PgBouncer in transaction mode strips session state between transactions, which breaks the JWT-based RLS pattern Supabase recommends by default."
  - question: "why does enabling RLS slow down supabase queries"
    answer: "Enabling Row Level Security in Supabase causes PostgreSQL to evaluate policy conditions against every qualifying row a query touches — a single query scanning 10,000 rows can trigger a policy function 10,000 times. The performance cost scales with table cardinality, function volatility, and whether the query planner can push policy conditions into index scans, which is why RLS overhead is often invisible in development but significant in production."
  - question: "pgbouncer transaction mode breaking supabase RLS current_setting JWT claims"
    answer: "PgBouncer in transaction mode resets all session-level state between transactions, which means values set via set_config() or current_setting() — used to pass JWT claims into RLS policies — are wiped out before policy evaluation runs. This is a known conflict with Supabase's standard RLS implementation and is one of the core reasons the supabase row level security policy performance cost pgbouncer transaction mode conflict fix involves migrating to Supavisor in session mode."
  - question: "how much does RLS reduce query throughput supabase production"
    answer: "Enabling RLS on a high-traffic Supabase table without carefully optimized policies can cut query throughput by 40–60%, and the overhead compounds further when PgBouncer's transaction mode interferes with session-level policy evaluation. The impact is minimal at small scale but becomes significant for applications with tens of thousands of daily active users or high query volume."
  - question: "supavisor vs pgbouncer supabase which one to use with row level security"
    answer: "Supavisor, which became Supabase's recommended default connection pooler in 2024, supports session mode that preserves session-level state between transactions — making it compatible with Supabase's standard JWT-based RLS patterns. PgBouncer in transaction mode does not preserve this state, which causes RLS policies relying on current_setting() to fail silently or behave incorrectly in production."
---

Enabling RLS on a busy Supabase table can cut query throughput by 40–60% if the policies aren't written carefully — and that number gets worse when PgBouncer enters the picture.

This isn't theoretical. The Supabase Row Level Security policy performance cost PgBouncer transaction mode conflict is one of the most under-documented production headaches for teams scaling past their first 10,000 daily active users. The docs tell you to enable RLS. They don't always tell you what happens next.

So let's cover the actual mechanics: why RLS policies get expensive, what PgBouncer's transaction mode breaks at the session level, and what the fix looks like in production code.

---

> **Key Takeaways**
> - Supabase RLS policies run as row-level PostgreSQL checks on every qualifying row — a single query touching 10,000 rows can evaluate a policy function 10,000 times.
> - PgBouncer in transaction mode strips session-level state like `SET LOCAL` and `current_setting()` calls, which breaks the standard JWT-based RLS pattern Supabase recommends.
> - The performance cost of RLS isn't flat — it scales with cardinality, function volatility, and whether the planner can push policy conditions into index scans.
> - Teams that switch to `SECURITY DEFINER` wrapper functions or Supabase's built-in connection pooler (Supavisor) in session mode largely resolve the PgBouncer conflict without rewriting all their policies.

---

## Why RLS Performance Became a 2026 Conversation

Row Level Security in PostgreSQL has existed since version 9.5, released in 2016. Supabase made it a default expectation for every project — when you create a table, RLS is disabled, but the platform actively prompts you to enable it. The Supabase docs position RLS as the primary mechanism for controlling data access when clients connect directly via the auto-generated REST API or the JavaScript client library.

At small scale, this worked fine. A SaaS app with a few hundred users doesn't notice the overhead.

The friction started showing up as Supabase projects matured. By late 2024, Supabase reported over 1 million databases hosted on the platform (Supabase blog, August 2024). A meaningful portion of those are production apps with real query volume. Teams began hitting a specific wall: queries that were fast in development became sluggish in production, and the culprit traced back to policy evaluation cost.

The PgBouncer layer added a second, distinct problem. Supabase's default connection pooler — before Supavisor became the recommended default in 2024 — ran PgBouncer in transaction mode. Transaction mode resets session state between transactions, which breaks the `set_config()` / `current_setting()` pattern that Supabase's own RLS examples rely on to pass authenticated JWT claims into policy evaluation.

Two problems. Same stack. Both hitting teams at the same time.

---

## Why RLS Policies Get Expensive at Scale

PostgreSQL evaluates RLS policies as predicate filters appended to every query on a protected table. The policy runs per-row during the table scan. If the policy calls a function — say, `auth.uid()` — that function needs to resolve on every single row evaluation.

The critical variable is function volatility. PostgreSQL marks functions as `VOLATILE`, `STABLE`, or `IMMUTABLE`. A `VOLATILE` function re-executes on every row. `auth.uid()` in Supabase is marked `STABLE`, which tells the planner it can cache the result within a single query — that's the behavior you want. But many custom RLS policies call subqueries or join against permission tables, and those patterns can't be cached the same way.

The query planner also can't always push an RLS policy condition into an index scan. If the policy expression isn't indexable or references a non-indexed column, the database falls back to sequential scans even when a perfectly good index exists on the data column. This is the silent killer. A table with 500,000 rows, a clean index on `user_id`, but a policy that references a separate `team_memberships` table — that policy can force a seq scan on every query, regardless of what indexes exist elsewhere.

## The PgBouncer Transaction Mode Conflict

The standard Supabase RLS setup for authenticated requests works like this: the API layer calls `SET LOCAL role = 'authenticated'` and `SET LOCAL request.jwt.claims = '<jwt payload>'` at the start of each transaction. Policies then call `current_setting('request.jwt.claims')` to read the user's ID and enforce row-level filtering.

Transaction mode in PgBouncer resets all session-local settings when the transaction ends. `SET LOCAL` values are transaction-scoped by definition, so they survive within a transaction — but `SET` without `LOCAL` is session-scoped and gets wiped when PgBouncer reassigns the connection to a different client.

The conflict that surfaces: if any code path uses session-scoped `SET` instead of `SET LOCAL`, those values bleed between connections or disappear entirely. The result is policies that silently pass when they should block, or fail authentication checks for valid users. Neither failure mode is obvious from application logs. Both are the kind of bug that takes days to isolate.

Supabase's own connection pooler, **Supavisor**, launched as the default in 2024 specifically to address this. Supavisor supports both transaction and session modes, and its session mode preserves the `SET LOCAL` pattern correctly. According to Supabase's changelog (November 2024), new projects default to Supavisor rather than PgBouncer.

## Measuring the Actual Cost

There's no universal benchmark for Supabase RLS policy performance, but the mechanics are well-understood in PostgreSQL performance circles. The pganalyze team published analysis in 2023 showing that complex RLS policies — those involving subqueries or correlated expressions — can add 2–5ms per query on moderately loaded instances. At 1,000 queries per second, that's 2–5 seconds of added CPU time every second. That's unsustainable.

`EXPLAIN (ANALYZE, BUFFERS)` is the ground truth here. Running it on a query against an RLS-protected table shows whether the policy condition appears as a Filter (bad — applied after scan) or folds into an Index Cond (good — pushed into the index scan). The goal is always the latter.

## Comparison: RLS Approaches by Performance Profile

| Approach | Planner Optimization | PgBouncer-Safe | Policy Complexity | Best For |
|---|---|---|---|---|
| Simple column equality (`user_id = auth.uid()`) | ✅ Index pushdown possible | ✅ Yes | Low | Standard multi-tenant tables |
| Subquery against permission table | ❌ Often forces seq scan | ✅ Yes | High | Role-based or team access |
| `current_setting()` with `SET LOCAL` | ✅ Yes | ⚠️ Transaction mode only | Medium | JWT claim-based filtering |
| `SECURITY DEFINER` wrapper function | ✅ Cacheable result | ✅ Yes | Medium | Reusable cross-table policies |
| No RLS + application-layer filtering | ✅ Full planner control | ✅ Yes | None | Internal tools, trusted envs only |

The table makes a non-obvious point clear: simple column equality policies are both the safest for performance and the most PgBouncer-compatible. The moment policy logic requires a subquery or an external permission lookup, costs climb and compatibility narrows.

This approach can fail when your access model genuinely requires team-based or role-based permissions that can't reduce to a simple column comparison. In those cases, the subquery approach may be unavoidable — but it should be paired with aggressive index coverage and tested with `EXPLAIN ANALYZE` before it ever touches production.

---

## The Fix in Practice

**For the PgBouncer conflict**, the cleanest path in 2026 is migrating to Supavisor in session mode. Supabase's dashboard makes this a one-click change per project. If migration isn't immediate, auditing every policy for session-scoped `SET` calls (not `SET LOCAL`) and converting them is the safe interim step.

**For policy performance**, three concrete actions cover the majority of cases:

**1. Run `EXPLAIN ANALYZE` on every RLS-protected query in staging.** Look for "Filter" rows in the output that reference policy conditions. Those are the performance leaks. Rewrite policies so the condition folds into an existing index — typically by ensuring `user_id` or the equivalent tenant key is indexed and the policy uses direct equality.

**2. Mark policy functions `STABLE` explicitly when they qualify.** `auth.uid()` is already `STABLE`, but custom helper functions often get written as `VOLATILE` by default. A `STABLE` function that reads `current_setting()` gets evaluated once per query rather than once per row.

**3. Use `SECURITY DEFINER` functions for complex permission logic.** Wrapping a multi-table permission check in a `SECURITY DEFINER` function lets PostgreSQL cache the result more aggressively and keeps the policy expression itself simple. According to the Supabase RLS documentation, this pattern also makes policies easier to test in isolation — a practical benefit that often gets overlooked.

**What to watch over the next six months**: Supabase is actively developing policy-level caching improvements at the infrastructure layer. GitHub discussions in the supabase/supabase repository (open issues as of Q1 2026) suggest that automatic policy result memoization per-connection may ship as a configuration option by late 2026. If it does, the performance calculus for complex policies changes significantly.

---

## Putting It Together

The Supabase RLS performance and PgBouncer conflict isn't one problem — it's two distinct problems that hit simultaneously and produce overlapping symptoms. Slow queries and authentication weirdness both point back to the same stack, which is exactly why they're hard to untangle without understanding the mechanics underneath.

RLS policy cost scales with row cardinality and policy complexity. Simple equality checks stay fast at scale. Subqueries don't. PgBouncer transaction mode breaks `SET LOCAL`-based JWT claim passing in ways that are silent and difficult to reproduce in development — Supavisor in session mode resolves this cleanly. `EXPLAIN ANALYZE` remains the only reliable diagnostic. Don't guess which policies are expensive; measure them.

The broader pattern worth tracking: as Supabase continues scaling toward enterprise customers in 2026, the platform's connection pooling and RLS performance story will get more infrastructure investment. Supavisor's launch already signals that trajectory.

Enable RLS. But treat policy design like query design. Both have performance contracts, and both compound at scale.

---

*What's your biggest RLS pain point in production — policy complexity or connection pooler conflicts? The two problems often travel together but require different fixes.*

## References

1. [Row Level Security | Supabase Docs](https://supabase.com/docs/guides/database/postgres/row-level-security)


---

*Photo by [Merakist](https://unsplash.com/@merakist) on [Unsplash](https://unsplash.com/photos/assorted-color-digital-nomad-letter-decor-zY7b8rTra3A)*
