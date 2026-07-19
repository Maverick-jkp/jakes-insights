---
title: "Grafana Loki on a 1GB VPS: Docker Compose Memory Limits"
date: 2026-05-05T20:31:52+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "grafana", "loki", "docker", "Node.js"]
description: "Running Loki on a 1GB VPS via Docker Compose? Avoid OOM kills and log gaps with tuned ingestion limits built for low memory hosts."
image: "/images/20260505-grafana-loki-docker-compose-si.webp"
technologies: ["Node.js", "Docker", "Kubernetes", "Linux", "Go"]
faq:
  - question: "grafana loki docker compose single node log ingestion limit low memory vps 1gb settings"
    answer: "On a 1GB VPS, you should explicitly tune Loki's default ingestion_rate_mb from 4 to a lower value and ingestion_burst_size_mb from 6 to reduce memory pressure. Running Loki, Promtail, and Grafana together via Docker Compose consumes 600–750MB at idle, leaving under 300MB before the Linux OOM killer activates."
  - question: "how to stop loki container getting OOM killed on 1gb vps"
    answer: "The most effective fix is lowering chunk_target_size from the default 1.5MB to 256KB and setting max_chunk_age to 1m, which forces Loki to flush chunks to disk earlier instead of buffering them in memory. Using Loki's monolithic single-binary deployment mode instead of separate microservice containers also reduces overall RAM consumption significantly."
  - question: "grafana loki docker compose single node log ingestion limit low memory vps 1gb recommended architecture"
    answer: "For a 1GB VPS, Loki's monolithic deployment mode — where all components run in a single process — is the recommended architecture because it uses less RAM than running separate microservice containers. This approach, combined with explicit memory budgeting from the start, allows the stack to run reliably on constrained hosts like Hetzner CX11s or DigitalOcean Droplets."
  - question: "loki promtail grafana docker compose memory usage 1gb droplet"
    answer: "Running Loki, Promtail, and Grafana together on a 1GB host consumes roughly 600–750MB at idle, which leaves less than 300MB of headroom before the OS OOM killer starts terminating containers. The default Grafana Labs Docker Compose reference configurations are designed for developer laptops and assume available memory, making them unsuitable for 1GB production VMs without tuning."
  - question: "loki chunk_target_size and max_chunk_age settings for low memory server"
    answer: "Setting chunk_target_size to 256KB (down from the 1.5MB default) and max_chunk_age to 1m forces Loki to flush in-memory log chunks to disk more frequently, significantly reducing memory pressure. These two settings are considered the single biggest lever for reducing Loki's memory footprint on memory-constrained servers."
aliases:
  - "/tech/2026-05-05-grafana-loki-docker-compose-single-node-log-ingest/"

---

Running Grafana Loki on a $5/month VPS sounds like a win. Until your container gets OOM-killed at 3am and you're staring at a 6-hour log gap you can't explain.

This is a real operational problem in 2026. As more teams move monitoring stacks to cheap cloud VMs — DigitalOcean Droplets, Hetzner CX11s, Linode Nanodes — the pattern of running Loki, Promtail, and Grafana together on a 1GB host keeps surfacing in incident postmortems. The constraints are well-documented at the component level. What's less obvious is how they compound when all three services share the same memory ceiling.

The core argument: a single-node Loki deployment on a 1GB VPS *can* work reliably, but only if you treat memory budgeting as a first-class concern from day one — not an afterthought after your first OOM crash.

> **Key Takeaways**
> - Grafana Loki's default `filesystem` storage in single-node mode writes chunks to disk but still buffers ingested streams in memory. The defaults — `ingestion_rate_mb: 4` and `ingestion_burst_size_mb: 6` — both need explicit tuning on a 1GB host.
> - On a 1GB VPS running Loki + Promtail + Grafana via Docker Compose, the three containers together consume roughly 600–750MB at idle, leaving less than 300MB headroom before the Linux OOM killer activates.
> - The single biggest lever for reducing Loki's memory footprint is lowering `chunk_target_size` from the default 1.5MB to 256KB and setting `max_chunk_age` to 1m — this forces earlier chunk flushing and cuts in-memory pressure significantly.
> - Loki's monolithic deployment mode (single binary, all components in one process) uses less RAM than running separate microservice containers, making it the right architecture choice for constrained VPS environments.

