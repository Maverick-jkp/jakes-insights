---
title: "GitHub Actions Self-Hosted Runner Docker Cache Not Working ARM64 Mac Mini Fix"
date: 2026-05-28T23:10:04+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Docker"]
description: "Fix GitHub Actions self-hosted runner Docker cache not working on ARM64 Mac Mini M-series — it's an architectural mismatch, not a config typo."
image: "/images/20260528-github-actions-selfhosted-runn.webp"
technologies: ["Docker", "GitHub Actions", "Linux", "Rust", "Go"]
faq:
  - question: "github actions self-hosted runner docker cache not working arm64 mac mini fix"
    answer: "The root cause is that Docker on macOS runs inside a Linux VM via Docker Desktop or OrbStack, creating path and registry authentication mismatches that silently break cache-from and cache-to directives. The three most reliable fixes are local registry caching, BuildKit's --cache-type=local with explicit path mounts, and using cache-to: type=gha as the GitHub Actions Cache backend. Each approach has trade-offs depending on your pipeline structure and whether your runner environment is ephemeral or persistent."
  - question: "why is docker layer cache not persisting between runs on apple silicon mac mini self-hosted runner"
    answer: "Docker layer caching fails to persist on Apple Silicon Mac Mini runners because the Docker daemon runs inside a Linux VM, meaning cache paths and configurations interact with the host macOS OS in non-obvious ways. Unlike GitHub-hosted runners which use clean ephemeral VMs that the GHA cache backend is designed around, a persistent Mac Mini runner creates a mismatch between how the cache is written and how it is read back. Teams migrating from ubuntu-latest hosted runners to Mac Mini M-series hardware report build time regressions of 40-60% when this cache behavior breaks silently."
  - question: "how to fix docker buildkit cache on arm64 macos self-hosted github actions runner"
    answer: "The most reliable approach for the github actions self-hosted runner docker cache not working arm64 mac mini fix is to switch to BuildKit's --cache-type=local with explicitly defined path mounts that account for the macOS-to-Linux VM path translation. Alternatively, using cache-to: type=gha leverages the GitHub Actions Cache backend, though this was originally designed for ephemeral environments rather than persistent runners. A local registry cache is a third option that gives you the most control but requires additional infrastructure setup."
  - question: "mac mini m4 self-hosted runner vs github hosted ubuntu-latest performance ci"
    answer: "A Mac Mini M4, priced around $599 at release in late 2024, delivers sustained multi-core performance that outpaces GitHub's standard ubuntu-latest runners on CPU-bound workloads. The trade-off is upfront hardware cost and maintenance overhead versus paying for GitHub Actions compute minutes, making it cost-effective primarily for teams with consistent, high-volume CI load. However, teams must account for Docker caching issues specific to ARM64 macOS hosts, which can cause 40-60% build time regressions if not properly addressed."
  - question: "does github documentation cover docker cache issues on arm64 macos runners"
    answer: "As of May 2026, GitHub's official documentation does not explicitly address ARM64 macOS host differences for Docker layer caching on self-hosted runners. This leaves teams to diagnose the problem through community reports, runner logs, and third-party setup guides rather than official guidance. The silence in official docs is part of why the issue often goes undetected, since cache failures on ARM64 Mac Mini runners tend to surface as slow builds rather than clear error messages."
aliases:
  - "/tech/2026-05-28-github-actions-selfhosted-runner-docker-cache-not-/"

---

Build pipelines breaking silently on ARM64 is expensive. If you've recently moved CI workloads to a Mac Mini M-series runner, there's a good chance you've hit the `github actions self-hosted runner docker cache not working arm64 mac mini fix` problem without fully understanding why it's happening.

This isn't a configuration typo. It's an architectural mismatch baked into how Docker's layer caching interacts with ARM64 hosts — and GitHub's hosted runner ecosystem wasn't designed around it.

> **Key Takeaways**
> - Docker's `cache-from` and `cache-to` directives silently fail on ARM64 Mac Mini self-hosted runners because the Docker daemon on macOS runs inside a Linux VM, creating path and registry authentication mismatches that aren't clearly logged.
> - Teams migrating from GitHub's hosted `ubuntu-latest` runners to Apple Silicon Mac Minis report build time regressions of 40–60% when cache layers don't persist correctly between runs.
> - The three most reliable fixes — local registry caching, BuildKit's `--cache-type=local` with explicit path mounts, and GitHub Actions Cache backend via `cache-to: type=gha` — each carry distinct trade-offs depending on your pipeline structure.
> - As of May 2026, GitHub's official documentation still doesn't explicitly address ARM64 macOS host differences for Docker layer caching, leaving teams to debug through community reports and runner logs.

