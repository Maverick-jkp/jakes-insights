---
title: "GitHub Actions Self-Hosted Runner Docker Socket Permission Denied Fix Ubuntu 22.04"
date: 2026-03-28T19:54:31+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "Docker"]
description: "Fix the Docker socket permission denied error on your GitHub Actions self-hosted runner in Ubuntu 22.04 before it kills another CI job."
image: "/images/20260328-github-actions-selfhosted-runn.webp"
technologies: ["Docker", "GitHub Actions", "Linux", "Rust", "Go"]
faq:
  - question: "github actions self-hosted runner docker socket permission denied fix ubuntu 22.04"
    answer: "The most common fix is adding the runner's service account user to the 'docker' group using 'sudo usermod -aG docker <runner-user>', then restarting the runner service so the group membership takes effect. On Ubuntu 22.04, the Docker daemon only allows root and members of the 'docker' group to access the socket at /var/run/docker.sock by default, which is why self-hosted runners fail without this step."
  - question: "how to fix permission denied connecting to docker daemon socket unix var run docker sock"
    answer: "This error means the user running your process does not have permission to access the Docker Unix socket, which is restricted to root and the 'docker' group on most Linux systems. The fix is to add the relevant user to the 'docker' group and then log out and back in, or restart the service, so the new group membership is applied at runtime."
  - question: "github actions self-hosted runner docker socket permission denied fix ubuntu 22.04 after runner v2.332.0 update"
    answer: "Runner versions after v2.332.0 introduced stricter file permission handling for container jobs, which broke Docker access for workflows that previously worked without changes to the runner configuration. If your Docker jobs stopped working after a runner update, you may need to revisit group membership for your runner service account or adjust how the Docker socket is mounted in container jobs."
  - question: "ubuntu 22.04 self-hosted runner user not in docker group after install"
    answer: "When you install the GitHub Actions runner on Ubuntu 22.04, the dedicated runner user (commonly named 'github-runner' or 'actions-runner') is not automatically added to the 'docker' group, even if Docker is already installed. You need to manually run 'sudo usermod -aG docker <runner-user>' and then restart the runner service for the permission change to apply."
  - question: "rootless docker github actions self-hosted runner socket path ubuntu"
    answer: "When running rootless Docker on Ubuntu 22.04, the daemon socket is not located at the default /var/run/docker.sock path but instead at a user-specific path like /run/user/<UID>/docker.sock. Most GitHub Actions self-hosted runner setup guides skip this configuration, so you need to explicitly set the DOCKER_HOST environment variable in your runner environment to point to the correct socket path."
---

The error hits mid-pipeline and kills your entire CI job: `permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock`. If you've set up a GitHub Actions self-hosted runner on Ubuntu 22.04 and tried running Docker-based jobs, you've almost certainly seen this. It's one of the most common failure points teams run into after migrating away from GitHub-hosted runners.

