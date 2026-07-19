---
title: "How to Fix Postgres Connection Pool Exhaustion on Fly.io"
date: 2026-04-23T20:25:56+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "fly.io", "free", "tier", "Node.js"]
description: "Fix Fly.io free tier Postgres connection pool exhausted errors before they kill your next demo or launch with these targeted 2025 solutions."
image: "/images/20260423-flyio-free-tier-postgres-conne.webp"
technologies: ["Node.js", "PostgreSQL", "Go", "Supabase"]
faq:
  - question: "fly.io free tier postgres connection pool exhausted fix 2025"
    answer: "The standard fix for Fly.io free tier Postgres connection pool exhaustion is deploying PgBouncer in transaction-pooling mode between your app and the database. This reduces the number of actual server-side connections from potentially dozens down to 5–10, staying well within the default 25-connection limit on the shared-cpu-1x instance. Be aware that transaction mode breaks some PostgreSQL features like prepared statements, which may require code-level workarounds."
  - question: "why does fly.io postgres say too many connections on free plan"
    answer: "Fly.io's free-tier Postgres runs on a 256 MB RAM VM that defaults to a hard cap of 25 total connections, calculated at startup based on available memory. Most web frameworks like Rails, Node.js, and Phoenix open connection pools of 5–10 per worker by default, making it easy to exceed 25 connections before any real users hit the app. Rolling deploys make this worse by temporarily doubling the active connection count."
  - question: "how to set up PgBouncer on fly.io to fix connection pool exhausted"
    answer: "PgBouncer should be deployed in transaction-pooling mode on Fly.io, sitting between your application instances and the Managed Postgres backend. In this mode, a connection is only held from the pool while an active transaction is executing, which dramatically reduces the number of simultaneous server-side connections needed. This is the recommended approach for the fly.io free tier postgres connection pool exhausted fix in 2025, though you must disable prepared statements in your ORM or driver configuration to avoid compatibility errors."
  - question: "what is the default max connections for fly.io managed postgres"
    answer: "Fly.io Managed Postgres on a shared-cpu-1x instance with 256 MB of RAM defaults to max_connections = 25, set automatically by PostgreSQL at startup based on available memory. This limit is not arbitrary — PostgreSQL reserves roughly 400–600 bytes of shared memory per connection slot, so increasing the value on a 256 MB VM risks out-of-memory crashes. Upgrading to a larger VM size will raise this default."
  - question: "does fly.io free tier postgres support more than 25 connections"
    answer: "The free-tier Fly.io Postgres instance is capped at 25 connections due to the memory constraints of the 256 MB shared VM, and simply raising max_connections risks crashing the instance with an OOM kill. Rather than increasing the limit, the recommended solution is adding a connection pooler like PgBouncer in front of Postgres, which allows many app threads to share a small number of real database connections. Upgrading to a paid Fly.io plan with more RAM is the other option, as larger VMs automatically get higher max_connections defaults."
aliases:
  - "/tech/2026-04-23-flyio-free-tier-postgres-connection-pool-exhausted/"

---

Fly.io's free tier attracts thousands of indie developers and early-stage teams every month. But there's a specific failure mode that keeps hitting newcomers hard: connection pool exhaustion on Postgres, often at the worst possible time — during a demo, a launch, or a production spike.

The error is blunt. `too many connections` or `connection pool exhausted` shows up in logs, your app stalls, and the Fly Managed Postgres instance simply stops accepting new clients. No graceful degradation. Just failure. This isn't a niche edge case — it's one of the most frequently reported issues in Fly.io's community forums as of 2026, with the [PgBouncer thread](https://community.fly.io/t/fly-managed-postgres-and-database-connection-limit-using-the-pg-bouncer/27103) alone accumulating hundreds of replies across multiple Phoenix and Node.js stacks.

The fix exists. It's well-documented in pieces, but scattered. This article pulls it together.

---

**In brief:** Fly.io's free-tier Postgres instances cap out at 25 total connections by default, and most application frameworks open far more than that. The standard solution is PgBouncer in transaction-pooling mode, but deploying it correctly requires understanding a few non-obvious trade-offs.

1. The free-tier Postgres VM (shared-cpu-1x, 256 MB RAM) sets `max_connections = 25` by default based on available memory.
2. PgBouncer in transaction mode drops effective connection demand from N app threads to 5–10 server-side connections, resolving the exhaustion issue for most workloads.
3. Certain PostgreSQL features — prepared statements, advisory locks, `SET` commands — break under transaction-mode pooling and require code-level workarounds.

---

## Why the Free Tier Runs Out of Connections So Fast

Fly.io's Managed Postgres runs on a standard PostgreSQL backend. Each `max_connections` value is calculated at startup based on available RAM. According to Fly.io's own documentation, the shared-cpu-1x instance with 256 MB RAM defaults to `max_connections = 25`. That's not a soft cap — PostgreSQL reserves roughly 400–600 bytes of shared memory per connection slot, so bumping this value on a 256 MB VM risks OOM kills.

The problem is that modern web frameworks don't connect conservatively. A default Rails app with Puma spins up a connection pool of 5 per worker. Run 4 Puma workers across 2 app instances and you've already consumed 40 connections — 60% over the limit before a single real user hits the app. Node.js with `pg` or Prisma behaves similarly. Phoenix/Ecto defaults to a pool of 10 per node. Every `fly deploy` that spins up a rolling restart briefly doubles your connection count.

The root cause isn't Fly.io being stingy. It's a genuine constraint of small-memory Postgres combined with connection-per-thread application models. The industry-standard fix for this gap is a connection pooler — specifically PgBouncer.

---

## What PgBouncer Actually Does (and Why Transaction Mode Matters)

