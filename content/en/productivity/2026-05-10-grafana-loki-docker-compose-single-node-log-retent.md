---
title: "Grafana Loki Docker Compose Single Node Log Retention Disk Full Fix"
date: 2026-05-10T20:17:05+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "grafana", "loki", "docker", "React"]
description: "Grafana Loki Docker Compose single node disk full? Fix log retention before Promtail backs up and dashboards go dark. Stop the spiral fast."
image: "/images/20260510-grafana-loki-docker-compose-si.webp"
technologies: ["React", "Node.js", "Docker", "Kubernetes", "AWS"]
faq:
  - question: "grafana loki docker compose single node log retention disk full fix"
    answer: "To fix disk full issues on a single-node Loki Docker Compose setup, you need to enable the compactor, set `retention_enabled: true` in the compactor block, and define `retention_period` under `limits_config`. Without all three changes in place, Loki silently ignores retention settings and logs accumulate indefinitely until the volume fills completely."
  - question: "why is loki not deleting old logs even though retention period is set"
    answer: "Loki requires the compactor service to be running and `retention_enabled: true` explicitly set before it will enforce any retention period you configure. If the compactor is missing from your setup, the `retention_period` value in `limits_config` is silently ignored and no logs are ever deleted."
  - question: "how much disk space does loki use in a single node docker compose setup"
    answer: "A moderately busy application logging at INFO level can generate 2–5 GB of compressed Loki chunks per week on a single-node filesystem storage setup. A Kubernetes cluster with around 20 pods can consume 15–40 GB per month, meaning a default 50 GB volume can fill in as little as six weeks without retention policies configured."
  - question: "how to set per tenant log retention in loki docker compose"
    answer: "Loki supports per-tenant retention overrides through the `limits_config` block, allowing you to keep critical application logs longer while applying shorter retention to verbose debug streams. This prevents high-priority logs from being deleted too early without inflating overall storage usage across all log streams."
  - question: "how to monitor loki disk usage before it fills up grafana loki docker compose single node log retention disk full fix"
    answer: "Loki exposes built-in metrics like `loki_ingester_chunks_stored_total` and `loki_compactor_deleted_series_total` that you can use to track storage pressure proactively. Scraping these metrics and setting Grafana alerts on them lets you catch disk growth trends before they cause an outage on your single-node deployment."
---

Disk full. Two words that end on-call shifts fast.

If you're running a **grafana loki docker compose single node** setup and you've hit that wall, you already know the spiral: Loki stops ingesting, Promtail backs up, dashboards go dark, and suddenly your "lightweight logging stack" feels anything but lightweight.

This isn't a rare edge case. Single-node Loki deployments are everywhere in 2026 — small teams, home labs, lean startups that don't need a distributed cluster. The problem is that Loki's default configuration treats disk space like it's infinite. It isn't. Without explicit retention policies, logs accumulate indefinitely until the volume fills and the whole stack chokes.

The fix exists. It's not complicated. But it requires touching three separate configuration layers that the official quick-start docs don't connect clearly.

> **Key Takeaways**
> - Grafana Loki's default `filesystem` storage backend has no retention enabled out of the box — logs accumulate indefinitely until the disk fills.
> - The **grafana loki docker compose single node log retention disk full fix** requires enabling the compactor, setting `retention_enabled: true`, and defining `retention_period` under the `limits_config` block.
> - A single-node Loki instance needs the compactor to run retention deletion; without it, `retention_period` is silently ignored.
> - Configuring per-tenant retention overrides lets you keep critical application logs longer without inflating storage for verbose debug streams.
> - Proactive disk monitoring via Loki's built-in metrics (`loki_ingester_chunks_stored_total`, `loki_compactor_deleted_series_total`) catches storage pressure before it becomes an outage.

---

## Why Single-Node Loki Fills Up Faster Than You'd Expect

Loki was designed around index separation — it stores compressed log chunks on object storage (S3, GCS) and keeps a lightweight index. That architecture scales beautifully in distributed mode. On a single node with `filesystem` storage, though, those chunks land directly on your host volume. No external drain. No automatic cleanup.

