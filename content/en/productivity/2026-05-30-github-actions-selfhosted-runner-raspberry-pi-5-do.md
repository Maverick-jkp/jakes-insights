---
title: "GitHub Actions Self-Hosted Runner Raspberry Pi 5 Docker Build Cache Speed Comparison"
date: 2026-05-30T20:39:56+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Node.js"]
description: "Cut GitHub Actions build times by 6x using a Raspberry Pi 5 self-hosted runner with Docker build cache. See the real speed comparison results."
image: "/images/20260530-github-actions-selfhosted-runn.webp"
technologies: ["Node.js", "Docker", "AWS", "GitHub Actions", "Linux"]
faq:
  - question: "github actions self-hosted runner raspberry pi 5 docker build cache speed comparison vs hosted runners"
    answer: "Teams using a GitHub Actions self-hosted runner on Raspberry Pi 5 report build time reductions of 4x–6x compared to GitHub-hosted runners, primarily because the Pi 5 retains Docker layer cache between runs. GitHub-hosted runners start completely cold on every job, meaning base images must be re-pulled and layers rebuilt from scratch each time, while a self-hosted Pi 5 runner preserves cached layers across runs."
  - question: "how much faster is raspberry pi 5 for github actions docker builds"
    answer: "The Raspberry Pi 5 can collapse multi-minute Docker builds down to under 60 seconds when Docker layer cache is persistent across runs on a self-hosted runner. The speed gain comes less from raw CPU power and more from avoiding the cold-start penalty that GitHub-hosted runners incur on every single build."
  - question: "is it worth running github actions self-hosted runner on raspberry pi 5"
    answer: "It makes economic sense for teams running 200 or more builds per month who want to avoid GitHub's higher-tier hosted runner pricing, especially for Docker-heavy workflows. The trade-off is real operational overhead — you are responsible for security patching, updates, and managing network exposure of the runner yourself."
  - question: "how to set up github actions self-hosted runner on raspberry pi 5"
    answer: "You can register a Raspberry Pi 5 as a GitHub Actions self-hosted runner in under 30 minutes using GitHub's official runner package for ARM64. The Pi 5's BCM2712 Cortex-A76 processor runs natively on ARM64, and pairing it with an NVMe SSD via a PCIe hat significantly improves disk I/O performance compared to older SD card setups."
  - question: "why do github hosted runners have slow docker builds"
    answer: "GitHub-hosted runners are ephemeral and start completely fresh on every run, meaning there is no persistent Docker layer cache, no pre-pulled base images, and no previously compiled dependencies available. A Docker-heavy workflow can spend 3–4 minutes just on image pulls and layer reconstruction before any actual build or test work begins."
aliases:
  - "/tech/2026-05-30-github-actions-selfhosted-runner-raspberry-pi-5-do/"

---

Build times are the silent tax on every engineering team's productivity. A Reddit thread from early 2026 caught attention across the DevOps community: a team reported cutting their GitHub Actions build times by 6x after switching to self-hosted runners. The hardware driving that result? A Raspberry Pi 5.

That's worth unpacking carefully.

> **Key Takeaways**
> - Teams running GitHub Actions self-hosted runners on Raspberry Pi 5 hardware report build time reductions of 4x–6x compared to GitHub-hosted runners, driven primarily by persistent Docker layer cache between runs.
> - The Raspberry Pi 5's BCM2712 processor (Cortex-A76, 2.4GHz) delivers roughly 2–3x the single-core performance of its predecessor, making it a credible CI node for ARM-native workloads in 2026.
> - Docker build cache persistence is the core speed advantage — GitHub-hosted runners start cold every run, while self-hosted runners retain cached layers across jobs, collapsing multi-minute builds to under 60 seconds.
> - The trade-off is real operational burden: self-hosted runners require you to manage updates, security patching, and network exposure yourself.
> - This setup makes economic sense for teams running 200+ builds per month who want to avoid GitHub's larger runner pricing tiers.

---

## Why Self-Hosted Runners Are Back in the Conversation

GitHub-hosted runners have always been convenient. Spin up, run, throw away. No maintenance. But that disposability has a cost that didn't matter much in 2020 — it matters a lot now.

