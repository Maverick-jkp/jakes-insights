---
title: "Hetzner VPS Caddy Docker Compose Wildcard Subdomain SaaS Setup"
date: 2026-05-09T20:07:11+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-ai", "hetzner", "vps", "caddy", "Docker"]
description: "Run multi-tenant SaaS on a €4/month Hetzner VPS using Caddy + Docker Compose for automatic HTTPS wildcard subdomains — a pattern powering $50K MRR setups."
image: "/images/20260509-hetzner-vps-caddy-docker-compo.webp"
technologies: ["Docker", "Kubernetes", "AWS", "Go"]
faq:
  - question: "how to set up automatic https wildcard subdomain per tenant saas with caddy docker compose on hetzner vps 2025"
    answer: "The hetzner vps caddy docker compose automatic https wildcard subdomain per tenant saas setup 2025 uses Caddy's DNS-01 ACME challenge combined with the caddy-dns/hetzner module to automatically obtain wildcard TLS certificates from Let's Encrypt. Caddy connects to Hetzner's DNS API to create the required TXT records, eliminating manual certificate management or cron-based renewals. Docker Compose then handles per-tenant container routing using label-based configuration in a single docker-compose.yml file."
  - question: "how many tenants can a hetzner cx22 vps handle with docker compose and caddy"
    answer: "A Hetzner CX22 instance (2 vCPU, 4GB RAM, approximately €3.79/month) can comfortably handle 50–200 concurrent tenants when containers are properly sized. This makes it a cost-effective choice for early to mid-scale SaaS products that don't yet require Kubernetes orchestration. Docker Compose label-based routing is generally sufficient at sub-500-tenant scale."
  - question: "caddy dns-01 challenge hetzner wildcard certificate setup explained"
    answer: "Caddy's DNS-01 challenge works by using the caddy-dns/hetzner module, available on GitHub, to communicate directly with Hetzner's DNS API and automatically create the TXT records that Let's Encrypt requires to validate wildcard domain ownership. This means port 80 does not need to be exposed during certificate issuance, and renewals happen automatically without any manual intervention. The result is a fully managed wildcard certificate for domains like *.yourdomain.com with no Certbot scripts or cron jobs needed."
  - question: "hetzner vps vs aws for multi tenant saas cost comparison 2025"
    answer: "The hetzner vps caddy docker compose automatic https wildcard subdomain per tenant saas setup 2025 approach costs roughly 90% less than an equivalent AWS setup using Application Load Balancer and ACM. AWS ALB plus ACM overhead typically runs $300–$800 per month, while a Hetzner CX22 instance costs under €4 per month. This cost difference makes Hetzner a popular choice for early-stage SaaS products that need production-grade HTTPS and multi-tenant subdomain routing without the cloud overhead."
  - question: "do I need kubernetes for per tenant subdomain routing docker compose enough"
    answer: "For SaaS products with fewer than 500 tenants, Docker Compose is generally sufficient for per-tenant subdomain routing and eliminates the operational complexity of Kubernetes. Docker Compose provides container isolation, health checks, restart policies, and network segmentation from a single configuration file. Kubernetes becomes more justified as tenant count, scaling requirements, or orchestration complexity grows beyond what Compose can efficiently manage."
---

Running a multi-tenant SaaS on a €4/month Hetzner CX22 instance sounds absurd until you realize the infrastructure doing $50K MRR at some shops costs less than a Netflix subscription monthly.

The combination of Hetzner VPS + Caddy + Docker Compose for automatic HTTPS wildcard subdomain per-tenant routing has quietly become one of the most cost-efficient production patterns for early-stage and mid-scale SaaS products in 2025 and into 2026. The approach eliminates the $300–$800/month AWS ALB + ACM overhead that bleeds early-stage products dry.

This piece breaks down exactly how the stack works, what the tradeoffs are versus alternatives, and when this architecture actually holds up under real load.

---

**In brief:** Hetzner VPS with Caddy's DNS-01 challenge and Docker Compose delivers wildcard TLS certificates and per-tenant subdomain routing at roughly 90% lower infrastructure cost than equivalent AWS setups. The `caddy-dns/hetzner` module (maintained on GitHub as of May 2026) makes this a single-file configuration.

Key points:
1. Caddy's automatic HTTPS via DNS-01 challenge supports `*.yourdomain.com` wildcard certificates without manual cert management.
2. Hetzner CX22 (2 vCPU, 4GB RAM) handles 50–200 concurrent tenants comfortably when containers are sized correctly.
3. Docker Compose label-based routing removes the need for Kubernetes at sub-500-tenant scale.

---

## Why This Stack Emerged in 2025

Multi-tenant SaaS subdomain routing used to require either a load balancer with wildcard cert support (expensive) or nginx reverse proxy configs that nobody wanted to maintain by hand. Caddy changed this.

