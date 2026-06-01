---
title: "Docker Compose depends_on Not Working: Postgres Startup Fix"
date: 2026-04-16T20:25:11+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "docker", "compose", "healthcheck", "Kubernetes"]
description: "Docker Compose depends_on doesn't wait for Postgres to be ready—just started. Fix the startup race condition with service_healthy and a proper healthcheck."
image: "/images/20260416-docker-compose-healthcheck-dep.webp"
technologies: ["Docker", "Kubernetes", "GitHub Actions", "Rust", "Go"]
faq:
  - question: "docker compose healthcheck depends_on not working postgres container startup race condition fix"
    answer: "The fix requires replacing the default `depends_on` condition with `condition: service_healthy` and adding a `pg_isready` healthcheck to your Postgres service definition. This forces Docker Compose to wait until Postgres is actually accepting connections, not just until the container process has started. Without this combination, your app container will attempt to connect before the Postgres socket is open, causing non-deterministic connection failures."
  - question: "why does my app crash on startup even though postgres container is running docker compose"
    answer: "This is caused by a race condition where Docker Compose's default `depends_on` behavior only waits for the Postgres container process to launch, not for Postgres to finish initializing and accept connections. The startup sequence — loading shared memory, replaying WAL, opening the TCP socket — can take 1 to 15 seconds after the container starts. Your app connects too early and receives a 'connection refused' error."
  - question: "docker compose depends_on condition service_healthy postgres example"
    answer: "To use `condition: service_healthy`, you need to define a healthcheck on your Postgres service using `pg_isready`, then reference it in your app service's `depends_on` block with `condition: service_healthy`. This feature has been available since Compose spec v3.4 and ensures your app container only starts after Postgres is verified to be accepting connections."
  - question: "how to fix docker compose postgres startup race condition in CI/CD pipeline"
    answer: "The docker compose healthcheck depends_on not working postgres container startup race condition fix involves configuring a `pg_isready`-based healthcheck on the Postgres service and setting `condition: service_healthy` in your dependent service's `depends_on` block. This eliminates non-deterministic connection failures in CI/CD pipelines and can reduce failed startup attempts from dozens of retries to near-zero. Without this fix, pipelines may pass or fail inconsistently depending on hardware speed and database size."
  - question: "difference between service_started and service_healthy in docker compose depends_on"
    answer: "`service_started` only waits for the container's entrypoint process to launch, meaning your dependent service starts regardless of whether the dependency is actually ready to serve requests. `service_healthy` holds the dependent container until the dependency passes its configured healthcheck, confirming it is fully operational. For databases like Postgres, `service_healthy` is the correct choice to prevent startup race conditions."
---

Your app crashes on startup. Postgres logs show it's running. The connection still fails. Every time.

This is the `depends_on` race condition — one of the most deceptively frustrating problems in containerized development. The fix exists. It's not obvious. And most tutorials get it halfway right.

> **Key Takeaways**
> - Docker Compose's `depends_on` with `condition: service_started` only waits for the container process to launch, not for Postgres to actually accept connections — making a healthcheck the only reliable fix.
> - Solving the startup race condition requires combining `condition: service_healthy` with a properly configured `pg_isready` healthcheck, not just container ordering.
> - According to Docker's official documentation, `service_healthy` has been available since Compose spec v3.4 (2018), yet misconfiguration remains one of the top reported issues in Docker community forums as of Q1 2026.
> - Teams using Kubernetes encounter the same race condition through readiness probe misconfiguration — the underlying problem is identical.
> - A correct healthcheck config reduces failed startup attempts from potentially dozens of retries to near-zero in CI/CD pipelines.

---

## What's Actually Happening at Startup

Postgres doesn't go from "container started" to "accepting connections" instantly. There's a real sequence: the container spawns, the init system runs, Postgres loads shared memory, replays WAL if needed, and *then* opens the socket for TCP connections. That entire process can take anywhere from 1 to 15 seconds depending on hardware and database size.

Docker Compose's default `depends_on` behavior checks exactly one thing: whether the *container process started*. Not whether it's ready. Not whether port 5432 is listening. Just that the PID exists.

So your app container starts, tries to connect immediately, and hits a socket that isn't open yet. Connection refused. Crash. The container restarts. Maybe it works on retry. Maybe it doesn't. This is non-deterministic — which makes it especially painful to debug.

The good news: Docker Compose has had a proper fix since the Compose spec added `condition: service_healthy` support. The bad news: it requires explicit healthcheck configuration that most tutorials skip entirely.

---

## Why `depends_on` Alone Doesn't Cut It

The root cause is a semantic gap between "container running" and "service ready." Docker's architecture deliberately separates these two concepts.

When you write:

```yaml
depends_on:
  - postgres
```

Compose translates that to `condition: service_started` internally. The app container gets a green light the moment the Postgres container's entrypoint process launches. Postgres itself might still be mid-initialization.

