---
title: "Supabase Edge Functions Cold Start Latency: Reduce It and How It Compares to Vercel"
date: 2026-05-16T20:27:39+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "supabase", "edge", "functions", "Next.js"]
description: "Supabase Edge Functions cold starts hit 400ms in real use. See how that compares to Vercel and what actually reduces the latency in production."
image: "/images/20260516-supabase-edge-functions-cold-s.webp"
technologies: ["Next.js", "Node.js", "AWS", "Vercel", "Cloudflare"]
faq:
  - question: "supabase edge functions cold start latency reduce vercel comparison real world"
    answer: "In real-world usage, Supabase Edge Functions typically experience cold starts between 150ms and 600ms depending on bundle size and region, while Vercel Edge Functions generally stay under 100ms due to aggressive pre-warming across a denser global PoP network. You can reduce Supabase cold start latency by minimizing bundle size, optimizing imports, and pinning your function region close to your database. Neither platform fully eliminates cold starts, but the performance gap narrows significantly once functions receive consistent traffic."
  - question: "how to reduce supabase edge functions cold start time"
    answer: "The biggest lever for reducing Supabase Edge Function cold start latency is bundle size — every unnecessary import adds initialization overhead that delays execution. Additional strategies include selecting function regions geographically close to your Supabase database and optimizing how imports are structured within your Deno-based function. These changes can bring cold starts closer to the lower end of the 150–600ms range without requiring a platform switch."
  - question: "supabase vs vercel edge functions cold start latency comparison"
    answer: "In a real world supabase edge functions cold start latency reduce vercel comparison, Vercel holds a meaningful advantage with sub-100ms cold starts driven by V8 isolate pre-warming across its global network, compared to Supabase's typical 150–600ms range. Both platforms use Deno or V8-based isolate infrastructure, but Vercel's denser point-of-presence network and pre-warming strategy give it a consistent speed edge. For teams already invested in Supabase, region pinning and bundle optimization can close much of this gap in practice."
  - question: "why are my supabase edge functions slow during off-peak hours"
    answer: "Slowdowns during off-peak hours are a classic cold start symptom — when a function hasn't been invoked recently, the runtime isolate is no longer warm and must reinitialize before serving the request. On Supabase Edge Functions, this can add anywhere from 150ms to 600ms of latency, which is noticeable in latency-sensitive features like real-time chat or live UI updates. Reducing your function's bundle size and keeping traffic consistent are the most effective ways to minimize this behavior."
  - question: "do vercel edge functions have cold starts like supabase"
    answer: "Yes, Vercel Edge Functions do experience cold starts, but they are generally shorter than Supabase's — typically under 100ms — because Vercel pre-warms isolates across a large global network of points of presence. Supabase Edge Functions, which run on Deno Deploy infrastructure, can take 150–600ms to cold start depending on function size and regional proximity. Both platforms see cold start times decrease significantly once a function is receiving regular traffic."
---

Cold start latency killed a real-time feature at a company running Supabase Edge Functions. Their function was waking up in 400ms during off-peak hours — slow enough to visibly lag a chat UI. That number is fixable. But the fix depends entirely on understanding *why* edge functions cold-start the way they do, and how that compares to Vercel's approach.

This piece breaks down the real-world performance picture for Supabase Edge Function cold start latency, how to reduce it, and what the Vercel comparison actually looks like when you move past marketing benchmarks.

**In brief:** Supabase Edge Functions and Vercel Edge Functions share Deno-based infrastructure but diverge sharply on cold start behavior, global distribution strategy, and the optimization controls available to developers.

1. Supabase Edge Functions run on Deno Deploy infrastructure, with cold starts typically ranging from 150ms to 600ms depending on bundle size and regional proximity, according to Supabase's own architecture documentation.
2. Vercel Edge Functions — running on their V8 isolate network — generally report cold starts under 100ms, partly because of aggressive pre-warming across their global PoP network.
3. Reducing cold start latency on Supabase Edge Functions is achievable through bundle size reduction, strategic region selection, and import optimization, without switching platforms.

