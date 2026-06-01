---
title: "Cloudflare Workers KV vs D1 SQLite Latency: Edge API Tradeoffs"
date: 2026-04-18T20:01:25+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "cloudflare", "workers", "sqlite", "Go"]
description: "Cloudflare Workers KV vs D1 SQLite latency benchmarked in 2025. D1 GA surprised teams with faster reads — see which storage layer wins for edge APIs."
image: "/images/20260418-cloudflare-workers-kv-vs-d1-sq.webp"
technologies: ["Go", "Cloudflare"]
faq:
  - question: "cloudflare workers kv vs d1 sqlite latency real benchmark edge api 2025 which is faster"
    answer: "Based on real benchmark data, KV is faster for simple key lookups, regularly hitting sub-5ms read latency on cache-hit paths at the edge. D1 SQLite delivers p50 read latency of around 10–25ms depending on region and database size, making KV the winner on raw read speed but D1 the better choice when you need relational queries or strong consistency."
  - question: "what is the difference between cloudflare KV and D1 SQLite for edge APIs"
    answer: "Cloudflare KV is a globally distributed key-value store that is eventually consistent, meaning writes can take up to 60 seconds to propagate across all edge locations. D1 SQLite uses a primary-replica model that supports relational queries and stronger consistency, but does not yet reach the full 310+ point-of-presence network that KV covers."
  - question: "cloudflare workers kv vs d1 sqlite latency real benchmark edge api 2025 which should I use"
    answer: "For most edge APIs, the decision comes down to data model complexity rather than raw performance. Choose KV when you need ultra-fast reads for simple key lookups like config or cached content, and choose D1 when your API requires relational structure, joins, or consistent reads after writes."
  - question: "is cloudflare D1 eventually consistent like KV"
    answer: "No, D1 SQLite and KV handle consistency very differently. KV is eventually consistent by design, with writes propagating across edge locations within roughly 60 seconds, while D1 uses a primary-replica model that routes all writes through a single primary, offering stronger consistency guarantees for relational data."
  - question: "cloudflare KV read latency vs D1 read latency numbers"
    answer: "Cloudflare KV regularly achieves sub-5ms read latency on cache-hit paths because reads are served directly from the nearest edge location without touching an origin. D1 SQLite read latency sits around 10–25ms at the p50 level, varying by region and database size, due to its primary-replica architecture."
---

Pick the wrong storage layer on Cloudflare Workers and you'll pay for it in milliseconds — and at scale, that compounds fast. The KV vs D1 SQLite debate exploded on engineering forums late last year, and for good reason: D1 hit general availability with meaningfully better read performance than many teams expected, while KV's eventual consistency model kept tripping up developers who assumed it behaved like a traditional cache.

Both products sit inside the same Workers runtime. Both are serverless. Both bill in a way that looks cheap until your API handles serious traffic. But they're solving fundamentally different problems, and confusing them costs you either latency or correctness — sometimes both.

This piece cuts through the noise with real benchmark data and architecture context: KV vs D1 read/write latency across cold and warm request paths, where each storage layer breaks under production load, how to match the right tool to your actual API access pattern, and what's changing in Cloudflare's storage roadmap through late 2026.

**The short version:** KV wins on read latency for simple key lookups at the edge, regularly hitting sub-5ms on cache-hit paths. D1 wins on query expressiveness and consistency, with p50 read latency around 10–25ms depending on region and database size. For most edge APIs, the decision isn't performance — it's data model complexity.

---

## Background: How These Two Products Actually Differ

Cloudflare Workers launched in 2017 as a pure compute layer. Storage was the obvious gap, and KV shipped in 2019 as the first answer — a globally distributed key-value store built on Cloudflare's edge network, which spans 310+ locations as of April 2026 (per Cloudflare's network status page).

KV's architecture is eventually consistent by design. Writes propagate across PoPs within roughly 60 seconds under normal conditions, according to Cloudflare's official KV documentation. That tradeoff bought massive read scalability: a cache-hit KV read doesn't touch an origin server at all. For content delivery and config propagation, it worked well. For anything requiring fresh writes or relational structure, it was awkward.

D1 entered public beta in 2022 and hit GA in late 2023. It's SQLite running at the edge — specifically, Cloudflare's distributed SQLite implementation using a primary-replica model. The primary handles all writes; read replicas are placed across regions. As of Q1 2026, D1 supports up to 10GB per database and offers read replication to a subset of Cloudflare's global PoPs, though not the full 310+ network that KV reaches.

The timing matters. Edge API architectures are no longer experimental — they're standard practice for latency-sensitive applications. According to PropTechUSA.ai's 2025 performance comparison report, teams building real estate data APIs, fintech dashboards, and e-commerce backends are actively benchmarking these two systems against each other rather than defaulting to a centralized Postgres instance. That shift is what makes this a real engineering decision, not an academic one.

---

## The Latency Numbers, With Full Context

### KV: Fast When Warm, Painful When It's Not

KV's best-case read performance is genuinely impressive. On a cache-hit request — meaning the key exists in the local PoP's cache — read latency sits between 1ms and 5ms consistently. Postry's practical edge computing guide benchmarks this range as reliable across North American and European PoPs.

Cache misses are a different story. When a key isn't locally cached (after a write or expiration), KV must fetch from Cloudflare's central store, pushing latency to 50–100ms. That's not catastrophic, but it matters if you're building an API with tight SLAs. Write latency runs even higher — typically 100–200ms because writes must propagate before confirming.

The practical consequence: KV works best when reads vastly outnumber writes and when stale-by-60-seconds data is acceptable. Feature flags, JWT public keys, and CDN configuration are perfect fits. User-specific session state with frequent updates? Much riskier.

### D1: The SQLite Trade-Off

