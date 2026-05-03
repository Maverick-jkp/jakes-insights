---
title: "Vercel Hobby Plan Bandwidth Limit Exceeded: Next.js Alternatives"
date: 2026-05-03T19:57:21+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "vercel", "hobby", "plan", "React"]
description: "Vercel Hobby plan's 100GB bandwidth limit just killed your Next.js app? Here are the fastest alternative deployment options to get back online."
image: "/images/20260503-vercel-hobby-plan-bandwidth-li.webp"
technologies: ["React", "Next.js", "Node.js", "Docker", "Vercel"]
faq:
  - question: "vercel hobby plan bandwidth limit exceeded alternative deployment nextjs app router 2025"
    answer: "When your Vercel Hobby plan bandwidth limit is exceeded on a Next.js App Router project, the main alternatives are Cloudflare Pages, Railway, and Fly.io, all of which support App Router in 2025-2026 without significant feature loss. Self-hosting on a VPS like Hetzner or DigitalOcean is also viable and offers the most cost control, though it requires manual infrastructure setup that Vercel normally handles for you."
  - question: "what happens when you hit vercel hobby plan 100gb bandwidth limit"
    answer: "When a Vercel Hobby plan hits the 100GB monthly bandwidth cap, your deployment effectively stops serving traffic normally, and you're forced to either upgrade to the Pro plan at $20/month per member or migrate to another platform. The situation is often compounded by the fact that Vercel's terms of service prohibit commercial use on the Hobby tier, meaning revenue-generating apps may already be out of compliance before hitting the bandwidth wall."
  - question: "is vercel hobby plan free tier good enough for production nextjs app"
    answer: "Vercel's Hobby plan is not suitable for production or commercial apps because it explicitly prohibits commercial use in its terms of service, caps bandwidth at 100GB per month, and limits log retention to just one hour. The one-hour log retention alone makes diagnosing production incidents very difficult, and any app that experiences a viral traffic spike can exhaust the bandwidth cap almost instantly."
  - question: "best cheap alternatives to vercel for nextjs app router deployment 2025"
    answer: "Cloudflare Pages, Railway, and Fly.io are the most production-ready low-cost alternatives to Vercel for Next.js App Router deployments in 2025, each with full or near-full support for Server Components and Edge Runtime. For teams comfortable with DevOps, self-hosting on affordable VPS providers like Hetzner or DigitalOcean offers even greater cost control, typically running a comparable workload for a few dollars per month."
  - question: "does cloudflare pages support nextjs app router server components 2025"
    answer: "Cloudflare Pages supports Next.js App Router including Server Components in 2025, making it one of the most credible free-tier alternatives when a vercel hobby plan bandwidth limit exceeded alternative deployment nextjs app router 2025 situation forces a migration. However, like other non-Vercel platforms, there may be minor trade-offs in certain edge cases around specific Next.js features that rely on deep Vercel-native integration."
---

Your Next.js app just hit Vercel's bandwidth ceiling. The dashboard shows "limit exceeded." Traffic's still coming in.

Now what?

This scenario plays out constantly for indie developers and small teams shipping production apps on Vercel's free tier. The Hobby plan's 100GB/month bandwidth cap sounds generous — until your app gets a Reddit mention or a Product Hunt bump. Then you're staring at a hard choice: pay Vercel's Pro plan at $20/month per member, or find a credible alternative deployment path for your Next.js App Router project.

The decision isn't obvious. Next.js has deep Vercel integration, and not every platform handles App Router, Server Components, and Edge Runtime equally well.

This analysis breaks down the real costs, the real alternatives, and what the data shows about platform maturity in 2026.

---

> **In brief:** Vercel's Hobby plan caps bandwidth at 100GB/month and blocks custom domains for commercial projects — limits that serious apps routinely hit within their first viral moment. At least three production-ready alternatives now handle Next.js App Router without meaningful feature loss.
>
> 1. Vercel's Hobby plan officially prohibits commercial use, meaning any revenue-generating project is already out of compliance before it hits the bandwidth wall.
> 2. Cloudflare Pages, Railway, and Fly.io each support Next.js App Router in 2026, though each trades a different feature for cost savings.
> 3. Self-hosting on a VPS (DigitalOcean, Hetzner) gives the most cost control but requires manual infrastructure work that Vercel abstracts away.

---

## The Vercel Hobby Plan: What the Limits Actually Say

Vercel's documentation is direct. The Hobby plan ships with 100GB bandwidth per month, 6,000 build minutes per month, and serverless function execution capped at 100GB-hours. But the bandwidth number is the one that catches people off guard.

