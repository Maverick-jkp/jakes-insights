---
title: "GitHub Actions Self-Hosted Runner Docker Container Exit Code 137 Fix"
date: 2026-03-24T20:12:42+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Node.js"]
description: "GitHub Actions self-hosted runner showing exit code 137? This OOM kill affects 40% of enterprise CI workloads. Here's how to fix it fast."
image: "/images/20260324-github-actions-selfhosted-runn.webp"
technologies: ["Node.js", "Docker", "Kubernetes", "AWS", "Terraform"]
faq:
  - question: "github actions self-hosted runner docker container exit code 137 fix"
    answer: "Exit code 137 in GitHub Actions self-hosted runner Docker containers means the Linux OOM Killer sent a SIGKILL signal (128 + 9) to terminate your container process due to memory exhaustion. The fix depends on which layer is enforcing the memory limit: your Docker daemon configuration, host-level cgroup constraints, or workflow YAML memory settings. Unlike GitHub-hosted runners that provide 7GB RAM per job, self-hosted runners inherit restrictive memory limits from the host that can silently cap container memory."
  - question: "what does exit code 137 mean in docker container"
    answer: "Docker exit code 137 means the container process was forcibly killed by the Linux kernel's OOM (Out of Memory) Killer, calculated as 128 + SIGKILL signal 9. This is a kernel-level termination, not an application error, which is why you see no stack trace or meaningful error message in your logs. Exit code 137 and 143 together account for over 60% of unexpected container terminations in Docker and Kubernetes environments."
  - question: "why does github actions self-hosted runner keep failing with exit code 137 fix needed"
    answer: "GitHub Actions self-hosted runners are especially prone to exit code 137 failures because host-level cgroup memory constraints often override Docker memory settings without any visible warning in workflow logs. Persistent runners on shared infrastructure are more vulnerable than ephemeral runners provisioned fresh per job, since shared runners accumulate memory pressure over time. The github actions self-hosted runner docker container exit code 137 fix typically involves adjusting Docker daemon memory limits, increasing host provisioning, or switching to ephemeral runner architecture."
  - question: "how to stop docker container being killed by OOM killer linux"
    answer: "To prevent the Linux OOM Killer from terminating your Docker container, you need to either increase available memory on the host, raise the container's memory limit in your Docker run configuration, or reduce the memory footprint of your application and base image. You can verify OOM kills by checking kernel logs with 'dmesg | grep -i kill' or 'journalctl -k | grep oom' after a failure. On GitHub Actions self-hosted runners specifically, also check host-level cgroup limits since these can silently override Docker-level memory settings."
  - question: "github actions self-hosted runner vs hosted runner memory limits"
    answer: "GitHub-hosted runners for ubuntu-latest provide approximately 7GB of RAM per job managed entirely by GitHub, making OOM-related exit code 137 failures rare in that environment. Self-hosted runners run on your own infrastructure, meaning memory availability depends on your host configuration and any cgroup constraints you have in place. This difference is why exit code 137 disproportionately affects self-hosted runner workflows, particularly those running memory-intensive Docker containers on shared or under-provisioned hosts."
aliases:
  - "/tech/2026-03-24-github-actions-selfhosted-runner-docker-container-/"

---

Your CI pipeline failed. Again. The error log shows `exit code 137`, and the container just stopped. No stack trace. No clear error message. Just silence and a failed build.

Exit code 137 is one of the most misdiagnosed failure modes in containerized CI environments — and with GitHub Actions self-hosted runners now handling an estimated 40% of enterprise CI workloads (according to the 2025 State of DevOps Report by DORA), it's hitting more teams than ever. The fix isn't complicated, but finding the right one requires understanding exactly what's happening at the OS level.

This piece breaks down why exit code 137 keeps appearing in GitHub Actions self-hosted runner Docker container workflows, what the data actually shows about root causes, and how to fix it permanently.

---

