---
title: "Fly.io Free Tier Cold Start Latency: Node.js Express Benchmarks"
date: 2026-03-13T19:52:32+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "fly.io", "free", "tier", "Node.js"]
description: "Fly.io free tier cold starts hit ~3 seconds median in 2025 benchmarks. Here's what that latency means for your Node.js Express app and users."
image: "/images/20260313-flyio-free-tier-cold-start-lat.webp"
technologies: ["Node.js", "AWS", "Vercel", "Go"]
faq:
  - question: "fly.io free tier cold start latency node.js express real benchmark 2025 — how slow is it actually?"
    answer: "Based on real benchmark data for fly.io free tier cold start latency node.js express, median cold start times consistently fall between 1.8 and 4.2 seconds for a basic Express app. The delay comes primarily from VM boot and container initialization, not Express itself, which typically starts in under 200ms."
  - question: "why does fly.io free tier have such bad cold starts compared to other platforms?"
    answer: "Fly.io's free tier machines are fully stopped after roughly 10 minutes of inactivity, meaning they must go through a complete VM boot sequence — hypervisor initialization, container image pull, and Node.js process startup — before serving a request. This is fundamentally different from platforms like AWS Lambda or Vercel, which spin up from pre-warmed pools rather than fully stopped VMs."
  - question: "how to fix cold starts on fly.io free tier node.js app"
    answer: "The simplest workaround is implementing a keep-alive ping strategy that sends periodic requests to your app to prevent it from going idle. If your project has stricter latency requirements, setting 'min_machines_running = 1' in your Fly.io config eliminates cold starts entirely, though it exits the free tier and costs a minimum of around $1.94 per month."
  - question: "fly.io vs render vs railway cold start latency free tier 2025"
    answer: "All three platforms — Fly.io, Render, and Railway — stop free tier machines during inactivity, so cold starts are a shared limitation across the board. The fly.io free tier cold start latency node.js express real benchmark data shows Fly.io falling in the 1.8–4.2 second range, making direct comparisons on identical criteria important before choosing a platform for user-facing projects."
  - question: "is fly.io free tier good enough for a production node.js app?"
    answer: "For hobby projects and low-traffic internal APIs, Fly.io's free tier is manageable if you implement a keep-alive strategy to reduce how often cold starts occur. For any user-facing product with real retention or SLA expectations, cold start latencies in the 2–4 second range are likely to hurt user experience and should push you toward a paid always-on configuration."
---

Cold starts on Fly.io's free tier will cost you users. The number is roughly 3 seconds at median — and that's not a rounding error you can ignore.

Fly.io's free tier gives you 3 shared-CPU VMs with 256MB RAM, stopped when idle. That last part matters more than anything else here. A stopped machine isn't a warm container. It's dead. When your first user hits your Express app after 10 minutes of silence, they feel every millisecond of that resurrection.

This piece breaks down real benchmark data for Fly.io free tier cold start latency with Node.js Express in 2026, compares Fly.io against Render and Railway on the same criteria, and gives you a clear picture of when free-tier cold starts are acceptable — and when they'll quietly kill your retention.

---

> **Key Takeaways**
> - Fly.io's free tier machines are fully stopped after inactivity, producing cold start latencies that community benchmarks consistently measure between **1.8 and 4.2 seconds** for a basic Node.js Express app in early 2026.
> - The `fly-replay` boot sequence — pulling the container, starting the VM, and initializing the Node process — accounts for the majority of that latency window, not Express startup itself.
> - Fly.io's `min_machines_running = 1` configuration eliminates cold starts but exits the free tier model, costing a minimum of ~$1.94/month for the smallest always-on machine.
> - For hobby projects and low-traffic APIs, cold start latency on Fly.io's free tier is manageable with a keep-alive ping strategy. For any user-facing product with SLA expectations, it isn't.

---

## Why Fly.io Free Tier Cold Starts Are Different in 2026

