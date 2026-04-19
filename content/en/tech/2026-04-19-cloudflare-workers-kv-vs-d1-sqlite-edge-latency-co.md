---
title: "Cloudflare Workers KV vs D1 SQLite: Edge Latency for SaaS"
date: 2026-04-19T19:54:34+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "cloudflare", "workers", "sqlite", "AWS"]
description: "KV vs D1 SQLite at Cloudflare's 300+ edge locations: which wins for small SaaS latency in 2025? Real tradeoffs, no server management needed."
image: "/images/20260419-cloudflare-workers-kv-vs-d1-sq.webp"
technologies: ["AWS", "Go", "Cloudflare", "Supabase"]
faq:
  - question: "cloudflare workers kv vs d1 sqlite edge latency comparison small saas 2025 which is faster"
    answer: "Cloudflare Workers KV delivers read latencies under 10ms globally for cached values, while D1 SQLite averages 15–40ms for simple reads and 80–120ms for complex joins. For raw speed on simple lookups, KV wins, but D1 is the more practical default for most small SaaS applications that need relational data and transactional consistency."
  - question: "should I use cloudflare KV or D1 for my small saas app"
    answer: "For most small SaaS products under 10,000 daily active users, D1 SQLite is the recommended default because it supports relational queries and consistent application state. KV is better suited for specific use cases like feature flags, session caching, and configuration data where eventual consistency is acceptable."
  - question: "cloudflare workers kv vs d1 sqlite edge latency comparison small saas 2025 cost difference"
    answer: "KV storage costs $0.50 per GB per month with read operations at $0.50 per million after the free tier, while D1 charges $0.75 per million rows read. Cost modeling is non-trivial at scale, so teams should estimate their expected read volumes and data size before committing to either option."
  - question: "what are the limitations of cloudflare D1 SQLite at scale"
    answer: "Cloudflare D1 has a 10GB per-database size limit, making it unsuitable for large datasets, and complex JOIN queries can push latency into the 80–120ms range. D1 also has less production hardening than KV, having only reached general availability in mid-2024, meaning edge cases are still being discovered in real-world workloads."
  - question: "is cloudflare KV eventually consistent and does it matter for saas"
    answer: "Yes, Cloudflare Workers KV uses an eventual consistency model, meaning writes may not be immediately visible across all edge locations. For transactional SaaS data such as user accounts, billing state, or inventory, this makes KV unsuitable, as stale reads can cause real data integrity problems rather than just minor inconveniences."
---

The choice between Cloudflare Workers KV and D1 SQLite is quietly becoming one of the most consequential architectural decisions a small SaaS team can make. Get it wrong and you're chasing latency regressions at 2am. Get it right and your app feels instant to users across 300+ Cloudflare edge locations — without managing a single server.

Both products live on Cloudflare's edge network. Both promise low-latency data access. But they're built for fundamentally different access patterns, and in 2026, the gap between "good enough" and "production-ready" often comes down to this one call.

Small SaaS products face a specific constraint: tight budgets, minimal DevOps headcount, and users who expect sub-100ms responses. The KV vs. D1 debate has been alive in developer communities for two years now, but the conversation has matured significantly as D1 moved out of beta and KV pricing shifted in Q3 2025.

What follows is what the data actually shows — measured latency differences, cost curves, query patterns, and when each tool earns its place in your stack.

**Topics covered:**
- KV read latency vs. D1 query latency under realistic SaaS workloads
- When eventual consistency in KV becomes a real problem, not just a footnote
- D1's SQLite limitations at scale and where they bite hardest
- A decision framework for small SaaS teams picking between them

> **Key Takeaways**
> - Cloudflare Workers KV delivers read latencies consistently under 10ms globally for cached values, but its eventual consistency model makes it unsuitable for transactional SaaS data.
> - D1 SQLite queries from Cloudflare's edge currently average 15–40ms for simple reads, rising to 80–120ms for complex joins, based on Cloudflare's published D1 benchmarks (2025).
> - KV storage costs $0.50/GB/month with read operations at $0.50 per million after the free tier; D1 charges $0.75/million rows read, making cost modeling non-trivial at scale.
> - For most small SaaS products under 10,000 daily active users, D1 is the more correct default — KV should serve configuration data, feature flags, and session caching, not application state.

---

## Background & Context

Cloudflare Workers launched in 2017 as a serverless edge compute platform. KV storage arrived shortly after, in 2018, as the natural companion — a distributed key-value store that replicated data across Cloudflare's global network. The pitch was simple: write to one location, read from anywhere with single-digit millisecond latency.

