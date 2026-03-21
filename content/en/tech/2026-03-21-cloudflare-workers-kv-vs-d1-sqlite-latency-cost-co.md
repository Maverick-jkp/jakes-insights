---
title: "Cloudflare Workers KV vs D1 SQLite: Latency and Cost for Small SaaS"
date: 2026-03-21T19:51:00+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "cloudflare", "workers", "sqlite", "Go"]
description: "Compare Cloudflare Workers KV vs D1 SQLite latency and cost before $5,000 MRR forces a painful weekend migration on your small SaaS stack."
image: "/images/20260321-cloudflare-workers-kv-vs-d1-sq.webp"
technologies: ["Go", "Cloudflare"]
faq:
  - question: "cloudflare workers kv vs d1 sqlite latency cost comparison small saas 2025 which is better"
    answer: "The better choice depends entirely on your data access pattern, not just price. Cloudflare KV excels at ultra-fast global reads (under 5ms) for simple key-value lookups like feature flags or session tokens, while D1 SQLite is the right fit for relational data like user records, subscriptions, and audit logs that require SQL queries and strong consistency."
  - question: "how fast is cloudflare d1 vs kv read latency"
    answer: "Cloudflare KV delivers sub-5ms read latency globally by serving data from the nearest edge cache, making it one of the fastest read options available. D1 SQLite sits slightly higher in latency since it runs a SQLite instance co-located with your Worker rather than serving from a pure cache, but it eliminates the round-trip cost of hitting a remote database like Postgres."
  - question: "cloudflare d1 free tier limits 2025 is it enough for small saas"
    answer: "Cloudflare D1's free tier includes 5 million row reads and 100,000 row writes per day, which is generous enough for most early-stage SaaS products. For small SaaS teams with under roughly 10,000 active users, D1 typically stays within the free tier and costs less than $1/month even at moderate growth."
  - question: "cloudflare workers kv vs d1 sqlite latency cost comparison small saas 2025 which should a solo founder pick"
    answer: "For a bootstrapped founder building a relational SaaS product with user accounts, subscriptions, or audit logs, D1 SQLite is the stronger default choice due to its full SQL support, strong consistency, and generous free tier. KV is better reserved for specific use cases like caching, feature flags, or session tokens where eventual consistency is acceptable and read speed is the top priority."
  - question: "is cloudflare kv eventually consistent and does it matter for saas apps"
    answer: "Yes, Cloudflare KV is eventually consistent, meaning writes can take up to roughly 60 seconds to propagate across all 300+ edge locations globally. For SaaS applications where data accuracy matters — such as user permissions, billing status, or account settings — this eventual consistency can cause real bugs, making D1's strong consistency model a safer architectural choice."
---

Picking the wrong data layer at $50 MRR is annoying. Picking it at $5,000 MRR costs you a full weekend of migrations. The Cloudflare Workers KV vs D1 SQLite latency and cost comparison for small SaaS isn't a theoretical debate — it's a decision that directly shapes your architecture, your bill, and your users' experience.

Cloudflare's edge data story has matured fast. D1 hit general availability in late 2023, and by early 2026, it's processing hundreds of millions of queries daily according to Cloudflare's own engineering blog. KV has been battle-tested since 2018. So which one should a bootstrapped SaaS founder or solo dev reach for?

The answer depends entirely on your query pattern. And most comparisons get this wrong by treating them as substitutes.

> **Key Takeaways**
> - Cloudflare KV delivers sub-5ms read latency globally through edge caching, but it's fundamentally an eventually consistent key-value store — not a relational database.
> - Cloudflare D1 (SQLite at the edge) supports full SQL queries with strong consistency, making it the right fit for relational SaaS data like user records, subscriptions, and audit logs.
> - KV's free tier covers 100,000 reads/day and 1,000 writes/day; D1's free tier covers 5 million row reads and 100,000 row writes per day, per Cloudflare's official pricing page.
> - For most small SaaS products under roughly 10,000 active users, D1 fits within the free tier and costs less than $1/month at moderate growth.
> - This comparison ultimately comes down to access pattern, not just price.

---

## Background: How Cloudflare Got Here

Cloudflare Workers launched compute at the edge in 2017. KV followed a year later, solving one obvious problem: Workers needed somewhere to read config, feature flags, and session tokens without round-tripping to a central database. It was never designed to be a full database. It does one thing exceptionally well — low-latency, globally distributed reads with eventual consistency.

D1 came later, entering open beta in 2022 and reaching general availability in 2023. The bet was explicit. Cloudflare's engineering team wrote in their "D1: our quest to simplify databases" post that they wanted SQLite running at the edge so developers wouldn't need a separate database vendor at all. D1 runs a SQLite instance co-located with your Worker, eliminating the cold-start latency of hitting a remote Postgres cluster.

By Q1 2026, D1 supports read replicas across multiple regions, WAL-based replication, and time-travel queries for point-in-time recovery. This isn't a toy. Small SaaS teams running on Workers now have a credible full-stack option without leaving Cloudflare's ecosystem entirely.

---

## KV: Built for Reads, Not Relationships

KV is a global, eventually consistent key-value store. Writes propagate across Cloudflare's 300+ points of presence within roughly 60 seconds. Reads hit the nearest edge node — often under 5ms. That's genuinely fast.

But that speed comes with hard constraints. No queries. No filtering. No joins. If you need to fetch all users in a specific subscription tier, you can't do it directly. You'd need to build your own index keys and manage that complexity manually. Write latency sits around 200ms because writes must reach a central region before acknowledging.

