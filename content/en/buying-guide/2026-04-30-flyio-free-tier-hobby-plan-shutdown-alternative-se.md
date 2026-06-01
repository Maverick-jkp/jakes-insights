---
title: "Fly.io Free Tier Is Gone: Is Self-Hosting on Hetzner Worth It?"
date: 2026-04-30T20:47:01+0900
draft: false
author: "Jake Park"
categories: ["buying-guide"]
tags: ["subtopic-web", "fly.io", "free", "tier", "Docker"]
description: "Fly.io killed its free tier in 2024. Here's what migration to self-hosted Coolify on Hetzner actually costs compared to staying in managed cloud."
image: "/images/20260430-flyio-free-tier-hobby-plan-shu.webp"
technologies: ["Docker", "AWS", "GCP", "Go"]
faq:
  - question: "what happened to fly.io free tier and what are the alternatives"
    answer: "Fly.io removed its free tier entirely in late 2024, requiring all users to have a valid credit card and pay for compute resources. The Fly.io free tier hobby plan shutdown pushed many developers toward self-hosted alternatives like Coolify on Hetzner, which can cost as little as €3.29–€4.35/month compared to Fly.io's $10–15/month for comparable machines."
  - question: "fly.io free tier hobby plan shutdown alternative self-host coolify hetzner actual migration cost"
    answer: "Migrating from Fly.io to a self-hosted Coolify setup on Hetzner can significantly reduce compute costs, but experienced engineers report spending 4–8 hours on a production-ready configuration. The actual migration cost depends heavily on how you value your time, since the infrastructure savings are real but the setup overhead is not trivial."
  - question: "how much does it cost to self-host apps on hetzner instead of fly.io"
    answer: "A Hetzner CX22 instance with 2 vCPU and 4 GB RAM costs approximately €4.35/month as of 2026, while a comparable Fly.io shared-cpu-2x machine runs roughly $10–15/month. Running three or four hobby apps on Hetzner with Coolify can cost less than a single app on Fly.io's paid plans."
  - question: "is coolify a good fly.io alternative for hobby projects"
    answer: "Coolify is a leading open-source self-hosting platform that can replicate most Fly.io workflows, making it a popular choice following the Fly.io free tier hobby plan shutdown. However, it requires meaningful upfront setup time and ongoing maintenance, so it works best for developers comfortable managing their own infrastructure."
  - question: "fly.io vs self-hosting which is cheaper for small apps"
    answer: "For developers running multiple small apps, self-hosting on a provider like Hetzner is significantly cheaper at scale, while Fly.io wins on operational simplicity since it handles infrastructure management for you. Fly.io's paid entry point starts around $5/month per machine, meaning three to four hobby apps can easily reach $15–25/month, whereas a single Hetzner server can host all of them for under €5/month."
---

Fly.io killed its free tier in late 2024. No soft landing, no grandfathered plans — just a billing requirement and a deadline. For thousands of developers running hobby projects and early-stage apps, that decision forced a real question: pay up, or figure something else out.

The timing matters. Cloud costs have been under a microscope since 2023, and by April 2026, the "just throw it on a managed platform" default is getting harder to justify. Fly.io's paid entry point starts around $5/month for the smallest `shared-cpu-1x` machines — not catastrophic, but when you're running three or four hobby apps, it compounds fast.

The real question isn't whether Fly.io is "worth it." It's whether the math works out in your favor once you count everything: setup time, maintenance overhead, downtime risk, and actual compute pricing.

> **Key Takeaways**
> - Fly.io's removal of its free tier in late 2024 pushed a significant share of hobby developers toward self-hosted alternatives on providers like Hetzner.
> - A Hetzner CX22 instance (2 vCPU, 4 GB RAM) costs approximately €4.35/month as of April 2026, versus Fly.io's comparable `shared-cpu-2x` 1 GB RAM machine at roughly $10–15/month.
> - Coolify, the leading open-source self-hosting platform, can replicate most Fly.io workflows — but carries a real setup cost: experienced engineers report 4–8 hours for a production-ready configuration.
> - The true migration cost depends heavily on how much you value your time, not just compute prices.
> - Managed platforms win on operational simplicity. Self-hosting wins on cost at scale.

---

## How the Free Tier Disappeared

