---
title: "GitHub Actions Self-Hosted Runner Docker ARM64 Raspberry Pi 5 Setup Pitfalls"
date: 2026-04-01T20:13:25+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Python"]
description: "Set up a GitHub Actions self-hosted runner on Raspberry Pi 5 ARM64 without the Docker image pull failures that waste hours of debugging time."
image: "/images/20260401-github-actions-selfhosted-runn.webp"
technologies: ["Python", "Docker", "REST API", "GitHub Actions", "Linux"]
faq:
  - question: "github actions self-hosted runner docker arm64 raspberry pi 5 setup pitfalls"
    answer: "The three main pitfalls when setting up GitHub Actions self-hosted runners in Docker on Raspberry Pi 5 ARM64 are: ARM64 image compatibility gaps causing silent build failures, privilege and cgroup configuration mismatches causing runner registration failures, and network persistence or token expiry causing runners to go offline after reboots. These issues consistently affect engineers who assume the setup mirrors a standard x86 cloud VM configuration. Addressing all three categories is necessary for a stable unattended CI pipeline."
  - question: "why does my github actions self-hosted runner keep going offline raspberry pi"
    answer: "Runners on Raspberry Pi hardware frequently drop offline after host reboots due to network persistence issues and GitHub Actions registration token expiry. Registration tokens are short-lived, meaning a runner that was successfully registered before a reboot may no longer authenticate after coming back online. Configuring the runner as a persistent system service and handling token renewal are the standard fixes for this failure mode."
  - question: "docker arm64 exec format error raspberry pi github actions"
    answer: "The 'exec format error' on ARM64 hardware like Raspberry Pi occurs when a Docker image does not include a linux/arm64 layer in its manifest, meaning the image was only built for x86/amd64 architecture. If QEMU emulation is enabled, Docker may silently pull the amd64 image instead of failing, causing builds to appear successful while actually running emulated x86 binaries. Checking image manifests with 'docker manifest inspect' before adding dependencies to your pipeline helps catch this early."
  - question: "how to fix github actions self-hosted runner docker arm64 raspberry pi 5 setup pitfalls related to cgroups"
    answer: "Cgroup misconfiguration between the Raspberry Pi OS host and the Docker engine is a common cause of runner registration failures that can appear unrelated to their actual root cause. The Raspberry Pi 5 running a 64-bit OS may need cgroup v2 explicitly enabled in the boot configuration, and Docker must be configured to match the host's cgroup driver. Ensuring both the host and Docker daemon use the same cgroup version resolves most privilege-related runner startup failures."
  - question: "is raspberry pi 5 good enough for github actions ci cd docker builds"
    answer: "The Raspberry Pi 5's Cortex-A76 cores running at 2.4GHz and up to 8GB RAM make it a genuinely viable option for lightweight CI/CD workloads in 2026, with Geekbench 6 single-core scores around 940 — roughly 2.3x the performance of the Raspberry Pi 4. It is particularly cost-effective for teams exceeding GitHub's free tier of 2,000 hosted runner minutes per month on private repositories. However, ARM64 Docker image compatibility gaps for niche build tools and older language versions remain a practical constraint to evaluate before committing to this setup."
aliases:
  - "/tech/2026-04-01-github-actions-selfhosted-runner-docker-arm64-rasp/"

---

Build pipelines on a $80 Raspberry Pi 5 sound compelling — until hour three, when your Docker container refuses to pull images and your runner reports offline for the fourth time.

Self-hosted GitHub Actions runners on ARM64 hardware have picked up serious momentum heading into 2026. The Raspberry Pi 5's Cortex-A76 architecture and up to 8GB RAM make it genuinely viable for lightweight CI/CD workloads. But the setup pitfalls are real, poorly documented, and consistently bite engineers who assume the process mirrors an x86 cloud VM setup.

This isn't a beginner walkthrough. It's a forensic breakdown of where things go wrong, why they go wrong, and what the data shows about each failure mode.

**In brief:** Running GitHub Actions self-hosted runners in Docker on Raspberry Pi 5 ARM64 hardware is viable in 2026, but three specific failure categories account for the majority of broken setups.

1. ARM64 image compatibility gaps cause silent build failures when upstream Docker images don't publish `linux/arm64` manifests.
2. Privilege and cgroup configuration mismatches between the host OS and Docker engine create runner registration failures that look unrelated to their root cause.
3. Network persistence and token expiry cause runners to drop offline after host reboots, breaking unattended CI pipelines.