And in 2026, more teams are making that migration. GitHub-hosted runners cost roughly $0.008 per minute for Linux (per GitHub's published pricing), which adds up fast at scale. Self-hosted runners on your own infrastructure eliminate that per-minute cost entirely — but they shift the operational burden to you. That includes debugging socket permission errors that don't surface until your first Docker job fires in production.

The Docker socket permission denied issue on Ubuntu 22.04 isn't a single bug. It's actually several overlapping problems — user group membership, runner service accounts, and container job isolation — that can each independently block Docker access.

This article breaks down:

- Why the permission error happens at a Linux system level
- How the runner v2.332.0+ change made things worse for container jobs
- The three main fix approaches and when to use each
- A structured comparison of solutions so you can pick the right one for your environment

---

**In brief:** The Docker socket permission error on Ubuntu 22.04 self-hosted runners stems from the `docker` group not being applied to the runner's service account at runtime. This is fixable, but the right fix depends on whether you're running rootless Docker, standard Docker, or container jobs with `runs-on: container`.

1. Adding the runner user to the `docker` group is the fastest fix but requires a full logout-login cycle (or service restart) to take effect.
2. Runner versions after v2.332.0 introduced stricter file permission handling for container jobs, breaking workflows that previously worked fine.
3. Rootless Docker on Ubuntu 22.04 requires a separate socket path configuration that most setup guides skip entirely.

---

## Background & Context

Self-hosted runners have existed since GitHub Actions launched in late 2019, but adoption accelerated sharply through 2024–2025 as teams hit the cost ceiling on GitHub-hosted compute. The runner software itself is open-source (github.com/actions/runner), and Ubuntu 22.04 is now the most common Linux configuration teams deploy.

Docker access is where things get complicated. On Ubuntu 22.04, the Docker daemon runs as root and exposes a Unix socket at `/var/run/docker.sock`. By default, only `root` and members of the `docker` group can write to that socket. When you install the GitHub Actions runner, it typically runs under a dedicated user — often called `github-runner` or `actions-runner` — that isn't in the `docker` group by default.

The runner installation docs cover this, but it's easy to miss the group step, especially when provisioning runners via automation scripts or cloud-init. You run the config, start the service, and everything looks fine until a workflow actually tries to call `docker build` or `docker run`.

The situation got more complex after runner version v2.332.0 (released in late 2024). According to the GitHub Actions runner issue tracker (issue #4302), this version changed how the runner handles file permissions inside container jobs — specifically around `GITHUB_ENV` and workspace paths. Workflows using `container:` blocks that worked on v2.331.x started failing with permission denied errors, even when the base Docker access issue was already resolved. Two separate problems, nearly identical error messages.

As of early 2026, this issue appears in GitHub Discussions weekly. It's not fixed at the platform level — it's something each team needs to resolve during runner setup.

---

## Main Analysis

### The Docker Group Problem (Most Common Root Cause)

The socket itself is straightforward Linux permissions:

```bash
ls -la /var/run/docker.sock
# srw-rw---- 1 root docker 0 Mar 28 10:14 /var/run/docker.sock
```

Group is `docker`. Write permission for group members only. The runner user isn't in that group. End of story — until you fix it.

The fix is one command:

```bash
sudo usermod -aG docker $RUNNER_USER
```

Replace `$RUNNER_USER` with your actual runner service account (check with `ps aux | grep Runner.Listener` to confirm which user runs the service). The critical part most guides skip: group changes don't apply to running processes. You must restart the runner service after adding the user.

```bash
sudo systemctl restart actions-runner.service
```

Running `newgrp docker` isn't enough when the runner is managed as a systemd service. The service process needs to restart with the updated group list inherited from the OS.

### The v2.332.0 Container Job Regression

If you're using container jobs — workflows with a `container:` key, not just `docker` CLI calls inside steps — you may hit a different error even after the group fix is applied. This is the issue documented in runner issue #4302.

Starting with v2.332.0, the runner applies tighter ownership checks on workspace directories when running inside containers. The runner process writes environment files to a path like `/__w/_temp/`, and if the container's internal user doesn't match the host runner's UID, you get `permission denied` on `GITHUB_ENV`, `GITHUB_OUTPUT`, or workspace mounts.

Two workarounds exist for this specific regression:

**Option A** — Add a `USER` directive in your Dockerfile that matches the host runner's UID (typically `1001` for auto-provisioned runner users):

```dockerfile
USER 1001
```

**Option B** — If you control the container image but can't change the user, add this to your workflow job:

```yaml
options: --user root
```

This is less secure but unblocks pipelines immediately while you work on the proper fix.

### Rootless Docker on Ubuntu 22.04

Ubuntu 22.04 ships with rootless Docker support, and some teams enable it — especially on shared machines where giving a service account docker group access feels too permissive. Rootless Docker runs the daemon as an unprivileged user, but the socket path changes:

```
/run/user/1000/docker.sock  # example — UID varies
```

The runner doesn't know about this path by default. You need to set `DOCKER_HOST` in the runner's environment before the service starts.

Add this to `/etc/systemd/system/actions-runner.service` (or the override file):

```ini
[Service]
Environment="DOCKER_HOST=unix:///run/user/1001/docker.sock"
```

Then reload systemd and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart actions-runner.service
```

Without this, the runner falls back to `/var/run/docker.sock`, which doesn't exist (or isn't writable) in rootless mode — and you're back to permission denied.

### Comparison: Fix Approaches for the Docker Socket Permission Issue

| Approach | Fixes Standard Docker | Fixes Container Jobs (v2.332.0+) | Fixes Rootless Docker | Security Tradeoff | Setup Time |
|---|---|---|---|---|---|
| `usermod -aG docker` + service restart | ✅ Yes | ❌ No | ❌ No | Docker socket = root equivalent access | ~2 minutes |
| Container user UID matching | ❌ No | ✅ Yes | ❌ No | No additional risk | 5–15 minutes (image rebuild) |
| `--user root` option | Partial | ✅ Yes | ❌ No | Runs container as root | ~1 minute |
| `DOCKER_HOST` env override | ❌ No | ❌ No | ✅ Yes | Keeps rootless isolation | ~5 minutes |
| Combined (group + UID match) | ✅ Yes | ✅ Yes | ❌ No | Moderate | ~20 minutes |

The security tradeoff on the `docker` group approach deserves a direct note. Adding a user to the `docker` group is functionally equivalent to giving them passwordless sudo for most practical purposes. On shared runners handling multiple teams' workloads, that's worth thinking through before applying it automatically.

For isolated single-tenant runners — common in small teams — the group approach is fine and fastest. For multi-tenant environments, the rootless Docker path with proper `DOCKER_HOST` configuration keeps the security boundary intact, even if setup takes longer.

The container job regression introduced in v2.332.0 is independent of socket access entirely. Teams that only run `docker` CLI steps (not `container:` blocks) won't hit it at all. But teams migrating workflows from GitHub-hosted to self-hosted runners often use container jobs extensively — that's where this bites hardest.

---

## Practical Implications

**Scenario 1: New runner setup, standard Docker jobs**

After the standard runner installation from the GitHub repository settings page, run:

```bash
sudo usermod -aG docker runner   # substitute actual username
sudo systemctl restart actions-runner
```

Verify it worked before committing to production by running a test workflow with a single `docker info` step. If that passes, socket access is clean.

**Scenario 2: Existing runner that broke after upgrading to v2.332.0+**

Check your runner version first:

```bash
./config.sh --version
```

If you're past v2.332.0 and using `container:` in your workflows, the UID mismatch is likely the problem. Pull the container image locally, check what user it runs as (`docker inspect <image> --format '{{.Config.User}}'`), and compare against the runner service account's UID (`id runner`). If they don't match, use the `--user` option as a short-term patch while you rebuild the image with the correct UID.

**Scenario 3: Security-conscious team, shared runner infrastructure**

Don't use the docker group approach here. Set up rootless Docker per Ubuntu's official docs — which includes enabling lingering for the user (`loginctl enable-linger $RUNNER_USER`) — then configure `DOCKER_HOST` in the systemd service file. The setup takes 30–45 minutes the first time but gives you proper isolation. GitHub's own documentation on self-hosted runner security (docs.github.com/en/actions/security-guides) explicitly recommends avoiding broad socket access on shared runners.

**What to watch next:**

- GitHub is actively tracking issue #4302 — a proper fix at the runner level may ship in a v2.335+ release, which would eliminate the need for UID matching workarounds entirely.
- Ubuntu 24.04 LTS is now in wide use as of 2026, and its default AppArmor profiles handle Docker socket access differently. Teams upgrading OS versions on runner hosts may hit a variant of this same error with a different root cause.

---

## Conclusion

The Docker socket permission denied error frustrates so many teams because the error message is identical across three completely different root causes. Get the diagnosis wrong, apply the wrong fix, and you're still stuck.

> **Key Takeaways**
> - **Standard Docker access**: `usermod -aG docker` plus a service restart. Don't skip the restart — group changes don't apply to running processes.
> - **Container jobs post-v2.332.0**: UID mismatch between the container image and runner user. Fix it in the Dockerfile or use `--user root` as a temporary patch.
> - **Rootless Docker**: Set `DOCKER_HOST` in the systemd unit file. The default socket path won't work.
> - **Shared runners**: Skip the docker group approach entirely. Rootless Docker keeps the security boundary intact.

Over the next 6–12 months, expect the v2.332.0 container job regression to get an upstream fix — the GitHub runner team acknowledged the issue in the tracker. Rootless Docker on Ubuntu will likely become the documented default for self-hosted setups as security guidance tightens.

The fix that matters is the one that matches your actual error. These three problems look identical in the logs but need different solutions. Confusing them is exactly how teams spend hours pointed in the wrong direction.

So before reaching for the first Stack Overflow answer that looks close: figure out which of the three scenarios you're actually in. The rest follows from there.

## References

1. [v2.332.0: Container jobs fail with permission denied on GITHUB_ENV and workspace after upgrade from ](https://github.com/actions/runner/issues/4302)
2. [How to Set Up a Self-Hosted GitHub Actions Runner on Ubuntu](https://oneuptime.com/blog/post/2026-01-07-ubuntu-github-actions-runner/view)


---

*Photo by [Shantanu Kumar](https://unsplash.com/@theshantanukr) on [Unsplash](https://unsplash.com/photos/a-cell-phone-sitting-on-top-of-an-open-book-xvdkNBaja90)*
