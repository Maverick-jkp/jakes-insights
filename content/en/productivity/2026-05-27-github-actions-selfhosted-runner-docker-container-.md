---
title: "GitHub Actions Self-Hosted Runner Docker Container Memory Leak Fix"
date: 2026-05-27T22:10:58+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Node.js"]
description: "Fix GitHub Actions self-hosted runner Docker container memory leaks causing OOM crashes mid-job — stop patching symptoms and eliminate the root cause."
image: "/images/20260527-github-actions-selfhosted-runn.webp"
technologies: ["Node.js", "Docker", "Kubernetes", "GitHub Actions", "Go"]
faq:
  - question: "github actions self-hosted runner docker container memory leak fix"
    answer: "The most effective fix for GitHub Actions self-hosted runner Docker container memory leaks is switching to ephemeral, single-job containers that are destroyed and recreated after each job execution. This architectural shift eliminates 90%+ of memory leak incidents because the runner process accumulates heap allocations and file descriptors across jobs when running persistently. Kubernetes-based deployments with pod recycling offer the cleanest implementation of this approach at scale."
  - question: "why does github actions self-hosted runner keep running out of memory"
    answer: "GitHub Actions self-hosted runners accumulate memory across job executions because the runner agent (actions/runner) was designed as a persistent process that handles multiple jobs sequentially without fully resetting between runs. This causes heap allocations, file descriptors, and child process residue to build up inside the container over time. Teams running more than 50 concurrent jobs typically hit memory exhaustion within 4-6 hours of runner startup."
  - question: "how to fix github actions self-hosted runner docker container memory leak fix with kubernetes"
    answer: "Kubernetes-based auto-scaling deployments fix the GitHub Actions self-hosted runner Docker container memory leak by recycling pods after each job, which acts as a natural memory reset mechanism. Each new job gets a fresh container with a clean memory state, preventing the monotonic memory growth seen in persistent runner setups. This approach also handles concurrency scaling automatically, making it the recommended solution for teams running large numbers of parallel jobs."
  - question: "github actions self-hosted runner OOM kill mid pipeline"
    answer: "OOM (out-of-memory) kills during GitHub Actions pipelines on self-hosted runners are typically caused by persistent runner containers accumulating memory across multiple job executions over time. The runner process does not fully reset between jobs, causing memory usage to grow until the container hits its limit and crashes. Switching to ephemeral single-job containers that are destroyed after each run is the most reliable way to prevent mid-pipeline OOM kills."
  - question: "should I use persistent or ephemeral containers for github actions self-hosted runners"
    answer: "Ephemeral containers are strongly recommended for GitHub Actions self-hosted runners because persistent containers accumulate memory across job runs, eventually causing crashes. With ephemeral runners, a new container is spun up for each job and destroyed afterward, eliminating memory buildup entirely. While persistent containers have lower startup overhead, the operational cost of memory-related failures at scale makes ephemeral containers the better architectural choice for most teams."
aliases:
  - "/tech/2026-05-27-github-actions-selfhosted-runner-docker-container-/"

---

Memory leaks in containerized CI/CD runners aren't new. But in 2026, they're actively killing engineering velocity at scale — and most teams are still treating symptoms instead of fixing the root cause.

The specific problem: GitHub Actions self-hosted runners running inside Docker containers accumulate memory across job executions, eventually hitting OOM (out-of-memory) limits and crashing mid-pipeline. According to HyperEnv's analysis of production runner deployments, teams running more than 50 concurrent jobs regularly hit memory exhaustion within 4-6 hours of runner startup — even when individual jobs look clean in isolation.

This breaks down why the leak happens, what actually fixes it, and how different deployment architectures handle the problem at scale.

> **Key Takeaways**
> - GitHub Actions self-hosted runners accumulate memory across job runs because the runner process doesn't fully reset between executions — a known architectural limitation documented in GitHub's runner repository.
> - Teams running ephemeral, single-job containers eliminate 90%+ of memory leak incidents by destroying and recreating the container after each job, according to HyperEnv's 2026 production data.
> - Kubernetes-based auto-scaling deployments (documented by OneUptime in February 2026) provide the cleanest path to ephemeral runner management at scale, with pod recycling acting as a natural memory reset mechanism.
> - The fix isn't a single patch — it's an architectural shift from persistent to ephemeral runner containers.

---

