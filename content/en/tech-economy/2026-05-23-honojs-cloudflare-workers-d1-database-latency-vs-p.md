---
title: "Hono.js Cloudflare Workers D1 vs PlanetScale Latency for Solo SaaS"
date: 2026-05-23T20:32:24+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "hono.js", "cloudflare", "workers", "TypeScript"]
description: "Hono.js + Cloudflare D1 is hitting 500ms+ API responses in production. Here's why solo SaaS builders are rethinking this stack."
image: "/images/20260523-honojs-cloudflare-workers-d1-d.webp"
technologies: ["TypeScript", "Next.js", "AWS", "Vercel", "Go"]
faq:
  - question: "hono.js cloudflare workers d1 database latency vs planetscale solo saas comparison which is faster"
    answer: "In a hono.js cloudflare workers d1 database latency vs planetscale solo saas comparison, PlanetScale Solo delivers faster raw query times of 5–15ms from its fixed AWS us-east-1 region, while D1 averages 80–150ms per query at the edge. However, D1 can outperform PlanetScale for globally distributed users when combined with proper caching layers, since PlanetScale's centralized region adds geographic latency for non-US users."
  - question: "why is my cloudflare workers d1 api response over 500ms in production"
    answer: "D1 responses exceed 500ms in production primarily due to cold-start database connections and sequential query patterns, not misconfiguration. Each D1 query averages 80–150ms at the edge, meaning even two or three chained queries in a single API request can push total response time well past 500ms for real SaaS workloads."
  - question: "planetscale solo plan cost vs cloudflare d1 for indie saas 2026"
    answer: "PlanetScale Solo costs $29/month as of May 2026, while Cloudflare D1 offers an aggressive free tier before paid usage kicks in, making D1 cheaper for early-stage bootstrapped products. The cost difference matters less than the architectural tradeoff — PlanetScale provides fast centralized MySQL-compatible queries, while D1 offers globally distributed SQLite storage that requires careful query optimization to avoid latency issues."
  - question: "is cloudflare d1 good enough for production saas or should I use planetscale"
    answer: "Cloudflare D1 is viable for production SaaS but requires architectural adjustments, particularly adding caching layers and minimizing sequential queries to stay under acceptable response times. For read-heavy workloads with a primarily US-based audience, PlanetScale Solo's 5–15ms query latency can be the simpler choice, while global audiences may actually benefit more from D1's edge-distributed approach."
  - question: "hono.js cloudflare workers d1 database latency vs planetscale solo saas comparison for global users"
    answer: "The core finding in a hono.js cloudflare workers d1 database latency vs planetscale solo saas comparison is that this is an architectural decision, not just a speed contest — D1 distributes data globally near users, while PlanetScale anchors queries to a single AWS us-east-1 region. Global SaaS audiences will experience significantly higher latency with PlanetScale as geographic distance from us-east-1 increases, whereas D1's edge replication is designed specifically to reduce that problem."
---

Solo SaaS builders are chasing sub-100ms response times on $20/month budgets. The stack that looked obvious six months ago — Hono.js on Cloudflare Workers with D1 — is producing 500ms+ API responses in production. That's not a configuration mistake. It's an architectural constraint worth understanding before you commit.

> **Key Takeaways**
> - Cloudflare D1 read latency in production averages 80–150ms per query at the edge, but cold-start database connections and sequential query patterns routinely push total request time past 500ms for real SaaS workloads.
> - PlanetScale Solo ($29/month as of May 2026) delivers 5ms–15ms query latency from a fixed AWS us-east-1 region — faster than D1 for co-located users, but significantly slower for global audiences.
> - This comparison isn't primarily a speed debate. It's an architectural tradeoff between globally distributed compute with edge-local data versus centralized fast queries with regional compute.
> - Solo SaaS developers running read-heavy workloads with global users should benchmark D1 with caching layers before assuming PlanetScale wins on latency.

