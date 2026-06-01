---
title: "GitHub Actions Self-Hosted Runner Docker Compose Memory Limit Ubuntu 2GB VPS"
date: 2026-05-01T20:25:53+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Python"]
description: "Running a GitHub Actions self-hosted runner on a 2GB VPS? Docker Compose memory spikes trigger exit code 137. Here's how to set safe limits."
image: "/images/20260501-github-actions-selfhosted-runn.webp"
technologies: ["Python", "Node.js", "Docker", "PostgreSQL", "Redis"]
faq:
  - question: "github actions self-hosted runner docker compose memory limit ubuntu 2GB vps out of memory"
    answer: "When running a GitHub Actions self-hosted runner with Docker Compose on a 2GB Ubuntu VPS, the OS, runner daemon, and Docker daemon together consume roughly 1.6–1.7GB before any containers start, leaving only 300–400MB for your actual workloads. Without explicit mem_limit declarations in your Docker Compose file, a single container can consume all remaining memory and trigger the OOM killer, causing exit code 137 errors. Setting per-service memory caps like --memory=512m is the most direct fix."
  - question: "how to set docker compose memory limits on ubuntu VPS to prevent OOM killer"
    answer: "To prevent OOM kills in Docker Compose, add explicit mem_limit values to each service definition in your docker-compose.yml file, for example mem_limit: 512m. You should also set --memory-swap equal to --memory to prevent swap exhaustion on constrained hosts. Enabling cgroup v2 configuration on Ubuntu further improves per-container memory enforcement reliability."
  - question: "github actions self-hosted runner docker compose memory limit ubuntu 2GB vps vs hosted runner RAM difference"
    answer: "GitHub's hosted Linux runners provide 7GB of RAM per job, while a 2GB VPS self-hosted runner leaves only 300–400MB of usable headroom after OS, runner, and Docker daemon overhead. This means teams choosing a 2GB VPS for cost savings must deliberately architect memory usage in a way that GitHub's default hosted tooling handles automatically. Without explicit memory limits in Docker Compose, this gap in available RAM frequently causes build failures on self-hosted environments."
  - question: "exit code 137 github actions docker compose what does it mean"
    answer: "Exit code 137 in a GitHub Actions Docker Compose workflow means the container process was forcibly killed by the Linux OOM (Out of Memory) killer because the system ran out of available RAM. This is especially common on 2GB VPS hosts running a self-hosted runner, where available memory is already thin before containers launch. Fixing it requires adding explicit per-service memory limits in your Docker Compose configuration to prevent any single container from consuming all host memory."
  - question: "how much RAM does github actions self-hosted runner use on ubuntu"
    answer: "A GitHub Actions self-hosted runner daemon on Ubuntu typically consumes 200–300MB of RAM when actively processing a job, on top of the 300–500MB Ubuntu itself uses at idle. Combined with the Docker daemon adding another 100–150MB, total baseline consumption on a 2GB VPS reaches roughly 600–950MB before any containers start. This leaves a relatively small and unpredictable memory budget for Docker Compose workloads without careful resource planning."
---

A 2GB VPS running GitHub Actions sounds like a smart budget move — until Docker Compose quietly consumes everything and your runner dies mid-pipeline with a cryptic exit code 137. This is fixable. But only if you understand exactly where the limits are before you hit them.

> **Key Takeaways**
> - A default GitHub Actions self-hosted runner on Ubuntu consumes 200–400MB of base RAM, leaving a 2GB VPS with roughly 1.4–1.6GB for Docker Compose workloads before the OOM killer fires.
> - Docker Compose doesn't enforce per-service memory limits by default — without explicit `mem_limit` declarations, a single container can consume the entire available host memory.
> - Setting `--memory=512m` and `--memory-swap=512m` at the container level is the most direct way to prevent swap exhaustion on a constrained VPS.
> - GitHub's hosted runners provide 7GB RAM per job (as of 2026), meaning self-hosted 2GB environments require deliberate memory architecture that GitHub's default tooling doesn't enforce for you.
> - Teams running Docker Compose on sub-4GB hosts report a measurable drop in OOM-related build failures after implementing per-service memory caps and cgroup v2 configurations.

---

## The Memory Math Nobody Does Before Deploying

Two gigabytes feels like plenty until you run the actual numbers.

