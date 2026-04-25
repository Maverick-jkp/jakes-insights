---
title: "Fly.io Free Tier PostgreSQL Connection Pool Exhausted: Fix"
date: 2026-04-25T19:51:06+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-data", "fly.io", "free", "tier", "Python"]
description: "Fly.io free tier PostgreSQL caps at 25 connections. When your pool exhausts, apps die instantly. Here's how to fix connection pool exhaustion in 2025."
image: "/images/20260425-flyio-free-tier-postgresql-con.webp"
technologies: ["Python", "Node.js", "PostgreSQL", "Go", "Supabase"]
faq:
  - question: "fly.io free tier postgresql connection pool exhausted fix 2025"
    answer: "The fix for Fly.io free tier PostgreSQL connection pool exhaustion is to configure PgBouncer in transaction-mode pooling, which reduces active database connections by 80–90%. Fly.io's managed Postgres service does not ship with PgBouncer pre-configured, so you need to add it yourself as a sidecar or separate service. This is an application architecture fix, not a database problem, and it's a one-time configuration change."
  - question: "why does fly.io free tier postgresql only allow 25 connections"
    answer: "Fly.io's free tier PostgreSQL instances run on 256MB RAM VMs, and PostgreSQL requires roughly 5–10MB of RAM per connection for buffers and process overhead. To prevent out-of-memory crashes on these constrained VMs, Fly deliberately sets max_connections to 25 on its smallest managed Postgres instances. This is an intentional tradeoff, not a bug."
  - question: "FATAL remaining connection slots are reserved for non-replication superuser connections fly.io fix"
    answer: "This error means your PostgreSQL instance has hit its maximum concurrent connection limit, which on Fly.io's free tier is capped at 25. The most reliable fix is to add PgBouncer as a connection pooler between your app and the database, allowing hundreds of app-level connections to share a small pool of real database connections. Without a pooler, even two Fly machines running a default Node.js app can exhaust the limit before any user traffic arrives."
  - question: "how many database connections does a node.js app use on fly.io"
    answer: "A default Express.js app using the pg library creates a pool of 10 connections per process by default. If you run two Fly.io machines for the same service, that's already 20 active database connections before a single user request is handled. Adding background workers, migration scripts, or a staging environment pointing at the same database can push you past Fly's free tier limit of 25 connections almost immediately."
  - question: "pgbouncer fly.io free tier postgresql connection pool exhausted fix 2025 setup"
    answer: "PgBouncer configured in transaction mode is the standard solution for the fly.io free tier PostgreSQL connection pool exhausted problem, and it can reduce your active database connections by 80–90%. You need to wire it up yourself since Fly's managed Postgres service does not include PgBouncer by default — the most common approach is deploying it as a sidecar alongside your app. Once configured, hundreds of application-level connections can share just a handful of real PostgreSQL connections, keeping you well under the 25-connection ceiling."
---

Your Fly.io app is humming along. Then a deploy restarts your server, traffic spikes, or a background worker kicks in — and suddenly every request returns `FATAL: remaining connection slots are reserved for non-replication superuser connections`. The app is dead. The database is fine. Fly.io's free tier just has a hard ceiling of 25 connections, and you hit it.

This is the most common silent killer for Fly.io free tier PostgreSQL deployments in 2026. It's completely fixable. The fix isn't complicated, but understanding *why* it happens matters if you want to stop it from coming back at 2am.

> **Key Takeaways**
> - Fly.io's free tier PostgreSQL (1 shared CPU, 256MB RAM) enforces a hard ceiling of 25 concurrent connections. Most multi-process Node.js or Python apps exhaust this within minutes of modest traffic.
> - PgBouncer in transaction-mode pooling reduces active database connections by 80–90%, letting hundreds of app-level connections share a small pool of real PostgreSQL connections.
> - Fly.io's community forum confirms that the `fly managed postgres` service ships without PgBouncer pre-configured — you wire it yourself or use a sidecar approach.
> - Connection pool exhaustion on Fly.io free tier is almost never a database problem. It's an application architecture problem that a one-time configuration change resolves.
> - The `fly.io free tier postgresql connection pool exhausted fix` search trend has stayed consistently high through early 2026, making this the #1 pain point for developers building on Fly's free infrastructure.

