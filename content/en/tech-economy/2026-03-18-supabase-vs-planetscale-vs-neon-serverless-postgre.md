---
title: "Supabase vs PlanetScale vs Neon Serverless Postgres Cold Start"
date: 2026-03-18T20:14:03+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "supabase", "planetscale", "neon", "Next.js"]
description: "Supabase vs PlanetScale vs Neon cold start latency tested in 2025 — find out which platform hides a full second of lag in your p99 response times."
image: "/images/20260318-supabase-vs-planetscale-vs-neo.webp"
technologies: ["Next.js", "PostgreSQL", "Vercel", "Go", "Cloudflare"]
faq:
  - question: "supabase vs planetscale vs neon serverless postgres cold start latency comparison 2025 which is fastest"
    answer: "In the supabase vs planetscale vs neon serverless postgres cold start latency comparison 2025, Supabase effectively eliminates cold starts on paid plans by keeping compute always-on via PgBouncer connection pooling, though this requires a minimum $25/month spend. Neon has the highest cold start variance at 500ms–2,000ms due to its scale-to-zero architecture, while PlanetScale uses an HTTP-based serverless driver that makes direct latency comparisons with PostgreSQL platforms misleading."
  - question: "how long are neon postgres cold starts in 2025"
    answer: "Neon's scale-to-zero architecture produces cold start latency between 500ms and 2,000ms after an idle period, according to Neon's own compute lifecycle documentation. This variance is highest for infrequently accessed databases like hobby projects or background jobs that don't receive consistent traffic to keep the compute instance warm."
  - question: "does supabase have cold start issues like neon"
    answer: "Supabase does not experience cold starts on paid plans because it does not scale to zero — compute stays always-on, and connections are managed through PgBouncer connection pooling. The tradeoff is a minimum $25/month compute floor, meaning the cold-start-free experience comes at a cost compared to Neon's free tier."
  - question: "is planetscale actually postgres or mysql serverless database"
    answer: "PlanetScale is MySQL-compatible under the hood, powered by Vitess, and is not a PostgreSQL database — a critical distinction for teams whose stack assumes Postgres-compatible behavior or extensions. This is a key reason why including PlanetScale in a supabase vs planetscale vs neon serverless postgres cold start latency comparison 2025 requires careful framing, as its serverless driver runs over HTTP rather than TCP and targets edge runtimes like Cloudflare Workers."
  - question: "which serverless database should I use for Vercel edge functions in 2025"
    answer: "PlanetScale's serverless driver is specifically designed for edge environments like Vercel Edge Functions and Cloudflare Workers because it runs over HTTP rather than requiring a traditional TCP connection. However, if your project requires PostgreSQL compatibility, Neon is generally the recommended choice for edge workloads, as it also offers an HTTP-compatible driver and maintains a generous free tier."
---

Cold starts have quietly become the most argued-about metric in serverless database selection. Pick the wrong platform and your API's p99 latency looks like a network blip — or a full second of unexplained lag your users blame on "the internet."

The Supabase vs PlanetScale vs Neon comparison has gotten genuinely complicated heading into 2026. PlanetScale pivoted away from its free tier in 2024, Neon shipped branching as a first-class feature, and Supabase crossed 1 million databases hosted. The platforms aren't converging — they're diverging fast, which makes choosing between them harder than it was two years ago.

The core argument: cold start latency is the wrong single metric to optimize for. What actually matters is *which workload pattern you're running* and how each platform handles connection pooling, region availability, and scaling-to-zero behavior under that pattern.

**In brief:** Cold start performance in 2026 varies dramatically by platform architecture, not just raw numbers. Neon's scale-to-zero approach introduces the highest cold start variance. Supabase's always-on connection pooling via PgBouncer avoids most cold start costs entirely. PlanetScale's serverless driver targets edge environments where traditional TCP connections fail.

What this analysis covers:
1. How each platform handles the cold start problem structurally
2. Where the real latency numbers come from — and what benchmarks miss
3. Which workload maps to which platform
4. Practical decisions for teams choosing in Q1–Q2 2026

