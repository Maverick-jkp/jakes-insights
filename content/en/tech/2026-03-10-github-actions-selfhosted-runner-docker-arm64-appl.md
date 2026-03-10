---
title: "GitHub Actions Self-Hosted Runner Docker ARM64 Apple Silicon Permission Denied Fix"
date: 2026-03-10T19:56:40+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Docker"]
description: "Fix GitHub Actions self-hosted runner Docker ARM64 permission denied on Apple Silicon M1/M2/M3 — stop that exit code 1 from killing your builds."
image: "/images/20260310-github-actions-selfhosted-runn.webp"
technologies: ["Docker", "AWS", "GitHub Actions", "Linux", "Rust"]
faq:
  - question: "github actions self-hosted runner docker arm64 apple silicon permission denied fix"
    answer: "The permission denied error on GitHub Actions self-hosted runners with Docker on Apple Silicon is caused by a Unix permissions mismatch between the runner process user and the Docker socket at /var/run/docker.sock. Unlike Linux, macOS with Docker Desktop does not automatically create a docker group at install time, so the runner user lacks access to the socket. The fix involves either adding the runner user to the docker group, adjusting socket permissions directly, or running the runner as the same user who owns the Docker socket."
  - question: "why does docker permission denied error happen on M1 M2 Mac GitHub Actions runner"
    answer: "On Apple Silicon Macs running macOS, Docker Desktop does not create a docker group the same way Linux distributions like Ubuntu or Debian do during Docker Engine installation. This means the user running the GitHub Actions runner daemon does not automatically inherit access to /var/run/docker.sock. The same issue reproduces identically on AWS EC2 Mac instances such as m1.metal and m2.metal, so it is not specific to local development machines."
  - question: "how to add github actions runner user to docker group on mac"
    answer: "To fix Docker socket access for a self-hosted GitHub Actions runner on macOS, you need to add the runner user to the docker group using the command 'sudo dseditgroup -o edit -a YOUR_USERNAME -t user docker'. After adding the user, the runner process must be restarted for the group membership change to take effect. This is one of three documented approaches, and it is generally the recommended starting point for most teams due to its simplicity."
  - question: "github actions self-hosted runner docker arm64 apple silicon permission denied fix for AWS EC2 Mac instances"
    answer: "AWS EC2 Mac instances running M1 or M2 hardware reproduce the same Docker socket permission denied error as physical Apple Silicon Macs when used as GitHub Actions self-hosted runners. The root cause is identical: the GitHub Actions runner process user does not have access to /var/run/docker.sock because macOS does not configure a docker group automatically during Docker Desktop installation. Applying the same fixes used on local Apple Silicon machines, such as adding the runner user to the docker group, resolves the issue on EC2 Mac instances as well."
  - question: "process usr bin docker failed with exit code 1 github actions self-hosted runner"
    answer: "The error 'The process /usr/bin/docker failed with exit code 1' in GitHub Actions self-hosted runner logs typically indicates a Docker socket permission problem rather than a bug in Docker itself or your docker-compose configuration. The runner process does not have the necessary Unix permissions to communicate with the Docker daemon via /var/run/docker.sock. Resolving the socket permission mismatch by adjusting user group membership or socket ownership will fix this error and restore the pipeline."
---

The error hits mid-pipeline and kills your build instantly: `The process '/usr/bin/docker' failed with exit code 1`. No stack trace. No obvious cause. Just a dead CI run on hardware that cost you real money.

If you're running a GitHub Actions self-hosted runner on Apple Silicon — an M1, M2, or M3 Mac, either physical or on AWS EC2 Mac instances — this `permission denied` error on Docker ARM64 is one of the most common CI blockers teams hit in 2026. And it's completely fixable once you understand why it happens.

The root cause isn't Docker itself. It isn't your `docker-compose.yml`. It's a Unix permissions mismatch between the user running the GitHub Actions runner process and the Docker socket at `/var/run/docker.sock`. Apple Silicon Macs running macOS have slightly different default group configurations compared to Linux x86_64 runners, and the GitHub Actions runner daemon doesn't automatically inherit the Docker socket access it needs.

This piece covers:
- Why the ARM64 permission error is more common than on x86 Linux
- The three main fix approaches and their real trade-offs
- Which solution fits which team size and security posture
- What to watch as EC2 Mac instance adoption grows through 2026

**The short version:** This is a Unix socket permissions problem, not a Docker or ARM64 architecture bug. Fixing it requires adding the runner user to the `docker` group, adjusting socket permissions, or running the runner as the same user who owns the Docker socket.