---

## Why This Comparison Matters in 2026

Two years ago, the solo SaaS stack was boring and predictable: Next.js on Vercel, PlanetScale for the database, Stripe for billing. It worked. Then Cloudflare started aggressively positioning Workers as a full application runtime, and D1 — their SQLite-at-the-edge database product — hit general availability in late 2023.

By 2025, a generation of indie developers had shipped production SaaS on the Cloudflare stack. Hono.js emerged as the de facto framework for Workers: Express-like, TypeScript-native, near-zero overhead. The pitch was compelling — one platform, global edge deployment, no cold starts, SQLite simplicity, aggressive free tiers.

PlanetScale went through its own turbulence in parallel. After eliminating their free tier in April 2024 and restructuring pricing, the Solo plan stabilized at $29/month by mid-2025. Not cheap for a bootstrapped product, but a known quantity: MySQL-compatible, horizontally scalable, battle-tested.

The tension point arrived when developers started posting production performance numbers. A thread on r/CloudFlare in early 2026 captured the problem precisely — developers running SaaS products fully on Cloudflare reported 500ms+ per request despite Workers' theoretical speed advantage. The culprit wasn't the compute. It was the data layer.

---

## Why D1 Latency Surprises Developers

D1 is SQLite running at Cloudflare's edge locations. On paper, that means your database query executes close to your user. In practice, two problems compound.

First, D1's architecture as of 2026 uses a primary write location with read replication. Writes always hit the primary. Reads *should* hit a nearby replica, but replica propagation adds latency — and the routing isn't always as local as you'd expect. Cloudflare's own documentation acknowledges that D1 is "read-replicated globally" but doesn't guarantee sub-region latency.

Second, sequential queries hurt. If your Hono.js handler runs three queries in sequence — authenticate user, fetch account, load data — you're paying the network round-trip penalty three times. In a Workers environment where the script itself starts in microseconds, the database becomes the bottleneck almost immediately.

The result: a handler that looks fast in local development hits 400–600ms in production for a logged-in user making a typical dashboard request.

---

## PlanetScale Solo's Actual Performance Profile

PlanetScale runs on AWS infrastructure. The Solo plan connects to a single primary region — historically us-east-1. For a developer building a US-focused SaaS, queries run at 5–15ms consistently. That's genuinely fast.

The constraint is geography. A user in Frankfurt hitting a PlanetScale Solo database in Virginia adds 80–120ms of pure network transit before the query even starts. So PlanetScale's "faster" label depends entirely on where your users are.

PlanetScale's connection model also differs. It uses an HTTP-based connection proxy — no persistent TCP connections, no connection pool exhaustion. A real advantage over traditional MySQL deployments. But that proxy adds a fixed overhead per query that PlanetScale benchmarks at roughly 1–3ms.

---

## Where These Stacks Stop Being Symmetric Choices

This comparison assumes D1 and PlanetScale are interchangeable options. They're not.

With Cloudflare's stack, compute *and* data are theoretically edge-local. With PlanetScale plus any fixed-region deployment, both are centralized. If your SaaS targets a global audience and you get the caching layer right on D1, edge wins. If your audience is US-only and you're running complex relational queries, PlanetScale's consistency is worth the trade.

The 500ms+ numbers reported in production almost always trace back to sequential queries against D1 writes, not reads. Batch your writes. Use D1's `batch()` API to run multiple statements in a single round-trip. That alone can cut 200–300ms from write-heavy flows.

### Comparison: Hono.js + Workers + D1 vs. PlanetScale Solo