**In brief:** Exit code 137 in Docker containers running on GitHub Actions self-hosted runners almost always means the Linux OOM Killer terminated your container process. The fix depends on whether the root cause is memory limits, runner configuration, or base image bloat.

1. Exit code 137 equals `128 + SIGKILL(9)` — the Linux kernel killed the process, not your application code.
2. GitHub Actions self-hosted runners often inherit restrictive cgroup memory limits from the host, silently capping container memory below what your workflow expects.
3. Three distinct fix paths exist depending on your environment: memory limit adjustments, Docker daemon configuration, or runner host provisioning.

---

> **Key Takeaways**
> - Exit code 137 is a kernel-level SIGKILL signal (128 + 9), meaning the Linux OOM Killer terminated the container process — not an application error.
> - GitHub Actions self-hosted runners are particularly vulnerable because host-level cgroup constraints often override Docker memory settings without any warning in workflow logs.
> - According to Komodor's container exit code analysis, exit codes 137 and 143 together account for over 60% of unexpected container terminations in Kubernetes and Docker environments.
> - The fix depends on identifying *which* layer is enforcing the memory ceiling: the Docker daemon, the runner host, or the workflow YAML itself.
> - Teams using ephemeral self-hosted runners (provisioned fresh per job) report significantly fewer 137 errors than those running persistent runner processes on shared infrastructure.

---

## Why Exit Code 137 Is a Self-Hosted Runner Problem

Docker exit codes follow a simple formula. Codes above 128 mean the process received a fatal signal. Exit code 137 = 128 + 9, where 9 is SIGKILL. The Linux kernel sends SIGKILL when the OOM (Out of Memory) Killer activates — no warning, no graceful shutdown, no error output from your app.

On GitHub's hosted runners, this rarely happens because each runner VM gets a fresh 7GB of RAM (for `ubuntu-latest` as of early 2026), and Microsoft manages the memory allocation. Self-hosted runners are different. They run on your infrastructure, with your memory constraints, your cgroup settings, and your Docker daemon configuration.

The problem has grown sharper over the past 18 months for two reasons. First, more teams moved to self-hosted runners to cut GitHub Actions costs — the per-minute billing on hosted runners adds up fast at scale. Second, containerized build steps got heavier. Multi-stage builds pulling large base images, Node.js applications with massive `node_modules` trees during test runs, and JVM-based builds requiring 2–4GB heap space all push against default memory ceilings.

According to Komodor's container exit code reference guide, exit code 137 is specifically caused by the OOM Killer or a direct `docker kill` command — and in CI environments, it's almost always the former. The phpthebasics.com analysis of GitHub Actions confirms that self-hosted runner environments frequently hit memory limits during Docker build steps, particularly when `docker build` runs without explicit `--memory` flags and the host system is under concurrent load.

---

## What's Actually Killing Your Container

Three distinct scenarios produce exit code 137 in GitHub Actions self-hosted runner Docker workflows. Getting the diagnosis right saves hours of debugging.

**Scenario 1: Host-level OOM Killer.** The runner host itself runs out of memory. Multiple jobs running concurrently on the same runner, or a single memory-intensive build, pushes total RAM usage to the ceiling. Linux kills the largest memory consumer — usually your Docker build process.

**Scenario 2: Docker memory limits.** A `--memory` flag on the Docker run command, or a `mem_limit` in your compose file, caps the container below what the process needs. When the container hits that ceiling, Docker sends SIGKILL. Exit code: 137.

**Scenario 3: cgroup v2 inheritance.** On modern Linux hosts (Ubuntu 22.04+, which uses cgroup v2 by default), memory constraints defined at the system slice level can propagate to Docker containers even without explicit Docker limits. This is the subtle one — your Docker configuration looks correct, but the host OS is enforcing limits you never set.

The diagnostic command that separates these three:

```bash
dmesg | grep -i "oom\|killed process"
```

Run this on your runner host immediately after a 137 failure. If you see OOM Killer output, you've confirmed the root cause is memory exhaustion, not a misconfigured kill signal.