GitHub's hosted runner pricing scaled up significantly across 2024 and 2025 as teams started running more frequent, more complex CI pipelines. Docker-heavy workflows hit hardest. Every run on a hosted runner starts from scratch: no layer cache, no pre-pulled base images, no previously compiled dependencies. A Node.js app with a fat `node_modules` layer might spend 3–4 minutes just on `docker pull` and layer reconstruction before a single test runs.

The Raspberry Pi 5 launched in late 2023 with the BCM2712 chip — a quad-core Cortex-A76 running at 2.4GHz. According to Raspberry Pi Ltd's official specs, this delivers roughly 2–3x the CPU performance of the Pi 4. More relevant for CI: it supports PCIe 2.0, which means NVMe SSD storage via a hat, dramatically changing disk I/O characteristics compared to the SD card era.

By early 2026, the Pi 5 ecosystem matured enough that running production-grade GitHub Actions self-hosted runners on it became genuinely viable — not a hobbyist experiment, but a cost-conscious engineering decision. According to the BetterLink/EastonDev guide published in April 2026, teams can register a Pi 5 as a self-hosted runner in under 30 minutes using GitHub's official runner package for ARM64.

The timing matters. GitHub's Actions pricing for macOS and Windows runners increased again in Q1 2026, pushing more teams to evaluate the self-hosted option seriously.

---

## Docker Build Cache: The Core Performance Driver

The Pi 5 speed story isn't really about CPU. It's about cache persistence.

On GitHub-hosted runners, each job gets a fresh VM. Docker's layer cache is empty. Even with `actions/cache` configured to save and restore Docker layers, the restore step itself takes 30–90 seconds depending on image size. Then Docker still has to decompress and load those layers into the local cache. You're trading one cost for another.

On a Pi 5 self-hosted runner, the Docker daemon keeps running between jobs. Layers cached from the last build are immediately available. A `FROM node:20-alpine` that takes 45 seconds to pull on a hosted runner takes 0 seconds on the Pi — it's already there. For a typical multi-stage Dockerfile, this alone collapses 3–4 minutes of overhead per run.

The OneUptime blog's February 2026 performance guide confirms this pattern: persistent Docker cache on self-hosted runners is consistently the highest-impact single optimization for Docker-heavy pipelines.

This approach can fail, though. If your runner disk fills up with stale layers and you're not pruning regularly, cache corruption and unpredictable build behavior follow. Persistent cache is a feature that requires active management to stay useful.

## Raw Throughput: Pi 5 vs. GitHub-Hosted Runners

GitHub's standard hosted runners use 2-core AMD64 virtual machines (per GitHub's official documentation as of May 2026). The Pi 5 runs ARM64. That architecture difference matters for build comparisons.

ARM64-native Docker images build faster on ARM64 hardware — no emulation overhead. But multi-platform builds targeting `linux/amd64` from a Pi 5 require QEMU emulation, which is slow. This is a real constraint teams hit in practice. Reports from teams running compute-heavy compilation steps via QEMU describe 4–8x slowdowns. That's not a minor footnote — it can fully erase the cache advantage.

For pure ARM64 workloads — increasingly common as AWS Graviton and Apple Silicon adoption grows — the Pi 5 holds up well. For AMD64-only images, a GitHub-hosted runner is faster on raw CPU throughput.

## GitHub-Hosted vs. Pi 5 Self-Hosted: The Full Picture

| Criteria | GitHub-Hosted (2-core) | Pi 5 Self-Hosted |
|---|---|---|
| **Architecture** | AMD64 | ARM64 |
| **Docker cache on start** | Cold (empty) | Warm (persistent) |
| **Typical Docker pull time** | 45–90 sec | 0–5 sec (cached) |
| **AMD64 build speed** | Fast (native) | Slow (QEMU emulation) |
| **ARM64 build speed** | Slow (emulation) | Fast (native) |
| **Monthly cost (200 builds)** | ~$10–40 (GitHub pricing) | ~$0 (hardware amortized) |
| **Maintenance burden** | None | High (patching, uptime) |
| **Concurrent jobs** | Scales instantly | Limited by hardware |
| **Security isolation** | Full VM isolation | Shared process space |
| **Setup time** | 0 minutes | 20–30 minutes |
| **Best for** | AMD64, variable workloads | ARM64, high-frequency builds |

