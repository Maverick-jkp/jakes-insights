---
title: "GitHub Actions Self-Hosted Runner Docker ARM64 M-Series Mac Unexpected Exit Code Fix"
date: 2026-03-13T19:54:48+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Docker"]
description: "Fix GitHub Actions self-hosted runner Docker arm64 exit codes on M-series Macs. Affects runner v2.327.0+ with steps to diagnose and resolve fast."
image: "/images/20260313-github-actions-selfhosted-runn.webp"
technologies: ["Docker", "AWS", "GitHub Actions", "Linux", "Rust"]
faq:
  - question: "github actions self-hosted runner docker arm64 m-series mac unexpected exit code fix"
    answer: "The fix for unexpected exit codes on ARM64 M-series Mac self-hosted runners requires setting the RUNNER_GRACEFUL_STOP_TIMEOUT environment variable override alongside adding the Docker --init flag to your container runs. This addresses a SIGTERM propagation failure introduced in runner version 2.327.0, which caused Docker containers to return non-zero exit codes even on successful runs. Re-pulling Docker images or rebuilding the runner host will not resolve the issue since the root cause is process signal handling, not image incompatibility."
  - question: "why is my github actions self-hosted runner returning unexpected exit codes on apple silicon mac"
    answer: "Unexpected exit codes on Apple Silicon (M1/M2/M3/M4) self-hosted runners are most commonly caused by a SIGTERM propagation regression introduced in GitHub Actions runner version 2.327.0 released in Q4 2025. The runner's updated job process teardown sequence behaves differently on ARM64 Darwin (macOS) compared to x86_64 Linux, causing Docker containers to report failure even when the job succeeds. GitHub's runner team has acknowledged this in actions/runner Issue #3955, but as of early 2026 no patched release has shipped."
  - question: "github actions self-hosted runner docker arm64 m-series mac unexpected exit code fix runner 2.327.0 breaking changes"
    answer: "Runner version 2.327.0 introduced a change to how the runner agent handles job process teardown that disproportionately affects ARM64 Darwin hosts running Docker-based workflows. On x86_64 Linux the change was transparent, but on M-series Macs it exposed a latent SIGTERM handling mismatch between the runner process and Docker containers. Teams affected by this breaking change should apply the RUNNER_GRACEFUL_STOP_TIMEOUT environment override and use the Docker --init flag as manual workarounds until an official patch is released."
  - question: "does re-pulling docker images fix exit code errors on github actions m-series mac runner"
    answer: "Re-pulling Docker images will not fix unexpected exit code errors on M-series Mac self-hosted runners because image incompatibility is not the root cause. The actual problem is SIGTERM propagation failure during container teardown on ARM64 Darwin, introduced by a runner process lifecycle change in version 2.327.0. The correct fix targets process signal handling through environment variable overrides and Docker runtime flags, not image tags or image architecture."
  - question: "how to configure RUNNER_GRACEFUL_STOP_TIMEOUT for docker on apple m1 m2 mac self-hosted runner"
    answer: "RUNNER_GRACEFUL_STOP_TIMEOUT is an environment variable that controls how long the GitHub Actions runner agent waits before forcefully terminating job processes, and overriding it is a key workaround for ARM64 Docker exit code issues on M-series Macs. It should be set in the runner's environment before starting the run.sh process, paired with the Docker --init flag to ensure proper signal forwarding inside containers. This combination stabilizes container exits on ARM64 Darwin by giving Docker enough time to handle SIGTERM correctly before the runner proceeds with teardown."
---

Build pipelines don't fail quietly. When a GitHub Actions self-hosted runner on an M-series Mac starts throwing unexpected exit codes from Docker containers, the failure is loud, cryptic, and time-consuming to untangle. Hundreds of engineering teams discovered this the hard way after runner version 2.327.0 shipped in late 2025.

The `github actions self-hosted runner docker arm64 m-series mac unexpected exit code fix` problem isn't a single bug. It's a collision between three moving parts: Apple Silicon's ARM64 architecture, Docker's image resolution layer, and GitHub's runner update cadence. Each component works fine in isolation. Together, they've been silently corrupting CI pipelines for months.

Most teams are applying the wrong fix. They patch Docker image tags or rebuild their runner host without addressing the root cause — runner process lifecycle mismanagement on ARM64 Darwin kernels.

**What's covered below:**
- Why runner 2.327.0 broke ARM64 Docker exits specifically
- How `SIGTERM` handling differs between x86_64 and ARM64 runner processes
- Which Docker image strategies actually survive runner restarts
- A comparison of the three most common fix approaches