For feature flags, A/B test configs, rate-limit counters, and user session tokens, KV is excellent. For anything resembling a relational dataset, it starts creating architectural debt immediately.

---

## D1: SQLite Where Your Code Already Lives

D1 gives you a full SQLite database running in the same region as your Worker. SQL queries execute in roughly 1–5ms when the Worker and database are co-located. According to Cloudflare's D1 documentation updated in January 2026, D1 now supports up to 10GB per database and auto-scales read replicas globally for read-heavy workloads.

The critical insight: D1 read replicas work similarly to KV in one respect — reads are served from the nearest node. Writes still go to the primary (currently one writable instance per database). For SaaS apps where reads dwarf writes, and a 10:1 ratio is realistic, this architecture handles real traffic without breaking down.

D1 also integrates directly with Cloudflare's `wrangler` CLI. Schema migrations, seeding, and local development all work offline with the same SQLite file, which keeps the development loop tight.

---

## Latency Reality: Numbers That Actually Matter

| Metric | Workers KV | D1 (SQLite) |
|---|---|---|
| Read latency (cached edge) | ~2–5ms | ~1–5ms (co-located) |
| Write latency | ~150–250ms | ~30–60ms (WAL commit) |
| Query complexity | Key lookup only | Full SQL (joins, filters, aggregations) |
| Consistency model | Eventually consistent | Strong consistency (single primary) |
| Max value/row size | 25MB per value | 1MB per row, 10GB DB max |
| Free tier reads | 100,000/day | 5M row reads/day |
| Free tier writes | 1,000/day | 100,000 row writes/day |
| Paid pricing (reads) | $0.50/million | $0.001/100K rows |
| Best for | Config, sessions, feature flags | User data, billing records, app state |

The free tier gap is striking. D1 gives you 50x more read operations daily on the free plan. For a small SaaS doing 2–3 million queries per day, KV gets expensive fast while D1 stays free.

---

## Cost Projection for a Small SaaS

Take a realistic small SaaS: 500 active users, each triggering roughly 200 database operations per day. That's 100,000 operations daily.

**KV cost**: 100K reads hits the free tier ceiling. Add any writes above 1,000 per day and you're on the paid plan at $5/month base plus $0.50 per million reads. At 10K writes per day, you're looking at roughly $5.20/month just for KV.

**D1 cost**: 100K operations sits well within the 5M daily read free tier. Even at 10x growth, D1's paid plan at $0.001 per 100K rows stays under $0.50/month for reads.

At small scale, D1 is cheaper. For relational data workloads, the cost comparison tilts heavily toward D1.

This approach can fail, though. If your access pattern is genuinely key-value shaped — think session tokens, feature flags, or per-user rate-limit counters — D1 adds unnecessary overhead. Forcing relational structure onto flat data wastes both query complexity and mental overhead.

---

## Practical Implications: Matching the Tool to the Pattern

**Scenario 1 — Feature flags and session management**: KV wins. If you're storing JWT session state or rolling out a feature to 10% of users, KV's roughly 3ms global read latency and simple API are the right fit. D1 adds unnecessary complexity for pure key-value access.

**Scenario 2 — User records, subscriptions, and billing**: D1 wins. Running `SELECT * FROM users WHERE plan = 'pro' AND last_active > ?` is a single D1 query. The same operation in KV requires maintaining separate index keys, manual consistency management, and significantly more code surface area. Every workaround expands your error surface.

**Scenario 3 — Hybrid architecture**: Many production Workers setups already run both. KV handles the hot path — session lookups, config reads — while D1 handles business logic queries. Cloudflare's own developer documentation explicitly shows this pattern. That's not over-engineering. It's matching the tool to the access pattern.

**What to watch**: Cloudflare is actively expanding D1 write capabilities. A multi-primary D1 configuration would close the last real latency gap for write-heavy edge workloads. If that ships in 2026, the remaining advantage KV holds in that category shrinks considerably.

---

## Conclusion

Three things stand out from this comparison.

KV's strength is speed on simple reads. Nothing beats 3ms globally for key lookups, and the service has been production-stable for seven years. D1's strength is SQL at zero extra cost — for relational SaaS data, it's already the better choice on both latency and pricing at small scale. And they're not substitutes. The best Workers-based SaaS architectures use both, routing traffic by access pattern rather than forcing everything through one layer.

Over the next 6–12 months, watch for D1 multi-region write support and tighter Hyperdrive integration that could let D1 front external Postgres instances. If that matures, D1 becomes a caching and edge-query layer on top of existing databases — a strong story for SaaS teams that can't fully migrate away from Postgres yet.

Start with D1 for your application data. Add KV where latency is critical and the data is truly key-value shaped. Don't pick one and force everything into it.

What's your current data layer on Workers — have you benchmarked D1's read replicas under real load yet?

## References

1. [r/CloudFlare on Reddit: Cloudflare D1 vs other serverless databases - has anyone made the switch?](https://www.reddit.com/r/CloudFlare/comments/1jl1tgp/cloudflare_d1_vs_other_serverless_databases_has/)
2. [Edge Databases Compared: Cloudflare D1/KV/Durable Objects vs DynamoDB vs Cosmos DB vs Firestore](https://inventivehq.com/blog/cloudflare-d1-kv-vs-dynamodb-vs-cosmos-db-vs-firestore-edge-databases)
3. [D1: our quest to simplify databases](https://blog.cloudflare.com/whats-new-with-d1/)


---

*Photo by [Robynne O](https://unsplash.com/@roborobs) on [Unsplash](https://unsplash.com/photos/a-group-of-people-standing-next-to-each-other-HOrhCnQsxnQ)*
