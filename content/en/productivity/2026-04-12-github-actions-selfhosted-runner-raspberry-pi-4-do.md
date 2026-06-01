---
title: "GitHub Actions Self-Hosted Runner Raspberry Pi 4 Docker Build ARM64 Cache Miss Slow"
date: 2026-04-12T20:02:38+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Node.js"]
description: "ARM64 Docker builds on a Raspberry Pi 4 self-hosted runner jumped from 4 to 55 minutes? Cache misses are why. Here's the fix."
image: "/images/20260412-github-actions-selfhosted-runn.webp"
technologies: ["Node.js", "Docker", "AWS", "Azure", "GitHub Actions"]
faq:
  - question: "why is github actions self-hosted runner raspberry pi 4 docker build arm64 cache miss slow"
    answer: "The slowdown is caused by three compounding issues: the Raspberry Pi 4's limited memory bandwidth (~6.4 GB/s), Docker BuildKit's default inline cache mode performing poorly on ARM64, and how GitHub Actions manages cache artifacts across self-hosted runner instances. Together, these can inflate build times from under 5 minutes to 40–55 minutes even with no code changes. Switching to registry cache mode with explicit cache-from and cache-to directives is the most impactful fix without replacing hardware."
  - question: "how to fix docker buildx cache miss on arm64 raspberry pi self-hosted runner"
    answer: "Replace Docker BuildKit's default inline cache mode with registry cache mode by adding explicit cache-from and cache-to directives in your GitHub Actions workflow. This change alone can reduce ARM64 build times by 60–75% on self-hosted Raspberry Pi 4 runners without any hardware upgrade. The inline cache mode is largely ineffective for multi-stage Docker builds on ARM64 self-hosted runners."
  - question: "github actions self-hosted runner raspberry pi 4 docker build arm64 cache miss slow vs github hosted runners"
    answer: "GitHub-hosted M-series runners offer significantly higher memory bandwidth compared to the Raspberry Pi 4's ~6.4 GB/s, making them 8–10× faster for layer-heavy Docker builds. Teams experiencing persistent slow ARM64 builds on Raspberry Pi 4 self-hosted runners can route ARM64 jobs to GitHub's hosted M-series runners as an alternative to fixing cache configuration or upgrading hardware. This is one of three viable solutions alongside fixing BuildKit cache settings or upgrading the self-hosted hardware itself."
  - question: "does raspberry pi 4 support arm64 docker builds for ci cd"
    answer: "Yes, the Raspberry Pi 4 runs 64-bit ARM natively using the BCM2711 SoC, making it capable of building linux/arm64 Docker images without QEMU emulation. However, its limited memory bandwidth and default Docker BuildKit behavior make it significantly slower than cloud-based alternatives for production CI/CD pipelines. It works best when properly configured with registry-mode caching to avoid repeated cache misses."
  - question: "how much does arm64 docker build slow down on raspberry pi 4 compared to normal"
    answer: "Community reports from 2025 document build times jumping from approximately 4 minutes to 55 minutes after migrating Docker builds to ARM64 self-hosted runners on Raspberry Pi 4 hardware. The Raspberry Pi 4's memory bandwidth is roughly 8–10 times lower than a modern cloud runner, making layer-heavy multi-stage builds disproportionately affected by cache misses. Proper BuildKit cache configuration can recover most of that lost time without hardware changes."
---

Build times jumped from 4 minutes to 55 minutes overnight. No code changes. No infrastructure updates. Just a switch to ARM64 runners—and suddenly everything crawled.

That's not a one-off horror story. It's a pattern showing up across engineering teams in 2026, and the root cause is almost always the same: **cache misses on ARM64 Docker builds combined with self-hosted runner misconfiguration on hardware like the Raspberry Pi 4**.

> **Key Takeaways**
> - GitHub Actions self-hosted runners on Raspberry Pi 4 hardware suffer ARM64 Docker build cache misses that can inflate build times from under 5 minutes to 40–55 minutes, according to community reports on HostingArtisan forums (2025).
> - The BCM2711 chip in the Raspberry Pi 4 provides ~6.4 GB/s memory bandwidth—roughly 8–10× lower than a modern cloud runner—making layer-heavy Docker builds disproportionately slow.
> - Docker BuildKit's cache storage backend behaves differently on ARM64 versus x86_64, and the default `inline` cache mode is nearly useless for multi-stage builds on self-hosted ARM runners.
> - Switching to `registry` cache mode with explicit `cache-from` and `cache-to` directives can cut ARM64 build times by 60–75% without any hardware upgrade.
> - Teams hitting slow ARM64 builds on Raspberry Pi 4 self-hosted runners have three viable paths: fix the cache config, upgrade hardware, or route ARM64 builds to GitHub's hosted M-series runners.

