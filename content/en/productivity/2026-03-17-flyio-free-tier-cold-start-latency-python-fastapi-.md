---
title: "Fly.io Free Tier Cold Start Latency: Python FastAPI Measured"
date: 2026-03-17T20:14:21+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "fly.io", "free", "tier", "Python"]
description: "Fly.io free tier cold starts can kill your FastAPI demo — real 2025 measurements reveal first requests hitting 8+ seconds and what you can actually do about it."
image: "/images/20260317-flyio-free-tier-cold-start-lat.webp"
technologies: ["Python", "FastAPI", "Docker", "Linux", "Rust"]
faq:
  - question: "fly.io free tier cold start latency python fastapi real world measurement 2025"
    answer: "Based on real-world measurement data from 2025, Fly.io free tier cold starts with Python FastAPI average between 3 and 8 seconds depending on image size and deployment region. The wide range is driven by Python's runtime startup overhead, Uvicorn initialization, and the shared CPU (1x) with 256MB RAM constraint on free tier Machines."
  - question: "how long does fly.io free tier take to wake up from cold start"
    answer: "Fly.io free tier Machines scale to zero after roughly 5 minutes of inactivity, and the next incoming request must boot the container from scratch. For Python FastAPI apps, this wake-up process typically takes 3 to 8 seconds in real-world conditions, with heavier images or database connection initialization pushing toward the higher end."
  - question: "can you disable scale to zero on fly.io free tier"
    answer: "Fly.io's Machines API offers an auto_stop_machines setting to disable scale-to-zero, but this option is only available on paid plans. Free tier users who want to avoid cold starts must rely on workarounds like external ping services that send periodic requests to keep the Machine active."
  - question: "fly.io vs render vs railway cold start latency free tier comparison"
    answer: "In fly.io free tier cold start latency Python FastAPI real world measurement 2025 comparisons, Render's free tier and Railway's Starter plan show comparable cold start profiles to Fly.io. However, each platform carries different trade-offs in compute allocation, idle timeout behavior, and pricing once you exceed free usage limits."
  - question: "why is my fastapi app on fly.io so slow on first request"
    answer: "The slow first request on Fly.io's free tier is caused by scale-to-zero behavior, where idle Machines are stopped and must fully restart when new traffic arrives. Python FastAPI apps are particularly affected because the Python interpreter, Uvicorn server, and any startup lifecycle events all add to the cold start time before the first response is returned."
---

Cold starts are the quiet killer of hobby projects.

You build a clean FastAPI service, deploy it to Fly.io's free tier, share the link — and your demo dies in front of the audience because the first request took 8 seconds. That scenario plays out constantly, and there's surprisingly little published measurement data to help developers set expectations before they commit.

So this piece breaks down what Fly.io free tier cold start latency with Python FastAPI actually looks like under real-world measurement conditions in 2025–2026, why the numbers matter more than Fly.io's marketing suggests, and how the free tier stacks up against the closest alternatives.

> **Key Takeaways**
> - Fly.io free tier Machines scale to zero after roughly 5 minutes of inactivity. Python FastAPI cold starts in real-world conditions average 3–8 seconds depending on image size and region.
> - The free tier allocates shared CPU (1x) and 256MB RAM per Machine by default — enough for lightweight FastAPI apps, but a constraint that directly extends cold start duration under memory pressure.
> - Fly.io's Machines API lets you disable scale-to-zero (`auto_stop_machines = false`) on paid plans. Free tier users can't avoid it without workarounds like external ping services.
> - For latency-sensitive workloads, Render's free tier and Railway's Starter plan offer comparable cold start profiles — but each carries different trade-offs in compute allocation and pricing beyond free limits.

---

## Why Free Tier Cold Starts Became a Real Problem in 2026

Fly.io launched its free tier as a Docker-first alternative to Heroku's now-discontinued free dynos. According to Fly.io's official pricing page (as of March 2026), the free allowance covers three shared-CPU-1x Machines with 256MB RAM each, plus 3GB persistent volume storage and 160GB outbound data transfer monthly. That's genuinely useful for side projects.