---

## Why ARM64 CI on Pi Hardware Is a 2026 Story

Three factors converged to make this setup worth attempting.

The Raspberry Pi 5 shipped with a BCM2712 SoC running Cortex-A76 cores at 2.4GHz — a meaningful jump over the Pi 4's Cortex-A72. Geekbench 6 single-core scores for the Pi 5 land around 940, roughly 2.3x the Pi 4's approximate 410. That's enough headroom to run Docker builds in reasonable time for small services.

GitHub's hosted runner pricing has crept upward. As of early 2026, the free tier provides 2,000 minutes per month for private repositories. Teams with frequent deploys — 15 to 20 pushes daily — burn through that ceiling fast. A self-hosted runner eliminates per-minute costs entirely.

ARM64 Docker image support finally crossed a practical threshold. Docker Hub's official library now publishes `linux/arm64` manifests for Python, Node, Go, and most common base images. But "most" isn't "all," and the gaps cluster around niche build tools and older language versions — exactly where CI pipelines tend to depend.

The combination creates a real use case. It also creates a specific failure surface that maps to these pitfalls almost exactly.

---

## The Three Failure Categories

### Image Architecture Mismatches Cause Silent Failures

The most common pitfall isn't a crash. It's a silent wrong-architecture pull.

When a Docker image doesn't include a `linux/arm64` layer in its manifest, Docker on ARM64 will either fail with `exec format error` or — if emulation is enabled — pull the `linux/amd64` layer and run it under QEMU. The QEMU path is the dangerous one. Builds appear to succeed. Tests pass. But you're running x86 binaries emulated on ARM64. Performance degrades by 3–5x based on QEMU 8.x benchmarks for integer workloads, and some binaries produce subtly wrong outputs.

The fix is explicit. Always specify platform in your `docker run` or Compose calls:

```yaml
- name: Build image
  run: docker build --platform linux/arm64 -t myapp:latest .
```

Audit every image your workflow pulls. The `docker manifest inspect <image>` command shows which architectures are published before you commit a pipeline. Don't skip this step.

### Cgroup and Privilege Configuration Breaks Runner Registration

GitHub's runner binary requires specific Linux capabilities to work inside Docker. On Raspberry Pi OS (Bookworm, 64-bit), the default cgroup version is v2, but the Docker engine's default runtime configuration doesn't always expose the necessary cgroup hierarchy to containers.

The symptom: the runner registers successfully, shows as online in your repository settings, then goes offline within 60 seconds. No obvious error in the runner logs — just a quiet exit.

