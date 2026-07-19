---
title: "Prometheus Grafana Docker Compose on a 1GB VPS: Low Memory Tuning"
date: 2026-05-16T20:16:03+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "prometheus", "grafana", "docker", "Node.js"]
description: "Run Prometheus + Grafana via Docker Compose on a 1GB VPS without OOM kills. Includes low-memory tuning to cut default 400–600MB RAM usage down to size."
image: "/images/20260516-prometheus-grafana-docker-comp.webp"
technologies: ["Node.js", "Docker", "PostgreSQL", "Linux", "Go"]
faq:
  - question: "how to run prometheus grafana docker compose on 1gb ram vps without running out of memory"
    answer: "Running prometheus grafana docker compose on a single vps 1gb ram requires deliberate low memory tuning rather than default settings. The practical 2025 approach is to budget around 200MB for Prometheus, 150MB for Grafana, and 100MB for node_exporter, using Docker Compose mem_limit to enforce these caps and prevent any single container from OOM-killing your entire server."
  - question: "prometheus docker memory usage too high how to reduce"
    answer: "Default Prometheus Docker containers consume 400–600MB of RSS out of the box due to aggressive TSDB defaults like 15-day retention and unlimited query concurrency. Setting --storage.tsdb.retention.time=7d and --query.max-concurrency=2 can reduce memory usage by roughly 40%, making it viable for low-resource hosts."
  - question: "prometheus grafana docker compose single vps 1gb ram low memory tuning 2025 best settings"
    answer: "For prometheus grafana docker compose single vps 1gb ram low memory tuning in 2025, the most impactful settings are shortening TSDB retention to 7 days, capping query concurrency at 2, disabling unused Grafana plugins, and setting GF_DATABASE_WAL=false for SQLite. Docker Compose mem_limit values should be treated as mandatory, not optional, to prevent cascading OOM failures."
  - question: "grafana high memory usage docker how to fix"
    answer: "Grafana's memory footprint can be significantly reduced by disabling unused plugins and setting GF_DATABASE_WAL=false when using the default SQLite database. Targeting around 150MB RSS for the Grafana container is achievable on constrained hosts with these configuration changes."
  - question: "victoriametrics vs prometheus low memory vps which is better 2025"
    answer: "VictoriaMetrics can reduce memory usage by 3–7x compared to a default Prometheus deployment, making it attractive for prometheus grafana docker compose single vps 1gb ram low memory tuning in 2025. However, it introduces additional operational complexity, so for simple setups scraping only a handful of targets, a properly tuned Prometheus configuration may be the more practical choice."
aliases:
  - "/tech/2026-05-16-prometheus-grafana-docker-compose-single-vps-1gb-r/"

---

Most monitoring guides assume you have RAM to burn. A 1GB VPS doesn't.

The default Prometheus Docker image consumes 400–600MB of RSS out of the box. Add Grafana's default configuration and you've already eaten your entire server before your application even starts. But this setup *can* work on a single 1GB VPS — if you tune it deliberately instead of just running `docker compose up` and hoping for the best.

This is a practical breakdown of how to run Prometheus and Grafana on a resource-constrained host without getting OOM-killed at 2am.

> **Key Takeaways**
> - Default Prometheus allocates memory aggressively; `--storage.tsdb.retention.time=7d` and `--query.max-concurrency=2` together reduce RSS by roughly 40% on low-resource hosts.
> - Grafana's memory footprint drops significantly when you disable unused plugins and set `GF_DATABASE_WAL=false` on SQLite.
> - On a 1GB VPS, the practical container memory budget is ~200MB Prometheus + ~150MB Grafana + ~100MB node_exporter, leaving headroom for your actual workload.
> - Docker Compose resource limits (`mem_limit`) are non-optional on constrained hosts — without them, a single slow query can OOM the entire server.
> - Lightweight alternatives like VictoriaMetrics can cut Prometheus memory usage by 3–7x, but introduce operational complexity that may not be worth it for simple setups.

---

## Why This Stack Ends Up on 1GB Instances So Often

The $4–6/month VPS tier — Hetzner CX11, DigitalOcean Basic, Vultr's 1GB Cloud Compute — became the default "I want monitoring for my side project" choice for one simple reason: it's cheap enough to run indefinitely. According to Hetzner's 2025 pricing, a CX22 instance with 2 vCPU and 4GB RAM costs €4.35/month. But plenty of engineers still run everything on the 1–2GB tier to minimize recurring costs.

