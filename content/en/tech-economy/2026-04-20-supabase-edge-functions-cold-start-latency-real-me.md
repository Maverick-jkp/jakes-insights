---
title: "Supabase Edge Functions vs Vercel Edge: Cold Start Latency"
date: 2026-04-20T20:37:24+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-cloud", "supabase", "edge", "functions", "JavaScript"]
description: "Supabase Edge Functions vs Vercel Edge cold start latency tested in 2025. A 400ms p99 spike is real — here's what the measurements actually show."
image: "/images/20260420-supabase-edge-functions-cold-s.webp"
technologies: ["JavaScript", "TypeScript", "Node.js", "REST API", "Vercel"]
faq:
  - question: "supabase edge functions cold start latency real measurement vs vercel edge 2025 which is faster"
    answer: "Based on real-world measurements rather than synthetic benchmarks, Vercel Edge Runtime typically achieves cold starts of 30–120ms while Supabase Edge Functions range from 80–250ms, depending on region and function complexity. Vercel's advantage comes from its stripped-down V8 isolate architecture, which allows aggressive isolate recycling at the cost of a restricted API surface."
  - question: "what causes supabase edge functions to have slower cold starts than vercel"
    answer: "Supabase Edge Functions run on Deno Deploy infrastructure, where Deno's module loading behavior adds startup overhead, especially when functions import large dependency trees. Vercel Edge Runtime enforces a 4MB code size limit and restricts available APIs, which allows it to recycle V8 isolates much faster and reduce cold start times."
  - question: "supabase edge functions cold start latency real measurement vs vercel edge 2025 which should I use for latency sensitive APIs"
    answer: "For latency-sensitive APIs where p99 performance matters, Vercel Edge Runtime is generally faster in cold start scenarios, but only works if your function fits within its constraints — no Node.js built-ins, no native modules, and under 4MB code size. If your function requires broader runtime access like direct database drivers or Deno-specific APIs, Supabase Edge Functions offer more flexibility despite the higher cold start overhead."
  - question: "does vercel edge runtime support node.js modules"
    answer: "No, Vercel Edge Runtime does not support Node.js built-ins or native modules, and enforces a hard 4MB code size limit per function. This restricted API surface is intentional, as it enables faster V8 isolate recycling and lower cold start latency compared to more permissive runtimes like Supabase Edge Functions."
  - question: "how do I accurately measure cold start latency for edge functions in production"
    answer: "Accurate cold start measurement requires real invocation patterns rather than synthetic benchmarks, accounting for variables like geographic region, payload size, and invocation frequency. Community projects like `edge-runtime-benchmarks` on GitHub provide real-world telemetry data, and replicating their methodology — measuring first-invocation latency across multiple regions — gives results closer to actual production p99 numbers."
---

Cold starts aren't a minor inconvenience. For latency-sensitive APIs, a 400ms spike on first invocation can tank your p99 numbers and break SLA commitments.

This piece cuts through the marketing claims. Both Supabase Edge Functions and Vercel Edge Runtime have matured considerably since their early releases — but actual cold start behavior under real measurement conditions tells a different story than their documentation suggests. The gap between benchmark numbers and production reality is where engineering decisions get made.

Four things to cover: the runtime architecture differences that drive cold start behavior, real measurement methodology you should replicate, a direct comparison across key performance dimensions, and which workloads each platform actually suits.

---

**In brief:** Supabase Edge Functions (Deno Deploy-powered) and Vercel Edge Runtime (V8 isolate-based) both aim for sub-100ms cold starts, but real-world measurements show meaningful differences depending on region, payload size, and invocation patterns.

1. Supabase Edge Functions run on Deno Deploy infrastructure — JavaScript/TypeScript with Deno runtime semantics, not Node.js.
2. Vercel Edge Runtime uses V8 isolates with a restricted API surface, enabling extremely fast isolate recycling but limiting what you can do at the edge.
3. Cold start latency under real measurement (not synthetic benchmarks) ranges from 80–250ms for Supabase and 30–120ms for Vercel, depending on geographic region and function complexity, based on community-published telemetry from projects like `edge-runtime-benchmarks` on GitHub (as of Q1 2026).

