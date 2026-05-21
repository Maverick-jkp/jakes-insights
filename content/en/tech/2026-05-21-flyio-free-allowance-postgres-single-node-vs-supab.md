---
title: "Fly.io Free Allowance Postgres Single Node vs Supabase Free Tier Hobby Project Actual Cost Breakdown"
date: 2026-05-21T22:03:04+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "fly.io", "free", "allowance", "React"]
description: "Fly.io vs Supabase free tier: the real Postgres single node costs revealed before your first unexpected invoice hits."
image: "/images/20260521-flyio-free-allowance-postgres-.webp"
technologies: ["React", "Next.js", "Docker", "REST API", "Vercel"]
faq:
  - question: "fly.io free allowance postgres single node vs supabase free tier hobby project actual cost breakdown which is cheaper"
    answer: "For hobby projects with consistent traffic above 50 requests per day, Supabase Pro at $25/month typically works out cheaper than an equivalent Fly.io Postgres setup, which can range from $15–$40/month once storage and compute stack up. Fly.io's free allowance covers 3 shared-CPU VMs and 3GB persistent storage, but a Postgres single node often consumes that quota before you add any other services. Hidden costs like egress, backup storage, and connection pooling push the real price higher on both platforms."
  - question: "does supabase free tier pause inactive projects"
    answer: "Yes, Supabase pauses free tier projects after 7 consecutive days of inactivity, requiring manual reactivation before your app can use the database again. This is a significant constraint for hobby projects that don't get daily traffic, such as personal tools or side projects you check in on weekly. Upgrading to Supabase Pro removes the pause policy entirely."
  - question: "is postgres on fly.io actually free or does it cost money"
    answer: "Postgres on Fly.io is technically free only if it's your sole running app, since it consumes one of your three free shared-CPU VM allowances and runs at roughly $2.07/month in compute if used continuously. Once you add a web backend or additional services, you exceed the free VM quota and charges begin. Persistent volume storage is also billed at $0.15/GB/month beyond the 3GB free allowance, which a minimal Postgres setup can exceed faster than expected."
  - question: "fly.io free allowance postgres single node vs supabase free tier hobby project actual cost breakdown hidden fees to watch out for"
    answer: "Both platforms have costs that rarely appear in marketing materials, including egress bandwidth charges, backup storage, and connection pooling fees. On Fly.io, WAL logs and indexes can push a Postgres single node past the 3GB free storage limit, while Supabase caps free tier bandwidth at 5GB and database storage at 500MB. Factoring in these hidden costs is essential before choosing a platform for a hobby project that may scale unexpectedly."
  - question: "supabase vs fly.io postgres which is better for a hobby project in 2026"
    answer: "Supabase is generally the lower-friction option for hobby projects because it provides a fully managed Postgres instance without requiring Docker image maintenance or VM configuration. Fly.io offers more control and can be cost-effective if your project stays within the free allowance, but the unmanaged nature of its Postgres setup adds operational overhead. The best choice depends on whether you prioritize simplicity and managed infrastructure or flexibility and granular control over your database environment."
---

Starting a hobby project feels free—until the invoice arrives.

Both Fly.io and Supabase advertise "free" database hosting, but the actual cost breakdown for a Postgres single node tells a very different story depending on how you build. This is the comparison most tutorials skip. Not which platform has prettier docs, but what you actually pay when your weekend project needs persistent data, a backend, and occasional real traffic.

> **Key Takeaways**
> - Fly.io's free allowance covers 3GB of persistent volume storage and shared-CPU VMs, but a Postgres single node requires a dedicated machine that falls outside the free tier on most configurations.
> - Supabase's free tier provides a full Postgres instance with 500MB database storage, but projects pause after 7 days of inactivity—a real constraint for hobby work.
> - For projects with consistent traffic above 50 requests/day, Supabase Pro at $25/month typically outperforms the equivalent Fly.io Postgres setup at $15–$40/month once storage and compute stack up.
> - The cost comparison shifts significantly when you factor in egress, backup storage, and connection pooling—costs that rarely appear in the platform marketing.

---

## The "Free" Database Problem in 2026

Fly.io launched its current free tier structure in late 2023 and has maintained it through 2026, per the official pricing page. The allowance includes 3 shared-CPU VMs, 3GB of persistent volume storage, and 160GB of outbound data per month. Sounds reasonable.

Postgres on Fly.io isn't a managed service. It's a Fly App running the `flyio/postgres` Docker image. That means your "free" Postgres instance is actually a VM consuming shared-CPU compute. The smallest viable Postgres machine—`shared-cpu-1x` with 256MB RAM—runs $0.0000008/second according to Fly.io's billing documentation, which works out to roughly $2.07/month if running continuously.

That's technically within free allowances if it's your *only* running app. Stack a web backend on top, and you've already burned through the free VM quota.

Supabase takes the opposite approach. Its free tier is a *managed* Postgres instance—no VM to wrangle, no Docker image to maintain. The trade-off is the pause policy: projects inactive for 7 consecutive days get paused and require manual reactivation. According to Supabase's official documentation as of May 2026, free tier projects also cap at 500MB database storage and 5GB bandwidth.

---

## Actual Cost Breakdown: What You're Really Running

### Storage and Compute Reality

On Fly.io, persistent volumes are billed at $0.15/GB/month after the 3GB free allowance. A minimal Postgres setup with WAL logs, indexes, and modest data can push past 3GB faster than expected—especially if you're not pruning old records. Add a second volume for backups and you're at $0.30–$0.60/month just in extra storage.