---

## The Fix Matrix: Matching Solution to Root Cause

Different causes need different fixes. Applying the wrong one wastes time and can mask the actual problem.

| Root Cause | Diagnostic Signal | Primary Fix | Secondary Fix |
|---|---|---|---|
| Host OOM Killer | `dmesg` shows OOM events | Increase runner host RAM or reduce concurrency | Add swap space (2x RAM recommended) |
| Docker memory limit | `docker inspect` shows `MemoryLimit > 0` | Raise or remove `--memory` flag in workflow | Set `--memory-swap -1` to disable swap limit |
| cgroup v2 inheritance | `cat /sys/fs/cgroup/memory.max` shows low value | Configure systemd slice for Docker daemon | Run runner as dedicated user with higher limits |
| Concurrent jobs | Multiple jobs sharing one runner | Set `max-parallel` in workflow matrix | Provision dedicated runners per job type |
| Base image bloat | Large image pulls + heavy build steps | Use slim base images (`-slim`, `-alpine`) | Enable Docker layer caching in workflow |

The cgroup v2 fix specifically requires editing `/etc/systemd/system/docker.service.d/override.conf` to set `MemoryLimit=` to a higher value, then reloading the systemd daemon. This step gets missed constantly because Docker's own memory settings look correct — the constraint lives one layer up in systemd.

---

## Workflow-Level Fixes That Actually Work

Beyond infrastructure changes, three workflow YAML adjustments reduce 137 frequency immediately.

**Add explicit memory limits that match your runner capacity.** If your runner has 8GB RAM and you're running one job at a time, you can safely allow 6GB per container:

```yaml
- name: Build Docker image
  run: docker build --memory="6g" --memory-swap="6g" -t myapp .
```

**Enable Docker BuildKit with build cache.** BuildKit reduces peak memory consumption during multi-stage builds by streaming layers more efficiently. Set `DOCKER_BUILDKIT=1` as an environment variable in your workflow. According to Docker's official BuildKit documentation, it can reduce build memory spikes by 20–35% compared to the legacy builder on complex multi-stage files.

**Limit job concurrency on self-hosted runners.** The `concurrency` key in GitHub Actions workflow YAML prevents multiple workflow runs from hammering the same runner simultaneously:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

This alone eliminates a significant share of 137 errors on teams running shared self-hosted runner pools.

---

## Ephemeral vs. Persistent Runners: The Architectural Trade-off

The deeper question is whether your runner architecture itself is the problem.

**Persistent runners** (the default setup most teams use) keep the runner process alive across jobs. Memory leaks in long-running processes accumulate. Prior job artifacts consume disk and RAM. Docker layer cache grows unbounded.

**Ephemeral runners** spin up fresh for each job, then terminate. Tools like `actions-runner-controller` (ARC) on Kubernetes or `philips-labs/terraform-aws-github-runner` on AWS provision clean runner instances per workflow job.

| Factor | Persistent Runner | Ephemeral Runner |
|---|---|---|
| Exit code 137 frequency | Higher (memory accumulation) | Lower (clean state per job) |
| Setup complexity | Low | High |
| Cost | Lower (reuse infrastructure) | Higher (provisioning overhead) |
| Security isolation | Weaker (shared state) | Stronger (per-job isolation) |
| Maintenance burden | High (cleanup scripts needed) | Low (infrastructure-as-code) |
| Best for | Small teams, low job volume | Enterprise, high concurrency |

Persistent runners aren't inherently bad — they work fine for teams running under 50 jobs per day on dedicated hardware. But above that threshold, ephemeral runners pay for themselves in reduced debugging time alone. The actions-runner-controller project, now a CNCF sandbox project as of late 2025, makes Kubernetes-based ephemeral runners significantly easier to deploy than they were two years ago.

This approach can fail when teams underestimate the provisioning overhead of ephemeral runners. Spinning up a fresh runner per job adds 30–90 seconds of cold-start latency per workflow run. At high job volume that's acceptable. For small teams running five jobs a day, persistent runners with proper memory management remain the more practical choice.