---

## Background: Why This Setup Even Exists

Grafana Loki launched in 2018 as a cost-efficient alternative to Elasticsearch-based log stacks. The design philosophy — index only labels, store log lines compressed on object storage — made it genuinely attractive for small teams. By 2024, Loki had become the default log aggregation layer in a large share of self-hosted monitoring stacks.

The typical Docker Compose setup people reach for today pairs Loki with Promtail (log shipper) and Grafana (visualization), all sitting behind a reverse proxy. According to Grafana Labs documentation and community guides published through early 2026, the reference `docker-compose.yml` for this stack pulls three separate images: `grafana/loki:3.x`, `grafana/promtail:3.x`, and `grafana/grafana:latest`.

The problem is that these reference configurations are written for developer laptops, not 1GB VMs in production. The defaults assume available memory. On a 1GB host — the kind that costs $4–6/month from Hetzner, Vultr, or DigitalOcean — those defaults will kill your stack under moderate log volume.

And the baseline has shifted. Log volume per service has grown considerably since 2020, when the 1GB VPS + Loki combo was first popularized. Structured logging is now standard across most frameworks. A single Node.js service with `pino` logging at `info` level can push 500KB–2MB of logs per minute during normal traffic. That's a meaningfully different operating environment than the one these defaults were designed for.

---

## The Real Memory Budget on a 1GB VPS

Start with the math. A fresh Ubuntu 24.04 VPS with 1GB RAM has roughly 850MB available after the OS reserves its baseline. The Docker daemon itself consumes ~50–80MB. That leaves approximately 770MB for your containers.

The three-service Compose stack at idle looks roughly like this:

| Container | Idle RAM (observed) | Peak RAM (under load) |
|-----------|--------------------|-----------------------|
| `grafana/loki:3.x` | 180–250MB | 400–600MB+ |
| `grafana/promtail:3.x` | 40–70MB | 100–150MB |
| `grafana/grafana:latest` | 120–180MB | 200–300MB |
| **Total** | **340–500MB** | **700MB–1GB+** |

Peak RAM under load routinely exceeds the 1GB ceiling. Default Loki configurations don't set hard memory limits — so Go's runtime will happily consume all available memory when chunk buffers fill up during a log burst. The Linux OOM killer then terminates the highest-memory process, which is almost always Loki.

This isn't a theoretical edge case. It's a predictable outcome of running default configs on constrained hardware.

---

## The Configuration Levers That Actually Matter

Three settings control most of Loki's memory behavior in `loki-config.yaml`:

**1. Chunk flushing aggressiveness**

```yaml
chunk_store_config:
  chunk_target_size: 262144    # 256KB instead of default 1.5MB
  max_chunk_age: 1m            # flush early, don't buffer long
```

Smaller chunks mean Loki flushes to disk more frequently. You trade slightly higher I/O for dramatically lower in-memory buffer pressure. On a 1GB VPS with an NVMe-backed SSD — standard on Hetzner CX11 and DigitalOcean Basic Droplets — this I/O cost is negligible.

**2. Ingestion rate limits**

```yaml
limits_config:
  ingestion_rate_mb: 2         # down from default 4
  ingestion_burst_size_mb: 4   # down from default 6
  per_stream_rate_limit: 512KB
```

These are per-tenant rate limits. Lowering them doesn't drop logs — it backpressures Promtail, which buffers locally instead. Promtail's local buffer is configurable and far cheaper memory-wise than Loki's in-memory chunks.

**3. Query memory limits**

```yaml
query_range:
  results_cache:
    cache:
      enable_fifocache: true
      fifocache:
        max_size_bytes: 33554432   # 32MB hard cap on query cache
```

Default query cache in Loki has no hard size cap. Under a dashboard with multiple panels querying 24 hours of logs, this cache can spike to 200MB+ on its own. That's the silent RAM killer most guides never mention.

---

## Monolithic Mode vs. Microservice Compose Setup

This is the architectural decision most guides skip entirely.

Loki supports a `target: all` flag that runs all components — ingester, querier, compactor, ruler — inside a single process. Monolithic mode shares Go runtime memory between components rather than duplicating overhead across separate containers. According to Grafana Labs' own deployment documentation, monolithic mode is explicitly recommended for single-node deployments.

The practical difference on a 1GB host:

| Deployment Mode | Memory Overhead | Config Complexity | Failure Isolation |
|-----------------|-----------------|-------------------|-------------------|
| Monolithic (`target: all`) | Low (~180MB idle) | Simple, one config | Single point of failure |
| Microservice Compose | High (~400MB+ idle) | Complex, multiple configs | Better isolation |
| Kubernetes (even k3s) | Very High (k3s alone ~512MB) | Very complex | Best isolation |

For a 1GB VPS, monolithic is the only rational choice. Kubernetes — even lightweight k3s — consumes so much baseline memory that there's nothing left for actual workloads. The failure isolation benefits simply don't justify the overhead when you're working with this little RAM.

---

## Three Scenarios Worth Planning For

**Scenario 1: Personal project, fewer than 10 services, low log volume (under 1MB/min total)**

This works fine with defaults *if* you add hard memory limits to your Compose file:

```yaml
services:
  loki:
    mem_limit: 400m
    memswap_limit: 400m
```

Hard limits prevent OOM kills from cascading. Loki will reject ingestion instead of crashing the host — a much better failure mode.

**Scenario 2: Small production app, 10–30 services, moderate log volume (1–5MB/min)**

Apply all three config changes above. Run Loki in monolithic mode. Configure Promtail's `client.backoff_config` to handle rate limit rejections gracefully. Monitor with `container_memory_usage_bytes` in Prometheus and set an alert at 80% of your `mem_limit`.

**Scenario 3: Growing team, 30+ services, log spikes during deploys**

A 1GB VPS hits its ceiling here — and no amount of tuning changes that. The right move is upgrading to a 2–4GB node *before* you need it, or moving Loki's storage backend to S3-compatible object storage (MinIO, Backblaze B2) and running Loki with `store_gateway` to offload memory pressure from local disk queries. This approach can still fail during aggressive deploy bursts if Promtail's local buffer isn't sized correctly — so test your spike behavior before calling it production-ready.

---

## Where This Goes From Here

Running this stack on a 1GB VPS is viable. But "viable" requires deliberate configuration, not copy-pasted defaults.

The key findings hold up across scenarios:

- Default Loki configs assume 1–4GB RAM *for Loki alone*. They're not written for shared 1GB hosts.
- Monolithic deployment mode, aggressive chunk flushing (256KB target, 1m max age), and hard `mem_limit` in Compose are the three non-negotiable changes.
- Query cache is the silent RAM killer. Cap it at 32MB.
- At sustained log ingestion above 5MB/min, upgrade your host. The $4/month savings aren't worth the 3am pages.

Looking at the next 6–12 months: Grafana Labs shipped Loki 3.x with improved memory management for single-node deployments, and the project's roadmap points toward further work on automatic resource detection. There's a reasonable case that by late 2026, `target: all` mode will ship with memory-aware defaults that self-tune based on available host RAM.

Until that lands, treat your Loki config the way you'd treat any production database config on constrained hardware. The defaults are starting points. Not production settings.

If you're already pushing past 2MB/min on a 1GB host and haven't tuned these settings, pull up your container memory graphs before reading anything else. That's where your answer is.

---

- OneUptime Engineering Blog, "How to Run Loki in Docker and Docker Compose" (January 2026): https://oneuptime.com/blog/post/2026-01-21-loki-docker-compose/view
- Amol Mali, "Monitoring Stack with Prometheus, Grafana, and Loki using Docker," Medium/DevOps with Amol: https://devopswithamol.medium.com/monitoring-stack-with-prometheus-grafana-and-loki-using-docker-ed3759f0628b
- Grafana Labs, Loki Deployment Modes documentation: https://grafana.com/docs/loki/latest/setup/

## References

1. [How to Run Loki in Docker and Docker Compose](https://oneuptime.com/blog/post/2026-01-21-loki-docker-compose/view)
2. [Setting Up Grafana Loki on Kubernetes: A Simplified Guide | by Sagar Srivastava | Medium](https://sagar-srivastava.medium.com/setting-up-grafana-loki-on-kubernetes-a-simplified-guide-97fbf850ba55)
3. [Monitoring Stack with Prometheus, Grafana, and Loki using Docker | by Amol Mali | Medium](https://devopswithamol.medium.com/monitoring-stack-with-prometheus-grafana-and-loki-using-docker-ed3759f0628b)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
