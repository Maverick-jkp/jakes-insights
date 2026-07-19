---
title: "Cloudflare Workers KV vs D1 SQLite Latency for Edge Functions"
date: 2026-04-14T20:23:46+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "cloudflare", "workers", "sqlite", "Go"]
description: "Cloudflare Workers KV vs D1 SQLite isn't a simple choice. Wrong pick means 300ms latency hits users hard. Here's what small edge projects actually need."
image: "/images/20260414-cloudflare-workers-kv-vs-d1-sq.webp"
technologies: ["Go", "Cloudflare"]
faq:
  - question: "Cloudflare Workers KV vs D1 SQLite latency comparison edge function small project which is faster"
    answer: "In a Cloudflare Workers KV vs D1 SQLite latency comparison for an edge function small project, KV is faster for pure reads, delivering 5–15ms globally through edge-cached replication. D1 SQLite reads range from 10–40ms, with writes taking 20–80ms since they route to a primary region. However, for complex relational lookups, D1 can actually be faster overall because it handles in a single query what KV would require multiple round-trips to achieve."
  - question: "does Cloudflare KV have eventual consistency problems"
    answer: "Yes, Cloudflare KV uses an eventual consistency model where stale reads are possible for up to 60 seconds after a write. This means any use case requiring read-after-write guarantees — such as user account updates or inventory changes — should not use KV. For those scenarios, Cloudflare D1 SQLite is the more appropriate choice."
  - question: "Cloudflare Workers KV vs D1 SQLite latency comparison edge function small project which should I use"
    answer: "The right choice in a Cloudflare Workers KV vs D1 SQLite latency comparison for an edge function small project depends on your data model, not just raw speed. KV is best for high-read, low-write workloads like feature flags, session tokens, or config storage where eventual consistency is acceptable. D1 is the better fit when you need relational queries, structured data, or guaranteed write consistency."
  - question: "what is the write latency for Cloudflare D1 SQLite"
    answer: "Cloudflare D1 SQLite write latency ranges from approximately 20–80ms on small datasets, according to Cloudflare's own benchmark documentation. This is because all writes are routed to a single primary region rather than being distributed globally. For small projects under 10,000 daily active users, this latency is generally acceptable and rarely becomes the primary bottleneck."
  - question: "Cloudflare D1 database size limit and limitations"
    answer: "Cloudflare D1 supports up to 500MB per database and runs on a SQLite engine, making it suitable for small to mid-sized relational workloads at the edge. It supports standard SQL queries and can serve reads from regional replicas close to the user. The main limitation to plan for is that all writes go to a single primary region, which adds latency compared to fully distributed solutions."
aliases:
  - "/tech/2026-04-14-cloudflare-workers-kv-vs-d1-sqlite-latency-compari/"

---

If you're building a small edge function and you've stared at the Cloudflare docs trying to decide between KV and D1, the choice looks simple on the surface. It isn't.

The two products solve genuinely different problems, and picking the wrong one adds latency you can't easily explain to a user hitting a 300ms wall on what should be a snappy API response. With Cloudflare's network now spanning over 300 cities and D1 hitting general availability with SQLite-backed relational storage, the KV vs D1 architecture decision has become one of the most common calls for solo developers and small teams building on the edge in 2026.

**The short answer:** For pure read-heavy workloads, KV wins on latency. For structured queries with write consistency requirements, D1 is the correct tool — and the latency penalty is smaller than most benchmarks suggest.

1. KV delivers read latency as low as 5–15ms globally through edge-cached replication.
2. D1 SQLite read latency sits between 10–40ms for small datasets, with writes routed to a primary region.
3. For small projects under 10,000 daily active users, the operational difference is rarely the bottleneck — query design is.

---

> **Key Takeaways**
> - Cloudflare Workers KV achieves global read latency of 5–15ms for cached values, making it the fastest option for static or infrequently-updated key-value lookups at the edge.
> - Cloudflare D1 SQLite latency ranges from 10–40ms for reads and 20–80ms for writes on small datasets, according to Cloudflare's own D1 documentation benchmarks.
> - The KV vs D1 decision hinges on data model complexity, not raw speed alone.
> - KV's eventual consistency model means stale reads are possible for up to 60 seconds after a write, which disqualifies it from any use case requiring read-after-write guarantees.
> - D1's SQLite engine supports up to 500MB per database and handles relational queries that would require multiple KV round-trips — often resulting in *lower* total latency for complex lookups.

---

## How These Two Products Actually Work

Cloudflare KV launched in 2018 as a globally distributed key-value store. It replicates values to edge nodes across Cloudflare's network, so reads are served locally — that's where the speed comes from. Writes hit a central store and propagate outward, which explains the eventual consistency window. According to the Cloudflare Workers KV documentation, KV is designed specifically for "high-read, low-write" use cases like config storage, user session tokens, or feature flags.

D1 launched in open beta in late 2023 and reached general availability in 2024. It runs SQLite at the edge through Cloudflare's infrastructure. Unlike KV, D1 doesn't globally replicate data. Reads can be served from a read replica close to the user, but writes go to a single primary region. For small projects, this write latency is usually acceptable — but it's the tradeoff you need to understand before committing.

