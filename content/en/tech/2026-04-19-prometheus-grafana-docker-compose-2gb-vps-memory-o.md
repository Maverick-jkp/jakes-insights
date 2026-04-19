---
title: "Prometheus Grafana Docker Compose Tuning for 2GB VPS OOM"
date: 2026-04-19T19:58:30+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "prometheus", "grafana", "docker", "Redis"]
description: "Run Prometheus and Grafana on a 2GB VPS without triggering the OOM killer at 3AM. Docker Compose tuning, scrape intervals, and memory limits that actually work."
image: "/images/20260419-prometheus-grafana-docker-comp.webp"
technologies: ["Docker", "Redis", "Linux", "Go"]
faq:
  - question: "prometheus grafana docker compose 2gb vps memory oom killer how to fix"
    answer: "On a 2GB VPS, the default Prometheus and Grafana Docker Compose setup can consume 1–1.8GB of RAM before any workload runs, leaving the kernel no choice but to trigger the OOM killer against Prometheus. The fix involves setting explicit mem_limit values in docker-compose.yml, increasing the scrape interval from 15s to 60s, and disabling unused Grafana features like server-side rendering. A properly tuned stack can fit comfortably within 1.4GB, leaving ~600MB headroom for the OS."
  - question: "prometheus scrape interval 15s vs 60s memory usage difference"
    answer: "Changing the Prometheus scrape interval from 15s to 60s reduces TSDB write operations by roughly 75%, which directly lowers RAM consumption and disk I/O pressure. This change has minimal impact on alerting accuracy for infrastructure-level metrics, since most host-level conditions like CPU spikes or disk pressure develop over minutes, not seconds. It is one of the highest-impact single-line config changes you can make when tuning a prometheus grafana docker compose 2gb vps memory oom killer tuning scrape interval setup."
  - question: "why does the OOM killer keep killing prometheus on my VPS"
    answer: "The Linux OOM killer targets the process with the highest oom_score when the kernel runs out of free memory pages, and Prometheus almost always scores highest due to its large heap size from storing time series data. On a 2GB VPS running a default prometheus grafana docker compose 2gb vps memory oom killer tuning scrape interval stack, Prometheus alone can consume 400–700MB, leaving insufficient room for Grafana, Node Exporter, and OS overhead. Setting a mem_limit in docker-compose.yml forces Docker to enforce a hard cap before the kernel intervenes."
  - question: "how much RAM does grafana use in docker and how to reduce it"
    answer: "Grafana typically uses 200–350MB of RAM in a default Docker deployment, with spikes during dashboard renders. You can significantly reduce its footprint by enabling anonymous access, disabling server-side image rendering, and removing unused data sources at startup. These changes are especially important when running a full monitoring stack on a 2GB VPS where every megabyte counts."
  - question: "minimum VPS size to run prometheus grafana node exporter docker compose"
    answer: "A 2GB VPS is the common entry-level choice for self-hosted Prometheus and Grafana, but it requires deliberate memory tuning to run stably. With default settings, the combined stack including Node Exporter and OS overhead can push 1.8GB, leaving almost no buffer. After tuning the scrape interval, applying mem_limit constraints, and trimming Grafana's features, the stack can run reliably within 1.4GB on a 2GB instance."
---

A 2GB VPS costs around $6–$12/month in 2026. It's the default entry point for self-hosted monitoring. And it's exactly the size where a default `docker compose up` with Prometheus and Grafana will eat your RAM, trigger the OOM killer at 3 AM, and leave you staring at a blank dashboard wondering what happened.

The good news: this is a solved problem. The bad news: most tutorials skip the tuning part entirely.

> **Key Takeaways**
> - A default Prometheus deployment with a 15-second scrape interval can consume 400–700MB of RAM on its own, leaving almost no headroom on a 2GB VPS running Grafana and Node Exporter simultaneously.
> - The Linux OOM killer targets the process with the highest `oom_score` — almost always Prometheus — making memory limits in `docker-compose.yml` a critical safety mechanism, not optional tuning.
> - Increasing the scrape interval from `15s` to `60s` reduces Prometheus TSDB write load by roughly 75%, with minimal impact on alerting accuracy for infrastructure-level metrics.
> - Grafana's memory footprint drops significantly when anonymous access is enabled, server-side image rendering is disabled, and unused data sources are removed at startup.
> - A properly tuned stack can run comfortably within 1.4GB of RAM, leaving ~600MB for the OS and other processes.

