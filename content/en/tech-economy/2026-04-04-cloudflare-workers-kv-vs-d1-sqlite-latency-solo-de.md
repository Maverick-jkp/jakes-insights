---
title: "Cloudflare Workers KV vs D1 SQLite: Cost Breakdown for Solo Devs"
date: 2026-04-04T19:55:02+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "cloudflare", "workers", "sqlite", "AWS"]
description: "KV vs D1 on Cloudflare Workers: see real latency differences and cost breakdowns before your side project outgrows the free tier."
image: "/images/20260404-cloudflare-workers-kv-vs-d1-sq.webp"
technologies: ["AWS", "Go", "Cloudflare"]
faq:
  - question: "cloudflare workers kv vs d1 sqlite latency solo developer side project cost breakdown which is cheaper"
    answer: "For solo developers on the free tier, D1 SQLite offers 5 million row reads per day compared to KV's 100,000 reads per day, making D1 significantly more generous for relational data workloads. However, KV is cheaper for simple key-value lookups with high cache hit rates since warm edge reads complete in single-digit milliseconds with minimal compute cost."
  - question: "how fast is cloudflare KV vs D1 read latency"
    answer: "Cloudflare KV cached reads typically resolve in under 10ms globally via edge caching, but uncached reads from central storage can hit 40–100ms depending on your region. D1 SQLite queries route to a regional data center rather than every edge node, resulting in consistent but generally higher per-query latency compared to a warm KV read."
  - question: "should I use cloudflare KV or D1 for my side project"
    answer: "The decision depends on your data structure and read pattern: use KV for simple cached lookups like config flags, session tokens, or static content, and use D1 when you need relational data, SQL joins, or strong consistency. For most solo developer side projects with structured data and low-to-moderate traffic, D1's generous free tier row read allowance makes it the better default choice."
  - question: "cloudflare workers kv vs d1 sqlite latency solo developer side project cost breakdown free tier limits 2024"
    answer: "As of 2026, Cloudflare's free tier gives KV 100,000 reads per day and D1 5 million row reads per day, which heavily favors D1 for data-heavy side projects with relational queries. KV's free tier makes more sense when your access pattern relies on frequently repeated lookups for the same keys, keeping the cache hit rate high and costs low."
  - question: "is cloudflare D1 eventually consistent like KV"
    answer: "No, Cloudflare D1 provides strongly consistent reads, which is a key difference from KV's eventual consistency model. KV achieves its global speed by caching reads at edge nodes, which means writes can take time to propagate, whereas D1 executes SQL queries at a regional data center ensuring data is always up to date."
aliases:
  - "/tech/2026-04-04-cloudflare-workers-kv-vs-d1-sqlite-latency-solo-de/"

---

Picking the wrong storage layer on a Cloudflare Workers project doesn't just hurt performance. It quietly drains your free tier, then your wallet, once traffic picks up. KV and D1 solve genuinely different problems—and most solo developers conflate them because both live inside the Workers ecosystem.

> **Key Takeaways**
> - Cloudflare KV reads are eventually consistent and typically resolve in under 10ms globally via edge cache, but uncached reads from central storage can hit 50–100ms depending on region.
> - Cloudflare D1 (SQLite at the edge) delivers strongly consistent reads with full SQL support, but each query costs more compute time and doesn't benefit from edge caching the same way KV does.
> - On the Workers free tier as of April 2026, KV gives 100,000 reads/day and D1 gives 5 million row reads/day — these numbers favor very different usage patterns.
> - For solo side projects with relational data and low-to-moderate traffic, D1's generous row read allowance makes it the better default despite higher per-query latency.
> - The KV vs D1 decision ultimately depends on your read pattern: cached lookups go to KV, SQL queries with joins go to D1.

---

## Background: Why This Choice Matters More in 2026

Cloudflare Workers became a credible full-stack runtime when D1 exited beta in late 2023 and hit general availability in 2024. Before D1, the KV store was the only native persistence option — a globally distributed key-value cache with eventual consistency baked in. It worked fine for config flags, session tokens, and static content. Relational data? You'd bolt on an external Postgres instance and eat the cold-start latency.

D1 changed the calculus. It runs SQLite at Cloudflare's data centers, not at every edge node globally like KV. That distinction is frequently misunderstood. KV caches reads geographically; D1 executes queries at a regional data center close to your account's home region. Both are fast. They're just fast in different ways.

For solo developers building side projects on a tight budget in 2026, the choice comes down to three factors: data structure, read pattern, and free tier math. Cloudflare's pricing page (as of April 2026) draws a clear line between the two products — and that line maps directly onto architectural decisions you'll feel six months into production.

---

## Latency Reality: What the Numbers Actually Show

KV's edge cache is the fastest read you can get on Workers. When a key is warm — meaning it's been requested recently from that edge location — reads typically complete in single-digit milliseconds. Cloudflare's own documentation acknowledges that uncached KV reads route to a central store, which adds latency. Community benchmarks published on the Cloudflare Discord and the Workers developer forum in Q1 2026 show uncached KV reads from distant regions regularly hitting 40–80ms round trips.

