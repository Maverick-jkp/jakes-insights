---
title: "GitHub Actions Self-Hosted Runner Docker ARM64 M2 Mac Memory Leak Fix"
date: 2026-05-02T20:06:58+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Node.js"]
description: "Fix the GitHub Actions self-hosted runner memory leak on Docker ARM64 M2 Mac before silent failures stall your CI queue indefinitely."
image: "/images/20260502-github-actions-selfhosted-runn.webp"
technologies: ["Node.js", "Docker", "Kubernetes", "GitHub Actions", "Linux"]
faq:
  - question: "github actions self-hosted runner docker arm64 M2 Mac memory leak fix"
    answer: "The fix for this memory leak involves three parts: enforcing cgroup v2, setting explicit memory limits in Kubernetes manifests, and adding ARC pod cleanup hooks. Without these changes, ephemeral runner pods get stuck in a Running state after OOM-kill events, blocking the CI queue indefinitely. This issue specifically affects the combination of GitHub Actions self-hosted runners, Docker, ARM64, and M2 Mac hardware running ARC in ephemeral mode."
  - question: "why do GitHub Actions self-hosted runners get stuck in Running state on M2 Mac"
    answer: "When an ephemeral runner pod hits the kernel's OOM killer on Docker ARM64, the container process dies but the ARC controller doesn't always receive a clean termination signal, leaving the pod stuck in Running state. This happens because Docker on macOS runs inside a Linux VM, causing memory reporting mismatches between the host OS and the container runtime on Apple Silicon. The stuck pod prevents the GitHub Actions job from dequeuing, and a new pod spins up repeating the cycle."
  - question: "how many stuck runner pods accumulate from ARC memory leak on ARM64"
    answer: "Community reports in the actions/actions-runner-controller GitHub issue #4155 document pod accumulation rates of 3 to 5 stuck pods per hour under moderate CI load. Teams running ephemeral runners without explicit resources.limits.memory in their Kubernetes manifests are most affected. This rate can quickly block an entire CI queue if not addressed with proper resource limits and cleanup hooks."
  - question: "what causes memory leak in GitHub Actions self-hosted runner docker arm64 M2 Mac memory leak fix setups"
    answer: "The root cause combines three factors: Docker's inaccurate memory accounting on Apple Silicon due to the macOS virtualization layer, gaps in ARC's ephemeral pod lifecycle management that miss unclean termination signals, and default resource limits that are too low for real ARM64 workloads. These individual mismatches compound into a recurring OOM-kill and stuck-pod cycle. The problem became widespread as M2 Mac minis grew popular as self-hosted runner hardware through 2023 and 2024."
  - question: "does cgroup v2 fix GitHub Actions runner OOM kill on Apple Silicon Docker"
    answer: "Enforcing cgroup v2 is one of three recommended steps to resolve OOM-kill issues with GitHub Actions runners on Docker and Apple Silicon. It improves memory accounting accuracy between the Docker VM and the container runtime, reducing the frequency of unexpected OOM events. However, cgroup v2 alone is not sufficient and should be combined with explicit Kubernetes memory limits and ARC pod cleanup hooks for a complete fix."
aliases:
  - "/tech/2026-05-02-github-actions-selfhosted-runner-docker-arm64-m2-m/"

---

Build pipelines die quietly. No fanfare, no obvious error — just a runner that stops responding, a pod stuck in `Running` state, and a CI queue that never clears. If you're running GitHub Actions self-hosted runners on Docker with ARM64 and an M2 Mac, that scenario is probably familiar. The memory leak pattern hitting this specific stack has become one of the more frustrating infrastructure problems in 2026, and the fix isn't where most teams look first.

> **Key Takeaways**
> - GitHub Actions self-hosted runners on Docker ARM64 (M2 Mac) exhibit a documented OOM-kill cycle where ephemeral runner pods get stuck in a `Running` state after memory exhaustion, blocking the CI queue indefinitely.
> - The root cause combines Docker's memory accounting on Apple Silicon, ARC (Actions Runner Controller) pod lifecycle management gaps, and default resource limits that don't reflect real ARM64 workloads.
> - Teams running ephemeral runners without explicit `resources.limits.memory` on Kubernetes manifests report pod accumulation rates of 3–5 stuck pods per hour under moderate CI load, per community reports in actions/actions-runner-controller issue #4155.
> - A targeted three-part fix — cgroup v2 enforcement, explicit memory limits, and ARC pod cleanup hooks — resolves the majority of stuck-runner incidents without a full infrastructure overhaul.

---

## 1. The Specific Problem Stack and Why It Surfaced Now