Three things to know upfront:
1. The error surfaces consistently because macOS doesn't create a `docker` group at install time the same way Linux does.
2. AWS EC2 Mac instances (m1.metal, m2.metal) running self-hosted runners reproduce this identically — it's not a local dev machine quirk.
3. Three documented approaches exist, each with different security implications worth understanding before you pick one.

---

## Why Apple Silicon Runners Break Docker Access

GitHub announced support for Apple M1 self-hosted runners in August 2022. Since then, ARM64 Mac runners have moved from experimental curiosity to production CI infrastructure — especially for iOS/macOS builds, cross-platform Docker image publishing, and teams standardizing on Apple hardware across dev and CI environments.

The adoption curve accelerated through 2025–2026. AWS EC2 Mac instances based on M1 and M2 hardware became significantly more accessible, and according to Khoa Pham's January 2026 guide on Medium, engineers are now regularly deploying GitHub Actions runners directly onto these EC2 Mac instances for production pipelines. That's a meaningful shift from "interesting experiment" to "this is how we ship."

But macOS handles the Docker socket differently than Linux. On Linux — Ubuntu, Debian, Amazon Linux 2 — installing Docker Engine creates a `docker` group automatically. Adding your CI user to that group is a one-liner. Done.

On macOS with Docker Desktop, which is the standard Docker runtime on Apple Silicon, the socket at `/var/run/docker.sock` is owned by `root` with permissions that may not include a separate `docker` group in the same predictable way. The GitHub Actions runner, launched as a non-root service user, can't touch that socket. Exit code 1. Build dead.

The problem compounds on EC2 Mac instances because those machines run a fixed macOS AMI. You can't always control the exact Docker Desktop version or the initial socket ownership that came with the image. According to documented fix patterns from engineers who've worked through this — including a detailed Korean-language teardown at gerrymandering.tistory.com that traced the exact exit-code-1 path — the fix sequence is consistent across both physical Macs and EC2 Mac instances.

---

## Three Fix Approaches for the Permission Denied Error

### Fix #1: Add the Runner User to the Docker Group

This is the most direct approach. The GitHub Actions runner runs as a specific user — often `ec2-user` on EC2 Mac, or whatever user you configured during runner setup. The fix:

```bash
sudo dseditgroup -o edit -a YOUR_RUNNER_USER -t user docker
```

On macOS, `dseditgroup` is the correct tool — not `usermod`, which is Linux-only. After running this, restart the runner service. The runner user now has socket access.

One catch: this requires the `docker` group to already exist. On macOS with Docker Desktop, it sometimes doesn't. If `dseditgroup` errors, create the group first:

```bash
sudo dseditgroup -o create docker
sudo dseditgroup -o edit -a YOUR_RUNNER_USER -t user docker
```

Verify with `id YOUR_RUNNER_USER` — you should see `docker` in the groups list. Restart the runner. Most teams report this resolves the issue in one shot.

### Fix #2: Adjust Socket Permissions Directly

A faster but less elegant approach: change the socket permissions so the runner user can access it without group membership.

```bash
sudo chmod 666 /var/run/docker.sock
```

This works immediately, no restart needed. But it's not persistent — macOS resets socket permissions on reboot. Teams that use this approach typically add a `launchd` job or a startup script to reapply the permission after restart. That's maintenance overhead worth acknowledging.

On EC2 Mac instances, this is documented as a reliable quick fix, but the reboot persistence issue makes it second-tier for production environments. Use it to confirm that permissions are actually the problem before committing to a more complete solution.

### Fix #3: Run the Runner Service as the Docker-Owning User

The cleanest long-term approach: configure the GitHub Actions runner service to launch as the same user who owns the Docker socket, rather than a separate service account.

On macOS, Docker Desktop typically runs under the logged-in user account. If the runner service runs under that same user, socket permissions become a non-issue. According to the EC2 Mac setup guide on Medium from January 2026, this pattern holds up best across macOS AMI updates and Docker Desktop upgrades — because you're aligning with the permission model rather than fighting it.

The trade-off is real. This user now has broader system access, which some security policies won't allow. For tightly controlled enterprise environments, Fix #1 with explicit group management is more auditable.

### Comparison: Three Fix Approaches Side by Side

| Criteria | Fix #1: Docker Group | Fix #2: chmod 666 | Fix #3: Same User |
|---|---|---|---|
| **Persistence** | Permanent | Resets on reboot | Permanent |
| **Security posture** | Good (scoped) | Weak (open socket) | Depends on user perms |
| **Setup complexity** | Medium | Low | Medium-High |
| **Survives macOS update** | Usually yes | No | Yes |
| **Works on EC2 Mac** | Yes | Yes (with workaround) | Yes |
| **Best for** | Team CI, production | Quick local debugging | Single-user EC2 Mac |