---

## The 2GB Wall: Why Default Configs Fail

Prometheus wasn't designed for constrained environments. It was built by SoundCloud engineers to handle millions of time series at scale, and its defaults reflect that origin. The `global.scrape_interval` defaults to `15s`. TSDB retention defaults to `15d`. Both are fine on a 16GB dedicated server. On a 2GB VPS, they're a slow-motion crash.

A typical self-hosted stack — Prometheus, Grafana, Node Exporter, and maybe cAdvisor — will consume memory roughly like this on a fresh deploy with default settings:

| Container | Default RAM Usage | Notes |
|---|---|---|
| Prometheus | 400–700MB | Grows with scrape frequency and series count |
| Grafana | 200–350MB | Spikes on dashboard render |
| Node Exporter | 20–40MB | Stable, low footprint |
| cAdvisor | 100–200MB | Significant if enabled |
| **Total** | **720MB–1.29GB** | Plus OS overhead (~300–500MB) |

That math puts you at 1–1.8GB before any workload runs on the host. The OOM killer kicks in when the kernel can't find free pages. It doesn't give warnings. It just kills the highest-scoring process and moves on.

According to the Grafana Cloud documentation on Docker Compose Linux deployments, the recommended approach for resource-constrained environments starts with adjusting `scrape_interval` and setting explicit `mem_limit` values in Compose — but these options are buried in footnotes, not the main setup flow.

---

## The Core Tuning Levers

### Scrape Interval: The Biggest Bang-Per-Config-Line

The relationship between scrape interval and memory pressure is direct. Prometheus writes a new data point for every metric on every scrape. At `15s`, that's 4 writes per minute per series. At `60s`, it's 1. For a Node Exporter setup tracking ~800 default metrics, that's the difference between ~3,200 writes/minute and ~800 writes/minute.

Change this in `prometheus.yml`:

```yaml
global:
  scrape_interval: 60s
  evaluation_interval: 60s
```

For alerting on things like CPU spikes or disk fill rates, 60-second resolution is entirely adequate. You'd only need 15s for high-frequency application metrics like p99 latency on a busy API — and those workloads shouldn't live on a 2GB VPS anyway.

### Memory Limits in Docker Compose

Docker doesn't automatically protect containers from each other's memory appetite. Without explicit limits, Prometheus can consume all available RAM and starve Grafana mid-render.

Add hard limits in your `docker-compose.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    mem_limit: 512m
    memswap_limit: 512m
  grafana:
    image: grafana/grafana:latest
    mem_limit: 300m
    memswap_limit: 300m
```

Setting `memswap_limit` equal to `mem_limit` disables swap for that container, which prevents thrashing. If Prometheus hits 512MB, Docker sends `SIGKILL` — cleaner than letting the OOM killer pick its own victim at random.

### Prometheus TSDB Retention and Chunk Size

Two more flags that matter on small instances:

```yaml
command:
  - '--storage.tsdb.retention.time=7d'
  - '--storage.tsdb.wal-compression'
```

Dropping retention from 15 days to 7 days cuts on-disk storage roughly in half, which also reduces memory used by the TSDB head block. WAL compression is free performance — available since Prometheus 2.11, it reduces WAL size by ~50% according to the Prometheus project changelog.

### Grafana: Trim the Fat

Grafana's default config assumes a multi-user, plugin-heavy environment. On a 2GB VPS, strip it down:

```ini
[users]
allow_sign_up = false

[auth.anonymous]
enabled = true
org_role = Viewer

[rendering]
# Don't enable server-side rendering unless needed
```

Disabling the image renderer alone saves 150–200MB. The `docker.recipes` Prometheus-Grafana stack template explicitly excludes the renderer for exactly this reason.

---

### Configuration Trade-offs: Conservative vs. Default