The problem is that Prometheus was architected for fleet-scale observability at companies like SoundCloud (its origin) and Google. Its default settings reflect that heritage. Out of the box, `tsdb` retains 15 days of data, the WAL is unbounded during heavy scrape intervals, and query concurrency has no practical ceiling. None of that is appropriate for a single server scraping 3–4 targets every 15 seconds.

This isn't an obscure edge case. Engineers consistently report in GitHub issues on both the Prometheus and Grafana repositories that naive deployments hit 800MB+ total memory on 1GB instances, triggering Linux OOM kills on the database or application process they were trying to monitor in the first place.

The fix isn't exotic. It's configuration discipline.

---

## The Memory Budget: Where the RAM Actually Goes

Before tuning anything, establish your actual memory ceiling. On a 1GB (1024MB) VPS, you can't give monitoring more than ~30% of available RAM without starving your application. That's a hard cap of roughly 300–350MB for the entire observability stack.

Memory distribution across default vs. tuned configurations:

| Component | Default RSS | Tuned RSS | Savings |
|---|---|---|---|
| Prometheus | 450–600MB | 180–220MB | ~60% |
| Grafana | 200–280MB | 120–160MB | ~40% |
| node_exporter | 15–25MB | 15–25MB | Minimal |
| **Total** | **665–905MB** | **315–405MB** | **~50%** |

*RSS estimates based on community benchmarks from Prometheus GitHub issues #11891 and Grafana community forums, 2024–2025.*

The tuned total still exceeds 300MB at the high end — which is why `mem_limit` enforcement in Docker Compose is the actual safety net, not a nice-to-have.

---

## The Tuning Playbook: Prometheus First

Prometheus is where you get the most leverage. Four settings do the heavy lifting.

**`--storage.tsdb.retention.time=7d`** — Default is 15 days. Cutting retention in half cuts disk and memory proportionally for time-series data. For a personal VPS, 7 days of metrics history is almost always enough.

**`--storage.tsdb.wal-compression`** — Enables Snappy compression on the WAL. According to the official Prometheus documentation, this reduces WAL disk usage by roughly 50%, which indirectly reduces mmap pressure on low-RAM systems.

**`--query.max-concurrency=2`** — Default is 20. On a single-core or dual-core VPS, 20 concurrent queries is a denial-of-service scenario waiting to happen. Set this to 2 or 3.

**`scrape_interval: 30s`** instead of the default 15s — This halves the ingest rate and directly reduces TSDB head block churn.

In your `docker-compose.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.51.0
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=7d'
      - '--storage.tsdb.wal-compression'
      - '--query.max-concurrency=2'
    mem_limit: 256m
    memswap_limit: 256m
```

Setting `memswap_limit` equal to `mem_limit` disables swap usage for the container. That matters because swap thrashing on a VPS with shared disk I/O is often worse than an OOM kill.

---

## Grafana Tuning: The Settings Nobody Talks About

Grafana's memory issues are less obvious but just as impactful on constrained setups.

**Disable unused plugins.** Grafana loads all installed panel plugins at startup. The Docker image ships with roughly 15 plugins enabled by default. Set `GF_PLUGINS_ENABLE_ALPHA=false` and explicitly list only the plugins you use via `GF_INSTALL_PLUGINS`.

**Skip the renderer.** The optional `grafana-image-renderer` plugin can consume 200MB on its own. Don't install it unless you specifically need PNG export.

**SQLite WAL mode.** Grafana uses SQLite by default for its internal database. On constrained hosts, setting `GF_DATABASE_WAL=false` reduces write amplification at the cost of slightly slower concurrent writes — a reasonable tradeoff when you're the only user.

```yaml
  grafana:
    image: grafana/grafana:10.4.2
    environment:
      - GF_PLUGINS_ENABLE_ALPHA=false
      - GF_DATABASE_WAL=false
      - GF_LOG_LEVEL=warn
    mem_limit: 192m
    memswap_limit: 192m
```

`GF_LOG_LEVEL=warn` alone can reduce I/O noise by 30–40% on verbose Grafana deployments. Small setting, real impact.

---

## VictoriaMetrics vs. Prometheus: When to Switch

VictoriaMetrics is the obvious alternative worth knowing about. It's a drop-in Prometheus replacement that, according to VictoriaMetrics' own benchmarks, uses 3–7x less RAM for equivalent workloads. That's a genuine difference, not marketing copy.

| Criteria | Prometheus | VictoriaMetrics (single-node) |
|---|---|---|
| Memory (1K series, 15s scrape) | ~200MB tuned | ~40–60MB |
| PromQL compatibility | Native | High (not 100%) |
| Ecosystem maturity | 10+ years | ~6 years |
| Docker image size | 180MB | 32MB |
| Alerting | Requires Alertmanager | Built-in |
| Complexity for simple setups | Low | Low |
| **Best for** | Standard setups, broad community support | Memory-constrained hosts, high cardinality |

