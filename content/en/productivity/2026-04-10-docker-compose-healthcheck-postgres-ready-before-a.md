---
title: "Docker Compose Healthcheck: Postgres Ready Before App Start"
date: 2026-04-10T20:16:16+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "healthcheck", "Python"]
description: "Stop Docker race conditions in production: depends_on without service_healthy won't wait for Postgres to accept connections. Fix it with healthchecks."
image: "/images/20260410-docker-compose-healthcheck-pos.webp"
technologies: ["Python", "Docker", "GitHub Actions", "Rust", "Go"]
faq:
  - question: "docker compose depends_on not waiting for postgres to be ready"
    answer: "By default, Docker Compose's `depends_on` only waits for a container to start, not for Postgres to actually accept connections. This creates a race condition where your app tries to connect before Postgres is ready, resulting in `ECONNREFUSED` errors or crashes. The fix is to use `condition: service_healthy` alongside a `pg_isready` healthcheck block on the Postgres service."
  - question: "docker compose healthcheck postgres ready before app start production pattern"
    answer: "The production-standard pattern uses a `healthcheck` block with `pg_isready` on your Postgres service, combined with `depends_on: condition: service_healthy` on your app service. This ensures Docker waits until Postgres is genuinely accepting connections before starting your application container. According to Docker's documentation, both halves — the healthcheck block and the service_healthy condition — must be present or the mechanism silently breaks."
  - question: "how to use pg_isready in docker compose healthcheck"
    answer: "`pg_isready` is a Postgres utility that checks whether the database server is ready to accept connections, making it ideal for Docker healthchecks. You configure it in the `healthcheck` block of your Postgres service within `docker-compose.yml`, specifying the host and user flags. Once the healthcheck passes, any dependent service using `condition: service_healthy` will be allowed to start."
  - question: "docker compose healthcheck postgres ready before app start production pattern works locally fails in CI"
    answer: "Startup race conditions between Postgres and app containers are a leading cause of 'works locally, fails in CI' bugs in multi-container stacks. CI environments and cloud platforms trigger cold container starts constantly, making the timing window where Postgres isn't yet ready much more likely to cause failures. Implementing the `pg_isready` healthcheck pattern with `condition: service_healthy` eliminates this class of bug in both local and CI environments."
  - question: "docker compose restart policy vs healthcheck for postgres startup"
    answer: "Restart policies like `restart: on-failure` let your app retry after crashing, but they don't prevent the crash or guarantee Postgres is ready before the next attempt. Healthchecks with `condition: service_healthy` proactively hold the app container from starting until Postgres passes readiness checks, avoiding crashes entirely. For production deployments, healthchecks are the more reliable and predictable approach, though restart policies can serve as an additional safety net."
---

Production deployments still fail in 2026 because developers trust `depends_on` without healthchecks. That's the whole problem — and it's more widespread than most engineering teams want to admit.

> **Key Takeaways**
> - Docker's `depends_on` without `condition: service_healthy` only waits for a container to *start*, not for Postgres to accept connections — creating race conditions that surface unpredictably in production.
> - The `pg_isready` healthcheck pattern eliminates the most common class of container startup failures across multi-service stacks.
> - According to Docker documentation (2025), `service_healthy` conditions require an explicit `healthcheck` block on the dependency service — omitting either half silently breaks the mechanism.
> - Teams running multi-container stacks on platforms like Railway, Render, or self-hosted VMs report that startup race conditions account for a disproportionate share of "works locally, fails in CI" bugs.
> - A properly configured healthcheck adds 3–10 seconds to cold start time — a worthwhile trade against app crashes and manual restarts.

---

## 1. The Problem Nobody Reads the Docs About

Postgres takes time to be ready. Not just *running* — actually ready to accept TCP connections, initialize the data directory, and process queries. That window is typically 2–8 seconds on a cold container start. On slower VPS hardware or network-attached storage, it can stretch past 20 seconds.

Most Docker Compose tutorials show `depends_on` and stop there. That's the trap.

`depends_on` in its default form tells Docker: "start this container *after* that one." It says nothing about whether Postgres is actually accepting connections. So your Node, Python, or Go app boots up, tries to connect on port 5432, gets `ECONNREFUSED`, and either crashes or enters a broken state that's annoying to diagnose and embarrassing to explain.

This matters more now because container-native deployments are the default across most mid-size engineering teams. According to the 2025 Stack Overflow Developer Survey, over 78% of professional developers use containers in their workflow — up from 69% in 2023. More teams running containers means more teams hitting this exact startup race condition. And more of those teams are deploying to ephemeral environments — CI pipelines, preview deployments, autoscaling groups — where cold starts happen constantly.

The `pg_isready` healthcheck pattern exists specifically to close this gap. It's not new. But it's still misconfigured far more often than it should be.