| Setting | Default Config | Tuned for 2GB VPS | Trade-off |
|---|---|---|---|
| `scrape_interval` | 15s | 60s | Lower time resolution |
| TSDB retention | 15d | 7d | Shorter history |
| Grafana mem_limit | None | 300MB | Harder crash on spike |
| Prometheus mem_limit | None | 512MB | Prevents OOM cascade |
| WAL compression | Off | On | Tiny CPU cost |
| cAdvisor | Often included | Remove or limit | Less container insight |

The tuned config trades granularity for stability. For most infrastructure monitoring use cases — uptime, disk, CPU trends, memory — that trade-off is worth it.

This approach can fail when your application layer generates high-cardinality metrics. If you're scraping a service that emits per-user or per-request labels, even a 60s interval won't save you. The series count, not the interval alone, drives memory growth. In those cases, `metric_relabel_configs` to drop labels you don't actually query is the fix — not more tuning of the global interval.

---

## Running It Safely: Practical Scenarios

**Scenario 1 — Solo developer, personal projects:** You want visibility without babysitting. Set `scrape_interval: 60s`, drop retention to `7d`, add `mem_limit` to both containers. Enable anonymous viewer access in Grafana. Total RAM budget: ~850MB. Comfortable headroom.

**Scenario 2 — Small production service (under 50 req/s):** Add a lightweight app exporter — the official Redis or Postgres exporter each adds ~20–30MB. Keep Prometheus under 512MB with the retention and scrape tuning above. Monitor `container_memory_usage_bytes` via cAdvisor — but if cAdvisor itself climbs above 180MB, cut it and use Node Exporter's systemd metrics instead.

**Scenario 3 — Still getting OOM-killed despite tuning:** Check `dmesg | grep -i oom` first. If Prometheus is the victim, its `oom_score_adj` can be lowered in the Compose file:

```yaml
oom_score_adj: -500
```

That makes the kernel deprioritize Prometheus when looking for a kill target. It buys time — but the real fix is reducing series cardinality with `metric_relabel_configs` to drop high-cardinality labels you don't actually query. Adjusting the score without fixing the root cause just shifts which process dies next.

---

## What to Expect Over the Next 6–12 Months

Prometheus 3.x (active development as of Q1 2026) is pushing native histogram support and improved TSDB memory management. Early benchmarks from the OpenMetrics working group suggest memory reduction of 15–25% for typical infrastructure workloads in high-cardinality scenarios. That'll matter for 2GB deployments.

Grafana Labs continues improving Grafana's own memory profile — the 10.x series reduced idle memory by ~20% compared to 9.x. These gains compound over time.

Three things worth watching:

- `--storage.tsdb.head-chunks-write-queue-size` tuning in Prometheus 3.x for low-memory modes
- Grafana's Alloy agent (replacing Grafana Agent) as a lighter Prometheus-compatible scraper
- DigitalOcean and Hetzner both offering 4GB tiers at near-2GB pricing — the budget ceiling for "small VPS" monitoring is shifting upward, which changes the calculus on what's worth tuning vs. what's worth paying for

---

A tuned Prometheus and Grafana stack on a 2GB VPS isn't magic. It's four config changes: set `scrape_interval` to `60s`, cap both containers with `mem_limit`, drop retention to `7d`, and enable WAL compression. Do those four things and the OOM killer stops being your on-call engineer.

What's the monitoring metric you find yourself checking at 3 AM most often? That's the one worth keeping at 15s scrape resolution. Everything else can wait a minute.

## References

1. [How to Monitor NVIDIA GPUs with Prometheus & Grafana (Docker Guide)](https://www.servermo.com/howto/monitor-nvidia-gpu-prometheus-grafana/)
2. [Monitoring a Linux host with Prometheus, Node Exporter, and Docker Compose | Grafana Cloud documenta](https://grafana.com/docs/grafana-cloud/send-data/metrics/metrics-prometheus/prometheus-config-examples/docker-compose-linux/)
3. [Prometheus + Grafana Docker Compose - Ready to Deploy | Docker Recipes](https://docker.recipes/monitoring/prometheus-grafana)


---

*Photo by [Ales Nesetril](https://unsplash.com/@alesnesetril) on [Unsplash](https://unsplash.com/photos/gray-and-black-laptop-computer-on-surface-Im7lZjxeLhg)*