ARM64 adoption in CI didn't happen overnight. Apple's M1 release in late 2020 started the shift, but M2 Mac minis became the go-to self-hosted runner hardware through 2023–2024 because they're cheap, fast, and ARM-native. By early 2026, a significant portion of mid-sized engineering teams run their GitHub Actions self-hosted runner fleets on M2 hardware — either bare-metal or containerized via Docker with a Kubernetes layer managed by ARC.

The memory leak problem specifically emerges from this stack: **GitHub Actions self-hosted runner + Docker + ARM64 + M2 Mac + ARC ephemeral mode**. Each layer introduces a small mismatch. Together, they compound into a serious operational headache.

Docker on macOS has never had native kernel integration — it runs inside a Linux VM (HyperKit, then Apple Virtualization Framework). On ARM64, the interaction between Docker's memory reporting and macOS's memory compression means the host OS and the container runtime often disagree about how much memory a process is actually using. When an ephemeral runner pod hits the kernel's OOM killer, the container process dies, but the ARC controller doesn't always receive a clean termination signal. The pod sits in `Running` state. The GitHub Actions job registration never dequeues. A new pod spins up, potentially inheriting the same conditions, and the cycle repeats.

This became a documented pattern in ARC issue #4155 (actions/actions-runner-controller), where multiple teams reported EphemeralRunner pods accumulating in a stuck state after OOM events. The issue thread spans several months of reports from teams across different organization sizes, with the M2 Mac / ARM64 Docker combination appearing consistently as the trigger environment.

---

## 2. Root Cause Analysis: Three Compounding Factors

### cgroup v2 Memory Accounting Gaps on ARM64

Linux's cgroup v2 handles memory accounting differently from cgroup v1, and Docker's behavior on ARM64 under Apple Virtualization Framework doesn't always enforce limits the way you'd expect on x86_64 Linux. Specifically, `memory.swap.max` and `memory.high` thresholds can be ignored or misreported when the VM layer intercepts cgroup signals. The runner process grows past its soft limit before the hard limit triggers a clean shutdown — and by then, it's an OOM kill, not a graceful exit.

The practical result: a runner allocated 4GB in your Kubernetes manifest might consume 6GB before anything stops it, because the enforcement chain breaks down at the virtualization boundary.

### ARC Ephemeral Pod Lifecycle — The Missing Cleanup Hook

ARC's ephemeral runner model is built around a clean exit path: job finishes → runner deregisters → pod terminates → ARC reconciles. OOM kills break step two. The runner process dies without deregistering from the GitHub API, which means ARC's controller sees a pod it believes is still active. GitHub's API still shows a registered runner. Nothing triggers pod deletion.

Community reports in issue #4155 put the stuck pod accumulation rate at roughly 3–5 pods per hour under active CI load — enough to exhaust a small runner fleet within a few hours if left unaddressed.

### Default Resource Limits Don't Reflect ARM64 Workload Reality

Most ARC deployment templates still ship with resource limits tuned for x86_64 CI workloads. A typical default of `memory: 2Gi` per runner is inadequate for modern build workloads — especially Node.js, Rust, or JVM builds — on ARM64, where toolchain memory profiles differ meaningfully from x86_64 equivalents. Teams copy the template, deploy, and don't discover the mismatch until runners start dying under real load.

This isn't always obvious upfront. The same build that runs fine on a hosted x86_64 runner can quietly overconsume memory on ARM64 due to differences in how compilers and runtimes allocate working memory on the architecture.

---

## 3. The Fix: Three Layers, Applied in Order

### Layer 1 — Enforce cgroup v2 Hard Limits at the Docker Level

Add explicit cgroup enforcement to your Docker daemon config on the M2 host:

```json
{
  "default-runtime": "runc",
  "exec-opts": ["native.cgroupdriver=cgroupfs"],
  "memory": "6g",
  "memory-swap": "6g"
}
```

Set `memory-swap` equal to `memory` to disable swap entirely. This forces the OOM killer to act deterministically rather than letting swap buffer overruns mask real usage. Without this, the virtualization layer can absorb overruns silently until the process is well past any meaningful limit.

### Layer 2 — Set Explicit Resource Limits in ARC Runner Manifests

In your `EphemeralRunnerSet` spec, define hard limits that reflect actual workload needs:

```yaml
spec:
  ephemeralRunnerSpec:
    spec:
      containers:
        - name: runner
          resources:
            requests:
              memory: "3Gi"
              cpu: "2"
            limits:
              memory: "5Gi"
              cpu: "4"
```

The gap between `requests` and `limits` gives Kubernetes scheduling flexibility without allowing unbounded growth. Tune these against your actual build profiles — run three representative jobs and measure before setting final values. Template defaults are a starting point, not a recommendation.

