---
title: "Docker Compose depends_on Not Working: Fix Service Startup Order"
date: 2026-05-11T21:56:49+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "docker", "compose", "healthcheck", "PostgreSQL"]
description: "Docker's depends_on only waits for container start, not readiness. Fix your healthcheck depends_on startup order before your API crashes again."
image: "/images/20260511-docker-compose-healthcheck-dep.webp"
technologies: ["Docker", "PostgreSQL", "Redis", "Rust", "Go"]
faq:
  - question: "docker compose healthcheck depends_on not working service startup order fix"
    answer: "The most common reason docker compose healthcheck depends_on not working is that depends_on defaults to 'condition: service_started', which only waits for the container process to launch, not for the service inside to be ready. The fix is to add a healthcheck block to your dependency service and set 'condition: service_healthy' in your depends_on configuration. You should also include a 'start_period' field to give slow-starting services like PostgreSQL enough time before health checks begin firing."
  - question: "why does depends_on not wait for database to be ready docker compose"
    answer: "By default, depends_on only confirms that a container's process has started, not that the application inside is accepting connections. For a PostgreSQL container, Docker may report it as 'started' up to 800ms before it actually accepts TCP connections on port 5432. To fix this, you need to define a healthcheck on the database service and use 'condition: service_healthy' in your depends_on block."
  - question: "docker compose depends_on condition service_healthy vs service_started difference"
    answer: "There are three depends_on conditions in Docker Compose: service_started (default) confirms the container process is running, service_healthy confirms the container has passed its defined healthcheck, and service_completed_successfully is used for init or migration containers. Using service_started when you actually need service_healthy is the root cause of most startup ordering failures in multi-container applications."
  - question: "should I use wait-for-it.sh or docker compose healthcheck for container startup ordering"
    answer: "The native Docker Compose healthcheck combined with depends_on condition: service_healthy is the recommended modern approach and requires no external dependencies or custom scripts. Scripts like wait-for-it.sh are considered a legacy workaround from when Docker Compose lacked built-in condition support. The native solution is cleaner, more portable, and directly supported in the Compose specification."
  - question: "docker compose postgres container ready before api starts healthcheck setup"
    answer: "To ensure your API waits for PostgreSQL to be fully ready, add a healthcheck block to your postgres service using pg_isready as the test command, and set depends_on in your API service with 'condition: service_healthy'. You must also include a 'start_period' value in the healthcheck to prevent health checks from failing prematurely before PostgreSQL finishes initializing, especially on slower storage environments like CI."
aliases:
  - "/tech/2026-05-11-docker-compose-healthcheck-dependson-not-working-s/"

---

Most engineers hit this wall within their first week of containerizing a real app. The database container is "up," the API crashes anyway, and `depends_on` is sitting there doing absolutely nothing useful.

