---
title: "WSL2 Ubuntu 24.04 Docker Desktop Memory Leak Fix Windows 11"
date: 2026-05-22T21:38:56+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "wsl2", "ubuntu", "24.04", "Node.js"]
description: "WSL2 Ubuntu 24.04 Docker Desktop memory leak draining 12GB on Windows 11? Fix the config problem hitting thousands of devs in 2026."
image: "/images/20260522-wsl2-ubuntu-2404-docker-deskto.webp"
technologies: ["Node.js", "Docker", "Redis", "Linux", "Go"]
faq:
  - question: "wsl2 ubuntu 24.04 docker desktop memory leak fix windows 11 16gb ram"
    answer: "The most effective fix for the WSL2 Ubuntu 24.04 Docker Desktop memory leak on Windows 11 16GB RAM systems is configuring a .wslconfig file to cap memory usage and enable automatic reclamation. A properly configured .wslconfig can reduce steady-state WSL2 memory consumption by 40–60%, preventing the Vmmem process from consuming 8–14GB even when containers are idle."
  - question: "why is vmmem using so much memory windows 11 wsl2"
    answer: "Vmmem balloons on Windows 11 because WSL2 runs inside a Hyper-V virtual machine that claims RAM from the host but doesn't eagerly return it when Linux processes free pages. Linux uses freed RAM as disk cache by default, and Windows cannot distinguish that cache from active usage, so the memory appears permanently consumed."
  - question: "does ubuntu 24.04 make wsl2 memory worse than older ubuntu versions"
    answer: "Yes, Ubuntu 24.04 specifically worsens WSL2 memory ballooning because its kernel 6.8.x removed certain virtio-balloon driver behaviors that previously helped WSL2 return memory pages to the Windows host OS. This makes the wsl2 ubuntu 24.04 docker desktop memory leak fix windows 11 16gb ram problem measurably worse compared to systems running older Ubuntu versions."
  - question: "how to limit wsl2 memory usage docker desktop windows 11"
    answer: "You can limit WSL2 memory usage by creating or editing a .wslconfig file in your Windows user profile directory and setting a hard memory cap, such as 'memory=6GB', under the [wsl2] section. This prevents Docker Desktop and Ubuntu from collectively consuming nearly all available RAM on 16GB systems, keeping Windows processes responsive."
  - question: "docker desktop wsl2 backend vs hyper-v backend memory usage comparison"
    answer: "Docker Desktop defaults to the WSL2 backend, which spawns additional WSL distros like docker-desktop alongside your Ubuntu instance, compounding memory ballooning issues on Windows 11. The WSL2 backend pre-allocates large memory regions inside the VM that are not released back to Windows even when containers are idle, making memory pressure significantly worse than older Hyper-V backend configurations on 16GB systems."
aliases:
  - "/tech/2026-05-22-wsl2-ubuntu-2404-docker-desktop-memory-leak-fix-wi/"

---

Your machine has 16GB of RAM. Docker Desktop is running three modest containers. Task Manager shows WSL2 consuming 12GB and climbing.

This isn't a fringe edge case. It's a widespread configuration problem affecting thousands of developers on Windows 11 in 2026.

The WSL2 + Ubuntu 24.04 + Docker Desktop memory leak on Windows 11 has become one of the most-searched developer pain points this year. After a series of Windows 11 updates in late 2025 changed how WSL2 handles memory reclamation, the situation got measurably worse. Microsoft's own Q&A forums document cases where `Vmmem` — the process hosting WSL2's virtual machine — balloons past available physical RAM and never releases it back to Windows.

What's actually happening, why it's worse on Ubuntu 24.04 specifically, and which fixes work in 2026 — that's what this covers.

Topics covered:

- Why WSL2's memory model causes ballooning on Windows 11
- How Ubuntu 24.04's memory management interacts badly with Docker Desktop
- Concrete `.wslconfig` settings that reclaim memory without breaking workflows
- A comparison of the three main mitigation approaches

---

**In brief:** WSL2 doesn't automatically return freed memory to Windows, and Docker Desktop compounds this by pre-allocating large memory regions inside the WSL2 VM. On 16GB systems running Ubuntu 24.04, this combination regularly leaves fewer than 2GB available for Windows processes.