According to Vercel's official limits documentation, the Hobby plan also restricts concurrent builds to 1 and limits log retention to 1 hour. That last one hurts in production — you can't diagnose a 2 AM outage with 1-hour logs.

More critically, Vercel's terms of service explicitly prohibit commercial use on the Hobby tier. That Reddit thread from r/nextjs captures the exact moment this becomes real: someone ships a product, gains traction, and gets flagged simultaneously for bandwidth overage *and* a commercial use violation. Two problems, not one.

The math on bandwidth hits quickly for media-heavy apps. A Next.js app serving optimized images through `next/image` — with Vercel handling the image optimization — counts that processed bandwidth against your cap. A landing page with a 500KB hero image and 10,000 monthly visitors burns through roughly 5GB on images alone, before counting HTML, JS bundles, and API responses.

Next.js 14 and 15 App Router apps also tend to ship heavier JS bundles than Pages Router equivalents during the transition period, as teams progressively migrate components. That adds up fast.

---

## Why This Is Getting Worse in 2026

Next.js App Router adoption has crossed into mainstream. By early 2026, most new Next.js projects start with App Router by default — Vercel's own documentation treats it as the primary architecture. Server Components, Server Actions, and the new `use cache` directive in Next.js 15 all tie into Vercel's infrastructure in ways that feel native.

That native integration is the trap. It makes Vercel look like the only viable host, when the reality is more nuanced.

The second factor is cost pressure. Vercel Pro at $20/user/month works out to $240/year for a solo developer. For a bootstrapped SaaS doing $500/month in revenue, that's a meaningful percentage of income. The gap between "free and over-limit" and "paid and viable" feels steep — steep enough that developers are actively looking for exits.

And third: App Router's reliance on React Server Components creates genuine hosting complexity. Not every platform handled RSC correctly in 2024. By 2026, that's changed — but the reputation stuck, and many developers haven't re-evaluated their options since.

---

## Alternative Deployment Options: What the Data Shows

### Cloudflare Pages + Workers

Cloudflare Pages supports Next.js via the `@cloudflare/next-on-pages` adapter. As of 2026, it handles App Router, Server Components, and Edge Runtime. The free tier includes unlimited bandwidth — Cloudflare's CDN network absorbs egress costs differently than Vercel's model.

The catch: Node.js runtime isn't available on Pages. Functions run in the Workers runtime (V8 isolates), which means `node:crypto`, `node:fs`, and other Node APIs require workarounds or polyfills. If your app uses libraries that assume a Node environment, you'll hit compatibility issues that aren't always obvious until deployment.

This approach can fail when your dependency tree runs deep into Node-specific APIs. Audit before you commit.

### Railway

Railway runs your Next.js app as a containerized Node process. App Router works fully — RSC, Server Actions, everything — because it's just running `next start` on a real Node server. Railway's pricing is usage-based: roughly $5/month for a small always-on service, scaling with CPU and memory.

Bandwidth on Railway is also usage-based, but far cheaper than Vercel's overage pricing. And because Railway runs always-on containers, there are no cold starts — which actually improves performance consistency compared to serverless.

### Fly.io

Similar to Railway: containerized deployment, full Node runtime, no platform-specific adapter needed. Fly's free tier (as of May 2026) includes 3 shared-CPU VMs with 256MB RAM. That's tight for a Next.js App Router app under load, but workable for low-traffic projects. Paid machines start at roughly $1.94/month for a shared-CPU-1x with 256MB.

The multi-region deployment story on Fly is genuinely strong — if you need geographic distribution without Vercel's pricing, it's worth the extra operational learning curve.

### Self-Hosted VPS (DigitalOcean / Hetzner)

A Hetzner CX22 server (2 vCPU, 4GB RAM) costs €3.79/month as of 2026 pricing. Run `next start` behind an Nginx reverse proxy, add a free SSL cert via Let's Encrypt, and you have a production Next.js host for under $5/month. Bandwidth is either unmetered or very high-cap — Hetzner includes 20TB/month on that tier.

The real cost is operational: OS updates, process supervision (`pm2` or systemd), and deployment pipelines are all yours to manage. This isn't the right path for teams without infrastructure experience. But for developers who are comfortable in a terminal, it's the highest-control, lowest-cost option on the board.

### Platform Comparison

