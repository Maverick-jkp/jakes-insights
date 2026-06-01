---
title: "GitHub Actions Self-Hosted Runner OOM Killed Fix on Ubuntu 22.04"
date: 2026-05-29T22:11:30+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "React"]
description: "GitHub Actions self-hosted runner getting OOM killed on Ubuntu 22.04? Fix silent Docker memory limit crashes before they kill your 2 AM CI pipeline."
image: "/images/20260529-github-actions-selfhosted-runn.webp"
technologies: ["React", "Docker", "AWS", "GitHub Actions", "Linux"]
faq:
  - question: "GitHub Actions self-hosted runner Docker memory limit OOM killed fix ubuntu 22.04"
    answer: "Fixing OOM kills on GitHub Actions self-hosted runners running Docker on Ubuntu 22.04 requires changes at three layers: the Docker daemon config, the runner service limits, and kernel/cgroup settings. Ubuntu 22.04 uses cgroup v2 by default, which requires explicit kernel parameter adjustments to allow Docker to enforce memory limits correctly. Without these changes, Docker containers don't automatically inherit memory limits from the runner process, causing silent job termination."
  - question: "why does my GitHub Actions self-hosted runner keep getting killed with no error"
    answer: "A job that dies with just 'Killed' in the logs and no stack trace is almost always terminated by the Linux OOM killer, which ends processes without warning when the system runs out of RAM. Self-hosted runners don't have automatic resource caps like GitHub-hosted runners do, so memory governance is entirely your responsibility. This is especially common when multiple jobs run concurrently on the same host or when Docker-in-Docker workflows consume more memory than expected."
  - question: "how to fix GitHub Actions self-hosted runner Docker memory limit OOM killed fix ubuntu 22.04 cgroup v2"
    answer: "Ubuntu 22.04 ships with cgroup v2 as the default hierarchy, which changes how Docker enforces memory limits compared to older Ubuntu versions running cgroup v1. To fix OOM kills, you need to explicitly configure kernel parameters so Docker can properly apply '--memory' flags within the cgroup v2 structure. Running Docker 20.10.x or newer is also required, as older versions did not handle the cgroup v2 transition reliably."
  - question: "self-hosted runner EC2 t3.medium running out of memory during Docker builds"
    answer: "EC2 t3.medium instances with 4 GB of RAM are particularly vulnerable to OOM conditions when running concurrent Docker builds through GitHub Actions self-hosted runners. Without explicit resource constraints configured at the runner and Docker daemon level, parallel jobs can consume 100% of available RAM within minutes. Adding memory limits to the Docker daemon config and setting service-level constraints on the runner process are the primary mitigations."
  - question: "does switching to self-hosted runners on EC2 save money compared to GitHub hosted runners"
    answer: "Self-hosted runners on EC2 reserved instances can reduce CI costs by 40-60% compared to GitHub-hosted runners, which bill per minute of usage. However, the cost savings come with the trade-off that resource governance, including memory limits and OOM protection, becomes entirely your responsibility. Teams that don't configure explicit memory constraints on their self-hosted runners often encounter unexpected job failures that can offset the operational savings."
---

Your CI pipeline dies at 2 AM. The logs say `Killed`. No stack trace. No warning. Just a dead job and a confused on-call engineer staring at a failure they didn't know they had.

This is one of the most silently destructive failure modes in modern CI infrastructure — and it's getting worse as Docker-in-Docker workflows grow heavier.

**Quick orientation:**

- The Linux OOM killer doesn't ask permission — it terminates processes when RAM is exhausted, and your runner is almost always the target
- Ubuntu 22.04 ships with `cgroup v2` by default, which changes how Docker enforces memory limits compared to older setups
- Self-hosted runners on AWS EC2 (or any fixed-memory VMs) are especially exposed when multiple jobs share the same host
- The fix isn't one setting — it's a layered approach across Docker, the runner service, and the OS itself

> **Key Takeaways**
> - GitHub Actions self-hosted runners running Docker workloads on Ubuntu 22.04 face OOM kills because Docker containers don't inherit memory limits from the runner process automatically.
> - Ubuntu 22.04's default cgroup v2 hierarchy requires explicit kernel parameter adjustments to allow Docker to enforce `--memory` flags correctly.
> - According to a 2026 post by OneUptime, runners configured without explicit resource constraints regularly consume 100% of available RAM during parallel job execution.
> - The Elvis Gitau analysis on Medium documents that EC2 t3.medium instances (4 GB RAM) running untuned GitHub Actions runners hit OOM conditions within 8–12 minutes of concurrent Docker builds.
> - A complete fix requires changes at three layers: Docker daemon config, runner service limits, and kernel/cgroup settings.