> **Key Takeaways**
> - Supabase Edge Functions deploy via Deno Deploy and execute at the edge closest to the user, but cold start latency varies significantly (150–600ms) based on function weight and geographic distribution.
> - Vercel Edge Functions use V8 isolates with sub-100ms cold starts in most regions, primarily because of their denser global PoP network and isolate pre-warming.
> - Bundle size is the single biggest driver of cold start time — every unnecessary import adds initialization overhead.
> - For Supabase users, pinning function regions close to your database reduces the cold start *and* eliminates round-trip latency simultaneously.
> - Neither platform eliminates cold starts entirely; the gap narrows considerably once functions receive consistent traffic.

---

## Why Edge Cold Starts Are Still a Problem in 2026

Serverless functions have been mainstream since AWS Lambda launched in 2014. But the shift to *edge* serverless — functions running at CDN nodes rather than centralized data centers — introduced a new cold start calculus.

Classic Lambda cold starts were painful but predictable: 200ms–2s for Node.js, manageable with provisioned concurrency. Edge functions promised to solve this by running closer to users with lighter runtimes. Deno's V8-based isolate model (used by both Supabase and Cloudflare Workers) boots faster than Node.js containers — no full OS spin-up required.

Supabase Edge Functions launched for general availability in 2022 and run on Deno Deploy infrastructure. Per Supabase's architecture documentation, each function executes in a Deno isolate at the edge region, with the function code fetched and compiled on first invocation if not recently active.

Vercel Edge Functions, also Deno-based under the hood, launched their edge runtime around the same period and now run across a network of 100+ global PoPs — more than double Supabase's current regional footprint.

In 2026, both platforms have matured significantly. But the cold start gap remains real, particularly for low-traffic functions that don't benefit from warm isolate reuse. With real-time applications, auth middleware, and API routes increasingly moved to the edge, that gap directly impacts user experience.

---

## What's Actually Causing the Cold Start

The cold start on a Supabase Edge Function breaks into three phases:

1. **Isolate initialization** — spinning up the Deno V8 isolate (~10–50ms, relatively fixed)
2. **Code fetch and compile** — loading your function bundle from storage and JIT-compiling it
3. **Module import resolution** — executing top-level `import` statements

Phase 3 is where most developers lose time without realizing it. A function that imports the entire Supabase client library plus a third-party JWT library plus an ORM can easily push 300ms of startup overhead just from module resolution. According to Supabase's architecture docs, the function worker is re-used across requests when warm — so the cold start only hits the *first* request to a newly allocated isolate.

The practical implication: functions with heavy imports serving low-traffic routes will cold-start on nearly every request during off-peak hours. This isn't a platform defect. It's a predictable consequence of how isolate reuse works, and it responds directly to code-level changes.

---

## How to Actually Reduce Cold Start Latency on Supabase

Three approaches that move the needle:

**Minimize bundle size.** Import only what you use. Instead of `import { createClient } from '@supabase/supabase-js'`, pull in specific sub-modules where the package supports it. This alone can cut module resolution time by 40–60%, according to community benchmarks shared in Supabase's GitHub discussions (the 2025 edge function performance thread is worth reading in full).

**Pin your function region.** Supabase lets you specify the deployment region for edge functions. If your database lives in `us-east-1`, deploying your function to `us-east-1` eliminates cross-region database latency *and* keeps your cold start in the same region as your data. Two problems, one setting.

**Use top-level await carefully.** Any async operation at module scope — like establishing a connection or fetching a secret — blocks the entire cold start. Move these into the handler body, or use lazy initialization patterns with a module-level cached variable. It's a small structural change that consistently shaves meaningful time off initialization.

This approach can fail when your function genuinely needs heavy dependencies at startup. Some workloads — ML inference wrappers, complex auth chains — can't be trimmed without rearchitecting the function itself. In those cases, synthetic warm-up pings (a scheduled cron hitting the function every few minutes) are crude but effective.