Fix #1 is the right default for production. Fix #2 is useful for diagnosing whether permissions are actually the issue before committing to a full solution. Fix #3 suits setups where the EC2 Mac instance exists purely to run CI and there's no multi-user concern.

Two approaches that fail silently are worth calling out explicitly. Some teams try setting `DOCKER_HOST` environment variables in the workflow YAML without fixing the underlying socket access — that doesn't help here. Others add `sudo` to Docker commands in the workflow, which works but creates a different security problem: your CI pipelines now run arbitrary Docker commands as root. Neither is an acceptable permanent fix.

---

## Scenarios and Recommendations

**Scenario 1: Physical Mac mini or Mac Studio as a self-hosted runner**

The runner was set up manually using `./config.sh` and `./svc.sh install`. The service user is different from the admin account that installed Docker Desktop. Apply Fix #1. Run `dseditgroup`, verify group membership with `id`, then restart with `./svc.sh stop && ./svc.sh start`. This resolves the issue in under five minutes in most cases.

**Scenario 2: AWS EC2 Mac instance (m1.metal or m2.metal)**

The AMI may have Docker Desktop pre-installed, or you've installed it during bootstrap. The `ec2-user` account is the default runner user. Follow Fix #1, but add the group creation step — EC2 Mac AMIs don't guarantee the `docker` group exists. Bake this into your EC2 user data script so it runs automatically on instance launch. Don't rely on manual setup for instances that may be replaced.

**Scenario 3: Multi-architecture Docker image builds (ARM64 + AMD64)**

Teams publishing multi-arch Docker images to registries like Docker Hub or AWS ECR often run both an ARM64 Mac runner and an x86 Linux runner in parallel. The Linux runner rarely hits this issue. The Mac runner almost always does. Apply Fix #1 on the Mac runner, confirm with `docker buildx ls` that the ARM64 node is available, then test a `docker buildx build --platform linux/arm64` push. Socket access is the only thing blocking it.

**What to watch through mid-2026:** GitHub has been expanding its managed hosted runner options for ARM64 — GitHub-hosted runners on Arm are now available for Linux. If managed ARM64 Linux runners cover your use case, the self-hosted Mac runner permission problem becomes less relevant. You can drop the infrastructure maintenance entirely. Track whether GitHub extends managed runners to macOS ARM64 at reasonable price points. That's the signal that would shift the calculus for most teams currently running self-hosted Mac CI.

---

## Conclusion

The frustration with this error is that the message doesn't tell you what's wrong. Exit code 1 from `/usr/bin/docker` is too generic. But the cause is always the same: the runner user can't access `/var/run/docker.sock`.

> **Key Takeaways**
> - **Fix #1 — Docker group via `dseditgroup` — is the correct production solution.** Persistent, scoped, and auditable.
> - **Fix #2 — chmod 666 — is for debugging only.** A reboot wipes it.
> - **EC2 Mac instances need the group creation step baked into user data scripts** for reliable automation across instance replacements.
> - **Adding `sudo` to workflow YAML files introduces real security exposure.** It is not a permanent fix.
> - **Managed ARM64 runners are expanding.** If GitHub extends macOS ARM64 to hosted runners at reasonable cost, the operational case for self-hosted Mac CI weakens considerably.

For now, if you're hitting this error: check the runner user, check the socket owner, add the user to the docker group. That's 90% of cases resolved.

What's your current setup — physical Mac mini fleet or EC2 Mac instances? The bootstrapping approach differs enough between the two that it changes which steps you need. Drop a comment below.

## References

1. [GitHub Actions: Self-hosted runners now support Apple M1 hardware - GitHub Changelog](https://github.blog/changelog/2022-08-09-github-actions-self-hosted-runners-now-support-apple-m1-hardware/)
2. [Github Actions Sef-hosted runners - Error: The process '/usr/bin/docker' failed with exit code 1 해결 ](https://gerrymandering.tistory.com/entry/Github-Actions-Sef-hosted-runners-Error-The-process-usrbindocker-failed-with-exit-code-1-%ED%95%B4%EA%B2%B0)
3. [How to install GitHub action runner on EC2 Mac | by Khoa Pham | Indie Goodies | Jan, 2026 | Medium](https://medium.com/fantageek/how-to-install-github-action-runner-on-ec2-mac-088b7e62b8c4)


---

*Photo by [Shantanu Kumar](https://unsplash.com/@theshantanukr) on [Unsplash](https://unsplash.com/photos/a-cell-phone-sitting-on-top-of-an-open-book-xvdkNBaja90)*