Fly.io launched in 2020 with a generous free tier — three shared VMs, 160 GB outbound transfer, and a small Postgres allowance. That attracted a specific kind of user: developers who wanted Heroku-like simplicity without the Heroku price tag, especially after Heroku ended its own free tier in November 2022.

The cascade was predictable. Heroku's free tier dies → developers flood to Fly.io, Railway, Render, and similar platforms → those platforms absorb enormous infrastructure cost from non-paying users → free tiers get quietly renegotiated or killed.

Fly.io started restricting its free allowances through 2023–2024, eventually requiring a valid credit card and removing the no-cost baseline entirely. By Q1 2025, any app on Fly.io was generating a bill. Keeping three small apps alive runs roughly $15–25/month depending on memory and CPU configuration, according to Fly.io's published pricing page.

Meanwhile, Hetzner — a German cloud provider with data centers in Falkenstein, Nuremberg, Helsinki, and (since 2023) Ashburn, Virginia — had been quietly building out its Cloud product. As of April 2026, their cheapest ARM-based CX22 machine runs €4.35/month. Their CAX11 ARM instance (2 vCPU, 4 GB RAM) costs €3.29/month. These aren't promotional rates — they're standard pricing, consistently cheaper than AWS, GCP, or managed PaaS platforms at comparable specs.

That price gap is exactly why "Hetzner + Coolify" became the dominant migration recommendation across r/selfhosted, r/Hosting, and the indie hacker community through 2025.

---

## The Actual Compute Cost Gap

Price out a typical hobby stack on Fly.io's calculator: one web app (512 MB RAM, shared CPU), one background worker, one small Postgres instance. You're looking at $20–30/month minimum, before bandwidth overages.

The same workload on a Hetzner CX22 at €4.35/month fits everything on a single VPS with headroom to spare. Hetzner includes 20 TB of outbound traffic per month at that tier — essentially unlimited for a hobby project. According to getdeploying.com's Fly.io vs Hetzner comparison, Hetzner wins on raw price for equivalent compute in almost every configuration.

That's a real delta. Over 12 months, you're looking at $240–360/year on Fly.io versus roughly $52–60/year on Hetzner.

---

## Coolify: What You're Actually Getting

Coolify is an open-source, self-hosted Heroku/Netlify alternative. Version 4 — the current stable branch as of 2026 — supports Docker deployments, Git-based CI/CD, SSL via Let's Encrypt, reverse proxy via Caddy, and a built-in database management UI. It's the closest thing to a full PaaS you can run on your own box.

Setup isn't trivial, but it's not brutal either. The official one-line installer works on a fresh Debian or Ubuntu VPS. First-time configuration — SSH keys, Git provider connection, domain setup, first app deployment — takes 2–4 hours if you know what you're doing. If you're newer to VPS management, budget 6–8 hours and expect at least one "why isn't SSL working" moment.

Ongoing maintenance is the honest cost that migration guides skip. Monthly, you're realistically looking at:

- Coolify updates (15–30 minutes, mostly automated)
- OS security patches (`apt upgrade`, 10 minutes)
- Backup verification (if you've set it up properly)
- Occasional debugging when Docker networking does something unexpected

Call it 1–2 hours/month. At a $100/hour developer rate, that's $100–200/month in time cost — which immediately flips the math against self-hosting for many people. This is the number the "just use Hetzner" crowd consistently undersells.

---

## When Self-Hosting Actually Wins

The math flips positive under specific conditions.

**Multiple apps, single server.** Running 5+ projects? A single Hetzner CX32 (€8.39/month, 4 vCPU, 8 GB RAM) handles all of them under Coolify. Fly.io bills per-app. The more you consolidate, the better self-hosting looks.

**Database costs.** Fly.io's managed Postgres starts low but scales quickly to $15–30/month for anything with real storage needs. On Hetzner, Postgres runs on your VPS at no additional cost. For data-heavy side projects, this alone can justify the migration.

**Bandwidth-heavy workloads.** Fly.io charges $0.02/GB for outbound transfer beyond the free allowance. Hetzner's 20 TB/month included transfer covers virtually all hobby use cases at no extra charge.

This approach can fail when you're running a single app, have limited VPS experience, or can't afford 2am debugging sessions on a production issue. Operational simplicity has real value — and it's easy to underestimate until something breaks.

---

## Fly.io vs Hetzner + Coolify vs Railway

| Criteria | Fly.io | Hetzner + Coolify | Railway |
|---|---|---|---|
| Entry price (1 app) | ~$5–10/month | €4.35/month (shared) | $5/month (Hobby plan) |
| 5 apps, 1 DB | ~$25–40/month | €4.35–8.39/month | $20–40/month |
| Outbound transfer | $0.02/GB over limit | 20 TB included | 100 GB included |
| Setup complexity | Low (PaaS) | Medium (4–8 hrs) | Low (PaaS) |
| Maintenance overhead | None | 1–2 hrs/month | None |
| Deploy from Git | Yes | Yes (via Coolify) | Yes |
| Global edge | Yes (30+ regions) | Limited (5 regions) | Limited |
| Managed Postgres | Yes ($) | DIY (included in VPS) | Yes ($) |
| Best for | Single apps, latency-sensitive | 3+ apps, cost-focused | Simple deploys, small teams |

Railway deserves a mention. It kept a scaled-down free tier through 2025, and its Hobby plan at $5/month is genuinely competitive for single-app deployments. For developers who want PaaS convenience without Fly.io's full pricing, it's worth evaluating alongside the self-hosting path.

The trade-off is sharp. Fly.io and Railway charge for convenience. Hetzner + Coolify charges in time. Neither is universally correct — the right choice depends on your app count, technical comfort level, and whether your time has a dollar value you're willing to assign to infrastructure work.

---

## Three Scenarios Worth Thinking Through

**Scenario 1: Solo developer, 1–2 hobby apps, low traffic.**
Fly.io's paid tier at $10–15/month is probably the right answer. The setup cost of Hetzner + Coolify doesn't recover over 12 months if you're only running one or two apps. Railway is also worth checking — simpler billing, comparable pricing.

**Scenario 2: Solo developer, 4–8 projects, tight budget.**
This is the Coolify sweet spot. One Hetzner CX32 at €8.39/month handles everything. The first-month setup cost in time is real, but by month 3–4, you're ahead. The math becomes firmly positive here.

**Scenario 3: Small startup, early-stage product.**
Don't self-host your primary product on a €4/month VPS. Operational simplicity and reliability matter more than $100/year in savings when something breaks at 2am. Fly.io, Railway, or Render make more sense until you have dedicated ops capacity.

A few things worth tracking over the next six months: Fly.io has been expanding its GPU and machine learning infrastructure, and pricing changes there could ripple into the broader platform cost structure. Coolify 5 is in active development as of Q1 2026, with multi-server clustering support that would meaningfully change the scalability equation. And Hetzner's US East (Ashburn) region is still relatively new — latency benchmarks for North American workloads are improving, but not yet at parity with US-native providers.

---

## The Bottom Line

The Fly.io free tier shutdown forced a decision many developers had been avoiding: what does your infrastructure actually cost, and is the convenience worth it?

The data points in a few clear directions. Compute cost advantage firmly favors Hetzner + Coolify for developers running three or more projects. Single-app convenience still favors managed PaaS — the setup overhead doesn't amortize fast enough. The actual migration cost includes 4–8 hours of setup time and 1–2 hours of monthly maintenance, which most migration guides quietly ignore. And Railway remains a credible middle ground for developers who want simplicity without full Fly.io pricing.

Over the next 12 months, expect more PaaS providers to tighten or eliminate free tiers. The economics of subsidizing non-paying infrastructure users haven't improved. Coolify's continued development and Hetzner's aggressive pricing will keep the self-hosting path viable — but it's not free, even when the monthly bill says €4.35.

If you're running more than three apps and can spare a weekend afternoon to set things up, the math works out clearly in favor of Hetzner. Otherwise, pay the $10/month and ship things instead.

Your current stack probably says as much about your time constraints as it does about your budget.

## References

1. [Fly.io vs Hetzner](https://getdeploying.com/flyio-vs-hetzner)
2. [r/Hosting on Reddit: Scaleway vs OVHcloud vs Fly.io vs Hetzner for microservices (solo dev)](https://www.reddit.com/r/Hosting/comments/1rs81z6/scaleway_vs_ovhcloud_vs_flyio_vs_hetzner_for/)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
