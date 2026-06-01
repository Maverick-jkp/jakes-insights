---
title: "GitHub Actions Self-Hosted Runner Docker Memory Limit cgroup v2 Ubuntu 24.04"
date: 2026-04-25T20:04:58+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Docker"]
description: "GitHub Actions self-hosted runners on Ubuntu 24.04 silently hang instead of crashing due to cgroup v2 changing how Docker enforces memory limits."
image: "/images/20260425-github-actions-selfhosted-runn.webp"
technologies: ["Docker", "Kubernetes", "AWS", "Azure", "GCP"]
faq:
  - question: "github actions self-hosted runner docker memory limit cgroup v2 ubuntu 24.04 silent hang fix"
    answer: "When running GitHub Actions self-hosted runners with Docker on Ubuntu 24.04, silent hangs occur because cgroup v2 attempts to reclaim file-backed pages before triggering an OOMKill, which can stall indefinitely under CI workloads. The fix requires either adjusting kernel boot parameters to revert to cgroup v1, modifying the Docker daemon configuration, or updating your runner controller depending on your stack. Teams using actions-runner-controller on Kubernetes are especially affected due to how pod memory limits interact with cgroup v2 page thresholds."
  - question: "why does docker container hang instead of OOMKill on ubuntu 24.04"
    answer: "On Ubuntu 24.04, Docker containers hang instead of receiving an OOMKill because cgroup v2 (enabled by default) unifies memory accounting to include file-backed page cache against a container's memory limit. When the limit is hit, the kernel attempts to reclaim those file-backed pages first, and if reclaim stalls — which commonly happens during Docker builds, npm installs, or large test fixture loading — the container freezes indefinitely. This is a kernel-level behavioral change, not a bug in Docker or GitHub Actions."
  - question: "github actions self-hosted runner docker memory limit cgroup v2 ubuntu 24.04 actions-runner-controller kubernetes"
    answer: "Teams running actions-runner-controller on Kubernetes with Ubuntu 24.04 nodes are disproportionately impacted by cgroup v2 memory limit changes because pod memory limits interact differently with the unified cgroup v2 memory controller. File-backed page cache now counts against container memory limits, and reclaim stalls under typical CI I/O patterns cause pods to hang indefinitely rather than being cleanly OOM killed. Resolving this requires updates to either the runner controller configuration or the underlying node's cgroup settings."
  - question: "ubuntu 22.04 vs ubuntu 24.04 cgroup version difference docker CI runners"
    answer: "Ubuntu 20.04 and 22.04 defaulted to cgroup v1 or hybrid mode, while Ubuntu 24.04 ships with pure cgroup v2 enabled by default as of its April 2024 release. This is a significant behavioral change for Docker-based CI runners because cgroup v1 applied memory limits more predictably, triggering clean OOMKills when containers exceeded their memory allocation. Teams migrating CI infrastructure to Ubuntu 24.04 in 2026 on AWS, GCP, or Azure will encounter this difference immediately on fresh VM provisioning."
  - question: "how to revert cgroup v2 to cgroup v1 ubuntu 24.04 docker"
    answer: "To revert Ubuntu 24.04 from cgroup v2 to cgroup v1, you can add the kernel boot parameter `systemd.unified_cgroup_hierarchy=0` to your GRUB configuration, which forces the system back to cgroup v1 mode. Alternatively, you can configure the Docker daemon to use a cgroupfs driver compatible with v1 behavior, or update your runner controller to handle cgroup v2 memory accounting correctly. The right approach depends on whether you control the host OS, are running in Kubernetes, or need a solution that doesn't require kernel-level changes."
---

Memory limits that silently hang instead of killing. Runners that freeze indefinitely. CI/CD pipelines that worked perfectly on Ubuntu 22.04 but collapse the moment you upgrade. If you're running GitHub Actions self-hosted runners with Docker on Ubuntu 24.04, you've likely already hit this wall.

This isn't a misconfiguration. It's a structural shift in how Linux manages memory — and it's catching teams off guard in 2026 as Ubuntu 24.04 becomes the default choice for new infrastructure.

**This analysis covers:**

- Why cgroup v2 changes the memory management contract between the kernel and Docker
- The specific failure mode: pod hangs vs. OOMKill, and why they're different problems
- How to configure GitHub Actions self-hosted runners correctly on Ubuntu 24.04
- Which mitigation approach fits which infrastructure setup

---

**In brief:** Ubuntu 24.04 ships with cgroup v2 as the default, which breaks the memory limit enforcement behavior that Docker and GitHub Actions runners relied on under cgroup v1. Teams migrating CI runners to Ubuntu 24.04 in 2026 face silent hangs instead of clean OOM kills unless they explicitly reconfigure their setup.

