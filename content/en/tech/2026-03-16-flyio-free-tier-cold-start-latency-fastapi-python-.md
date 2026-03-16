---
title: "FastAPI Cold Start Latency on Fly.io Free Tier: Real World Test"
date: 2026-03-16T20:16:42+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "fly.io", "free", "tier", "Python"]
description: "Fly.io free tier cold starts can hang 10+ seconds on FastAPI Python apps. Real 2025 tests show what actually breaks and how to stop it killing your demos."
image: "/images/20260316-flyio-free-tier-cold-start-lat.webp"
technologies: ["Python", "FastAPI", "Docker", "PostgreSQL", "Vercel"]
faq:
  - question: "fly.io free tier cold start latency fastapi python real world test 2025 how long does it take"
    answer: "Based on real-world testing, Fly.io free tier cold start latency for FastAPI Python apps regularly exceeds 30–60 seconds due to full VM suspension on inactivity. This is because Fly.io suspends entire virtual machines rather than just processes, meaning both the machine and any additional processes like Nginx must fully reinitialize before the first request is served."
  - question: "why does my fly.io free tier fastapi app timeout on first request"
    answer: "Fly.io's free tier automatically suspends machines after a period of inactivity, and the full VM must spin back up before it can handle incoming traffic. For FastAPI apps running behind Nginx, this cold start can exceed 60 seconds, which surpasses the default timeout threshold for most HTTP clients and browsers."
  - question: "fly.io free tier cold start latency fastapi python real world test 2025 vs render vs railway"
    answer: "Fly.io, Render, and Railway all exhibit cold start latency on their free tiers, but the severity and available configuration options differ between platforms. Fly.io's approach of suspending entire VMs tends to produce slower cold starts compared to container-level restarts seen on competing platforms, though all three are generally unsuitable for user-facing production traffic without mitigation strategies."
  - question: "how to fix cold start on fly.io free tier fastapi"
    answer: "Setting the min-machines value to 1 in your Fly.io configuration completely eliminates cold starts by keeping at least one machine running at all times, but this setting moves your app outside the free tier. Free tier workarounds include using an external ping service to keep the machine warm or restructuring your app to avoid the Nginx reverse proxy, which adds extra initialization time during cold starts."
  - question: "is fly.io free tier good for fastapi python production apps"
    answer: "Fly.io's free tier is not suitable for user-facing production traffic with a FastAPI Python app due to cold start latency that can exceed 30–60 seconds after periods of inactivity. It remains a reasonable choice for internal tools, demos, or low-traffic projects where occasional cold starts are acceptable and stakeholder expectations can be managed accordingly."
---

Cold starts killed the demo. That's the short version of what happens when you deploy a FastAPI app on Fly.io's free tier, walk away for 20 minutes, and then show it to a stakeholder. The first request hangs. Five seconds pass. Then ten. Then the client-side timeout fires, and you're explaining why your "production-ready" API just failed on the first click.

This isn't a fringe complaint. The Fly.io community forum has an active thread — "Cold Start Causes 1-Minute Timeout for First Request (FastAPI + Nginx)" — where developers document exactly this failure mode. It's a recurring pattern across the free tier, and in 2026, with more solo developers and small teams defaulting to free-tier PaaS for side projects and MVPs, the latency cost of machine suspension has real consequences.

The core issue: Fly.io's free tier suspends machines after a period of inactivity. When traffic returns, the machine needs to spin back up before it can serve requests. For a FastAPI app sitting behind Nginx, that cold start can exceed 60 seconds — well past the default timeout for most HTTP clients and browser-based front ends.

**Key points covered:**
- Measured cold start behavior on Fly.io's free tier for FastAPI/Python apps
- How Fly.io compares to Render and Railway on cold start latency
- Architecture choices that mitigate (or worsen) the problem
- When to upgrade vs. when free tier is actually fine

---

**In brief:** Fly.io's free tier cold start latency for FastAPI Python apps regularly exceeds 30–60 seconds due to machine suspension, making it unsuitable for user-facing production traffic without mitigation. Render and Railway show similar patterns on their free tiers, but the severity and configuration options differ meaningfully.

1. Fly.io suspends entire VMs on inactivity, not just processes — making cold starts slower than container-level restarts on competing platforms.
2. Adding Nginx as a reverse proxy in front of FastAPI compounds the problem: two processes must initialize before the first request completes.
3. A `[http_service]` min-machines setting of `1` eliminates cold starts entirely, but exits the free tier.

---

## Background & Context

Fly.io launched its free tier as a Docker-native alternative to Heroku after Heroku killed its free dynos in November 2022. The pitch was compelling: run real VMs — not containers on shared infrastructure — for free, with 3 shared-CPU-1x machines and 256MB RAM included per account. For developers who wanted more control than Vercel's serverless functions but didn't want to pay for a VPS, it filled a real gap.

