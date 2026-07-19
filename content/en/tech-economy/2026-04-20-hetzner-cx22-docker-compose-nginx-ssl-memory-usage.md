---
title: "Hetzner CX22 Docker Compose Nginx SSL Setup for Solo Developers"
date: 2026-04-20T20:39:21+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-security", "hetzner", "cx22", "docker", "Node.js"]
description: "Run 12 production services on Hetzner CX22 for under €4/month. Docker Compose, Nginx, and SSL without the AWS markup — memory setup included."
image: "/images/20260420-hetzner-cx22-docker-compose-ng.webp"
technologies: ["Node.js", "Docker", "Kubernetes", "AWS", "PostgreSQL"]
faq:
  - question: "how much memory does nginx ssl use on hetzner cx22 docker compose setup"
    answer: "Nginx as a reverse proxy with Certbot/Let's Encrypt SSL termination uses roughly 30–50MB of RAM, making it negligible in a hetzner cx22 docker compose nginx ssl memory usage solo developer production setup. The real memory concerns are unconfigured database buffers and log accumulation in long-running containers, not the Nginx/SSL layer itself."
  - question: "how many docker containers can run on hetzner cx22 4gb ram"
    answer: "A Hetzner CX22 with 4GB RAM can comfortably run 8–12 lightweight containers when memory limits are explicitly set per service in your Docker Compose configuration. Without explicit memory limits, a single misconfigured database buffer can cause out-of-memory kills, especially overnight when no one is monitoring."
  - question: "is hetzner cx22 good enough for solo developer production setup with docker compose nginx ssl"
    answer: "Yes, the hetzner cx22 docker compose nginx ssl memory usage solo developer production setup is viable and used in real production environments, including publicly documented deployments like Plausible Analytics. The CX22 offers 2 vCPUs, 4GB RAM, and 40GB NVMe SSD for around €3.79/month, which can serve 10–12 production services if memory is managed carefully."
  - question: "why are developers switching from vercel and aws back to hetzner vps"
    answer: "Unpredictable serverless billing on platforms like Vercel, Render, and Railway became a pain point after high-profile billing surprises went viral in late 2024, with modest SaaS apps seeing costs swing between $40–120/month. Hetzner's flat-rate pricing model eliminates that unpredictability, and mature tooling like Docker Compose makes self-hosted production setups accessible without requiring full-time infrastructure management."
  - question: "what causes out of memory errors on hetzner cx22 docker production server"
    answer: "The most common cause of OOM kills on a Hetzner CX22 production server is not application code but unconfigured database buffer settings and log accumulation inside long-running containers. Setting explicit memory limits in your Docker Compose file for each service, especially databases like PostgreSQL, is the primary defense against 2am OOM incidents."
aliases:
  - "/tech/2026-04-20-hetzner-cx22-docker-compose-nginx-ssl-memory-usage/"

---

The Hetzner CX22 runs 12 production services for under €4/month. Most developers still pay 5-10x that on DigitalOcean or AWS for the same workload.

That gap isn't closing. And the tooling around it — Docker Compose, Nginx as a reverse proxy, Let's Encrypt SSL — has matured enough in 2026 that a solo developer can ship a genuinely production-grade stack in an afternoon. But memory management is where most people hit a wall. A CX22 gives you 4GB RAM. Mismanage it and you'll OOM-kill your own database at 2am.

This analysis covers what the numbers actually show about Hetzner CX22 Docker Compose Nginx SSL memory usage for solo developer production setups: what fits, what doesn't, and where the real constraints are.

---

> **In brief:** The Hetzner CX22 offers a compelling price-to-performance ratio for solo developer production stacks, but memory budget discipline is non-negotiable. A well-structured Docker Compose setup with Nginx and SSL termination can serve real production traffic on 4GB RAM — if you measure before you deploy.
>
> 1. The CX22's 4GB RAM ceiling accommodates 8–12 lightweight containers when memory limits are explicitly set per service.
> 2. Nginx as a reverse proxy with Certbot/Let's Encrypt SSL adds roughly 30–50MB overhead, which is negligible at this scale.
> 3. The primary memory risk isn't your app — it's unconfigured database buffers and log accumulation in long-running containers.

---

## Why Developers Are Returning to Bare Metal-Adjacent VPS

