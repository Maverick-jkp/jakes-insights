---
title: "GitHub Actions Self-Hosted Runner Docker Compose ARM64 M2 Mac Permission Denied Fix"
date: 2026-05-08T20:32:07+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Docker"]
description: "Fix GitHub Actions self-hosted runner permission denied errors on ARM64 M2 Macs with Docker Compose. Over 200 replies on issue #4302 led to this patch."
image: "/images/20260508-github-actions-selfhosted-runn.webp"
technologies: ["Docker", "GitHub Actions", "Linux"]
faq:
  - question: "github actions self-hosted runner docker compose arm64 m2 mac permission denied fix"
    answer: "The permission denied error on GitHub Actions self-hosted runners running Docker Compose on ARM64 M2 Macs is caused by a UID/GID mismatch introduced in runner v2.332.0, where stricter ownership checks block writes to GITHUB_ENV and workspace directories. The fix requires explicitly aligning the UID and GID between the runner process and the Docker container user, not just applying chmod patches. Docker Desktop on Apple Silicon compounds the issue because containers run inside a Linux VM with a separate UID namespace from the host Mac user."
  - question: "why does github actions runner v2.332.0 cause permission denied errors in docker containers"
    answer: "Runner v2.332.0 introduced stricter ownership checks when the runner agent writes to GITHUB_ENV and the workspace directory inside container jobs. If the UID of the process inside the Docker container does not match the UID the runner expects on the host, writes to these paths fail with a permission denied error. This was confirmed in the official GitHub Actions runner issue tracker under issue #4302, which received over 200 thread replies before a patch shipped."
  - question: "docker desktop apple silicon uid namespace mismatch github actions self-hosted runner"
    answer: "Docker Desktop on Apple Silicon runs containers inside a lightweight Linux VM using Apple's Virtualization Framework, which maintains its own UID/GID namespace separate from the host Mac. This means a container running as root (UID 0) inside Docker is seen by the host-side runner process, typically running as Mac user UID 501 or 502, as a UID mismatch at the volume mount boundary. When combined with the stricter permission checks in runner v2.332.0, this mismatch causes CI pipeline failures on ARM64 M2 Macs."
  - question: "does chmod fix github actions self-hosted runner permission denied on m2 mac docker compose arm64"
    answer: "Applying chmod patches does not fix the root cause of the github actions self-hosted runner docker compose arm64 m2 mac permission denied error and only masks the symptom temporarily. The underlying issue is a file ownership mismatch between the runner process UID on the host and the user UID inside the Docker container. A proper fix requires explicitly aligning the UID and GID values so the runner's post-v2.332.0 ownership checks pass correctly."
  - question: "github actions container job cannot write to GITHUB_ENV self-hosted runner apple silicon"
    answer: "When a GitHub Actions container job cannot write to GITHUB_ENV on a self-hosted runner running on Apple Silicon, the cause is typically a UID mismatch between the Docker container user and the host runner process, made worse by runner v2.332.0's stricter ownership enforcement. Docker Desktop on M2 Macs introduces a separate UID namespace through its Linux VM layer, making this conflict more frequent than on x86 machines. Resolving it requires aligning the container user's UID and GID with those of the runner process on the host."
aliases:
  - "/tech/2026-05-08-github-actions-selfhosted-runner-docker-compose-ar/"

---

The `permission denied` error on a GitHub Actions self-hosted runner isn't random. It's structural—and on ARM64 M2 Macs running Docker Compose, it's hitting teams hard enough that the GitHub Actions runner issue tracker logged over 200 thread replies on a single bug report (actions/runner #4302) before a patch shipped.

> **Key Takeaways**
> - The `permission denied` error on GitHub Actions self-hosted runners running Docker Compose on ARM64 M2 Macs traces directly to a file ownership mismatch introduced in runner v2.332.0, confirmed in the official GitHub Actions runner issue tracker.
> - ARM64 architecture on Apple Silicon adds a second layer of friction: Docker Desktop on M2 Macs runs containers via a Linux VM with a separate UID namespace, making host-to-container permission conflicts more frequent than on x86 machines.
> - The fix requires explicit UID/GID alignment between the runner process and the Docker container user—not just `chmod` patches, which mask the symptom without resolving the root cause.
> - Teams running self-hosted runners on M2 Macs saw CI pipeline failures spike after upgrading to runner v2.332.0, with `GITHUB_ENV` and workspace directory writes blocked at the container boundary.