The Postgres VM itself needs at least 256MB RAM to stay stable under even light load. The `performance-1x` instance sits at roughly $1.94/month. But if you hit connection spikes—say, a serverless frontend firing concurrent queries—that 256MB ceiling causes OOM kills. Upgrading to 512MB runs about $3.83/month.

The honest Fly.io Postgres floor for a hobby project: **$4–$6/month** once compute and storage combine, assuming you're using the free tier for your app VM separately.

Supabase's free tier genuinely costs $0 for the database layer—but that pause behavior is a serious UX problem. Waking a paused project adds 10–30 seconds of cold-start latency. For personal projects you check weekly, this is annoying but manageable. For anything with occasional real users, it's not.

### Connection Pooling Costs

Fly.io Postgres doesn't include PgBouncer by default. You can add it as a sidecar, but that means another process, more memory pressure, and manual configuration. Supabase includes Supavisor (their connection pooler) at no additional cost on all tiers as of 2026.

If your hobby project uses a serverless runtime—Next.js API routes on Vercel, Cloudflare Workers—connection pooling isn't optional. Each function invocation opens a new DB connection. Without pooling, you'll hit Postgres connection limits within minutes of moderate traffic. On Fly.io, solving this correctly adds configuration complexity and possibly another $1–$2/month.

### The Full Comparison

| Criteria | Fly.io (Single Node Postgres) | Supabase Free Tier |
|---|---|---|
| Base monthly cost | ~$0–$6 (compute + storage) | $0 |
| Storage included | 3GB (shared w/ all apps) | 500MB dedicated DB |
| Connection pooling | Manual (PgBouncer DIY) | Included (Supavisor) |
| Backup strategy | Manual snapshots or paid | Daily backups included |
| Inactivity penalty | None | Pauses after 7 days |
| Egress free allowance | 160GB/month | 5GB/month |
| Auth/API layer | Not included | Included (PostgREST, GoTrue) |
| Maintenance overhead | High (self-managed VM) | Low (fully managed) |
| Best for | Projects needing VM control | Rapid prototyping, BaaS use cases |

---

## When Each Option Actually Makes Sense

**Choose Fly.io Postgres** when your project already lives on Fly.io and you want the database co-located with low latency. If you're running a full backend on Fly.io VMs anyway, adding a Postgres app in the same region costs little extra and avoids cross-platform egress charges. The self-management overhead is also a legitimate learning opportunity if you want real production Postgres experience.

The cost comparison tips toward Fly.io when you need more than 500MB storage without paying. Supabase's free tier cap fills up quickly with any meaningful relational data—a blog with image URLs and 10,000 posts can hit 200–300MB in post content and metadata alone.

This approach can fail when your project has unpredictable traffic spikes. A self-managed Postgres VM with 256MB RAM and no connection pooler is one noisy traffic burst away from an OOM kill and a silent outage you won't notice until morning.

**Choose Supabase** when you want zero database administration. The free tier includes auth, storage, auto-generated REST APIs, and real-time subscriptions. For a solo developer building a side project, that's weeks of setup work eliminated. The pause problem is real but solvable: a simple cron job pinging your project URL every 5 days keeps it alive within Supabase's own terms of service.

This isn't always the answer, though. If you need more than 5GB egress on the free tier, Supabase's limits hit hard and fast. Fly.io's 160GB free egress allowance is dramatically more generous for data-heavy projects.

At scale, Supabase Pro at $25/month—8GB storage, no pause policy, daily backups, 50GB egress—typically beats a comparable Fly.io Postgres setup running $15–$40/month once you add performance instances and volume storage.

---

## What Changes If Your Project Gets Traction

Hobby projects don't stay hobby forever.

On Fly.io, scaling Postgres means manually resizing the VM, adding read replicas (each billed separately), and managing failover yourself. Fly.io does offer Managed Postgres through their partnership with Supabase—which redirects you back toward the managed approach anyway.

On Supabase, scaling from free to Pro is one button click. The Pro tier adds point-in-time recovery, dedicated resources, and removes the pause constraint. You don't touch the connection string.

Watch for Fly.io's pricing updates in late 2026—the platform has been adjusting machine pricing quarterly, and current `shared-cpu-1x` rates may not hold. Supabase has been stable on free tier limits since mid-2024, which matters when you're budgeting a side project with no revenue to absorb surprise cost changes.

Industry reports consistently show that developer tooling decisions made at the hobby stage tend to stick well past initial deployment. The platform you pick for your weekend project is often the platform you're still running six months later when the project has real users. That switching cost is invisible in any pricing table.

---

## Bottom Line

The comparison comes down to one question: do you want to manage a VM or ship a product?

Fly.io's free tier is genuinely powerful, but Postgres on it requires real operational care. Supabase's free tier is narrower in storage and frustrating with its pause policy, but the managed experience is worth it for 90% of hobby projects.

Start with Supabase. Keep a cron job running. When you hit 400MB of data or need serious uptime guarantees, the $25/month Pro upgrade is still cheaper than the equivalent Fly.io setup with proper failover.

What's your current DB bill on a hobby project? Drop your stack in the comments—curious how others are handling the cost crunch on personal side projects in 2026.

## References

1. [Fly.io Pricing Explained 2026 - Plans, Real Costs & a Smarter Alternative • Kuberns](https://kuberns.com/blogs/flyio-pricing/)
2. [Fly.io Pricing 2026: 4 Plans from Free–$300/month](https://costbench.com/software/developer-tools/flyio/)
3. [Fly.io Pricing Plans and Tiers Compared (2026) | CompareTiers](https://comparetiers.com/tools/fly-io)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
