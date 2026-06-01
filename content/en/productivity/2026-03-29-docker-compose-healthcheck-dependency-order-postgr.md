---
title: "Docker Compose Healthcheck Dependency Order: Postgres Not Ready Fix"
date: 2026-03-29T19:54:11+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "healthcheck", "Django"]
description: "Fix Docker Compose healthcheck dependency order so Postgres is truly ready before your app starts — not just 'up' but accepting connections."
image: "/images/20260329-docker-compose-healthcheck-dep.webp"
technologies: ["Django", "Docker", "Kubernetes", "Redis", "Rust"]
faq:
  - question: "docker compose healthcheck dependency order postgres not ready fix production"
    answer: "The fix requires using `condition: service_healthy` in your `depends_on` block combined with a properly configured `healthcheck` using `pg_isready`. By default, `depends_on` only waits for the container to start, not for Postgres to actually be ready to accept connections. Tuning the `interval`, `retries`, and `start_period` parameters to match your environment's real initialization time prevents the app from connecting too early."
  - question: "why does my app crash even though postgres container is running docker compose"
    answer: "Docker Compose's default `depends_on` behavior only waits for the Postgres container process to launch, not for the database to finish initializing. Postgres can still be setting up its data directory or running recovery while your app attempts its first connection. Adding a healthcheck with `pg_isready` and setting `condition: service_healthy` in `depends_on` ensures the database is truly ready before your app starts."
  - question: "docker compose depends_on condition service_healthy postgres example"
    answer: "To use `condition: service_healthy`, add a `healthcheck` block to your Postgres service that runs `pg_isready -U youruser`, then reference it in your app service with `depends_on: postgres: condition: service_healthy`. This is the production-grade approach recommended in the official Docker Compose documentation. Without the `condition` field, `depends_on` defaults to `service_started`, which does not guarantee the database is accepting connections."
  - question: "wait-for-it.sh vs docker compose healthcheck which is better for postgres"
    answer: "Docker Compose's built-in healthcheck with `condition: service_healthy` is generally preferred over wrapper scripts like `wait-for-it.sh` for production environments. Wrapper scripts are a valid fallback but add maintenance overhead and require modifying your container's entrypoint. Proper healthcheck configuration is more declarative, integrates natively with Compose's dependency ordering, and is easier to maintain long-term."
  - question: "how to fix postgres not ready connection refused docker compose production"
    answer: "The root cause is that `depends_on` without a health condition starts your app container before Postgres finishes initializing. The docker compose healthcheck dependency order postgres not ready fix production solution is to define a `healthcheck` on your Postgres service using `pg_isready` and set `condition: service_healthy` in your app's `depends_on` block. You should also adjust `start_period` and `retries` values to account for slower initialization times in real production environments."
---

Your container starts. Postgres is "up." Your app crashes anyway.

This failure pattern accounts for a significant share of production incidents in containerized environments — and the fix is less obvious than you'd think.

Docker Compose's `depends_on` keyword has existed for years, but most engineers still misconfigure it the same way. The container starts. The health check passes. The app connects too early. Chaos.

What follows is why the default behavior fails, what the correct configuration looks like, and how to structure your production Compose files so Postgres is actually ready before your application touches it.

> **Key Takeaways**
> - Docker Compose's `depends_on` by default only waits for a container to *start*, not for the service inside it to be *ready* — this distinction is the root cause of most "Postgres not ready" failures in production.
> - The `condition: service_healthy` option in `depends_on`, combined with a properly tuned `healthcheck` block, is the correct production-grade fix.
> - Healthcheck parameters — specifically `interval`, `retries`, and `start_period` — must be calibrated for your environment; the defaults are too aggressive for most real-world Postgres initialization times.
> - Wrapper scripts like `wait-for-it.sh` are a valid fallback, but they introduce additional maintenance overhead and don't replace proper healthcheck configuration.

---

## The Problem With `depends_on` Out of the Box

Docker Compose has supported `depends_on` since the early Compose v2 spec. The catch? Without additional configuration, it only guarantees *container start order*, not *service readiness*. Postgres the container can be "running" while Postgres the database is still initializing its data directory, running recovery, or accepting its first TCP connections.

