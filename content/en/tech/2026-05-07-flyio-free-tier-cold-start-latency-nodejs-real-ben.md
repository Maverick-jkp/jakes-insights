---
title: "Fly.io Free Tier Cold Start Latency: Node.js Real Benchmark"
date: 2026-05-07T21:04:33+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "fly.io", "free", "tier", "JavaScript"]
description: "Fly.io free tier cold starts hit 800ms–3s for sleeping Node.js machines. See real 2025 benchmark data and exactly when latency strikes."
image: "/images/20260507-flyio-free-tier-cold-start-lat.webp"
technologies: ["JavaScript", "TypeScript", "Node.js", "PostgreSQL", "Vercel"]
faq:
  - question: "fly.io free tier cold start latency node.js real benchmark 2025"
    answer: "Based on real benchmark data from 2025, Fly.io free tier cold start latency for Node.js apps ranges from around 900ms at the median (P50) to over 3,200ms in worst-case scenarios (P99). These delays occur because free tier machines auto-suspend after roughly 5 minutes of inactivity and must fully resume before serving a response."
  - question: "how long does fly.io free tier take to wake up from sleep"
    answer: "Fly.io free tier machines typically take between 800ms and 3+ seconds to wake up from suspension, depending on traffic conditions and server load. The default idle timeout is 5 minutes, after which the machine suspends and must reboot the Node.js runtime and execute startup code before handling the next request."
  - question: "how to prevent cold starts on fly.io free tier node.js"
    answer: "You can eliminate cold starts entirely on Fly.io by setting 'min_machines_running = 1' in your fly.toml configuration file, which keeps at least one machine running at all times. However, this continuously consumes compute hours from your free monthly allowance, which can push multi-app setups beyond the free tier limits."
  - question: "fly.io vs render free tier cold start speed comparison 2025"
    answer: "Fly.io free tier cold starts are significantly faster than Render's free tier, which can take 30–50 seconds to spin up a sleeping service. In the fly.io free tier cold start latency node.js real benchmark 2025 data, Fly.io sits in a middle-performance position — slower than a paid always-on plan like Railway's $5/month Hobby tier, but much faster than Render at zero cost."
  - question: "how to reduce node.js cold start time on fly.io"
    answer: "You can reduce Node.js cold start time on Fly.io by keeping your require() dependency chains flat and pre-compiling TypeScript before deployment, which can shave 200–400ms off startup time without any infrastructure changes. These code-level optimizations are especially valuable on free tier shared-CPU-1x machines where compute resources are limited."
---

Cold starts are the silent performance tax every developer pays on free-tier hosting. On Fly.io's free tier, that tax can hit **800ms to 3+ seconds** for a sleeping Node.js machine — and knowing exactly when and why that happens is the difference between a demo that impresses and one that embarrasses.

This is the analysis that most Fly.io tutorials skip.

> **Key Takeaways**
> - Fly.io's free tier machines auto-suspend after roughly 5 minutes of inactivity, producing cold start penalties between 800ms and 3,200ms on Node.js apps in 2025 benchmarks.
> - Setting `min_machines_running = 1` in `fly.toml` eliminates cold starts entirely — but continuously consumes compute hours, pushing multi-app setups outside the free allowance.
> - Compared to Render's free tier (30–50 second spin-up) and Railway's always-on Hobby plan ($5/month), Fly.io occupies a middle-performance, zero-cost position.
> - Keeping `require()` chains flat and pre-compiling TypeScript can shave 200–400ms off cold start time without touching your infrastructure.

---

## Why Fly.io's Free Tier Works the Way It Does

Fly.io restructured its free offering in late 2023 after killing the original always-on free plan. What exists in 2026 is an **allowance model**: every account gets 3 shared-CPU-1x VMs with 256MB RAM at no charge, drawing from a monthly free compute budget — currently 2,340 hours per month for shared-CPU-1x machines, per Fly.io's official pricing page.

The catch is machine suspension. To stay within that budget, Fly.io's default `auto_stop_machines` behavior — set to `"stop"` in new apps — suspends idle machines after a configurable idle timeout. The default is 5 minutes. When the next request arrives, the machine needs to boot, load the Node.js runtime, execute your startup code, and then serve the response.

That sequence is your cold start.

Fly.io's documentation describes this as "fast VM suspend/resume" rather than a container rebuild, which is technically accurate. Fly machines use Firecracker microVMs and can checkpoint state. But "fast" is relative. On a shared-CPU-1x instance — the free tier default — resume latency under real traffic conditions is not the sub-100ms number marketing copy implies. Real benchmarks tell a more complicated story.

---

## What the Benchmark Data Actually Shows

### Cold Start Latency: The Real Numbers

Community benchmarks published through late 2024 and early 2025 — referenced in DEV Community's Node.js deployment comparison — measured Fly.io free tier cold starts under these conditions: shared-CPU-1x machine, 256MB RAM, Node.js 20 LTS, a basic Express.js app with 3–5 dependencies.

Results across 50 test runs after 10-minute idle periods:

- **P50 cold start**: ~900ms
- **P95 cold start**: ~2,100ms
- **P99 cold start**: ~3,200ms
- **Warm request latency** (subsequent requests): 12–40ms

That P99 figure is the one worth sitting with. One in a hundred visitors hitting a sleeping free-tier Node.js app on Fly.io waits over 3 seconds before seeing a response. For a portfolio project or internal tool, that's acceptable. For anything customer-facing, it's a problem.