The root cause is almost always one of two things. Either the container lacks `--privileged` access (or the specific capabilities `SYS_PTRACE` and `NET_ADMIN` if you're scoping tightly), or `cgroupns` is set to `private` rather than `host` in the Docker daemon config.

Fix the daemon config first:

```json
{
  "default-cgroupns-mode": "host",
  "exec-opts": ["native.cgroupdriver=systemd"]
}
```

Restart the Docker service after applying this. It resolves the silent disconnect in the majority of cases, based on patterns documented in the GitHub Actions runner issue tracker (github/actions-runner, issues #2547 and related threads). This approach can still fail when the host kernel lacks certain cgroup controllers entirely — worth checking `cat /proc/cgroups` before assuming the daemon config is the only variable.

### Token Expiry and Restart Persistence Break Unattended Runners

Runner registration tokens expire after one hour. Fine during initial setup. It becomes a problem when the Pi reboots — power outage, kernel update, accidental unplug — and the runner container tries to re-register with a stale token stored in environment variables.

The container starts, fails silently, and your pipeline queues jobs that never execute. No alert fires unless you've configured one explicitly.

Two approaches solve this. The cleaner one uses GitHub's `--once` flag combined with a startup script that fetches a fresh token via the GitHub REST API (`POST /repos/{owner}/{repo}/actions/runners/registration-token`) before the container launches. The simpler one — appropriate for low-security homelab contexts — stores the PAT with `repo` scope and generates tokens on each restart via a shell script in the container's entrypoint.

Neither is complicated. Both require intentional setup that most Docker runner tutorials skip entirely.

---

## Runner Deployment Approaches: Comparison

| Approach | ARM64 Compatibility | Restart Resilience | Setup Complexity | Security Profile |
|---|---|---|---|---|
| Docker container (official image) | High (with platform flag) | Requires token refresh script | Medium | Moderate |
| Docker container (custom image) | Full control | Same as above | High | Best |
| Native install (bare metal) | Native, no emulation | Systemd service handles restart | Low | Good |
| Docker Compose with restart policy | High | Partial — token still expires | Medium | Moderate |

The bare-metal install avoids every Docker-related pitfall. It's the right call when the Pi runs a single project and you want zero abstraction overhead. Docker containers win when you need environment isolation between multiple repositories sharing one Pi, or when you want the runner itself to be reproducible and version-controlled.

---

## Three Scenarios Worth Planning For

**Scenario 1 — Single-repo homelab deployment.** Native install wins. Use `sudo ./svc.sh install` to register the runner as a systemd service. It survives reboots automatically. Skip Docker entirely unless the workflow itself requires it.

Pin the runner version explicitly in your install script. GitHub drops support for older runner versions on a rolling six-month cycle, and an outdated runner on a Pi you forgot about will silently stop accepting jobs.

**Scenario 2 — Multi-repo shared runner.** Docker isolation is worth the complexity. Build a custom `Dockerfile` based on `ghcr.io/actions/runner` — the official image published to GitHub Container Registry, which includes ARM64 manifests as of runner v2.315+. Mount the token refresh script as an entrypoint. Use Docker Compose `restart: unless-stopped` as a baseline, but don't rely on it for token management.

Add a health check that pings the GitHub API to confirm the runner shows as online. If it doesn't, trigger a re-registration. A five-line bash script handles this.

**Scenario 3 — Production-adjacent deployment.** The Pi 5 can handle it for small services, but treat the runner as ephemeral infrastructure. Use Cloudflare Tunnel — as documented across several community setups in 2025 — to avoid exposing the Pi directly. The runner doesn't need an inbound port. Outbound HTTPS to GitHub's endpoints is sufficient. Cloudflare Tunnel adds an access control layer without complicating the runner setup itself.

Log runner job durations. If builds consistently exceed eight minutes, the Pi 5 has hit its ceiling for that workload. That's a signal to either split the pipeline or move compute-heavy steps to a GitHub-hosted runner via a split workflow.

---

## What Comes Next

The pitfalls concentrate in three areas: architecture mismatches during image pulls, cgroup configuration breaking runner registration, and token expiry breaking restart resilience. None are unsolvable. All are skipped by most setup guides.

> **Key Takeaways**
> - Always specify `--platform linux/arm64` explicitly — Docker's auto-detection fails silently on mixed-architecture environments
> - Fix `cgroupns` mode in the Docker daemon config before troubleshooting runner connectivity issues
> - Token expiry on restart requires an intentional refresh mechanism — `restart: always` alone won't save you
> - Bare-metal installs sidestep all Docker pitfalls and are the right default for single-repo setups
> - Check `/proc/cgroups` before assuming daemon config is your only variable

Looking at the next six to twelve months: GitHub is expanding its ARM64-hosted runner tier, currently in beta for Teams and Enterprise plans as of Q1 2026. When that reaches general availability at competitive pricing, the ROI calculation for Pi-based runners will shift. The use case narrows to cost-sensitive, high-frequency pipelines and air-gapped or on-device deployments where network latency to GitHub's cloud is a genuine constraint.

The setup works well when configured correctly. The gap between "it appeared to work" and "it actually works reliably" is exactly where these pitfalls live.

What's your current build time on Pi 5? The numbers vary enough by workload that a comparison across different project types would be worth tracking — drop a comment if you've measured it.

## References

1. [Self-Hosting on Raspberry Pi: CI/CD with GitHub Actions and Secure Access via Cloudflare Tunnel - DE](https://dev.to/alex_p_3aad3da07749e6adef/self-hosting-on-raspberry-pi-cicd-with-github-actions-and-secure-access-via-cloudflare-tunnel-50eo)
2. [Use Docker to Set Up a Self-Hosted GitHub Actions Runner in 10 Minutes — LeoTheLegion](https://leothelegion.net/2025/07/28/use-docker-to-set-up-self-hosted-github-actions-runner-in-10-minutes/)
3. [Deploying FastAPI on Raspberry Pi using GitHub Actions (Self‑Hosted Runner) | by Kumar Shishir | Dec](https://tech-logger.medium.com/deploying-fastapi-on-raspberry-pi-using-github-actions-self-hosted-runner-44a41aa111bc)


---

*Photo by [Roman Synkevych](https://unsplash.com/@synkevych) on [Unsplash](https://unsplash.com/photos/blue-and-black-penguin-plush-toy-UT8LMo-wlyk)*
