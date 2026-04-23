---
title: "GitHub Actions Self-Hosted Runner Docker ARM64 Apple Silicon Timeout Issue Workaround"
date: 2026-04-23T20:28:20+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Python"]
description: "Fix silent timeout failures in GitHub Actions self-hosted runner on Docker ARM64 Apple Silicon — no error, no exit code, just a hanging workflow."
image: "/images/20260423-github-actions-selfhosted-runn.webp"
technologies: ["Python", "Docker", "GitHub Actions", "Linux", "Go"]
faq:
  - question: "github actions self-hosted runner docker arm64 apple silicon timeout issue workaround"
    answer: "The most effective workarounds for this issue include switching from Docker Desktop to Colima, using native ARM64 runner binaries instead of containerized runners, or adjusting ephemeral container configurations to reduce virtualization overhead. Teams who switched to Colima or native ARM64 binaries reported timeout failures dropping from multiple daily occurrences to near-zero. The root cause is a compatibility stack involving Rosetta emulation, Docker Desktop's virtualization layer, and the runner's process-health checks conflicting under load."
  - question: "why does github actions self-hosted runner hang silently with no error on mac m1 m2"
    answer: "The silent hang occurs because the runner process loses track of the Docker child process during execution, receiving no exit signal and simply waiting until the job timeout kills the workflow. This leaves no error code or stack trace in the logs — just the last successful step followed by nothing. It is a documented interaction between GitHub's runner health checks and the Linux VM layer that Docker requires on macOS Apple Silicon."
  - question: "colima vs docker desktop for github actions self-hosted runner on apple silicon"
    answer: "Community reports in 2026 indicate that switching from Docker Desktop to Colima significantly reduces silent timeout failures on Apple Silicon self-hosted runners, with some teams going from multiple daily failures to near-zero incidents. Colima introduces less virtualization overhead compared to Docker Desktop on ARM64, which reduces the likelihood of the runner losing track of child processes. It is one of three proven workarounds for the github actions self-hosted runner docker arm64 apple silicon timeout issue, and is generally the lowest-cost switch for teams already using Docker-based workflows."
  - question: "how to fix github actions job timeout with no error on self-hosted mac runner"
    answer: "If your GitHub Actions job times out silently on a Mac self-hosted runner, the likely cause is Docker Desktop's virtualization layer interfering with the runner's process-health checks on ARM64 hardware. Proven fixes include replacing Docker Desktop with Colima, switching to native ARM64 runner binaries, or restructuring your pipeline to use ephemeral containers differently to reduce VM interaction. GitHub has not released an official fix for this specific ARM64 Docker interaction as of April 2026, so community workarounds remain the primary solution."
  - question: "is it worth using apple silicon mac mini as github actions self-hosted runner in 2026"
    answer: "Apple Silicon Mac Minis and Mac Studios can reduce CI/CD compute costs by 60–70% compared to cloud runners for heavy build workloads, making them financially attractive as self-hosted GitHub Actions runners. However, teams should be aware of the github actions self-hosted runner docker arm64 apple silicon timeout issue workaround requirement, as Docker-based pipelines can experience silent failures without proper configuration. With the right setup — such as using Colima instead of Docker Desktop or native ARM64 binaries — the hardware performs reliably and the cost savings hold up."
---

Build pipelines don't fail loudly. They just stop.

No error, no stack trace, no exit code — the runner goes quiet, and your workflow sits there, burning minutes until GitHub's timeout kills it. That's the reality many teams face when running the GitHub Actions self-hosted runner with Docker on ARM64 Apple Silicon machines in 2026.

> **Key Takeaways**
> - Silent timeout failures on ARM64 Apple Silicon self-hosted runners are a documented, recurring issue in 2026, with reports surfacing across GitHub's own issue tracker and r/github, affecting teams who migrated CI/CD pipelines to Apple M-series hardware.
> - The root cause isn't a single bug — it's a stack of compatibility layers: Rosetta emulation, Docker Desktop's virtualization overhead on ARM64, and the runner's process-health checks interacting badly under load.
> - GitHub's `actions/runner` release cadence has accelerated in 2026 (over 12 releases since January), but the ARM64 Docker interaction specifically still lacks an official fix as of April 2026.
> - Three proven workarounds exist — each with different cost/stability trade-offs — and choosing the right one depends on whether you're running ephemeral containers or persistent runner hosts.
> - Teams that switched from Docker Desktop to `colima` or native ARM64 runner binaries reported timeout frequency dropping from multiple daily failures to near-zero in community threads on r/github.

