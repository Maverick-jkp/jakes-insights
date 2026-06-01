---
title: "GitHub Actions Self-Hosted Runner Docker Container Exit Code 137 OOM Fix"
date: 2026-05-19T21:56:13+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Python"]
description: "GitHub Actions self-hosted runner showing exit code 137? The Linux kernel OOM killer terminated your Docker container. Here's how to fix it."
image: "/images/20260519-github-actions-selfhosted-runn.webp"
technologies: ["Python", "Node.js", "Docker", "GitHub Actions", "Linux"]
faq:
  - question: "what does exit code 137 mean in docker"
    answer: "Docker exit code 137 means the container was forcefully killed by the Linux kernel's OOM (Out of Memory) killer, calculated as 128 + signal 9 (SIGKILL). This is not a Docker bug or application crash — it means the host system ran out of available RAM and swap space. The kernel selects the most memory-intensive process to terminate, and Docker containers are frequent targets."
  - question: "github actions self-hosted runner docker container exit code 137 OOM fix"
    answer: "Fixing exit code 137 OOM kills on GitHub Actions self-hosted runners requires a layered approach: setting hard memory limits on Docker containers, configuring swap space on the host, and reducing runner job concurrency so fewer jobs compete for the same RAM. The root cause is typically multiple concurrent jobs sharing host memory without per-job limits enforced by default."
  - question: "why does github actions self-hosted runner docker container exit code 137 OOM fix keep coming up even with no config errors"
    answer: "Even with no configuration errors, exit code 137 can appear because GitHub's default runner setup allows multiple jobs to run in parallel on the same host, each spinning up its own Docker container. On a machine with 8GB RAM running three concurrent jobs, each job may only have around 2.5GB available after OS overhead — not enough for memory-intensive workloads like ML training or large Docker builds. GitHub's community confirmed this affects standard ubuntu-24.04 runners as well."
  - question: "how to limit memory for docker container in github actions"
    answer: "You can limit memory for a Docker container in GitHub Actions by passing the --memory flag in your Docker run command (e.g., --memory=4g) or by setting resource limits in your Docker Compose configuration. For self-hosted runners, also consider reducing the MAX_CONCURRENT_JOBS setting on the runner daemon to prevent multiple jobs from exhausting host memory simultaneously."
  - question: "how to stop OOM killer from killing docker containers on linux"
    answer: "To prevent the Linux OOM killer from terminating Docker containers, you should add swap space to give the kernel more memory headroom before it resorts to killing processes. Additionally, setting explicit memory limits per container ensures the OOM killer has a predictable boundary to work with, and monitoring tools like dmesg or /var/log/syslog can confirm whether OOM kills are actually occurring."
---

Exit code 137. Two numbers that've killed more CI pipelines than any misconfigured YAML ever will. If your GitHub Actions self-hosted runner is dropping Docker containers with this code, the diagnosis is almost always the same: the Linux kernel OOM killer stepped in and terminated your process because memory ran out.

This isn't a Docker bug. It's not a GitHub Actions quirk. It's your infrastructure running out of memory, and the fix requires understanding exactly where the pressure comes from.

In 2026, this problem is getting *worse* before it gets better. Self-hosted runner adoption has climbed sharply as teams move heavier workloads — ML model training, large test suites, multi-stage Docker builds — onto their own infrastructure to cut GitHub-hosted runner costs. More workload, same memory ceiling. The math doesn't work.

What follows covers: what exit code 137 actually means at the kernel level, why self-hosted runners are uniquely exposed to OOM conditions, four concrete fixes ranked by effort and reliability, and a comparison table to help you pick the right approach for your stack.

---

**In brief:** Docker container exit code 137 is a SIGKILL signal issued by the Linux OOM killer when available memory is exhausted. GitHub Actions self-hosted runners running Docker workloads are particularly vulnerable because multiple concurrent jobs share host memory without hard per-job limits by default.

Three things to know immediately:

1. Exit code 137 = 128 + 9 (SIGKILL), meaning the process was killed externally — not a crash, a forced termination by the kernel.
2. GitHub's community discussion thread #169191 confirmed sporadic exit-137 failures on `ubuntu-24.04` runners, affecting teams with no apparent configuration errors.
3. The fix isn't one thing — it's a layered approach: memory limits, swap configuration, and runner concurrency controls.