D1 came much later. Cloudflare announced D1 in 2022 and ran an extended public beta through 2023–2024. The GA release landed in mid-2024, with meaningful performance improvements shipping through 2025. D1 is SQLite running at the edge, closer to the Worker than a traditional remote database — but not as close as KV's in-memory cache reads.

That context matters. KV has five years of production hardening. D1 is still accumulating battle scars. Cloudflare's own documentation acknowledges D1's 10GB per-database limit and the absence of multi-region write replication — D1 writes go to a single primary region and replicate reads globally.

That asymmetry — fast global reads, single-region writes — is a deliberate architectural choice. SQLite's single-writer model maps directly to it. And for most small SaaS applications, writes are the minority of traffic. Read-heavy workloads like dashboard queries, user profile fetches, and content delivery map naturally onto D1's strengths.

KV dropped strong consistency from its feature set deliberately. According to Cloudflare's official KV documentation, changes propagate globally within 60 seconds under normal conditions, though the median is often faster. This makes KV inappropriate for any data where two users might race to read a just-written value and get different results.

The small SaaS market accelerated its adoption of Cloudflare Workers through 2025, driven by the Workers free tier (100,000 requests/day) and the predictable cost model compared to AWS Lambda's request-plus-duration billing.

---

## Read Latency: KV's Structural Advantage for Cached Data

KV wins the raw latency race. Full stop.

When a value exists in KV's edge cache — meaning it's been accessed recently from a nearby PoP — reads come back in under 5ms, sometimes under 2ms, according to Cloudflare's internal benchmarks cited in their developer documentation. That's memory-speed access from the edge node processing your Worker.

D1 reads don't compete at that tier. According to Cloudflare's D1 performance documentation and independent benchmarks published by PropTechUSA.ai in late 2025, simple D1 queries on small tables average 15–25ms. Complex joins with multiple tables push that to 80–120ms. The D1 database lives close to the Worker, but it's still a SQLite file being queried, not a hash map lookup.

For session tokens, feature flags, or rate-limit counters, that 20ms difference across millions of requests compounds fast. KV was built for exactly these cases.

The nuance: KV's cache isn't guaranteed. A cold read — a key that hasn't been accessed from a particular region recently — goes back to the primary storage layer. Cold KV reads can take 50–100ms, erasing the latency advantage entirely. Apps with sparse, diverse key access patterns don't always get the headline 2ms number.

---

## Consistency Model: Where KV's Limitations Bite SaaS

Eventual consistency sounds fine in theory. In practice, it creates failure modes that are hard to debug and impossible to explain to customers.

Consider a billing SaaS scenario: a user upgrades their plan, the app writes their new plan tier to KV, and the next request checks that value to gate a premium feature. If the write hasn't propagated to the edge PoP handling the next request — which can happen within that 60-second window — the user sees an inconsistent state. They paid. The feature doesn't unlock. Support ticket incoming.

D1's consistency model is stronger. Reads from the global read replicas are eventually consistent with the primary, but Cloudflare reduced that lag significantly through 2025. More critically, if you route reads to the primary region (adding latency), you get strong consistency. D1 also supports transactions — `BEGIN`, `COMMIT`, `ROLLBACK` — which KV simply doesn't offer.

For any SaaS data involving money, permissions, or user state, the decision effectively makes itself: D1 is the correct choice.

This approach can fail when teams treat D1 as a drop-in replacement for a fully distributed database. D1 isn't that. Single-region writes mean that write-heavy, globally distributed workloads will feel the latency of that primary region. If your users are split across continents and generating high write volumes, you'll hit D1's architectural ceiling before you hit its storage limit.

---

## Query Expressiveness and Operational Complexity

KV's API surface is minimal. `get`, `put`, `delete`, `list`. That's the model. Fast to learn, fast to implement for simple cases — but any relational data model becomes painful quickly. Searching for all users in a specific plan tier means maintaining secondary indexes manually: storing extra keys that map plan tiers to user IDs, keeping them in sync, handling race conditions yourself.

D1 gives you SQL. Full SQLite SQL: `SELECT`, `JOIN`, `WHERE`, `GROUP BY`, indexes, foreign keys (when enabled), prepared statements. According to Cloudflare's D1 documentation, D1 supports most of SQLite 3.x's feature set. For a SaaS product with even modest data modeling requirements — users, organizations, subscriptions, usage events — this expressiveness difference is decisive.

The operational gap is smaller than it looks. D1 handles backups, replication, and scaling automatically. No connection pooling to configure, no `pg_hba.conf` to touch. It's significantly simpler than running PlanetScale or Supabase, and it stays within the Cloudflare ecosystem if you're already there.