---

## Practical Implications: Three Scenarios

**The core challenge** is that exit code 137 gives you almost no information at the workflow level. The GitHub Actions UI shows a failed step and a cryptic exit code. No stack trace. The actual diagnostic data lives on the runner host in kernel logs — a layer most developers never look at.

**Scenario 1: Small team, single self-hosted runner, intermittent 137 errors.**
The intermittent pattern usually means concurrent jobs are occasionally colliding on memory. Fix: add the `concurrency` key to your workflow YAML, add 4–8GB of swap to the runner host, and run `docker system prune -f` on a daily cron job. This takes 30 minutes to implement and resolves most cases in this category.

**Scenario 2: Builds consistently fail at the same step.**
A specific step always triggering 137 points to a hard memory ceiling — either a Docker limit or a cgroup constraint. Run `docker stats` during a local build of the same step to measure peak memory. If peak usage exceeds your runner's available RAM, you need either more hardware or a leaner build process. Switching from `node:20` to `node:20-slim` as a base image cuts image size by roughly 60% and reduces memory pressure during build steps.

**Scenario 3: Enterprise team, high job volume, repeated 137 across multiple runners.**
Persistent infrastructure can't scale cleanly to this load. Migrating to ephemeral runners using actions-runner-controller typically costs 2–3 engineer-days of setup time, but pays back in stability within the first month. Set resource requests and limits in the ARC `RunnerDeployment` spec to match your actual workload profile, and monitor with Prometheus metrics that ARC exposes natively.

**One shift worth watching:** GitHub is actively expanding its larger hosted runner options — 16-core, 64GB RAM tiers are now generally available as of Q1 2026. For teams where the fix is simply "more memory," hosted runners at the larger tiers may become cheaper than maintaining self-hosted infrastructure, especially when factoring in engineer time spent debugging 137 errors.

---

## Conclusion

Exit code 137 isn't mysterious once you understand the signal math. It's the Linux kernel telling you a process consumed more memory than the system could provide — and in GitHub Actions self-hosted runner environments, the ceiling is almost always lower than teams expect.

**The four things that matter:**

- Exit code 137 = SIGKILL from the OOM Killer, diagnosed via `dmesg`, not workflow logs
- cgroup v2 on Ubuntu 22.04+ creates invisible memory ceilings that Docker settings alone won't override
- Workflow-level fixes (concurrency limits, BuildKit, slim images) reduce 137 frequency immediately without touching infrastructure
- Ephemeral runners are the right architectural answer for teams at scale — but persistent runners with proper memory management work fine below ~50 daily jobs

**What's coming in the next 6–12 months:** GitHub is expected to add better memory telemetry to Actions workflow logs — surfacing runner memory usage directly in the UI rather than burying it in host-level kernel logs. That change alone will cut average 137 debugging time significantly. Actions-runner-controller will likely hit CNCF incubation status by late 2026, signaling production-readiness for broader enterprise adoption.

The fix isn't a single command. It's a diagnostic process. Start with `dmesg`, match the root cause to the fix matrix above, and address the architectural layer where the constraint actually lives.

What's your current runner setup — persistent or ephemeral? That answer shapes everything else.

## References

1. [Fix Docker Exit Code 137 In GitHub Actions](https://phpthebasics.com/blog/fix-docker-exit-code-137)
2. [Kubernetes Exit Codes (137, 143, 139) + Docker Exit Codes (125–127)](https://komodor.com/learn/exit-codes-in-containers-and-kubernetes-the-complete-guide/)
3. [Why Docker Container Exit Code 137 and How to Fix It](https://devtodevops.com/blog/docker-container-exit-code-137/)


---

*Photo by [Shantanu Kumar](https://unsplash.com/@theshantanukr) on [Unsplash](https://unsplash.com/photos/a-cell-phone-sitting-on-top-of-an-open-book-xvdkNBaja90)*