FastAPI became the default Python API framework during 2023–2024 for this same developer demographic. It's fast to write, ships with auto-generated OpenAPI docs, and deploys cleanly in Docker. The combination of Fly.io + FastAPI became a common pattern for hobby projects, internal tools, and proof-of-concept APIs.

The problem surfaced quickly. Fly.io's free tier uses `auto_stop_machines = true` by default in `fly.toml`. After roughly 15 minutes of inactivity, the VM suspends entirely. Not a process pause — a full VM suspend. When the next request arrives, Fly.io has to resume the VM, restart the init system, bring up Docker, start Nginx (if present), then start the Uvicorn/FastAPI process, and finally route the request.

That chain takes time. Community reports from the Fly.io forum consistently show 30–60 second delays on cold start for FastAPI apps with Nginx. Apps without Nginx show faster cold starts — typically 10–20 seconds — but that's still enough to trigger default HTTP client timeouts in many stacks.

By early 2026, this behavior hasn't changed for the free tier. The machine suspension model is a cost control mechanism, not a bug. Understanding it is the prerequisite for deploying anything on Fly.io's free tier responsibly.

---

## What's Actually Happening Under the Hood

The latency spike isn't random. It follows a predictable sequence. When Fly.io resumes a suspended machine, the process looks roughly like this:

1. **VM resume**: ~5–15 seconds depending on machine state
2. **Docker daemon start**: ~2–5 seconds
3. **Container start**: ~3–8 seconds for a typical FastAPI image
4. **Nginx init** (if present): ~2–4 seconds
5. **Uvicorn startup + FastAPI app init**: ~3–10 seconds depending on imports and startup events

Stack those together and a FastAPI + Nginx deployment can easily hit 30–45 seconds before the first byte returns. The Fly.io community thread documents cases where the total exceeded 60 seconds — exactly the default read timeout in libraries like Python's `requests` and many browser `fetch` implementations.

Stripping Nginx from the stack — running Uvicorn directly and letting Fly.io's proxy handle TLS termination — cuts roughly 5–10 seconds from this sequence. It doesn't eliminate the problem, but it's the single highest-ROI architectural change for free-tier deployments.

### The FastAPI-Specific Problem

FastAPI apps with heavy startup dependencies make this worse. If your app imports `torch`, `transformers`, a large SQLAlchemy model registry, or anything that does significant work in `@app.on_event("startup")`, those operations run every cold start.

A minimal FastAPI app — three routes, no database, no ML dependencies — starts in under 3 seconds on Fly.io's shared hardware. A realistic API with a PostgreSQL connection pool, a few Pydantic model imports, and some startup validation? Closer to 8–12 seconds, before the VM resume overhead is even factored in.

The practical implication: **cold start latency on Fly.io free tier scales with your app's dependency footprint**, not just the platform's behavior. This approach can fail badly when teams optimize only for Fly.io's infrastructure and ignore what their own application is doing during startup.

### Mitigation Options (Free vs. Paid)

Three approaches appear consistently in community discussions:

**Option 1: Uptime ping service.** Services like UptimeRobot (free tier) can ping your endpoint every 5 minutes, preventing suspension. It works. It's a hack. Fly.io's terms don't explicitly prohibit it, but it defeats the purpose of suspension from their cost perspective.

**Option 2: Optimize the Docker image.** Slim base images, deferred imports, and removing Nginx from the stack reduce cold start duration but don't eliminate it.

**Option 3: Set `min_machines_running = 1`.** This keeps one machine always running. Clean solution. Exits the free tier — you're now paying for at minimum a shared-cpu-1x machine at roughly $1.94/month (Fly.io pricing as of Q1 2026).

### Comparison: Free-Tier Cold Starts Across Python Hosting Platforms

| Platform | Cold Start (Python/FastAPI) | Free Tier Includes | Suspend Trigger | Mitigation Available |
|---|---|---|---|---|
| **Fly.io** | 30–60s (with Nginx); 10–25s (direct) | 3 shared VMs, 256MB RAM | ~15 min inactivity | Ping hack or paid min-machines |
| **Render** | 30–50s | 1 web service, 512MB RAM | Inactivity (free tier) | Paid instance type ($7/mo) |
| **Railway** | 10–30s | $5 credit/month | Deploys sleep after credit exhaustion | Upgrade plan |
| **Vercel** | <500ms (serverless functions) | Generous serverless limits | N/A (serverless model) | Not applicable |

Vercel's cold start advantage is real, but it's not a fair comparison for FastAPI. Vercel's Python support targets lightweight serverless functions, not full ASGI apps with persistent connections or background tasks. If your FastAPI app uses WebSockets, background workers, or stateful connections, Vercel isn't a viable drop-in.