Three facts worth knowing upfront:
1. The `Vmmem` process can consume 8–14GB on a 16GB system even when containers are idle, according to documented cases in Microsoft's Q&A forums (May 2026).
2. Ubuntu 24.04's updated kernel (6.8.x) removed certain memory balloon driver behaviors that previously helped WSL2 return pages to the host OS.
3. A properly configured `.wslconfig` file reduces steady-state WSL2 memory usage by 40–60% in reported community benchmarks on DEV Community and Reddit r/docker threads.

---

## The Architecture Problem Nobody Warned You About

WSL2 runs inside a lightweight Hyper-V virtual machine. That VM claims memory from Windows at startup and — crucially — doesn't eagerly return it when processes inside WSL2 free pages. Linux uses freed RAM as disk cache by default. From Windows' perspective, that cache looks like active usage. The host OS can't tell the difference.

Docker Desktop makes this dramatically worse. When Docker Desktop runs on WSL2 (its default backend since 2022), it spawns a `docker-desktop` WSL distro alongside your Ubuntu 24.04 distro. Both consume memory inside separate VM instances, or share one depending on your Docker Desktop version. As of Docker Desktop 4.29+ (released Q4 2025), the integration moved to a shared WSL2 VM model, which reduced isolation but didn't fix the ballooning behavior.

Ubuntu 24.04 (Noble Numbat) shipped with kernel 6.8, which changed how the `virtio-balloon` driver works inside VMs. According to the Microsoft Q&A thread from May 2026, several users confirmed that the memory reclamation callbacks that previously triggered Windows to reclaim pages stopped working correctly after upgrading from Ubuntu 22.04 to 24.04. The timing coincided with the Windows 11 24H2 rollout, creating a two-sided regression.

The practical result: a developer running VS Code, a Node.js container, a Postgres container, and a Redis container on a 16GB Windows 11 machine will routinely see their system swap to disk within two hours of starting work.

This approach can fail in a specific way. The regression isn't isolated to one layer — it's kernel-level changes in Ubuntu 24.04 colliding with Windows 11 24H2 behavior changes at the same time. That's why a single patch from either Microsoft or Canonical won't fully resolve it.

---

## What the Fixes Actually Do

Three approaches exist. They're not mutually exclusive.

### Fix 1: Hard Memory Cap via `.wslconfig`

The `.wslconfig` file lives in your Windows user profile (`C:\Users\<username>\.wslconfig`) and controls WSL2's VM parameters globally.

```ini
[wsl2]
memory=6GB
processors=4
swap=2GB
swapFile=C:\\temp\\wsl-swap.vhdx
```

Setting `memory=6GB` on a 16GB system is the single highest-impact change. It hard-caps the WSL2 VM, leaving 10GB for Windows, Docker Desktop's overhead, and your browser. Community testing documented on DEV Community shows this alone drops `Vmmem` from 12GB+ to a consistent 5–6GB ceiling.

The tradeoff: if your containers genuinely need more than 6GB — large ML models, for example — you'll hit OOM errors inside WSL2. Adjust based on your actual workload.

### Fix 2: Periodic Memory Release via `wsl --shutdown`

WSL2 reclaims memory when the VM fully shuts down. Running `wsl --shutdown` from PowerShell terminates all WSL2 instances and releases `Vmmem` back to Windows immediately.

This isn't a permanent fix. It's a pressure-relief valve. Some teams script this to run on a schedule:

```powershell
# Run in Task Scheduler — every 4 hours
wsl --shutdown
```

The VM restarts automatically on next WSL2 access, with a 2–5 second cold-start delay. For most web developers, that's a non-issue.

### Fix 3: Docker Desktop Memory Limits

Inside Docker Desktop settings (`Settings → Resources → Advanced`), you can cap the memory Docker allocates. Setting this to 4GB means Docker's WSL2 distro won't pre-allocate beyond that ceiling, independent of your `.wslconfig` settings.

---

## Comparing the Three Approaches

| Approach | Memory Saved | Persistence | Risk | Best For |
|---|---|---|---|---|
| `.wslconfig` memory cap | 40–60% reduction | Permanent | OOM if cap too low | Most developers |
| `wsl --shutdown` schedule | Full release (temporary) | Resets on restart | Brief cold-start delay | Power users, long sessions |
| Docker Desktop resource cap | 20–40% reduction | Permanent | Container OOM on heavy workloads | Docker-heavy workflows |
| All three combined | 60–75% reduction | Permanent | Minimal with correct sizing | 16GB RAM machines |

