---
title: "GitHub Actions Self-Hosted Runner Docker ARM64 M2 Mac Permission Denied Fix"
date: 2026-03-19T20:01:34+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Docker"]
description: "Fix the Docker daemon permission denied error on your GitHub Actions self-hosted runner M2 Mac ARM64 builds with this targeted socket access solution."
image: "/images/20260319-github-actions-selfhosted-runn.webp"
technologies: ["Docker", "AWS", "GitHub Actions", "Linux", "Rust"]
faq:
  - question: "github actions self-hosted runner docker arm64 M2 Mac permission denied fix"
    answer: "The permission denied error when connecting to the Docker daemon socket on an M2 Mac self-hosted runner is caused by a user and socket permission mismatch, not a Docker or GitHub bug. The fix involves adjusting Docker Desktop settings, adding the runner user to the correct group, and configuring the DOCKER_HOST environment variable. Importantly, this can be resolved without running the runner process as root."
  - question: "permission denied var/run/docker.sock github actions self-hosted runner Mac"
    answer: "This error occurs because the GitHub Actions runner process runs as a non-root user by default, while Docker Desktop on macOS binds its socket with restrictive group permissions. Unlike Linux, where adding a user to the docker group resolves the issue, macOS handles the Docker daemon differently, requiring additional configuration steps. The error affects both ARM64 and x86_64 Mac runners when Docker Desktop is configured the same way."
  - question: "how to run github actions self-hosted runner docker arm64 M2 Mac permission denied fix without root"
    answer: "You can resolve the Docker permission denied error on an M2 Mac self-hosted runner without granting root access to the runner process. The solution involves a combination of Docker Desktop permission settings, correct runner user group membership, and setting the DOCKER_HOST environment variable. Running the runner as root is not recommended, as it introduces a separate class of security problems."
  - question: "is docker supported on apple silicon M2 github actions runner"
    answer: "Yes, GitHub officially confirmed self-hosted runner support for Apple Silicon (M1/M2) in August 2022, and Docker Desktop runs on ARM64 macOS. However, there is a gap between official support and out-of-the-box functionality, particularly around Docker socket permissions. Teams frequently lose hours to the permission denied error even on fully supported hardware configurations."
  - question: "why use M2 Mac as github actions self-hosted runner instead of cloud"
    answer: "M2 Macs deliver approximately 2x the performance-per-watt compared to comparable Intel Xeon configurations, making them cost-effective for CI/CD workloads. They are especially attractive for long-running pipelines involving mobile builds, Rust compilation, or other native ARM64 workloads. AWS also made EC2 Mac instances running on M2 Mac mini hardware generally available, giving teams a cloud-hosted Apple Silicon option."
---

The error appears without warning: `permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock`. Build fails. Pipeline stops. The M2 Mac you spun up as a self-hosted runner — because Apple Silicon's performance-per-watt ratio is genuinely hard to argue with — becomes a roadblock instead of an asset.

This isn't a niche problem. As of early 2026, ARM64-based self-hosted runners running Docker on Apple Silicon are increasingly common in mid-size engineering teams. GitHub officially confirmed M1/M2 support for self-hosted runners back in August 2022, but the Docker permission layer on macOS has remained an ongoing friction point ever since. The gap between "supported" and "working out of the box" is where most teams lose hours.

The thesis is straightforward: the `permission denied` error on a GitHub Actions self-hosted runner running Docker on an ARM64 M2 Mac isn't a Docker bug or a GitHub bug. It's a user and socket permission mismatch with a clean, repeatable fix. Getting it wrong means either broken pipelines or a runner process running as root — which creates a different class of problem entirely.

**In brief:** The `permission denied` error stems from Docker socket ownership mismatches, not architectural incompatibility. The fix is deterministic and doesn't require running the runner as root.

Three things are true simultaneously:
- The GitHub Actions runner process runs as a non-root user by default, but Docker Desktop on macOS binds its socket with restrictive group permissions.
- The ARM64 architecture itself isn't the root cause — the same error appears on x86_64 Mac runners with identical Docker Desktop configurations.
- A combination of Docker Desktop settings, runner user group membership, and `DOCKER_HOST` environment variable configuration resolves the issue across all three common deployment patterns.

---