---

## Why Self-Hosted Runners Have a Memory Problem

GitHub-hosted runners come with managed resource caps. Self-hosted runners don't. That's the entire trade-off — you get flexibility and cost savings, but resource governance falls on you completely.

The OOM problem accelerated as teams moved toward heavier workloads: multi-stage Docker builds, large test matrices, ML model training pipelines. A 2024–2025 shift toward self-hosted runners on EC2 for cost reduction — GitHub-hosted runners bill per-minute, while EC2 reserved instances can cut that cost by 40–60% according to AWS pricing data — meant more teams were suddenly responsible for memory management they'd never thought about before.

Ubuntu 22.04 added a specific wrinkle. It fully adopted **cgroup v2** (the unified hierarchy), replacing the older cgroup v1 structure. Docker versions below 20.10.x didn't handle this transition gracefully — memory limits set via `docker run --memory` sometimes failed to propagate correctly. Even on Docker 24.x (current in 2026), the interaction between the runner's process limits and Docker's internal cgroup management requires explicit configuration.

The Elvis Gitau analysis on Medium is one of the cleaner write-ups on this: EC2 t3.medium instances with 4 GB RAM, running three concurrent GitHub Actions jobs that each spawn Docker containers, would routinely exhaust memory within minutes. The OOM killer targets the runner process itself — which means the job dies silently, GitHub marks it as failed, and nothing in the logs tells you *why*.

---

## Main Analysis

### Why the OOM Killer Targets Your Runner First

The Linux OOM killer scores processes by memory usage and "oom_score_adj". The GitHub Actions runner binary (`Runner.Worker`) is a large .NET process. When Docker containers it spawns start consuming RAM, the kernel's accounting attributes that memory to the runner's process tree. High RSS, no explicit protection, and the runner becomes the highest-scoring kill candidate.

On Ubuntu 22.04 specifically, the default `systemd` unit for the runner service sets no `MemoryLimit`. That means the runner competes for RAM on equal footing with everything else on the host. Add three parallel Docker builds and you've got a race to the floor.

The fix is direct: add `MemoryMax` and `MemorySwapMax` to the runner's systemd unit:

```ini
[Service]
MemoryMax=3G
MemorySwapMax=0
OOMScoreAdjust=-500
```

Setting `OOMScoreAdjust=-500` tells the kernel to deprioritize the runner process as an OOM kill target — giving Docker containers (which you can kill more gracefully) a higher score instead.

### Docker Daemon Configuration on cgroup v2

This is where Ubuntu 22.04 diverges from older setups. Docker needs `cgroupdriver=systemd` and `cgroupns=host` to work correctly with the unified cgroup v2 hierarchy. Without this, `--memory` limits in your `docker run` commands or `docker-compose` files don't actually constrain container memory at the kernel level.

Edit `/etc/docker/daemon.json`:

```json
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "default-shm-size": "128m",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Then restart Docker: `sudo systemctl restart docker`.

The LeoTheLegion guide (2025) recommends verifying cgroup v2 is active with `mount | grep cgroup2` before assuming limits will apply. If you're on a kernel below 5.15 — Ubuntu 22.04 ships 5.15 LTS — some edge-case cgroup behaviors differ.

### Kernel Parameters and Swap Configuration

Two kernel parameters matter here.

First, `vm.overcommit_memory`. The default (`0`) lets the kernel optimistically grant memory allocations. For CI workloads with bursty Docker builds, setting it to `2` (strict mode) prevents allocations that exceed available RAM plus swap. Add to `/etc/sysctl.conf`:

```
vm.overcommit_memory=2
vm.overcommit_ratio=80
```

Second, swap. The OneUptime 2026 setup guide recommends configuring at least 2 GB of swap on instances with 4–8 GB RAM. This isn't a performance solution — swap is slow — but it gives the OOM killer a buffer and prevents hard kills during transient memory spikes. Create a swap file:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

Add to `/etc/fstab` for persistence.

### Comparison: Fix Approaches Side by Side

| Approach | Complexity | OOM Prevention | Affects Performance | Persists Across Reboots |
|---|---|---|---|---|
| systemd `MemoryMax` + `OOMScoreAdjust` | Low | High | Minimal | Yes (with drop-in file) |
| Docker daemon `cgroupdriver=systemd` | Low | Medium | None | Yes |
| `vm.overcommit_memory=2` | Low | Medium | Minor (some alloc failures) | Yes (sysctl.conf) |
| Add 2 GB swap | Low | Medium (buffer) | Degrades under heavy swap | Yes (fstab) |
| Per-job `docker run --memory` flags | Medium | High (per container) | None | Per-workflow change |
| Upgrade instance size | None (infra change) | High | Positive | Yes |

The cleanest fix combines the first two rows — systemd limits plus correct cgroup driver — and adds swap as a safety net. Kernel overcommit tuning is worth applying on dedicated CI hosts but skip it on shared machines where other services have different memory profiles.

Per-job `--memory` flags in your workflow YAML give the most granular control but require updating every workflow file. Practical for teams with a handful of pipelines. Doesn't scale to 50+ repos.

---

## Three Scenarios, Three Fixes

**Scenario 1 — Single EC2 t3.medium (4 GB), parallel matrix builds.**
The Elvis Gitau analysis on Medium documents this exact setup hitting OOM within 8–12 minutes. Apply the systemd drop-in file first (roughly 30 minutes of work), add swap, then set `cgroupdriver=systemd`. That's the minimum viable fix before considering an instance upgrade.

**Scenario 2 — Self-hosted runner pool, Docker-in-Docker builds.**
Docker-in-Docker (DinD) doubles memory pressure — the outer Docker daemon and inner daemon both consume RAM. The OneUptime 2026 guide recommends `--privileged` mode with explicit `--memory` flags on the DinD container itself. Set `--memory=2g --memory-swap=2g` on the inner daemon container. Without this, the inner daemon inherits no limits at all.

**Scenario 3 — Ubuntu 22.04 fresh runner setup (new deployment).**
Don't wait for OOM kills to happen. The LeoTheLegion 2025 setup guide recommends baking the daemon.json config, swap file, and sysctl settings into your AMI or cloud-init script. Reactive fixes cost more than proactive configuration. A 45-minute upfront setup eliminates an entire class of 2 AM incidents.

This approach can fail when teams use shared hosts for both CI and production workloads — setting `vm.overcommit_memory=2` in that context can cause legitimate application allocations to fail. Know your host's role before applying OS-level tuning.

---

## Conclusion

The GitHub Actions self-hosted runner OOM killed problem on Ubuntu 22.04 is fundamentally a configuration gap, not a platform bug. Linux, Docker, and GitHub's runner all behave correctly — they just don't protect you from yourself.

**Key fixes to apply now:**

- Add `MemoryMax` and `OOMScoreAdjust` to the runner's systemd unit
- Set `cgroupdriver=systemd` in `/etc/docker/daemon.json`
- Configure 2 GB swap on instances under 8 GB RAM
- Tune `vm.overcommit_memory=2` on dedicated CI hosts only
- Use explicit `--memory` flags on Docker-in-Docker workloads

Looking ahead 6–12 months: Docker's containerd migration (progressing through 2026) will shift some of this configuration surface. Containerd handles cgroup integration differently and may simplify the daemon.json requirements. Watch the Docker 27.x release notes for cgroup v2 handling changes.

The one concrete action to take today: check your runner's systemd unit with `systemctl cat github-actions-runner` and confirm `MemoryMax` is set. If it's not there, that's your next 30 minutes of work.

What's your current instance size for self-hosted runners, and are you running matrix builds in parallel? The answer changes which fix matters most.

## References

1. [How to Set Up a Self-Hosted GitHub Actions Runner on Ubuntu](https://oneuptime.com/blog/post/2026-01-07-ubuntu-github-actions-runner/view)
2. [Self-Hosted GitHub Actions Runners on AWS EC2: Solving Memory and Disk Space Challenges | by ELVIS G](https://medium.com/@elvisgitau10/self-hosted-github-actions-runners-on-aws-ec2-solving-memory-and-disk-space-challenges-9c3299de9d2c)
3. [Use Docker to Set Up a Self-Hosted GitHub Actions Runner in 10 Minutes — LeoTheLegion](https://leothelegion.net/2025/07/28/use-docker-to-set-up-self-hosted-github-actions-runner-in-10-minutes/)


---

*Photo by [Ferenc Almasi](https://unsplash.com/@flowforfrank) on [Unsplash](https://unsplash.com/photos/a-computer-screen-with-a-bunch-of-buttons-on-it--FHIdRVGets)*
