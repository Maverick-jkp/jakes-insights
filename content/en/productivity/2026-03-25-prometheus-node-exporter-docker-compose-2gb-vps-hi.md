---
title: "Prometheus Node Exporter Docker Compose 2GB VPS Memory Tuning"
date: 2026-03-25T20:16:16+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "prometheus", "node", "exporter", "Python"]
description: "Prometheus Node Exporter on a 2GB VPS can trigger 3AM swap storms. Tune Docker Compose memory limits before your monitoring stack becomes the problem."
image: "/images/20260325-prometheus-node-exporter-docke.webp"
technologies: ["Python", "Node.js", "Docker", "Linux", "Go"]
faq:
  - question: "prometheus node exporter docker compose 2gb vps high memory usage tuning how to reduce RAM"
    answer: "To reduce RAM usage on a 2GB VPS, set '--storage.tsdb.retention.time=7d' to cut Prometheus's TSDB memory footprint and disable unused Node Exporter collectors like hwmon, wifi, and nfs. A default Prometheus, Node Exporter, and Grafana Docker Compose stack uses 600MB to 1.1GB at idle, which leaves dangerously little headroom alongside your OS and application processes. Targeted TSDB and query flags in your Docker Compose file can produce measurable reductions without losing core monitoring functionality."
  - question: "why is prometheus using so much memory on a small VPS"
    answer: "Prometheus stores recent time series data in memory-mapped chunks inside its TSDB head block before compacting to disk, which can consume 200-400MB alone on active scrape configs. The default 15-day retention setting and disabled WAL compression on older builds compound this problem significantly. These defaults are optimized for large multi-node production environments, not constrained 2GB VPS deployments."
  - question: "prometheus node exporter docker compose 2gb vps high memory usage tuning disable collectors"
    answer: "Disabling unused Node Exporter collectors such as hwmon, wifi, and nfs can reduce Node Exporter's own memory footprint by 30-40%. You can control which collectors run by passing '--no-collector.hwmon' style flags in your Docker Compose command section. This is one of the quickest wins available when tuning a constrained monitoring stack without removing functionality you actually use."
  - question: "how much RAM does prometheus grafana node exporter use on a 2gb vps"
    answer: "A default Docker Compose stack running Prometheus, Grafana, and Node Exporter consumes between 600MB and 1.1GB of RAM at idle depending on scrape intervals and dashboard complexity. On a 2GB VPS already running Ubuntu 22.04 and an application process, this can leave as little as 400MB of free headroom. This tight margin puts the server at risk of OOM kills, particularly under load spikes."
  - question: "docker compose monitoring stack OOM killer killing app process instead of prometheus"
    answer: "Linux's OOM killer prioritizes terminating processes based on memory scores, and it does not distinguish between your critical application and your monitoring stack. On a 2GB VPS, a bloated default Prometheus configuration can consume enough memory to push the system into OOM territory, where the killer may terminate your app rather than Prometheus itself. Tuning TSDB retention and disabling unused collectors reduces this risk by lowering Prometheus's overall memory footprint."
aliases:
  - "/tech/2026-03-25-prometheus-node-exporter-docker-compose-2gb-vps-hi/"

---

Running Prometheus, Node Exporter, and Grafana on a 2GB VPS sounds manageable — until your server starts swapping at 3 AM and your monitoring stack is the thing being monitored for being too heavy. This happens more than people admit, and the fix requires understanding exactly what's consuming memory and why Docker Compose default configurations are optimized for convenience, not constrained environments.

> **Key Takeaways**
> - A default Prometheus + Node Exporter + Grafana Docker Compose stack consumes between 600MB and 1.1GB of RAM at idle, leaving dangerously little headroom on a 2GB VPS.
> - Prometheus's TSDB (Time Series Database) storage engine is the primary memory culprit, with default retention settings storing 15 days of data in memory-heavy block format.
> - Node Exporter collector filtering can cut its own memory footprint by 30–40% by disabling unused collectors like `hwmon`, `wifi`, and `nfs`.
> - Targeted `--storage.tsdb.*` and `--query.*` flags in your Docker Compose file produce measurable RAM reductions without sacrificing core monitoring functionality.

