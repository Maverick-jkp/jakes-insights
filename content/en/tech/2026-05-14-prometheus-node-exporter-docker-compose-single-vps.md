---
title: "Prometheus Node Exporter Docker Compose 1GB RAM Memory Tuning"
date: 2026-05-14T21:09:38+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "prometheus", "node", "exporter", "Docker"]
description: "Tune Prometheus Node Exporter on a 1GB VPS with Docker Compose by fixing default retention settings before memory hits 94% and the server crawls."
image: "/images/20260514-prometheus-node-exporter-docke.webp"
technologies: ["Docker", "PostgreSQL", "Linux", "Go"]
faq:
  - question: "prometheus node exporter docker compose single vps 1gb ram memory tuning how to stop OOM kills"
    answer: "OOM kills on a 1GB VPS running Prometheus are almost always caused by missing Docker Compose memory limits, not an undersized server. Adding explicit `mem_limit` and `memswap_limit` directives to each service in your docker-compose.yml prevents any single container from consuming all available host memory. Pairing this with Prometheus TSDB retention tuning (reducing from the default 15 days) typically brings total container memory usage under 650MB."
  - question: "how much ram does prometheus use by default on a small server"
    answer: "Prometheus's default TSDB retention of 15 days can consume between 300–500MB of RAM on a moderately active node, which is catastrophic on a 1GB VPS. Memory usage scales with the number of active time series and the configured chunk range, and default settings assume you have significant headroom available. Reducing retention time and capping in-memory chunks are the two highest-impact tuning changes you can make."
  - question: "prometheus node exporter docker compose single vps 1gb ram memory tuning what limits to set"
    answer: "For a 1GB VPS, a well-tuned stack allocates roughly 200–280MB to the Prometheus server, 15–20MB to Node Exporter, and leaves 150–200MB free for the Linux kernel, systemd, and SSH. In Docker Compose, set `mem_limit` per service and always pair it with `memswap_limit` to prevent swap thrashing under memory pressure. This approach keeps total container memory usage comfortably under 650MB."
  - question: "does node exporter use a lot of memory in docker"
    answer: "Node Exporter itself has a very small memory footprint, typically consuming only 15–25MB even with default collectors enabled. The Prometheus server process is almost always the real source of memory pressure in a monitoring stack. Disabling unused Node Exporter collectors has minimal impact compared to tuning Prometheus TSDB retention and adding Docker Compose memory limits."
  - question: "can you run prometheus and grafana on a 1gb vps digitalocean hetzner"
    answer: "Yes, a full Prometheus, Node Exporter, and Grafana stack can run on a $6/month DigitalOcean Droplet or a Hetzner CX11 with 1GB RAM, but only with explicit tuning from the start. The Linux kernel and SSH consume 150–200MB at idle, so containers must stay within roughly 800MB combined. With Docker Compose memory limits and reduced Prometheus TSDB retention, the stack can run stably within 650MB of container memory."
---

Running a full Prometheus stack on a 1GB VPS sounds like a bad idea. It isn't — but only if you tune it correctly from day one.

Most engineers spin up Prometheus, Node Exporter, and Grafana via Docker Compose, watch the system crawl at 94% memory usage, and assume the server's just too small. The real problem is almost always defaults. Prometheus's default `--storage.tsdb.retention.time` keeps 15 days of data, its chunk encoding eagerly caches in RAM, and Docker Compose applies zero memory limits unless you explicitly configure them. On a 1GB host, that combination is quietly catastrophic.

This analysis covers the exact configuration decisions — with real numbers — that let a Prometheus Node Exporter Docker Compose stack run cleanly on a $6/month Hetzner CX11 or a DigitalOcean Droplet with 1GB RAM.

> **Key Takeaways**
> - Prometheus's default TSDB retention (15 days) consumes roughly 300–500MB RAM on a moderately active node, making 1GB VPS deployments unstable without explicit tuning.
> - Docker Compose memory limits (`mem_limit`) prevent a single container from OOM-killing the host, but require companion `memswap_limit` settings to avoid swap thrash.
> - Node Exporter's default collector set adds negligible RAM overhead. The real culprit is always the Prometheus server process itself.
> - A correctly tuned stack can run comfortably within 650MB total container memory, leaving headroom for the OS kernel and SSH.