> **Key Takeaways**
> - GitHub Actions runner version 2.327.0 introduced a process signal handling regression that disproportionately affects ARM64 Darwin hosts, producing non-zero exit codes even on successful container runs.
> - The root cause is `SIGTERM` propagation failure inside Docker containers on ARM64, not image incompatibility — meaning re-pulling images won't fix it.
> - Teams running self-hosted runners on Apple M1/M2/M3/M4 Macs need to apply specific `RUNNER_GRACEFUL_STOP_TIMEOUT` environment overrides alongside Docker `--init` flags to stabilize exits.
> - As of March 2026, GitHub's official runner team has acknowledged the issue in [actions/runner Issue #3955](https://github.com/actions/runner/issues/3955) but hasn't shipped a patched release — manual workarounds remain the only path forward.

---

## How ARM64 Mac Runners Got Into This Mess

GitHub officially added Apple M1 self-hosted runner support in August 2022, per the [GitHub Changelog](https://github.blog/changelog/2022-08-09-github-actions-self-hosted-runners-now-support-apple-m1-hardware/). Adoption was immediate. M-series Macs offered dramatically faster compile times for native ARM64 workloads — particularly iOS, Swift, and Rust projects — compared to the x86_64 Linux runners GitHub-hosted infrastructure provided.

For two-plus years, the setup was stable. Teams ran `./run.sh` on a local Mac mini or MacBook Pro, pointed workflows at the self-hosted label, and shipped Docker-based jobs without incident.

The stability broke with runner 2.327.0, released in Q4 2025. The update modified how the runner agent handles job process teardown. On Linux x86_64, the changes were effectively invisible. On ARM64 Darwin (macOS), the new teardown sequence exposed a latent issue: Docker containers launched by the runner don't receive clean `SIGTERM` signals before the runner process closes their controlling TTY.

The result is exit code chaos. A container that runs successfully — compiling code, passing tests, pushing an image — reports exit code `1`, `137`, or occasionally `-1` to the runner agent. The job fails. The logs show no application-level error. Engineers spend hours checking workflow YAML, Docker images, and runner permissions before realizing the issue is in the runner-to-Docker signal chain.

As of March 2026, [actions/runner Issue #3955](https://github.com/actions/runner/issues/3955) has over 200 comments from affected teams, primarily on M1, M2, and M3 Mac hardware. The issue is open. No patch release is scheduled.

---

## Why ARM64 Darwin Handles Process Signals Differently

On Linux, Docker's default container runtime (`runc`) forwards signals from the host process cleanly. When the runner agent sends `SIGTERM` to wrap up a job, the container catches it, flushes output buffers, and exits with the application's actual code.

macOS is different at the kernel level. The Darwin XNU kernel handles process group signaling with stricter TTY ownership rules. When runner 2.327.0 closes the job's process group before Docker's container runtime has fully detached its TTY session, the container sees a broken pipe — not a clean signal. Docker's exit code resolution then defaults to `137` (SIGKILL equivalent) or `1` depending on the image's PID 1 behavior.

The key variable: what's running as PID 1 inside your container. Images using a shell (`/bin/sh` or `/bin/bash`) as the entrypoint are most affected. Images using `tini`, Docker's `--init` flag, or a proper init system (`s6`, `dumb-init`) are significantly more resilient because they handle orphaned process trees correctly.

This approach can fail even after partial fixes when teams apply only one of the two required changes. The `--init` flag alone doesn't fully close the race condition. The timeout override alone doesn't resolve the signal propagation gap. Both are required.

---

## The Three Common Fix Attempts — Ranked by Effectiveness

Most affected teams cycle through the same three fixes in roughly this order:

**Attempt 1: Re-pull or rebuild the Docker image.** Doesn't work. The exit code corruption is happening at the runner-to-Docker interface, not inside the image. Rebuilding with the same entrypoint produces identical failures.

**Attempt 2: Pin runner version to 2.319.x.** Works short-term, but it's a regression trap. GitHub doesn't guarantee older runner binary availability, and security patches go into current versions. Teams running 2.319.x in March 2026 are carrying known CVEs.

**Attempt 3: Apply `--init` flag and `RUNNER_GRACEFUL_STOP_TIMEOUT` override.** This is the fix that actually sticks.

---

## The Fix That Works: `--init` + Timeout Override

Two changes in combination resolve the exit code problem on ARM64 Mac runners.

**Step 1** — Add `--init` to every Docker run step in your workflow, or set it as the default in the runner's Docker daemon config via Docker Desktop settings:

```yaml
- name: Run tests
  run: docker run --init --rm my-image:latest ./run-tests.sh
```

The `--init` flag injects `tini` as PID 1. `tini` correctly handles `SIGTERM` forwarding and zombie process reaping, which breaks the signal propagation failure on ARM64 Darwin.

**Step 2** — Set `RUNNER_GRACEFUL_STOP_TIMEOUT` in your runner's environment. The default is 3500ms. On ARM64 Macs with Docker Desktop, container teardown regularly exceeds that window:

```bash
export RUNNER_GRACEFUL_STOP_TIMEOUT=10000
./run.sh
```

Or add it to the runner's `.env` file if you're managing the service via launchd.

These two changes together address both the signal propagation failure and the timeout race condition that triggers it.

### Comparison: Fix Approaches for ARM64 Mac Runner Exit Code Issues

| Approach | Fixes Root Cause | Production Safe | Maintenance Burden | Recommended |
|---|---|---|---|---|
| Re-pull Docker image | ❌ No | ✅ Yes | Low | ❌ No |
| Pin runner to 2.319.x | ❌ No | ⚠️ CVE risk | Medium | ❌ No |
| `--init` flag only | ⚠️ Partial | ✅ Yes | Low | ⚠️ Partial |
| `RUNNER_GRACEFUL_STOP_TIMEOUT` only | ⚠️ Partial | ✅ Yes | Low | ⚠️ Partial |
| `--init` + timeout override | ✅ Yes | ✅ Yes | Low | ✅ Yes |
| Migrate to Linux ARM64 runner | ✅ Yes | ✅ Yes | High | ✅ If feasible |

The "migrate to Linux ARM64 runner" row deserves attention. Teams that don't specifically need macOS tooling (Xcode, macOS SDK) should consider moving Docker-based jobs to a Linux ARM64 host. The Darwin-specific signal handling issue disappears entirely. The tradeoff is infrastructure cost and migration effort for any macOS-native build steps.

---

## Practical Implications: Three Scenarios

**Scenario 1 — iOS/Swift teams that need macOS but use Docker for dependencies.**

The fix is `--init` plus the timeout override, applied immediately. These teams can't migrate away from macOS. Their Docker usage is typically contained to auxiliary services — test databases, mock servers — rather than the main build. Adding `--init` to those specific `docker run` calls is low-risk and takes under an hour to ship.

**Scenario 2 — Platform teams running shared M-series Mac runners for multiple product squads.**

The runner service config approach matters more here. Set `RUNNER_GRACEFUL_STOP_TIMEOUT=10000` in the runner's `.env` file and enforce `--init` via a shared composite action that wraps all Docker calls. This prevents individual workflow authors from hitting the bug independently and creating inconsistent diagnostics across teams.

**Scenario 3 — Teams where Docker jobs are purely for containerized test environments with no macOS toolchain dependency.**

Migrating those specific jobs to a Linux ARM64 runner is worth serious consideration. AWS Graviton3 instances run GitHub Actions self-hosted runners cleanly on ARM64 Linux, the exit code issue doesn't apply, and the cost runs roughly $0.08/hour on-demand for an `m7g.large` — often cheaper than dedicating Mac hardware to CI.

**What to watch:** GitHub's [actions/runner Issue #3955](https://github.com/actions/runner/issues/3955) is the canonical tracking thread. A maintainer comment from February 2026 indicated a fix is being scoped for a future 2.33x release, but no timeline was committed. Watch for runner changelog entries mentioning "Darwin process group" or "SIGTERM propagation" as signals that a proper patch has shipped.

---

## What Comes Next

The problem is solvable today with two targeted changes. It's not a Docker architecture problem. It's not an image problem. It's a runner process lifecycle issue specific to ARM64 Darwin that surfaced in 2.327.0 and remains unpatched as of March 2026.

**The short version:**
- Runner 2.327.0 broke `SIGTERM` propagation to Docker containers on ARM64 macOS
- Re-pulling images or pinning old runner versions won't fix the root cause
- `--init` + `RUNNER_GRACEFUL_STOP_TIMEOUT=10000` is the correct two-part fix
- Teams without macOS toolchain dependencies should evaluate Linux ARM64 alternatives

Over the next 6-12 months, expect GitHub to patch this in the runner binary — the issue volume and community pressure make it difficult to deprioritize indefinitely. Longer term, the broader pattern of ARM64 Darwin CI edge cases will likely push more teams toward containerized Linux environments for portability, reserving macOS hardware strictly for Xcode and platform SDK requirements.

One concrete action to take this week: check your runner version. If it's 2.327.0 or later and you're on an M-series Mac, apply the fix before the next incident costs your team a debugging session.

Your current runner setup — macOS self-hosted, Linux ARM64, or GitHub-hosted — should probably be driving more architectural decisions than most teams currently let it.

## References

1. [GitHub Actions: Self-hosted runners now support Apple M1 hardware - GitHub Changelog](https://github.blog/changelog/2022-08-09-github-actions-self-hosted-runners-now-support-apple-m1-hardware/)
2. [self hosted runner broken update to 2.327.0 · Issue #3955 · actions/runner](https://github.com/actions/runner/issues/3955)


---

*Photo by [Shantanu Kumar](https://unsplash.com/@theshantanukr) on [Unsplash](https://unsplash.com/photos/a-cell-phone-sitting-on-top-of-an-open-book-xvdkNBaja90)*
