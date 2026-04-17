---
title: "WSL2 Docker Desktop Memory Fix on Windows 11 with .wslconfig"
date: 2026-03-28T19:57:00+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "wsl2", "docker", "desktop", "PostgreSQL"]
description: "Fix WSL2 Docker Desktop memory leaks on Windows 11. Stop VmmemWSL from consuming 8GB+ RAM with a simple .wslconfig tweak that actually works."
image: "/images/20260328-wsl2-docker-desktop-memory-lea.webp"
technologies: ["Docker", "PostgreSQL", "Redis", "GitHub Actions", "Linux"]
faq:
  - question: "how to fix wsl2 docker desktop memory leak windows 11 .wslconfig optimization real fix"
    answer: "The real fix for the WSL2 Docker Desktop memory leak on Windows 11 is creating a .wslconfig file in your %USERPROFILE% folder with hard limits like memory=4GB and swap=2GB. This prevents WSL2 from consuming up to 50% of your total RAM by default, which is the root cause of VmmemWSL bloating in Task Manager. After saving the file, restart WSL2 with 'wsl --shutdown' for the changes to take effect."
  - question: "why is VmmemWSL using so much memory windows 11"
    answer: "VmmemWSL represents the entire WSL2 virtual machine's memory footprint, which balloons because the Linux kernel inside WSL2 aggressively caches disk I/O in RAM and Windows does not automatically reclaim that memory when the VM goes idle. Docker Desktop worsens this by running its Linux daemon directly inside WSL2, meaning every container, image pull, and build layer adds to the growing Linux page cache. On a 16GB machine, this can consume 6–9GB of RAM during normal development work."
  - question: "what should I put in .wslconfig to limit docker desktop memory usage"
    answer: "For a 16GB Windows 11 machine, setting memory=4GB and swap=2GB in your .wslconfig file is a widely recommended starting configuration that cuts Docker Desktop RAM consumption from 6–8GB down to 2–4GB. The .wslconfig file must be placed in your %USERPROFILE% directory (typically C:/Users/YourName) and requires a WSL restart to apply. You can adjust the memory value higher or lower depending on how many containers you typically run simultaneously."
  - question: "does docker desktop cause memory leak on windows 11 wsl2 backend"
    answer: "Docker Desktop does not have a traditional memory leak, but its use of the WSL2 backend by default since version 4.x causes persistent high memory usage through standard Linux page cache behavior that Windows never reclaims. This is a well-documented issue tracked in WSL2 GitHub issue #4166 with over 800 comments, and it affects every Windows 11 Docker user who has not explicitly configured .wslconfig limits. The wsl2 docker desktop memory leak windows 11 .wslconfig optimization real fix involves capping WSL2 memory allocation manually since no automatic reclamation occurs."
  - question: "how much memory does wsl2 use by default on windows 11"
    answer: "By default, WSL2 on Windows 11 can allocate up to 50% of your total system RAM with no automatic upper cap enforced unless you configure one yourself. On a 16GB machine that means WSL2 can claim up to 8GB for the VmmemWSL process, leaving the rest of your Windows applications competing for whatever remains. Microsoft's own documentation recommends using the .wslconfig file to set a memory ceiling appropriate for your workload."
---

Your Windows 11 machine is grinding to a halt. Task Manager shows `VmmemWSL` consuming 8GB of RAM. Docker Desktop is open, three containers are running, and the entire OS feels like it's wading through wet concrete. This isn't a hardware problem. It's a well-documented WSL2 memory allocation issue — and the fix is simpler than most Stack Overflow threads suggest.

> **Key Takeaways**
> - WSL2 allocates up to 50% of total system RAM by default, with no automatic reclamation when that memory goes idle — causing persistent `VmmemWSL` bloat on Windows 11.
> - The `.wslconfig` file in `%USERPROFILE%` gives you hard caps on memory, CPU, and swap. Microsoft documented this configuration in Windows 11 Build 22000 and later.
> - Setting `memory=4GB` and `swap=2GB` in `.wslconfig` cuts typical Docker Desktop RAM consumption from 6–8GB down to 2–4GB on a 16GB machine, according to multiple developer reports on DEV Community and DevOps.dev.
> - Docker Desktop's WSL2 backend has been the default since version 4.x — meaning every Windows 11 Docker user is exposed to this behavior unless they've explicitly configured limits.

---

## Why WSL2 Eats RAM and Never Gives It Back

WSL2 launched in 2020 as a genuine Linux kernel running inside a lightweight Hyper-V virtual machine. That was a massive step forward from WSL1's syscall translation layer. But the trade-off was memory management behavior inherited from traditional VMs.

