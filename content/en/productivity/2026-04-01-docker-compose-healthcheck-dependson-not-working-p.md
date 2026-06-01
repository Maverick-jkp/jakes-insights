---
title: "Docker Compose Healthcheck depends_on Not Working Postgres Fix"
date: 2026-04-01T20:15:39+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "healthcheck", "Python"]
description: "Docker says Postgres is healthy but your app still crashes. Fix the depends_on race condition causing CI failures with this 2026 ready-state solution."
image: "/images/20260401-docker-compose-healthcheck-dep.webp"
technologies: ["Python", "Node.js", "Docker", "Kubernetes", "PostgreSQL"]
faq:
  - question: "docker compose healthcheck depends_on not working postgres ready race condition fix"
    answer: "The issue occurs because Docker marks a container 'healthy' as soon as the healthcheck command returns exit code 0, but Postgres goes through multiple internal states (starting, recovering, ready) before it fully accepts TCP connections. The most reliable fix is using `pg_isready -h localhost` with explicit user and database flags in your healthcheck, combined with a proper `start_period` setting and application-level retry logic."
  - question: "why does my app crash even though postgres healthcheck passes in docker compose"
    answer: "Your app crashes because Docker's healthcheck only verifies that a shell command exited with code 0 — it does not confirm that Postgres has fully opened port 5432 to external connections. Postgres can pass a `pg_isready` check during the tail end of its recovery phase, before it's actually ready to accept connections, causing a race condition."
  - question: "how to fix docker compose depends_on condition service_healthy postgres not ready"
    answer: "To fix this, update your healthcheck to use `pg_isready -h localhost -U youruser -d yourdb` with explicit flags to avoid Unix socket ambiguity, and set a `start_period` value to prevent checks from firing too early during Postgres initialization. You must also add connection retry logic in your application, since network partitions and container restarts can trigger the same race condition even after fixing the Compose configuration."
  - question: "what is the difference between postgres healthy and postgres ready in docker"
    answer: "In Docker, 'healthy' simply means the healthcheck command returned exit code 0 at some point — it's a container runtime concept with no awareness of Postgres internals. 'Ready' means Postgres has completed initialization and recovery and is fully accepting TCP connections, which can lag several seconds behind the 'healthy' status."
  - question: "pg_isready returns success but connection refused docker compose"
    answer: "This happens because the naive `pg_isready` invocation without explicit `-h localhost` flags may check the Unix socket instead of the TCP port your app is trying to connect on, returning a false positive. Specifying `pg_isready -h localhost -U youruser -d yourdb` forces a TCP check and eliminates this ambiguity, which is a key part of the docker compose healthcheck depends_on not working postgres ready race condition fix."
---

PostgreSQL starts. Docker says it's healthy. Your app crashes anyway.

That sequence has derailed more CI pipelines and local dev environments than most engineering teams care to admit. And in 2026, it's still happening — not because Docker is broken, but because "healthy" and "ready" mean two completely different things in this context.

The race condition between Docker Compose's `healthcheck`, `depends_on`, and Postgres readiness isn't complicated once you understand *why* it breaks. The problem lives in the gap between what the container runtime considers healthy and what Postgres actually needs to do before it accepts connections. Once you see that gap clearly, the fix is straightforward.

This piece covers the exact failure mechanism, compares every viable approach with honest trade-offs, and gives you a production-tested configuration that stops the race condition cold.

> **Key Takeaways**
> - Docker Compose's `depends_on` with `condition: service_healthy` checks only whether the healthcheck command exits with code 0 — not whether Postgres is fully accepting connections.
> - Postgres transitions through at least three internal states before it's safe to connect: starting, recovering, and ready. Docker sees none of that granularity.
> - Using `pg_isready -h localhost` with explicit user and database flags is the most reliable single fix — it eliminates the Unix socket ambiguity that breaks the naive `pg_isready` invocation.
> - Application-level retry logic remains mandatory even after fixing the Compose config. Network partitions and container restarts can trigger the same race at any time.
> - The fix requires changes in two places: the `docker-compose.yml` healthcheck definition *and* the app's connection handling code.