Fly.io's Firecracker-based resume is still significantly faster than Render's free tier, which effectively rebuilds and restarts the container from scratch after 15 minutes of inactivity. Render's documented cold start on free plans averages 30–50 seconds — a different category of pain entirely.

### The `min_machines_running` Trade-off

Setting `min_machines_running = 1` in `fly.toml` keeps one machine always on. Cold starts disappear completely. But a shared-CPU-1x machine running 24/7 consumes roughly 744 hours per month. In practice, a single always-on instance stays within the free budget for one app. Two or more apps with `min_machines_running = 1` each will start generating charges. The math works — until it doesn't.

### Node.js-Specific Factors That Amplify Cold Starts

Node's startup overhead isn't flat. The cold start tax compounds based on:

- **Dependency tree size**: An Express app with Prisma and 40 transitive dependencies adds ~400–600ms of module initialization vs. a bare `http` server.
- **TypeScript compilation at startup**: Apps running `ts-node` directly in production (not pre-compiled) add another 300–800ms.
- **Database connection pooling**: Apps that establish a PostgreSQL connection during startup add 100–300ms depending on the Fly.io region and database proximity.

Pre-compiling TypeScript to JavaScript before deployment and deferring database connections to first request (lazy initialization) are the two highest-leverage changes available at the application layer. Everything else is marginal by comparison.

---

## Platform Comparison: Free Tier Cold Starts

| Platform | Cold Start (P50) | Cold Start (P99) | Idle Timeout | Always-On Free? |
|---|---|---|---|---|
| **Fly.io** (shared-CPU-1x) | ~900ms | ~3,200ms | 5 min (configurable) | No |
| **Render** (free tier) | ~30,000ms | ~50,000ms | 15 min | No |
| **Railway** (Hobby $5/mo) | N/A (always on) | N/A | None | No (paid) |
| **Vercel** (serverless) | 100–300ms | ~800ms | Per-request | Yes (functions) |
| **Koyeb** (free tier) | ~1,200ms | ~2,800ms | 10 min | No |

*Sources: DEV Community Node.js deployment comparison (2025), Kuberns Fly.io pricing analysis (2026), Fly.io official docs.*

Fly.io's position is clear: meaningfully faster than Render on free, slower than Vercel's serverless cold starts, and more configurable than either.

This approach can fail when your app's dependency tree is heavy or when database connections get established eagerly at boot. Under those conditions, even Fly.io's relatively fast Firecracker resume gets buried under application-layer initialization time. The platform isn't the bottleneck — your startup code is.

---

## What This Means for How You Deploy

**For personal projects or side tools** with low traffic (under 100 requests/day), Fly.io free tier with default auto-stop is the right call. The cold start is annoying, not catastrophic. Add an UptimeRobot ping every 4 minutes to keep the machine warm — a free workaround that effectively eliminates cold starts without touching your compute budget.

**For production APIs** that external users depend on, the calculus shifts. The cheapest path to reliable performance is `min_machines_running = 1` plus monitoring your monthly usage against Fly.io's free compute allowance. One always-on app still costs $0. Two always-on apps on the same account will likely need a paid plan.

**When Node.js startup time is the actual constraint**, app-level changes matter more than platform selection. Audit your dependency footprint with `node --require module-load-time` (available in Node 18+), eliminate `ts-node` from production, and defer expensive initialization. Benchmarks from Vibe Coding With Fred's Fly.io deployment guide confirm that a lean Express app with under 10 dependencies consistently cold-starts in under 1,000ms on the free tier — roughly 50% faster than a typical Prisma-backed app.

This isn't always the answer, but it's usually the right first question: how fat is your startup path?

---

## What Comes Next

The cold start conversation isn't static. Fly.io's engineering team has signaled interest in faster machine resume times through checkpoint improvements in their public roadmap discussions. If Firecracker snapshot restore times drop below 200ms — a goal cited in Fly.io community forums as of Q1 2026 — the free-tier cold start penalty becomes trivially small.

Three things worth watching over the next 6–12 months:

- **Fly.io's memory configurations on free tier**: More RAM directly reduces Node.js initialization time by allowing more aggressive caching.
- **Node.js 22/23 startup improvements**: The Node.js core team's work on V8 startup snapshot support could cut baseline runtime initialization by 30–40%.
- **Competitor responses**: Render has hinted at faster container resume for free tier users. If that lands, the platform comparison table above shifts meaningfully.

The bottom line: Fly.io free tier is genuinely useful for Node.js apps, but the cold start penalty is real and measurable. Plan around it with a warm-ping strategy, lean dependency trees, and pre-compiled JavaScript — and you'll get solid performance at zero cost.

What's your current cold start time on the free tier? The `fly logs` command plus a basic timing wrapper on your first middleware will give you the exact P50 number in about 10 minutes.

## References

1. [Why Fly.io Is the Best Free Docker Hosting You're Not Using | Vibe Coding With Fred](https://vibecodingwithfred.com/blog/flyio-free-tier-guide/)
2. [Deploying Node.js Apps: Comparing Railway, Render, and Fly.io - DEV Community](https://dev.to/whoffagents/deploying-nodejs-apps-comparing-railway-render-and-flyio-4cfj)
3. [Fly.io Pricing Explained 2026 - Plans, Real Costs & a Smarter Alternative • Kuberns](https://kuberns.com/blogs/flyio-pricing/)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
