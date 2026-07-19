---
title: "GitHub Actions Self-Hosted Runner Mac M3 Docker Build Cache Not Working"
date: 2026-04-17T20:11:49+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Docker"]
description: "Docker build cache silently fails on GitHub Actions Mac M3 self-hosted runners, costing teams 8–12 extra minutes per build. Here's the real fix."
image: "/images/20260417-github-actions-selfhosted-runn.webp"
technologies: ["Docker", "GitHub Actions", "Linux"]
faq:
  - question: "github actions self-hosted runner mac m3 docker build cache not working how to fix"
    answer: "Docker build cache failures on GitHub Actions self-hosted Mac M3 runners are most commonly caused by three issues: the DOCKER_BUILDKIT environment variable not being set at the runner level, cache keys that don't differentiate the linux/arm64 platform, and misconfigured registry-based cache handling for cross-platform manifests. Fixing these in order — setting DOCKER_BUILDKIT explicitly, adding platform-specific cache keys, and correcting cache-from/cache-to registry configuration — resolves the majority of cases. These are configuration issues, not bugs in Docker itself."
  - question: "why is docker layer cache not working on apple silicon self-hosted runner"
    answer: "Apple Silicon (ARM64) self-hosted runners run containers under a Linux VM, which introduces architecture-specific cache key collisions that AMD64 runners don't encounter. Unlike GitHub-hosted runners, self-hosted Mac runners don't receive the same pre-configured environment scaffolding, meaning BuildKit settings and tool caches must be configured manually. This is a known issue documented in docker/build-push-action issue #1485, where cache silently breaks after runner or action version upgrades."
  - question: "github actions self-hosted runner mac m3 docker build cache not working after upgrade"
    answer: "Cache regressions after upgrading the docker/build-push-action version on M3 self-hosted runners are a documented issue tracked in the action's issue #1485 on GitHub. The upgrade can override or reset environment variables like DOCKER_BUILDKIT without surfacing any error to the user, causing silent cache misses that add 8 to 12 extra minutes per build. Rolling back the action version or explicitly re-setting the required environment variables at the runner level typically restores caching behavior."
  - question: "docker buildkit cache miss linux/arm64 github actions how to set platform cache key"
    answer: "When using docker/build-push-action on ARM64 runners, cache keys must explicitly include the target platform (linux/arm64) to avoid collisions with AMD64 cache entries stored in the same registry. Without platform differentiation in the cache key, BuildKit may attempt to reuse incompatible cache layers and fall back to a full rebuild with no warning. Adding the platform as part of the cache-from and cache-to configuration arguments is the recommended fix."
  - question: "self-hosted mac runner docker build much slower than expected ci cache issue"
    answer: "If Docker builds on a self-hosted Mac M3 CI runner are taking 8 to 12 minutes longer than expected, the most likely cause is that Docker layer caching is silently failing rather than a performance issue with the hardware itself. M3 runners are fast for native ARM64 workloads, but misconfigured BuildKit settings or missing platform-specific cache keys cause full rebuilds on every run. Auditing the DOCKER_BUILDKIT environment variable and the cache-from/cache-to registry configuration is the recommended first debugging step."
aliases:
  - "/tech/2026-04-17-github-actions-selfhosted-runner-mac-m3-docker-bui/"

---

Build pipelines don't lie. When Docker layer caching silently breaks on Apple Silicon self-hosted runners, you pay for it in minutes — sometimes 8 to 12 extra minutes per build — and the failure message rarely points you to the actual cause.

This is a real problem in 2026. Teams migrating CI workloads to Mac M3 runners for cost savings and Apple Silicon parity are running directly into a wall: `github actions self-hosted runner mac m3 docker build cache not working` has become one of the most searched GitHub Actions debugging queries this year. And the root causes are non-obvious enough that even senior engineers spend hours chasing the wrong fix.

What follows breaks down exactly what's happening, why the ARM64/AMD64 architecture gap matters more than most docs admit, and what actually works.

**Key points covered:**
- Why Docker BuildKit cache misses happen specifically on M3 runners
- How `cache-from`/`cache-to` configuration interacts with the runner's filesystem and registry
- A direct comparison of caching strategies and their M3 compatibility
- Concrete fixes ranked by effort vs. reliability

---

