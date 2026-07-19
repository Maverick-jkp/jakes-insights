---
title: "Supabase Edge Functions Cold Start Latency vs Vercel Serverless"
date: 2026-05-13T21:22:00+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "supabase", "edge", "functions", "TypeScript"]
description: "61% of orgs run serverless in 2025. See real cold start latency measurements for Supabase Edge Functions vs Vercel serverless before you commit."
image: "/images/20260513-supabase-edge-functions-cold-s.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "AWS", "GraphQL"]
faq:
  - question: "Supabase edge functions cold start latency vs Vercel serverless real measurement 2025 which is faster"
    answer: "Based on real 2025 measurements, Supabase Edge Functions produce cold starts in the 5–50ms range due to their V8 isolate architecture on Deno Deploy, while Vercel standard serverless functions on Node.js range from 100ms to 800ms depending on bundle size and region. However, Vercel's Edge Runtime (a separate product using V8 isolates) narrows the gap significantly with sub-25ms cold starts."
  - question: "why are Vercel serverless functions slower cold start than Supabase edge functions"
    answer: "Vercel's standard serverless functions run on AWS Lambda, which requires container provisioning, JIT compilation, and module loading — all of which add latency during cold starts. Supabase Edge Functions use Deno Deploy's V8 isolate model, where isolates share a single process and spin up in microseconds rather than the seconds needed to cold-boot a full container."
  - question: "does Vercel have edge functions with low cold start latency like Supabase"
    answer: "Yes, Vercel offers an Edge Runtime that is separate from its standard serverless functions and also uses V8 isolates, achieving cold starts closer to sub-25ms. This is a common source of confusion in platform comparisons, as Vercel actually ships two distinct execution models with very different cold start characteristics."
  - question: "Supabase edge functions cold start latency vs Vercel serverless real measurement 2025 which should I use for my app"
    answer: "The right choice depends on your specific bottleneck — whether that's compute latency, database proximity, or ecosystem integration rather than raw cold start numbers alone. For teams already using Supabase's Postgres database, co-locating logic in Edge Functions can reduce total round-trip latency by 30–60ms per request by eliminating an extra network hop."
  - question: "what is a realistic cold start time for Vercel serverless functions in 2025"
    answer: "Independent 2024 benchmark data from Measured.dev shows Vercel serverless functions on Node.js runtimes experiencing cold starts ranging from 100ms to 800ms, with the wide range depending on bundle size, deployment region, and runtime version. Vercel's newer Edge Runtime is a separate option that performs significantly better, achieving sub-25ms cold starts using V8 isolate technology."
aliases:
  - "/tech/2026-05-13-supabase-edge-functions-cold-start-latency-vs-verc/"

---

Cold starts used to be a footnote in serverless discussions. Now they're a billing line item and a user experience problem rolled into one.

According to the CNCF's 2024 Annual Survey, over 61% of organizations run at least one workload on serverless or edge compute infrastructure. Both Supabase Edge Functions and Vercel's serverless platform are front-runners in that shift. But they're built on fundamentally different execution models — and when it comes to cold start latency, the architectural difference matters more than the marketing copy.

Cold start latency isn't a single number you can look up on a docs page. It's a product of runtime, region, payload, and execution model. Once you understand those variables, the right platform choice becomes much clearer.

> **Key Takeaways**
> - Supabase Edge Functions run on Deno Deploy's V8 isolate model, producing cold starts in the **5–50ms range** — significantly lower than traditional Node.js Lambda cold starts.
> - Vercel serverless functions on Node.js runtimes show cold starts ranging from **100ms to 800ms** depending on bundle size, region, and runtime version, per independent 2024 benchmark data from Measured.dev.
> - Vercel's Edge Runtime — separate from its standard serverless functions — also uses V8 isolates and achieves cold starts closer to **sub-25ms**, narrowing the gap with Supabase considerably.
> - The right choice depends on whether your bottleneck is compute latency, database proximity, or ecosystem integration — not raw cold start numbers alone.
> - For teams already on Supabase's Postgres stack, co-locating logic in Edge Functions can cut total round-trip latency by 30–60ms per request by eliminating an extra network hop.

---

## Two Platforms, Two Different Origins