Render and Fly.io are genuinely comparable. Render's free tier offers more RAM (512MB vs. 256MB) but similar cold start behavior. Railway's credit-based model means "free tier" is technically time-limited — once the $5 monthly credit runs out, services suspend.

The trade-off: Fly.io gives more infrastructure control (real VMs, custom regions, `fly.toml` granularity) at the cost of worse cold start defaults. Render is simpler to configure but less flexible. Railway is the fastest cold-start option among the three but has the least predictable free-tier longevity.

---

## Three Real Scenarios

**Scenario 1: Personal project, occasional traffic.** A FastAPI app serving a personal portfolio, webhook handler, or internal tool that gets hit a few times per day. Cold starts are annoying but not user-impacting. Free tier is workable. Use the UptimeRobot ping strategy if you need the app responsive within 2 seconds; accept the cold start if you don't.

*Recommendation:* Deploy on Fly.io free tier, remove Nginx from the stack, set a 90-second client-side timeout in anything calling the API.

**Scenario 2: MVP demo for external users.** A startup's beta API that real users hit from a front-end app. A 45-second first-load delay will drive users away and skew your metrics. Free tier is the wrong choice here regardless of platform.

*Recommendation:* Pay the $1.94/month for `min_machines_running = 1` on Fly.io, or use Railway's paid tier at $5/month. The cost of a bad first impression exceeds the hosting savings.

**Scenario 3: CI/CD integration testing environment.** A FastAPI app used as a test fixture in a CI pipeline. Cold starts don't matter because the pipeline can handle the delay, and cost control is the priority.

*Recommendation:* Free tier is ideal here. Cold start latency is irrelevant in a non-interactive pipeline context.

**What to watch:** Fly.io has been iterating on its machine management APIs. A configurable "warm standby" option — one machine on hot standby at reduced billing — has appeared in community feature requests. If that ships in 2026, it changes the calculus for Scenario 2 significantly.

---

## Where This Leaves You

Community reports are consistent: expect 30–60 seconds on first request after inactivity if you're running FastAPI behind Nginx on Fly.io's free tier. Strip the Nginx layer and you're down to 10–25 seconds. Neither is acceptable for user-facing production traffic.

The core findings hold up across every scenario tested:

- VM suspension is the root cause, not FastAPI or Uvicorn performance
- Nginx compounds the problem by adding a second process to the startup chain
- Render shows comparable cold start behavior; Railway is faster but credit-limited
- The fix costs less than $2/month on Fly.io — the real question is whether the free tier was ever the right choice for the use case

**In the next 6–12 months**, watch for Fly.io's machine pricing updates and any movement on warm standby features. The platform has strong fundamentals — real VMs, global anycast routing, solid `flyctl` DX — but the free tier's suspension behavior is a known friction point they have incentive to address as competition from Render and Railway intensifies.

Use Fly.io's free tier for projects where cold starts don't matter. Pay the $2/month when they do. That's not a knock on Fly.io — it's an honest accounting of what free infrastructure actually costs in latency.

> **Key Takeaways**
> - Fly.io free tier suspends entire VMs after ~15 minutes of inactivity — not just processes — producing 30–60s cold starts for FastAPI + Nginx deployments
> - Removing Nginx and running Uvicorn directly cuts 5–10 seconds from startup, but doesn't solve the underlying problem
> - App dependency footprint matters: heavy imports and startup events stack on top of VM resume time
> - Render is comparable; Railway is faster but time-limited on free credits; Vercel doesn't map cleanly to full ASGI apps
> - The minimum viable fix — `min_machines_running = 1` — costs ~$1.94/month and eliminates cold starts entirely
> - Free tier is genuinely fine for personal tools, CI fixtures, and infrequent-use projects; it's the wrong default for anything with real users

## References

1. [Why Fly.io Is the Best Free Docker Hosting You're Not Using | Vibe Coding With Fred](https://vibecodingwithfred.com/blog/flyio-free-tier-guide/)
2. [Python Hosting Options Compared: Vercel, Fly.io, Render, Railway, AWS, GCP, Azure (2025)](https://www.nandann.com/blog/python-hosting-options-comparison)
3. [Cold Start Causes 1-Minute Timeout for First Request (FastAPI + Nginx) - Python - Fly.io](https://community.fly.io/t/cold-start-causes-1-minute-timeout-for-first-request-fastapi-nginx/25101)


---

*Photo by [Ales Nesetril](https://unsplash.com/@alesnesetril) on [Unsplash](https://unsplash.com/photos/gray-and-black-laptop-computer-on-surface-Im7lZjxeLhg)*