---

## Why ARM64 Apple Silicon CI Pipelines Are Breaking Now

Apple Silicon's CI story looked promising in 2022. M1 machines were fast, power-efficient, and cheap compared to cloud runners. By 2024, engineering teams at mid-size companies started racking Mac Minis and Mac Studios as self-hosted GitHub Actions runners to cut cloud compute costs — sometimes by 60–70% on heavy build workloads, according to cost analyses shared in the GitHub Community forum.

The architecture shift created a compounding problem. GitHub's `actions/runner` binary is compiled natively for `linux/arm64` and `osx-arm64`, which is fine. Docker on macOS, though, runs inside a Linux VM — and on Apple Silicon, that VM layer (whether via Docker Desktop or alternatives) adds latency and process isolation that the runner's internal health checks weren't designed around.

The specific failure mode looks like this: a Docker step starts, the container launches, and then the runner process loses track of the child process. No signal is sent back. The runner waits. GitHub's job timeout (default: 6 hours, but most teams set it to 30–60 minutes) eventually kills it. The workflow log shows the last successful step, then nothing. No "Process exited with code X." Just silence.

This pattern showed up in a Reddit thread on r/github titled *"Self-hosted github runner just fails without any error sometimes"* — and the comments confirmed it's not isolated. Multiple teams across different repo sizes and macOS versions reported identical behavior. The `actions/runner` GitHub releases page shows the project has been active (12+ releases in Q1 2026 alone), but ARM64 Docker timeout handling hasn't been explicitly addressed in any release note through April 2026.

The timing matters because Apple Silicon Mac adoption in dev teams peaked in 2025. More self-hosted runners on ARM64 means more exposure to this exact failure mode.

---

## Diagnosing and Fixing the Silence

### Why the Runner Goes Silent: The Process Tracking Problem

Docker on macOS doesn't run containers directly on the host kernel. It runs them inside a Linux VM. That indirection breaks the assumption baked into the GitHub Actions runner: that spawned child processes are directly visible to the runner's process tree.

When a `docker run` command is issued from a macOS runner, the actual container process lives inside the VM. If Docker Desktop's VM layer hiccups — due to memory pressure, a VM restart, or a networking blip — the runner's child process handle becomes invalid. The runner doesn't detect this as a failure. It just waits for output that'll never come.

M2 and M3 machines with 16GB RAM can hit this under parallel job loads. Two concurrent Docker builds on a 16GB M2 Mac Mini can push Docker Desktop's VM to swap, which triggers exactly this kind of silent drop.

### The Rosetta Factor: x86 Images Making It Worse

Many teams still pull `linux/amd64` Docker images because ARM64 equivalents aren't published yet. Docker Desktop on Apple Silicon handles this via Rosetta 2 emulation. That's a third layer of translation: macOS → Linux VM → x86 emulation.

Rosetta works well for most workloads. But under CI load, the emulation adds non-deterministic latency spikes. A step that normally completes in 8 seconds might take 45 seconds under emulation plus memory pressure. If the runner's internal step-level watchdog interprets that gap as a hang, it can trigger a silent kill without propagating an error.

The fix is straightforward but easy to miss: explicitly set `--platform linux/arm64` in your Dockerfile or `docker-compose.yml` and verify your base images have ARM64 variants. `ubuntu:22.04`, `node:20`, `python:3.12`, and most major images on Docker Hub now ship multi-arch manifests. Pull the ARM64 layer directly and skip Rosetta entirely.

### Workaround Comparison: Three Paths Forward

| Approach | Setup Complexity | Timeout Fix Rate | Ongoing Maintenance | Best For |
|---|---|---|---|---|
| Switch Docker Desktop → `colima` | Medium (1–2 hours) | High (community-reported near-zero failures) | Low | Teams with persistent runner hosts |
| Pin `actions/runner` to pre-regression version | Low (15 min) | Medium (version-dependent) | High (manual updates) | Quick triage, not long-term |
| Move to native `osx-arm64` runner (no Docker) | High (pipeline rewrite) | Highest | Medium | Teams who can containerize at build time |
| Use GitHub-hosted `macos-latest-xlarge` runners | Low | Highest (managed infra) | None | Teams where cost isn't the primary constraint |