| Criteria | Hono.js + Workers + D1 | PlanetScale Solo |
|---|---|---|
| **Base cost (2026)** | ~$5–25/month (Workers Paid + D1 usage) | $29/month flat |
| **Query latency (ideal)** | 80–150ms (edge replica) | 5–15ms (same region) |
| **Query latency (cross-region)** | 80–150ms (replicated globally) | 80–150ms+ (network transit) |
| **Write latency** | 150–300ms (primary writes) | 10–30ms |
| **Cold starts** | None (Workers are persistent) | None (HTTP proxy) |
| **Connection limits** | No connection pool needed | No connection pool (HTTP proxy) |
| **Query complexity** | SQLite-limited (no stored procs, limited joins) | Full MySQL 8.x |
| **Horizontal scale** | D1 sharding (manual) | Built-in (branching model) |
| **Best for** | Global read-heavy, simple schema SaaS | US-centric, complex relational SaaS |

---

## Three Scenarios Worth Thinking Through

**Scenario 1: Global SaaS with simple data models.** An indie developer shipping a URL shortener, link-in-bio tool, or simple scheduling app — schema is flat, reads dominate, writes are infrequent. D1 with Hono.js wins here. The global read replica advantage kicks in, costs stay below $15/month, and the SQLite constraint doesn't bite because the schema stays simple. Add `Cache-Control` headers on Hono responses and use D1's batch API aggressively.

**Scenario 2: US-focused B2B SaaS with relational complexity.** A small CRM or invoicing tool with joins across 8+ tables, complex reporting queries, and a predominantly US customer base. PlanetScale Solo is the right call. MySQL's query planner handles this far better than SQLite, and the 5–15ms latency from us-east-1 beats D1's edge reads for a US audience anyway. Deploy your API on a single-region service — Railway, Render, or Fly.io — co-located with PlanetScale's region.

**Scenario 3: Hybrid architecture.** Use Workers and Hono for your public-facing API routes (auth checks, read-heavy endpoints), connect to PlanetScale for complex writes and reporting. The architecture is less simple, but latency profiles improve meaningfully. Watch Cloudflare's Hyperdrive product — it proxies external databases including MySQL to Workers with connection pooling. As of May 2026, Hyperdrive plus PlanetScale is a legitimate production pattern.

This approach can fail when your team lacks the operational overhead to maintain two database layers. For a solo founder already context-switching between product, support, and growth, a hybrid data architecture introduces failure modes that a single-platform approach avoids entirely. It's worth the complexity only if benchmarking shows a clear latency win for your specific query patterns.

**What to watch in the next 90 days:** Cloudflare has been iterating D1's read replica routing aggressively. If they ship automatic query routing based on user IP geolocation for reads — currently in beta per their changelog — the D1 latency story changes materially.

---

## Where This Goes in the Next 12 Months

The data points to a conclusion that gets buried in marketing copy:

- D1 write latency is the real bottleneck for SaaS apps, not read latency
- PlanetScale Solo is faster within its region but loses its advantage for global audiences
- The winner is determined by your user geography and schema complexity, not by any universal performance ranking
- Hyperdrive is the emerging bridge that may make this debate obsolete

Over the next 6–12 months, expect D1's global write performance to improve as Cloudflare builds out their storage infrastructure. PlanetScale, meanwhile, is positioning toward larger teams — the Solo plan may face pricing pressure as competition intensifies.

The practical takeaway: benchmark your specific query pattern before choosing a stack. Run `wrk` against a staging environment with realistic data volumes. A tool that returns 12ms for a single-row lookup might return 480ms for your actual multi-join dashboard query.

The stack that wins is the one you've tested under your real workload — not the one with the better conference talk.

*Which query pattern is your SaaS actually dominated by — reads or writes? That answer determines your stack.*

## References

1. [r/CloudFlare on Reddit: Anyone hosted SaaS fully on Cloudflare? Mine slow as hell, 500ms+ per reques](https://www.reddit.com/r/CloudFlare/comments/1qk6z8q/anyone_hosted_saas_fully_on_cloudflare_mine_slow/)
2. [Choosing a data or storage product. · Cloudflare Workers docs](https://developers.cloudflare.com/workers/platform/storage-options/)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
