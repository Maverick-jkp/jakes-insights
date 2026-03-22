---
title: "Prometheus Grafana Docker Compose OOM Tuning on 2GB RAM VPS"
date: 2026-03-22T19:49:58+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "prometheus", "grafana", "docker", "Kubernetes"]
description: "Running Prometheus and Grafana on a 2GB RAM VPS without tuning invites the OOM killer. Here's how to configure your Docker Compose stack to survive."
image: "/images/20260322-prometheus-grafana-docker-comp.webp"
technologies: ["Docker", "Kubernetes", "Linux", "Go", "Ollama"]
faq:
  - question: "why does prometheus grafana docker compose on 2gb ram vps keep getting oom killed"
    answer: "A default Prometheus deployment can consume 800MB–1.2GB RAM on its own, leaving almost no headroom on a 2GB VPS before the Linux OOM killer terminates processes. Without explicit Docker Compose memory limits, containers inherit the host's full address space and become prime targets when the system is under pressure. The issue is often a slow memory creep over days or weeks rather than a sudden spike, making it easy to miss without proper alerting."
  - question: "how to set memory limits for prometheus and grafana in docker compose"
    answer: "In your docker-compose.yml, you can enforce hard memory ceilings per container using the `mem_limit` and `memswap_limit` directives, which prevent any single service from consuming all available host memory. This is one of the most important steps in prometheus grafana docker compose 2gb ram vps memory oom killed tuning, as default deployments apply no resource constraints at all. Setting these limits ensures that even if one container leaks memory, it cannot take down the entire host."
  - question: "how to reduce prometheus memory usage on a small vps"
    answer: "The biggest lever for reducing Prometheus memory usage is lowering the TSDB retention period using the `--storage.tsdb.retention.time` and `--storage.tsdb.retention.size` startup flags, since the default 15-day retention is often 4–5 times more than a small VPS needs. Reducing the number of scrape targets and increasing the scrape interval from 15 seconds to 30 or 60 seconds also significantly cuts memory load. These tuning steps are essential for prometheus grafana docker compose 2gb ram vps memory oom killed tuning scenarios."
  - question: "how much ram does prometheus use by default"
    answer: "A default Prometheus deployment typically consumes between 800MB and 1.2GB of RAM on its own, depending on the number of scrape targets and the retention period configured. This is because Prometheus loads its entire TSDB index into memory and defaults to keeping 15 days of metrics data. On a 2GB VPS also running Grafana and other services, this leaves almost no memory headroom before the Linux OOM killer fires."
  - question: "how to stop grafana from using too much memory in docker"
    answer: "Grafana's memory footprint is primarily driven by the number of concurrent dashboard queries and installed plugins, both of which can be controlled through environment variables in your Docker Compose file. Reducing the number of active dashboards, limiting concurrent users, and removing unused plugins are the most effective steps to lower Grafana's RAM consumption. Combining these changes with hard `mem_limit` values in Docker Compose prevents Grafana from contributing to OOM kill events on memory-constrained servers."
---

The OOM killer doesn't care about your uptime targets. One morning your monitoring stack is gone — containers dead, logs full of `Killed` entries, and your entire observability pipeline offline on the machine that's supposed to be watching everything else.

This is what happens when you deploy a default Prometheus + Grafana stack on a 2GB RAM VPS without tuning a single parameter. It's more common than most ops teams admit, and the fix is more precise than "just add more RAM."

> **Key Takeaways**
> - A default Prometheus deployment can consume 800MB–1.2GB RAM on its own, leaving almost no headroom on a 2GB VPS before the Linux OOM killer fires.
> - Docker Compose's `mem_limit` and `memswap_limit` directives enforce hard memory ceilings per container, preventing one service from consuming all available host memory.
> - Prometheus's `--storage.tsdb.retention.time` and `--storage.tsdb.retention.size` flags are the single biggest levers for memory reduction — default retention of 15 days is often 4–5x more than a small VPS needs.
> - Grafana's memory footprint is largely driven by concurrent dashboard queries and plugin count, both controllable through environment variables in Compose.
> - Memory tuning on a constrained VPS is not a one-time fix — it requires ongoing alerting on container memory usage trends.

---