---

## The 2GB VPS Memory Reality Check

Two gigabytes of RAM sounds like enough. It isn't — not once the OS kernel, SSH daemon, your application process, and a full observability stack are competing for the same pool.

A standard Ubuntu 22.04 LTS installation consumes roughly 200–300MB at idle. Add a lightweight Node.js or Python app and you're already at 500MB before Prometheus touches a single metric. The default Docker Compose monitoring stack — Prometheus, Node Exporter, Grafana — adds another 600MB to 1.1GB depending on scrape intervals and dashboard complexity, according to community benchmarks documented across the Prometheus GitHub issues tracker and Spacelift's Docker Compose monitoring guide.

That leaves 400MB of buffer. Maybe. And Linux's OOM killer doesn't care that it's 3 AM when it decides to terminate your app process instead of Prometheus.

The core problem isn't that these tools are poorly built. They're designed for multi-node production environments where memory is measured in tens of gigabytes. Squeezing them into a constrained VPS requires intentional configuration — not just copy-pasting the standard `docker-compose.yml` from a tutorial.

---

## What's Actually Using All the Memory

### Prometheus TSDB: The Biggest Offender

Prometheus's local storage engine — TSDB — keeps recent data in memory-mapped chunks before compacting them to disk. By default, it retains 15 days of data (`--storage.tsdb.retention.time=15d`) and doesn't cap total storage size.

On a busy scrape configuration with 30-second intervals across 500+ time series, the in-memory head block alone can reach 200–400MB. The `--storage.tsdb.wal-compression` flag is disabled by default on older builds, meaning the Write-Ahead Log also eats uncompressed disk and memory I/O buffer.

Two flags change this immediately:

```yaml
command:
  - '--storage.tsdb.retention.time=7d'
  - '--storage.tsdb.retention.size=512MB'
  - '--storage.tsdb.wal-compression=true'
  - '--query.max-concurrency=2'
  - '--query.timeout=30s'
```

Dropping retention to 7 days and capping size at 512MB cuts Prometheus's working memory by roughly 35–45% in practice, based on documented configurations in the Last9 Prometheus Docker Compose guide.

### Node Exporter: Death by a Thousand Collectors

Node Exporter is deceptively lightweight on paper — its binary sits around 20MB. But it loads every collector by default, including ones that actively poll hardware interfaces that may not even exist on a VPS: `hwmon` (hardware temperature sensors), `wifi`, `nfs`, `infiniband`, `ipvs`.

Each collector runs on every scrape cycle. On a 15-second scrape interval, irrelevant collectors add CPU overhead that translates to memory pressure from goroutine scheduling.

The fix: disable unnecessary collectors explicitly in Docker Compose.

```yaml
command:
  - '--collector.disable-defaults'
  - '--collector.cpu'
  - '--collector.meminfo'
  - '--collector.diskstats'
  - '--collector.filesystem'
  - '--collector.netdev'
  - '--collector.loadavg'
  - '--collector.stat'
  - '--collector.time'
  - '--collector.uname'
```

This allowlist approach — disabling defaults and explicitly enabling only what's needed — can cut Node Exporter's CPU cycles by 30–40% and reduces memory churn from unnecessary goroutine activity.

### Grafana: The Silent RAM Consumer

Grafana idles at 80–150MB but spikes to 300MB+ when dashboards with complex queries are loaded. On a 2GB VPS, spike timing matters enormously.

Two practical mitigations:
- Set `GF_RENDERING_SERVER_URL` only if you're actually using image rendering — it adds roughly 200MB by itself
- Reduce dashboard refresh intervals from 30 seconds to 2–5 minutes for non-critical metrics

---

## Default Stack vs. Tuned Stack on a 2GB VPS

| Component | Default Config RAM | Tuned Config RAM | Key Changes |
|---|---|---|---|
| Prometheus | 350–500MB | 180–280MB | Retention 7d, size cap 512MB, WAL compression |
| Node Exporter | 30–60MB | 20–35MB | Allowlist collectors only |
| Grafana | 100–150MB idle | 80–120MB idle | No renderer, longer refresh |
| **Total Stack** | **480–710MB** | **280–435MB** | — |
| **OS + App headroom** | ~500MB remaining | ~700MB+ remaining | Meaningful buffer restored |