The trade-off is clear. The Pi 5 wins on cache and cost for ARM64-native, high-frequency pipelines. GitHub-hosted runners win on AMD64 throughput, scalability, and zero ops burden.

---

## Three Scenarios Worth Thinking Through

**Scenario 1 — High-frequency ARM64 service builds.**
A team shipping a containerized Go or Node.js service 15–20 times daily on Graviton-targeted infrastructure. A Pi 5 runner with an NVMe SSD hat and persistent Docker cache cuts per-build time from ~4 minutes to under 60 seconds. At 300 builds/month, that's 15+ hours of compute time recovered. The hardware pays for itself in one month against GitHub's standard runner pricing.

Recommendation: Deploy 2 Pi 5 nodes for redundancy. Use GitHub's `runs-on: [self-hosted, linux, arm64]` label. Configure Docker's `--cache-from` with a local registry for even faster cache hits.

**Scenario 2 — Multi-platform image builds.**
A team publishing images for both `linux/amd64` and `linux/arm64`. Running AMD64 builds on the Pi 5 via QEMU emulation is painful — expect 4–8x slowdown on compute-heavy compilation steps. This is where the Pi 5 self-hosted comparison breaks down hard.

Recommendation: Use the Pi 5 for the ARM64 leg and a GitHub-hosted runner for AMD64. Docker's `buildx` with `--platform` flags supports splitting cross-platform builds across multiple runners natively. This isn't elegant, but it's the pragmatic answer until ARM64 hosted runners reach standard pricing.

**Scenario 3 — Small team, irregular build cadence.**
Fewer than 50 builds per month, mixed workloads, no dedicated ops person. The Pi 5 is the wrong call. Security patching, runner token rotation, and uptime management create more friction than the cost savings justify. Industry reports on self-hosted runner adoption consistently show that teams underestimate ongoing maintenance costs when evaluating the self-hosted option.

Recommendation: Stay on GitHub-hosted runners. Use `actions/cache` with `cache-from` and `cache-to` registry caching — GitHub Container Registry supports this — to recover most of the cache benefit without the self-hosted complexity.

**One thing to watch:** GitHub is reportedly expanding its larger hosted runner tiers with ARM64 options in 2026. If ARM64 hosted runners reach standard pricing, the Pi 5 cost advantage narrows significantly. That's worth tracking before committing to self-hosted infrastructure at scale.

---

## The Bottom Line

The whole Pi 5 self-hosted runner question comes down to one thing: is persistent Docker cache worth the operational overhead?

For ARM64-native, high-frequency pipelines, yes — clearly. The data from real teams shows 4x–6x build time reductions, driven almost entirely by warm cache, not raw CPU speed.

For AMD64 workloads or teams without dedicated infrastructure capacity, the answer flips.

A few things the data makes clear: Docker cache persistence — not CPU speed — explains the majority of Pi 5 runner performance gains. ARM64 workloads are the natural fit; AMD64 emulation on Pi 5 is a performance trap. The economics work at 200+ builds per month; below that, managed runners win on simplicity. And security isolation on self-hosted runners needs explicit hardening — process-level isolation isn't the same as VM-level.

Looking ahead 6–12 months: GitHub's ARM64 hosted runner expansion will pressure the self-hosted economics. NVMe-equipped Pi 5 clusters with local Docker registry caching represent the near-term performance ceiling for this approach. Teams already invested in ARM infrastructure — particularly those targeting AWS Graviton or Apple Silicon deployment targets — will keep finding value here.

The Pi 5 isn't a universal CI upgrade. It's a targeted tool for a specific problem. Use it for what it's actually good at.

What's your current build time on GitHub-hosted runners, and what percentage of that is Docker layer pulls? That number tells you whether this trade-off is worth making.

## References

1. [r/github on Reddit: We cut GitHub Actions build times by 6x with self-hosted runners — sharing our s](https://www.reddit.com/r/github/comments/1rhpavo/we_cut_github_actions_build_times_by_6x_with/)
2. [GitHub Actions Self-Hosted Runner: A Complete Guide to Private Environment Deployment · BetterLink B](https://eastondev.com/blog/en/posts/dev/20260423-github-actions-self-hosted-runner/)
3. [How to Optimize GitHub Actions Performance](https://oneuptime.com/blog/post/2026-02-02-github-actions-performance-optimization/view)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