According to the official [Docker Compose documentation](https://docs.docker.com/compose/compose-file/05-services/#depends_on), the default `condition` for `depends_on` is `service_started` — which fires the moment the container process launches. For stateless services this is often fine. For Postgres, MySQL, Redis, or any service with a non-trivial startup sequence, it's a ticking clock.

The failure mode is consistent: your application container starts, attempts a database connection at boot, and hits a "connection refused" or "role does not exist" error. If your app doesn't retry on startup — and many don't — it crashes immediately. If it does retry, it may exhaust retries before Postgres is ready.

The Docker team has acknowledged this in their docs since at least 2020, but it keeps biting teams in 2026 because the naive `depends_on: postgres` syntax *looks* correct. It isn't.

---

## How Healthchecks Actually Work in Compose

A `healthcheck` block tells Docker how to test whether a service is genuinely ready. For Postgres, the standard check uses `pg_isready`, a small utility that ships with every Postgres installation.

A production-ready Postgres service block looks like this:

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: appdb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d appdb"]
      interval: 5s
      timeout: 5s
      retries: 10
      start_period: 10s
```

Each parameter matters:

- **`interval`**: How often Docker runs the check. Five seconds is a reasonable production default.
- **`timeout`**: How long Docker waits for the check command to return. Keep this below `interval`.
- **`retries`**: How many consecutive failures before the container is marked `unhealthy`.
- **`start_period`**: A grace period before failures count toward `retries`. Critical for Postgres initialization — on a cold start with a large data directory, Postgres can take 8–15 seconds before accepting connections.

Without `start_period`, a slow-starting Postgres instance can exhaust `retries` before it's even finished initializing, leaving the container permanently marked `unhealthy` and blocking dependent services forever. That's a particularly frustrating failure to debug at midnight.

---

## Wiring the Dependency Correctly

Once the healthcheck is defined, the dependent service must explicitly declare the readiness condition:

```yaml
services:
  app:
    image: myapp:latest
    depends_on:
      postgres:
        condition: service_healthy
```

`condition: service_healthy` tells Compose to block the `app` container from starting until `postgres` reports a healthy status. This is the fix that actually works in production.

Two important caveats apply:

**First**, this requires Compose file version 2.1 or later. The bare `depends_on: postgres` shorthand doesn't support condition syntax. If you're running an older Compose spec, the condition key will silently be ignored — which is a genuinely painful debugging experience.

**Second**, `service_healthy` only works if the target service *has* a `healthcheck` defined. No healthcheck means Docker has no health status to evaluate, and Compose will throw an error or fall back to `service_started` depending on version.

---

## Comparing Your Fix Options

Not every team can or wants to modify their Compose files. Three realistic approaches exist:

| Approach | Setup Complexity | Reliability | Production-Grade | Maintenance |
|---|---|---|---|---|
| `depends_on` + `service_healthy` | Low | High | ✅ Yes | Minimal |
| `wait-for-it.sh` wrapper script | Medium | Medium | ⚠️ Conditional | Script updates needed |
| Application-level retry logic | High | High | ✅ Yes | Code changes required |
| `dockerize` utility | Medium | Medium | ⚠️ Conditional | External dependency |

**`depends_on` + `service_healthy`** is the cleanest solution for pure Compose environments. No changes to application code, no external tools. The only requirement is a well-tuned healthcheck block — which you should have anyway for production monitoring.

**`wait-for-it.sh`** — originally published by Gliderlabs — works by overriding your container's entrypoint with a shell script that polls TCP connectivity before launching the real process. It's reliable, but it conflates "port open" with "service ready." Postgres accepts TCP connections slightly before it finishes initialization, so this approach can still produce race conditions under load.

**Application-level retry logic** is the most resilient pattern long-term. It handles not just startup races but mid-lifecycle failures like Postgres restarts. Django's `CONN_MAX_AGE`, SQLAlchemy's `pool_pre_ping`, and similar settings handle this well. But it doesn't eliminate the need for startup ordering — it just makes the app more tolerant of imperfect conditions.

**`dockerize`** is a Go utility that supports waiting on both TCP and HTTP endpoints. More flexible than `wait-for-it.sh`, but it adds an external binary to your image, increasing image size and introducing a supply chain dependency.

The right call for most teams: use `depends_on` + `service_healthy` as your primary guard, and add application-level connection retries as a secondary defense. Defense in depth applies here the same way it does everywhere else.

---

## Practical Scenarios and What to Do

**Scenario 1 — Fresh dev environment, containers won't start.** Your `app` container exits immediately with a database connection error. The healthcheck isn't configured. Add the `healthcheck` block to your Postgres service and update `depends_on` to use `condition: service_healthy`. Set `start_period` to at least `10s` if your machine is slow or the data volume is large.

**Scenario 2 — CI pipeline flakiness.** Postgres passes health checks in local dev but fails intermittently in CI. CI machines are often slower and share CPU. Increase `start_period` to `30s` and `retries` to `15` in your CI-specific override file. Docker Compose supports multiple `-f` flags, so maintaining a `docker-compose.ci.yml` override is clean practice.

**Scenario 3 — Production with multiple dependent services.** Three services all depend on the same Postgres instance. Each needs `condition: service_healthy` in its own `depends_on` block. Docker handles parallel readiness checks — all three will wait independently on the same health status. No need to chain them sequentially.

---

## What to Watch in the Next 6–12 Months

A few trends worth tracking:

- **Docker Compose spec evolution**: The Compose maintainers have been iterating on the spec. Watch the [Compose Specification GitHub](https://github.com/compose-spec/compose-spec) for changes to how `condition` and `start_period` behavior is documented.
- **Kubernetes parity pressure**: As more teams graduate from Compose to Kubernetes, the analogous `readinessProbe` concept becomes familiar. Expect better tooling and documentation parity between the two ecosystems.
- **Postgres 17 initialization speed**: Postgres 17 shipped in Q4 2024 with improvements to startup time. Benchmarks from [pganalyze](https://pganalyze.com) suggest cold-start times dropped measurably for smaller databases — which may make overly conservative `start_period` values less necessary over time.

---

Default `depends_on` doesn't solve the Postgres not-ready problem. It never did.

Add a `healthcheck` with a calibrated `start_period`, switch to `condition: service_healthy`, and layer in application-level connection retries. That combination handles 95% of these failures cleanly — no wrapper scripts, no fragile polling loops.

If your `docker-compose.yml` doesn't have a `healthcheck` on every stateful service, add one today. Future you will be grateful at 2am.

*Was this useful? What Compose or container orchestration topics should we cover next? Drop it in the comments.*

## References

1. [How to Use Docker Compose depends_on with Health Checks](https://oneuptime.com/blog/post/2026-01-16-docker-compose-depends-on-healthcheck/view)
2. [Docker Compose Health Checks Made Easy: A Practical Guide | by Cyril Baah | Medium](https://medium.com/@cbaah123/docker-compose-health-checks-made-easy-a-practical-guide-3a340571b88e)


---

*Photo by [Egor Komarov](https://unsplash.com/@egorkomarov) on [Unsplash](https://unsplash.com/photos/a-close-up-of-a-control-panel-with-buttons-n2jspRppehw)*