PgBouncer sits between your app and Postgres. Instead of 40 app threads each holding an open Postgres connection, they all connect to PgBouncer, which maintains a much smaller server-side pool.

Three pooling modes exist, and choosing the wrong one is where most developers go wrong:

- **Session mode**: One server connection per client session. Effectively useless for connection reduction.
- **Transaction mode**: Server connection assigned only during a transaction, released immediately after `COMMIT`/`ROLLBACK`. This is what you want.
- **Statement mode**: One connection per SQL statement. Breaks multi-statement transactions entirely. Don't use this.

Transaction mode can serve 40+ application clients through 5–8 server-side Postgres connections. That's the math that solves free-tier exhaustion.

Fly.io ships PgBouncer bundled inside its Managed Postgres image, accessible on port `5432` while raw Postgres listens on `5433`. As noted in the Fly community forum thread, many users don't realize the default connection string already routes through PgBouncer — but often in session mode, which doesn't help.

---

## Fixing the Exhaustion: Step-by-Step Configuration

### Step 1: Confirm Your Pooling Mode

Connect to your Postgres app machine directly:

```bash
fly ssh console -a <your-postgres-app-name>
```

Check `/etc/pgbouncer/pgbouncer.ini` for `pool_mode`. If it reads `session`, that's your problem.

### Step 2: Switch to Transaction Mode

Edit the config:

```ini
[pgbouncer]
pool_mode = transaction
max_client_conn = 100
default_pool_size = 10
server_pool_size = 5
```

Restart PgBouncer inside the VM:

```bash
supervisorctl restart pgbouncer
```

### Step 3: Adjust Application Connection Strings

Point your app at port `5432` (PgBouncer), not `5433` (raw Postgres). Your `DATABASE_URL` secret in Fly should already reflect this if you used `fly postgres attach`.

### Step 4: Handle Transaction-Mode Incompatibilities

This is where teams get surprised. Transaction-mode pooling breaks:

- **Named prepared statements** — Prisma and some ORMs use these by default. Disable with `?pgbouncer=true` in Prisma's connection URL, or set `prepare: false` in node-postgres.
- **`SET` commands outside transactions** — Some ORMs issue `SET search_path` on connect. These don't persist across pooled connections.
- **Advisory locks** — Session-scoped locks don't work because the session isn't consistent.

---

## Comparing Your Connection Pooling Options on Fly.io

| Approach | Connection Reduction | Setup Complexity | Free Tier Compatible | Breaks Prepared Statements |
|---|---|---|---|---|
| PgBouncer (session mode) | Low — none effectively | Low | No | No |
| PgBouncer (transaction mode) | High — 5–8x | Medium | Yes | Yes (needs config) |
| Application-level pooling only | Medium — 2–3x | Low | Marginal | No |
| External pooler (Supabase Pooler) | High | Medium-High | Depends on plan | Partial |
| Upgrade Fly Postgres VM size | N/A — more headroom | Very Low | No (paid) | No |

The upgrade path — bumping to a 1 GB VM — increases `max_connections` to roughly 100 and costs around $7–10/month on Fly. For serious production apps, this is often cleaner than wrestling with transaction-mode edge cases. But for free-tier workloads — side projects, demos, MVPs — transaction-mode PgBouncer is the right call.

Application-level pooling (setting `pool: 2` in Ecto or Rails, for example) helps reduce pressure but doesn't solve the problem when you have multiple app instances or serverless functions firing simultaneously.

---

## What This Means for Teams Running on Fly's Free Tier in 2026

**For solo developers and indie hackers**: Set `default_pool_size = 5` in PgBouncer and cap your app's internal pool at 2–3 per worker. That combination keeps you well under 25 connections even with rolling deploys. Test it before launch — not during.

**For early-stage teams with 2–3 engineers**: The free-tier Postgres is genuinely production-risky for anything with real traffic. Budget $7/month for the 1 GB VM upgrade. The engineering time spent debugging connection errors costs far more.

**For Phoenix/Ecto users specifically**: Ecto's connection pool is configurable in `config/runtime.exs`. Setting `pool_size: 2` per node and routing through PgBouncer in transaction mode handles most free-tier workloads cleanly. The Fly community thread shows this combination working reliably for apps under roughly 50 concurrent users.

Watch for one upcoming change: Fly.io has signaled interest in deeper PgBouncer integration with automatic mode selection based on VM memory tier. If that ships in 2026, manual INI editing may become unnecessary for new Postgres deployments.

---

## The Bottom Line

The connection pool exhaustion problem isn't mysterious — it's a memory-constrained PostgreSQL default colliding with connection-hungry frameworks. The fix is transaction-mode PgBouncer with sensible pool sizes. Not glamorous. But it works.

> **Key Takeaways**
> - Free-tier Postgres caps at 25 connections due to 256 MB RAM constraints
> - Transaction-mode PgBouncer reduces server-side connections by 5–8x
> - Prepared statements and advisory locks require code-level fixes under transaction mode
> - Upgrading to a 1 GB VM is the cleaner path for anything approaching real production traffic

Over the next several months, expect Fly.io to improve first-run developer experience around database pooling — the community volume on this issue is too high to ignore. Automatic pooler configuration based on VM size is a likely near-term improvement.

The immediate action: check your `pgbouncer.ini` today. If it says `session`, you're one traffic spike away from this problem.

## References

1. [Fly Managed Postgres and database connection limit using the PG Bouncer - Phoenix - Fly.io](https://community.fly.io/t/fly-managed-postgres-and-database-connection-limit-using-the-pg-bouncer/27103)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-meditating-on-yoga-mat-with-phone-and-drink-G94PWBjH-Yo)*