---

## Side-by-Side: KV vs D1 for Small SaaS Workloads

| Criteria | Workers KV | D1 SQLite |
|---|---|---|
| **Avg. Read Latency (cached)** | 2–10ms | 15–40ms |
| **Avg. Read Latency (cold)** | 50–100ms | 15–40ms (consistent) |
| **Write Consistency** | Eventual (~60s propagation) | Strong (primary) / Eventually consistent (replicas) |
| **Query Model** | Key-value only | Full SQLite SQL |
| **Transactions** | No | Yes (ACID) |
| **Max Storage** | 25GB per namespace | 10GB per database |
| **Cost (reads)** | $0.50/million after free tier | $0.75/million rows read |
| **Best For** | Flags, sessions, caching | App state, user data, billing |
| **Worst For** | Relational data, transactions | Extremely low-latency global caching |

The cost picture isn't straightforward. KV charges per operation; D1 charges per row read. A query that scans 10,000 rows costs the same in D1 as 10,000 individual KV reads — but the query returns structured, relational results that would require significant application logic to replicate in KV. Efficient D1 indexes reduce row-scan counts dramatically, which directly controls cost at scale.

Practically: a small SaaS at 5,000 DAU with typical usage patterns will spend under $20/month on D1. The same product at 50,000 DAU starts needing careful index design to stay under $100/month.

---

## Practical Implications: Picking the Right Tool Per Data Type

The core challenge isn't picking a winner. It's recognizing that these two tools aren't competing — they're complementary. Using only KV means building a relational database on top of key-value primitives, which is a painful path. Using only D1 for every data access means accepting 15–40ms latency on things that should be instant.

**Scenario 1: User session management**
Session data is write-once-read-many, doesn't need transactions, and tolerable eventual consistency is fine — a 60-second window where a just-created session isn't globally visible is acceptable for most apps. KV is correct here. Store session tokens in KV, get 2–5ms validation on every authenticated request.

**Scenario 2: Subscription gating**
A user's plan tier determines feature access. Checked on every API call. The data changes infrequently, but incorrectly serving stale data has real business consequences. D1 is correct here. Store plan data in D1, query it with a prepared statement, and accept 20–30ms on that single read for the guarantee that it's accurate.

**Scenario 3: Feature flags**
Boolean values, changed occasionally by internal tooling, read on every request. KV is the canonical answer — low latency, high read volume, and stale data for 60 seconds is an acceptable trade-off for a feature flag system.

The pattern holds consistently: use KV as a caching layer for configuration and session data. Use D1 as your application database for anything that needs consistency or relational queries. The framing that you need to pick one is a false constraint. The right architecture uses both, deliberately.

**What to watch:** Cloudflare has signaled plans for D1 read replica improvements and potential multi-primary write support in their 2026 roadmap. If write replication ships, D1 becomes viable for a much wider range of real-time SaaS use cases that currently require external databases like PlanetScale or Turso.

---

## Conclusion

The key findings are straightforward:

- KV delivers under 10ms reads for cached data — the right tool for sessions, flags, and configuration
- D1 SQLite averages 15–40ms for simple queries with full ACID transactions and SQL expressiveness
- Eventual consistency makes KV wrong for billing, permissions, or any transactional SaaS data
- The optimal small SaaS architecture uses both — KV for caching, D1 for application state

Looking ahead 6–12 months: D1's 10GB database limit is the most pressing constraint for growing SaaS products, and Cloudflare is expected to raise it. Multi-region D1 writes — if they ship — would close the remaining gap that pushes teams toward external databases. KV pricing changes in Q3 2025 made it slightly more expensive at high read volumes, nudging more teams toward D1 for reads that don't require sub-10ms performance.

The edge-native data stack is maturing fast. By end of 2026, this may be settled architecture rather than active debate.

Pick the right tool for each data type. The latency difference is real — but the consistency difference is what actually breaks production apps.

What's your current split between KV and D1 in production? The architecture decisions teams are making today will define the edge-native SaaS patterns of the next three years.

## References

1. [Edge Computing with Cloudflare Workers: A Practical Guide for Devs | Postry](https://www.postry.com.br/en/blog/edge-computing-cloudflare-workers-guide)
2. [Cloudflare Workers KV vs D1: Complete Performance Guide | PropTechUSA.ai](https://www.proptechusa.ai/news/cloudflare-workers-kv-vs-d1-performance-comparison)
3. [Cloudflare Workers KV · Cloudflare Workers KV docs](https://developers.cloudflare.com/kv/)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