Vercel launched serverless functions around 2019 as a natural extension of its frontend deployment platform. The mental model was simple: deploy a Next.js app, get API routes as Lambda-backed serverless functions automatically. Under the hood, Vercel runs on AWS Lambda — which means it inherits Lambda's cold start characteristics: JIT compilation overhead, module loading time, and container provisioning latency.

Supabase Edge Functions arrived later, reaching general availability in 2022, built on top of Deno Deploy. The architecture choice was deliberate. Deno uses V8 isolates rather than full containers. Isolates share a single process, which means spin-up time is measured in microseconds for the V8 context itself — not the seconds required to cold-boot a container.

By 2025, Vercel introduced its own Edge Runtime — also V8 isolate-based — as a distinct option alongside traditional serverless functions. Vercel now ships *two* execution models. Conflating them is the most common mistake in platform comparisons.

The market context: Vercel's 2024 revenue reportedly crossed $250M ARR per Sacra's market analysis, while Supabase raised at a $2B valuation in its 2024 Series D. Both platforms have serious infrastructure investment behind them — which is why the performance comparison is genuinely close in some dimensions and miles apart in others.

---

## Cold Start Mechanics: Isolates vs. Containers

The core difference comes down to what has to happen before your first line of code runs.

Traditional serverless functions — Vercel's Node.js functions, AWS Lambda — require spinning up a container, loading the Node.js runtime, then executing module imports. A minimal Node.js 20 function on Vercel with no external dependencies cold-starts in roughly **150–250ms** in `us-east-1`, based on Measured.dev's 2024 benchmark dataset. Add a database client like `pg` or Prisma, and that number climbs to **400–700ms** before a single query runs.

Supabase Edge Functions run on Deno's V8 isolate model. An isolate doesn't need to bootstrap a full runtime — it's already running inside a shared Deno process. According to Supabase's architecture documentation, isolate boot time typically sits in the **single-digit milliseconds** range for the V8 context. Real-world cold starts, including function-specific module loading, land in the **5–50ms** window for typical functions.

Vercel's Edge Runtime changes this picture. For functions deployed to `edge` runtime in `next.config.js`, Vercel also uses V8 isolates. Cold starts here are competitive with Supabase: independent tests by the Upstash team in Q4 2024 showed Vercel Edge Runtime cold starts averaging **18–30ms** across multiple regions.

So the real comparison is actually three-way:

| Metric | Supabase Edge Functions | Vercel Serverless (Node.js) | Vercel Edge Runtime |
|---|---|---|---|
| **Cold Start Range** | 5–50ms | 100–800ms | 15–40ms |
| **Runtime** | Deno (V8 isolate) | Node.js 18/20 (container) | V8 isolate |
| **Max Bundle Size** | 20MB (compressed) | 250MB (unzipped) | 4MB |
| **NPM Package Support** | Limited (ESM via CDN) | Full Node.js ecosystem | Limited (Web APIs only) |
| **Database Proximity** | Co-located with Supabase Postgres | External connection required | External connection required |
| **Global Regions** | ~25 (Deno Deploy network) | ~35+ (Vercel's network) | ~35+ (Vercel's network) |
| **TypeScript Support** | Native (Deno) | Via compilation step | Native |
| **Best For** | Supabase-native backends, low-latency data ops | Complex Node.js logic, large dependencies | Simple auth, routing, request transformation |

---

## Where Latency Actually Compounds

Raw cold start numbers are only part of the story. For most applications, the relevant metric is **total first-byte latency** — cold start plus network plus database query time.

This is where Supabase Edge Functions have a structural advantage that no Vercel configuration can replicate. When your function runs on Deno Deploy and your database is a Supabase Postgres instance, they're co-located in the same data center. According to Supabase's architecture docs, this can reduce database query latency to under 1ms for the network portion.

Run the same query from a Vercel serverless function in `us-east-1` connecting to a Supabase Postgres instance in `us-east-1` and you're adding ~5–15ms per query in ideal conditions — and up to 50ms+ if your database is in a different region. At 10 queries per request, that's a 50–500ms penalty on every cold-start cycle.

Vercel partially addresses this with its Postgres product (which uses Neon under the hood), but that still doesn't achieve the same physical proximity as native Supabase edge-to-database co-location.

---

## The NPM Dependency Tax

One underreported factor in cold start benchmarks: dependency weight.