## Why M2 Macs Became a Self-Hosted Runner Target

Apple Silicon changed the economics of CI/CD hardware. The M2 chip family delivers roughly 2x the performance-per-watt compared to comparable Intel Xeon configurations, according to Apple's published benchmarks. For teams running long build pipelines — especially mobile, Rust, or native compilation workloads — the thermal headroom and sustained performance of M2 machines made them attractive as always-on runner hosts.

GitHub's August 2022 changelog confirmed official self-hosted runner support for Apple M1 hardware. M2 followed naturally, given ABI compatibility. By 2024, AWS had made EC2 Mac instances (running on M2 Mac mini hardware) generally available. According to a January 2026 Medium tutorial by Khoa Pham covering EC2 Mac runner setup, the installation process itself is straightforward — the complications emerge specifically at the Docker layer.

Docker Desktop on macOS manages its daemon differently than Linux. On Linux, `/var/run/docker.sock` is owned by the `docker` group, and adding a user to that group resolves permission issues cleanly. On macOS, Docker Desktop runs inside a Linux VM via the Apple Virtualization Framework on ARM64, and the socket path and ownership rules don't map 1:1 to Linux conventions. Copying Linux solutions won't work here.

The other compounding factor: GitHub's runner binary, when installed following the standard documentation, creates and runs under a `_github_runner` service account or the installing user's account. Neither typically has Docker socket access by default.

---

## Why the Permission Error Happens on ARM64 M2 Macs

The error `Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock` means the runner process can't read or write to the Docker socket file. On macOS with Docker Desktop, the socket is typically located at `~/.docker/run/docker.sock` or `/var/run/docker.sock` via a symlink Docker Desktop creates.

The runner process — running as your user or a service account — doesn't have access to that socket. On Linux, the standard fix is `sudo usermod -aG docker $USER`. On macOS ARM64, it's more nuanced because Docker Desktop doesn't use a system-level `docker` group in the same way.

Three factors collide:
- Docker Desktop's socket permissions on macOS are controlled by the app, not `/etc/group`
- The runner may run as a different user than the one who installed Docker Desktop
- `launchd` service mode uses a different user context than interactive shell sessions

This approach can also fail when teams assume the Linux group-based fix translates directly to macOS — it doesn't, and that assumption costs debugging time.

---

## The Three Common Deployment Patterns and Their Fix

Most teams hit this issue in one of three configurations. Each has a distinct resolution path.

**Pattern 1: Runner running interactively as the logged-in user**

The simplest case. Docker Desktop is installed for that user, and the socket exists at `~/Library/Group Containers/group.com.docker/run/docker.sock`. The fix: set `DOCKER_HOST=unix://$HOME/.docker/run/docker.sock` in the runner's environment, either via a `.env` file or the runner's `env` configuration. No group changes needed.

**Pattern 2: Runner installed as a `launchd` service**

The runner service runs under a system account, not your interactive user. Docker Desktop's socket is user-scoped. The fix requires either configuring Docker Desktop to use a system-accessible socket path, or running the runner service under the same user as Docker Desktop. The second option is cleaner. Use `./svc.sh install` and `./svc.sh start` under your primary user account — not root.

**Pattern 3: Runner on EC2 Mac (AWS)**

EC2 Mac instances running M2 hardware use an `ec2-user` account. Docker Desktop or Docker Engine via OrbStack needs explicit socket configuration. Khoa Pham's January 2026 Medium walkthrough notes that OrbStack works particularly well as a Docker Desktop replacement in headless and CI environments, handling socket permissions more cleanly than Docker Desktop in that context.

---

## Docker Desktop vs. OrbStack on M2 Mac Runners

| Criteria | Docker Desktop | OrbStack |
|---|---|---|
| Socket permission handling | User-scoped, requires `DOCKER_HOST` config | More permissive by default, easier CI setup |
| ARM64 native support | Yes (via Apple Virtualization Framework) | Yes (native ARM64) |
| Performance on M2 | Good | Measurably faster cold starts |
| Cost (2026) | Free for small teams; Pro at $9/user/month | $8/user/month (individual) |
| Headless/service mode | Requires workarounds | Better support for background operation |
| GitHub Actions compatibility | Full, with configuration | Full, simpler setup |
| Best for | Teams already in Docker ecosystem | CI-focused M2 runner setups |

