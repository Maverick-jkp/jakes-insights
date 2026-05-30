---
title: "Fly.io Free Tier: Actual Monthly Bill for a Solo Side Project"
date: 2026-05-30T20:37:54+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-devtools", "fly.io", "free", "tier", "Python"]
description: "Fly.io free tier hides real costs. See the exact 2025 monthly bill breakdown for a solo dev side project once real traffic hits your machines."
image: "/images/20260530-flyio-free-tier-single-develop.webp"
technologies: ["Python", "Next.js", "Node.js", "Go"]
faq:
  - question: "fly.io free tier single developer side project actual monthly bill breakdown 2025"
    answer: "A solo developer running a typical web app on Fly.io should expect to pay $15–25/month in 2025–2026, not zero, despite the free tier allowances. The biggest surprise charges come from persistent volumes, egress bandwidth, and IPv4 addresses, none of which are fully covered after Fly.io restructured its pricing in late 2024."
  - question: "does fly.io free tier actually cost nothing for a side project"
    answer: "Fly.io's free tier covers roughly $5–7 of compute per month, but most side projects exceed this within 60–90 days of launch. Once you add persistent storage, a public IPv4 address ($2/month each), and moderate traffic, the bill grows quickly beyond zero."
  - question: "what are the hidden costs on fly.io for a small app"
    answer: "The three most common surprise charges on Fly.io are persistent volumes billed at $0.15/GB/month beyond the free 3GB, outbound bandwidth beyond 160GB, and static IPv4 addresses at $2/month per app. Many developers only discover these costs after their first billing cycle when running a real side project."
  - question: "fly.io vs railway vs render pricing for solo developer 2025"
    answer: "Based on a fly.io free tier single developer side project actual monthly bill breakdown 2025 analysis, Fly.io typically costs $15–25/month for a realistic stack while Railway and Render offer more predictable flat-rate pricing. However, Fly.io's edge deployment model and infrastructure density make it technically superior for latency-sensitive workloads despite the less predictable billing."
  - question: "how does fly.io free tier work across multiple projects same account"
    answer: "Fly.io's free allowances are shared across your entire organization, not allocated per project or per repository. If you run two or three side projects under one account, they all split the same pool of free compute hours, storage, and bandwidth, meaning multi-project developers exhaust the free tier much faster than expected."
---

Most developers assume "free tier" means zero dollars. Fly.io's pricing structure makes that assumption expensive.

The platform's free allowances look generous on paper — shared CPUs, 256MB RAM machines, 3GB storage. But once you push past the defaults and start running anything resembling real traffic, the actual monthly bill tells a different story.

This breakdown covers exactly what you'll pay, where the surprises hide, and how Fly.io stacks up against alternatives in 2026.

> **Key Takeaways**
> - Fly.io's free tier covers roughly $5–7 of compute per month, but most side projects exceed this within 60–90 days of launch.
> - The three biggest surprise charges are persistent volumes, egress bandwidth, and IPv4 addresses — none covered by free allowances after Fly.io restructured pricing in late 2024.
> - A solo developer running a typical web app (Node.js or Python backend, Postgres database, low-to-moderate traffic) should budget $15–25/month in 2026, not zero.
> - Alternatives like Railway and Render offer more predictable flat-rate pricing, but Fly.io's infrastructure density and edge deployment model remain technically superior for latency-sensitive workloads.
> - Your actual bill varies significantly depending on whether you're running always-on machines or machines that scale to zero.

---

## What Fly.io's Free Tier Actually Covers in 2026

Fly.io's cost management documentation lists a monthly free allowance that resets each billing cycle. As of May 2026, that includes:

- **3 shared-CPU-1x machines** with 256MB RAM (up to 2,160 combined hours)
- **3GB persistent storage** across all volumes
- **160GB outbound data transfer**
- **Shared IPv6** addressing (IPv4 costs $2/month per static IP)

That sounds workable. A small Express.js API or a hobby Postgres instance fits inside those limits. The problem is what *isn't* covered.

Persistent volumes beyond 3GB bill at $0.15/GB/month. Dedicated CPU machines — which you'll want the moment you're running background workers or anything CPU-bound — aren't in the free tier at all. And that $2/month IPv4 charge applies per app that needs a routable public IP, which covers most apps not sitting behind a proxy.

One detail buried in the documentation: free allowances are shared across your organization, not per project. If you've got two or three side projects under one account, you're splitting those compute hours. You don't get a fresh allocation for each repo.

---

## The Actual Bill: A Realistic Side Project Scenario

Take a common 2026 side project stack: a Next.js app, a Node.js API server, and a managed Postgres database on Fly.io. This is exactly the kind of setup where the numbers get concrete fast.

### Compute Costs

Running two `shared-cpu-1x, 256mb` machines (frontend + API) continuously consumes roughly 1,440 hours each per month. That's 2,880 hours total — already consuming the entire free allowance. Add a third machine for a database proxy or background worker and you're paying for overage.

Each additional shared-CPU machine runs approximately **$1.94/month** if it scales to zero overnight. Always-on? Closer to **$5.70/month** per machine.

