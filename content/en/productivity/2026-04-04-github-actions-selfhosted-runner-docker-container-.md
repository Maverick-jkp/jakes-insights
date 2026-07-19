---
title: "GitHub Actions Self-Hosted Runner Docker OOM Kill Fix"
date: 2026-04-04T19:53:03+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Docker"]
description: "GitHub Actions self-hosted runner OOM kills are silent and misdiagnosed. Fix Docker container memory limits before the kernel murders your next CI build."
image: "/images/20260404-github-actions-selfhosted-runn.webp"
technologies: ["Docker", "Kubernetes", "AWS", "GitHub Actions", "Linux"]
faq:
  - question: "github actions self-hosted runner docker container memory limit oom killed fix"
    answer: "The most common fix for GitHub Actions self-hosted runner Docker container memory limit OOM killed scenarios is adding a `--memory-swap` flag alongside your `--memory` flag in Docker, which prevents the kernel from triggering OOM kills when virtual memory spikes. The root cause is that the .NET-based runner pre-allocates 1-2GB of virtual address space even at idle, which conflicts with strict Docker memory limits."
  - question: "why does github actions self-hosted runner keep getting killed in docker"
    answer: "Your GitHub Actions self-hosted runner is likely being killed by the Linux kernel's OOM killer, not because of a code or test failure. The runner process (built on .NET) pre-allocates 1-2GB of virtual memory even when idle, which can push it over Docker container memory limits and trigger an OOM kill silently."
  - question: "how to fix OOM killed errors in github actions self-hosted runner docker container memory limit"
    answer: "To fix OOM killed errors in a GitHub Actions self-hosted runner Docker container, set both `--memory` and `--memory-swap` flags when running your container, ensuring swap space is accounted for alongside RAM. You can also use community-built OOM prevention daemons or increase the container memory limit to accommodate the runner's idle virtual memory footprint of 1-2GB."
  - question: "docker memory limit causing flaky tests in ci pipeline"
    answer: "Flaky tests or intermittent CI failures are often misdiagnosed symptoms of OOM kills caused by Docker memory limits being set too low. When the Linux kernel kills a runner process due to memory pressure, the failure can look like a network timeout or test flakiness rather than an out-of-memory error, making it difficult to diagnose."
  - question: "github actions runner virtual memory too high docker"
    answer: "The GitHub Actions runner process consumes 1-2GB of virtual memory (VSZ) even at idle due to how the .NET runtime pre-allocates address space, a behavior documented in GitHub issue #3796. This is not a memory leak but rather expected .NET runtime behavior, and it becomes a problem specifically when Docker container memory limits are enforced without accounting for swap."
aliases:
  - "/tech/2026-04-04-github-actions-selfhosted-runner-docker-container-/"

---

Your CI pipeline didn't fail because of bad code. It got murdered by the Linux kernel. That distinction matters more than most teams realize.

OOM kills — where the kernel terminates a process because the host ran out of memory — are one of the most frustrating failure modes in self-hosted CI. They're silent, intermittent, and chronically misdiagnosed as flaky tests or network timeouts. In 2026, as more engineering teams migrate from GitHub-hosted runners to self-hosted infrastructure to cut costs, this problem surfaces constantly. And the fix isn't always obvious.

What follows breaks down why GitHub Actions self-hosted runner Docker container memory limit OOM killed scenarios happen, what the data shows about root causes, and how to actually fix it.

**Quick navigation:**
- Why the runner's virtual memory behavior catches teams off guard
- How Docker container memory limits interact with the Linux OOM killer
- Which mitigation approaches work — and which ones don't
- A practical comparison of fix strategies by use case

---

**In brief:** GitHub Actions self-hosted runners consume unexpectedly large amounts of virtual memory even at idle, making Docker container memory limits a landmine for CI workloads. The fixes range from simple `--memory-swap` adjustments to dedicated memory pressure monitoring tools, depending on your infrastructure setup.

1. Virtual memory (VSZ) consumption in idle runners routinely exceeds 1–2 GB, independent of actual RSS usage — confirmed in the open GitHub issue #3796 with hundreds of affected reports.
2. Docker's default `--memory` flag without a corresponding `--memory-swap` setting can silently trigger OOM kills even when physical RAM appears available.
3. Community-built tooling — including a purpose-built OOM prevention daemon posted to r/devops in 2025 — now exists specifically for this problem, filling a gap GitHub hasn't officially addressed.