1. The root cause is a kernel-level change — not a Docker bug, not a GitHub Actions bug.
2. The fix requires either kernel boot parameter adjustments, Docker daemon configuration changes, or runner controller updates, depending on your stack.
3. Teams running `actions-runner-controller` on Kubernetes are disproportionately affected due to how pod memory limits interact with cgroup v2 file-backed page thresholds.

---

## The cgroup v2 Shift: What Changed and When

cgroup v1 and cgroup v2 aren't just version numbers. They represent fundamentally different approaches to resource accounting in the Linux kernel.

Under **cgroup v1**, memory limits applied to anonymous memory (heap, stack) and file-backed memory somewhat independently. Docker's `--memory` flag worked predictably: exceed the limit, get an OOMKill, job ends, runner picks up the next task. Teams built CI pipelines around this behavior without realizing it was a cgroup v1 assumption baked into their architecture.

**cgroup v2** unified the memory controller. File-backed page cache now counts against the container's memory limit. That sounds reasonable — until you see what happens when a container actually hits the limit. Instead of an immediate OOMKill, the kernel tries to reclaim file-backed pages first. If reclaim stalls — which it does under certain I/O patterns common in CI workloads like Docker build layers, npm installs, or large test fixtures — the container hangs indefinitely.

Ubuntu 20.04 and 22.04 both defaulted to **cgroup v1** (or hybrid mode). Ubuntu 24.04 ships with **pure cgroup v2 enabled by default** as of its April 2024 release. By early 2026, this is the standard for new VM provisioning on AWS, GCP, and Azure when selecting Ubuntu 24.04 LTS images.