Docker's official Compose specification is explicit about this. `service_started` means: *"Wait until a container with a matching name or label is running."* Running. Not healthy. Not ready.

`service_healthy` is different. It holds the dependent container in a waiting state until the target container's healthcheck returns exit code 0. No healthcheck defined? The condition can never be satisfied, and Compose will either throw an error or fall back to `service_started` depending on version.

This is where most engineers hit the wall. They add `condition: service_healthy` without defining a healthcheck on the Postgres service. Compose either errors out or the condition is never met — so the app still starts prematurely.

---

## The Complete Fix: Healthcheck + Condition Together

Getting this right requires two changes working in tandem.

### The Postgres Service Healthcheck

Add this to your Postgres service definition:

```yaml
postgres:
  image: postgres:16
  environment:
    POSTGRES_USER: myuser
    POSTGRES_PASSWORD: mypassword
    POSTGRES_DB: mydb
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U myuser -d mydb"]
    interval: 5s
    timeout: 5s
    retries: 5
    start_period: 10s
```

`pg_isready` is the right tool here. It's a Postgres-native utility that checks whether the server is ready to accept connections on the specified user and database — not just whether the port is open. According to Last9's Docker health monitoring analysis, using `pg_isready` instead of a raw TCP check catches cases where Postgres is listening but hasn't finished setting up the target database yet.

The `start_period: 10s` parameter matters more than people realize. It tells Docker not to count failed healthchecks during the first 10 seconds of container life. Without it, Compose may mark the container as unhealthy before Postgres even finishes initializing — triggering unnecessary restarts before the process has a fair shot.

### The App Service Dependency

```yaml
app:
  build: .
  depends_on:
    postgres:
      condition: service_healthy
```

That's it. Compose will now poll the Postgres healthcheck every 5 seconds, wait for a clean success, and only then start the app container.

### Dependency Strategies Compared

| Strategy | What It Waits For | Reliable? | Config Complexity |
|---|---|---|---|
| `depends_on: [postgres]` | Container process start | ❌ No | Minimal |
| `depends_on` + `service_started` | Container process start | ❌ No | Minimal |
| `depends_on` + `service_healthy` (no healthcheck) | Undefined / error | ❌ No | Low |
| `depends_on` + `service_healthy` + `pg_isready` | Postgres accepting connections | ✅ Yes | Moderate |
| External wait scripts (`wait-for-it.sh`) | TCP port open | ⚠️ Partial | High |

External wait scripts like `wait-for-it.sh` are a common workaround, but they check TCP connectivity — not application readiness. Postgres can accept a TCP handshake while still refusing database connections. The native healthcheck approach is cleaner and more accurate.

---

## Real-World Scenarios and What to Do

**CI/CD pipelines failing intermittently**

This is the most common production symptom. A GitHub Actions or GitLab CI pipeline runs integration tests. 70% of the time it works. 30% of the time the app can't connect to Postgres on startup and the tests fail. The fix is the healthcheck config above, applied consistently across all Compose files used in CI. According to OneUptime's January 2026 Docker Compose health check guide, adding `start_period` to account for slower CI runner hardware is especially important — Postgres startup in shared CI environments can run 2–3x slower than local dev.

**Local development restarts causing connection errors**

When you run `docker compose restart app`, the app might come back up before Postgres finishes its own restart cycle. The healthcheck fixes this too. The `condition: service_healthy` dependency applies on restarts, not just initial startup.

**Multi-service apps with migrations**

If your app runs database migrations on startup — common with tools like Flyway or Alembic — a race condition here is catastrophic. Migrations fail, the schema is left in a partial state, and subsequent restarts compound the damage. The healthcheck approach gives migrations a clean, ready database every time. This isn't always the answer if your migration tool has its own retry logic, but for most setups it removes an entire class of failure.

---

## What Comes Next

Docker Desktop 4.x, the dominant dev environment as of April 2026, supports the full healthcheck spec with no additional configuration. The tooling is there. Adoption is still inconsistent.

Over the next 6–12 months, expect Docker Compose to add better warnings when `condition: service_healthy` is declared without a corresponding healthcheck. There's an open feature request in the Docker Compose GitHub repository (as of early 2026) to surface this as a validation error rather than silent misbehavior.

The race condition isn't going away. But the fix is now yours.

Check your existing Compose files. If `depends_on` doesn't have `condition: service_healthy` paired with a working `pg_isready` healthcheck, it's probably just lucky timing holding things together — and that luck will eventually run out in CI.

## References

1. [Docker Status Unhealthy: What It Means and How to Fix It | Last9](https://last9.io/blog/docker-status-unhealthy-how-to-fix-it/)
2. [How to Create Docker Compose Health Checks](https://oneuptime.com/blog/post/2026-01-30-docker-compose-health-checks/view)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-golden-docker-logo-on-a-black-background-HSACbYjZsqQ)*