The frustration is legitimate. According to Docker's own documentation, `depends_on` in its default form only waits for a container to *start* — not to be *ready*. That single distinction kills more staging deployments than any code bug. Docker's [2025 Developer Survey](https://www.docker.com/blog/docker-state-of-app-development-report-2025/) shows 78% of teams now run multi-container local dev environments, which means this misconfiguration is endemic across the industry.

The fix exists. It's not obvious. And the Docker Compose documentation buries the critical detail under three levels of nesting.

---

> **Key Takeaways**
> - `depends_on` defaults to `condition: service_started`, which only confirms a container process launched — not that the service inside is accepting connections.
> - Adding a `healthcheck` block combined with `condition: service_healthy` in `depends_on` is the correct fix for startup ordering failures.
> - The `start_period` field is non-optional for slow-starting services like PostgreSQL or Elasticsearch — without it, health checks fire before the service is ready and fail prematurely.
> - Three distinct conditions exist (`service_started`, `service_healthy`, `service_completed_successfully`) — choosing the wrong one is the root cause of most `healthcheck` + `depends_on` failures.
> - Scripts like `wait-for-it.sh` are a legacy workaround. The native `healthcheck` + `depends_on` approach is cleaner and requires no external dependencies.

---

## Why `depends_on` Alone Doesn't Work

The confusion starts with what "started" actually means in container terms. Docker reports a container as started the moment its entrypoint process kicks off — that's it. For a PostgreSQL container, that moment comes roughly 200–800ms before it's actually accepting TCP connections on port 5432, depending on hardware and volume mounts.

So your API container starts, tries to connect at boot, gets `ECONNREFUSED`, and crashes. Docker restarts it (if you've got a restart policy), it races again, maybe succeeds on attempt three. This is non-deterministic. It works locally on a fast SSD and fails in CI on slower provisioned storage.

The Docker Compose documentation (Compose Specification, updated March 2026) defines three conditions:

- **`service_started`** — default; container process is running
- **`service_healthy`** — container passed its defined healthcheck
- **`service_completed_successfully`** — used for init or migration containers

Almost every `healthcheck` + `depends_on` failure traces back to using `service_started` — or no condition at all — when the intent was `service_healthy`.

---

## Background: How We Got Here

Docker Compose v1 had no `condition` key. `depends_on` was purely ordering — it guaranteed container *creation* sequence, nothing about readiness. Engineers compensated with shell scripts: `wait-for-it.sh` (GitHub: ~14k stars as of May 2026) and `dockerize` became standard Dockerfile inclusions just to patch this gap.

Compose v2, bundled with Docker Desktop by default starting in 2022, introduced `condition` syntax and moved healthcheck integration into the core spec. Docker Engine 25.0 (released January 2024) and 27.x (current as of 2026) have stable support for all three conditions.

The problem is inertia. Thousands of tutorials, Stack Overflow answers, and copy-pasted `docker-compose.yml` files still show bare `depends_on` lists with no condition. Engineers grab those snippets, hit startup ordering failures, and spend hours debugging what is ultimately a two-line fix.

The `healthcheck` block itself adds confusion. Defined at the *service* level rather than under `depends_on`, it's easy to misplace. And without a `start_period`, a slow-starting database like MySQL or Elasticsearch fails the healthcheck before it's ever had a chance to initialize.

---

## The Correct Configuration Pattern

The working pattern requires two changes. First, add a `healthcheck` block to the dependency service:

```yaml
services:
  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
```

Second, reference that health status in the dependent service's `depends_on`:

```yaml
  api:
    build: .
    depends_on:
      db:
        condition: service_healthy
```

That `start_period: 10s` field is what most engineers miss. It tells Docker to ignore healthcheck failures during the first 10 seconds of container life — giving PostgreSQL time to initialize data directories and start accepting connections before failures actually count.

Without `start_period`, Docker runs `pg_isready` immediately. PostgreSQL fails it. After `retries: 5` failures, the container is marked `unhealthy`. The `api` service never starts. And the error message says nothing useful about why.

### The Three Conditions Compared

| Condition | Waits For | Use Case | Startup Failure Risk |
|---|---|---|---|
| `service_started` (default) | Container process running | Stateless services, sidecars | High — no readiness guarantee |
| `service_healthy` | Healthcheck passes | Databases, message queues, caches | Low — requires correct healthcheck |
| `service_completed_successfully` | Container exits with code 0 | DB migrations, seed scripts | Low — deterministic exit |

For a typical web app stack — API + PostgreSQL + Redis — use `service_healthy` for both the database and cache. If a migration container runs before the API, it uses `service_completed_successfully` against the DB, and the API uses `service_completed_successfully` against the migration container. Each link in the chain is explicit, not a timing assumption.

### Common Healthcheck Commands by Service

The `test` command needs to match what the service actually exposes:

- **PostgreSQL**: `pg_isready -U $POSTGRES_USER`
- **MySQL/MariaDB**: `mysqladmin ping -h localhost -u root -p$MYSQL_ROOT_PASSWORD`
- **Redis**: `redis-cli ping`
- **HTTP APIs**: `curl -f http://localhost:8080/health || exit 1`
- **Elasticsearch**: `curl -f http://localhost:9200/_cluster/health?wait_for_status=yellow`

The `-f` flag on `curl` is critical for HTTP checks. It forces curl to return a non-zero exit code on HTTP errors (4xx, 5xx). Without it, curl exits 0 even on a 503 — and the healthcheck reports healthy when the service is down.

### Legacy Workarounds vs. Native Solution

**`wait-for-it.sh` (legacy approach):**
- **Pros**: Works with any Compose version; no Compose-level config required
- **Cons**: Requires modifying the Dockerfile or entrypoint; adds an external dependency; checks TCP port only, not actual service readiness
- **Best for**: Teams stuck on Compose v1 syntax or images they can't modify

**Native `healthcheck` + `condition: service_healthy`:**
- **Pros**: No external scripts; health state visible in `docker ps`; works with Docker Swarm and orchestrators that read health status
- **Cons**: Requires write access to `docker-compose.yml` and an appropriate healthcheck command for the image
- **Best for**: Any project using Compose v2 (Docker Desktop 4.x+, Docker Engine 23+)

The native approach wins for every greenfield project in 2026. The `docker ps` output shows `(healthy)` or `(unhealthy)` inline — that visibility alone cuts debugging time significantly.

---

## Where This Still Breaks

This approach isn't foolproof. A few scenarios where it can fail:

**Healthcheck command returns false positives.** If `pg_isready` reports ready before PostgreSQL has finished replaying WAL logs or loading extensions, the dependent service starts against an incompletely initialized database. The fix is a more precise healthcheck — one that queries a known table rather than just checking TCP connectivity.

**`start_period` set too short.** On cold container pulls in CI with network-attached storage, PostgreSQL can take 4–6 seconds to initialize. A `start_period: 3s` that works locally will fail in pipeline. Set it conservatively — 10–15 seconds costs nothing in practice.

**Images without healthcheck utilities.** Minimal base images (Alpine, distroless) sometimes lack `curl`, `pg_isready`, or `redis-cli`. Either install them in the Dockerfile or use a TCP-based check with `nc -z localhost 5432`. This isn't ideal, but it's better than no check at all.

---

## Practical Scenarios

**API crashes on startup in CI but works locally.** The local machine has fast NVMe storage. PostgreSQL initializes in under 500ms. The race condition is invisible. CI uses network-attached storage and cold container pulls — PostgreSQL takes 3–4 seconds. Adding `condition: service_healthy` with a proper `healthcheck` block makes behavior deterministic across both environments.

**Elasticsearch takes 45 seconds to go yellow.** Set `start_period: 45s`, `interval: 10s`, `retries: 6`. The healthcheck won't mark anything unhealthy for 45 seconds, then checks every 10 seconds up to 6 times. That's a 105-second total window — enough for any realistic cold start.

**What's coming:** Docker's 2026 roadmap includes improved `healthcheck` output in `docker compose ps` (currently verbose only with `--format json`). Better terminal visibility for health state transitions would reduce debugging friction significantly.

---

## Conclusion

The `depends_on` + `healthcheck` problem is a documentation failure more than a technical one. The tooling has had the right solution since Compose v2 shipped. The `condition: service_healthy` pattern is clean, native, and requires no external scripts.

The practical audit is simple: open every `docker-compose.yml` in your projects. Find every `depends_on` block. If it doesn't have an explicit `condition`, it's a latent startup race condition — one that will surface at the worst possible moment, in CI or production, not on your local machine.

`depends_on` without a condition is nearly always wrong for stateful services. `start_period` in the `healthcheck` block is non-optional for slow-starting databases. And `wait-for-it.sh` is a 2018 solution to a problem that's already been solved natively.

Fix the config. Ship deterministic deployments.

## References

1. [Docker Compose Health Checks: An Easy-to-follow Guide | Last9](https://last9.io/blog/docker-compose-health-checks/)
2. [How to Use Docker Compose depends_on with Health Checks](https://oneuptime.com/blog/post/2026-01-16-docker-compose-depends-on-healthcheck/view)
3. [Docker Compose Service Dependencies: Solving Database Startup Sequence with Healthchecks · BetterLin](https://eastondev.com/blog/en/posts/dev/20251217-docker-compose-healthcheck/)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-golden-docker-logo-on-a-black-background-HSACbYjZsqQ)*