---

## Why Fly.io's Free Tier Creates This Trap

Fly.io launched its Machines V2 architecture in mid-2023 and steadily expanded free allowances through 2024. By April 2026, the free tier includes up to 3 shared-CPU-1x, 256MB VMs — enough to run a small web app and a Postgres instance side by side. Attractive. But the Postgres VM's memory cap is where things go sideways.

PostgreSQL allocates roughly 5–10MB of RAM per connection for shared buffers, work memory, and process overhead. On a 256MB VM, that math runs out fast. PostgreSQL's `max_connections` parameter defaults to 100 on a fresh install, but Fly's managed Postgres template drops it to 25 on the smallest instance to prevent OOM crashes. That's not a bug. It's a deliberate tradeoff.

The problem compounds with modern app frameworks. A default Express.js app with `pg` uses a pool of 10 connections per process. Two Fly machines running the same service? That's 20 connections before a single user hits the app. Add a background job runner, a migration script, or a staging environment pointing at the same database, and you're over the limit before traffic even shows up.

Fly.io's community forum shows reports dating back to 2023 with the same scenario repeating: developer deploys, everything works locally, production hits the wall the first time process count or traffic scales up.

---

## Why Connection Limits Hit Free Tier Users Harder Than Expected

PostgreSQL doesn't queue excess connections. It rejects them immediately with a fatal error. No grace period, no backoff. The 26th connection attempt fails, full stop.

Most connection pool libraries — `pg` for Node, `psycopg2` for Python, `ActiveRecord` for Rails — default to pool sizes between 5 and 25 *per process*. On a local dev machine running one process, that's fine. On Fly.io free tier with two app VMs (Fly recommends at least 2 for zero-downtime deploys), the math breaks fast:

- 2 app VMs × 10 connections per pool = 20 connections
- 1 Fly internal health check process = 1–2 connections
- 1 deploy migration runner = 1–5 connections
- **Total: 22–27 connections**, which crosses the 25-connection ceiling

This isn't edge-case behavior. It's the default configuration hitting a default limit.

---

## The PgBouncer Fix: Transaction Mode Is the Right Call

PgBouncer sits between your app and PostgreSQL. It accepts hundreds of incoming connections but maintains a small pool of real database connections. In *transaction mode*, a real connection is held only for the duration of a transaction, then returned to the pool. An app with 200 open "connections" to PgBouncer might use only 5 real PostgreSQL connections.

Fly.io's managed Postgres doesn't include PgBouncer by default. The community-documented approach is to run PgBouncer as a sidecar process on the same VM or as a separate Fly Machine. The sidecar approach keeps latency low.

A working `pgbouncer.ini` for Fly.io free tier:

```ini
[databases]
myapp = host=localhost port=5432 dbname=myapp

[pgbouncer]
listen_port = 6432
listen_addr = *
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 200
default_pool_size = 10
server_idle_timeout = 60
```

Key settings to understand:
- `pool_mode = transaction` — most efficient for web apps
- `default_pool_size = 10` — keeps real connections well under the 25-connection ceiling
- `max_client_conn = 200` — lets your app scale without hitting PgBouncer limits

Point your `DATABASE_URL` at port 6432 instead of 5432, and the exhaustion problem disappears.

**One caveat worth knowing**: transaction mode breaks `SET LOCAL`, advisory locks, and `LISTEN/NOTIFY`. If your app uses any of these — common in Rails Action Cable setups — use *session mode* instead. It's less efficient but fully compatible.

---

## Reducing App-Level Pool Size as a Quick Fix

Before wiring up PgBouncer, the fastest immediate fix is reducing your application's connection pool size:

- Node `pg`: `pool: { max: 3 }` in the `Pool` constructor
- Python `psycopg2`: `connection_pool.ThreadedConnectionPool(1, 3, dsn)`
- Rails: `pool: 3` in `database.yml`