| Feature | Vercel Pro | Cloudflare Pages | Railway | Fly.io | Hetzner VPS |
|---|---|---|---|---|---|
| **Monthly cost (base)** | $20/user | Free / $5 Workers | ~$5 | ~$2–5 | ~$4 |
| **Bandwidth** | 1TB included | Unlimited | Usage-based | 160GB free | 20TB |
| **App Router support** | Native | Via adapter | Full (Node) | Full (Node) | Full (Node) |
| **Server Actions** | Yes | Partial* | Yes | Yes | Yes |
| **Cold starts** | Yes (serverless) | Yes (edge) | No (always-on) | No (always-on) | No |
| **Ops overhead** | None | Low | Low | Medium | High |
| **Best for** | Teams, enterprise | Edge-heavy apps | Solo devs, small teams | Multi-region apps | Cost-sensitive production |

*Cloudflare's Workers adapter support for Server Actions improved significantly in late 2025 but still has edge cases with streaming responses.

The trade-off pattern is consistent across all alternatives. Moving away from Vercel means accepting runtime constraints (Cloudflare), adding operational overhead (VPS), or accepting usage-based pricing uncertainty (Railway/Fly). None of these is a dealbreaker — but each one requires a deliberate decision, not a default.

---

## Making the Decision: Three Real Scenarios

**Scenario 1: Indie SaaS, fewer than 50K monthly visitors, standard Node dependencies**

Railway wins. Full App Router support, predictable costs around $5–10/month, and deployment via `railway up` is nearly as simple as `vercel --prod`. No adapter quirks, no runtime restrictions.

**Scenario 2: Content-heavy site, global audience, bandwidth-sensitive**

Cloudflare Pages is worth the adapter complexity. Unlimited bandwidth and a global CDN with sub-50ms response times in most regions make it hard to beat for static-heavy or ISR-heavy Next.js apps. That said, audit your Node.js dependencies first — run `npx @cloudflare/next-on-pages` locally and check the compatibility report before committing. Discovering a blocking incompatibility after migration is a bad afternoon.

**Scenario 3: Startup with engineering capacity, cost matters more than convenience**

Hetzner VPS plus Nixpacks or a Dockerfile, with GitHub Actions handling CI/CD. Marginally more setup time upfront, but the long-term cost and control are unmatched. At $4/month versus $20/month, that's $192/year saved per developer seat — real money for early-stage teams watching burn rate.

---

## What to Watch Through the Rest of 2026

The platform landscape for Next.js App Router deployment is still shifting. Three signals worth tracking:

**Cloudflare's Node.js compatibility roadmap.** Cloudflare has been steadily expanding Node.js API support in Workers. If they reach parity with the commonly used Node APIs — particularly `crypto` and stream APIs — Pages becomes a much cleaner Vercel alternative without the adapter workarounds.

**Vercel's pricing pressure.** Vercel isn't immune to competition. Their January 2026 pricing changes slightly reduced overage costs for Pro users, which suggests awareness of churn risk. Further adjustments are possible as Railway and Fly continue gaining adoption.

**Next.js 15 self-hosting improvements.** The Next.js team has shipped dedicated documentation for self-hosting App Router in recent releases, including better guidance on output file tracing for Docker deployments. That makes the VPS path more accessible to developers who aren't infrastructure specialists — which widens the viable audience for the cheapest option on the list.

---

## The Bottom Line

Hitting Vercel's Hobby bandwidth limit isn't the end of the road. It's a forcing function.

The Hobby plan was never designed for production commercial apps — Vercel's own terms say so explicitly. The good news: by 2026, App Router works well on Railway, Fly.io, and self-hosted Node environments, and Cloudflare Pages handles it acceptably for edge-compatible workloads.

The decision criteria are straightforward. If you need zero ops overhead and have budget, Vercel Pro is still the path of least resistance. If you're cost-sensitive and your app doesn't have exotic Node dependencies, Railway is the closest equivalent experience. If bandwidth is your primary concern and your app is edge-compatible, Cloudflare Pages eliminates that variable entirely.

What's your current deployment setup — and which constraint hit you first, bandwidth or the commercial use clause?

## References

1. [Limits](https://vercel.com/docs/limits)
2. [r/nextjs on Reddit: My product has exceeded the Vercel Hobby Plan limits.](https://www.reddit.com/r/nextjs/comments/1skm2ks/my_product_has_exceeded_the_vercel_hobby_plan/)


---

*Photo by [Surface](https://unsplash.com/@surface) on [Unsplash](https://unsplash.com/photos/a-laptop-computer-sitting-on-top-of-a-white-table-F4ottWBnCpM)*
