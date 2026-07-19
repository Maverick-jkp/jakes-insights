---
title: "GitHub Actions Self-Hosted Runner on Raspberry Pi 5 Pitfalls"
date: 2026-05-04T21:02:26+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Python"]
description: "Self-hosted GitHub Actions runners on Raspberry Pi 5 ARM64 are powerful but tricky. Avoid the setup pitfalls costing developers hours of lost debugging time."
image: "/images/20260504-github-actions-selfhosted-runn.webp"
technologies: ["Python", "FastAPI", "Docker", "REST API", "GitHub Actions"]
faq:
  - question: "github actions self-hosted runner docker container arm64 raspberry pi 5 setup pitfalls what are the main problems"
    answer: "The three biggest github actions self-hosted runner docker container arm64 raspberry pi 5 setup pitfalls are missing ARM64 Docker image variants, cgroup v2 misconfiguration, and runner registration tokens expiring after 60 minutes. Many popular CI images don't publish linux/arm64 variants, causing silent fallback to slow QEMU emulation or outright failures. Raspberry Pi OS Bookworm's default cgroup v2 support also breaks Docker's resource constraint handling unless explicitly configured."
  - question: "how to run github actions self-hosted runner in docker on raspberry pi 5"
    answer: "You can run a GitHub Actions self-hosted runner in a Docker container on the Raspberry Pi 5 by downloading the official arm64 actions-runner tarball from GitHub Releases and containerizing it. The Pi 5's Cortex-A76 cores and up to 8GB RAM make it viable for CI workloads, but you must verify ARM64 image availability and configure cgroup v2 correctly before the setup will work reliably. Containerizing the runner process is recommended by GitHub for isolation, but ARM64-specific Docker ecosystem gaps add significant friction."
  - question: "raspberry pi 5 cgroup v2 docker not working fix"
    answer: "Raspberry Pi OS Bookworm ships with cgroup v2 enabled by default, which breaks Docker's default resource constraint handling and causes containers to fail unexpectedly. To fix this, you need to explicitly configure Docker to handle cgroup v2, either by adjusting the Docker daemon settings or modifying kernel boot parameters. This is one of the most common github actions self-hosted runner docker container arm64 raspberry pi 5 setup pitfalls that is rarely documented in standard tutorials."
  - question: "github actions runner registration token expires 60 minutes docker bootstrap script failing"
    answer: "GitHub's runner registration tokens have a hard 60-minute expiration window, which silently breaks unattended Docker-based runner bootstrap scripts if the container takes too long to start or the token is reused. This means any automated setup script that generates a token and later attempts to register the runner after the window has passed will fail without a clear error message. The fix is to generate a fresh token immediately before runner registration runs, ideally as part of the container entrypoint logic."
  - question: "are ARM64 docker images available for CI tools like node python maven on raspberry pi"
    answer: "Most Docker Official Images including node, python, and maven publish multi-arch manifests that include linux/arm64 variants, so they work natively on Raspberry Pi 5 without QEMU emulation. However, many third-party and enterprise CI tool images do not publish ARM64 variants, which can cause silent fallback to emulation that runs 3–5x slower or fails outright. Always verify that your specific CI image has an arm64 manifest using 'docker manifest inspect' before building your pipeline around it."
aliases:
  - "/tech/2026-05-04-github-actions-selfhosted-runner-docker-container-/"

---

Running CI/CD on a Raspberry Pi 5 sounds elegant on paper — cheap hardware, low power draw, ARM64 native builds. The reality involves a surprising number of sharp edges that can cost hours of debugging time before a single workflow succeeds.

Self-hosted GitHub Actions runners have surged in adoption since 2025. According to GitHub's 2025 Actions usage report, self-hosted runners now account for roughly 34% of all workflow minutes across enterprise accounts, up from 22% in 2023. The Raspberry Pi 5's Cortex-A76 cores and up to 8GB RAM make it genuinely viable for CI workloads — but the ARM64/Docker intersection is full of undocumented friction, and most tutorials simply skip it.

The core argument: the Pi 5 is a legitimate CI node, but only if you navigate the ARM64/Docker intersection deliberately.

**The short version:** The Raspberry Pi 5 can run GitHub Actions self-hosted runners reliably in Docker containers, but ARM64-specific image availability, `cgroup v2` configuration, and runner registration token handling are the three failure points that trip up most setups.