## Background: How This Became a 2026 Problem

Self-hosted runners existed in relative obscurity for years. GitHub-hosted runners handled most workloads. Then three things changed.

First, AI/ML build pipelines exploded. Training jobs, model validation, and large dataset processing require RAM that GitHub's hosted runners — capped at 7GB on standard tiers — simply can't provide. Second, enterprise security mandates pushed more teams off hosted runners entirely. Air-gapped environments and SOC 2 compliance requirements demand runner infrastructure you control. Third, container costs dropped. Running a beefy self-hosted runner on a $300/month bare-metal instance now beats GitHub's per-minute pricing for teams doing 10,000+ minutes monthly.

The result: far more teams running self-hosted runners in Docker containers, at much higher concurrency, for much longer job durations. Memory pressure that was previously theoretical became a daily operational problem.

The architectural issue isn't subtle. GitHub's runner agent (`actions/runner`) was originally designed as a persistent process that registers once and handles multiple jobs sequentially. In containerized environments, that persistent process accumulates heap allocations, file descriptors, and child process residue across jobs. The container's memory usage grows monotonically. Without intervention, OOM kills become inevitable.

According to youngju.dev's 2026 hardening guide, teams operating runners at scale without ephemeral configuration see runner crashes averaging every 6-8 hours in high-throughput environments — translating directly to failed pipelines and manual restarts.

---

## Why Persistent Runners Leak Memory in Docker

The runner agent spawns child processes for each job step. Shell processes, Docker-in-Docker daemons, and tool cache managers all get created and theoretically cleaned up. "Theoretically" is doing a lot of work in that sentence.

In practice, zombie processes accumulate. The `/tmp` workspace directory inside the container grows with each job if cleanup scripts fail midway. Node.js-based action runners hold V8 heap references longer than expected. And if you're running Docker-in-Docker (DinD) for container builds inside your runner, you're compounding the problem — the inner Docker daemon maintains its own layer cache and image storage in memory.

HyperEnv's monitoring data shows that a runner handling mixed workloads (Node.js actions plus Docker builds) consumes roughly 180MB of baseline RAM after the first job. By job 50, that number hits 1.4GB — a 7.8x increase with no corresponding increase in job complexity.

This isn't a fluke. It's the architecture working exactly as designed, just not for your use case.

---

## The Ephemeral Runner Pattern: What Actually Works

The fix that production teams converged on in 2025-2026 is straightforward: make runners disposable. One container, one job, then destroy it.

GitHub's `--once` flag for the runner agent makes this possible. When you start the runner with `./run.sh --once`, it registers, handles exactly one job, then exits. Your container orchestration layer — whether that's a simple bash loop on a VM, Docker Compose with restart policies, or Kubernetes — spins up a fresh container for the next job.

Fresh container, fresh memory space. No accumulation. No leak.

OneUptime's February 2026 guide to Kubernetes-based auto-scaling shows this pattern implemented with Actions Runner Controller (ARC). Each job gets a clean pod. Pod exits after job completion. The Kubernetes scheduler handles the rest. Their reported outcome: memory-related runner failures dropped to effectively zero after migration from persistent to ephemeral configuration.

This approach can fail when cold start latency matters. If your pipeline is latency-sensitive — say, sub-30-second feedback loops for developer workflows — the 20-30 second pod spin-up time on Kubernetes introduces friction. Bare-metal with `--once` loops cuts that to 8-12 seconds, but you lose the auto-scaling benefits. Neither option is free.

---

## Kubernetes vs. Docker Compose vs. Bare-Metal: A Comparison

Different teams have different infrastructure maturity. The right fix depends on your setup.

| Criteria | Bare-Metal + `--once` Loop | Docker Compose Ephemeral | Kubernetes + ARC |
|---|---|---|---|
| **Setup complexity** | Low (bash scripts) | Medium | High |
| **Memory leak elimination** | Yes | Yes | Yes |
| **Auto-scaling** | Manual | Limited | Native |
| **Cost overhead** | Minimal | Minimal | Moderate (control plane) |
| **Cold start time** | ~8-12 seconds | ~10-15 seconds | ~20-30 seconds |
| **Best for** | Small teams, <10 concurrent jobs | Medium teams, predictable load | Large orgs, variable/spiky load |
| **Failure recovery** | Manual restart scripts | Docker restart policies | Kubernetes self-healing |