OrbStack's socket behavior is the key differentiator. It doesn't restrict socket access to a single user session the way Docker Desktop does — which is why it's becoming the preferred choice for self-hosted ARM64 runner setups in 2026.

That said, Docker Desktop isn't wrong. It's designed for interactive desktop use, not headless CI. If your team already uses it, fixing the `DOCKER_HOST` environment variable is a five-minute change. Switching to OrbStack makes more sense when you're building dedicated Mac runner infrastructure from scratch.

---

## Three Scenarios, Three Fixes

**Scenario 1: Developer-run M2 Mac as an occasional runner**

The runner runs interactively, Docker Desktop is installed normally. Add this to the runner's `.env` file in the runner directory:

```
DOCKER_HOST=unix:///Users/YOUR_USERNAME/.docker/run/docker.sock
```

Restart the runner. No elevated permissions required. The fix applies immediately.

**Scenario 2: Dedicated M2 Mac mini as a persistent runner (on-prem)**

Install the runner as a `launchd` service under your primary macOS user — not root. Confirm Docker Desktop is set to start at login for the same user. Add `DOCKER_HOST` to the runner environment. Test with a workflow that runs `docker info` as the first step. If that passes, the socket issue is resolved.

**Scenario 3: EC2 Mac M2 instance (AWS)**

Follow the runner installation steps from GitHub's docs, then configure either Docker Desktop with explicit socket path settings or switch to OrbStack. Set `DOCKER_HOST` in the runner's environment variables. Khoa Pham's January 2026 guide covers the EC2-specific `launchd` configuration in detail and is worth bookmarking for this exact setup.

**What to watch:**
- Docker Desktop's macOS socket handling may improve in upcoming releases — the company is aware of the CI and headless pain point
- GitHub's own hosted ARM64 runners, currently in limited availability for macOS, could reduce the need for self-hosted M2 setups by mid-2026
- OrbStack's roadmap includes enhanced CI mode features, per their public GitHub discussions

---

## Where This Lands

The fix comes down to three consistent insights:

- **The error is a socket permission mismatch**, not an ARM64 or GitHub compatibility issue
- **`DOCKER_HOST` environment configuration** resolves most cases without touching system permissions
- **OrbStack outperforms Docker Desktop** for headless CI runner scenarios on M2 hardware
- **Service account alignment** — runner process user matching Docker Desktop user — prevents the issue at the root

Over the next 6-12 months, expect GitHub's hosted macOS ARM64 runners to expand availability, reducing the operational overhead of maintaining self-hosted M2 infrastructure. But for teams with performance-sensitive builds or genuine cost constraints, M2 self-hosted runners remain a strong option. OrbStack's trajectory suggests it'll become the default Docker runtime recommendation for macOS CI by late 2026.

The action is concrete: audit which user your runner service runs as, confirm it matches your Docker runtime's socket owner, and set `DOCKER_HOST` explicitly. That sequence solves the issue in under 10 minutes.

> **Key Takeaways**
> - The `permission denied` error is a socket ownership mismatch, not an ARM64 compatibility bug
> - `DOCKER_HOST` environment variable configuration fixes most cases without elevated permissions
> - Match your runner's service account user to the user running Docker Desktop — that's the root fix
> - OrbStack handles macOS socket permissions more cleanly than Docker Desktop in headless CI environments
> - EC2 Mac M2 runners follow the same pattern; Khoa Pham's January 2026 guide covers the AWS-specific `launchd` details
> - GitHub's hosted ARM64 macOS runners are expanding — self-hosted M2 infrastructure may become optional by mid-2026

What's your current runner deployment pattern — interactive, service mode, or EC2 Mac? The fix path differs enough that it's worth knowing before you start.

## References

1. [GitHub Actions: Self-hosted runners now support Apple M1 hardware - GitHub Changelog](https://github.blog/changelog/2022-08-09-github-actions-self-hosted-runners-now-support-apple-m1-hardware/)
2. [How to install GitHub action runner on EC2 Mac | by Khoa Pham | Indie Goodies | Jan, 2026 | Medium](https://medium.com/fantageek/how-to-install-github-action-runner-on-ec2-mac-088b7e62b8c4)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