---

## How ARM64 Self-Hosted Runners Became a Build Bottleneck

ARM64 on CI pipelines was a fringe concern three years ago. Not anymore. The Apple M-series wave normalized ARM64 in production, and container registries now routinely ship multi-arch images. By early 2026, a meaningful portion of new Docker images target `linux/arm64` natively—partly to support M-series dev machines and partly for AWS Graviton3 deployments.

The Raspberry Pi 4 looked like an attractive self-hosted runner option. It's cheap (~$75), runs 64-bit ARM natively, and draws under 15W. Engineering teams started spinning them up around 2022–2023 as a low-cost way to build and test ARM64 containers without QEMU emulation overhead.

The problem emerged at scale. Running `docker buildx build` on a Pi 4 with a cold cache isn't just slow—it can be *catastrophically* slow. Posts on the HostingArtisan forum (late 2025) documented teams watching pipelines balloon from 4 minutes to 55 minutes after migrating builds to ARM64 self-hosted runners. A parallel thread on r/rust identified container builds taking "forever" even on reasonably modern hardware.

The cause isn't purely the Pi 4's CPU. It's three problems stacking on each other: limited memory bandwidth, Docker BuildKit's default caching behavior on ARM64, and how GitHub Actions manages cache artifacts across runner instances.

---

## The Hardware Ceiling: What the Raspberry Pi 4 Actually Delivers

The Pi 4 uses Broadcom's BCM2711 SoC with a quad-core Cortex-A72 at 1.8 GHz. Memory bandwidth tops out around 6.4 GB/s (LPDDR4). Compare that to a GitHub-hosted `ubuntu-latest` runner, which as of Q1 2026 runs on Azure hardware delivering roughly 50–60 GB/s of memory bandwidth.

Docker layer operations are memory-bandwidth-bound. Decompressing and writing filesystem layers during a `docker pull` or build cache restore is essentially a sustained memory copy. On the Pi 4, that bottleneck is brutal. A 2 GB image with 20 layers that restores in 8 seconds on a cloud runner can take 90+ seconds on Pi 4 hardware.

That's why ARM64 cache miss problems are so pronounced on this hardware: even a partial cache hit still triggers expensive layer operations on underpowered memory. The ceiling is physical. You can't configure your way past it—only around it.

---

## The Cache Architecture Problem: Why `inline` Mode Fails

Docker BuildKit ships with three cache storage backends: `inline`, `registry`, and `local`. Most tutorials default to `inline`. That's the wrong choice for self-hosted ARM64 runners.

`Inline` cache embeds cache metadata directly in the image manifest. It only preserves the final stage of a multi-stage build. For a typical production Dockerfile with a `builder` stage and a `runtime` stage, this means every CI run re-executes the entire `builder` stage from scratch—even if nothing changed.

On x86_64 cloud runners with fast I/O, this is annoying but survivable. On a Pi 4, re-executing a Rust compile stage or a Node.js `npm ci` from zero is a 15–40 minute operation.

According to Akhilesh Mishra's analysis on Medium (2024), self-hosted runner teams routinely underestimate cache layer costs. The default GitHub Actions `actions/cache` mechanism doesn't integrate with Docker's layer cache at all—it only caches the exported archive, which means cache restoration still requires full layer decompression on every run. So even when the logs say "Cache restored," you're still paying the decompression cost every single time.

### Comparison: Cache Strategies for ARM64 Docker Builds

| Strategy | Cache Hit Speed | Cold Build Speed | Works on Pi 4 | Complexity |
|---|---|---|---|---|
| `inline` cache mode | Slow (final stage only) | Slow | Technically yes | Low |
| `registry` cache mode | Fast (all stages) | Normal | Yes | Medium |
| `local` cache + `actions/cache` | Medium | Slow (decompress) | Yes, but fragile | Medium |
| GitHub-hosted ARM64 runner | Fast | Fast | N/A | Low |
| Self-hosted Pi 4 + `registry` cache | Fast (warmed) | Slow | Yes | Medium-High |

The `registry` cache mode stores intermediate build stages directly in your container registry—Docker Hub, GHCR, ECR. On subsequent runs, BuildKit fetches only changed layers. For a multi-stage Rust build, this can drop rebuild time from 45 minutes to under 8 minutes, provided the registry is geographically close and the runner has adequate network throughput.

