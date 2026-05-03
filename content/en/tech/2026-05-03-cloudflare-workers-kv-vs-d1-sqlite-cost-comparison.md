---
title: "Cloudflare Workers KV vs D1 SQLite Cost Comparison for Small SaaS"
date: 2026-05-03T20:05:29+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "cloudflare", "workers", "sqlite", "Go"]
description: "Cloudflare Workers KV vs D1 SQLite cost comparison for small SaaS in 2025—stop guessing and see which database actually saves money at your scale."
image: "/images/20260503-cloudflare-workers-kv-vs-d1-sq.webp"
technologies: ["Go", "Cloudflare"]
faq:
  - question: "cloudflare workers kv vs d1 sqlite cost comparison small saas 2025 which is cheaper"
    answer: "The cheaper option depends entirely on your read/write patterns. KV costs $0.50 per million reads and $5.00 per million writes, while D1 charges $0.001 per 1,000 rows read and $1.00 per million rows written, meaning KV wins for high-read/low-write workloads but D1 can be more economical for complex queries that avoid full table scans."
  - question: "when should I use cloudflare D1 sqlite instead of KV for my saas app"
    answer: "Use D1 when your application needs SQL queries, joins, indexes, or ACID transactions — things KV simply cannot do. If you're storing relational data or need to filter and sort records, D1's SQLite support makes it the right architectural fit despite the row-based pricing model."
  - question: "cloudflare workers kv vs d1 sqlite cost comparison small saas 2025 free tier limits"
    answer: "Both products offer generous free tiers that most early-stage SaaS products won't exhaust for months. D1 includes 5GB of free storage on the paid Workers plan, and both KV and D1 have free read/write allowances that cover typical low-traffic workloads before any charges kick in."
  - question: "does cloudflare D1 get expensive if queries scan too many rows"
    answer: "Yes, D1's pricing is based on rows read rather than requests, so a single query scanning 50,000 rows costs significantly more than 50,000 individual KV reads. Proper indexing is critical with D1 to keep row scan counts low and prevent unexpected bills at scale."
  - question: "cloudflare KV write costs too high saas alternative options"
    answer: "If your SaaS writes frequently — such as updating user activity timestamps on every request — KV's $5 per million writes can add up quickly and become prohibitively expensive. In high-write scenarios, D1 or restructuring your writes to batch updates may offer better cost efficiency depending on your total row write volume."
---

Most small SaaS founders pick between Cloudflare KV and D1 SQLite based on instinct, not numbers. That instinct shows up on your bill later.

The KV vs D1 cost question has gotten significantly more relevant now that D1 has exited beta and teams are running real production workloads on it. Both products live inside the Workers ecosystem, both have generous free tiers, and both solve "I need data persistence at the edge" — but they solve it differently, and the cost curves diverge fast depending on your access patterns.

**The short version:** KV is a globally-replicated key-value store built for high-read, low-write workloads. D1 is a full SQLite database running at Cloudflare's edge with SQL query support. Picking the wrong one for your read/write ratio can mean paying 3–10x more at scale.

Three things worth understanding before you commit:

1. KV pricing is read-heavy friendly — writes are cheap in isolation but add up fast.
2. D1 pricing is based on rows read/written, not requests. A single query scanning 50k rows costs more than 50k individual KV reads.
3. Free tier limits are generous enough that most early-stage SaaS products won't pay anything for months.

---

## How These Two Products Ended Up Competing

Cloudflare Workers KV launched in 2018 as a globally-distributed key-value store. The pitch was simple: cache configuration, store user sessions, persist feature flags — anything where eventual consistency is acceptable and read throughput matters. By 2024 it had become the default persistence layer for Workers-based applications.

D1 entered public beta in late 2022 and went generally available in 2024. It's SQLite running on Cloudflare's infrastructure, queryable via Workers bindings using standard SQL. That's a meaningful shift. You're not just storing strings by key anymore — you're running `SELECT ... WHERE ... JOIN` queries with indexes, foreign keys, and ACID transactions.

The architectural difference matters for pricing. KV charges per operation. D1 charges per row read and per row written, plus storage. According to Cloudflare's official Workers pricing page, KV on the paid Workers plan costs $0.50 per million reads and $5.00 per million writes. D1 on the paid plan costs $0.001 per 1,000 rows read and $1.00 per 1,000,000 rows written, with storage at $0.75/GB-month beyond the free 5GB.

That structure creates very different economics depending on what your SaaS actually does.

---

## KV's Pricing Favors Session-Heavy, Config-Heavy Workloads

KV rewards you for doing one thing billions of times. Reading a user's session token? One KV read, one flat charge. Reading a feature flag on every request? Still one read per request, predictable cost. At 10 million reads per month on the paid plan, you're paying $5. Genuinely cheap.

But write costs bite. At $5 per million writes, a SaaS that writes frequently — say, updating a user's `last_seen` timestamp on every request — hits real costs fast. One million write operations per day across your user base is $150/month in KV writes alone. That's before any other Workers costs.