---

## Background: How ARM64 and Runner v2.332.0 Created the Perfect Storm

Apple Silicon adoption accelerated fast. By early 2026, M2 and M3 Macs account for the majority of developer machines shipped by Apple—and a growing share of those machines run GitHub Actions self-hosted runners locally or in small-team CI setups. It's a practical choice: the hardware is fast, power-efficient, and already on the desk.

The trouble started with runner v2.332.0. According to the GitHub Actions runner issue tracker (#4302), this release changed how the runner agent writes to `GITHUB_ENV` and the workspace directory inside container jobs. Before the update, container jobs inherited file permissions more loosely. After it, the runner enforces stricter ownership checks—and if the UID of the process inside the Docker container doesn't match the UID the runner expects on the host, writes to `GITHUB_ENV`, `GITHUB_WORKSPACE`, and related paths fail with `permission denied`.

On x86 Linux, this is annoying. On ARM64 M2 Macs, it compounds. Docker Desktop on Apple Silicon runs containers inside a lightweight Linux VM (using Apple's Virtualization Framework). That VM maintains its own UID/GID namespace. So when a container runs as `root` (UID 0) inside Docker, the host-side runner process—running as your Mac user (typically UID 501 or 502)—sees a UID mismatch at the volume mount boundary. The runner's stricter post-v2.332.0 ownership checks then reject the write. Two separate issues collide. One error message.

The n8n community documented a nearly identical pattern on Latenode's forum, where container jobs in GitHub Actions workflows failed because the runner couldn't write environment variables mid-job—same root cause, different application stack.

---

## Main Analysis

### Key Point #1: The UID Mismatch Is the Actual Problem

Most engineers hit `permission denied` and reach for `chmod 777`. Wrong move. That patches the symptom on the next run, then breaks again after a runner restart or Docker volume recreate.

The real fix is UID alignment. The runner process on the host runs as a specific user. The container needs to run as the same UID. On a Mac, find your UID with `id -u` (typically `501`). Then in your `docker-compose.yml`:

```yaml
services:
  app:
    image: your-image:latest
    user: "501:501"
```

Or pass it dynamically in the GitHub Actions workflow:

```yaml
- name: Run container job
  run: |
    docker compose run --user $(id -u):$(id -g) app your-command
```

This makes the container process write files with the same UID the runner expects. No ownership conflict. No `permission denied`.

### Key Point #2: ARM64-Specific Docker Compose Wrinkles

Docker Compose on ARM64 M2 Macs has one behavior that catches teams off guard: the `platform` field. If your image was built for `linux/amd64` and you're running on ARM64 without specifying `platform: linux/arm64`, Docker Desktop silently runs it under Rosetta emulation. Emulated containers have slightly different behavior at volume mount boundaries—and the UID mapping through the VM layer gets murkier.

Specify the platform explicitly:

```yaml
services:
  app:
    image: your-image:latest
    platform: linux/arm64
    user: "501:501"
```

And for self-hosted runner setups, make sure the runner itself was installed as the correct user—not root. The OneUptime blog's 2026 guide on configuring self-hosted runners flags this directly: running the runner agent as root on macOS creates downstream permission issues because Docker Desktop on Mac deliberately restricts root-level host access for security reasons.

### Key Point #3: The `GITHUB_ENV` Write Failure Is a Separate Layer

Even after fixing container user alignment, some teams on M2 Macs still see `GITHUB_ENV` write failures. This is runner v2.332.0's specific regression. The runner writes `GITHUB_ENV` to a temp path on the host, then mounts it into the container. If the container process can't write back to that path—because of the UID mismatch—the env var never propagates.

The workaround until a full patch ships: explicitly mount the `GITHUB_ENV` file path with correct permissions in your Compose file, or use the `--env-file` flag to pass variables at container start rather than writing them mid-job.

### Comparison: Fix Approaches for the ARM64 M2 Mac Permission Denied Issue

| Approach | Fixes Root Cause | Works on ARM64 | Survives Runner Restart | Complexity |
|---|---|---|---|---|
| `chmod 777` on workspace | ❌ No | ✅ Yes | ❌ No | Low |
| `user: "UID:GID"` in Compose | ✅ Yes | ✅ Yes | ✅ Yes | Low |
| `--user $(id -u):$(id -g)` flag | ✅ Yes | ✅ Yes | ✅ Yes | Medium |
| Rebuild image with correct UID baked in | ✅ Yes | ✅ Yes | ✅ Yes | High |
| Pin runner to pre-v2.332.0 version | ❌ Avoids issue | ✅ Yes | ✅ Yes | Low (risky) |

The `user: "UID:GID"` approach in `docker-compose.yml` wins on almost every axis. It's declarative, reproducible, and doesn't require workflow-level changes. Pinning the runner version is a short-term workaround that accumulates security debt fast—GitHub's runner release cadence is aggressive, and older versions drop security patches quickly.

---

## Practical Implications: Who Gets Hit and What to Do

**Scenario 1: Small team running self-hosted runners on M2 MacBook Pros.**
This is the highest-impact group right now. Apply the fix at the Compose file level immediately. Add `user: "501:501"` (or your actual UID) and add `platform: linux/arm64` to every service. Run `id -u` and `id -g` on the runner machine and hardcode those values in the Compose file or pass them as build args.

**Scenario 2: Docker Compose CI pipelines migrated from Linux x86 runners to M2 Mac runners.**
These pipelines frequently omit `platform` declarations because x86 images worked fine before. Audit every `docker-compose.yml` for missing platform tags. Mismatched architecture triggers Rosetta emulation, which amplifies the UID mapping problem at the VM layer.

**Scenario 3: Workflows that write environment variables mid-job via `GITHUB_ENV`.**
Add an explicit volume mount for the `GITHUB_ENV` path in the container definition, or restructure the workflow to pass all required env vars at container start. The mid-job write pattern is fragile post-v2.332.0 on M2 Mac runners regardless of other fixes.

This approach can fail when your team runs multiple developers' machines as self-hosted runners simultaneously—each Mac will have a different UID, which means a hardcoded `user: "501:501"` breaks on any machine where that UID doesn't match. In that scenario, use the dynamic `--user $(id -u):$(id -g)` flag at the workflow level instead, or standardize UIDs across runner machines during provisioning.

**What to watch:** GitHub's runner team acknowledged the v2.332.0 regression in issue #4302. A targeted fix for the `GITHUB_ENV` write path is in progress as of Q1 2026. Watch the runner changelog for v2.334.0 and above—that's the likely landing zone for the patch.

---

## Conclusion & Future Outlook

The fix comes down to three things: align UIDs between the host runner and container process, declare the ARM64 platform explicitly in Compose files, and work around the v2.332.0 `GITHUB_ENV` write regression until the patch ships.

Three things to carry forward:

- Runner v2.332.0 introduced stricter ownership checks that break container jobs when UIDs don't match
- ARM64 M2 Macs add a VM-layer UID namespace that makes mismatches more likely than on x86 Linux
- `user: "UID:GID"` in `docker-compose.yml` is the most durable fix — `chmod 777` is not a fix, it's a timer until the next failure

Over the next 6–12 months, expect GitHub to ship better UID auto-detection in the runner agent for containerized jobs, and Docker Desktop to improve its UID passthrough behavior on Apple Silicon. Both teams are aware of the friction. But in May 2026, the fix is manual and must be applied per-project.

Check your runner UID, match it in your Compose file, pin your platform to `linux/arm64`, and stop letting a one-line config gap burn your CI pipeline.

**What's your current runner setup—hosted GitHub runners or self-hosted on Apple Silicon? Drop your config in the comments.**

## References

1. [How to resolve n8n container permissions issue in GitHub Actions? - N8n - Latenode Official Communit](https://community.latenode.com/t/how-to-resolve-n8n-container-permissions-issue-in-github-actions/18058)
2. [v2.332.0: Container jobs fail with permission denied on GITHUB_ENV and workspace after upgrade from ](https://github.com/actions/runner/issues/4302)
3. [How to Configure Self-Hosted Runners in GitHub Actions](https://oneuptime.com/blog/post/2026-01-25-github-actions-self-hosted-runners/view)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