---

## The Runtime Architectures Are Fundamentally Different

This matters more than most comparisons acknowledge.

Supabase Edge Functions run on [Deno Deploy](https://supabase.com/docs/guides/functions/architecture) infrastructure. Each function executes in a Deno isolate, which means you get full Deno runtime semantics — `Deno.env`, native TypeScript support, and access to Deno's standard library. The trade-off is that Deno's module loading behavior affects cold start time, particularly when functions import large dependency trees.

Vercel Edge Runtime strips the runtime down deliberately. It's a V8 isolate environment with a constrained Web API surface — no Node.js built-ins, no native modules, and a hard 4MB code size limit (per Vercel's official Edge Runtime documentation). That constraint isn't a bug. It's what enables Vercel to recycle isolates aggressively and push cold starts down toward the 30ms range in optimal conditions.

So before you even benchmark these two, the question is: does your function fit inside Vercel's constraints? If you're importing `pg` directly, or relying on Node.js `fs` operations, Vercel Edge Runtime isn't even an option. Supabase Edge Functions give you more headroom — but you'll pay for it in startup overhead.

Deno's architecture initializes a fresh isolate per worker instance, warming it with function code, then handles requests. According to Supabase's own architecture documentation, functions are deployed globally across the Deno Deploy network, but the warm instance pool size per region isn't publicly specified — which makes cold start frequency harder to predict in practice.

---

## How to Actually Measure Cold Start Latency

Synthetic benchmarks are nearly useless here. What you want is **forced cold start measurement** — deliberately invoking a function after a period of inactivity that exceeds the platform's warm instance TTL.

The approach that produces reliable data:

- Deploy a minimal function (a simple JSON response, no external calls)
- Wait 5 minutes after last invocation (both platforms drop warm instances within this window based on observed behavior)
- Fire a request and capture `time_to_first_byte` (TTFB) via `curl -w "%{time_starttransfer}"` or a tool like `k6`
- Repeat 20–30 times across different times of day to account for regional traffic load variance

Community-published results from the `edge-runtime-benchmarks` repository (maintained by contributors tracking Supabase, Vercel, and Cloudflare Workers as of Q1 2026) show:

- **Supabase Edge Functions** cold start TTFB: **80–250ms** (median ~140ms, higher variance in `ap-southeast-1`)
- **Vercel Edge Runtime** cold start TTFB: **30–120ms** (median ~55ms, more consistent globally)

Warm request latency converges — both platforms handle warm requests in the 15–40ms range for trivial functions. Cold starts are where the difference lives.

---

## Side-by-Side Comparison

### Key Performance and Developer Experience Metrics

| Dimension | Supabase Edge Functions | Vercel Edge Runtime |
|---|---|---|
| **Cold start (measured, median)** | ~140ms | ~55ms |
| **Cold start (measured, worst-case)** | ~250ms | ~120ms |
| **Warm request latency** | 15–40ms | 15–35ms |
| **Runtime** | Deno (full) | V8 isolate (restricted) |
| **Max bundle size** | ~2MB compressed | 4MB (hard limit) |
| **Node.js compatibility** | Partial (via compat flags) | No native modules |
| **Supabase DB integration** | Native (same platform) | Via HTTP/REST only |
| **Pricing model** | Included in Supabase plan; usage-based above free tier | Per invocation + GB-hours |
| **Global regions** | ~30+ (Deno Deploy network) | ~18 Edge Network regions |
| **Cold start frequency control** | No warm instance pinning | No warm instance pinning |

The cold start gap — roughly 85ms at median — sounds small until you're building a user-facing API that hits an edge function on every page load. At p99, that gap widens.

### Trade-off Analysis

Vercel's speed advantage comes from its intentional constraints. The restricted API surface means smaller isolates, faster initialization, and more aggressive recycling. If your function fits within those constraints — stateless transformations, auth token validation, A/B test routing — Vercel Edge Runtime delivers consistently lower cold start latency across its global footprint.

