---
title: "GitHub Actions Free Minutes Exhausted: Self-Hosted Runner on Pi 4"
date: 2026-04-16T20:23:12+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "free", "Python"]
description: "Burned through GitHub Actions' 2,000 free monthly minutes by week two? Route private repo workflows to a Raspberry Pi 4 self-hosted runner for $0/minute."
image: "/images/20260416-github-actions-free-minutes-ex.webp"
technologies: ["Python", "React", "Node.js", "Docker", "AWS"]
faq:
  - question: "github actions free minutes exhausted private repo workaround self-hosted runner raspberry pi 4"
    answer: "Running a self-hosted runner on a Raspberry Pi 4 is a legitimate workaround for exhausted GitHub Actions free minutes on private repos, eliminating per-minute billing entirely. The Pi 4 (4GB RAM model) costs $55–$80 upfront, draws only 6–8W under load, and provides unlimited CI minutes for lightweight workloads like Node.js, Python, Go, and Rust builds. As of April 2026, free-plan users with self-hosted runners remain exempt from the per-minute fees introduced in GitHub's December 2025 pricing update."
  - question: "how many github actions free minutes do private repos get per month"
    answer: "GitHub's free tier provides 2,000 minutes per month for private repository builds, but the effective limit drains faster than most teams expect due to multipliers. Linux runners consume minutes at 1x, Windows at 2x, and macOS at 10x, meaning a macOS build job uses 10 minutes of quota for every 1 minute of actual runtime. A team pushing code 15–20 times per week with typical modern workflows can exhaust the 2,000-minute allotment by day 18 of the month."
  - question: "did github change pricing for self-hosted runners 2025 2026"
    answer: "Yes, GitHub's December 16, 2025 changelog announcement introduced per-minute billing for self-hosted runners on Business and Enterprise plan tiers, taking effect in Q1 2026. This was a significant change from the previous model where self-hosted runners carried zero minute charges regardless of plan. Free-plan self-hosted runners remained exempt from these new fees as of April 2026."
  - question: "is raspberry pi 4 good enough for github actions self-hosted runner ci cd"
    answer: "A Raspberry Pi 4 with 4GB RAM is a viable self-hosted GitHub Actions runner for lightweight CI workloads including Node.js, Python, Go, and Rust builds. However, it is not well-suited for Docker-heavy workflows or toolchains that are incompatible with ARM architecture. The hardware cost is under $80 upfront, making it a cost-effective alternative to paid GitHub-hosted runner minutes for teams with compatible build requirements."
  - question: "how to stop paying for github actions minutes private repo"
    answer: "The most practical way to avoid per-minute charges for private repo GitHub Actions builds is to register a self-hosted runner on your own hardware, such as a Raspberry Pi 4. Self-hosted runners on the free GitHub plan are exempt from per-minute billing as of April 2026, effectively giving you unlimited CI minutes for the cost of the hardware and electricity. This approach is officially documented and production-tested, not a policy violation, though it works best for ARM-compatible, non-Docker-heavy workloads."
---

The math stopped working somewhere around late 2025.

GitHub Actions gives private repo users 2,000 free minutes per month on the free tier — sounds generous until a mid-size team ships daily and burns through that in week two. Then came GitHub's December 2025 pricing update, which introduced per-minute fees for self-hosted runners on certain plan tiers starting in 2026. The cost conversation got uncomfortable fast.

The good news: there's a legitimate escape hatch. Running a self-hosted runner on a Raspberry Pi 4 costs roughly $55–$80 in hardware, draws about 6–8W under load, and eliminates per-minute billing for your private repo builds entirely. It's not a hack. It's documented, production-tested infrastructure.

What follows covers why the free minutes problem hits private repo teams hardest, how self-hosted runners work as a workaround, the specific Pi 4 setup vs. alternatives, and — critically — where this approach breaks down.

> **Key Takeaways**
> - GitHub's December 2025 pricing change introduced per-minute fees for self-hosted runners on certain paid plans. Teams who previously treated them as fully free now see new invoice line items.
> - Private repositories consume free minutes at 1x on Linux, 2x on Windows, and 10x on macOS — draining the 2,000-minute free tier far faster than most teams expect.
> - A Raspberry Pi 4 (4GB RAM model) running as a self-hosted runner costs under $80 upfront and delivers unlimited CI minutes for lightweight workloads.
> - Free-plan self-hosted runners remain exempt from the new per-minute fees as of April 2026, making the Pi 4 workaround still viable — for now.
> - This setup works well for Node.js, Python, Go, and Rust builds. It's the wrong tool for Docker-heavy workloads or ARM-incompatible toolchains.

---

## How GitHub's Pricing Evolution Created This Problem

GitHub Actions launched in 2018 with a simple model: public repos get unlimited minutes, private repos get a monthly allotment based on plan tier. For solo developers and small teams, the free tier's 2,000 minutes felt comfortable.