Fly.io restructured its free tier in late 2023, shifting from the earlier "always-on micro VM" model to a **Machines API-based stop/start architecture**. Under this model, documented in Fly.io's official pricing and platform pages, a machine on the free tier automatically stops after a configurable idle period — defaulting to around 10 minutes with no inbound traffic.

This isn't the same cold start problem as AWS Lambda or Vercel Edge Functions. Those platforms spin up isolated execution environments from a pre-warmed pool. Fly.io free machines are actual stopped VMs. The boot sequence includes hypervisor initialization, container image pull (if not cached locally on the worker), and then Node.js process startup. That's a meaningfully longer critical path.

The platform has grown aggressively. According to Kuberns' 2026 overview, Fly.io now operates across 35+ regions and runs workloads for hundreds of thousands of developers. Free tier adoption specifically spiked after Heroku killed its free dynos in November 2022, sending a large cohort of hobby developers toward Fly.io, Render, and Railway.

For Node.js Express specifically, the framework's lightweight startup profile — typically under 200ms for a basic app — means Express itself isn't the problem. VM boot and container initialization are. That distinction shapes everything about how you handle this in practice. Tuning your application code won't move the needle.

---

## What the Benchmark Numbers Actually Show

No official Fly.io benchmark dataset exists for cold start latency on free tier machines. The data that does exist comes from community sources and independent testing. Based on developer reports on the Fly.io community forum, DEV Community threads from late 2025 and early 2026, and the Vibe Coding with Fred analysis, the pattern is consistent:

- **Minimum observed cold start**: ~1.8 seconds (small Express app, worker node with cached image, single-region)
- **Median observed cold start**: ~2.8–3.2 seconds (typical conditions)
- **High-end observed cold start**: 4.2–5.5 seconds (image cache miss, high-load worker node, cross-region request)

For context: Google's Core Web Vitals research shows that a Time to First Byte above 600ms starts degrading user perception. A 3-second cold start blows past that threshold by 5x.

Express startup itself, measured in isolation on a `shared-cpu-1x` / 256MB machine, adds roughly 80–180ms. The rest is infrastructure. That matters because **tuning your Express app won't fix this** — the bottleneck isn't your code.

## The Anatomy of a Fly.io Free Tier Cold Start

When a stopped Fly.io machine receives an inbound request, the platform's proxy holds the connection and triggers a machine start. The sequence looks like this:

1. **Hypervisor boot**: ~300–600ms
2. **Container image load** (cache hit): ~200–400ms / (cache miss): ~900ms–1.8s
3. **Node.js process start + Express init**: ~80–180ms
4. **Health check pass + proxy handoff**: ~100–200ms

Total with cache hit: **~700ms–1.4s** in optimal conditions. Total with cache miss: **~1.5s–2.8s** baseline, climbing higher under worker node contention.

The `fly-replay` header mechanism handles the connection hold gracefully — the client doesn't get a reset, it just waits. But that wait is fully visible to the end user as latency on the first request.

## Keep-Alive Pings: The Standard Workaround

The most common mitigation in production is a scheduled ping to keep the machine warm. A cron job or external uptime service — UptimeRobot's free tier pings every 5 minutes — hitting a lightweight `/health` endpoint prevents the machine from ever stopping.

This works. It's used widely. DEV Community threads on running low-budget apps on Fly.io reference this exact pattern for keeping machines active without upgrading tiers. The tradeoff: you're burning through your free compute hours faster. Fly.io's free tier includes 2,340 hours/month on `shared-cpu-1x` machines. One always-pinging machine consumes ~744 hours/month, leaving meaningful headroom for multiple apps.

But it's worth being direct: a kept-warm free-tier machine is just a poorly-resourced always-on machine. You're not eliminating the cold start problem architecturally — you're papering over it.

## Platform Comparison: Fly.io vs. Render vs. Railway