The tuned configuration doesn't sacrifice visibility — it removes noise. CPU metrics, memory, disk I/O, network throughput, and load average all remain in scope. What disappears are sensors that VPS hypervisors never expose anyway.

---

## Practical Configuration and What to Watch

**The docker-compose.yml changes that matter most:**

Apply memory limits directly in the Compose file so Docker enforces a ceiling before the OOM killer escalates:

```yaml
services:
  prometheus:
    mem_limit: 512m
    memswap_limit: 512m
  grafana:
    mem_limit: 256m
    memswap_limit: 256m
  node-exporter:
    mem_limit: 64m
    memswap_limit: 64m
```

Setting `memswap_limit` equal to `mem_limit` prevents containers from quietly spilling into swap — which destroys VPS I/O performance on NVMe-backed instances where swap lives on the same disk as your app data.

**Scrape interval tuning:** Default 15-second scrape intervals generate roughly 5,760 data points per metric per day. On a 2GB VPS, 60-second intervals reduce TSDB write pressure by 75% while preserving per-minute granularity — more than sufficient for infrastructure alerting.

**When this approach can fail:** Hard memory limits through `mem_limit` will cause containers to restart if they breach the ceiling during a metrics burst. Set limits too aggressively and Prometheus restarts mid-collection, creating gaps in your data. The numbers in this guide are starting points, not universal constants. Monitor your actual container memory usage for a week before locking in limits.

**Signals worth tracking:** If you're running this stack on providers like Hetzner CX22 (2GB RAM, ~4.35€/month as of Q1 2026) or DigitalOcean Basic Droplets, watch for memory pressure crossing 85% utilization. That's the threshold where Linux starts aggressive swapping and application latency degrades visibly — well before any OOM event fires.

The Prometheus community is actively developing [Agent Mode](https://prometheus.io/blog/2021/11/16/agent/), a lightweight scrape-only mode that forwards metrics to remote storage without local TSDB overhead. For pure VPS monitoring use cases, Agent Mode pointing to a hosted backend like Grafana Cloud's free tier (10,000 series, 14-day retention) eliminates local storage memory cost entirely. It's worth evaluating as an alternative architecture, particularly if your scrape cardinality keeps climbing and retention matters less than stability.

This isn't always the right answer, though. Remote storage introduces network dependency — if Grafana Cloud has an incident, you lose observability at exactly the wrong moment. Local TSDB, even tuned conservatively, keeps your monitoring self-contained.

---

## Closing Thoughts

Running a Prometheus stack on a 2GB VPS isn't about heroic optimization. It's about recognizing that default configurations assume abundant resources, and three specific changes — TSDB retention caps, Node Exporter collector allowlisting, and Docker memory limits — close most of the gap between "constantly swapping" and "stable under load."

The tuned stack runs at 280–435MB total, restoring 700MB+ of breathing room for your actual workload. That's the difference between a VPS that survives a traffic spike and one that OOMs at the worst possible moment.

**What's your current scrape interval?** If it's 15 seconds on a 2GB box, that's the first thing to change. Drop it to 60 seconds and watch your TSDB memory footprint shrink within hours.

## References

1. [Prometheus with Docker Compose: Guide & Examples](https://spacelift.io/blog/prometheus-docker-compose)
2. [Prometheus with Docker Compose: The Complete Setup Guide | Last9](https://last9.io/blog/prometheus-with-docker-compose/)
3. [How to Set Up a Monitoring Stack with Prometheus, Grafana, and Node Exporter Using Docker Compose - ](https://dev.to/rafi021/how-to-set-up-a-monitoring-stack-with-prometheus-grafana-and-node-exporter-using-docker-compose-17cc)


---

*Photo by [GuerrillaBuzz](https://unsplash.com/@guerrillabuzz) on [Unsplash](https://unsplash.com/photos/diagram-RIvSJTiGwLc)*