**What this analysis covers:**
- How the race condition actually manifests and why `depends_on` alone fails
- The correct healthcheck configuration using `pg_isready`
- A comparison of common approaches — restart policies, healthchecks, wait scripts
- Practical recommendations for production and CI environments

---

**The short version:** `depends_on` without a health condition is a silent failure waiting to happen. The fix is a two-part pattern — a `healthcheck` block on the Postgres service and `condition: service_healthy` on the app — and it takes under 10 lines of YAML.

Three things to understand before diving in:

1. Postgres containers report as "started" while still initializing their data directory, making them unavailable for connections for several seconds.
2. The `pg_isready` utility (bundled with every official Postgres image) is the most reliable way to check actual connection readiness from inside a healthcheck.
3. Production configurations should tune `interval`, `timeout`, `retries`, and `start_period` based on the environment's cold start characteristics.

---

## 2. Background: How Docker Compose Dependencies Actually Work

Docker Compose introduced `depends_on` back in version 2 of the Compose spec, and the intent was clear: control startup order. But the implementation had a gap. The original `depends_on` only checked container state — `started`, `healthy`, or `completed` — and the default was just `started`.

That default persisted for years. Countless tutorials copied it. Stack Overflow answers cemented it. The result: a generation of `docker-compose.yml` files that *look* correct but fail under load or on slow hardware.

Compose v2 (which became the canonical format around 2022–2023) introduced `condition` as a proper dependency qualifier. Three values matter:

- `condition: service_started` — the old default. Container is running. No readiness check.
- `condition: service_healthy` — container has passed its `healthcheck`. This is what you want.
- `condition: service_completed_successfully` — for one-shot init containers.