---

## Why Exit Code 137 Keeps Appearing in GitHub Actions Pipelines

Exit code 137 has a precise definition: `128 + signal number`. Signal 9 is SIGKILL. So `128 + 9 = 137`. When the Linux kernel's OOM killer fires, it sends SIGKILL to whichever process it judges most expendable. Docker containers running as child processes are frequent targets.

The kernel OOM killer activates when physical RAM plus swap space drops near zero. At that point, it scores running processes by memory footprint and kills the highest scorer. Your Docker container — potentially holding a Node.js build, a JVM, or a Python test runner — is a large, obvious target.

Self-hosted runners amplify this risk for a specific reason: **job concurrency**. GitHub's default runner configuration allows multiple jobs to run in parallel on the same host. Each job spins up its own Docker container. On a 4-vCPU, 8GB RAM machine running three concurrent jobs, each job effectively gets ~2.5GB — before the host OS and runner daemon take their cut. A single `docker build` step for a non-trivial application can exceed that easily.

GitHub's community discussion thread #169191 (opened in early 2026) documented runners on `ubuntu-24.04` failing with exit 137 despite having no explicit memory-intensive steps. The culprit in many cases: memory fragmentation and swap being disabled by default on newer Ubuntu images. Without swap as a pressure valve, the OOM killer fires faster.

---

## The Kernel OOM Killer Isn't a Bug — It's a Safety Net

The OOM killer exists because the alternative is system-wide freeze. When Linux enables memory overcommit (the default on most distributions), processes can allocate more virtual memory than physically exists — betting that not all of it will be used simultaneously. When that bet fails and actual usage spikes, the kernel has to act.

Docker containers don't run in isolated memory namespaces by default. They share the host's memory pool. So a container that balloons to 3GB on an 8GB host, while two other containers and the OS itself are also resident, can push the system past its limit.

According to the OneUptime engineering blog (February 2026), the most common trigger in CI environments is multi-stage Docker builds where intermediate layers are kept in memory simultaneously. A `docker build` for a production image can temporarily require 2–3x the final image size in working memory.

## Why Self-Hosted Runners Are a Special Case

GitHub-hosted runners give each job a dedicated VM. Memory is isolated by definition. Self-hosted runners don't have this guarantee — you're responsible for the host, and by default, GitHub Actions will schedule concurrent jobs up to the runner's `max_parallel` value.

The `actions/runner` daemon itself consumes roughly 200–400MB. Add Docker daemon overhead (~300MB), and you've already spent ~700MB before a single workflow step runs. On an 8GB machine with three concurrent jobs, the real per-job budget is closer to 2GB, not 2.6GB.

That's why teams running seemingly identical workloads see intermittent exit 137 failures. It's not deterministic — it depends entirely on which jobs happen to overlap in time.

## Four Fixes, Ranked by Reliability

**Fix 1: Set explicit Docker memory limits (`--memory` flag)**

```bash
docker run --memory="2g" --memory-swap="4g" your-image
```

This tells the kernel to enforce a hard cap. The container gets OOM-killed at 2GB *before* the host runs out. Controlled failure beats random failure. In GitHub Actions workflows, pass these flags via `docker run` steps or configure them in your `docker-compose.yml` with `mem_limit`.

**Fix 2: Enable swap on the runner host**

Many Ubuntu 22.04/24.04 images ship with swap disabled. Adding even 4GB of swap gives the OOM killer room to breathe before it acts:

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

Add to `/etc/fstab` for persistence. According to phpthebasics.com's analysis, enabling swap reduced exit 137 occurrences by a significant margin for teams running memory-intensive test suites — though swap is slower than RAM and not a substitute for adequate provisioning.

**Fix 3: Limit runner concurrency**

In your runner's `.env` or `config.yml`, set:

```
RUNNER_MAX_CONCURRENT_JOBS=1
```

One job at a time. Blunt, but effective. For workloads that can't be parallelized safely, this is often the right call.