The trade-off is clear. Bare-metal with `--once` scripts gets you 80% of the benefit with 20% of the complexity. Kubernetes gets you the full picture — auto-scaling, self-healing, resource quotas — but it's real infrastructure to maintain. Don't let "gold standard" become an excuse to over-engineer a two-runner setup.

For teams not ready for Kubernetes, the Docker Compose approach hits a sweet spot. Define a runner service with `restart: always`, use `--once` in the entrypoint, and Docker handles container recycling automatically. youngju.dev's hardening guide recommends this as the minimum viable configuration for any production self-hosted runner deployment in 2026.

---

## Memory Limits and Cgroup Configuration

Even with ephemeral runners, setting explicit memory limits matters. It's a safety net, not a nice-to-have.

In Docker, `--memory=4g --memory-swap=4g` prevents any single job from consuming host memory unbounded. In Kubernetes, `resources.limits.memory` on the runner pod achieves the same effect. Without limits, a runaway job on an ephemeral runner can still take down the host — and then you're dealing with an infrastructure outage, not just a failed pipeline.

Configuring `--oom-score-adj` appropriately also matters: if memory pressure does occur, you want the runner process killed before critical host services. This is the layer most teams skip until something expensive breaks.

---

## Three Scenarios Worth Walking Through

**Scenario 1: Small team, single runner VM.**
You're running one VM with a persistent runner container. Jobs fail randomly every few days. Update your container entrypoint to use `--once`, add a simple restart loop or use `docker run --restart=always`. Estimated implementation time: 2 hours. Expected outcome: memory-related failures drop to zero.

**Scenario 2: Mid-size org, Docker Compose runner fleet.**
You've got 5-10 runner containers defined in a Compose file. Memory accumulation is gradual but real — runners degrade after 48-72 hours of operation. Migrate to ephemeral mode per container, add `--memory` limits per service definition, and set up basic Prometheus plus cAdvisor monitoring to catch remaining anomalies. This is the configuration youngju.dev describes as production-ready for teams handling 500-2,000 CI jobs per day.

**Scenario 3: Large org, 50+ concurrent runners, variable load.**
Persistent runners are costing you real money in failed jobs and engineering time. Kubernetes with ARC is the right call here. OneUptime's guide walks through the full ARC setup, including horizontal pod autoscaling tied to queue depth. Expect 3-5 days of migration work — but auto-scaling, zero memory leak incidents, and declarative configuration pay back quickly at this scale.

One thing worth watching: GitHub is reportedly working on runner lifecycle improvements in their 2026 roadmap, including better process isolation between jobs. If that ships, persistent runners may become viable again for some workloads. Until it does, ephemeral is the only production-safe pattern.

---

## Conclusion

The fix isn't a hotfix. It's an architectural decision.

Persistent runner containers accumulate memory across jobs — this is a structural limitation of the runner agent design, not a configuration bug you can tweak away. The `--once` flag plus container recycling eliminates the leak entirely, regardless of orchestration layer. Kubernetes plus ARC is the right call for large-scale deployments; Docker Compose ephemeral mode is sufficient for most mid-size teams. And memory limits via cgroups are non-negotiable even with ephemeral runners — they're your last line of defense when a job goes sideways.

Over the next 6-12 months, expect Actions Runner Controller to mature further with better queue-based scaling triggers and tighter GitHub API integration. GitHub's own hosted runners are also expanding large-runner tiers, which may reduce self-hosted demand for some teams. But for air-gapped environments and ML workloads, self-hosted isn't going anywhere.

If your runners are crashing on memory, the fix is one flag and a restart policy. Ship it this week.

---

*What's your current runner setup — persistent or ephemeral? If you're still running persistent containers in production, what's been the main blocker to migrating?*

## References

1. [GitHub Actions Self-Hosted Runner: Large-Scale Operations and Security Hardening Guide | Chaos and O](https://www.youngju.dev/blog/devops/2026-03-05-devops-github-actions-self-hosted-runner-ops.en)
2. [GitHub Actions running out of memory – HyperEnv for GitHub Actions Runner](https://hyperenv.com/blog/github-actions-running-out-of-memory/)
3. [How to Set Up GitHub Actions Self-Hosted Runners with Auto-Scaling on Kubernetes](https://oneuptime.com/blog/post/2026-02-09-github-actions-self-hosted-runners-k8s/view)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