`colima` — an open-source Lima-based container runtime — runs a slimmer VM than Docker Desktop and drops the GUI overhead entirely. Teams on r/github specifically called out switching to `colima` as the fix that stuck. Install it with `brew install colima` and start it with `colima start --arch arm64 --vm-type vz --vz-rosetta`. The `--vz-rosetta` flag enables Apple's Virtualization framework with Rosetta support for x86 images, but the VM itself is leaner and more stable under load.

If changing the Docker runtime isn't an option, the next lever is the runner's `ACTIONS_RUNNER_HOOK_JOB_STARTED` configuration combined with step-level `timeout-minutes` settings. Setting `timeout-minutes: 15` at the step level — not just the job level — forces faster failure detection and surfaces the issue as an actual timeout error rather than silent death. That at least gives you actionable logs to work with.

This approach can fail, though, when the VM-level hang occurs before the step timer even starts. In those cases, no amount of timeout tuning helps. The runtime change is the only reliable path.

---

## Practical Implications: Scenarios and Recommendations

**Scenario 1: You're running persistent Mac Mini runners in-office.**

Switch to `colima` now. Docker Desktop's overhead isn't justified for headless CI use. Set `colima start` as a `launchd` service so it survives reboots. Add a pre-flight job in your workflow that runs `docker info` and fails fast if the socket isn't responding — this surfaces VM-layer failures before your actual build jobs start.

**Scenario 2: You're using ephemeral runners via `actions/runner-controller` on a macOS host.**

This is the hardest configuration. The controller's runner lifecycle assumes Linux semantics. On macOS plus Docker, each ephemeral runner that spins up a new Docker context adds VM-state overhead. Consider batching ephemeral runners or switching to longer-lived runners with job isolation handled at the container level — one runner, Docker containers per job — rather than one runner per job.

**Scenario 3: Your team needs x86 Docker images specifically due to legacy dependencies.**

Don't use Rosetta transparently. Set up a dedicated `linux/amd64` runner on a cloud instance (use a `t3.medium` for x86, not the ARM64 Graviton `t4g`) for that specific job, and route ARM64-compatible jobs to the Apple Silicon self-hosted runner. Split the matrix explicitly in your workflow YAML with `runs-on` targeting different runner labels.

**What this doesn't solve:** teams running highly parallel workloads — eight-plus concurrent Docker jobs on a single Mac host — will hit memory ceiling issues regardless of runtime choice. `colima` reduces VM overhead, but physics still applies. At that scale, distributing across multiple Mac Mini hosts or routing overflow to GitHub-hosted runners is a more honest answer than chasing runtime optimizations.

**What to watch:** GitHub's `actions/runner` v2.320+ releases in Q2 2026. The runner team has acknowledged macOS ARM64 Docker process tracking in their open issue backlog. A native fix that wraps Docker child processes with explicit PID monitoring on macOS would eliminate the root cause without requiring runtime changes. Check the release notes at `github.com/actions/runner/releases` — specifically for any mention of `DOCKER_HOST` socket handling or macOS-specific process supervision.

---

## What Comes Next

Silent timeout failures on the GitHub Actions self-hosted runner with Docker on ARM64 Apple Silicon aren't random. They're predictable, reproducible, and fixable today with the right workaround.

The failure is architectural: Docker Desktop's VM layer on macOS breaks the runner's process tracking under load. Rosetta emulation amplifies that problem when x86 images are pulled on ARM64 hosts. `colima` is the highest-signal fix for persistent runner hosts, with near-zero timeout reports from teams who've made the switch. Step-level `timeout-minutes` is the minimum mitigation if you can't change the runtime.

Over the next 6–12 months, two things could shift this landscape. GitHub may ship a macOS-specific process wrapper in the runner binary — the issue is tracked and the engineering activity is visible in their public backlog. And Docker Desktop's VM stability on Apple Silicon has improved with each major release; version 5.x (expected mid-2026) may narrow the gap further.

For now: audit your self-hosted runner setup, check whether you're pulling ARM64-native images, and if you're still on Docker Desktop for CI, try `colima` for a week. The community data is consistent enough that it's worth the experiment — even if the official fix eventually makes it unnecessary.

What's your current runner setup — Docker Desktop, `colima`, or something else? The answer matters more than most teams realize.

## References

1. [r/github on Reddit: Self-hosted github runner just fails without any error sometimes](https://www.reddit.com/r/github/comments/1nd9pkp/selfhosted_github_runner_just_fails_without_any/)
2. [Releases · actions/runner](https://github.com/actions/runner/releases)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