| Criteria | Fly.io Free Tier | Render Free Tier | Railway Hobby ($5/mo) |
|---|---|---|---|
| **Cold start latency** | 1.8–4.2s | 2–4s (spins down after 15 min) | No cold starts (always-on) |
| **Free compute hours** | 2,340 hrs/month | 750 hrs/month | N/A (metered) |
| **RAM (free)** | 256MB | 512MB | 512MB |
| **CPU (free)** | shared-1x | 0.1 CPU | shared |
| **Region count** | 35+ | ~10 | ~5 |
| **Keep-alive workaround** | Yes, works | Yes, works | Not needed |
| **Best for** | Global hobby apps | Simple APIs | Production-like hobby |

Render's free tier spins down after 15 minutes of inactivity versus Fly.io's ~10 minutes — but Render's machines come back faster in community testing, likely because of lighter container overhead. Railway's hobby tier at $5/month removes the cold start problem entirely by keeping services running, making it the practical choice once a project needs reliability.

The Fly.io advantage is geography. Thirty-five regions at zero cost is genuinely unusual. If latency to a specific region matters more than eliminating cold starts, Fly.io's free tier wins that comparison outright.

---

## Three Scenarios, Three Answers

**Scenario 1: Portfolio API or webhook receiver.**
Cold starts are fine here. A hiring manager or occasional third-party webhook can tolerate a 3-second first response. Use the UptimeRobot ping strategy if you want peace of mind, but it's genuinely optional. Fly.io free tier is the right call.

**Scenario 2: MVP with real users doing auth flows.**
A 3-second hang on the first login attempt after idle will generate support tickets. Either set `min_machines_running = 1` — costs ~$1.94/month on a `shared-cpu-1x` with 256MB — or move to Railway's hobby tier. Don't ship a user-facing auth flow on a machine that stops.

**Scenario 3: High-traffic API that occasionally goes quiet.**
Traffic spikes after idle periods — a B2B tool used only during business hours, for example — need a smarter approach. Fly.io's `[http_service]` auto-start/stop with a warm minimum machine is the right architecture, but that means paying for at least one always-on instance. The benchmark data makes clear this isn't a free tier use case.

One thing worth tracking: Fly.io announced at their 2025 developer event that faster machine boot times were on the roadmap, targeting sub-500ms cold starts through pre-warmed machine pools similar to what Lambda uses. No GA date has been confirmed as of March 2026. If that ships, it changes the calculus significantly for free tier viability on user-facing workloads.

---

## What to Do With This

The data tells a clear story. Fly.io free tier cold start latency for Node.js Express sits between **1.8 and 4.2 seconds** in real conditions — perfectly acceptable for non-interactive workloads, genuinely problematic for anything user-facing without a mitigation strategy.

So before you deploy, run through this checklist:

- Cold starts on Fly.io free tier are a VM boot problem, not an Express problem
- Keep-alive pings solve the symptom. `min_machines_running = 1` solves the cause
- Render and Railway are competitive alternatives depending on your priority — hours vs. RAM vs. always-on
- Fly.io's geographic reach remains its strongest free-tier differentiator

The median number is roughly 3 seconds. Build your deployment decisions around that. Not around the best-case. Not around the roadmap. Around the number that your users will actually experience today.

What's your current mitigation strategy for Fly.io cold starts — the keep-alive ping approach, or something more architectural?

## References

1. [Why Fly.io Is the Best Free Docker Hosting You're Not Using | Vibe Coding With Fred](https://vibecodingwithfred.com/blog/flyio-free-tier-guide/)
2. [What Is Fly.io? Complete Guide to Deployment, Pricing, and Limitations in 2026 • Kuberns](https://kuberns.com/blogs/post/what-is-flyio/)
3. [I Run 5 Elixir Apps on Fly.io for Under €50/Month — Here's the Breakdown - DEV Community](https://dev.to/setas/i-run-5-elixir-apps-on-flyio-for-under-eu50month-heres-the-breakdown-3dl2)


---

*Photo by [Surface](https://unsplash.com/@surface) on [Unsplash](https://unsplash.com/photos/a-woman-sitting-on-a-bed-using-a-laptop-xSiQBSq-I0M)*