### Storage and Database

A Fly Postgres cluster with a 10GB volume — realistic for any app storing user data — costs:
- 3GB free, 7GB billed at $0.15/GB = **$1.05/month**
- Plus the Postgres machine itself, which counts against your compute allowance

### Networking

The 160GB free egress covers moderate traffic. But serving images, assets, or API responses to a few hundred daily active users can push you past that threshold. Bandwidth above the free tier runs **$0.02/GB**. The IPv4 charge is effectively unavoidable for most apps: **$2.00/month**.

### Real Monthly Total

| Cost Item | Monthly Estimate |
|-----------|-----------------|
| Compute (2 always-on shared machines) | $11.40 |
| Extra compute (worker machine, scaled to zero) | $1.94 |
| Postgres volume storage (7GB overage) | $1.05 |
| Static IPv4 address | $2.00 |
| Egress bandwidth (within free tier) | $0.00 |
| **Total** | **~$16.39** |

That's a realistic floor. Add a second IPv4, a larger database, or a dedicated CPU machine and you're at $25–35/month fast.

This approach can also fail quietly — if a traffic spike hits while you haven't set a billing cap, Fly.io will keep scaling and keep charging. The dashboard supports hard spending limits. Use them.

---

## Fly.io vs. Alternatives: Where the Math Changes

| Platform | Free Compute | Database Included | Predictable Pricing | Edge Deployment |
|----------|-------------|-------------------|--------------------|--------------| 
| Fly.io | 3 shared machines | No (separate cluster) | No (usage-based) | Yes (30+ regions) |
| Railway | $5 credit/month | Postgres included | Yes (flat plans) | No |
| Render | 750 hrs free/month | 90-day free Postgres | Yes (flat plans) | Limited |
| Hetzner VPS | N/A | Self-managed | Yes (flat) | No |

Railway's Hobby plan starts at $5/month and includes Postgres. It's simpler to reason about financially. According to SaasPricePulse's 2026 analysis of Fly.io's tier structure, the absence of a predictable flat-rate option remains the top complaint among solo developers — not the price itself, but the unpredictability.

Render's free tier comes with a different penalty: services suspend after 15 minutes of inactivity. That cold-start delay makes it impractical for any app where consistent response time matters.

Fly.io's technical edge is real and not trivial. Sub-20ms latency from 30+ global regions, machine startup times under 2 seconds for most workloads, genuine Anycast networking. For a latency-sensitive side project with international users, that infrastructure density is hard to match at any price point. But it's not the right trade-off for every project — an internal tool or low-traffic MVP doesn't need edge deployment, and Railway's flat pricing will serve it better.

---

## What to Do With This Information

**Pre-launch or early experimentation?** Fly.io's free tier genuinely works. Two machines, no custom domain requiring IPv4, Postgres under 3GB — you can stay in the free zone for months without careful management.

**Past early traction?** Budget $15–20/month and treat it as a real infrastructure line item. Set a hard spending limit inside the billing dashboard before you need it, not after a surprise invoice forces the conversation.

**Predictability matters more than edge performance?** Railway's flat pricing or a Hetzner VPS ($4–6/month for a CX22) gives you a fixed monthly number. You lose the global edge network. Most side projects don't need it, and the mental overhead of usage-based billing adds up over time in ways that don't show on invoices.

Fly.io has also signaled a potential developer plan tier in Q3 2026 that would bundle compute, storage, and one IPv4 address at a flat monthly rate. If that ships, it changes the calculation above materially. If it doesn't, expect solo developers to keep drifting toward simpler pricing models.

---

## The Bottom Line

The actual monthly bill for a solo developer on Fly.io lands between $0 and $35 depending on usage — with most realistic, actively-used apps settling around $15–20/month.

The free tier is real, but it's scoped to roughly three always-on machines before charges start. IPv4 addresses and persistent storage are the two costs that catch developers off guard most consistently. Fly.io's infrastructure justifies the cost for latency-sensitive workloads. For everything else, Railway and Hetzner offer better pricing predictability, if not better infrastructure.

The next six months will clarify whether Fly.io closes that gap with a flat developer plan. Until then, the honest answer to "is Fly.io free?" is: not once your project is actually running.

What's your Fly.io bill at right now? Drop the number in the comments — real data helps everyone plan better.

## References

1. [7 Fly.io Alternatives in 2026: Real Pricing After the Free Tier Died - ExpressTech](https://expresstech.io/7-fly-io-alternatives-in-2026-real-pricing-after-the-free-tier-died/)
2. [Cost Management on Fly.io · Fly Docs](https://fly.io/docs/about/cost-management/)
3. [Fly.io Free Tier 2026: What Can You Actually Host?](https://www.saaspricepulse.com/blog/flyio-free-tier-2026)


---

*Photo by [Microsoft Copilot](https://unsplash.com/@microsoftcopilot) on [Unsplash](https://unsplash.com/photos/woman-cooking-on-a-stovetop-in-a-kitchen-eoTvdke70Vw)*