On a 16GB Windows 11 machine, WSL2's default allocation ceiling sits at 8GB — half of total RAM, per Microsoft's WSL documentation. The deeper problem isn't the ceiling itself. It's that the Linux kernel inside WSL2 aggressively caches disk I/O in RAM (standard Linux behavior), and Windows doesn't reclaim that memory automatically when the VM goes idle.

Docker Desktop made this worse. Starting with Docker Desktop 4.x, Microsoft's WSL2 backend became the default over the older Hyper-V backend. Docker now runs its Linux daemon directly inside WSL2 distributions (`docker-desktop` and `docker-desktop-data`). Every image pull, every build layer, every running container contributes to the Linux page cache — which grows and stays grown.

According to a February 2026 analysis on OneUptime's engineering blog, Docker Desktop on a 16GB Windows 11 machine without configuration limits can consume 6–9GB through `VmmemWSL` alone during moderate development workloads. That leaves your actual Windows processes — Chrome, VS Code, everything else — competing for whatever's left.

The WSL2 GitHub issue tracker (specifically issue #4166, opened in 2020) has over 800 comments as of early 2026, making it one of the most-tracked memory complaints in the repository's history. Microsoft added `memory` capping via `.wslconfig` as the primary mitigation. But the default install gives you no cap at all.

---

## The Root Cause: Linux Page Cache + No Automatic Reclaim

The `VmmemWSL` process in Task Manager represents the entire WSL2 VM's memory footprint. It balloons for two reasons.

First, Docker image layers. Pulling a `node:20` image downloads roughly 1.1GB of compressed layers. Uncompressed, those layers land in the WSL2 filesystem and get cached by the Linux kernel. Pull three or four images during a workday and the cache swells fast.

Second, container build operations. Running `docker build` generates intermediate layers that the Docker daemon keeps in its build cache. According to Colin Williams' write-up on DEV Community, running `docker system prune` can free several gigabytes immediately — but the WSL2 VM doesn't release that memory back to Windows automatically afterward. The memory stays allocated to the VM even when empty.

The fix for immediate bloat: run `docker system prune -f` to clear unused containers, networks, and images. Then in a WSL2 terminal, run:

```bash
sudo sh -c "echo 3 > /proc/sys/vm/drop_caches"
```

This forces Linux to flush the page cache. But it's a bandage. The VM still hits the same ceiling on the next build cycle.

## The Real Fix: .wslconfig Hard Limits

The permanent solution lives in one file: `C:\Users\YourUsername\.wslconfig`.

Create or edit it with these settings:

```ini
[wsl2]
memory=4GB
swap=2GB
processors=4
```

Breaking this down:

- **`memory=4GB`** — caps the WSL2 VM at 4GB regardless of Linux page cache growth. On a 16GB machine, this leaves 12GB free for Windows processes.
- **`swap=2GB`** — gives WSL2 a swap file so container workloads don't crash when they hit the memory cap.
- **`processors=4`** — limits CPU core access, which also reduces build-induced memory spikes.

After saving, run `wsl --shutdown` from PowerShell and restart Docker Desktop. According to Worapon Asavanik's analysis on DevOps.dev, this configuration alone drops `VmmemWSL` from a sustained 6–8GB down to the configured cap — typically 3–4GB during active Docker use on a 16GB system.

One caveat worth knowing: if you're running memory-hungry containers — PostgreSQL with large datasets, Elasticsearch — set `memory=6GB` instead. 4GB is the right floor for typical web dev workloads, not a universal ceiling.

## WSL2 Backend vs. Hyper-V Backend vs. Configured WSL2

| Factor | WSL2 (unconfigured) | WSL2 + .wslconfig | Hyper-V backend |
|---|---|---|---|
| **Default RAM usage** | 6–9GB on 16GB system | 3–4GB (capped) | ~2GB (fixed allocation) |
| **Memory reclaim** | None automatic | None, but capped | Fixed, predictable |
| **Startup speed** | Fast (~10s) | Fast (~10s) | Slow (~30–45s) |
| **Docker performance** | Fast I/O via Linux fs | Fast I/O (same) | Slower (SMB filesystem) |
| **Volume mount speed** | Good (native Linux paths) | Good | Poor (Windows path mounting) |
| **Config complexity** | None required | One file, 3 lines | Docker Desktop settings UI |
| **Windows 11 support** | Default | Recommended | Deprecated in Docker 4.x |
| **Best for** | Throwaway VMs | Daily dev work | Legacy compatibility only |

The Hyper-V backend used to be the go-to recommendation for memory control — it let you set a fixed VM size directly in Docker Desktop's settings UI. But Docker deprecated that path with version 4.x on Windows 11, and I/O performance through Hyper-V's SMB volume mounting was noticeably slower for bind-mounted projects. The `.wslconfig` approach gives you the performance of the WSL2 backend with predictable memory behavior. It's the right call for anyone doing daily Docker development on Windows 11.

## The Extra Lever: WSL2 Memory Reclaim (Windows 11 22H2+)

Microsoft quietly added an `[experimental]` option in the `.wslconfig` spec for Windows 11 22H2 and later:

```ini
[experimental]
autoMemoryReclaim=gradual
```

This tells WSL2 to gradually release cached memory back to Windows when the VM is idle. The alternative value is `dropcache`, which reclaims more aggressively but can cause brief stalls during active work.

Combined with the hard `memory=` cap, `autoMemoryReclaim=gradual` is the closest thing to a complete solution currently available. It won't eliminate `VmmemWSL` spikes during builds, but it prevents the VM from holding onto 6GB at 2am when nothing's running. That distinction matters if you leave Docker Desktop open overnight.

---

## Three Scenarios Worth Knowing

**Scenario 1 — Memory pressure during builds.**
If your machine slows down mid-`docker build`, the immediate fix is the `.wslconfig` memory cap plus `docker system prune` as a weekly habit. Set a recurring reminder. Pruned caches mean the VM starts each week with actual headroom.

*Recommendation*: Set `memory=4GB` (8GB machine) or `memory=6GB` (16GB machine). Add `autoMemoryReclaim=gradual`. Run `docker system prune -f` every Monday morning.

**Scenario 2 — Running multiple services simultaneously.**
Postgres, Redis, and a Node API together can legitimately need 3–4GB. Capping at 4GB causes OOM kills inside containers. Don't blindly copy a config from a blog post — including this one.

*Recommendation*: Run `docker stats` during your heaviest workload. Take the peak RAM across all containers, add 1.5GB for Docker daemon overhead, and set `memory=` to that number. Keep `swap=2GB` as a safety net.

**Scenario 3 — CI/CD pipelines on a Windows 11 dev machine.**
Local CI builds — a GitHub Actions self-hosted runner, for example — can spike WSL2 to its unconfigured ceiling and leave it there for hours. Without `.wslconfig` limits, this starves everything else running simultaneously.

*Recommendation*: Set `processors=` to leave at least 2 cores for Windows, and use `memory=` to reserve at least 4GB for non-WSL processes. Consider scheduling `wsl --shutdown` via Task Scheduler during non-build windows.

---

## Where This Is Heading

The core findings are straightforward:

- **WSL2 doesn't reclaim memory by default.** Linux page cache grows, `VmmemWSL` bloats, and Windows feels the squeeze.
- **Docker Desktop's WSL2 backend makes this the default experience** for every Windows 11 developer since version 4.x.
- **The `.wslconfig` memory cap plus `autoMemoryReclaim=gradual`** is the complete solution available today — three lines of config that should've been the default years ago.
- **`docker system prune` isn't optional maintenance.** It's the other half of keeping the VM's actual working set small enough for the cap to matter.

Microsoft's WSL team has signaled continued investment in memory management through 2026. The `autoMemoryReclaim` feature is still marked `[experimental]`, but based on WSL GitHub activity it's likely to become a stable, default-on setting before the end of 2026. Docker Desktop's public roadmap also includes better memory telemetry in the Dashboard UI — which would surface this problem before it becomes critical, rather than after your machine is already grinding.

The one action worth taking today: create the `.wslconfig` file, add the three lines above, and run `wsl --shutdown`. That's 90 seconds of work to recover gigabytes of RAM permanently.

What's your current `VmmemWSL` baseline without any config — and what workload's driving it?

## References

1. [How to Configure Docker Desktop Memory and CPU Limits on Windows](https://oneuptime.com/blog/post/2026-02-08-how-to-configure-docker-desktop-memory-and-cpu-limits-on-windows/view)
2. [How to Reclaim Memory from Docker WSL - DEV Community](https://dev.to/colin-williams-dev/how-to-reclaim-memory-from-docker-wsl-2lkf)
3. [Docker Desktop Using Too Much Memory (VmmemWSL): Cause and Solution | by Worapon Asavanik | DevOps.d](https://blog.devops.dev/docker-desktop-using-too-much-memory-vmmemwsl-cause-and-solution-0a54998ab65a)


---

*Photo by [amt8u](https://unsplash.com/@amt8u) on [Unsplash](https://unsplash.com/photos/a-black-rectangular-object-with-a-white-and-blue-label-on-it-kdot3M5eq90)*