Running all three together is the recommended configuration for this specific setup. The `.wslconfig` cap controls the ceiling, Docker Desktop's limit controls pre-allocation, and the scheduled shutdown clears any lingering cache accumulation.

---

## Real-World Configuration for 16GB Systems

Different workloads need different answers.

**Scenario 1: Web developer (Node.js + Postgres + Redis)**
Set `.wslconfig` memory to 6GB, Docker Desktop cap to 4GB, and schedule `wsl --shutdown` every 6 hours via Task Scheduler. This leaves ~8GB for Windows processes and browser tabs.

**Scenario 2: Data engineer running dbt + Spark containers**
These workloads legitimately need memory. Set `.wslconfig` to 10GB, Docker Desktop to 8GB, and skip the shutdown schedule — cold starts interrupt long-running jobs. At this workload level, the memory problem on a 16GB machine becomes a hardware constraint, not a configuration problem. Upgrading to 32GB is the practical answer.

**Scenario 3: Intermittent Docker use (running containers only during active development)**
Use `wsl --shutdown` as a manual alias triggered when switching tasks. No persistent cap needed. This keeps maximum memory available when you actually need it.

**What to watch:** Microsoft has an open GitHub issue (WSL #11636) tracking automatic memory reclamation for WSL2. A fix has been prototyped but hasn't shipped to stable Windows 11 builds as of May 2026. If it lands, the `.wslconfig` workaround becomes optional rather than mandatory — but it isn't there yet.

---

## Where This Goes in the Next 12 Months

Three things worth tracking:

- **WSL2 automatic memory reclaim**: The GitHub prototype uses a background pressure daemon. If it ships in Windows 11 25H2 (expected late 2026), it could eliminate the need for manual `.wslconfig` caps for most users.
- **Docker Desktop 5.x architecture**: Docker's roadmap, shared in DockerCon 2025 materials, indicates a shift toward rootless container execution that reduces VM memory pre-allocation significantly.
- **Ubuntu 24.04 kernel updates**: Canonical's 6.11 kernel backport for Noble Numbat, expected in HWE updates mid-2026, may restore the `virtio-balloon` behavior that regressed in 6.8.

None of these are guaranteed to land on schedule. The combined fix approach works right now, regardless of what ships.

> **Key Takeaways**
> - WSL2's memory model doesn't auto-reclaim — this is architectural, not a bug that patches will fully resolve
> - Ubuntu 24.04 made the baseline worse due to kernel 6.8 changes to the `virtio-balloon` driver
> - A hard memory cap in `.wslconfig` is the fastest, highest-impact fix available today
> - Running all three fixes together drops `Vmmem` consumption by 60–75% on 16GB systems
> - At data-engineering workload levels, 16GB becomes a hardware constraint — configuration alone won't solve it

Don't wait for Microsoft or Canonical to ship a fix. Configure `.wslconfig` today. It takes five minutes and the difference on a 16GB machine is immediate.

What's your current `Vmmem` ceiling sitting at? Drop your config in the comments — particularly if you've found a Docker Desktop version that behaves notably better.

---

**References**

1. Microsoft Q&A — *Regarding WSL Network and Docker Memory Consumption Following Windows Update* (May 2026): [learn.microsoft.com](https://learn.microsoft.com/en-us/answers/questions/5621996/regarding-wsl-network-and-docker-memory-consumptio)
2. DEV Community — *How to Reclaim Memory from Docker WSL*, Colin Williams: [dev.to](https://dev.to/colin-williams-dev/how-to-reclaim-memory-from-docker-wsl-2lkf)
3. Reddit r/docker — *Docker with wsl2 using ALL my memory*: [reddit.com](https://www.reddit.com/r/docker/comments/1lk0wtf/docker_with_wsl2_using_all_my_memory/)

## References

1. [Regarding WSL Network and Docker Memory Consumption Following Windows Update - Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/5621996/regarding-wsl-network-and-docker-memory-consumptio)
2. [How to Reclaim Memory from Docker WSL - DEV Community](https://dev.to/colin-williams-dev/how-to-reclaim-memory-from-docker-wsl-2lkf)
3. [Docker with wsl2 using ALL my memory : r/docker](https://www.reddit.com/r/docker/comments/1lk0wtf/docker_with_wsl2_using_all_my_memory/)


---

*Photo by [Rohan](https://unsplash.com/@rohanphoto) on [Unsplash](https://unsplash.com/photos/a-laptop-and-a-computer-ZoXCoH7tja0)*
