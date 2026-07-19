---
title: "Prometheus Scrape Interval 15s vs 30s Memory Usage on 1GB VPS"
date: 2026-03-27T20:18:12+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-web", "prometheus", "scrape", "interval", "Redis"]
description: "Prometheus scrape_interval 15s vs 30s on a 1GB VPS can mean the difference between a stable stack and a 2 AM OOM-kill. Here's what to change."
image: "/images/20260327-prometheus-scrape-interval-15s.webp"
technologies: ["Redis", "Go"]
faq:
  - question: "Prometheus scrape interval 15s vs 30s memory usage difference single VPS 1GB RAM"
    answer: "On a 1GB VPS, changing the Prometheus scrape interval from 15s to 30s can reduce memory consumption by roughly 40–60% for the same target set. This is because the TSDB head block holds approximately 2 hours of data, so halving the scrape interval nearly doubles the number of samples stored in memory before compaction runs."
  - question: "does Prometheus scrape interval affect RAM usage"
    answer: "Yes, scrape interval directly impacts how much RAM Prometheus consumes because more frequent scrapes generate more samples per active series stored in the in-memory head block. Shorter intervals like 15s mean more samples accumulate before the 2-hour compaction window closes, increasing overall memory pressure significantly."
  - question: "Prometheus OOM kill on 1GB VPS how to fix"
    answer: "The most common cause of Prometheus OOM kills on a 1GB VPS is a scrape interval that is too short, typically the community-default 15s. Switching to a global 30s scrape interval while reserving 15s overrides only for SLO-critical jobs is the recommended fix to recover memory headroom without losing meaningful observability."
  - question: "best Prometheus scrape interval for low memory server"
    answer: "For low-memory servers like a 1GB VPS, a global scrape interval of 30s is recommended over the popular 15s default. You can still use per-job overrides to scrape latency-sensitive or SLO-tracked targets at 15s, keeping memory usage manageable while retaining granularity where it actually matters."
  - question: "how much memory does Prometheus use with 15s vs 30s scrape interval"
    answer: "The Prometheus scrape interval 15s vs 30s memory usage difference on a single VPS with 1GB RAM is significant enough to cause instability, with 15s consuming roughly 40–60% more memory than 30s on an equivalent target set. The increase stems from the TSDB head block retaining approximately twice as many samples per series across its 2-hour window when scraping at the shorter interval."
aliases:
  - "/tech/2026-03-27-prometheus-scrape-interval-15s-vs-30s-memory-usage/"

---

Running Prometheus on a 1GB VPS costs you nothing upfront — until your monitoring stack OOM-kills itself at 2 AM during a traffic spike, and you wake up to zero visibility into what just happened.

That default `scrape_interval: 15s` in your `prometheus.yml` is the quiet culprit. On a dedicated monitoring server with 8–16GB RAM, it's fine. On a 1GB node running Prometheus alongside Node Exporter, an application container, and a reverse proxy, it's eating memory you don't have to spare.

> **Key Takeaways**
> - Halving the scrape interval from 30s to 15s roughly doubles in-memory time-series churn, pushing Prometheus memory consumption 40–60% higher on the same target set.
> - On a 1GB VPS with a typical co-located stack, the `15s` default leaves dangerously little headroom — OOM kills become a real risk under cardinality spikes.
> - The practical fix: `30s` globally, `15s` only for SLO-sensitive targets. Per-job overrides handle this cleanly.
> - Prometheus's TSDB head block is where RAM disappears — the per-sample cost is low, but active series count accumulates fast.
> - The 15s vs 30s memory difference on 1GB hardware isn't an academic concern. It determines whether your monitoring stack survives a traffic burst.

---

## Why This Decision Is More Consequential Than It Looks

Most guides tell you to set `scrape_interval` once and forget it. The Prometheus documentation defaults to 1 minute globally, but community convention drifted toward 15 seconds for "better granularity." That drift made sense on dedicated monitoring servers. On a 1GB VPS, it's a different story entirely.

The core mechanic: every scrape cycle, Prometheus pulls all metrics from every configured target and appends them to its in-memory head block. The head block holds roughly 2 hours of data before compaction runs. Shorter intervals mean more samples per active series per hour — which means more memory consumed before that compaction window closes.