Supabase Edge Functions make more sense when your function needs to talk directly to a Supabase Postgres database. The latency between a Supabase Edge Function and its co-located Postgres instance is negligible — often under 5ms within the same region. Running that same database call from a Vercel Edge Function adds a full round-trip over HTTP through the Supabase REST API or `pg` connection (which isn't supported in Edge Runtime anyway, forcing the PostgREST HTTP path).

That architectural coupling is Supabase's strongest argument. The cold start overhead is real, but if your function is doing database work, the co-location benefit can more than compensate.

This approach can fail when your Supabase region doesn't align with your users' geography. A function co-located with a Postgres instance in `us-east-1` still incurs round-trip latency for users in Southeast Asia — and that latency may dwarf any cold start benefit. Region selection matters more than platform choice in those cases.

---

## Practical Implications: Which Workload Goes Where

**Scenario 1: Stateless middleware (auth checks, header manipulation, redirects)**
Cold start frequency is high here because these functions handle every request. Vercel Edge Runtime's ~55ms median cold start and tight performance consistency make it the stronger choice. Supabase Edge Functions' extra 85ms at cold start is harder to justify when the function itself runs in under 5ms warm.

**Scenario 2: API routes that query Supabase Postgres directly**
Deploy on Supabase Edge Functions. The co-location advantage eliminates the database round-trip latency that would otherwise dominate your response time. A Vercel Edge Function doing the same work adds 30–80ms of Supabase REST API overhead per query — easily exceeding any cold start advantage.

**Scenario 3: Background processing triggered by webhooks**
Cold start latency matters less here. Webhook handlers are typically called asynchronously. Both platforms work, but Supabase Edge Functions' fuller Deno runtime makes complex processing logic easier to write without hitting API surface constraints.

**What doesn't work well on either platform:** Functions with heavy initialization logic — large ML model loading, extensive module trees, or complex startup routines — will expose the worst cold start behavior on both. Neither platform offers warm instance pinning, so sporadic traffic patterns will continue producing cold starts regardless of which runtime you choose.

**What to watch:** Both platforms are iterating on warm instance management. Vercel's "Fluid compute" model (announced late 2025, per Vercel's changelog) aims to reduce cold starts further by keeping instances warm on low-traffic deployments. Supabase hasn't announced equivalent changes as of April 2026, but the Deno Deploy team continues improving isolate initialization speed — the gap may narrow by Q3 2026.

---

## Where This Leaves You in 2026

The choice between these two platforms comes down to one primary question: is your function tightly coupled to Supabase data, or is it standalone middleware?

Vercel wins on raw cold start speed. Supabase wins on integrated database workflows. Neither platform lets you pin warm instances, so cold start frequency is a function of your traffic patterns — sporadic traffic means more cold starts, regardless of platform.

> **Key Takeaways**
> - **Measure your own cold starts** — synthetic benchmarks don't reflect your function's actual dependency load or regional traffic variance
> - **Supabase Edge Functions** suit data-heavy, Postgres-connected workloads despite the higher cold start floor; co-location often outweighs the startup penalty
> - **Vercel Edge Runtime** wins for stateless, high-frequency middleware where cold start consistency and a minimal API surface are acceptable constraints
> - The ~85ms median cold start gap closes to near-zero once functions are warm — so traffic volume determines whether this gap matters at all
> - Neither platform solves cold starts for sporadic workloads; architectural patterns like request coalescing matter more than platform selection in low-traffic scenarios

The most expensive engineering decision is picking a platform based on documentation benchmarks rather than production measurement. Run the `curl -w "%{time_starttransfer}"` test yourself, in your target regions, with your actual function code.

Your current cold start distribution in production is the only number worth building around.

## References

1. [Edge Functions Architecture | Supabase Docs](https://supabase.com/docs/guides/functions/architecture)
2. [Supabase vs Vercel](https://getdeploying.com/supabase-vs-vercel)


---

*Photo by [Ales Nesetril](https://unsplash.com/@alesnesetril) on [Unsplash](https://unsplash.com/photos/gray-and-black-laptop-computer-on-surface-Im7lZjxeLhg)*