### Layer 3 — Add a Forced Pod Cleanup Sidecar or CronJob

OOM kills bypass the graceful deregistration path, so a cleanup mechanism is non-negotiable. A simple Kubernetes `CronJob` running every 5 minutes — querying for pods in `Running` state older than your maximum job duration (e.g., 45 minutes) and force-deleting them — covers the gap:

```bash
kubectl get pods -n actions-runner \
  --field-selector=status.phase=Running \
  -o json | jq '.items[] | select(.metadata.creationTimestamp < "AGE_THRESHOLD")' \
  | kubectl delete -f -
```

Pair this with a GitHub Actions webhook-based runner deregistration script to clean the API side. ARC issue #4155 contributors confirmed this combination stops the pod accumulation cycle in most cases.

### Mitigation Approaches: Comparison

| Approach | Stops OOM Kill | Cleans Stuck Pods | Complexity | Recommended |
|---|---|---|---|---|
| cgroup v2 hard limits only | Partially | No | Low | As first step |
| ARC manifest resource limits | Yes | No | Low | Always |
| Cleanup CronJob | No | Yes | Medium | Yes |
| Full ARC upgrade + fix PR | Yes | Yes | High | When available |
| Switch to Linux x86 runners | Yes | Yes | High | Last resort |

The cgroup fix and manifest limits together stop new stuck pods from forming. The CronJob handles the backlog. Waiting on an upstream ARC patch is viable if you're not under active operational pressure — but as of May 2026, the fix hasn't landed in a stable ARC release.

This approach can fail when your build workloads vary dramatically in memory demand across jobs. If a single outlier job consumes 2–3x the memory of a typical build, static limits won't save you — you'll need per-job resource overrides or dedicated runner pools for memory-intensive pipelines.

---

## 4. Practical Implications: Who Fixes This When, and How

For teams running M2 Mac mini fleets as self-hosted runners right now, the priority order is clear: manifest limits first (20 minutes of work, immediate impact), cgroup config second (requires Docker restart, causes brief runner downtime), cleanup CronJob third (set it and forget it).

Don't wait for the "right" time. If your CI queue is already backing up, stuck pods are probably the reason — not job volume.

**Near-term (next 4–8 weeks):** The ARC maintainers have acknowledged the lifecycle gap in issue #4155. Watch for a point release that adds OOM-kill detection to the controller reconciliation loop. When it ships, the CronJob workaround becomes redundant — but the manifest limits and cgroup config remain best practice regardless.

**Medium-term (next 3–6 months):** Docker's ARM64 support on macOS continues improving with each release cycle. Docker Desktop 4.x (2026 releases) has incrementally tightened cgroup enforcement on Apple Silicon. The memory accounting gap described here may narrow without explicit user intervention — but don't count on it. Explicit limits are always safer than relying on runtime defaults.

**One open question worth tracking:** Whether GitHub's hosted ARM64 runners (now available in beta for some plan tiers) make self-hosted M2 Mac fleets obsolete for most teams. If hosted ARM64 capacity scales through 2026, the operational cost of maintaining this stack may outweigh the performance advantage. That calculus depends entirely on your build volume and budget.

---

## 5. Conclusion: Operational Discipline Beats Waiting for Upstream

The fix here isn't a single patch — it's three layers of operational hygiene applied to a stack that ships with inadequate defaults. The core issue is documented, reproducible, and fixable today without waiting for ARC or Docker to release anything.

**Key insights to carry forward:**

- OOM kills break ARC's ephemeral runner lifecycle, creating stuck pods that block CI queues.
- cgroup v2 enforcement on Apple Silicon requires explicit configuration — the defaults are unreliable.
- Manifest resource limits should always reflect real workload profiles, not template defaults.
- A cleanup CronJob is a low-effort safety net that pays for itself the first time it fires.

The next 6–12 months will likely bring upstream fixes to ARC's pod lifecycle management and improved Docker cgroup enforcement on ARM64. Until then, the three-layer approach above is the production-ready answer. Apply it in order, measure the impact, and adjust resource limits as your build workloads evolve.

What's your current runner fleet setup — M2 bare-metal, Docker, or something else? The fix path changes depending on where you're running ARC.

## References

1. [EphemeralRunner and its pods left stuck Running after runner OOMKILL · Issue #4155 · actions/actions](https://github.com/actions/actions-runner-controller/issues/4155)
2. [GitHub Actions running out of memory – HyperEnv for GitHub Actions Runner](https://hyperenv.com/blog/github-actions-running-out-of-memory/)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