The serverless boom peaked around 2023–2024. Vercel, Render, and Railway made deployment frictionless — but the billing got unpredictable fast. A modest SaaS with 10,000 monthly active users could see costs swing $40–120/month depending on cold start patterns and function invocations.

Hetzner's pricing model doesn't do that. The CX22 — 2 vCPUs, 4GB RAM, 40GB NVMe SSD — costs €3.79/month as of April 2026 (Hetzner official pricing page). That's not a promotional rate. It's their standard AMD EPYC-based instance in Falkenstein or Helsinki.

The shift back to predictable VPS hosting accelerated after several high-profile serverless billing surprises went viral on Hacker News in late 2024. Developers started sharing self-hosted setups again. Plausible Analytics documented their own CX22-based deployment publicly, showing a full analytics stack — PostgreSQL, Plausible itself, Nginx, SSL — sitting comfortably under 2GB RAM in steady state.

Docker Compose became the orchestration layer of choice because it's not Kubernetes. No control plane overhead. No etcd cluster. Just a `docker-compose.yml` and `docker compose up -d`. For a solo developer, that's the right abstraction layer — enough structure to be reproducible, not so much that you're managing infrastructure full-time.

---

## Memory Reality Check: What 4GB Actually Buys You

4GB sounds tight. It isn't, if you're intentional.

A typical CX22 Docker Compose Nginx SSL production setup breaks down roughly like this:

| Service | Typical Steady-State RAM |
|---|---|
| Nginx (reverse proxy) | 20–40MB |
| Certbot/Let's Encrypt | ~10MB (periodic) |
| Node.js app (small SaaS) | 150–300MB |
| PostgreSQL (default config) | 300–600MB |
| Redis (default config) | 10–50MB |
| Plausible or similar analytics | 200–400MB |
| Linux OS + Docker daemon | 400–600MB |

Total: roughly 1.1–2.0GB in steady state. That leaves 2GB of headroom — which sounds great until PostgreSQL's `shared_buffers` auto-configures to 25% of system RAM (1GB) and you've quietly eaten your buffer.

The fix: explicitly set `shared_buffers = 128MB` and `work_mem = 4MB` in your `postgresql.conf`. Per Hetzner's community forum discussions and the PostgreSQL documentation, default configs assume a dedicated database server — not a container sharing RAM with six other services.

Memory limits in `docker-compose.yml` aren't optional at this scale:

```yaml
services:
  postgres:
    mem_limit: 512m
    memswap_limit: 512m
```

Without this, one slow query with a bad execution plan can spike PostgreSQL to 1.5GB and cascade into container kills. That's your 2am incident. It's not dramatic — it's just a missing four lines in a config file.

---

## Nginx SSL Termination: The Right Architecture

Nginx as a reverse proxy with Let's Encrypt SSL is the standard pattern for a reason. It handles SSL termination once, at the edge, and passes plain HTTP traffic to upstream containers over the internal Docker network.

The `--volumes-from` approach for Certbot is mostly deprecated now. The cleaner 2026 pattern uses a named volume shared between the Nginx container and a Certbot container that runs on a cron-style schedule:

```yaml
volumes:
  certbot-etc:
  certbot-var:
  webroot:
```

Nginx listens on 443, terminates SSL, proxies to `app:3000` internally. Certbot renews against the webroot. No manual intervention after initial setup.

CPU overhead for SSL termination on a CX22's AMD EPYC vCPUs is negligible — TLS 1.3 hardware acceleration is available, and Nginx handles thousands of concurrent connections well within the CX22's 2 vCPU allocation for typical solo developer traffic volumes (sub-50k daily requests).

This approach can fail when certificate renewal silently errors out — usually because the webroot path in your Nginx config doesn't match the path Certbot is writing to. Set up renewal logging and a basic alerting check before you consider this "done."

---

## CX22 vs. Alternatives: The Honest Comparison

| Criteria | Hetzner CX22 | DigitalOcean Basic (2GB) | Render Starter |
|---|---|---|---|
| Monthly cost | €3.79 (~$4.10) | $12.00 | $7.00/service |
| RAM | 4GB | 2GB | 512MB–2GB |
| NVMe SSD | 40GB | 50GB SSD | Shared |
| Docker Compose support | Native | Native | No (platform-managed) |
| SSL management | Manual (Certbot) | Manual or $1/mo LB | Automatic |
| Network egress pricing | Free (20TB/mo) | $0.01/GB after 1TB | Metered |
| Solo dev production fit | Strong | Adequate | Limited for multi-service |