The case for switching is strong *if* memory is your primary constraint and you don't rely on Prometheus-specific recording rules or Alertmanager integrations. For a typical 1GB VPS running a single application, the tuned Prometheus approach gets the job done without adding another unfamiliar system to troubleshoot at 2am.

This approach can fail when you're running high-cardinality metrics — hundreds of labels, dozens of microservices — even with tuning. That's when VictoriaMetrics stops being optional.

---

## What Breaks If You Skip This

Three real failure patterns on under-tuned setups:

**Scenario 1 — Your app gets OOM-killed, not monitoring.** Linux's OOM killer targets the largest RSS consumer. With default Prometheus eating 500MB+, your Node.js app or PostgreSQL instance gets killed first. You lose the service you were supposed to be monitoring, while Prometheus keeps running, obliviously healthy.

**Scenario 2 — Dashboard queries cause memory spikes.** A single "last 7 days" query against Prometheus with default concurrency settings can spike memory by 150–200MB briefly. Without `mem_limit`, that spike propagates instantly. With `mem_limit`, the query fails gracefully with a 500 error instead of taking down the server.

**Scenario 3 — WAL accumulation during restart loops.** If Prometheus crashes and restarts repeatedly — common during initial setup — the WAL grows unbounded because compaction hasn't run. On a 20GB disk VPS, you can fill the disk within hours. Add `--storage.tsdb.retention.size=2GB` as an explicit ceiling.

---

## The Complete Compose File

A minimal but complete `docker-compose.yml` for a memory-constrained single-VPS setup:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.51.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=7d'
      - '--storage.tsdb.retention.size=2GB'
      - '--storage.tsdb.wal-compression'
      - '--query.max-concurrency=2'
    mem_limit: 256m
    memswap_limit: 256m
    restart: unless-stopped

  grafana:
    image: grafana/grafana:10.4.2
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_PLUGINS_ENABLE_ALPHA=false
      - GF_DATABASE_WAL=false
      - GF_LOG_LEVEL=warn
    mem_limit: 192m
    memswap_limit: 192m
    ports:
      - "3000:3000"
    restart: unless-stopped

  node_exporter:
    image: prom/node-exporter:v1.8.0
    mem_limit: 32m
    memswap_limit: 32m
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

Total enforced memory ceiling: 480MB. That leaves 544MB for your application, OS overhead, and the Docker daemon — tight, but workable.

---

## Which Scenario Are You In?

**Solo developers running side projects:** The tuned Prometheus + Grafana stack is the right call. Don't over-engineer it with VictoriaMetrics unless you're still hitting memory limits after tuning. The community documentation, pre-built dashboards (Grafana's library had 6,000+ community dashboards as of early 2026), and Alertmanager integrations are worth the slightly higher baseline memory.

**Teams running staging environments on cheap VPS instances:** Add `--web.enable-lifecycle` to Prometheus so you can hot-reload config without container restarts. And cap `scrape_interval` at 60s for staging — you don't need 15-second resolution on an environment that runs twice a week.

**Anyone hitting 90%+ memory utilization after tuning:** That's the signal to either upgrade to a 2GB instance or migrate to VictoriaMetrics single-node. The $3–4/month cost difference for the next tier up is almost always cheaper than the engineering time spent squeezing more performance out of 1GB.

---

## The Bottom Line

Running Prometheus and Grafana on a 1GB host isn't a hack. It's a configuration problem with known solutions. Set retention to 7 days, cap query concurrency, enable WAL compression, enforce `mem_limit` in Compose, and disable Grafana features you don't use. That moves you from a server-killing 800MB+ default footprint to a manageable 350–480MB stack.

The biggest mistake isn't the initial setup. It's running with defaults and assuming Docker will handle resource contention gracefully.

It won't. The OOM killer will — and it won't pick the right process.

What's your current VPS memory budget? If you're running this stack on under 2GB, what other optimizations have proven worth the effort?

## References

1. [Prometheus + Grafana Docker Compose - Ready to Deploy | Docker Recipes](https://docker.recipes/monitoring/prometheus-grafana)
2. [One Dashboard To Rule Your Servers: Grafana + Prometheus](https://victornava.dev/2025/09/09/one-dashboard-to-rule-your-servers-grafana-prometheus-for-proxmox-kvm-vps-and-dedicated-boxes/)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-working-at-a-desk-in-a-cozy-home-office-rIPVJ6dMOPI)*