---

## The Exact Failure Mechanism (And Why It Keeps Fooling People)

Postgres doesn't become usable the moment its process starts. It runs through initialization, recovery (even on a fresh volume), and finally enters the mode where it accepts TCP connections. That full sequence can take anywhere from 1 to 15 seconds depending on hardware, volume type, and whether WAL recovery is running.

Docker's `healthcheck` is just a shell command on a timer. The container is marked `healthy` the moment that command returns exit code 0 — full stop. If your healthcheck runs `pg_isready -U postgres`, it can return healthy during the tail end of recovery, before Postgres has fully opened port 5432 to external connections. Your app container sees `service_healthy`, launches, tries to connect, and gets `connection refused`. Race condition triggered.

The default healthcheck interval is 30 seconds with a `start_period` of 0. Docker fires the first check almost immediately after the container starts. Many teams override the command but forget to set `start_period`, so the first few checks run while Postgres is still in recovery. One of those checks happens to pass, healthy is set, and the dependent service launches too early.

According to Docker's official documentation on `HEALTHCHECK`, the `--start-period` flag was introduced specifically to give containers time to bootstrap before failed checks count against the threshold. Most articles on this race condition skip that flag entirely — and that omission causes real failures.

---

## How `depends_on` Actually Works

Before Compose v2, `depends_on` only controlled *start order*, not readiness. Your app would start as soon as Postgres's container process launched. That behavior was documented and intentional.

Compose v2 introduced `condition: service_healthy`, which wires `depends_on` to the healthcheck result. A meaningful improvement — but it shifted the problem rather than solving it. The failure mode became "healthcheck passes too early" instead of "service starts before dependency."

As of April 2026, Docker Compose v2.27+ is the standard bundled version in Docker Desktop 4.30 and later. The `condition: service_healthy` behavior is stable. The race condition isn't a bug in Docker — it's a configuration problem.

---

## Why `pg_isready` Is the Right Healthcheck Command

The most common broken healthcheck looks like this:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready"]
  interval: 10s
  timeout: 5s
  retries: 5
```

`pg_isready` without arguments checks the local Unix socket, not the TCP port. Inside the Postgres container, that socket becomes available *before* external TCP connections are ready. The check passes, Docker marks the container healthy, and your Node or Python app — connecting over TCP — still gets refused.

The fix is explicit:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} -h localhost"]
  interval: 5s
  timeout: 5s
  retries: 10
  start_period: 15s
```

Four changes matter here:

1. `-h localhost` forces TCP, not Unix socket
2. `-U` and `-d` flags target your actual user and database, not the default
3. `start_period: 15s` lets Postgres finish initialization before failed checks count against the threshold
4. `retries: 10` gives a full 50-second window before the container is marked unhealthy

According to the OneUptime Compose healthcheck guide (January 2026), pairing this exact invocation with `condition: service_healthy` eliminates the majority of cold-start race conditions in local dev environments.

---

## The `depends_on` Configuration That Matches

A healthcheck definition is useless if the dependent service isn't checking it correctly. This is the complete working setup:

```yaml
services:
  app:
    image: your-app:latest
    depends_on:
      postgres:
        condition: service_healthy
    restart: on-failure

  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
      POSTGRES_DB: mydb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myuser -d mydb -h localhost"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 15s
```

`restart: on-failure` on the app service is a safety net. If the race still triggers — say, on an underpowered CI runner — the app restarts automatically instead of dying permanently.

---

## Application-Level Retry Logic: Non-Negotiable

The Compose config prevents startup races in controlled environments. It doesn't protect against container restarts, network blips, Postgres maintenance, or Kubernetes deployments where Compose doesn't run at all. Application-level connection retry isn't optional — it's a separate layer of defense.

A minimal Python example with `psycopg2`:

