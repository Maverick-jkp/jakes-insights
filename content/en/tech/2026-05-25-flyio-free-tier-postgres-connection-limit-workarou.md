---
title: "Fly.io Free Tier Postgres Connection Limits and Workarounds"
date: 2026-05-25T22:46:51+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "fly.io", "free", "tier", "PostgreSQL"]
description: "Hit Fly.io's 25-connection Postgres limit? See how PGBouncer solves the free tier cap in 2025 and what it actually costs to scale beyond it."
image: "/images/20260525-flyio-free-tier-postgres-conne.webp"
technologies: ["PostgreSQL", "Supabase"]
faq:
  - question: "fly.io free tier postgres connection limit workaround pgbouncer real cost 2025"
    answer: "Fly.io's free tier Postgres caps connections at around 25 on 256 MB shared instances due to RAM constraints, and PgBouncer is the most commonly recommended workaround in 2025. However, PgBouncer in transaction pooling mode breaks prepared statements and adds operational complexity that many developers underestimate. Upgrading to a 512 MB instance at roughly $3.19/month is often cheaper than the engineering time spent debugging PgBouncer compatibility issues."
  - question: "how many postgres connections does fly.io free tier allow"
    answer: "Fly.io's free tier Postgres instances on shared-cpu-1x 256 MB machines are limited to approximately 25 concurrent connections. This isn't an arbitrary restriction — each PostgreSQL connection consumes 5-10 MB of RAM as a separate OS process, so 25 connections is close to the physical memory ceiling. Exceeding this limit causes OOM kills or connection refused errors."
  - question: "does pgbouncer break prepared statements postgresql"
    answer: "Yes, PgBouncer in transaction pooling mode breaks prepared statements because connections are reassigned between transactions, making session-level state like prepared statements unreliable. This is a significant compatibility issue for ORMs like ActiveRecord or Ecto that use prepared statements by default. Developers must either disable prepared statements in their application config or switch PgBouncer to session pooling mode, which reduces the pooling benefit."
  - question: "fly.io postgres connection limit workaround without pgbouncer"
    answer: "Besides PgBouncer, two other main workarounds exist for Fly.io's Postgres connection limits: upgrading to a larger instance with more RAM (a 512 MB machine costs around $3.19/month), or migrating to a managed database platform like Neon or Supabase that handles connection pooling at the platform layer. The best option depends on your app's connection pattern and how much operational overhead you're willing to manage."
  - question: "why does fly.io postgres run out of connections phoenix liveview"
    answer: "Phoenix LiveView applications are especially prone to hitting Fly.io's Postgres connection limits because LiveView's persistent WebSocket model keeps database connections open longer than a standard HTTP request/response cycle. Combined with the free tier's 25-connection ceiling on 256 MB instances, even modest traffic can exhaust available connections quickly. This makes Phoenix LiveView apps one of the most commonly affected use cases in the fly.io free tier postgres connection limit workaround pgbouncer discussions throughout 2025."
---

Fly.io's free tier hits a wall fast. The managed Postgres offering caps connections at 25 per instance on the smallest `shared-cpu-1x` machines — and if you're running a Phoenix or Rails app with even modest traffic, you'll breach that ceiling before your first coffee.

The connection limit isn't a bug. It's a structural property of how PostgreSQL allocates shared memory per connection, each one consuming roughly 5-10 MB of RAM. On a 256 MB free-tier machine, the math is brutal. Twenty-five connections isn't stingy — it's literally what fits. The "just add PgBouncer" answer has dominated developer communities throughout 2025 and into 2026, but that fix carries hidden trade-offs most developers don't price in before they hit production.

**The short version:** PgBouncer fixes the connection ceiling on Fly.io's free tier, but shifts costs elsewhere — in machine sizing, operational complexity, and query compatibility. The right workaround depends entirely on your app's actual connection pattern.

1. Fly.io's free Postgres tier limits connections to ~25 on 256 MB shared instances due to RAM constraints.
2. PgBouncer in transaction pooling mode can reduce active backend connections by 80-90%, but breaks prepared statements.
3. Upgrading to a `shared-cpu-1x` with 512 MB RAM costs approximately $3.19/month per the Fly.io pricing page — often cheaper than the engineering time spent debugging PgBouncer compatibility.
4. Three distinct workarounds exist, each with different cost profiles and failure modes.