---

## The Root Cause: Virtual Memory, Not What You Think

Most engineers assume an OOM kill means actual RAM exhaustion. Often it doesn't.

The GitHub Actions runner process itself — even sitting idle between jobs — allocates substantial virtual address space. A tracked issue on the `actions/runner` GitHub repository (#3796) documents this directly: contributors reported the idle runner listener consuming virtual memory in the 1–2+ GB range. This isn't a memory leak in the traditional sense. It's how the .NET runtime (the runner is built on .NET) pre-allocates address space.

Why does this matter for Docker? When you run a self-hosted runner inside a container with a `--memory` flag, Docker enforces that limit against the container's total memory accounting. The Linux kernel's OOM killer doesn't distinguish between "virtual" and "real" memory in every scenario — when memory pressure hits, it looks for processes to kill. Your runner job is a prime target.

This is the core tension: the runner's runtime assumes generous address space, but your Docker memory limit assumes a tightly scoped process.

---

## How Docker Memory Limits Make This Worse

Setting `--memory 2g` on a runner container feels responsible. It often isn't.

Docker's `--memory` flag sets the hard limit for RAM. Without explicitly setting `--memory-swap`, Docker defaults to double that value for swap — so `--memory-swap 4g` implicitly. But on hosts where swap is disabled — common in cloud-native environments and Kubernetes nodes — that swap allowance is theoretical. The OOM killer fires when physical RAM fills.

The GitHub Actions self-hosted runner Docker container memory limit OOM killed pattern accelerates under three specific conditions:

1. **Parallel jobs on the same host** — each runner container competes for the same pool
2. **Build tools with aggressive caching** — Maven, Gradle, and Webpack can spike memory 3–5x above their steady-state usage
3. **Container image pulls during the job** — the Docker daemon itself consumes memory during layer extraction, outside the runner container's accounting

A frequently cited r/devops thread from 2025 showed engineers hitting OOM kills not during compilation, but during `docker pull` steps — the daemon was consuming host memory that the kernel then couldn't satisfy for the runner container. That's a failure mode most teams don't anticipate, because the memory spike doesn't appear inside the container at all.

---

## Fix Strategies: A Comparison

There are four main approaches to the GitHub Actions self-hosted runner Docker container memory limit OOM killed problem. They're not mutually exclusive, but they carry meaningfully different trade-offs.

| Approach | Memory Safety | Complexity | Cost Impact | Best For |
|---|---|---|---|---|
| Increase `--memory` limit | Medium | Low | Higher host cost | Quick fix, single runner |
| Set `--memory-swap` explicitly | Medium | Low | Neutral | Hosts with swap enabled |
| Limit concurrent jobs (runner scale) | High | Medium | Neutral | Multi-runner hosts |
| Memory pressure monitoring daemon | High | Medium-High | Low | Production fleets |

### Approach 1: Resize the Container Limit

Bumping to `--memory 4g` or `--memory 6g` gives the runner room to breathe. It's the fastest fix. It's also wasteful on multi-tenant hosts, and it doesn't address the underlying cause — it just raises the ceiling. On AWS `t3.medium` instances (4 GB RAM), this approach leaves almost no headroom for the host OS and Docker daemon overhead, which together consume roughly 500 MB at baseline each.

### Approach 2: Explicit Swap Configuration

Setting `--memory-swap -1` disables the swap limit entirely, letting the container use host swap freely. On hosts with swap configured — a 4–8 GB swapfile is common on bare-metal CI boxes — this prevents hard OOM kills at the cost of slower job performance when swap is actually used. It's not appropriate for latency-sensitive builds, but it's a solid safety net for nightly integration jobs.

This approach can fail when the host itself has no swap configured. Check with `swapon --show` before relying on it.

### Approach 3: Job Concurrency Limits

The `--max-parallel` setting in your workflow, combined with runner group configurations, keeps memory pressure predictable. According to GitHub's documentation on self-hosted runner scaling (docs.github.com, 2026), limiting concurrent jobs per runner group is the recommended first mitigation for resource contention. This won't help if a single job's memory footprint is the problem, but it eliminates the multi-job stacking scenario entirely.

### Approach 4: Memory Pressure Monitoring

A purpose-built tool discussed on r/devops monitors memory pressure at the host level and proactively signals runners to pause or drain before the OOM killer activates. The tool watches `/proc/meminfo` and sends `SIGTERM` to the runner process gracefully — giving it a chance to fail the job cleanly rather than getting killed mid-execution. The result: actionable error messages instead of cryptic exit codes, which cuts debugging time significantly.

This isn't always the answer. If your workload is unpredictable and bursty, the daemon can trigger false positives, pausing jobs that would have completed fine. Tune the memory pressure threshold carefully before relying on it in production.

---

## Practical Scenarios: What to Actually Do

**Scenario 1 — Single runner on a dedicated VM:**
Start with `--memory-swap -1` and enable swap on the host. Add memory usage logging to your workflow (`free -h` as a step) to baseline actual consumption. If jobs consistently spike past 6 GB RSS, you need a larger instance — not a config tweak.

**Scenario 2 — Multiple runners on a shared host:**
Set explicit `--max-parallel 2` (or 1) per runner group. Add cgroup-level monitoring via `/sys/fs/cgroup/memory/memory.usage_in_bytes` to alert before OOM conditions develop. The r/devops daemon approach fits well here — it prevents one job from starving another.

**Scenario 3 — Kubernetes-based self-hosted runners (Actions Runner Controller):**
Set `resources.requests.memory` and `resources.limits.memory` in your pod spec carefully. The gap between request and limit matters: a tight limit where request equals limit triggers OOM eviction under burst workloads. A 2:1 ratio — say, request 2 Gi with limit 4 Gi — gives burst headroom without over-provisioning reservations. GitHub issue #3796 specifically surfaces this as a Kubernetes pain point, with multiple contributors confirming the pattern.

---

## What Comes Next

The GitHub Actions self-hosted runner Docker container memory limit OOM killed problem isn't resolving on its own. GitHub hasn't shipped a fix for the runner's virtual memory footprint as of April 2026 — issue #3796 remains open with active discussion.

The .NET runtime's memory allocation behavior is partially configurable via environment variables (`DOTNET_GCHeapHardLimit`, `DOTNET_GCConserveMemory`), and a handful of teams have reported success tuning these. It's not officially documented by GitHub for runner deployments, which means you're operating outside the support envelope if something breaks.

**Signals worth tracking over the next 6 months:**
- Whether GitHub ships runner v2.320+ with configurable memory profiles, currently discussed in the issue thread
- Adoption of Actions Runner Controller 0.10.x, which adds better resource limit defaults
- Whether the community memory-pressure tooling gets packaged as a maintained open-source project

> **Key Takeaways**
> — OOM kills in self-hosted runners are frequently caused by virtual memory behavior in the .NET runtime, not actual workload RAM exhaustion.
> — Docker's `--memory` flag without explicit `--memory-swap` creates silent failure conditions, especially on swap-disabled hosts.
> — The right fix depends on your setup: swap configuration for dedicated VMs, concurrency limits for shared hosts, pod spec tuning for Kubernetes.
> — GitHub issue #3796 remains unresolved. Waiting for an official fix is not a strategy.
> — Add memory observability (`free -h`, cgroup metrics) to your CI jobs now, before the next OOM kill wipes a build you actually needed.

The OOM killer doesn't file bug reports. It just silently ends your build. Set explicit swap limits, constrain job concurrency, and instrument your runners before this becomes a production incident — not after.

What's your current runner setup — bare metal, cloud VMs, or Kubernetes? The right fix depends heavily on the answer.

---


- GitHub Actions Runner Issue #3796: [github.com/actions/runner/issues/3796](https://github.com/actions/runner/issues/3796)
- r/devops — OOM kill prevention tooling thread (2025): [reddit.com/r/devops/comments/1lrg0x4](https://www.reddit.com/r/devops/comments/1lrg0x4/i_wrote_a_tool_to_prevent_oomkilled_builds_on_our/)
- GitHub Docs — Self-hosted runner scaling: [docs.github.com/en/actions/hosting-your-own-runners](https://docs.github.com/en/actions/hosting-your-own-runners)

## References

1. [Self-Hosted Github actions runner listener uses huge amount of virtual memory when idle · Issue #379](https://github.com/actions/runner/issues/3796)
2. [r/devops on Reddit: I wrote a tool to prevent OOM-killed builds on our CI runners](https://www.reddit.com/r/devops/comments/1lrg0x4/i_wrote_a_tool_to_prevent_oomkilled_builds_on_our/)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