> **Key Takeaways**
> - Neon's scale-to-zero architecture produces cold start latency between 500ms–2,000ms after an idle period, per Neon's own documentation on compute lifecycle management.
> - Supabase doesn't scale to zero on paid plans, eliminating cold starts at the cost of a minimum $25/month compute floor.
> - PlanetScale's serverless driver runs on HTTP rather than TCP, targeting Cloudflare Workers and Vercel Edge Functions — making direct PostgreSQL latency comparisons misleading.
> - This comparison matters most for teams running hobby projects or infrequently triggered background jobs. Always-on production apps experience cold starts very differently.

---

## Why This Comparison Got Harder in 2024–2025

Three structural events reshaped this market.

PlanetScale killed its free tier in March 2024. That sent a wave of developers back to evaluating Supabase and Neon, both of which kept generous free tiers intact. PlanetScale's positioning shifted from "MySQL-compatible serverless for everyone" toward enterprise teams wanting Vitess-powered horizontal sharding. Worth noting: PlanetScale is MySQL under the hood, not PostgreSQL — a critical distinction when the rest of your stack assumes Postgres-compatible behavior.

Neon hit general availability with its branching feature in late 2024. Branching creates copy-on-write database clones in seconds, which matters enormously for preview environments and CI/CD pipelines. But branching means each branch is a separate compute endpoint — and each one can scale to zero independently. More branches equals more cold start surface area.

Supabase crossed 1 million databases in 2024, per Supabase's own engineering blog, and began defaulting new free-tier projects to a pause-after-one-week-of-inactivity model. This introduced cold starts to Supabase's free tier for the first time, blurring what had been a clean architectural distinction.

The market context matters. According to the Stack Overflow Developer Survey 2024, PostgreSQL is the most-used database for the fifth consecutive year at 49% adoption. Every platform in this comparison either is Postgres or offers a Postgres-compatible wire protocol. Developers aren't switching databases — they're switching *where* Postgres runs.

---

## Cold Start Architecture: Where Latency Actually Comes From

Cold starts aren't monolithic. They break into three phases: compute provisioning, connection establishment, and query execution. Each platform handles these differently.

**Neon** uses a separation of storage and compute architecture. When a compute endpoint idles — default is 5 minutes on the free tier, configurable on paid plans — Neon suspends the virtual machine entirely. Restarting requires spinning up a new VM and re-establishing the storage connection. Neon's own documentation cites cold start times of "up to a few seconds." Community benchmarks across DEV Community and GitHub discussions have measured 500ms–2,000ms depending on region and database size. The variance is real. A small database in `us-east-1` wakes faster than a larger one in `eu-central-1`. This approach can fail noticeably when background jobs run on irregular schedules — every invocation after a long idle period pays the full cold start cost.

**Supabase** runs dedicated PostgreSQL instances per project. On paid plans (Pro at $25/month), compute never scales to zero — cold starts don't exist in the traditional sense. On the free tier, projects pause after 7 days of inactivity, with resume time reported at roughly 2–5 seconds per Supabase's status documentation. The more important latency factor is connection pooling: Supabase uses PgBouncer in transaction mode, which handles connection overhead that would otherwise hit every serverless function invocation. According to getsabo.com's comparison analysis, Supabase's PgBouncer setup reduces connection time by eliminating TCP handshake overhead per request.

**PlanetScale** operates on a fundamentally different model. Its serverless driver uses HTTP/2 rather than TCP, which means it works in edge runtimes where persistent TCP isn't available. There's no cold start in the compute sense — but there's HTTP overhead per query that doesn't exist in persistent TCP connections. For single queries from edge functions, this is often faster than establishing a new TCP connection. For multi-query transactions, the overhead compounds. This isn't always the right trade-off, particularly for write-heavy workloads that depend on transaction consistency across multiple queries.

---

## The Benchmark Problem

Most cold start benchmarks measure the wrong thing.

They test cold starts in isolation — a single query fired at a just-woken database. Real applications don't work that way. A Next.js app with 100 daily active users keeps its serverless functions warm enough that Neon's cold start fires infrequently. A webhook processor that runs once an hour *will* hit Neon's cold start every single time.

The DEV Community analysis from Dataformathub (2025) made this point directly: connection pooling configuration has more impact on observed latency than cold start architecture for most production workloads. A misconfigured PgBouncer on Supabase or a missing `?pgbouncer=true` flag on Neon's connection string can add 200–400ms to every query — dwarfing the cold start difference between platforms.

---

## Platform-by-Platform Comparison

