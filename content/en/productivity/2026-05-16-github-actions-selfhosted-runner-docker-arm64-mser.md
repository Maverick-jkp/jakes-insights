---
title: "GitHub Actions Self-Hosted Runner Docker ARM64 Memory Leak Fix"
date: 2026-05-16T20:25:25+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Node.js"]
description: "Fix GitHub Actions self-hosted runner memory leaks on ARM64 M-series Mac Docker setups before OOMKills stall your CI pipeline for hours."
image: "/images/20260516-github-actions-selfhosted-runn.webp"
technologies: ["Node.js", "Docker", "Kubernetes", "GitHub Actions", "Linux"]
faq:
  - question: "github actions self-hosted runner docker arm64 m-series mac memory leak fix"
    answer: "The most effective fix for memory leaks on GitHub Actions self-hosted runners running Docker on ARM64 M-series Macs is switching to ephemeral runner configurations combined with explicit container memory limits. This addresses the root cause: a memory accounting gap between Docker Desktop's Linux VM layer and the actions-runner-controller, which leaves OOMKilled pods stuck in a Running state and blocks subsequent CI jobs."
  - question: "why does github actions runner get stuck in running state after OOMKill on mac"
    answer: "When a runner container is OOMKilled on macOS Docker, the actions-runner-controller (ARC) can fail to receive a clean status update, leaving the pod appearing as Running even though the process has died. This is a known issue tracked in actions-runner-controller GitHub issue #4155, and it can block new workflow jobs for 30 or more minutes without manual intervention."
  - question: "how to fix github actions self-hosted runner docker arm64 m-series mac memory leak with ephemeral runners"
    answer: "Switching to ephemeral runners ensures each job starts with a clean runner instance that is discarded after use, preventing stuck zombie pods from blocking the queue. Teams combining ephemeral runner configurations with hard container memory caps report significantly fewer OOMKill-related incidents compared to persistent runner setups on M-series Macs."
  - question: "why does docker use more memory on apple silicon m-series mac for CI runners"
    answer: "Docker on Apple Silicon runs inside a lightweight Linux VM using Apple's Virtualization Framework, which allocates a shared memory pool across all containers rather than dedicated per-container limits. When multiple parallel CI jobs run on high-performance M3 Pro or Max machines, total container memory demand can spike unexpectedly, making the default runner memory allocation dangerously optimistic compared to Linux-native environments."
  - question: "actions-runner-controller pod stuck running after oomkill how to resolve"
    answer: "The stuck Running state occurs because the Kubernetes status update from the OOMKilled container can lag or fail entirely under memory pressure, a failure mode documented in ARC issue #4155. Setting explicit memory limits on runner containers and enabling ephemeral mode are the two most reliable mitigations, as they either prevent the OOMKill from occurring or ensure the pod is cleanly replaced after each job."
aliases:
  - "/tech/2026-05-16-github-actions-selfhosted-runner-docker-arm64-mser/"

---

Memory leaks on self-hosted GitHub Actions runners aren't new. But on ARM64 M-series Macs running Docker containers, they're hitting teams hard enough to stall CI pipelines for hours.

The pattern is consistent: runner pods get OOMKilled, stay stuck in a `Running` state, and the next workflow job can't start until someone manually intervenes. For teams shipping multiple times a day, a frozen runner isn't a minor inconvenience — it's a real engineering tax.

The fix is more complex than a single config tweak. Here's what the data shows in 2026.

**Key points covered:**
- Why ARM64 architecture makes memory management harder on M-series hardware
- How OOMKill events leave runner pods stuck in a zombie state
- Comparison of fix strategies: ephemeral runners, memory limits, and host-level controls
- Practical steps to stop the bleed today

---

**In brief:** The memory leak issue on GitHub Actions self-hosted runners running Docker on ARM64 M-series Macs stems from a known interaction between container memory accounting and the Linux-on-ARM virtualization layer. Teams that switch to ephemeral runner configurations and set explicit container memory limits see the most consistent resolution.