The `service_healthy` condition only works if the target service has a `healthcheck` block defined. Write `condition: service_healthy` without a corresponding `healthcheck` on Postgres, and Docker treats the dependency as immediately satisfied. Silent failure, again. This behavior is documented in the [Docker Compose specification](https://docs.docker.com/compose/compose-file/05-services/#depends_on), but easy to miss when copying snippets from a tutorial at midnight.

The `pg_isready` utility — shipped with every official Postgres Docker image — is purpose-built for this check. It probes the Postgres socket and returns exit code 0 only when the server is ready to accept connections. That's exactly what a healthcheck `test` command needs.

---

## 3. Main Analysis

### The Race Condition in Detail

When you run `docker compose up` without healthchecks, the sequence looks like this:

1. Postgres container starts.
2. Docker marks it `started`.
3. App container starts (because `depends_on` says "after Postgres starts").
4. App tries to connect — Postgres is still running `initdb` or loading WAL.
5. Connection fails. App crashes or logs errors.

The timing window is narrow but consistent. On a typical 2-core VPS with a fresh Postgres 16 image, data directory initialization takes roughly 3–6 seconds. Your app's connection attempt often lands squarely inside that window.

The fix is making Docker *wait* for a real readiness signal before starting the app. That's the core of this pattern.

### The Correct YAML Configuration

This is the configuration that works:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: appdb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d appdb"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  app:
    image: myapp:latest
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgres://appuser:secret@db:5432/appdb
```

A few things to understand here. The `start_period` tells Docker not to count failed healthchecks against the retry limit during the first 10 seconds — giving Postgres time to cold-start without triggering a premature `unhealthy` state. With `interval: 5s` and `retries: 5`, the total grace period before marking `unhealthy` is about 35 seconds (`start_period` + `retries × interval`).

The `-U appuser -d appdb` flags on `pg_isready` are critical in production. Without them, `pg_isready` only checks if Postgres is *listening* — not if your specific database and user are accessible. Migrations running as `appuser` can still fail if the user isn't provisioned yet. This is the detail most tutorials skip.

### What Breaks When You Get This Wrong

Three failure modes show up repeatedly in production:

**Missing `healthcheck` block.** You write `condition: service_healthy` on the app but forget to add `healthcheck` to the Postgres service. Docker skips the wait entirely. App crashes on startup. This is the most common misconfiguration — easy to introduce when someone copies half a pattern from different sources.

**Using `restart: unless-stopped` as a workaround.** Some teams skip healthchecks and add `restart: unless-stopped` to the app service. The app crashes, Docker restarts it, Postgres eventually becomes ready, and the third or fourth restart succeeds. It *works*, but it's fragile. You're adding 10–30 seconds of crash-loop delay, polluting logs, and masking the root cause. In CI, it can trigger false failures before the eventual successful retry — which creates the kind of flaky pipeline behavior that erodes trust in the entire test suite.

**Overly short `timeout`.** A `timeout: 1s` on a slow network or NFS-backed volume means `pg_isready` itself times out before Postgres responds, even when Postgres is perfectly healthy. Set `timeout` to at least 5s in production environments.

### Comparison: Three Approaches to the Startup Race Condition

| Approach | Reliability | Complexity | CI Suitability | Cold Start Overhead |
|---|---|---|---|---|
| `depends_on` (default, no healthcheck) | Low — race condition always possible | Minimal | Poor | None |
| `restart: unless-stopped` on app | Medium — works eventually | Low | Poor — noisy logs, slow | 10–30s crash-loop |
| `pg_isready` healthcheck + `service_healthy` | High — deterministic | Low-Medium | Excellent | 3–10s (tunable) |
| Custom wait script (`wait-for-it.sh`) | High | Medium-High | Good | 3–15s |
| Application-level retry logic | High (with circuit breaker) | High | Good | None extra |

The healthcheck pattern wins on reliability-to-complexity ratio. Custom wait scripts like `wait-for-it.sh` or `dockerize` were popular before Compose's `service_healthy` condition matured — they work, but they require injecting an extra binary into your app image or wrapping your entrypoint. That's extra maintenance surface with no real advantage over the native approach.

Application-level retry logic with exponential backoff is worth adding *alongside* the healthcheck, not instead of it. Defense in depth. Your app shouldn't assume the database is permanently reachable just because startup succeeded.

---

## 4. Practical Implications

**For teams running local dev environments:** The healthcheck pattern works identically in development and production. Add it to your base `docker-compose.yml`, not just a `docker-compose.prod.yml`. If it's only in production, your dev environment becomes a different beast — and you'll debug production-only startup issues without being able to reproduce them locally. Consistency matters more than it seems.

**For CI/CD pipelines:** GitHub Actions, GitLab CI, and CircleCI all run Docker Compose natively. The `service_healthy` condition means your test runner waits for Postgres to be genuinely ready before running migrations or tests. Without it, you're adding `sleep 10` hacks to your pipeline YAML — fragile, embarrassing to maintain, and invisible to anyone reviewing the repository for the first time.

**Autoscaling and container restarts:** Consider an app container on a platform like Render or Fly.io that gets OOM-killed and restarts. If the Postgres container is already running and healthy, the healthcheck passes almost immediately on the app's restart — typically within one `interval` cycle, so about 5 seconds. Clean, predictable recovery. The crash-loop approach can't guarantee that timing, and in high-traffic scenarios, those extra seconds matter.

**Docker Compose on a VPS:** Teams running `docker compose up -d` on a DigitalOcean Droplet or Hetzner server after a reboot need deterministic startup order. Without healthchecks: reboot → services start in parallel → app crashes → manual intervention at 2am. With the healthcheck pattern: the app simply waits. No intervention needed.

**This approach isn't always sufficient.** If your Postgres container is healthy but your database migrations haven't run yet, `pg_isready` will pass while your app still fails. For migration-dependent apps, combine the healthcheck pattern with an init container or a migration job that runs with `condition: service_completed_successfully`. The healthcheck solves the connection readiness problem — not the schema readiness problem. Know the difference.

**What to watch:** Docker's [Compose v2.x roadmap](https://github.com/docker/compose) continues to evolve healthcheck semantics. Better observability in `docker compose ps` output and improvements to `start_period` behavior are both flagged in 2025 Compose specification discussions. Worth tracking if you're standardizing this pattern across a larger team.

---

## 5. Conclusion & Future Outlook

The pattern isn't complicated. Two additions to your YAML: a `healthcheck` block on Postgres and `condition: service_healthy` on your app. Ten lines. Deterministic startup. No more crash loops at 2am.

> **Key takeaways:**
> - `depends_on` alone doesn't wait for Postgres readiness — it only waits for container start, which is a meaningfully different thing.
> - `pg_isready -U <user> -d <dbname>` is the correct healthcheck command — the flags matter in production.
> - `start_period` prevents premature `unhealthy` states during cold starts; don't omit it.
> - Restart-policy workarounds eventually succeed but are fragile, slow, and obscure the underlying problem.
> - Healthchecks solve connection readiness — pair them with migration handling for full coverage.

As more teams move to declarative infrastructure, expect healthcheck patterns to become part of standard linting toolchains for Compose files. Tools like [Hadolint](https://github.com/hadolint/hadolint) already flag Dockerfile issues — similar static analysis for `docker-compose.yml` is a logical next step. By late 2026, CI platforms may warn on missing healthchecks by default, the same way they now flag exposed secrets or unpinned base images.

The one action worth taking today: audit your `docker-compose.yml` files. If you see `depends_on` without `condition: service_healthy`, that's a crash waiting for slower hardware to trigger it. Fix it before production does it for you.

**What does your current Compose setup look like — healthchecks in place, or still relying on restart policies? Drop your setup in the comments.**

## References

1. [How to Create Docker Compose Health Checks](https://oneuptime.com/blog/post/2026-01-30-docker-compose-health-checks/view)
2. [Docker Compose Service Dependencies: Solving Database Startup Sequence with Healthchecks · BetterLin](https://eastondev.com/blog/en/posts/dev/20251217-docker-compose-healthcheck/)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-golden-docker-logo-on-a-black-background-HSACbYjZsqQ)*