---

## The Vercel Comparison: Real Numbers, Not Marketing

| Metric | Supabase Edge Functions | Vercel Edge Functions |
|---|---|---|
| Runtime | Deno (V8 isolate) | V8 isolate (Edge Runtime) |
| Cold start (typical) | 150–600ms | 50–100ms |
| Global PoPs | ~30 regions | 100+ PoPs |
| Pre-warming | Not documented as default | Yes (network-level) |
| Bundle size limit | 2MB (compressed) | 1MB |
| Database proximity control | Yes (region pinning) | Limited (depends on Postgres provider) |
| Pricing model | Included in Supabase plan | Usage-based |
| Best for | Supabase-native stacks | Next.js / Vercel-hosted apps |

The cold start gap is real. Vercel's denser PoP network means a warm isolate is statistically more likely to be available when a request arrives. But "50ms vs 300ms" becomes less meaningful once your function handles consistent traffic — both platforms reuse warm isolates aggressively, and the gap collapses under load.

Where Vercel genuinely wins: global median latency for cold starts, purely from infrastructure density. Where Supabase wins: database proximity. A Supabase Edge Function pinned to the same region as your Postgres instance adds roughly zero network overhead for DB queries. A Vercel function calling a Supabase database across regions can add 80–150ms *per query*. At two queries per request, the math flips entirely in Supabase's favor — even accounting for the longer cold start.

---

## Choosing by Workload Type

**Auth middleware running on every request.** Vercel wins. Middleware runs before every page load, so cold starts happen less often under high traffic, and Vercel's edge network delivers lower p99 latency globally. If you're on Next.js, this is the natural fit and switching doesn't make sense.

**Database-heavy API routes on a Supabase stack.** Supabase Edge Functions, region-pinned to your DB, win. Even if the cold start is 200ms, you're saving 100–150ms per DB query compared to a Vercel function reaching across regions. The net latency is lower, and the operational simplicity of staying within one platform is worth something too.

**Low-traffic background functions — webhooks, cron-triggered jobs.** Cold starts hurt most here. For Supabase, the mitigation is synthetic warm-up pings. Vercel's pre-warming reduces this problem on their side, though it's not fully documented as a configurable feature. Neither solution is elegant. Both work.

One variable to watch: Supabase has been expanding its edge infrastructure, with new regions added through 2025. A denser PoP footprint would close the cold start gap with Vercel significantly. The Supabase changelog is the right place to track this — it's the single factor most likely to shift the comparison over the next 12 months.

---

## Where This Is Headed

The cold start debate comes down to this: Vercel has better raw cold start numbers from infrastructure density; Supabase has a structural advantage for database-proximate workloads.

Cold start on Supabase Edge Functions is primarily a bundle size and import strategy problem, not a platform ceiling. Vercel's sub-100ms cold starts reflect PoP density — match the traffic pattern and Supabase's gap shrinks. Region pinning on Supabase is underused and often worth more latency savings than any amount of code optimization.

Over the next 6–12 months, expect Supabase to expand its global edge footprint. If they close from ~30 to 60+ regions, the Vercel cold start advantage narrows to negligible for most use cases. Both platforms are investing in isolate pre-warming, which means the cold start problem may become largely moot for anything but the most latency-critical, lowest-traffic functions.

The gap exists. It's quantifiable. And for most Supabase-native stacks, it's either solvable at the code level or irrelevant once you account for database round-trip savings.

What's your current cold start profile on Supabase Edge Functions — and have region pinning or bundle optimization moved the number for you? Drop the data in the comments.

## References

1. [Edge Functions Architecture | Supabase Docs](https://supabase.com/docs/guides/functions/architecture)
2. [Edge Functions vs Serverless vs Containers — A Cost and Performance Shootout | CODERCOPS](https://www.codercops.com/blog/edge-functions-vs-serverless-vs-containers)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