---

## Why Fly.io's Connection Model Creates This Problem

Fly.io launched its managed Postgres offering as a Fly app — not a dedicated database service. That distinction matters. Unlike PlanetScale, Neon, or Supabase (which abstract connection pooling at the platform layer), Fly's Postgres is essentially a vanilla PostgreSQL container you manage yourself. According to [Fly.io's official documentation](https://fly.io/docs/postgres/), the platform provisions Postgres as a standard Fly application with the same resource constraints as any other app.

The architecture creates a predictable bottleneck. PostgreSQL spawns a new OS process per connection. On a `shared-cpu-1x / 256 MB` machine — the free tier baseline — active connections above ~25 start competing for RAM, triggering OOM kills or connection refused errors. The Fly community forums documented this pattern extensively through 2024 and into early 2025, with Phoenix LiveView applications being particularly affected because LiveView's persistent socket model keeps database connections open longer than a typical request/response cycle.

Why does this matter *now* in 2026? Fly.io's pricing restructuring. According to [Orb's Fly.io pricing breakdown](https://www.withorb.com/blog/flyio-pricing), Fly moved to a usage-based model where the free allowance covers $5/month of compute credit across all apps. Postgres instances eat into that credit. Developers who provisioned free Postgres clusters in 2024 and assumed they'd stay free are now hitting billing surprises as their apps scale.

---

## Three Workarounds, Three Cost Profiles

### The PgBouncer Overlay Approach

PgBouncer is the canonical answer in the Fly community forums. The standard pattern involves deploying PgBouncer as a separate Fly app sitting in front of your Postgres instance, running in transaction pooling mode. In transaction pooling, a client connection gets a server connection only during an active transaction — meaning 100 app connections might actually use only 8-12 backend Postgres connections at any moment.

The efficiency gain is real. Community benchmarks cited in the [Fly.io forum thread on PgBouncer](https://community.fly.io/t/fly-managed-postgres-and-database-connection-limit-using-the-pg-bouncer/27103) show transaction pooling reducing backend connection counts by 80-90% under typical OLTP workloads. For a Phoenix app generating 60-80 Ecto connections, this brings the backend count comfortably under 25.

But transaction pooling breaks prepared statements by default. PostgreSQL prepared statements are session-scoped. When PgBouncer shuffles connections between clients, prepared statement handles become invalid. Ecto's Postgrex driver uses prepared statements extensively. The fix — setting `PGBOUNCER_PREPARED_STATEMENTS=false` or switching to named query mode — works, but it's a footgun that isn't mentioned in most quick-start guides. Several developers in the Fly forum thread reported hours lost debugging `ERROR: prepared statement does not exist` before tracing it back to pooling mode.

The operational cost adds up, too. A minimal PgBouncer Fly app running at `shared-cpu-1x / 256 MB` costs approximately $1.94/month according to Fly's current pricing calculator. Not expensive — but it's another app to monitor, another config file to maintain, and another failure point in your connection chain.

### Upgrade the Postgres Machine

The blunter workaround: pay for more RAM. According to [Fly.io's pricing page](https://fly.io/docs/about/pricing/), upgrading from 256 MB to 512 MB costs approximately $3.19/month for a `shared-cpu-1x` instance. At 512 MB, you can safely run 40-50 connections without OOM risk — enough headroom for most solo projects and small teams.

Zero compatibility risk. No prepared statement debugging, no additional app deployments. For developers billing their own time at $50-100/hour, the break-even on this upgrade happens after roughly four minutes of PgBouncer troubleshooting.

### Connection Limiting at the Application Layer

This path gets less attention but often fits best for smaller apps. Instead of deploying infrastructure to manage connections, limit them in your application pool config.

In Phoenix/Ecto, `config/runtime.exs` accepts a `pool_size` parameter. Setting `pool_size: 5` with `queue_target: 50` and `queue_timeout: 5000` means your app maintains 5 persistent database connections but queues additional requests for up to 5 seconds before returning an error. For apps with bursty-but-low sustained traffic, this costs nothing and requires no additional infrastructure.

The failure mode is latency spikes during bursts. If 50 requests queue simultaneously against 5 connections, P99 latency climbs sharply. Monitor `DBConnection.queue_time` to catch this before users do.

### Comparison: Fly.io Postgres Connection Workarounds

| Factor | PgBouncer Overlay | Upgrade to 512 MB | App-Level Pool Limiting |
|---|---|---|---|
| **Monthly Cost** | ~$1.94 (extra app) | ~$3.19 (vs $1.94 free) | $0 |
| **Setup Time** | 2-4 hours | 5 minutes | 30 minutes |
| **Prepared Stmt Risk** | High (transaction mode) | None | None |
| **Max Backend Connections** | 8-12 active | 40-50 | Equals pool_size |
| **Best For** | High concurrency apps | Quick fix, <50 connections | Bursty-low sustained traffic |
| **Operational Overhead** | Medium (2 apps to manage) | Low | Low |

The pattern is consistent across case studies: PgBouncer earns its complexity only when you're running 100+ concurrent connections. Below that threshold, you're paying in operational overhead for a problem a $1.25/month RAM upgrade would solve.

---

## Matching Workaround to Traffic Pattern

**Scenario 1 — Side project, fewer than 20 concurrent users.** Skip PgBouncer entirely. Set `pool_size: 5` in your app config and call it done. The free tier handles this. If you're still hitting limits, your traffic pattern warrants a real database service, not connection juggling.

**Scenario 2 — Growing SaaS app, 50-200 concurrent users.** Upgrade the Postgres machine to 512 MB. That's $1.25/month over the free tier, with no compatibility risk and no second app to maintain. At this range, PgBouncer's $1.94/month actually costs *more* while introducing prepared statement risks — a bad trade in both directions.

**Scenario 3 — High-concurrency app, 200+ concurrent users.** PgBouncer makes sense, but use session pooling mode instead of transaction pooling. Session pooling preserves prepared statement compatibility. You lose some connection efficiency — session pooling is less aggressive about reuse — but avoid the Ecto/Postgrex debugging spiral entirely. At this scale, also consider whether Fly Postgres is still the right tool. Neon's serverless Postgres [pricing model](https://neon.tech/pricing) may be more cost-effective for variable-load production workloads.

**What to watch over the next 3-6 months:** Fly.io has signaled interest in a native connection pooler integrated into the managed Postgres experience, similar to how Supabase bundles PgBouncer transparently. If that ships, it eliminates the manual deployment entirely — and changes the calculus significantly for Phoenix developers specifically. Watch the Fly.io changelog and community forums for announcements.

---

## Conclusion

The PgBouncer-as-default-answer is over-prescribed. A cleaner framework:

- **PgBouncer is overkill below ~100 concurrent connections** — the compatibility risks outweigh the cost savings at smaller scale.
- **Upgrading RAM costs less than an hour of debugging** in almost every realistic scenario.
- **App-level pool limiting is the zero-cost path** for projects that don't need high concurrency.
- **Session pooling beats transaction pooling** when you're using prepared statements — which most ORMs do by default.

Over the next 6-12 months, expect Fly.io to tighten free tier limits further as usage-based billing matures. The $5/month free credit model puts gentle pressure on developers to right-size their infrastructure. Native pooling built into Fly Postgres would resolve this entire class of problem — but that feature isn't here yet.

So the action is simple: measure your actual peak connection count with `SELECT count(*) FROM pg_stat_activity;` before choosing a workaround. Don't deploy infrastructure to solve a number you haven't checked yet.

## References

1. [Fly Managed Postgres and database connection limit using the PG Bouncer - Phoenix - Fly.io](https://community.fly.io/t/fly-managed-postgres-and-database-connection-limit-using-the-pg-bouncer/27103)
2. [Fly.io pricing: Plans and cost breakdown for 2025 - Orb Billing](https://www.withorb.com/blog/flyio-pricing)
3. [Fly.io | Review, Pricing & Alternatives](https://getdeploying.com/flyio)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-sitting-on-balcony-with-smartphone-7AoGuVvYO_w)*