1. Many popular CI Docker images don't publish `linux/arm64` variants, silently falling back to slow QEMU emulation or failing outright.
2. Raspberry Pi OS Bookworm ships with `cgroup v2` enabled by default, which breaks Docker's default resource constraint handling unless explicitly configured.
3. GitHub's runner registration tokens expire in 60 minutes — a fact that destroys unattended Docker-based runner bootstrap scripts.

---

## Why the Pi 5 + Self-Hosted Runner Combination Is Tempting

The Raspberry Pi 5 landed in late 2023 with a 2.4GHz quad-core Cortex-A76, PCIe 2.0, and genuine USB 3.0 bandwidth. By early 2026, it's a mature platform with reliable kernel support and a stable Bookworm (Debian 12) base. At roughly $80 for the 8GB model, it's cheaper than a single month of GitHub-hosted runner minutes for mid-sized teams running 3,000+ minutes monthly.

The appeal is obvious for teams building ARM-native applications — embedded Linux, mobile backends, edge computing. You want to test on real ARM64 silicon, not emulated environments. Emulated ARM64 builds via QEMU on x86_64 runners run approximately 3–5x slower, according to benchmarks published by the Buildjet team in their 2025 ARM CI analysis.

GitHub's own documentation for self-hosted runners recommends containerizing the runner process for isolation and repeatability. That's correct advice. But it papers over the ARM64-specific friction in Docker's ecosystem.

The self-hosted runner binary itself — `actions-runner` — publishes an `arm64` tarball directly from GitHub Releases. That part works fine. The problems live in the layers around it.

---

## The Image Availability Problem Is Worse Than You Think

Pull any "standard" CI Docker image — `node:20`, `python:3.12`, `maven:3.9` — and you'll get ARM64 images without issue. The Docker Official Images library maintains multi-arch manifests for most popular runtimes. Step one layer out into community images or organization-specific CI tooling, and the `linux/arm64` variant simply doesn't exist.

The practical failure mode is subtle. Your `docker pull` succeeds on ARM64 because Docker silently pulls the `linux/amd64` image and runs it under QEMU's user-space emulation. Builds "work" but run at 20–30% of native speed. Worse, some binary tools inside those images segfault under QEMU because they use x86-specific instructions — `CPUID`, AVX extensions — that QEMU doesn't faithfully emulate.

The fix is unglamorous but necessary. Before committing to any base image in your workflow, run:

```bash
docker manifest inspect <image>:<tag> | grep -A2 '"platform"'
```

If `linux/arm64` doesn't appear, either find an alternative image or build your own. The `buildx` multi-platform builds from an x86 machine can publish ARM64 images to Docker Hub or GHCR, which your Pi runner then pulls natively.

This isn't a rare edge case. It's the first wall most teams hit.

---

## cgroup v2 Breaks Your Resource Limits Silently

Raspberry Pi OS Bookworm defaults to `cgroup v2` — the unified hierarchy. Docker's older behavior assumed `cgroup v1` for memory and CPU limit enforcement. Docker Engine 24+ handles `cgroup v2` correctly *if* the kernel exposes the right controllers. On the Pi 5, `/boot/firmware/cmdline.txt` doesn't enable `cgroup_memory` and `cgroup_enable=memory` by default.

Without these flags, `docker run --memory=512m` doesn't actually enforce the limit. Containers OOM the host instead of being killed themselves. For CI workloads running multiple parallel jobs, this can take down the runner host entirely.

Add this to `/boot/firmware/cmdline.txt` — keep it on one line:

```
cgroup_enable=cpuset cgroup_enable=memory cgroup_memory=1
```

Reboot. Confirm with `cat /proc/cgroups | grep memory`. The `enabled` column should show `1`.

This is documented in Raspberry Pi's official kernel docs. It's almost never mentioned in runner setup guides.

---

## Runner Registration Token Expiry Kills Unattended Setups

GitHub's registration tokens for self-hosted runners expire in **60 minutes** from generation. This is documented in GitHub's REST API reference. But most Docker-based runner setup scripts — including the popular `myoung34/github-runner` container image — generate the token at `docker run` time and bake it into the container environment.

When the container restarts after a reboot, a Docker daemon update, or an OOM kill, the token is stale. The runner tries to re-register, fails silently, and sits in a "waiting for jobs" state that never receives anything. Your workflows queue indefinitely. No error. Just silence.

The correct pattern: use a small init script that fetches a fresh token at container startup via the GitHub API, using a long-lived Personal Access Token or GitHub App credentials stored in a Docker secret.

```bash
REG_TOKEN=$(curl -sX POST \
  -H "Authorization: token ${GITHUB_PAT}" \
  https://api.github.com/repos/${REPO}/actions/runners/registration-token \
  | jq .token --raw-output)
./config.sh --url https://github.com/${REPO} --token ${REG_TOKEN}
```