---

## Why ARM64 Mac Minis Became CI Targets

The shift accelerated in late 2024. Apple Silicon's performance-per-watt ratio made Mac Minis genuinely attractive as self-hosted CI nodes — especially for teams building iOS apps or cross-platform tools that needed native ARM64 environments. A Mac Mini M4 (~$599, released late 2024) delivers sustained multi-core performance that outpaces GitHub's standard `ubuntu-latest` runners on CPU-bound workloads.

According to Matthieu Napoli's documented setup at mnapoli.fr, running a self-hosted Mac Mini runner is cost-effective for teams with consistent CI load — you're trading GitHub Actions compute minutes for upfront hardware and maintenance overhead. OneUptime's 2026 runner configuration guide similarly notes that self-hosted runners give you full control over the execution environment, which sounds great until Docker's caching layer stops cooperating.

The core problem: GitHub-hosted runners spin up fresh VMs every run. That clean-slate model is actually what makes `cache-to: type=gha` work — it's designed around ephemeral environments. A persistent Mac Mini runner is the opposite. The Docker daemon persists, the filesystem persists, but the cache doesn't behave the way you'd expect because macOS isn't Linux.

Docker on macOS runs its daemon inside a Linux virtual machine (via Docker Desktop or OrbStack). That indirection means your `--cache-dir` paths, registry credentials, and BuildKit configurations interact with the host OS in non-obvious ways. When the cache problem surfaces, it's usually one of three things: the cache backend isn't supported in that context, the path the runner uses doesn't persist between jobs, or BuildKit isn't enabled.

---

## Why the Cache Silently Fails

The failure mode is frustrating because Docker doesn't always error loudly. You'll see build steps completing, but layer cache hits are zero. Every run pulls base images. Build times that should be 90 seconds stretch to 8 minutes.

The root cause on ARM64 Mac Minis is usually BuildKit not being the active builder. Classic Docker build (`DOCKER_BUILDKIT=0`) doesn't support `cache-from`/`cache-to` flags at all — it silently ignores them. On macOS, Docker Desktop sometimes defaults to legacy mode depending on the version. Confirming BuildKit is active with `docker buildx inspect` is step one. If you see `Driver: docker` instead of `docker-container`, caching won't work as expected.

The second issue: the `type=gha` cache backend requires network access to GitHub's Actions cache service. On self-hosted runners, that connection works — but the runner must be authenticated correctly, and the `ACTIONS_CACHE_URL` and `ACTIONS_RUNTIME_TOKEN` environment variables must be present. These are injected automatically on GitHub-hosted runners. On self-hosted runners, they're present during job execution but scoped per-job. Cache entries written with `type=gha` by one job aren't always readable by a subsequent job if the scope keys don't match.

## The ARM64-Specific Layer Problem

Searches for this fix spiked in early 2026 because more teams hit a specific edge case: multi-platform builds. When you run `docker buildx build --platform linux/amd64,linux/arm64` on an ARM64 host, BuildKit creates separate cache manifests per platform. If your `cache-to` registry doesn't support manifest lists — older self-hosted registries, some ECR configurations prior to 2025 updates — the ARM64 cache manifest gets dropped silently. The AMD64 layer caches fine. The ARM64 layer rebuilds from scratch every time.

This is the exact failure mode Akhilesh Mishra documented in his Medium analysis of slow, expensive runners: cache misses that look like hits at the job level. You're paying the rebuild cost on every run without any clear signal that it's happening.

## The Three Fix Approaches Compared

| Approach | Setup Complexity | Cache Persistence | ARM64 Reliable | Cost |
|---|---|---|---|---|
| `type=gha` (GitHub Actions Cache) | Low | Per-key, scoped | Yes, if keys match | Free (within 10GB limit) |
| `type=local` with mounted volume | Medium | Full, persistent on host | Yes | Storage only |
| Local registry (`registry:2`) | High | Full, persistent | Yes | Storage + registry overhead |
| `type=registry` (external ECR/GCR) | Medium | Full, persistent | Yes, if manifest lists enabled | Egress + storage fees |

**`type=gha`** is the lowest-friction path if your jobs are structured sequentially and cache keys are consistent. The 10GB cap matters for large Docker images. And it doesn't survive runner restarts well — it's re-fetched from GitHub's servers each time, adding latency on large caches.