Caddy 2.x introduced the `dns-01` ACME challenge provider system, which lets you get wildcard TLS certs from Let's Encrypt without exposing port 80. The `caddy-dns/hetzner` module (available at `github.com/caddy-dns/hetzner`) connects Caddy directly to Hetzner's DNS API, automating the DNS TXT record creation that Let's Encrypt requires for wildcard validation. No Certbot scripts. No cron jobs. No manual renewals.

Hetzner's infrastructure became the natural pairing. Their CX-series VPS pricing — CX22 at approximately €3.79/month as of early 2026 — makes dedicated tenant infrastructure almost free at sub-100-tenant scale. Combined with their DNS API, you get a closed loop: Caddy requests a cert, Hetzner DNS proves ownership, Let's Encrypt issues the wildcard.

Docker Compose ties it together. For SaaS products that don't yet need Kubernetes orchestration, Compose gives you container isolation per service, health checks, restart policies, and network segmentation — all from one `docker-compose.yml`.

The pattern matured in 2024–2025 as Caddy's DNS provider ecosystem expanded. The OneUptime engineering team documented their wildcard cert setup in February 2026, and `selfhosting.sh` catalogued production Caddy + Docker patterns. Independent deployments confirm this stack handles real traffic.

---

## How the DNS-01 Wildcard Flow Works

The core mechanism is straightforward. Caddy's `Caddyfile` uses the `tls` directive with the `dns hetzner` provider block. On startup, Caddy calls Hetzner's DNS API, creates a `_acme-challenge.yourdomain.com` TXT record, Let's Encrypt validates it, and issues `*.yourdomain.com`.

A minimal `Caddyfile` looks like this:

```
*.yourdomain.com {
    tls {
        dns hetzner {env.HETZNER_API_TOKEN}
    }
    reverse_proxy localhost:3000
}
```

That's it. Caddy handles renewal automatically — no external scheduler, no Certbot, nothing. The `HETZNER_API_TOKEN` is your Hetzner DNS API key passed as an environment variable, which Docker Compose injects cleanly via an `.env` file.

Per-tenant routing happens through Caddy's `host` matcher. Each tenant gets `tenant1.yourdomain.com` resolved by your app's tenant lookup. Caddy doesn't need to know about individual tenants — just the wildcard.

## Docker Compose Structure for Per-Tenant Routing

The typical Docker Compose setup runs Caddy as the front-facing container with other services on an internal network. Caddy's container uses a custom image built with the `caddy-dns/hetzner` module baked in — the standard `caddy:latest` Docker image doesn't include third-party DNS providers.

```yaml
services:
  caddy:
    build: ./caddy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    env_file: .env
    networks:
      - proxy

  app:
    image: your-saas-app:latest
    networks:
      - proxy
    expose:
      - "3000"
```

The `caddy_data` volume persists certificates across container restarts. This is non-negotiable. Without it, Caddy re-requests certs on every restart and hits Let's Encrypt rate limits fast.

## Tenant Isolation Patterns

Wildcard subdomain routing doesn't automatically mean tenant isolation. The SaaS app itself must extract the subdomain from the `Host` header and resolve it to a tenant context. Most frameworks handle this at middleware level.