The GitHub Actions `actions-runner-controller` project documented this specifically in issue [#4436](https://github.com/actions/actions-runner-controller/issues/4436): runner pods hang indefinitely on memory limit instead of OOMKilling due to cgroup v2 file-backed page thresholds. That issue remained open and actively discussed through early 2026, affecting teams running ARC (Actions Runner Controller) on Kubernetes clusters with Ubuntu 24.04 nodes.

---

## Why CI Workloads Are Especially Vulnerable

Docker image pulls, layer extraction, and build cache operations are all heavily file-backed. A 2 GB memory limit on a runner container sounds generous until a multi-stage Docker build starts staging layers. The kernel sees file-backed page cache filling the cgroup and begins reclaim. The reclaim doesn't complete fast enough. The runner stalls.

The failure is silent by default. No OOMKill event in `dmesg`. No clear error in the GitHub Actions job log. The job just stops responding. Depending on your runner timeout configuration, this can hold a runner occupied for six hours before GitHub's own job timeout fires.

This is worse than a crash. A crash fails fast and frees the runner. A hang burns your concurrency slots, delays other jobs, and produces logs that give no actionable signal whatsoever.

---

## The Three Fix Patterns

There are three documented approaches, each with real tradeoffs.

**Pattern 1: Revert to cgroup v1 via kernel boot parameter**

Add `systemd.unified_cgroup_hierarchy=0` to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`, then run `update-grub` and reboot. This forces the system back to cgroup v1 behavior.

It works. But it's a regression. You're trading cgroup v2 features — better memory pressure reporting, PSI metrics, improved container isolation — for compatibility. As the Linux ecosystem moves forward, this becomes harder to maintain and defend in infrastructure reviews.

**Pattern 2: Configure Docker daemon memory swap behavior**

Set `"memory-swap": -1` in `/etc/docker/daemon.json` to disable memory+swap limits, or explicitly configure `--memory-swappiness=0` on runner containers. This changes how the kernel handles reclaim pressure.

More targeted than reverting cgroup v2 entirely. It doesn't fix the underlying page cache accounting, but reduces stall frequency significantly in practice.

**Pattern 3: ARC-specific pod spec adjustments**

For teams using `actions-runner-controller`, the fix involves setting `resources.limits.memory` with matching `resources.requests.memory` values and configuring the runner pod's `ephemeral-storage` limits to account for file-backed workload pressure separately. According to the ARC issue tracker, some teams also had success setting `memory.oom.group` cgroup parameters at the pod level.

### Mitigation Comparison

| Approach | Complexity | Preserves cgroup v2 | Kubernetes Compatible | Maintenance Burden |
|---|---|---|---|---|
| Revert to cgroup v1 (kernel flag) | Low | ❌ No | ✅ Yes (node-level) | High |
| Docker daemon swap config | Medium | ✅ Yes | ✅ Yes | Low |
| ARC pod spec tuning | High | ✅ Yes | ✅ Native | Medium |
| Upgrade to Ubuntu 22.04 base | Low | ❌ No | ✅ Yes | High |

The Docker daemon swap config hits the best balance for most teams running standalone self-hosted runners. If you're on ARC/Kubernetes, the pod spec approach is worth the one-time configuration cost — it keeps you on the modern cgroup v2 path without sacrificing job reliability.

---

## What Teams Are Getting Wrong During Migration

According to the [Markaicode Ubuntu 24.04 runner setup guide](https://markaicode.com/github-actions-runners-ubuntu-24-04/) published in 2026, the most common mistake during runner provisioning is following Ubuntu 22.04 documentation verbatim. The runner software installs fine. Docker installs fine. Jobs run fine — until memory pressure hits.

Teams typically discover the problem two to four weeks post-migration, after workloads that happen to be memory-intensive — large monorepo builds, integration test suites with database containers, multi-service Docker Compose CI environments — start hanging.

The [OneUptime self-hosted runner guide](https://oneuptime.com/blog/post/2026-01-07-ubuntu-github-actions-runner/view) from January 2026 covers the Ubuntu 24.04 setup path and explicitly calls out the need to verify cgroup configuration before deploying runners to production. That step is absent from most older tutorials.

Three mistakes drive most incident reports:

- **No memory limit testing before production** — staging environments often have looser resource constraints that don't trigger the hang
- **Missing cgroup v2 verification** — `cat /sys/fs/cgroup/cgroup.controllers` tells you immediately whether you're on v2; most teams don't check
- **Runner timeout set too high** — a 6-hour GitHub job timeout turns a hang into a 6-hour concurrency block instead of a fast failure

This approach can also fail when teams have heterogeneous node pools — some Ubuntu 22.04, some 24.04 — without runner labels routing jobs to the right OS version. You get intermittent hangs that are nearly impossible to reproduce consistently, which makes diagnosis painful.

---

## What to Do Right Now

If you're provisioning new Ubuntu 24.04 runners, add cgroup verification to your runner setup script before anything else:

```bash
# Check cgroup version
stat -fc %T /sys/fs/cgroup/
# "cgroup2fs" = cgroup v2 active
```

Then decide your mitigation path based on your stack:

- **Standalone Docker runners**: Add `"memory-swap": -1` and `"default-ulimits": {"memlock": {"Hard": -1, "Name": "memlock", "Soft": -1}}` to `/etc/docker/daemon.json`
- **ARC on Kubernetes**: Align memory requests and limits in your runner scale set configuration; set explicit `ephemeral-storage` limits
- **Mixed fleet (22.04 + 24.04)**: Tag runners by OS version in your workflow files and route memory-intensive jobs to 22.04 nodes during migration

**Near-term (next 4–8 weeks):** Ubuntu 24.04 LTS adoption accelerates as 22.04's standard support window closes in April 2027. Teams still on 22.04 runners are effectively on a countdown clock. Getting the cgroup v2 configuration right now — not at migration deadline — is the difference between a planned change and an emergency.

**Medium-term (next 3–6 months):** The ARC project is tracking cgroup v2 compatibility improvements. Watch the `actions-runner-controller` GitHub releases. If the project ships a cgroup v2-aware memory management update, the pod spec workaround becomes optional — but the Docker daemon configuration guidance stays relevant for non-Kubernetes deployments regardless.

One open question worth tracking: whether GitHub's hosted runners will move to Ubuntu 24.04 as default before the end of 2026. The `ubuntu-latest` label currently maps to Ubuntu 22.04 per GitHub's runner image documentation — but that mapping has changed before without much warning. If it changes again, this cgroup v2 behavior stops being a self-hosted runner problem and becomes everyone's problem.

---

## Conclusion

The cgroup v2 memory limit issue on Ubuntu 24.04 isn't exotic. It's a predictable consequence of a kernel architecture change that the CI tooling ecosystem is still catching up to.

> **Key Takeaways**
> - Ubuntu 24.04's cgroup v2 default changes how Docker enforces memory limits — file-backed pages now count, reclaim stalls, and jobs hang silently with no clear error signal
> - The ARC-specific issue (#4436) confirms Kubernetes-based runners are disproportionately affected
> - Three viable fixes exist; Docker daemon swap configuration is the lowest-risk path for most teams
> - Verify cgroup version and configure Docker before deploying any Ubuntu 24.04 runner to production
> - This isn't always the answer for every team — mixed fleets and heterogeneous node pools require routing strategy alongside configuration changes

The teams that handle this well aren't the ones with the most complex infrastructure. They're the ones that verify their assumptions at each OS upgrade instead of carrying old configs forward and hoping nothing breaks.

The question worth answering before your next large CI migration lands in production: what's your current runner OS baseline, and have you actually validated cgroup behavior after any recent Ubuntu upgrades?

## References

1. [How to Set Up a Self-Hosted GitHub Actions Runner on Ubuntu](https://oneuptime.com/blog/post/2026-01-07-ubuntu-github-actions-runner/view)
2. [Runner pod hangs indefinitely on memory limit instead of OOMKilling (cgroup v2 file-backed page thra](https://github.com/actions/actions-runner-controller/issues/4436)
3. [Setting Up GitHub Actions Runners on Ubuntu 24.04: Self-Hosted CI/CD Guide | Markaicode](https://markaicode.com/github-actions-runners-ubuntu-24-04/)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