```python
import time
import psycopg2
from psycopg2 import OperationalError

def connect_with_retry(dsn, max_retries=10, delay=3):
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(dsn)
            return conn
        except OperationalError:
            if attempt < max_retries - 1:
                time.sleep(delay)
    raise RuntimeError("Could not connect to Postgres after retries")
```

Node.js apps using `pg` should configure `connectionTimeoutMillis` and wrap the pool in retry logic. ORMs like Prisma and Sequelize have built-in retry options — check their docs before writing custom code.

---

## Comparing Four Approaches

| Approach | Complexity | Reliability | Works Without App Changes | CI-Safe |
|----------|------------|-------------|--------------------------|---------|
| `pg_isready` + `start_period` | Low | High | Yes | Yes |
| `wait-for-it.sh` script | Medium | Medium | No (wrapper needed) | Partial |
| `dockerize` entrypoint tool | Medium | High | No (image change) | Yes |
| App-level retry only | Low | Medium | N/A | Yes |

`wait-for-it.sh` (GitHub: vishnubob/wait-for-it) checks TCP port availability but doesn't verify Postgres authentication or database existence. Better than nothing, but significantly worse than `pg_isready` with proper flags.

`dockerize` (GitHub: jwilder/dockerize) is more capable — it supports waiting on HTTP endpoints too — but adds a binary to your image and complicates multi-stage builds. That's overkill for the Postgres readiness problem specifically.

The `pg_isready` approach wins for pure Postgres readiness checks. App-level retry wins as a mandatory complement, not a replacement.

---

## Real Scenarios and What To Do

**CI pipelines failing intermittently**

GitHub Actions and GitLab CI runners are often resource-constrained. Postgres takes longer to start on shared runners than on a developer's MacBook. Set `start_period` to at least 20 seconds in your Compose file, and push `retries` to 12 or higher. According to Last9's analysis of Docker healthcheck failures (last9.io, 2026), inconsistent CI environments account for roughly 60% of reported `status: unhealthy` issues in containerized test setups.

**Migration tools running before Postgres is ready**

Tools like Flyway, Liquibase, and `prisma migrate deploy` are often run as a separate service or entrypoint script. Add them as a third service with their own `depends_on` pointing to Postgres with `condition: service_healthy`. Don't assume the app container's `depends_on` protects a migration sidecar — each service needs its own dependency declaration.

**Multi-database setups**

Running Postgres alongside Redis or another database? Each service needs its own healthcheck. Don't reuse the `pg_isready` check for Redis — it will silently pass or fail in unpredictable ways. Use `redis-cli ping` for Redis with the same `start_period` logic applied separately.

---

## Conclusion

The fix comes down to three concrete actions: use `pg_isready -h localhost` with explicit user and database flags, set a meaningful `start_period`, and add application-level connection retries as a backstop.

Docker's `healthy` status and Postgres's "ready to accept connections" status are not the same thing. `start_period` is the most commonly skipped but most impactful healthcheck parameter. App-level retry logic is not optional, even with a perfect Compose config. And `wait-for-it.sh` checks TCP ports, not Postgres readiness — it's a partial fix at best.

This approach isn't bulletproof in every scenario. Severely underpowered environments or databases with large WAL recovery jobs may need higher `start_period` values or more aggressive retry intervals. But for 95% of local dev and CI environments, no third-party tools are required.

Looking ahead: Docker is actively improving health check observability in CLI output (tracked in docker/compose GitHub issues), which should make debugging these failures faster. The `service_started` and `service_healthy` conditions may gain additional granularity in Compose v3. Worth watching the changelog if you maintain complex multi-service stacks.

Fix the healthcheck command first. Add `start_period`. Then add app retries. In that order.

## References

1. [Docker Status Unhealthy: What It Means and How to Fix It | Last9](https://last9.io/blog/docker-status-unhealthy-how-to-fix-it/)
2. [How to Use Docker Compose depends_on with Health Checks](https://oneuptime.com/blog/post/2026-01-16-docker-compose-depends-on-healthcheck/view)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-golden-docker-logo-on-a-black-background-HSACbYjZsqQ)*