## Why 2GB VPS Deployments Keep Getting OOM-Killed

The popularity of $6–$12/month VPS instances — DigitalOcean Droplets, Hetzner CX22, Vultr Cloud Compute — has pushed monitoring stacks onto machines that weren't designed for them. Prometheus was built at Google-scale. Its defaults reflect that heritage.

By default, Prometheus loads its entire TSDB index into memory and keeps 15 days of metrics. On a lightly scraped instance with 10–20 targets, that's manageable. Add a Node Exporter scraping every 15 seconds, a cAdvisor watching your Docker containers, and Grafana running three dashboards — and resident memory climbs fast.

The Grafana Alloy team documented exactly this pattern in a 2024 GitHub issue (grafana/alloy#3447): memory grew steadily over two weeks before OOM termination. No sudden spike. Just a slow leak that the default monitoring setup never flagged until the process was dead.

Linux's OOM killer prioritizes processes with high `oom_score`. Docker containers without memory limits inherit the host's full address space, making them prime targets when the system is under pressure. The kernel doesn't warn you — it just kills.

Two converging trends make this urgent in 2026. First, the cost-optimization wave across engineering teams has pushed more workloads onto smaller instances. Second, the observability-as-standard movement means more teams are deploying Prometheus + Grafana stacks for the first time, often copy-pasting Compose files without reading the resource implications.

---

## Setting Hard Limits in Docker Compose

The first line of defense is explicit memory limits in your `docker-compose.yml`. Without them, Docker will let each container consume available host RAM until the OOM killer intervenes.

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.51.0
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
    command:
      - '--storage.tsdb.retention.time=7d'
      - '--storage.tsdb.retention.size=400MB'
      - '--storage.tsdb.wal-compression'

  grafana:
    image: grafana/grafana:10.4.0
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
    environment:
      - GF_RENDERING_SERVER_URL=""
      - GF_PLUGINS_ENABLE_ALPHA=false
```

According to the Docker Compose resource limits documentation, the `deploy.resources.limits.memory` key enforces a hard ceiling using Linux cgroups. When a container hits that ceiling, it receives SIGKILL rather than starving the host. That's the behavior you want — a dead container is recoverable; a dead host is not.

One critical detail: `memswap_limit` defaults to 2x the memory limit if not set explicitly. On a VPS with a small swap partition, this can still cause problems. Set `memswap_limit` equal to `memory` to disable swap use for containers you want to keep fast.

---

## Prometheus TSDB Tuning: The Biggest Win

The `--storage.tsdb.retention.time=15d` default is the primary memory driver on small deployments. Each day of retention adds roughly 30–80MB of RAM depending on cardinality. Cutting retention from 15 days to 7 days can drop Prometheus's resident memory by 40–50%.

The `--storage.tsdb.retention.size=400MB` flag adds a size-based ceiling as a secondary guard. Prometheus honors whichever limit is hit first. Combining both gives you predictable, bounded storage behavior.

WAL compression (`--storage.tsdb.wal-compression`) reduces write-ahead log disk usage by roughly 40% according to Prometheus's changelog for v2.11+, which also reduces the memory needed for WAL block management.

For cardinality control — the other major memory driver — audit your metrics with:

```
topk(20, count by (__name__)({__name__=~".+"}))
```

High-cardinality metrics from Kubernetes labels or per-request tracing are the usual culprits. Dropping them at the scrape level with `metric_relabel_configs` keeps memory flat over time.

---

## Grafana Memory Management

Grafana's footprint is smaller than Prometheus's but still significant. A fresh instance idles around 80–120MB. Add the image renderer plugin and that jumps to 250MB or more.

For a 2GB VPS, disable the renderer entirely and use Grafana's built-in PNG export. Set `GF_RENDERING_SERVER_URL=""` in your Compose environment block. Limit the number of concurrent dashboard queries with `GF_SERVER_ROUTER_LOGGING=false` and keep your dashboard count under 10 on constrained hardware.

The production Ollama monitoring setup documented at markaicode.com shows a practical pattern worth following: scope each Grafana data source to query only what's needed, set query time ranges to 1–3 hours by default, and avoid auto-refresh intervals below 30 seconds. Those three changes alone reduce Grafana's memory pressure by 30–40% under load.

This approach can fail when teams inherit large dashboard libraries from previous engineers — dozens of panels, each with wide time ranges and aggressive refresh rates. Auditing and pruning dashboards is unglamorous work, but it's often more impactful than any configuration change.

---

## Memory Profiles Across Common Configurations

| Configuration | Prometheus RAM | Grafana RAM | Total Stack | OOM Risk on 2GB VPS |
|---|---|---|---|---|
| Default (no limits, 15d retention) | 900MB–1.2GB | 200–350MB | 1.1–1.55GB | High |
| Limits only (no TSDB tuning) | 512MB cap | 256MB cap | ~770MB | Medium (swap risk) |
| Limits + 7d retention + WAL compression | 300–450MB | 150–200MB | ~650MB | Low |
| Limits + 7d retention + no renderer | 300–450MB | 80–120MB | ~500MB | Very Low |
| VictoriaMetrics swap-in (vs Prometheus) | 150–250MB | 80–120MB | ~370MB | Minimal |

VictoriaMetrics deserves a direct mention here. It's a Prometheus-compatible TSDB that typically uses 5–10x less RAM than Prometheus for equivalent workloads, according to VictoriaMetrics's own published benchmarks. For teams committed to staying on 2GB hardware long-term, swapping Prometheus for VictoriaMetrics single-node is worth the migration cost. The Grafana integration is identical — same dashboards, same PromQL queries. The tradeoff is operational familiarity: Prometheus has a larger community and more third-party tooling, so teams less comfortable with newer stacks may find the migration friction outweighs the memory savings.

---

## Three Practical Scenarios

**Scenario 1 — Already getting OOM-killed.** Stop the stack. Add memory limits and cut retention to 5 days immediately. Restart. This buys stability while you tune properly. Don't reach for swap as your primary fix — swap on a cloud VPS is slow NVMe, and Prometheus's random-access TSDB patterns perform terribly on it.

**Scenario 2 — Planning a fresh deployment.** Start with the tuned Compose file above. Add a Prometheus alert that fires when container memory exceeds 80% of its limit for 10 consecutive minutes. The tuning problem is 90% prevention — the alert catches slow leaks like the Grafana Alloy issue before they become outages.

**Scenario 3 — Need more metrics coverage but can't upgrade the VPS.** Shard your scrape targets. Run a second, cheaper scraper for low-priority metrics with longer scrape intervals (60 seconds instead of 15). Reducing scrape frequency for non-critical targets cuts TSDB ingestion rate and memory growth linearly.

**What to watch over the next 3–6 months:** Prometheus 3.x's native histograms reduce cardinality for histogram-heavy workloads by 5–10x in early benchmarks. If your memory pressure is histogram-driven, the upgrade path from 2.x to 3.x could be more impactful than any individual tuning change.

---

## Where This Leaves You

The solution set here isn't glamorous. But it works:

- **Hard memory limits in Compose** prevent host-level OOM events
- **7-day retention + WAL compression** cuts Prometheus RAM by 40–50%
- **Renderer removal + query scoping** keeps Grafana under 150MB
- **Cardinality auditing** catches slow leaks before they kill the process

Over the next 6–12 months, expect Prometheus 3.x adoption to accelerate as native histograms mature. VictoriaMetrics will continue gaining ground on memory-constrained deployments. Docker's resource limit APIs are stable and unlikely to change, so the Compose patterns above will remain valid regardless of which direction the ecosystem moves.

The real mindset shift is treating your monitoring stack as a production service with memory budgets — not a debug tool you stand up and forget. Most OOM events on small VPS deployments aren't hardware failures. They're configuration defaults that were never meant for this environment. What's your current Prometheus retention setting, and when did you last check?

## References

1. [alloy:v1.0.0 OOM .The memory continuously grew for two weeks, and then a memory overflow occurred. ·](https://github.com/grafana/alloy/issues/3447)
2. [CPU and Memory Limits in Docker Compose - Docker Compose Guide | Docker Recipes](https://docker.recipes/docs/resource-limits)
3. [Deploying Ollama as a Production API Server: Docker, Load Balancing, and Monitoring | Markaicode](https://markaicode.com/ollama-production-api-server/)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