D1's p50 read latency runs higher than KV's cache-hit performance — roughly 10ms to 25ms for simple `SELECT` queries, based on PropTechUSA.ai's benchmark data collected across multiple D1 databases in the 100MB–2GB range. Write latency is roughly 20–40ms for single-row inserts.

What D1 gives you in return is transactional consistency and SQL expressiveness. A query that joins user records, applies filters, and returns paginated results takes one round trip. KV would require multiple reads plus client-side assembly — with all the latency that stacks up.

D1's read replica coverage is still expanding. As of April 2026, Cloudflare's D1 documentation lists replica placement as "automatic and expanding," without publishing specific PoP counts. For teams in North America and Western Europe, D1 read latency is competitive. For Southeast Asia and South America, the numbers are less predictable and worth testing explicitly before committing.

### Where Each One Breaks

KV breaks when you need strong consistency (write then immediate read), structured queries across multiple keys, or transactional operations involving atomic multi-key updates.

D1 breaks when you need sub-5ms reads at global scale, extremely high read throughput without row-level caching, or database sizes above D1's current 10GB per-database limit.

### KV vs D1 for Edge API Workloads

| Criteria | Workers KV | D1 SQLite |
|---|---|---|
| **p50 Read Latency (cache hit)** | 1–5ms | 10–25ms |
| **p50 Read Latency (cache miss)** | 50–100ms | 10–25ms (consistent) |
| **Write Latency** | 100–200ms | 20–40ms |
| **Consistency Model** | Eventual (~60s) | Strong (primary) |
| **Query Capability** | Key lookup only | Full SQL (joins, aggregations) |
| **Global PoP Coverage** | 310+ locations | Expanding replicas (subset) |
| **Max Storage** | 25MB per value, unlimited keys | 10GB per database |
| **Pricing Model** | Reads/writes per million | Reads/writes + storage GB |
| **Best For** | Config, flags, session tokens | Relational data, transactional APIs |

The latency gap between KV cache-hits and D1 is real but often overstated in forum discussions. For most API response budgets targeting under 100ms total, both fit comfortably. The decision point usually isn't raw speed — it's whether your data model requires SQL or not.

Teams in Cloudflare's own developer ecosystem (based on Workers changelog notes from 2025) have started recommending a hybrid pattern: use D1 as the source of truth, and write hot read paths into KV with a short TTL. That captures KV's edge speed while maintaining D1's consistency for writes. More teams are shipping this pattern in production heading into late 2026.

---

## Three Real Scenarios, With Honest Recommendations

The KV vs D1 framing implies a binary choice. In practice, the worst outcomes come from treating it as one.

**Scenario 1: High-traffic public API serving semi-static data**

Think a product catalog, exchange rates, or sports scores updated every 30–60 seconds. KV is the right call. Writes are infrequent, reads are massive, and eventual consistency matches the update cadence. Store a JSON blob per entity, key by ID, and you're getting sub-5ms reads globally. Use KV with a 60-second TTL and a background Worker that pushes updates on change.

**Scenario 2: User-facing API with account data and preferences**

This is where D1 earns its place. User records have relations, preferences span multiple tables, and writes need to be immediately visible on the next read. Eventual consistency is a bug here, not a feature. Use D1 as primary, with KV caching only non-personalized, low-churn data — like plan metadata or public content.

**Scenario 3: Real-time collaborative features**

Neither KV nor D1 fits well here. KV's eventual consistency creates conflicts; D1's write latency is too high for sub-100ms round trips. Cloudflare's Durable Objects — which maintain single-instance state with WebSocket support — handle this pattern. Don't force KV or D1 into a real-time use case. That's not a failure of either product; it's a scope mismatch.

---

## What the Benchmarks Actually Show

Cloudflare has signaled expanded D1 read replica coverage on its 2026 roadmap. If D1 reaches KV-level PoP coverage, the latency gap narrows significantly and the case for KV as a read layer weakens for most use cases. Infrastructure investments in 2026 are visibly weighted toward D1 maturity — larger database limits, more replica locations, and point-in-time recovery now in beta. If those ship on schedule, this conversation shifts: D1 becomes viable for use cases KV currently dominates.

Until then, the benchmarks point to a clear set of conclusions:

> **Key Takeaways**
> - KV dominates on cache-hit read latency (1–5ms vs. 10–25ms for D1), but that advantage collapses entirely on cache misses
> - D1 wins on write latency and consistency — 20–40ms writes beat KV's 100–200ms, with strong consistency included at no extra cost
> - Your data model, not the latency chart, should drive the decision — SQL requirements go to D1, simple key lookups go to KV
> - Hybrid architectures (KV as a read cache in front of D1) are becoming the production standard for complex edge APIs that need both speed and correctness

Run your own benchmarks against your actual query patterns and data sizes. Published averages don't account for your specific PoP distribution or database row count. Cloudflare's `wrangler d1 execute` supports local testing, and KV's preview mode works in the same pipeline. The specifics of your workload will tell you more than any general comparison — including this one.

**What's your current storage setup on Workers, and what's pushing you toward one or the other?** Drop it in the comments — the edge cases are almost always more interesting than the general case.

## References

1. [Edge Computing with Cloudflare Workers: A Practical Guide for Devs | Postry](https://www.postry.com.br/en/blog/edge-computing-cloudflare-workers-guide)
2. [Cloudflare Workers KV vs D1: Complete Performance Guide | PropTechUSA.ai](https://www.proptechusa.ai/news/cloudflare-workers-kv-vs-d1-performance-comparison)
3. [Cloudflare Workers KV · Cloudflare Workers KV docs](https://developers.cloudflare.com/kv/)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-sitting-on-balcony-with-smartphone-7AoGuVvYO_w)*