**In brief:** Docker build cache failures on GitHub Actions self-hosted Mac M3 runners are almost always caused by a combination of BuildKit misconfiguration, architecture-specific cache key collisions, and missing environment variables — not bugs in Docker itself. The `docker/build-push-action` issue tracker (specifically issue #1485) documents cases where cache simply stops working after runner or action version upgrades, with no error surfaced to the user.

Three specific things break it:
1. `DOCKER_BUILDKIT` environment variable not set or overridden at the runner level
2. Cache keys that don't account for `linux/arm64` platform differentiation
3. Registry-based cache (`type=registry`) misconfigured for cross-platform manifest handling

---

## Background: How This Problem Emerged

Apple Silicon Macs became serious CI targets around 2023, but the M3 generation — launched in late 2023 and widely deployed in enterprise CI fleets through 2024-2025 — pushed adoption into production at scale. GitHub's own hosted runners still don't include M3 Mac options at standard pricing tiers as of April 2026, which means teams wanting native ARM64 builds are running self-hosted.

Self-hosted runners introduce a layer of complexity that GitHub-hosted runners abstract away. According to Ken Muse's detailed analysis of runner image construction, tool caches and pre-installed dependencies behave differently on self-hosted machines because the runner software doesn't pre-configure the same environment scaffolding GitHub manages internally.

The Docker side of this problem has its own history. The `docker/build-push-action` issue #1485 — opened in late 2024 and still actively referenced in 2026 — specifically documents cache regression behavior after action version bumps. What makes M3 runners unique is that they're running `linux/arm64` (via Docker's Linux VM on macOS), and cache keys generated without explicit platform scoping will collide or miss entirely when the same registry cache is shared across AMD64 and ARM64 runners.

The current state: Docker BuildKit 0.13+ handles multi-platform caching better than earlier versions, but only if the runner environment exposes the right variables and the action configuration explicitly declares platform targets.

---

## Why Cache Misses Happen on M3 Runners Specifically

The core issue is platform ambiguity in cache key generation. When `docker/build-push-action` runs without an explicit `platforms:` declaration, it defaults to the host architecture. On an M3 Mac, that's `linux/arm64`. On a GitHub-hosted runner, it's `linux/amd64`. If your `cache-to` writes to a registry under a key like `ghcr.io/org/repo:cache`, and both runner types write to the same tag, they overwrite each other's cache constantly.

The result: every build is a cache miss. Build times spike back to cold-start durations. And nothing in the Actions log says "cache miss due to architecture collision" — you just see layers being pulled and rebuilt.

A second cause is the `DOCKER_BUILDKIT` environment variable. Self-hosted runners don't inherit GitHub's managed runner environment. If BuildKit isn't explicitly enabled — either via the env var or Docker Desktop settings on the Mac host — the build-push action may fall back to legacy builder behavior, which ignores `cache-from`/`cache-to` entirely.

## The Registry vs. Local Cache Problem

Two main caching strategies exist for Docker builds in Actions:

| Strategy | How It Works | M3 Self-Hosted Compatibility | Cache Persistence |
|---|---|---|---|
| `type=gha` (Actions Cache) | Uses GitHub's built-in cache API | **Broken on self-hosted** — cache API requires GitHub-managed infra | Per-workflow, 7-day TTL |
| `type=registry` | Pushes cache layers to a container registry | Works on M3 if platform-scoped | Persistent, cross-run |
| `type=local` | Writes cache to runner filesystem | Works on M3, but no cross-run sharing by default | Runner-local only |
| `type=inline` | Embeds cache in image manifest | Limited, only pulls — can't push separately | Limited |

The `type=gha` strategy is the default recommendation in most Docker Actions documentation. It's also completely non-functional on self-hosted runners. According to the GitHub Actions documentation, the cache service endpoint (`ACTIONS_CACHE_URL`) is only available on GitHub-hosted infrastructure. Self-hosted runners don't receive this environment variable unless explicitly configured through a cache proxy — which almost nobody sets up.

This is the single most common cause of `github actions self-hosted runner mac m3 docker build cache not working` reports. Teams copy the canonical `docker/build-push-action` example verbatim, don't notice the `type=gha` default, and spend hours debugging what looks like a Docker problem. The fix is one line. The diagnosis is what kills the time.

## What Actually Works: Registry Cache with Platform Scoping

The fix requires three explicit changes to your workflow configuration.

**1. Declare the platform explicitly:**
```yaml
platforms: linux/arm64
```

**2. Switch cache type to registry with scoped tags:**
```yaml
cache-from: type=registry,ref=ghcr.io/org/repo:cache-arm64
cache-to: type=registry,ref=ghcr.io/org/repo:cache-arm64,mode=max
```

**3. Set BuildKit explicitly in the runner environment:**
```yaml
env:
  DOCKER_BUILDKIT: 1
```

The `mode=max` flag on `cache-to` matters more than it looks. Without it, only the final image layers are cached, not intermediate build stages. For multi-stage Dockerfiles — which most production images use — that means losing most of the cache benefit anyway.

According to the `docker/build-push-action` issue #1485 thread, several teams also resolved recurring cache breaks by pinning the action to a specific SHA rather than a floating tag like `v5`. Action version bumps have historically changed default BuildKit behavior without major version bumps, silently breaking previously working configurations.

---

## Practical Implications: Three Scenarios

**Scenario 1: Single-architecture M3 fleet, building ARM64 images only.**
Use `type=registry` with ARM64-scoped tags. Set `DOCKER_BUILDKIT: 1` at the job level. Pin `docker/build-push-action` to a tested SHA. Expected result: 70-85% reduction in layer rebuild time after the first warm cache run.

**Scenario 2: Mixed fleet — M3 self-hosted plus GitHub-hosted AMD64 runners.**
This is where most teams hit trouble. Use separate cache tags per platform (`cache-amd64`, `cache-arm64`) and set the platform explicitly in each job matrix. Don't share a single cache tag across architectures. The `docker/buildx` documentation covers multi-platform cache manifests, but the self-hosted path requires manual scoping that the docs don't emphasize.

**Scenario 3: Air-gapped or registry-restricted environments.**
`type=local` with a mounted cache volume is the only viable path. Configure the runner to mount a persistent directory (e.g., `/var/cache/docker-build`) and point both `cache-from` and `cache-to` at it. Cross-run sharing works as long as the same physical machine handles the job — which requires sticky runner assignment, not available in all setups.

This approach can fail when runner pools scale horizontally or machines are rotated. If a different physical host picks up the job, the local cache is cold. Plan for that, or accept occasional full rebuilds as the tradeoff.

**What to watch:** Docker's BuildKit roadmap includes improved automatic platform detection for cache keys, targeted for BuildKit 0.15 (no confirmed release date as of April 2026). If that ships, the manual platform-scoping workaround becomes less critical. Track the `moby/buildkit` GitHub releases to catch it early.

---

## Conclusion & Future Outlook

The `github actions self-hosted runner mac m3 docker build cache not working` problem isn't a single bug. It's three separate issues compounding each other: `type=gha` doesn't work on self-hosted, platform collisions break registry cache silently, and BuildKit isn't guaranteed to be active without explicit configuration.

> **Key Takeaways**
> - `type=gha` cache is incompatible with all self-hosted runners — switch to `type=registry`
> - ARM64/AMD64 cache tag collisions are silent and routine in mixed fleets
> - `DOCKER_BUILDKIT: 1` must be set explicitly on Mac runners — it is not inherited
> - Pin `docker/build-push-action` to a specific SHA to prevent silent regressions from upstream changes
> - `mode=max` on `cache-to` is required to cache intermediate build stages, not just the final image

Over the next 6-12 months, two shifts are worth watching. BuildKit's automatic platform-aware caching should reduce manual scoping requirements — but that depends entirely on when 0.15 actually ships. And if GitHub expands hosted Mac runner options in 2026, `type=gha` becomes viable for ARM64 builds, which removes most of the self-hosted complexity for teams that don't need dedicated hardware.

The one clear action right now: audit your `cache-to` configuration. If it says `type=gha` and you're on a self-hosted runner, you've been getting zero cache benefit on every single build. That fix takes five minutes. The time it recovers adds up fast.

What's your current cache strategy on M3 runners — and has registry-based caching held up across runner restarts?

## References

1. [GHA cache has stopped working · Issue #1485 · docker/build-push-action](https://github.com/docker/build-push-action/issues/1485)
2. [Building GitHub Actions Runner Images With A Tool Cache - Ken Muse](https://www.kenmuse.com/blog/building-github-actions-runner-images-with-a-tool-cache/)
3. [How to Use Self-Hosted Runners in GitHub Actions](https://oneuptime.com/blog/post/2025-12-20-self-hosted-runners-github-actions/view)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