KV also isn't a database. No queries. No filtering. No "give me all users who signed up this week." You store a value, you retrieve it by key. That constraint isn't a bug for certain use cases — it's the reason KV can be globally consistent within ~60ms — but it rules out most relational data models.

This approach can fail when teams start shoehorning relational data into KV by maintaining manual secondary indexes as separate key entries. That pattern doubles write costs and creates application complexity that compounds over time.

---

## D1 Costs Scale With Query Efficiency, Not Request Volume

D1 pricing punishes inefficient queries in a way KV never can. A full table scan on a 100,000-row users table reads 100,000 rows. On the paid plan, that's $0.0001. Trivial at one query. Run it 10,000 times per day and you're reading 1 billion rows daily — $100/day.

Add an index on the column you're filtering by, and the same query might read 10 rows instead of 100,000. That's a 10,000x cost reduction from one index. The D1 pricing model makes your schema design decisions a billing decision too.

The flip side: for structured data, D1 is dramatically more capable. A SaaS managing subscriptions, invoices, user roles, and audit logs needs relational queries. Doing that in KV requires storing denormalized data blobs and doing application-side filtering — which is usually both more complex and more expensive.

This isn't always the cleaner path. D1 query performance at the edge is still maturing, and for extremely latency-sensitive reads, KV's global replication model has an architectural edge that SQL queries can't fully close.

---

## Free Tier Realities for Early-Stage Products

Both products have free tiers that are actually usable — not just demo-level.

| Feature | KV Free | D1 Free | KV Paid | D1 Paid |
|---|---|---|---|---|
| Reads | 100K/day | — | $0.50/M | — |
| Rows Read | — | 5M/day | — | $0.001/1K |
| Writes | 1K/day | — | $5.00/M | — |
| Rows Written | — | 100K/day | — | $1.00/M |
| Storage | 1GB | 5GB | $0.50/GB/mo | $0.75/GB/mo |
| Databases | 1 | 500 | Unlimited | Unlimited |

*Source: Cloudflare Workers Pricing page, accessed May 2026*

For a SaaS doing under 5 million D1 row reads per day or under 100K KV reads per day, you're paying nothing. Most products in the first 6–12 months don't break those limits. The real cost math only starts mattering around 1,000+ daily active users.

---

## Three Scenarios Worth Walking Through

**Scenario 1 — SaaS with heavy session management, light data queries**

A B2B tool where users authenticate, get a session token, and you look it up on every request. Low write volume, extremely high read volume, no relational queries needed. KV wins cleanly. Session tokens fit the key-value model perfectly, and 10 million daily reads cost $5/month on the paid plan. D1 would technically work but adds SQL overhead you don't need.

*Recommendation: Use KV for sessions. Skip D1 until you need structured queries.*

**Scenario 2 — SaaS with user data, subscriptions, and audit trails**

A multi-tenant product where you need `SELECT * FROM invoices WHERE user_id = ? AND status = 'unpaid'`. KV can't do this without maintaining your own secondary indexes as separate KV entries — which doubles write costs and adds application complexity. D1 handles it natively with proper indexing.

*Recommendation: Start with D1. Design your schema carefully. Every missing index is a billing liability.*

**Scenario 3 — High-volume event ingestion (analytics, logging)**

Writing 500K events per day. KV at $5/million writes means $750/month just for writes at that scale. D1 at $1/million rows written means $15/month for the same volume. D1 is dramatically cheaper for write-heavy workloads, as long as your reads are indexed.

*Recommendation: Use D1 for event storage. Partition data by date to keep table sizes manageable and row-scan costs low.*

---

## What Changes Next

The pattern is clear, even if there's no single universal answer:

> **Key Takeaways**
> - **KV dominates** for high-read, low-write, schema-free workloads — sessions, config, caching
> - **D1 dominates** for structured relational data where SQL queries justify the row-read cost
> - **Free tiers cover most early-stage teams** — cost math becomes real around 1K+ DAU
> - **D1 query efficiency directly controls your bill** — schema design is now a financial decision
> - **Missing indexes aren't just a performance problem** — they're a recurring monthly cost

Over the next 6–12 months, Cloudflare is expected to extend D1's capabilities toward read replicas and larger database limits, based on their public roadmap. That will make D1 more competitive for read-heavy use cases currently owned by KV. Watch the D1 pricing page — any change to the rows-read cost will ripple through a lot of existing cost calculations.

So if you're building a new Workers-based SaaS in 2026, default to D1 for application data and KV for caching and sessions. Map your expected read/write ratios before you commit. Five minutes with a spreadsheet now saves a billing surprise at month six.

---

*What's your current Workers stack? If you're mixing KV and D1 in the same app, how are you drawing the line between them?*

## References

1. [Pricing · Cloudflare Workers docs](https://developers.cloudflare.com/workers/platform/pricing/)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