| Criteria | Supabase | Neon | PlanetScale |
|---|---|---|---|
| **Database Engine** | PostgreSQL 15/16 | PostgreSQL 16 | MySQL (Vitess) |
| **Cold Start (Free)** | ~2–5s after 7-day pause | 500ms–2s after 5min idle | N/A (HTTP model) |
| **Cold Start (Paid)** | None (always-on) | ~500ms–2s (configurable) | N/A |
| **Connection Pooling** | PgBouncer (built-in) | PgBouncer (built-in) | HTTP driver (no TCP pool needed) |
| **Scale to Zero** | Free tier only | Default (all tiers) | Always serverless |
| **Branching** | No | Yes (first-class) | No |
| **Edge Runtime Support** | Via connection string | Via serverless driver | Native HTTP driver |
| **Starting Price** | Free / $25 Pro | Free / $19 Launch | Free / $39 Scaler |
| **Best For** | Full-stack apps, auth-included | Preview envs, CI/CD, dev teams | Edge functions, MySQL-compatible stacks |

The trade-offs aren't subtle. Supabase's "no cold start on paid" is a strong operational guarantee — but it means paying for compute that sits idle during low-traffic hours. Neon's scale-to-zero saves money but requires accepting latency variance. PlanetScale's HTTP model sidesteps the cold start question entirely but forces a MySQL dependency.

---

## Matching Workload to Platform

**Next.js SaaS app with moderate traffic (500–5,000 DAU)**

Cold starts are mostly irrelevant because traffic keeps computes warm. Supabase Pro ($25/month) is the straightforward choice — auth, storage, and Postgres in one bill, no cold start risk. Neon's Launch plan ($19/month) works too if the team values branching for staging environments.

**Infrequently triggered background jobs or cron functions**

This is where cold start latency actually hurts. A nightly data sync hitting Neon after 23 hours of idle *will* pay the 500ms–2,000ms cold start cost on every run. The fix: set Neon's `suspend_timeout` to a longer value, or pre-warm the endpoint with a lightweight ping query 30 seconds before the job fires. Supabase Pro eliminates the problem entirely with always-on compute — though you're paying for that guarantee whether traffic shows up or not.

**Edge functions on Cloudflare Workers or Vercel Edge**

TCP-based PostgreSQL connections don't work in edge runtimes. Neither Supabase nor Neon's standard connection strings function here without a proxy layer. PlanetScale's HTTP driver is purpose-built for this case — genuinely the best option for edge-first architectures, assuming MySQL compatibility isn't a blocker.

**What to watch going forward:**
- Neon's roadmap includes configurable cold start warm-up, which could eliminate the idle latency problem by Q3 2026
- Supabase is working on read replicas for Pro tier, which changes the latency profile for read-heavy workloads
- PlanetScale's enterprise push means its free tier terms could shift again — teams relying on it should monitor billing announcement channels closely

---

## Where This Lands in 2026

The comparison comes down to three distinct architectural bets, not a single leaderboard.

**Neon** wins on developer experience and cost for teams that need branching and can tolerate idle latency. **Supabase** wins on operational predictability and feature completeness for full-stack products. **PlanetScale** wins specifically in edge runtime environments where TCP doesn't work.

In the next 6–12 months, Neon's warm-up features and Supabase's read replica rollout will close the gap on cold start concerns. The more interesting signal to watch is whether PlanetScale's enterprise push leaves the indie and startup segment open for Neon and Supabase to compete over.

The actionable takeaway: benchmark your *actual workload pattern*, not synthetic cold start numbers. Fire 100 queries at your real access pattern, measure p50 and p99, and pick based on that — not marketing pages.

Which of these three does your current stack use, and have cold starts actually caused production issues? That data point is worth more than any benchmark.

## References

1. [Serverless PostgreSQL 2025: The Truth About Supabase, Neon, and PlanetScale - DEV Community](https://dev.to/dataformathub/serverless-postgresql-2025-the-truth-about-supabase-neon-and-planetscale-7lf)
2. [Supabase vs PlanetScale vs Neon: The Best Serverless ...](https://getsabo.com/blog/supabase-vs-neon)
3. [Best Database Software for Startups and SaaS (2026): A Developer's Guide](https://makerkit.dev/blog/tutorials/best-database-software-startups)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