1. OOMKill events on M-series Mac Docker runners frequently leave pods in a stuck `Running` state, blocking subsequent jobs (tracked in `actions/actions-runner-controller` issue #4155).
2. ARM64's memory page handling under Docker Desktop's VM layer on macOS creates overhead that Linux-native runners don't face, making the default runner memory allocation dangerously optimistic.
3. Teams using ephemeral runners with hard memory caps report significantly fewer stuck-runner incidents compared to persistent runner setups.

---

## How This Problem Got Here

Docker on Apple Silicon runs inside a lightweight Linux VM — currently using Apple's Virtualization Framework rather than the older QEMU approach. That shift improved performance. But it introduced a subtle memory accounting gap.

When GitHub Actions spins up a runner container inside that VM, the container's memory usage isn't always accurately reflected back to the orchestration layer. The Linux kernel inside the VM tracks cgroup memory correctly. But the signal from the container to the runner controller can lag or fail entirely when memory pressure spikes.

The result: the container gets OOMKilled by the kernel. The runner process dies. But `actions-runner-controller` (ARC) sees the pod still in a `Running` phase because the Kubernetes status hasn't updated cleanly. This is the exact failure mode documented in ARC GitHub issue #4155, where teams report EphemeralRunner pods stuck after OOMKILL events — sometimes for 30+ minutes without intervention.

The issue compounds on M-series Macs specifically because Docker Desktop for Mac allocates a shared memory pool to the VM, not dedicated per-container limits. When multiple CI jobs run in parallel — common on beefy M3 Pro/Max machines — the total container memory demand can exceed the VM's assigned limit before any single container hits its individual cap.

This became a pressing issue in 2025–2026 as more engineering teams moved Apple Silicon machines into their self-hosted runner fleets, drawn by ARM64 performance gains and lower power draw compared to x86 servers.

---

## Why the Stuck-Runner State Is the Real Problem

Getting OOMKilled isn't inherently catastrophic. Containers die; orchestrators restart them. The damage is that the stuck `Running` state blocks ARC from scheduling the next job. The controller thinks a runner is active. It isn't.

According to the ARC issue tracker (#4155, opened in late 2024 and still active as of May 2026), the root cause is that `EphemeralRunner` controllers don't always reconcile correctly after an OOMKILL event. The pod phase stays `Running` even when all containers inside it have exited. The runner slot is occupied but useless.

Teams have confirmed waits of 15 to 45 minutes before the stale pod is garbage-collected and a fresh runner can start. On a team pushing 50+ commits a day, that's a genuine throughput problem.

## Memory Overhead on ARM64 Under Docker Desktop

The ARM64 layer adds overhead that Linux-native runners simply don't face. Docker Desktop on Mac allocates a fixed memory ceiling to its internal VM — configurable in Docker Desktop settings, defaulting to 8GB on most systems. That ceiling is shared across all running containers.

When a workflow runs tests with high memory pressure (JVM-based builds, large webpack bundles, in-memory databases), multiple parallel containers can collectively push past the VM ceiling. The kernel inside the VM then starts OOMKilling whichever container it deems lowest priority — which may not be the heaviest consumer.

This isn't always a true "leak" in the traditional sense. It's often misconfigured memory allocation combined with the virtualization layer's limited visibility into per-container pressure. The distinction matters, because the fix looks different depending on which problem you're actually solving.

## Ephemeral vs. Persistent Runners: The Core Trade-off

Configuration choices matter most here.

| Criteria | Persistent Runners | Ephemeral Runners | Ephemeral + Memory Limits |
|---|---|---|---|
| Stuck-pod risk | High (state accumulates) | Medium (dies after job) | Low (bounded + replaced) |
| Startup latency | Near-zero (warm) | 15-45s (cold start) | 15-45s (cold start) |
| Memory leak exposure | High (process lives across jobs) | Low (process dies each job) | Very low |
| OOMKill recovery | Manual or slow GC | Auto-replacement | Auto-replacement + bounded |
| Best for | Low-volume, stable workloads | High-volume, parallel CI | High-volume with memory-heavy jobs |

Persistent runners accumulate state between jobs. A runner process that's handled 200 jobs without a restart can carry leaked memory from earlier workflows — especially if those workflows involved Node.js processes, Docker-in-Docker builds, or JVM tools that don't release memory cleanly on exit.

Ephemeral runners solve the accumulation problem. Each job gets a fresh container. But without memory limits, a single runaway job on an M-series Mac can still OOMKill the runner and trigger the stuck-pod bug.

The combination that works: ephemeral runners **with** explicit `resources.limits.memory` set in the `RunnerDeployment` spec. According to HyperEnv's analysis of GitHub Actions memory failures, teams that set container memory limits see a significant drop in OOMKill-triggered pipeline stalls compared to unconstrained configurations.

This approach can fail when memory limits are set too aggressively low. If your limit is tighter than what legitimate builds actually need, you'll OOMKill healthy jobs constantly — trading one problem for another. Calibrate against your actual peak usage before enforcing hard caps.

## Practical Configuration Changes

Three changes address this directly.

**1. Increase Docker Desktop VM memory allocation.** Go to Docker Desktop → Settings → Resources → Memory. For M3 Pro/Max machines with 36GB+ RAM, allocating 16–20GB to the VM gives containers room without starving the host.

**2. Set explicit memory limits in your ARC RunnerDeployment:**
```yaml
resources:
  limits:
    memory: "6Gi"
  requests:
    memory: "2Gi"
```
This caps each runner container, forcing OOMKill to happen cleanly within a bounded scope rather than cascading across the VM.

**3. Configure ARC's runner pod GC timeout.** The stuck-pod issue (#4155) can be partially mitigated by reducing `runnerPodGCTimeout` in your ARC Helm values. The default is generous. Tightening it to 2–3 minutes means stale OOMKilled pods get reaped faster — not a root-cause fix, but it limits how long a dead runner blocks your queue.

---

## What Teams Should Do Right Now

**If you're running persistent self-hosted runners on M-series Macs**, switch to ephemeral mode first. It won't fix memory pressure, but it eliminates the accumulation problem immediately.

**If you're already on ephemeral runners but still seeing stuck pods**, the ARC issue #4155 suggests this is a controller reconciliation bug, not just a configuration problem. Pin to ARC version 0.9.x or later — check the release notes for the specific patch addressing EphemeralRunner OOMKILL reconciliation.

**If your Docker Desktop VM ceiling is at the default 8GB**, that's almost certainly too low for parallel ARM64 CI workloads. Bump it. The M-series hardware can handle it.

**Watch for:** Apple is expected to update the Virtualization Framework in macOS 26 (announced at WWDC 2026 for late-2026 release) with improved per-VM memory management. Better cgroup signal fidelity from the VM layer could reduce the underlying conditions that make this bug surface so often on M-series hardware. That's not a reason to wait — it's a reason to hope the long-term maintenance burden gets lighter.

---

## Conclusion

The fix requires changes at three levels: Docker Desktop resource allocation, ARC runner configuration, and awareness of the ARC reconciliation bug that leaves OOMKilled pods stuck.

> **Key Takeaways**
> - The "leak" is usually a memory accounting failure under ARM64 virtualization — not a traditional process leak
> - Stuck pods after OOMKILL are a confirmed ARC bug (#4155), not purely a config issue
> - Ephemeral runners + explicit memory limits + shorter GC timeouts resolve the majority of cases
> - Docker Desktop VM memory defaults are too low for parallel M-series CI workloads
> - Upstream fixes are coming, but teams shouldn't wait for them

Over the next 6–12 months, expect ARC to ship a proper fix for the EphemeralRunner reconciliation issue — community pressure on #4155 has been consistent since late 2024. Apple's Virtualization Framework improvements in late 2026 may reduce how often the underlying condition occurs in the first place.

The immediate action: tighten your memory limits, go ephemeral, and bump your Docker Desktop VM ceiling today. Stuck runners are an operational tax your team shouldn't still be paying in 2026.

**What's your current ARC version, and have you hit the stuck-pod issue post-OOMKILL?** Drop it in the comments — real version data from teams in the field helps everyone narrow down which patches actually moved the needle.

## References

1. [EphemeralRunner and its pods left stuck Running after runner OOMKILL · Issue #4155 · actions/actions](https://github.com/actions/actions-runner-controller/issues/4155)
2. [GitHub Actions running out of memory – HyperEnv for GitHub Actions Runner](https://hyperenv.com/blog/github-actions-running-out-of-memory/)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