The broader edge database market has matured fast. Inventive HQ's 2025 edge database comparison found that Cloudflare's KV and D1 stack up favorably against DynamoDB and Firestore specifically on cold-start latency and per-request pricing for low-traffic workloads — a key reason small projects gravitate toward them.

---

## The Latency Numbers, Side by Side

### Read Performance: KV's Home Turf

KV is fast at reads. That's its entire design philosophy. A cached KV read from an edge node typically resolves in 5–15ms, according to Cloudflare's internal benchmarks. No query parsing. No SQL engine overhead. Just a key lookup against an in-memory store.

D1 reads run 10–40ms for simple `SELECT` queries on small tables under 100k rows, based on Cloudflare's D1 performance data. The SQLite engine itself is lightweight, but there's overhead from spinning up the D1 runtime and parsing the query. For a single-row lookup — equivalent to a KV `get` — D1 is slower. Full stop.

### Write Performance: A Different Story

KV writes are deceptively slow for what they appear to be. A `put` operation commits to a central store, propagates to edges asynchronously, and returns in roughly 50–100ms in some regions. The edge doesn't confirm propagation — you're writing blind.

D1 write latency is 20–80ms to the primary region. That sounds comparable, but D1 writes are *consistent* and immediately readable from the same connection. For a small project handling user-generated content, order state, or anything where stale reads cause real bugs, D1's write model is the safer choice. This approach can fail when your primary region is geographically distant from your users — something worth stress-testing before you ship.

### Structured Queries: Where D1 Actually Wins on Latency

This is the part most benchmarks miss. A single KV read is faster than a single D1 read. But what if you need three related pieces of data?

Three KV reads = 3 sequential round-trips, or a complex denormalized key design you'll regret maintaining.
One D1 JOIN = a single query.

According to PropTechUSA.ai's performance guide, multi-entity lookups requiring 3+ KV reads average 45–90ms total. A comparable D1 JOIN on indexed columns resolves in 15–35ms. The latency picture inverts completely once your data has any relational structure at all.

### Full Comparison Table

| Criteria | Workers KV | D1 SQLite |
|---|---|---|
| Cached read latency | 5–15ms | 10–40ms |
| Write latency | 50–100ms (eventual) | 20–80ms (consistent) |
| Consistency model | Eventual (up to 60s lag) | Strong (within session) |
| Data model | Key-value only | Relational (SQLite) |
| Max storage (free tier) | 1GB | 500MB / database |
| Multi-entity lookups | Slow (multiple round-trips) | Fast (JOIN queries) |
| Best for | Config, flags, session tokens | User data, app state, CMS |
| Free tier writes | 1,000/day | 100,000/day |

The free tier write differential is worth pausing on: D1's 100,000 free daily writes versus KV's 1,000 makes D1 the obvious choice for write-heavy small projects staying on the free tier.

---

## Real-World Scenarios for Small Projects

**Scenario 1: Feature flags or A/B config**

The challenge is serving configuration to thousands of edge requests with minimal latency. KV is the right call. Values change infrequently, stale reads for 60 seconds don't break anything, and 5–15ms read latency beats D1 here. Store flags as JSON values under simple keys. Done.

**Scenario 2: User profile + recent activity lookup**

A user hits your API. You need their profile *and* their last 5 actions. With KV, that's two separate reads or a denormalized blob you have to maintain manually. With D1, it's a single JOIN. The D1 query runs in roughly 25ms. The two-KV approach runs in 30–60ms *and* introduces consistency bugs when the profile updates. Use D1.

**Scenario 3: Rate limiting at the edge**

Neither product is the right answer here — Cloudflare Durable Objects handle mutable per-user counters correctly. But if you're choosing between KV and D1 for a lightweight rate limiter, KV's read speed wins for check operations, and its eventual consistency is an acceptable tradeoff for approximate rate limiting. Just don't expect precision.

---

## Picking the Right Tool Without Overthinking It

The decision comes down to one question: does your data have relationships?

No relationships, infrequent writes, pure reads → KV. Any relational structure, write consistency matters, or you're staying in the free tier with high write volume → D1.

For most small projects in 2026, D1 is the better default. The latency gap is narrowing as Cloudflare adds more D1 read replicas globally, the SQLite engine is well-understood, and the free tier is genuinely generous. KV remains the faster option for the narrow use case it was designed for — and it's still unmatched there. This isn't always the answer for every team, though. If your entire application is session tokens and feature flags, KV's simplicity is a real advantage you shouldn't ignore.

Watch for Cloudflare's rumored D1 global read replica expansion later in 2026, which would push D1 read latency closer to KV's 5–15ms range. If that ships, the comparison changes significantly.

---

**What's your current storage setup on Cloudflare Workers?** If you've run your own benchmarks on KV vs D1 for a production edge function, the methodology matters — drop the results in the comments.

## References

1. [Cloudflare Workers KV vs D1: Complete Performance Guide | PropTechUSA.ai](https://www.proptechusa.ai/news/cloudflare-workers-kv-vs-d1-performance-comparison)
2. [Cloudflare Workers KV · Cloudflare Workers KV docs](https://developers.cloudflare.com/kv/)
3. [Edge Databases Compared: Cloudflare D1/KV/Durable Objects vs DynamoDB vs Cosmos DB vs Firestore](https://inventivehq.com/blog/cloudflare-d1-kv-vs-dynamodb-vs-cosmos-db-vs-firestore-edge-databases)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