That math aged poorly. By 2024, the average GitHub Actions workflow for a Node.js project had grown to include dependency caching, linting, unit tests, integration tests, and deployment steps — often running 8–12 minutes per push. A team pushing 15–20 times per week hits 2,000 minutes by day 18.

Then came the December 16, 2025 GitHub Changelog announcement. According to GitHub's official changelog, the rollout of "simpler pricing" for Actions introduced per-minute billing for self-hosted runners on Business and Enterprise plan tiers — a significant departure from the previous model where self-hosted runners carried zero minute charges. The r/devops community reacted immediately. Threads appeared noting that high-volume self-hosted fleets would see new line items on invoices starting Q1 2026.

The critical detail: as of April 2026, the free plan self-hosted runner exemption still holds. Free-tier users who bring their own compute don't get charged per-minute. That's the policy gap the Raspberry Pi 4 workaround exploits — legitimately.

The Pi 4 itself hits a useful sweet spot: ARM64 architecture, up to 8GB RAM, USB 3.0 for fast SSD storage, and a $55–75 street price for the 4GB model. It runs the GitHub Actions runner software natively. And it sits on your desk consuming less power than a phone charger.

---

## Why Private Repo Teams Hit the Wall First

Public repos don't have this problem. GitHub offers unlimited free minutes for public repositories — always has, likely always will, since it's core to their open-source strategy.

Private repos get the tiered treatment: 2,000 minutes/month on GitHub Free, 3,000 on Pro and Team. And the minute multipliers make it worse. Windows runners consume minutes at 2x the rate. macOS at 10x. A single macOS build that takes 6 minutes of wall-clock time costs 60 free minutes.

So a private repo team running any macOS builds — iOS CI, Mac app notarization, Swift package testing — burns through 2,000 minutes in roughly 33 macOS build-minutes of actual work. That's not a rounding error. That's a structural mismatch between GitHub's pricing model and how modern CI pipelines actually run.

The free-minutes-exhausted situation becomes a recurring monthly crisis for teams that don't actively monitor their usage dashboard. GitHub does send email warnings at 75% and 100% consumption, but by then the damage is already done for that billing cycle.

---

## Self-Hosted Runners: How the Mechanics Actually Work

Self-hosted runners are machines you register with GitHub that execute workflow jobs instead of GitHub's hosted infrastructure. Setup takes about 15 minutes:

1. Navigate to your repo → Settings → Actions → Runners → New self-hosted runner
2. Download the runner application package for your OS and architecture
3. Run the configuration script with your repo's registration token
4. Start the runner as a service

The runner polls GitHub's API for queued jobs and executes them locally. No inbound ports required. No VPN. Just outbound HTTPS to `*.actions.githubusercontent.com`.

For the Raspberry Pi 4 use case specifically, GitHub provides an ARM64 Linux package. The Raspberry Pi Foundation's official 64-bit OS (Raspberry Pi OS Lite, bookworm-based) supports it cleanly. According to dhewy.dev's documented setup, the runner installs and registers without modification on Pi OS 64-bit — no custom patches, no compatibility shims.

The workaround this creates: your workflow jobs route to your Pi instead of GitHub's servers. Zero minutes consumed from your monthly allotment.

---

## Setting Up the Raspberry Pi 4 Runner: What the Numbers Show

Hardware requirements for a functional runner:

- **Minimum**: Pi 4 2GB RAM — handles single-job, lightweight builds
- **Recommended**: Pi 4 4GB RAM — handles parallel steps, moderate dependency trees
- **Storage**: External SSD over USB 3.0 (not the SD card — SD write endurance fails under CI workloads within months)
- **Power**: Official USB-C power supply, 3A minimum. Undervoltage kills job stability.

Performance benchmarks from community testing (dhewy.dev, April 2025 data):

- Node.js 20 `npm ci` + unit test suite: ~3–4 minutes wall-clock
- Go 1.23 build + test: ~2–3 minutes
- Python 3.12 pytest suite (500 tests): ~90 seconds
- Docker buildx for ARM64 images: ~8–12 minutes (native, no emulation overhead)

The Pi struggles with cross-compilation and x86-targeted Docker builds. That's not a workaround failure — it's physics.

---

## Comparing CI Options for Private Repo Teams in 2026