According to SoloDevStack's 2026 comparison analysis, the CX22 delivers roughly 2.3x the RAM of DigitalOcean's comparable price tier. For a setup running 4–8 services, that headroom difference is meaningful — it's the gap between "runs fine" and "OOMs under load."

DigitalOcean's $12 Droplet at 2GB RAM forces tighter service consolidation or splits services across instances, which adds network complexity. Render's platform-managed containers are easier to deploy but don't support Docker Compose natively — you'd need to restructure your entire stack to migrate.

This isn't always the answer, though. If your priority is zero-ops deployment and you're comfortable with per-service pricing, Render or Railway still make sense. The CX22 setup trades deployment friction for cost efficiency and control. That trade-off only pays off if you're willing to own the infrastructure.

---

## Three Scenarios Worth Planning For

**Scenario 1 — Starting fresh with a side project:** Deploy with a single `docker-compose.yml`. Set explicit memory limits from day one. Use Nginx with Certbot. Don't add Redis until you've proven you need it. Servercompass.app's beginner deployment guide for Hetzner recommends starting with 2–3 services max and measuring baseline RAM before adding anything else. That's the right call.

**Scenario 2 — Migrating an existing app off Render or Railway:** Your stack probably has implicit memory assumptions baked in. Audit each service's actual usage in your current environment first — run `docker stats` for 24 hours, then size limits accordingly. Don't port your `docker-compose.yml` directly. Review every volume mount and health check. Assumptions that were invisible on a managed platform become incidents on a VPS.

**Scenario 3 — Running multiple small apps on one CX22:** This works. A CX22 can host 3–4 separate apps, each behind a different Nginx server block with separate SSL certs, on 4GB RAM — as documented in Plausible's self-hosting write-up. The constraint isn't CPU or RAM. It's disk I/O if multiple PostgreSQL instances are writing simultaneously. Consolidate into one Postgres instance with separate databases.

**When to upgrade:** Hetzner's CX32 (8GB RAM, €5.77/month) is worth moving to once steady-state RAM usage crosses 2.5GB. The price delta is small. The headroom gain is significant.

---

## Where This Goes Next

The CX22 Docker Compose Nginx SSL pattern is more viable in 2026 than it's been at any point in the past five years. Tooling maturity, Hetzner's pricing stability, and Docker Compose's durability as a format have converged into something genuinely practical for solo developers shipping real products.

The core findings hold up under scrutiny:

> - **4GB RAM fits a real production stack** — if PostgreSQL and Redis configs are tuned explicitly, not left at defaults
> - **Nginx SSL termination adds ~30–50MB overhead** — negligible, and the architectural simplicity pays dividends at 2am
> - **CX22 beats comparable DigitalOcean tiers on RAM by ~2x** at lower cost, per SoloDevStack's 2026 data
> - **Memory limits in docker-compose.yml aren't optional** — they're the difference between a stable server and an incident
> - **Silent failures happen** — certificate renewal errors and unchecked log accumulation are the two most common long-running issues

Over the next 6–12 months, expect Hetzner to push ARM-based instances harder — their CAX series already offers better price-per-core for certain workloads. Certbot's `--nginx` plugin is also maturing, which will simplify renewal automation further. The stack will get easier to maintain, not harder.

One concrete action before your next deployment: run `docker stats --no-stream` after 48 hours of production traffic. The numbers will tell you whether you're operating with margin or gambling against an OOM event. That single data point is worth more than any architecture diagram.

## References

1. [Self‑Hosting Plausible Analytics on a Budget Hetzner CX22](https://deducement.com/posts/self-hosting-plausible)
2. [Hetzner vs DigitalOcean for Solo Developers (2026) | SoloDevStack](https://solodevstack.com/blog/hetzner-vs-digitalocean-solo-developers)
3. [Deploy Apps on Hetzner: The Complete Beginner Guide](https://servercompass.app/blog/deploy-apps-hetzner-beginner-guide)


---

*Photo by [Robynne O](https://unsplash.com/@roborobs) on [Unsplash](https://unsplash.com/photos/a-group-of-people-standing-next-to-each-other-HOrhCnQsxnQ)*