According to Palark's engineering analysis of Prometheus resource consumption, memory usage scales non-linearly with active series count and scrape frequency. The relationship between interval and RAM isn't a clean 2:1 ratio, but it's close enough to matter when you're working with 1GB total.

The proliferation of sub-$10/month VPS offerings — Hetzner's CAX11 at €3.29/month as of Q1 2026, Contabo's comparable tiers — has pushed more developers toward self-hosted monitoring instead of paying $20–$50/month for Grafana Cloud or Datadog's entry tier. The constraint isn't the software. It's the iron.

---

## How Prometheus Actually Allocates Memory

Prometheus doesn't store raw text. Every scraped metric gets parsed into a time series — a (labels → samples) structure — and written to the TSDB head block in memory. The head block is a 2-hour rolling window of uncompressed series data.

The formula that matters for capacity planning:

```
Approximate RAM ≈ (active_series × bytes_per_series) + overhead
```

According to the Prometheus documentation and Palark's benchmarks, each active series consumes approximately **3KB–4KB** in the head block under typical workloads. That number stays relatively stable across scrape intervals. What *changes* is how many series Prometheus considers "active."

Shorter scrape intervals don't directly multiply the bytes-per-series cost. But they increase the probability that series which *would* have gone stale at 30s remain active at 15s. And they double the write throughput to the WAL (Write-Ahead Log), which increases background memory pressure during compaction cycles.

Node Exporter alone exposes roughly 800–1,200 metrics by default. At 15s intervals, Prometheus ingests ~4,800–7,200 samples per minute from a single Node Exporter target. At 30s, that drops to 1,600–2,400 samples per minute. The head block delta between those two configs, across a 2-hour compaction window, represents tens of thousands of additional in-memory samples.

According to OneUptime's 2026 analysis of Prometheus scrape interval tuning, reducing scrape frequency is one of the first recommended actions when Prometheus memory exceeds available headroom on single-node deployments. The guidance specifically flags the 15s vs 30s memory usage difference as a commonly overlooked factor in 1GB RAM configurations.

**Cardinality is the real amplifier.** If you're scraping a service that emits high-cardinality labels — user IDs, request paths, trace IDs — halving the interval doubles the rate at which new series enter the head block. On a 1GB VPS, this is where OOM events originate.

---

## The Measured Memory Delta on 1GB Hardware

Exact numbers vary by target count and label cardinality, but the pattern is consistent. Based on Palark's resource consumption benchmarks and OneUptime's tuning data, here's a representative comparison for a minimal single-node setup (Prometheus + Node Exporter + one application target):

| Configuration | Estimated Active Series | Head Block RAM | Total Prometheus RSS | Headroom on 1GB |
|---|---|---|---|---|
| `15s` global interval | ~3,000–5,000 | 90–180MB | 200–350MB | 650–800MB |
| `30s` global interval | ~2,500–4,000 | 60–120MB | 130–250MB | 750–870MB |
| `60s` global interval | ~2,000–3,500 | 45–90MB | 100–200MB | 800–900MB |
| `15s` with high cardinality | ~15,000–30,000 | 500MB–900MB | 700MB–1.1GB | **Critical / OOM risk** |

*Sources: Palark engineering blog (prometheus-resource-consumption-optimization), OneUptime Prometheus tuning guide (2026-02-09)*

The raw difference between `15s` and `30s` in a clean, low-cardinality setup is approximately **60–130MB RSS**. Meaningful, but survivable on 1GB if you're disciplined about co-located services.

The dangerous scenario is that last row. A single misconfigured service pushing high-cardinality labels at 15s can saturate the head block completely. At 30s, that same service gives you twice the time to catch the issue before Prometheus runs out of RAM.

### Where the 60–130MB Actually Goes

The memory breakdown isn't random. Prometheus allocates RAM across several pools:

- **Head block (active series)**: Scales directly with `active_series × ~3KB`
- **WAL buffer**: Scales with write throughput — faster scrapes mean a larger WAL backlog
- **Chunk cache**: Prometheus 2.x caches recently accessed disk chunks for query speed
- **Query engine**: Spikes during alert evaluation or dashboard refreshes