---

## Why 1GB VPS Deployments Keep Failing

Single-node monitoring setups exploded between 2023 and 2026 as cheap VPS tiers got more capable. Hetzner's CX11 (1 vCPU, 1GB RAM) runs at €3.29/month as of May 2026. DigitalOcean's Basic Droplet at $6/month matches it. These boxes are genuinely useful for monitoring a small application stack — a few services, a PostgreSQL instance, maybe an nginx reverse proxy.

Prometheus wasn't designed for memory-constrained environments. Its TSDB uses a WAL (write-ahead log) plus in-memory chunks for recent data. According to the Prometheus documentation on storage, memory usage scales with the number of active time series and the configured chunk range. Default settings assume you have headroom. On a 1GB box, you don't.

Docker Compose compounds the problem. Without explicit `mem_limit` directives, each container can consume all available host memory. Prometheus will happily take 700MB, leaving nothing for Node Exporter, Grafana, or the OS itself.

The result: the host's OOM killer fires, containers restart randomly, and the monitoring stack you built to catch problems becomes the source of them.

---

## The Memory Budget: Where Every Megabyte Goes

Start with a hard constraint. On a 1GB VPS, the Linux kernel plus systemd and SSH typically consumes 150–200MB at idle. That leaves roughly **800–850MB** for containers.

A realistic allocation:

| Component | Default RAM Usage | Tuned RAM Usage |
|---|---|---|
| Prometheus Server | 400–600MB | 200–280MB |
| Node Exporter | 15–25MB | 15–20MB |
| Grafana | 120–180MB | 80–120MB |
| OS + SSH overhead | 150–200MB | 150–200MB |
| **Total** | **685MB–1GB+** | **445–620MB** |

The default column regularly exceeds 1GB. The tuned column keeps you comfortably under 800MB. The entire difference comes from four specific Prometheus flags and three Docker Compose memory directives.

---

## Prometheus Flags That Actually Move the Needle

Four startup flags control most of Prometheus's RAM behavior:

```yaml
command:
  - '--config.file=/etc/prometheus/prometheus.yml'
  - '--storage.tsdb.path=/prometheus'
  - '--storage.tsdb.retention.time=7d'
  - '--storage.tsdb.retention.size=512MB'
  - '--storage.tsdb.min-block-duration=2h'
  - '--web.enable-lifecycle'
```

`--storage.tsdb.retention.time=7d` cuts retention from 15 days to 7. That alone reduces TSDB head block size by roughly 40–50% on a typical single-node setup. `--storage.tsdb.retention.size=512MB` adds a hard disk-based cap that prevents runaway data growth from spilling back into RAM pressure through cache.

`--storage.tsdb.min-block-duration=2h` controls how quickly the WAL compacts into persistent blocks. Shorter durations reduce the in-memory WAL size at the cost of slightly more disk I/O — a worthwhile trade on a RAM-limited host.

According to Last9's Prometheus Docker Compose guide, these flags combined with scrape interval tuning — setting `scrape_interval: 30s` instead of the default 15s — can reduce active time series memory pressure by 30–35%.

---

## Docker Compose Memory Limits: The Missing Layer

Flags help, but they don't prevent Prometheus from occasionally spiking. Container limits are the safety net.

Docker's resource limits documentation notes that `mem_limit` sets a hard memory cap while `memswap_limit` controls the combined memory+swap ceiling. Setting them equal prevents swap usage entirely:

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.52.0
    mem_limit: 300m
    memswap_limit: 300m

  node-exporter:
    image: prom/node-exporter:v1.8.1
    mem_limit: 32m
    memswap_limit: 32m

  grafana:
    image: grafana/grafana:10.4.2
    mem_limit: 150m
    memswap_limit: 150m