The trade-off is registry egress cost and configuration overhead. A Pi 4 on a home network pulling from us-east-1 ECR will face latency penalties that partially negate the cache benefit. This approach isn't always the answer—geography matters.

---

## The QEMU Tax on Mixed-Architecture Pipelines

Teams that run x86_64 cloud runners *and* Pi 4 ARM64 runners in the same workflow hit an additional problem: cache keys are architecture-specific. A layer cached by a `linux/amd64` build is useless to `linux/arm64`. GitHub Actions doesn't surface this clearly in its cache hit/miss logs.

The result: developers see `Cache restored` in the logs, assume everything is fine, and can't explain why the ARM64 leg of the matrix still takes 40 minutes. The cache *did* restore—just the wrong architecture's cache.

Fix: explicitly scope cache keys by architecture. Adding `${{ runner.arch }}` to your `cache-key` in `actions/cache` steps prevents cross-architecture cache poisoning. It's a one-line change that can recover a significant chunk of lost build time on its own.

---

## Three Scenarios, Three Fixes

**Scenario 1: Small team, Pi 4 as the only ARM64 runner.**
Switch to `registry` cache mode immediately. Add this to your `docker/build-push-action` step:

```yaml
cache-from: type=registry,ref=ghcr.io/your-org/your-image:buildcache
cache-to: type=registry,ref=ghcr.io/your-org/your-image:buildcache,mode=max
```

`mode=max` preserves all intermediate stages. Combined with scoped cache keys, this is the highest-leverage single change available—no new hardware required.

**Scenario 2: Build times still slow after the cache fix (>15 minutes).**
The Pi 4's memory bandwidth is the ceiling. An upgrade to a Pi 5 (released late 2023, LPDDR4X at ~17 GB/s) roughly triples available bandwidth. Community benchmarks from early 2025 show Docker layer operations running 2.5–3× faster on Pi 5 versus Pi 4 with identical software configuration.

Alternatively, route ARM64 builds to GitHub's hosted `ubuntu-24.04-arm` runners (available since mid-2024, powered by Ampere Altra). GitHub charges approximately $0.008/minute for ARM64 hosted runners as of April 2026. For a team with 50 builds/day averaging 8 minutes each, that's roughly $96/month—cheap compared to developer time lost waiting on a Pi 4.

**Scenario 3: Matrix builds with both amd64 and arm64.**
Don't share cache entries across architectures. Scope cache keys, run amd64 and arm64 as separate jobs with separate caches, and consider whether you actually need native ARM64 builds or whether multi-arch manifest builds via `docker buildx` on a single hosted runner are sufficient. Many teams discover the latter covers 90% of their use cases with far less operational complexity.

---

## Where This Is Headed

The slow ARM64 build problem on Raspberry Pi 4 self-hosted runners is solvable—but it requires addressing all three compounding factors: hardware bandwidth limits, BuildKit cache mode defaults, and GitHub Actions cache key scoping. Fix one in isolation and you'll still hit the other two.

The software path forward is clear: `registry` mode with `mode=max`, architecture-scoped cache keys, and an honest look at whether `inline` mode snuck into your config via a tutorial written for x86_64 environments.

The hardware path is equally clear. Pi 5 if you want to stay self-hosted. GitHub-hosted ARM64 runners if operational simplicity matters more than infrastructure cost. GitHub's ARM64 hosted runner capacity has expanded significantly in early 2026, and pricing continues to drop—which steadily weakens the case for running Pi 4 hardware as a CI runner at all.

Start with your cache key configuration. Audit it this week. Odds are it's not architecture-scoped, and that single fix might recover 30–40% of lost build time before you touch any hardware.

What's your current ARM64 build time after a cold cache? That number tells you exactly how much headroom you have.

## References

1. [r/rust on Reddit: GitHub Actions container builds take forever](https://www.reddit.com/r/rust/comments/1n4s4xb/github_actions_container_builds_take_forever/)
2. [Your GitHub Actions Runners Are Slow, And You Are Paying Too Much For Them. | by Akhilesh Mishra | F](https://medium.com/@akhilesh-mishra/your-github-actions-runners-are-slow-and-you-are-paying-too-much-for-them-5406577314fe)
3. [GitHub Actions ARM64 runners killing our build pipeline—went from 4min to 55min — Forum - hostingart](https://hostingartisan.com/forum/thread/github-actions-arm64-runners-killing-our-build-pipeline-went-from-4min-to-55min-CMbtB)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