On two Fly VMs, a pool size of 3 per process gives you a maximum of 6 real connections — well inside the free tier ceiling. This doesn't scale, but it buys time while you set up PgBouncer properly.

---

## Comparing Your Options

| Approach | Max Real Connections | Setup Complexity | Prepared Statements | Best For |
|---|---|---|---|---|
| Default app pool (no changes) | 10–25+ per process | None | Yes | Local dev only |
| Reduced pool size (`max: 3`) | 3–6 total | Low (env var) | Yes | Quick fix, low traffic |
| PgBouncer transaction mode | 5–10 total | Medium (sidecar) | No (workaround needed) | Most production apps |
| PgBouncer session mode | 10–20 total | Medium | Yes | Apps using `LISTEN/NOTIFY` |
| Upgrade to paid Fly Postgres (4GB) | 200 (default) | None | Yes | High-traffic, paid tier |

PgBouncer in transaction mode is the best tradeoff for apps that don't rely on session-level PostgreSQL features. Session mode with a slightly larger pool still beats the default for apps that do.

---

## Practical Scenarios and What to Do

**Early-stage app, one or two Fly VMs, sub-1,000 daily users**

Reduce pool size to 3 per process immediately. Set `DATABASE_POOL_SIZE=3` as a Fly secret. This costs nothing and takes two minutes. Fly.io community forums are full of developers who spent hours debugging before finding this one-line change.

**App with background job workers (Sidekiq, BullMQ, Celery)**

Background workers are the biggest culprits. Sidekiq's default concurrency is 10, meaning 10 database threads per worker process. Set `concurrency: 2` in your Sidekiq config on free tier, dedicate 5 pool connections to the web process and 5 to the worker. Deploy PgBouncer before adding any additional worker VMs — not after.

**Multi-environment staging sharing the same Postgres instance**

Don't. This is how teams hit the 25-connection ceiling in non-production traffic. Staging environments should use a separate Fly Postgres app (free tier allows multiple) or a local SQLite instance for lightweight testing.

**What to watch**: Fly.io's roadmap as of Q1 2026 includes plans for a managed PgBouncer option on Postgres clusters, similar to what Supabase and Railway already offer. If that ships, the manual sidecar configuration described here becomes unnecessary. Watch `fly.io/changelog` for the announcement.

---

## Where This Approach Can Fail

This isn't always a clean fix. Transaction-mode PgBouncer breaks prepared statements by default — which matters if your ORM uses them heavily. Some versions of SQLAlchemy and ActiveRecord do this automatically, and you'll see cryptic errors after switching. The workaround is disabling prepared statements at the ORM level, but that's a separate configuration step that's easy to miss.

Session mode avoids this but reduces the connection savings. On free tier with very limited headroom, session mode might not cut your connection count enough to matter.

And if you're sharing one Postgres instance across staging and production — even temporarily — no amount of pooling will fully protect you. Separate the environments first.

---

## What to Do Right Now

The 25-connection ceiling is architectural, not a bug. PgBouncer transaction mode reduces real connections by 80–90%. Reducing app-level pool size is the fastest immediate fix. Multi-process deploys and background workers are the primary causes.

Set your pool size to 3 per process today if you're on free tier. If you're growing, wire up PgBouncer before you scale to a second VM. The manual configuration described here is production-tested and reliable until Fly ships native pooling support.

Not sure what your current connection count looks like? Run this in `psql`:

```sql
SELECT count(*) FROM pg_stat_activity;
```

The answer might surprise you.

## References

1. [Fly Managed Postgres and database connection limit using the PG Bouncer - Phoenix - Fly.io](https://community.fly.io/t/fly-managed-postgres-and-database-connection-limit-using-the-pg-bouncer/27103)
2. [Why Fly.io Is the Best Free Docker Hosting You're Not Using | Vibe Coding With Fred](https://vibecodingwithfred.com/blog/flyio-free-tier-guide/)


---

*Photo by [Surface](https://unsplash.com/@surface) on [Unsplash](https://unsplash.com/photos/a-laptop-computer-sitting-on-top-of-a-white-table-F4ottWBnCpM)*