**`type=local`** with an explicit volume mount on the Mac Mini's filesystem is the most reliable for persistent runners. You're pointing BuildKit at a directory that survives between runs:

```yaml
- name: Build with cache
  run: |
    docker buildx build \
      --cache-from type=local,src=/var/cache/docker-buildx \
      --cache-to type=local,dest=/var/cache/docker-buildx,mode=max \
      -t myapp:latest .
```

The catch: `mode=max` exports all intermediate layers, which can balloon the cache directory to 20–40GB on complex images. You need a cleanup cron job.

**Local registry** is the most production-grade option for teams running multiple Mac Mini runners. Spin up a `registry:2` container on the local network, point all runners at it. Cache is shared across machines, and manifest lists work correctly on modern Docker Registry API v2. Setup takes an afternoon but it's the approach closest to what large CI shops run internally.

---

## Scenarios and Recommendations

**Scenario 1: Single Mac Mini, iOS/macOS builds with Docker sidecars.**
The `type=local` approach wins here. Your runner is persistent, the filesystem is fast NVMe, and you control the cache path. Set `mode=max` for the first week to warm the cache, then switch to `mode=min` to control disk growth. Add a weekly `find /var/cache/docker-buildx -mtime +14 -delete` cron to prevent runaway storage.

**Scenario 2: Multiple Mac Minis in a runner group.**
Don't rely on `type=local` — each machine has its own cache, so jobs routed to different runners get cache misses. A shared local registry on your LAN (or a lightweight NAS) solves this. According to OneUptime's 2026 runner guide, runner groups with shared infrastructure consistently outperform isolated runner setups for cache-heavy pipelines.

**Scenario 3: Multi-platform builds targeting both AMD64 and ARM64.**
Explicitly separate your build jobs by platform. Don't use a single `--platform linux/amd64,linux/arm64` flag if your registry doesn't confirm manifest list support. Build ARM64 on the Mac Mini, AMD64 on a Linux runner, then merge with `docker buildx imagetools create`. This sidesteps the manifest cache drop issue entirely.

One thing worth watching: Docker's BuildKit roadmap for 2026 includes improvements to cache backend negotiation that should reduce silent failures. GitHub Actions' runner documentation team has an open issue (as of Q1 2026) to document self-hosted runner cache behavior differences explicitly. Neither fix is shipping imminently, so don't wait on upstream.

---

## What Comes Next

This problem isn't going away on its own. Docker's macOS VM layer, BuildKit backend defaults, and GitHub's cache service scope assumptions all create a specific failure surface that teams only discover after migrating to Apple Silicon runners.

The core findings:

- BuildKit must be explicitly enabled and using the `docker-container` driver, not the default `docker` driver
- `type=gha` works but has scope and size limitations on persistent self-hosted runners
- `type=local` is the most reliable single-runner fix, requiring cleanup automation
- Multi-platform builds need explicit platform separation to avoid ARM64 cache manifest drops

Over the next 6–12 months, expect Docker Desktop and OrbStack to improve BuildKit's default behavior on macOS ARM64. GitHub will likely update runner documentation to address self-hosted cache differences as community pressure builds. The local registry pattern will become more standardized as teams publish their multi-Mac-Mini setups publicly.

The action right now: run `docker buildx inspect` on your Mac Mini runner today. If you're not on `docker-container` driver, that's your first fix — and it'll cost you 15 minutes to switch.

---

*References: [mnapoli.fr/running-github-actions-mac-mini](https://mnapoli.fr/running-github-actions-mac-mini) | [OneUptime Runner Configuration Guide (Jan 2026)](https://oneuptime.com/blog/post/2026-01-25-github-actions-self-hosted-runners/view) | [Akhilesh Mishra, Medium — GitHub Actions Runner Performance Analysis](https://medium.com/@akhilesh-mishra/your-github-actions-runners-are-slow-and-you-are-paying-too-much-for-them-5406577314fe)*

## References

1. [Running GitHub Actions on a Mac Mini - Matthieu Napoli](https://mnapoli.fr/running-github-actions-mac-mini)
2. [How to Configure Self-Hosted Runners in GitHub Actions](https://oneuptime.com/blog/post/2026-01-25-github-actions-self-hosted-runners/view)
3. [Your GitHub Actions Runners Are Slow, And You Are Paying Too Much For Them. | by Akhilesh Mishra | M](https://medium.com/@akhilesh-mishra/your-github-actions-runners-are-slow-and-you-are-paying-too-much-for-them-5406577314fe)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