What Caddy *does* provide is clean per-tenant request logging (using Caddy's `log` directive with `{host}` variables), TLS termination, and optional per-tenant rate limiting via the `rate_limit` module, available separately.

For stricter isolation — separate databases, separate containers per tenant — Docker Compose can run per-tenant app containers. At 10–20 tenants this is manageable. Beyond 50, you'll want dynamic provisioning. That's where this stack starts showing its limits.

## Caddy vs. nginx-proxy vs. Traefik: The Honest Comparison

| Feature | Caddy + Hetzner DNS | nginx-proxy + Certbot | Traefik v3 |
|---|---|---|---|
| Wildcard cert automation | Native, single config | Requires Certbot cron | Supported, more config |
| Hetzner DNS integration | Official module (GitHub) | Manual or scripted | Via Let's Encrypt DNS-01 plugin |
| Config complexity | Low (Caddyfile) | Medium (nginx.conf + scripts) | Medium (labels or TOML) |
| Dynamic tenant routing | Manual host matcher | Manual server blocks | Docker label-based, dynamic |
| Cert renewal | Automatic | Cron-dependent | Automatic |
| Docker Compose integration | Good | Good | Excellent (designed for it) |
| Resource overhead | ~50MB RAM | ~20MB RAM | ~30MB RAM |
| Best for | Simple SaaS, fast setup | Legacy setups | Microservices, dynamic environments |

Traefik's Docker label-based routing is more dynamic — new containers register themselves automatically. But Traefik's wildcard cert setup requires more configuration steps than Caddy's single `dns` block. For a team of one or two shipping fast, Caddy wins on time-to-working.

nginx-proxy with Certbot is the oldest approach and still works. The cron dependency for renewals is the real failure point. When the cron doesn't run — and eventually it won't — tenants hit cert errors. Caddy's renewal is event-driven, not scheduled.

---

## Three Scenarios Worth Thinking Through

**Scenario 1: Early-stage SaaS, under 50 tenants.** This stack is the right call. A Hetzner CX32 (4 vCPU, 8GB RAM, ~€9/month) running Caddy + Docker Compose handles this load without breaking a sweat. Deploy time from zero to HTTPS wildcard subdomain routing: under two hours. The cost delta versus AWS ALB + ACM + EC2 is roughly €150–400/month saved.

**Scenario 2: 50–200 tenants, growing fast.** Still viable, but start planning the exit. Docker Compose doesn't give you zero-downtime rolling updates without manual work. Consider adding a Hetzner Load Balancer (€6.90/month) in front of two VPS nodes for high availability. Caddy's cert storage moves to a shared volume or S3-compatible backend — Hetzner Object Storage works here.

**Scenario 3: 500+ tenants with compliance requirements.** The wildcard cert approach becomes a liability. SOC 2 auditors sometimes flag single wildcard certs covering all tenants. Per-tenant cert issuance at scale requires Caddy's `on_demand_tls` feature — which works, but needs rate limit configuration to avoid hammering Let's Encrypt. At this stage, evaluate whether managed Kubernetes (Hetzner's k3s-based offering or a migration to GKE) makes more sense operationally.

**One rate limit to track before you hit it:** Let's Encrypt currently caps issuance at 50 certs per registered domain per week, per their official documentation. That ceiling becomes relevant the moment you switch from a single wildcard to per-tenant cert issuance. Plan for it early.

---

## Where This Goes Next

The Hetzner VPS + Caddy + Docker Compose pattern isn't a toy. It's a real production architecture that cuts infrastructure overhead for early-to-mid-stage SaaS products by 70–90% compared to equivalent AWS configurations.

The honest ceiling: 200–300 tenants before high availability and dynamic provisioning complexity start outweighing the simplicity benefits. That's not a knock on the stack — it's just the natural graduation point.

Over the next 6–12 months, expect Caddy's on-demand TLS to get better documentation and community tooling, making the 500+ tenant case less painful. Hetzner's continued infrastructure expansion in Europe also means more region options for data residency requirements — relevant if you're serving customers under GDPR with strict data localization needs.

The bottom line: if you're building a multi-tenant SaaS and you're not yet at 200 tenants, this stack deserves serious consideration before you default to AWS and its associated billing surprises. The `caddy-dns/hetzner` module makes wildcard cert automation a single config block, not a DevOps project. Docker Compose is the right abstraction at this scale. And Hetzner's price-to-performance ratio in 2026 remains unmatched among European VPS providers for this specific workload.

Start simple. Scale the complexity when the tenant count actually demands it.

---

> **Key Takeaways**
> - Caddy's `caddy-dns/hetzner` module turns wildcard TLS cert automation into a single configuration block — no Certbot, no cron jobs, no manual renewals.
> - Hetzner CX22/CX32 handles 50–200 concurrent tenants at a fraction of equivalent AWS costs.
> - Docker Compose is the right abstraction under 200 tenants. Kubernetes is premature complexity at that scale.
> - The stack has a real ceiling around 200–300 tenants — plan your HA and dynamic provisioning strategy before you hit it.
> - Let's Encrypt's 50-cert-per-week rate limit matters the moment you move from wildcard to per-tenant cert issuance. Track it early.

---

*References: caddy-dns/hetzner module (github.com/caddy-dns/hetzner); OneUptime Engineering Blog, "How to Run Caddy with Docker and Automatic HTTPS," February 2026 (oneuptime.com); selfhosting.sh Caddy + Docker guide (selfhosting.sh/apps/caddy); Let's Encrypt rate limits documentation (letsencrypt.org/docs/rate-limits).*

## References

1. [GitHub - caddy-dns/hetzner: Caddy module: dns.providers.hetzner · GitHub](https://github.com/caddy-dns/hetzner)
2. [How to Run Caddy with Docker and Automatic HTTPS (Wildcard Certificates)](https://oneuptime.com/blog/post/2026-02-08-how-to-run-caddy-with-docker-and-automatic-https-wildcard-certificates/view)
3. [How to Self-Host Caddy with Docker | selfhosting.sh](https://selfhosting.sh/apps/caddy/)


---

*Photo by [L N](https://unsplash.com/@younis67) on [Unsplash](https://unsplash.com/photos/black-and-white-heidelbeng-machine-PQlS2Xqb0dQ)*