Vercel's Node.js functions support the full NPM ecosystem. That sounds like a win. But every `require()` at cold start adds initialization time. Prisma's client alone adds ~200ms to cold start latency in Lambda environments, per Prisma's own 2023 performance documentation. Large ORMs, AWS SDKs, and GraphQL servers compound this fast.

Supabase Edge Functions run on Deno, which imports modules via URL (ESM). There's no `node_modules` directory to load. The trade-off is real: you can't use most Node.js-specific packages. But for teams willing to work within that constraint, the cold start floor stays low regardless of how many ES modules you import — because Deno caches and pre-compiles them on the isolate host.

Vercel's Edge Runtime faces the same constraint: 4MB bundle limit, no native Node.js modules. Both isolate-based options trade ecosystem breadth for cold start consistency. That's not a bug — it's the architectural bargain you're accepting.

---

## Practical Guidance

**Building Supabase-native?** Keep compute logic in Edge Functions. The database proximity advantage alone justifies the Deno constraint for data-heavy operations. A function running 5 Postgres queries saves 25–75ms in network overhead per request compared to the same database call from Vercel. Over millions of requests, that's measurable infrastructure cost reduction.

**On Vercel with a non-Supabase backend?** Migrate latency-sensitive routes — auth checks, session validation, lightweight middleware — to Vercel's Edge Runtime rather than standard serverless functions. The cold start difference between Node.js and Edge Runtime is often **5–10x** for simple logic with no heavy dependencies. That's the difference between 600ms and 25ms.

**Evaluating both platforms fresh?** The database decision drives the compute decision. Choose your data layer first. Supabase's Postgres plus Edge Functions stack is coherent and fast. Vercel's Edge Runtime plus Neon Postgres is a reasonable alternative but involves more configuration to achieve similar proximity.

**This approach can fail when** your application genuinely requires heavy NPM packages — complex ORMs, binary dependencies, large SDK bundles. In those cases, isolate-based runtimes hit hard limits, and Vercel's Node.js functions with careful bundle optimization may be the more practical path, cold start penalty included.

---

## What Changes Through 2026

Supabase has signaled expanded regional coverage for Edge Functions. Closing the region count gap with Vercel — currently ~25 vs ~35+ — would remove the last meaningful network argument for Vercel in global deployments.

Vercel's recent partnership announcements suggest deeper integration with non-AWS infrastructure. If they move more regions off Lambda to custom isolate infrastructure, their Node.js cold start problem could shrink significantly.

Deno Deploy's module caching improvements (v1.40+ introduced persistent module caches) are already reducing warm-start variance. Watch for this to show up in third-party benchmarks as the feature matures.

---

## The Bottom Line

The story here has a clear answer once you separate Vercel's two execution modes. Supabase Edge Functions and Vercel Edge Runtime are roughly competitive on raw cold start latency — both in the 5–50ms range. Vercel's standard Node.js serverless functions are a different category entirely, with cold starts 5–20x higher under real conditions.

V8 isolates beat containers on cold start. Full stop. The runtime model determines your floor. Database proximity matters as much as compute latency — and Supabase wins on co-location by default. NPM dependency weight is the hidden multiplier that turns theoretical 200ms cold starts into 700ms real-world ones. And Vercel Edge Runtime remains the most underused option on that platform — most teams default to Node.js serverless functions without checking whether their use case fits the Edge Runtime's constraints.

Both platforms will narrow gaps over the next 12 months. But the architectural decision between isolates and containers isn't going away.

If your current serverless architecture measures cold starts in hundreds of milliseconds, the honest question is whether that's a platform ceiling — or just a default configuration that nobody has reconsidered lately.

---

*References: Supabase Edge Functions Architecture (supabase.com/docs), Measured.dev 2024 Cold Start Benchmarks, CNCF Annual Survey 2024, Sacra Market Analysis Q4 2024, Upstash Edge Runtime Performance Tests Q4 2024, Prisma Performance Documentation 2023.*

## References

1. [Edge Functions Architecture | Supabase Docs](https://supabase.com/docs/guides/functions/architecture)
2. [Edge Functions vs Serverless vs Containers — A Cost and Performance Shootout | CODERCOPS](https://www.codercops.com/blog/edge-functions-vs-serverless-vs-containers)
3. [Vercel vs Supabase (2026): Features, Pricing, and Key Differences | UI Bakery Blog](https://uibakery.io/blog/vercel-vs-supabase)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