D1 query latency sits in a different bucket entirely. Cloudflare routes D1 queries to the nearest data center running your SQLite instance. According to Cloudflare's D1 documentation, simple SELECT statements average 1–5ms at the data center level — but network overhead from edge to data center adds another 10–30ms for users not geographically close to your D1 region.

The practical delta: a warm KV read beats a D1 query. A cold KV read is often comparable to or slower than D1. For a side project where most reads are unique — user profile lookups, per-user settings — KV's cache advantage largely disappears. You're paying the penalty without getting the benefit.

---

## Free Tier Math for Solo Projects

This is where the cost breakdown gets concrete. According to Cloudflare's official pricing page:

| Metric | KV (Free Tier) | D1 (Free Tier) |
|---|---|---|
| Reads per day | 100,000 | 5M row reads |
| Writes per day | 1,000 | 100K row writes |
| Storage | 1 GB | 5 GB |
| Paid overage (reads) | $0.50 / million | $0.001 / million rows |
| Paid overage (writes) | $5.00 / million | $1.00 / million rows |

D1's row read allowance sounds enormous — and it is, for a side project. A to-do app returning 50 rows per user session can handle 100,000 sessions per day before touching paid territory. KV at 100,000 reads/day sounds comparable on paper, but each KV read is one key. If your app fetches 10 KV keys per request — common when you're pulling feature flags, user config, and session data simultaneously — you're burning through 10,000 requests per day in 1,000 actual user sessions.

D1 wins the free tier math for most solo CRUD applications. It's not particularly close.

---

## When KV Still Makes Sense

KV isn't obsolete. It's the right call in specific scenarios:

**Configuration and feature flags.** One KV key, thousands of reads, consistent across a deploy. KV's edge caching means sub-5ms reads globally with no SQL overhead.

**Rate limiting counters.** KV's atomic `put` with TTL handles expiring counters cleanly. D1 transactions add unnecessary overhead for something this structurally simple.

**Static content with short TTL.** API responses you want to cache with controlled expiry. KV's TTL support is cleaner than rolling your own cache on D1.

This approach can fail when developers reach for KV as their primary data store and end up serializing relational data into key-value blobs. The update logic becomes a maintenance problem fast. For a solo developer running a SaaS side project — user accounts, subscription state, content rows — D1's SQL joins and relational integrity eliminate an entire class of application-level data management code that KV forces you to write yourself.

---

## Three Scenarios That Clarify the Decision

**Scenario 1 — Personal portfolio with a contact form and blog CMS.** Traffic is low and unpredictable. Data is relational: posts, tags, authors. D1 is the correct choice. The 5 GB free storage and 5M row reads handle any realistic personal site. KV would require serializing all blog data into key-value blobs, which creates messy update logic and no meaningful latency advantage.

**Scenario 2 — A side project with a public API serving cached responses.** If the same 20 responses answer 80% of requests — think public leaderboard or trending content feed — KV's edge cache cuts global latency dramatically. Cache the D1 query result into KV with a 60-second TTL. Use both. They're not mutually exclusive, and this pattern is where each tool does exactly what it was designed for.

**Scenario 3 — An auth-heavy app with session tokens.** Session data is ephemeral, key-shaped, and high-read. KV with a TTL is exactly right here. Don't put sessions in D1 — you'll waste row reads on data that's structurally a cache, not a record.

The pattern that emerges across all three: D1 as your primary store, KV as your cache and ephemeral data layer. That combination covers the overwhelming majority of solo side project architectures without requiring you to over-engineer anything upfront.

---

## What's Coming and Why It Changes This Analysis

The next 6–12 months matter for this decision. Cloudflare is actively expanding D1's regional coverage, which will close the latency gap with KV for uncached reads. The Workers team signaled in their Q4 2025 roadmap post that D1 read replicas are on the way — and when they ship, D1 latency moves into KV territory for read-heavy workloads. At that point, the remaining advantages of KV narrow to edge-cached hot keys and ephemeral data patterns.

So the practical action today:

- **KV wins** on cached read speed and ephemeral data — sessions, flags, rate limits.
- **D1 wins** on free tier generosity for relational CRUD apps and data integrity.
- **Use both**: KV as cache layer, D1 as source of truth.
- **Watch for D1 read replicas** — they'll change this analysis materially when they land.

If you're starting a Workers side project today, default to D1. Add KV only when you identify a specific caching or ephemeral data need. KV is the optimization layer you add later, not the architecture you start with. The cost breakdown almost always points the same direction — D1 as your foundation, KV as the targeted tool you reach for when you have a concrete reason.

What does your current Workers stack look like? Drop it in the comments — curious how many solo projects are still KV-only by default.

## References

1. [Pricing · Cloudflare Workers docs](https://developers.cloudflare.com/workers/platform/pricing/)


---

*Photo by [Ales Nesetril](https://unsplash.com/@alesnesetril) on [Unsplash](https://unsplash.com/photos/gray-and-black-laptop-computer-on-surface-Im7lZjxeLhg)*