**Fix 4: Upgrade host memory and monitor with `cgroups`**

If your workflow genuinely needs 4GB+, the honest fix is more RAM. Pair that with cgroup v2 memory accounting to track per-container usage in real time:

```bash
systemd-cgtop
```

This shows live memory usage by cgroup, which maps directly to Docker containers.

## Comparison: Approaches to Fixing Exit Code 137

| Approach | Memory Safety | Performance Impact | Setup Complexity | Best For |
|---|---|---|---|---|
| Docker `--memory` limits | High | None | Low | All self-hosted setups |
| Enable swap | Medium | Moderate (I/O) | Low | Light-to-medium workloads |
| Limit runner concurrency | High | Significant (slower CI) | Very low | Small teams, single runner |
| Increase host RAM | High | None | Medium (reprovisioning) | Heavy, sustained workloads |
| cgroup v2 monitoring | Diagnostic only | None | Medium | Debugging + prevention |

No single approach dominates. For most teams, the practical answer is **Docker memory limits + swap enabled** as a baseline, then monitoring with cgroup tools to decide whether a hardware upgrade makes sense.

Setting `--memory` limits won't prevent OOM kills entirely — it'll make them deterministic and scoped to one container rather than random across your host. That's a meaningful improvement. You'll see a clear error in the job log instead of a silent exit 137 mid-build.

---

## Practical Implications: Three Scenarios

**Scenario 1: Intermittent failures on a single self-hosted runner**

The runner is handling 3–4 concurrent jobs on an 8GB machine. Jobs fail randomly, not reproducibly. Enable swap immediately — that's a 30-minute change — then add `--memory` flags to the longest-running Docker steps. This combination covers the two most common causes without requiring reprovisioning.

**Scenario 2: Large Docker builds consistently hitting 137**

A multi-stage build process for a monorepo is failing every time past a certain build stage. This is a deterministic memory ceiling, not a concurrency problem. Profile the build with `docker stats` to find the peak memory step, then either split the build into smaller stages or upgrade the runner host to 16GB. The `--memory-swap` flag can serve as a bridge while you decide.

**Scenario 3: GitHub-hosted runner migration to self-hosted**

Teams moving from GitHub-hosted runners to self-hosted to cut costs — a common 2026 pattern as GitHub raised hosted-runner pricing tiers — often hit exit 137 for the first time. GitHub-hosted runners silently provided memory isolation they never had to think about. Treat self-hosted runners like production infrastructure from day one: define memory budgets per job type, set runner concurrency limits, and add swap. The default configuration is not production-ready.

---

## Conclusion & Future Outlook

The exit code 137 OOM problem isn't going away. The shift toward self-hosted infrastructure in 2026 means more teams will hit it, not fewer.

> **Key Takeaways**
> - Exit code 137 is the kernel OOM killer — not a Docker or GitHub bug
> - Self-hosted runners sharing host memory across concurrent jobs are structurally exposed to this failure mode
> - Docker `--memory` limits combined with swap enabled is the minimum viable fix for most setups
> - cgroup v2 monitoring is the right long-term tool for understanding memory pressure before it becomes an incident

Over the next 6–12 months, expect GitHub to add better per-job memory reporting in the Actions UI — there are open feature requests gaining traction in their community forums. Container-native CI platforms like Depot and Namespace are already building memory-aware scheduling by default, which may push GitHub to respond faster.

The action to take right now: check whether swap is enabled on your runner hosts. Run `swapon --show`. If it returns nothing, you're running without a safety net. That's a 20-minute fix that'll prevent your next 2 a.m. on-call page.

What memory limits are you setting per job? If the answer is none, that's the first thing worth changing.

## References

1. [Fix Docker Exit Code 137 In GitHub Actions - Trending News](https://phpthebasics.com/blog/fix-docker-exit-code-137)
2. [Jobs randomly fail with exit code 137 on ubuntu-24.04 runner · community · Discussion #169191](https://github.com/orgs/community/discussions/169191)
3. [How to Fix Docker Container Immediately Exiting with Code 137](https://oneuptime.com/blog/post/2026-02-08-how-to-fix-docker-container-immediately-exiting-with-code-137/view)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