```

This matters because swap on a VPS uses the same SSD storing your TSDB data. Swap thrash and disk I/O contention hit simultaneously — which is why untuned stacks on 1GB boxes don't just run slowly. They become completely unresponsive.

---

## Node Exporter's Collector Footprint

Node Exporter itself is lean. Version 1.8.x uses roughly 15–20MB RSS in a typical Docker deployment. The default collector set — cpu, diskstats, filesystem, loadavg, meminfo, netdev, netstat, stat, time, uname — covers everything useful for single-host monitoring.

Spacelift's Prometheus Docker Compose guide notes that disabling unused collectors via `--no-collector.<name>` flags can trim this slightly, but the savings are marginal. Don't spend time here. Node Exporter isn't your memory problem.

What does matter: mount the host's proc and sys filesystems correctly so Node Exporter reads real hardware metrics rather than container-namespaced ones:

```yaml
volumes:
  - /proc:/host/proc:ro
  - /sys:/host/sys:ro
  - /:/rootfs:ro
command:
  - '--path.procfs=/host/proc'
  - '--path.sysfs=/host/sys'
```

Skip this step and your memory and CPU graphs will reflect container namespace values — not what's actually happening on the host.

---

## Three Scenarios, Three Fixes

**Scenario 1 — OOM kills happening every few days.** Prometheus is eating all available RAM. Fix: add `mem_limit: 300m` and `memswap_limit: 300m` to the Prometheus service in `docker-compose.yml`. Restart the stack. Monitor with `docker stats` for 24 hours to confirm the ceiling holds.

**Scenario 2 — Grafana loads slowly but nothing crashes.** Grafana's default SQLite database and plugin cache are competing with Prometheus for RAM. Fix: set `mem_limit: 120m` on Grafana, and add `GF_DATABASE_WAL=true` as an environment variable to reduce SQLite's write-ahead log pressure.

**Scenario 3 — Disk fills faster than expected, causing memory spikes during compaction.** Default 15-day retention plus high-cardinality scrape targets causes large TSDB compaction events. Fix: set `--storage.tsdb.retention.time=5d` and audit your scrape targets. Node Exporter v1.8+ exposes roughly 800 time series by default. Each additional Docker container you're scraping adds approximately 200–400 more.

### When This Approach Doesn't Work

This tuning works well for small, stable application stacks. It starts breaking down when you're scraping more than 10–15 services, when your scrape targets expose high-cardinality labels (per-request IDs, dynamic hostnames), or when you need more than 7 days of retention for compliance or trend analysis. In those cases, a 1GB VPS isn't the right host — or you need to push metrics to a remote storage backend like Grafana Cloud's free tier and use the local Prometheus as a relay only.

---

## What to Do Right Now

Getting this stack right comes down to three decisions: cut TSDB retention to 7 days or less, add explicit `mem_limit` directives to every service, and set scrape intervals to 30 seconds. Those three changes take a failing stack to a stable one.

The quick summary:
- Default Prometheus settings are not safe on 1GB hosts without explicit memory caps
- `mem_limit` + `memswap_limit` parity eliminates swap thrash
- 7-day retention reduces RAM usage 40–50% compared to the 15-day default
- Node Exporter itself is not the memory problem — it never was

Over the next 6–12 months, Prometheus 3.x's native histogram support will further reduce time series cardinality, which should make 1GB deployments more comfortable out of the box. But that migration requires updating both Prometheus and any clients sending classic histograms — so it's not a drop-in fix.

The action right now: pull your current container memory usage with `docker stats --no-stream`, compare it against the budget table above, and apply limits before your next OOM event — not after.

## References

1. [Prometheus with Docker Compose: Guide & Examples](https://spacelift.io/blog/prometheus-docker-compose)
2. [Prometheus with Docker Compose: The Complete Setup Guide | Last9](https://last9.io/blog/prometheus-with-docker-compose/)
3. [CPU and Memory Limits in Docker Compose - Docker Compose Guide | Docker Recipes](https://docker.recipes/docs/resource-limits)


---

*Photo by [Growtika](https://unsplash.com/@growtika) on [Unsplash](https://unsplash.com/photos/a-computer-with-a-keyboard-and-mouse-9WnjxT1NCoY)*