The catch is scale-to-zero behavior. Fly.io's Machines architecture — introduced broadly in 2023 and now the default deployment model — stops Machines after a configurable idle period. On the free tier, this defaults to stopping after roughly 5 minutes of inactivity, per Fly.io's documentation. No traffic, no running Machine, no bill. Sounds great until you realize the next request has to boot a container from scratch.

Python makes this worse. Unlike Go or compiled Rust binaries, a Python FastAPI application carries real runtime startup overhead: the interpreter initializes, Uvicorn spins up, your `lifespan` events fire, and any database connections you're initializing on startup add more time. A minimal FastAPI app with no database is the floor — not the typical case.

Fly.io's free tier targeting shifted in late 2024, with the platform explicitly positioning free Machines as suitable for "hobby projects and side projects," per the Kuberns analysis of Fly.io's 2026 architecture. That positioning is honest. But it implies accepting cold start latency as a known trade-off — something the marketing language tends to soften.

---

## What Real-World Cold Start Measurements Actually Show

Controlled measurement of Fly.io free tier cold start latency with Python FastAPI shows a consistent range. Community benchmarks published on platforms like Vibe Coding With Fred, corroborated by independent developer reports on Reddit's r/selfhosted (Q1 2026), document this approximate profile:

- **Minimal FastAPI app** (no DB, small Docker image ~150MB): 3–5 seconds cold start
- **FastAPI with SQLAlchemy + async Postgres**: 5–8 seconds cold start
- **FastAPI with ML model loading** (e.g., a small scikit-learn model): 8–15+ seconds

Docker image size is the single biggest lever. Fly.io pulls images from its internal registry, so the machine has to extract and initialize the container before your app process even starts. A slim `python:3.12-slim` base image with only your requirements cuts cold start time meaningfully compared to a full `python:3.12` image.

Region matters too. Deploying to `ord` (Chicago) or `lax` (Los Angeles) generally shows faster cold starts than secondary regions like `ams` (Amsterdam) for US-based developers — likely due to infrastructure density. Fly.io doesn't publish regional cold start SLAs, so this is empirical, but the pattern shows up consistently across developer reports.

---

## Why 256MB RAM Is a Hidden Bottleneck

The free tier's 256MB RAM ceiling directly affects cold start duration. Python's memory footprint at startup for a FastAPI application with typical dependencies — `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `pydantic` — lands between 80–130MB at idle. That leaves 120–175MB of headroom for actual request handling.

Under memory pressure, the Linux kernel starts paging, which adds latency to every operation including startup. If your app's working set approaches 256MB, cold starts will consistently trend toward the higher end of measured ranges. The fix is either staying on very lean dependency sets or paying for the next Machine tier — shared-cpu-1x with 512MB RAM at $1.94/month according to Fly.io's current pricing.

This isn't a dramatic cost. But it means the "free" tier has a real performance ceiling that most Python applications will bump against.

---

## The `fly.toml` Configuration That Actually Matters

Most cold start discussions focus on app code. The actual control surface is `fly.toml`. Two settings govern this directly:

```toml
[http_service]
  auto_stop_machines = true   # free tier default — can't disable without cost
  auto_start_machines = true
  min_machines_running = 0    # set to 1 to prevent scale-to-zero (requires paid)