A fresh Ubuntu 22.04 LTS or 24.04 LTS installation consumes roughly 300–500MB at idle, depending on background services. Add the GitHub Actions runner daemon — another 200–300MB when active, visible in production process stats — and you're already at 500–800MB before a single Docker container starts. That leaves 1.2–1.5GB for your actual workloads.

Docker's own daemon, `dockerd`, adds another 100–150MB. Now you're sitting at roughly 1.6–1.7GB consumed before `docker compose up` runs a single service. On a 2GB VPS, that's 300–400MB of headroom for your entire application stack.

That's the core problem with running a self-hosted runner and Docker Compose without explicit constraints. The math is tight before you write a single line of workflow YAML.

According to the MassiveGRID GitHub Actions self-hosted runner guide, Ubuntu VPS environments require careful pre-configuration to avoid resource contention during CI runs. The problem isn't the runner itself — it's the compound effect of OS overhead, runner process, Docker daemon, and container memory all competing at the same time.

---

## Why Self-Hosted Runners on 2GB VPS Became a Common Pattern

GitHub's hosted runners are convenient. They're also $0.008 per minute for Linux (as of GitHub's 2026 pricing), which adds up fast for teams running dozens of daily builds. A $5–6/month VPS from Hetzner, DigitalOcean, or Vultr looks attractive by comparison.

The trade-off is resource management. GitHub's hosted Linux runners provide 7GB RAM, 2 vCPUs, and 14GB SSD by default. A 2GB VPS gives you 2GB RAM, typically 1–2 vCPUs, and whatever storage tier you've paid for.

That gap became more visible as Docker Compose adoption accelerated. Teams started packaging their entire test environments — app server, database, cache, queue — into Compose stacks and running them inside CI pipelines. On hosted runners, this works fine. On a 2GB self-hosted runner, it frequently doesn't.

According to the OneUptime guide on self-hosted runners (published January 2026), the setup process itself is straightforward: download the runner, configure it with a registration token, run it as a `systemd` service. Installation isn't the hard part. What happens after your first Docker Compose workflow fires is.

---

## Memory Limits, Cgroups, and Compose Configuration

### Where Docker Compose Actually Fails on 2GB Hosts

Docker Compose doesn't add memory limits by default. None. Spin up three services — a Node.js app, a PostgreSQL 15 instance, and a Redis cache — and each will consume as much RAM as the kernel allows before the OOM killer steps in.

PostgreSQL alone, with default settings, can grab 512MB–1GB in shared buffers plus working memory. On a 2GB host running a CI runner, that's a near-guaranteed crash.

The fix is explicit. In your `compose.yml` (Docker Compose v2 syntax), every service needs memory constraints:

```yaml
services:
  app:
    image: node:20-alpine
    deploy:
      resources:
        limits:
          memory: 512M
  db:
    image: postgres:15-alpine
    deploy:
      resources:
        limits:
          memory: 256M
    environment:
      POSTGRES_SHARED_BUFFERS: 64MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 128MB
```

The `deploy.resources.limits.memory` key works in Compose v2 when run with `docker compose` (not legacy `docker-compose`). On Ubuntu 22.04+ with cgroup v2 enabled by default, these limits are enforced at the kernel level.

### Cgroup v2: The Configuration Detail That Matters

Ubuntu 22.04 LTS ships with cgroup v2 enabled by default. That's good news for memory management — cgroup v2 provides more granular memory accounting than v1. But it also means some older Docker images and configurations don't behave as expected.

Run `cat /sys/fs/cgroup/cgroup.controllers` to confirm your VPS supports `memory` as a controller. If `memory` appears in the output, you're set. If not, pass `systemd.unified_cgroup_hierarchy=1` as a kernel boot parameter.

According to the LeoTheLegion Docker self-hosted runner guide (July 2025), configuring the runner inside a Docker container — rather than directly on the host — adds an isolation layer that improves memory predictability. The runner container gets its own cgroup allocation, separate from host processes.

### Swap: The Hidden Variable

Most VPS providers provision zero swap by default. On a 2GB host with no swap, an OOM event terminates the process immediately. Adding 1–2GB of swap via a swapfile provides a buffer, though it slows builds significantly when swap is actually used.

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

Set `vm.swappiness=10` in `/etc/sysctl.conf`. That tells the kernel to prefer RAM and use swap only as a last resort — preferable to the default value of `60`, which is tuned for desktop workloads, not constrained server environments.

### Memory Management Approaches on a 2GB Self-Hosted Runner

| Approach | Memory Control | Build Stability | Setup Complexity | Recommended? |
|---|---|---|---|---|
| No limits (default) | None | Low (OOM-prone) | Minimal | ❌ No |
| `mem_limit` in Compose v1 | Per-service | Medium | Low | ⚠️ Legacy |
| `deploy.resources.limits` in Compose v2 | Per-service | High | Low | ✅ Yes |
| Runner in Docker container + limits | Per-runner + per-service | Highest | Medium | ✅ Yes |
| Swap only, no limits | Host-level | Low (slow builds) | Low | ❌ No |

The Compose v2 `deploy.resources` approach combined with a runner running as a `systemd` service on the host delivers the best stability-to-complexity ratio for most teams. Running the runner inside Docker adds isolation benefits but requires managing a nested Docker-in-Docker setup, which introduces its own complexity.

The core trade-off: **host-based runner + Compose v2 limits** is simpler and sufficient for most 2GB VPS deployments. A **Dockerized runner** makes sense when you need clean environment resets between jobs or run multiple concurrent runners on the same host.

---

## Practical Scenarios and Recommendations

**Scenario 1 — Single app with a database (most common)**

A Node.js or Python app running tests against PostgreSQL. Cap the app at 512M, PostgreSQL at 256M, Redis (if used) at 128M. Set `POSTGRES_SHARED_BUFFERS=64MB` explicitly. Total container budget: ~900MB. Combined with runner overhead (~600MB), you're at ~1.5GB — workable on 2GB with 512MB swap as a safety net.

**Scenario 2 — Build + Docker image push**

Building a Docker image during CI is memory-intensive. `docker build` with layer caching can spike to 800MB–1GB depending on base image size. On a 2GB VPS, don't run `docker build` concurrently with other running services. Sequence your workflow steps: tear down Compose services before building the final image.

```yaml
- name: Stop test services
  run: docker compose down

- name: Build production image
  run: docker build -t myapp:latest .
```

**Scenario 3 — Multiple concurrent jobs**

GitHub Actions runners handle one job at a time by default. Don't run multiple parallel jobs on a single 2GB VPS runner — the memory math simply doesn't work. If you need parallelism, either upgrade to a 4GB instance or register two separate runners on separate VPS instances.

The signal to watch: exit code 137 means SIGKILL from the OOM killer. That's not a flaky test. That's a memory problem. Run `dmesg | grep -i oom` immediately after a failure to confirm.

---

## Conclusion

Running GitHub Actions with Docker Compose on a 2GB VPS isn't theoretically difficult. It requires explicit memory architecture that GitHub's tooling doesn't enforce for you — and that distinction matters when your build silently dies at 2am.

The practical summary:

- **Compose v2 `deploy.resources.limits.memory`** is the correct, supported way to cap container memory in 2026.
- **Ubuntu 22.04+ with cgroup v2** enforces these limits reliably at the kernel level.
- **Swap (1GB) + `vm.swappiness=10`** provides a safety net without encouraging swap-heavy builds.
- **Exit code 137 = OOM kill** — not a test failure. A memory failure.

Two things are worth watching over the next 6–12 months. Docker's continued work on memory reporting in `docker stats` is making it easier to profile container usage before setting limits — run `docker stats --no-stream` during a local test to gather real numbers before deploying to CI. And GitHub's expanding self-hosted runner documentation suggests official guidance on resource-constrained environments may improve.

A 2GB VPS is viable for CI workloads if you treat memory as a first-class configuration concern from day one. Don't let the OOM killer be the one to define your limits for you.

What's your current memory budget per service? Running those numbers before writing the workflow saves hours of debugging later.

## References

1. [Set Up CI/CD with GitHub Actions Self-Hosted Runners on Ubuntu VPS | MassiveGRID Blog](https://massivegrid.com/blog/github-actions-self-hosted-runner-ubuntu-vps/)
2. [How to Set Up a Self-Hosted GitHub Actions Runner on Ubuntu](https://oneuptime.com/blog/post/2026-01-07-ubuntu-github-actions-runner/view)
3. [Use Docker to Set Up a Self-Hosted GitHub Actions Runner in 10 Minutes — LeoTheLegion](https://leothelegion.net/2025/07/28/use-docker-to-set-up-self-hosted-github-actions-runner-in-10-minutes/)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