At `15s` intervals, the WAL buffer and head block are both consistently larger. According to Palark's analysis, WAL memory can represent 15–25% of total Prometheus RSS on high-frequency configurations. Dropping to `30s` meaningfully shrinks this pool.

### The Granularity vs. Stability Trade-off

The case for `15s`: twice the resolution for detecting short spikes. A CPU burst lasting 20 seconds is invisible at `30s` if it falls between scrape windows. For SLO monitoring — tracking error rates or latency percentiles with tight burn rate alerts — 15s resolution genuinely matters.

The case for `30s`: on a 1GB VPS, stability beats resolution. A Prometheus process that OOM-kills at 2 AM leaves you with *zero* monitoring data, not degraded monitoring data. Thirty seconds is still fast enough to page on fires.

The practical middle ground is per-job interval overrides. Prometheus lets you set `scrape_interval` globally at 30s and override per-job for the targets that actually need 15s resolution:

```yaml
global:
  scrape_interval: 30s

scrape_configs:
  - job_name: 'node'
    scrape_interval: 30s
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'app_slo_metrics'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8080']
```

This keeps the memory cost of 15s contained to only the targets where the resolution actually earns its overhead.

---

## Three Scenarios, Three Different Answers

**Scenario 1 — Solo developer, personal project**
You're running a side project on a €3–5/month Hetzner or Vultr VPS. Prometheus monitors Node Exporter plus one application. Cardinality is low. At `15s`, you're spending ~200–280MB on Prometheus. At `30s`, that drops to ~130–200MB.

Use `30s` globally. The 60–80MB savings is meaningful padding when a traffic spike temporarily inflates series count. You won't notice the resolution difference on dashboards.

**Scenario 2 — Small team, 3–5 microservices on one node**
Monitoring scope is wider: multiple application targets, Postgres, Redis, NGINX. Active series count climbs to 8,000–15,000. At `15s`, Prometheus RSS can hit 350–500MB. Combined with application containers, you're brushing against the 1GB ceiling regularly.

Set global `scrape_interval: 30s`. Override to `15s` only for the service backing your SLO alerts. Drop Node Exporter to `60s` — system metrics don't need 15s resolution for capacity planning.

**Scenario 3 — High-cardinality metrics**
Any service emitting per-request, per-user, or per-pod labels at `15s` is a memory time bomb on 1GB. According to the OneUptime tuning guide, this is the single most common cause of Prometheus OOM events on small deployments.

Fix the cardinality first. Use `metric_relabel_configs` to drop or hash high-cardinality label values before they reach Prometheus. Interval choice is secondary to cardinality hygiene — in this scenario, dropping to `30s` buys time, but it doesn't fix the underlying problem.

**This approach can fail when** you're running services with legitimately dynamic label spaces that can't be easily aggregated. In those cases, neither interval choice solves the problem — you need a dedicated monitoring node or a managed service.

---

## What to Do Right Now

Check your current Prometheus RSS with `process_resident_memory_bytes` in Grafana. If you're above 300MB on a single-node 1GB deployment, review your active series count with `prometheus_tsdb_head_series` before touching interval settings.

Prometheus 3.x (at 3.1.x as of Q1 2026) introduced improved TSDB head block memory management. The gap between `15s` and `30s` may narrow slightly in future releases. But the fundamental relationship between scrape frequency and active series count won't change — physics doesn't get patched.

The bottom line: on 1GB hardware, `30s` isn't a compromise. It's the right default. Save the 15s resolution for the two or three metrics that actually wake you up at night.

A monitoring stack that survives a traffic burst with degraded resolution beats one that OOM-kills itself and goes completely dark. Every time.

---

*What scrape interval are you running on your current setup — and have you hit memory pressure because of it? The configuration trade-offs shift significantly once you cross the 2GB threshold.*

## References

1. [How to Configure Prometheus Scrape Intervals and Timeout Tuning](https://oneuptime.com/blog/post/2026-02-09-prometheus-scrape-intervals-tuning/view)
2. [Understanding and optimizing resource consumption in Prometheus | Tech blog | Palark](https://palark.com/blog/prometheus-resource-consumption-optimization/)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