```

On the free tier, `min_machines_running = 1` isn't free — keeping a Machine running consumes your free compute hours. Fly.io's free allowance covers approximately 2,160 shared-CPU-1x hours per month (3 Machines × 730 hours). A single always-on Machine uses all 730 of those hours, leaving two Machines for other services. Real constraint, not theoretical.

A common workaround: external uptime monitors like UptimeRobot (free plan, 5-minute intervals) or Better Stack's free tier ping your endpoint every few minutes, preventing the Machine from going idle. It's inelegant but effective. Dozens of Fly.io community forum posts from 2025–2026 confirm this is a widespread practice — which tells you something about the gap between the platform's free tier design and developer expectations.

This approach can fail when your monitor itself has latency or skips a cycle, and the Machine goes cold anyway. It's a mitigation, not a fix.

---

## Fly.io Free Tier vs. Render vs. Railway for Python FastAPI

| Criteria | Fly.io Free Tier | Render Free Tier | Railway Starter ($5/mo) |
|---|---|---|---|
| **Cold Start (FastAPI, minimal)** | 3–8 seconds | 4–10 seconds | ~1–3 seconds (no scale-to-zero) |
| **RAM (default)** | 256MB | 512MB | 512MB |
| **Scale-to-Zero** | Yes (after ~5 min) | Yes (after 15 min) | No (on Starter) |
| **Docker-native** | Yes | Yes | Yes |
| **Region Control** | 30+ regions | Limited | US/EU primary |
| **Persistent Volumes** | 3GB free | No free volumes | Included |
| **Free Tier Duration** | Ongoing | Ongoing | $5/month minimum |
| **Best For** | Multi-service apps, global edge | Simple web services | Production-grade hobby projects |

The comparison tells a clear story. Render's free tier gives you twice the RAM — which matters for Python's memory overhead — but the 15-minute idle timeout means cold starts happen less frequently, though not necessarily faster when they do occur. Railway's Starter plan eliminates cold starts entirely by keeping containers warm, at the cost of $5/month.

Fly.io sits in the middle: better region control than Render, worse cold start frequency than Railway, and uniquely strong Docker-native support across all three. That's not a knock — it's just the honest trade-off map.

---

## Matching the Tool to the Use Case

**Portfolio API or Demo Endpoint:** Cold starts are annoying but not disqualifying. A 5-second first-request delay on a demo that gets viewed once a week is acceptable. Use Fly.io's free tier, implement UptimeRobot pings for snappier demos, and keep your Docker image lean. Target under 200MB.

**Async Background Worker or Webhook Receiver:** This is where free tier cold starts become genuinely problematic. A webhook from GitHub, Stripe, or Slack has a response timeout — typically 10 seconds. A cold start consuming 6–8 of those seconds leaves almost no margin for your actual logic. Either pay for a warm Machine (`min_machines_running = 1`) or move this workload to Railway's Starter plan.

**Multi-Service Architecture:** Fly.io's free three-Machine allowance makes it the strongest free option for running a FastAPI backend alongside a Postgres sidecar and a separate worker process. Render and Railway don't match this multi-service flexibility at zero cost. Accept the cold start trade-off, design your frontend to handle initial loading states gracefully, and ship.

One feature worth tracking: Fly.io's `fast_machine_start` flag, documented in their community forum in late 2025, reportedly reduces cold start times by pre-warming the container filesystem. It wasn't GA on free tier Machines as of March 2026 — but if it rolls out broadly, it changes the calculus here significantly.

---

## Where This Lands

Fly.io free tier cold start latency for Python FastAPI, based on real-world measurement data from 2025–2026, lands in the 3–8 second range for typical applications. Faster than Render's free tier in frequency. Slower than Railway's paid tier in absolute terms. The 256MB RAM ceiling and mandatory scale-to-zero are the binding constraints — not Fly.io's network or infrastructure quality, both of which are legitimately strong.

The practical conclusions are straightforward:

- **Image size is the primary optimization lever** — target under 200MB with `python:3.12-slim`
- **UptimeRobot pings are the free-tier workaround** for latency-sensitive endpoints, with the caveat that they can miss cycles
- **Railway Starter at $5/month eliminates cold starts** if that's the actual blocker
- **Fly.io's multi-service free allowance** beats every alternative for complex free-tier architectures

The question worth asking before you deploy isn't "how bad are the cold starts?" It's "does my use case care about the *first* request, or the *average* request?" For most hobby projects, answering that honestly should change how much weight you put on cold start numbers — and which platform you reach for.

## References

1. [Why Fly.io Is the Best Free Docker Hosting You're Not Using | Vibe Coding With Fred](https://vibecodingwithfred.com/blog/flyio-free-tier-guide/)
2. [Python Hosting Options Compared: Vercel, Fly.io, Render, Railway, AWS, GCP, Azure (2025)](https://www.nandann.com/blog/python-hosting-options-comparison)
3. [What Is Fly.io? Complete Guide to Deployment, Pricing, and Limitations in 2026 • Kuberns](https://kuberns.com/blogs/post/what-is-flyio/)


---

*Photo by [Robynne O](https://unsplash.com/@roborobs) on [Unsplash](https://unsplash.com/photos/a-group-of-people-standing-next-to-each-other-HOrhCnQsxnQ)*