This runs at every container start. No stale tokens. No mystery queues.

---

## Runner Comparison: Pi 5 vs. Alternatives

| Criteria | Raspberry Pi 5 (8GB) | GitHub-Hosted (ubuntu-latest) | Buildjet ARM64 Runner |
|---|---|---|---|
| Cost per month (3,000 min) | ~$2 electricity | ~$24 (at $0.008/min) | ~$12 (at $0.004/min) |
| ARM64 native | ✅ Yes | ❌ No (x86_64) | ✅ Yes |
| Setup complexity | High | None | Low |
| Maintenance burden | Owner's problem | GitHub's problem | Buildjet's problem |
| Network egress | Free (local) | Billed separately | Billed separately |
| Best for | ARM-native builds, cost-sensitive | General CI, no ops burden | ARM CI without hardware |

The Pi 5 wins on cost at scale and ARM64 fidelity. It loses on operational overhead. For teams without anyone comfortable managing Linux hosts, Buildjet's managed ARM64 runners are a cleaner trade-off at roughly half the GitHub-hosted price. This isn't always the right hardware project to take on — know your team's capacity before committing.

---

## Three Scenarios, Three Fixes

**Scenario 1 — FastAPI or similar Python services targeting ARM Linux edge deployments.** Build and test natively on the Pi 5. Use `python:3.12-slim` — ARM64 officially available. The runner's local network access means Docker image pulls from GHCR happen fast without egress charges. The risk: if the Pi is also the deployment target, a bad build can affect the production service. Run the runner container with `--restart=unless-stopped` and keep build artifacts in a separate volume.

**Scenario 2 — Multi-arch Docker image publishing.** Don't build multi-arch images *on* the Pi. Use `docker buildx` with a remote builder or GitHub-hosted runners for the x86_64 slice, and the Pi for the ARM64 slice via `buildx --platform linux/arm64`. This sidesteps QEMU entirely and cuts build times by 60–70% on the ARM64 leg.

**Scenario 3 — Teams hitting GitHub Actions minute limits on private repos.** Self-hosted runners on a Pi 5 consume zero billed minutes. For a team running 8,000+ minutes monthly on private repos, the Pi 5 pays for itself in under two months. The setup cost is real — budget 4–6 hours for first-time configuration including the `cgroup v2` fix and token refresh logic.

**What to watch:** GitHub is actively developing ephemeral runner support improvements, tracked in `actions/runner` GitHub Issues. Ephemeral runners — ones that register, run one job, then terminate — would eliminate the token expiry problem entirely. That's the direction the ecosystem is moving through 2026.

---

## Where This Goes From Here

These aren't showstoppers. They're known, fixable problems that the standard tutorial ecosystem underserves.

> **Key Takeaways**
> - Verify ARM64 image availability *before* designing your workflow — not after a 3-hour debug session
> - The `cgroup v2` cmdline fix is non-negotiable on Pi OS Bookworm
> - Runner registration tokens need dynamic refresh at container startup
> - For teams without ops capacity, managed ARM64 runners like Buildjet offer a practical middle ground
> - Ephemeral runner improvements coming in 2026 will significantly reduce token management complexity

Over the next 6–12 months, expect the Docker Official Images library to expand ARM64 coverage as Pi-class hardware becomes more common in CI contexts. The hardware case for the Pi 5 only strengthens as electricity costs stay low relative to cloud compute pricing.

If you're already running self-hosted runners on x86 hardware and building ARM64 targets, a Pi 5 node is worth the weekend setup investment. Just fix the `cgroup` flags first.

What's your current CI spend on ARM64 builds? The math on self-hosted might look different than you expect.

## References

1. [Use Docker to Set Up a Self-Hosted GitHub Actions Runner in 10 Minutes — LeoTheLegion](https://leothelegion.net/2025/07/28/use-docker-to-set-up-self-hosted-github-actions-runner-in-10-minutes/)
2. [GitHub Actions Self-Hosted Runner: A Complete Guide to Private Environment Deployment · BetterLink B](https://eastondev.com/blog/en/posts/dev/20260423-github-actions-self-hosted-runner/)
3. [Deploying FastAPI on Raspberry Pi using GitHub Actions (Self‑Hosted Runner) | by Kumar Shishir | Med](https://tech-logger.medium.com/deploying-fastapi-on-raspberry-pi-using-github-actions-self-hosted-runner-44a41aa111bc)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