| Feature | GitHub Hosted (Free) | GitHub Team Plan | Self-Hosted Pi 4 | Hetzner CX22 VM |
|---|---|---|---|---|
| Monthly cost | $0 (within 2,000 min) | $4/user + overages | ~$0.015/hr (electricity) | ~$4–6/month |
| Free minutes | 2,000/month | 3,000/month | Unlimited | Unlimited |
| CPU | 2 vCPU (x86) | 2 vCPU (x86) | 4-core ARM Cortex-A72 | 2 vCPU (x86) |
| RAM | 7GB | 7GB | 4GB (recommended) | 4GB |
| Setup time | 0 minutes | 0 minutes | ~20–30 minutes | ~15–20 minutes |
| x86 compatibility | ✅ Full | ✅ Full | ⚠️ Limited | ✅ Full |
| Maintenance burden | None | None | Low-medium | Low |
| Best for | Occasional builds | Active small teams | ARM-native builds | x86 + unlimited minutes |

The Hetzner CX22 comparison deserves a closer look. At €3.79/month (~$4.10 as of April 2026), a cloud VM gives you x86 architecture, 2 vCPUs, 4GB RAM, and unlimited CI minutes without physical hardware setup. For teams already running cloud infrastructure, this is often the cleaner path — no hardware to maintain, no dependency on home internet reliability.

The Pi 4 wins on total cost over time (no recurring monthly fee after hardware purchase) and on ARM64-native workloads where emulation overhead on x86 runners adds 3–5x to build time.

---

## Three Scenarios, Three Different Decisions

**Scenario 1: Solo developer, private repo, consistently hitting 2,000 minutes**

The Pi 4 is the right call. The upfront cost pays off in month two. Buy the 4GB model, add a 128GB USB SSD, flash Pi OS Lite 64-bit, register the runner. Label it `self-hosted, linux, arm64` in your workflow YAML and route your heaviest jobs there. Keep GitHub's hosted runners as fallback for macOS-specific needs.

**Scenario 2: Team of 5–10 developers, 50–80 builds per day**

A single Pi 4 becomes a bottleneck — it handles one job at a time by default. Options: run multiple runner instances on the same Pi (works for lightweight jobs, not build-heavy workloads), add a second Pi, or switch to a Hetzner or DigitalOcean VM where horizontal scaling doesn't require buying more hardware. At this volume, the GitHub Team plan ($4/user/month) also becomes competitive if the alternative is managing multiple machines.

**Scenario 3: Team needing Windows or macOS CI**

Self-hosted runners don't solve the macOS problem without a Mac. A Mac Mini M2 runs the GitHub runner and handles macOS/iOS builds natively — but at $599+ in hardware, the economics shift considerably. For Windows, any x86 mini PC running Windows Server works. The Pi 4 isn't in this conversation.

This approach can also fail when your home or office internet connection is unreliable. The runner needs stable outbound connectivity to GitHub's API. A flaky connection means failed jobs and frustrated developers, and that's a hidden cost that doesn't show up in the hardware comparison table.

**One thing to watch**: GitHub hasn't announced changes to the free-plan self-hosted runner exemption as of April 2026, but the December 2025 pricing update signals that the "self-hosted = always free" assumption has a shelf life. Monitor the GitHub Changelog (`github.blog/changelog`) for any free-tier policy adjustments in Q3–Q4 2026.

---

## What This Looks Like Going Forward

The self-hosted runner on Raspberry Pi 4 is legitimate, documented, and cost-effective for the right workloads. But it isn't appropriate for every team, and it's worth being honest about that.

GitHub's 2,000 free minutes disappear faster than the number implies, especially once Windows and macOS minute multipliers enter the picture. The December 2025 pricing update created new per-minute fees for self-hosted runners on paid plans, but free-tier self-hosted runners remain exempt as of April 2026. A Pi 4 (4GB, ~$70) plus a USB SSD covers its own cost in under two months compared to CI overage charges. Cloud VMs are the x86-compatible alternative at $4–6/month with no hardware maintenance overhead.

The honest near-term read: GitHub will likely close the free-tier self-hosted runner exemption or add restrictions within 12–18 months as self-hosted runner adoption continues scaling. The current window is real but probably temporary. The open product question — whether GitHub introduces a "bring your own compute" tier with explicit SLA guarantees for enterprise teams — remains unanswered. That's the gap making self-hosted runners so popular despite the operational overhead.

The one clear action regardless of which scenario fits your team: check your Actions usage dashboard today at `github.com/settings/billing`. If you're consistently hitting 80%+ of your monthly allotment on private repos, the Pi 4 setup pays for itself before your next billing cycle closes.

The calculation is more personal than technical. What's your current monthly CI bill, and is the setup time worth it for the volume you're running?

## References

1. [Running GitHub Actions on Your Desk Instead of Renting Compute | dhewy.dev - Platform Engineering & ](https://dhewy.dev/posts/running-github-actions-on-your-desk-instead-of-renting-compute/)
2. [r/devops on Reddit: Github Actions introducing a per-minute fee for self-hosted runners](https://www.reddit.com/r/devops/comments/1po8hj5/github_actions_introducing_a_perminute_fee_for/)
3. [Update to GitHub Actions pricing - GitHub Changelog](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