According to the [Grafana Labs Community Forums thread on Loki retention configuration](https://community.grafana.com/t/loki-configuration-for-logs-retention/150960), a common mistake is setting `retention_period` without enabling the compactor or without setting `retention_enabled: true` in the `compactor` block. The result: the configuration looks correct, but Loki never actually deletes anything. Logs keep piling up.

The growth rate catches most people off guard. A moderately busy Node.js service logging at INFO level can generate 2–5 GB of compressed chunks per week in Loki. Add a Kubernetes cluster with 20 pods, and you're looking at 15–40 GB monthly — easily filling a 50 GB volume in six weeks on a default docker compose deployment.

The `limits_config.retention_period` parameter controls how long log data is kept globally. The compactor is the process that enforces it. Without both running and connected, the fix is incomplete.

---

## The Compactor Is the Missing Piece

Most guides show you the `retention_period` setting. Few explain that Loki's compactor must be explicitly enabled and pointed at your storage backend before retention deletion actually fires. This gap causes the majority of "I set retention but disk is still full" issues reported in community forums as of Q1 2026.

The minimum compactor configuration for a single-node filesystem deployment:

```yaml
compactor:
  working_directory: /loki/compactor
  shared_store: filesystem
  compaction_interval: 10m
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150
```

The `retention_delete_delay` is deliberate — it gives queriers time to finish reading chunks before they're deleted. Setting it too low (under 30 minutes) on a busy instance can cause read errors mid-query. Don't optimize it away.

---

## Global vs. Per-Tenant Retention

Loki supports two retention scopes: global (applied to all log streams) and per-tenant (applied to specific label matchers). For a single-node stack without multi-tenancy, the global setting under `limits_config` does the heavy lifting.

According to [Faith Sodipe's DevOps.dev breakdown of Loki and Prometheus retention](https://blog.devops.dev/log-and-metric-retention-in-loki-and-prometheus-57e81bbad023), the correct placement is:

```yaml
limits_config:
  retention_period: 168h   # 7 days
```

That's the global floor. If you have noisy debug logs from a specific service you only need for 24 hours, you can override at the stream level using `per_stream_rate_limit` and `per_tenant_override_config`. Keep your critical app logs for 30 days while letting verbose debug streams evict after a day — that single change can dramatically reduce steady-state disk consumption without touching anything else.

This approach can fail when teams set per-tenant overrides inconsistently and lose track of which streams have which TTLs. Document your overrides. A config comment costs nothing; a surprise disk-full at 2 AM costs a lot.

---

## Storage Backend Matters for Retention Behavior

Not all Loki storage configurations support retention the same way. This table shows how the three common single-node approaches differ:

| Feature | `filesystem` (local) | `s3` (MinIO/AWS) | `boltdb-shipper` + `filesystem` |
|---|---|---|---|
| Retention support | ✅ Full (with compactor) | ✅ Full | ⚠️ Partial (index TTL only) |
| Setup complexity | Low | Medium | Medium |
| Compactor required | Yes | Yes | Yes |
| Data survives container restart | Yes (volume mounted) | Yes | Yes |
| Best for | Local single-node | Production single-node | Hybrid/migration |
| Disk full risk | High without retention | Low (offloaded) | Medium |

The `boltdb-shipper` backend — popular in older Loki 2.x setups — has a real nuance: the index TTL and chunk retention can fall out of sync if the compactor isn't running continuously. As of Loki 2.9+, the [TSDB index backend](https://oneuptime.com/blog/post/2026-01-21-loki-docker-compose/view) is the recommended single-node choice, and it handles retention more predictably when paired with `filesystem` storage.

The filesystem backend carries the highest disk-full risk precisely because it's the most common starting point. Teams spin up a docker compose stack from a quick-start template, log volume grows, and nobody added retention config because the stack "just worked" initially. Until it didn't.

---

## Three Scenarios, Three Fixes

**Scenario 1 — Disk already full, Loki won't start.**
Don't delete chunks manually. That corrupts the index. Instead: stop the Loki container, free space by removing old WAL files under `/loki/wal/` (safe to delete when Loki is stopped), then restart with retention properly configured. Loki will compact and delete on the next compaction cycle.

**Scenario 2 — Loki is running but slowly filling up despite `retention_period` being set.**
Check whether `retention_enabled: true` appears under the `compactor` block specifically — not just `limits_config`. Run `curl http://localhost:3100/metrics | grep loki_compactor` to confirm the compactor is active. If `loki_compactor_runs_total` isn't incrementing, the compactor isn't running. Full stop.

**Scenario 3 — Planning a new deployment and want to avoid this entirely.**
Set retention from day one. A 7-day global retention period (`168h`) covers most debugging needs. Add a Prometheus alert on volume disk usage at the 75% threshold — that gives you roughly 2–3 weeks of lead time on a typical small deployment before the disk-full condition hits.

Two Loki metrics worth tracking proactively:
- `loki_ingester_chunks_stored_total` — tracks ingestion volume over time
- `loki_compactor_deleted_series_total` — confirms retention deletion is actually firing

If `loki_compactor_deleted_series_total` stays at zero after a full compaction cycle, something in your config is wrong. That metric is your canary.

---

## Putting It Together

The **grafana loki docker compose single node log retention disk full fix** comes down to three things running together: compactor enabled with `retention_enabled: true`, `retention_period` set under `limits_config`, and the TSDB index backend for predictable deletion behavior. Miss any one of those three, and the other two don't save you.

A few things worth holding onto:

- Default Loki configs have no retention — this is intentional for flexibility, not a bug, but it's a reliable trap for single-node deployments
- The compactor must be explicitly enabled; `retention_period` alone does nothing
- Per-stream overrides let you tune retention granularly without blowing up overall storage
- Proactive metric monitoring beats reactive disk recovery every time

Looking at the Grafana Labs roadmap for the second half of 2026, the team is working on automatic retention recommendations based on observed ingestion rates — essentially a self-tuning compactor. That would eliminate most of this manual configuration. Until that ships, the approach above is what works.

What's your current retention period on your Loki stack — and did you have to find out the hard way that it wasn't working?

## References

1. [How to Run Loki in Docker and Docker Compose](https://oneuptime.com/blog/post/2026-01-21-loki-docker-compose/view)
2. [Log and Metric Retention in Loki and Prometheus | by Faith Sodipe | DevOps.dev](https://blog.devops.dev/log-and-metric-retention-in-loki-and-prometheus-57e81bbad023?gi=1d33a8bff598)
3. [Loki configuration for logs retention - Grafana Loki - Grafana Labs Community Forums](https://community.grafana.com/t/loki-configuration-for-logs-retention/150960)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
