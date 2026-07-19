---
title: "Hugo Cloudflare Pages Cron Job Not Triggering: How to Fix"
date: 2026-04-13T20:34:56+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "hugo", "cloudflare", "pages", "GitHub Actions"]
description: "Hugo cron jobs silently skip on Cloudflare Pages when no code changes exist. Fix your GitHub Actions schedule trigger and stop stale deploys in 2025."
image: "/images/20260413-hugo-cloudflare-pages-github-a.webp"
technologies: ["GitHub Actions", "Rust", "Go", "Cloudflare", "Hugo"]
faq:
  - question: "why is my Hugo Cloudflare Pages GitHub Actions cron job not triggering 2025"
    answer: "GitHub automatically disables scheduled workflow triggers on repositories that have had no activity (pushes, PRs, or manual triggers) for 60 days. This is documented platform behavior, not a misconfiguration, and it affects any repo using schedule events including Hugo Cloudflare Pages GitHub Actions deploy cron job setups. The fix is to use workflow_dispatch alongside schedule so the workflow can be manually re-enabled."
  - question: "GitHub Actions schedule trigger not running on inactive repository"
    answer: "GitHub's official Actions documentation states that schedule triggers are automatically disabled after 60 days of repository inactivity. The failure is completely silent — no error emails, no failed job badges, no notifications of any kind. Re-enabling requires a manual trigger or new repository activity to reactivate the scheduled workflow."
  - question: "Hugo Cloudflare Pages GitHub Actions deploy cron job not triggering troubleshoot 2025 fix"
    answer: "The working solution requires a two-part architecture: first, create a Cloudflare Pages Deploy Hook (a webhook URL generated in your Pages project settings), then configure your GitHub Actions workflow to call that hook URL on a schedule. Cloudflare Pages' native GitHub OAuth integration bypasses Actions entirely, so cron-triggered deploys must use the Deploy Hook API rather than the direct Git connection."
  - question: "Cloudflare Pages native GitHub integration not working with GitHub Actions scheduled deploys"
    answer: "Cloudflare Pages' built-in Git integration connects via OAuth and handles deploys independently of GitHub Actions, which means your scheduled Actions workflows cannot trigger it directly. To use time-based deploys, you must generate a Cloudflare Pages Deploy Hook URL and have your GitHub Actions workflow send an HTTP request to that endpoint. These are two separate deployment paths that do not share the same trigger mechanism."
  - question: "how to schedule automatic Hugo site rebuilds on Cloudflare Pages without pushing code"
    answer: "The correct approach is to combine a Cloudflare Pages Deploy Hook with a GitHub Actions workflow using both schedule and workflow_dispatch triggers. The scheduled workflow sends a POST request to the Deploy Hook URL, which tells Cloudflare Pages to rebuild the site without requiring a new Git commit. This pattern supports use cases like refreshing external API data, updating Hugo data files, or keeping timestamps current on a content-heavy static site."
aliases:
  - "/tech/2026-04-13-hugo-cloudflare-pages-github-actions-deploy-cron-j/"

---

Your Hugo site deploys fine when you push code manually. But the scheduled cron job? Silent. Nothing. The site stays stale while your content rots.

This is one of the most quietly frustrating debugging experiences in the modern static site stack. The failure isn't loud — no error emails, no red CI badges, no alerts. The cron job just doesn't run. And when you're trying to automate Hugo + Cloudflare Pages deployments via GitHub Actions with scheduled triggers, the failure modes are specific, well-documented by the community, and almost universally misunderstood the first time around.

This article breaks down why `schedule` triggers in GitHub Actions fail silently, how Cloudflare Pages' direct GitHub integration interacts poorly with Actions-based deploys, and what the working architecture actually looks like in 2026. Whether you're scheduling nightly rebuilds for a content-heavy Hugo site or running weekly link checks before deploy, the same root causes apply.

**Key points covered:**
- Why GitHub Actions `schedule` events stop firing on inactive repositories
- How Cloudflare Pages' native GitHub integration conflicts with Actions-based workflows
- The correct deploy hook + cron architecture for Hugo on Cloudflare Pages
- A comparison of deployment strategies by reliability and control

---

**In brief:** GitHub's documented behavior disables `schedule` triggers on repositories with no activity for 60 days, and Cloudflare Pages' native Git integration doesn't expose the API hooks needed for conditional Hugo deploys. These two constraints together create a silent failure that looks like a misconfiguration but is actually expected platform behavior.

1. GitHub disables scheduled workflows on inactive repos — this is documented in GitHub's official Actions docs and affects any repo that hasn't seen a push, PR, or manual trigger in 60 days.
2. Cloudflare Pages' built-in Git integration bypasses GitHub Actions entirely, meaning cron-triggered workflows that call the CF Pages API need explicit deploy hook URLs, not OAuth-based connections.
3. The fix requires a two-part architecture: a Cloudflare Pages Deploy Hook (webhook URL) + a GitHub Actions workflow using `schedule` + `workflow_dispatch` together.

---

## Background: How This Stack Is Supposed to Work

Hugo is a Go-based static site generator — fast builds, zero runtime dependencies, and a natural fit for Cloudflare Pages' edge delivery. The standard deployment path, as documented on the [Cloudflare Pages Hugo guide](https://developers.cloudflare.com/pages/framework-guides/deploy-a-hugo-site/), connects your GitHub repo directly to Cloudflare Pages via OAuth. Every push to `main` triggers a build. Simple.

The problem starts when you want *scheduled* deploys. Common reasons: pulling in external API data at build time, refreshing a Hugo data file from a remote source, or simply keeping the "Last Updated" timestamp current. None of these need a code push. They need a time trigger.

GitHub Actions supports this via the `schedule` event using cron syntax. Cloudflare Workers and Pages added programmatic deploy support through Deploy Hooks — unique URLs that trigger a build when POSTed to, no auth header required. The [Caktus Group's August 2025 deployment guide](https://www.caktusgroup.com/blog/2025/08/20/how-to-deploy-a-hugo-site-to-cloudflare-pages-with-github-actions/) documents the full GitHub Actions + Cloudflare Pages workflow and notes the deploy hook requirement explicitly.

Put these two together and you get a working scheduled deployment pipeline. Except when you don't — which is most of the first time.

---

## Main Analysis

### Why the Cron Job Stops Triggering

The single most common cause: GitHub disables `schedule` workflows on repositories that have had no activity for 60 days. This is documented behavior in GitHub's Actions documentation, not a bug. "Activity" means pushes, pull requests, or manual workflow runs. A repo that only gets cron-triggered builds doesn't count — the scheduler itself isn't considered activity.

The result is eerie. Your workflow was running fine in January. By March, it stopped. No notification. No email. Just silence.

Fix: Add `workflow_dispatch` as a secondary trigger alongside `schedule`. This lets you manually re-enable the workflow via the GitHub UI, and more importantly, it resets the inactivity clock.

```yaml
on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:
```

Run it manually once a month as a keep-alive. Some teams automate this with a second "ping" workflow that triggers the first one on a 45-day cycle.

### The Cloudflare Pages + GitHub Actions Integration Conflict

Cloudflare Pages offers two connection modes: native Git integration (OAuth-based, automatic) and Deploy Hooks (webhook URLs, manual trigger). When you connect via OAuth, Cloudflare Pages watches your repo directly and builds on push. GitHub Actions is bypassed entirely.

This creates the conflict. If your `schedule` workflow runs a `git commit --allow-empty && git push` to trigger a deploy, it works — but it's wasteful and pollutes your commit history. If it tries to call the Cloudflare API directly without a Deploy Hook configured, it'll fail with auth errors.

The clean solution, per both the Cloudflare Pages docs and the Hugo community discussions on [Hugo Discourse](https://discourse.gohugo.io/t/hugo-support-in-cloudflare-workers/54866), is to use a Deploy Hook. Generate one in your Cloudflare Pages dashboard under **Settings → Builds & Deployments → Deploy Hooks**. Store the URL as a GitHub Actions secret (`CF_DEPLOY_HOOK`). Then call it in your workflow:

```yaml
- name: Trigger Cloudflare Pages Deploy
  run: curl -X POST "${{ secrets.CF_DEPLOY_HOOK }}"
```

That's the entire deploy step. Hugo builds happen on Cloudflare's side using whatever build command you've configured in the dashboard.

This approach can fail when your Deploy Hook URL rotates or gets deleted — Cloudflare doesn't notify you when this happens. Keep a note of when you generated it, and verify the hook still exists if deploys go silent again.

### Cron Syntax and Timezone Traps

GitHub Actions cron runs in UTC. Always. There's no timezone configuration. A `cron: '0 8 * * *'` job runs at 8:00 AM UTC, which is 3:00 AM EST or 4:00 PM JST depending on your audience's location.

This catches teams who set a "morning rebuild" and then wonder why their site updates at 3 AM local time. The fix is arithmetic, not configuration — convert your desired local time to UTC before writing the cron expression.

And: GitHub's cron scheduler has a documented delay of up to 15 minutes during high-traffic periods. A job scheduled for `0 6 * * *` might fire at 6:07 or 6:14. For Hugo rebuilds this rarely matters, but if you're chaining downstream jobs on a tight schedule, pad your timing.

### When This Architecture Doesn't Work

The Deploy Hook + GitHub Actions approach isn't always the right answer.

If your Hugo site is purely content-driven with no external data dependencies and you push updates manually anyway, native Git integration is simpler and has fewer moving parts to break. Actions-based pipelines add workflow files, secrets management, and an additional failure surface.

This approach also works poorly when your team has strict security policies around webhook URLs. Deploy Hook URLs are essentially unauthenticated — anyone with the URL can trigger a build. If that's a concern in your environment, you'll need to route through the Cloudflare API with proper token-based auth instead, which adds complexity.

### Comparison: Hugo + Cloudflare Pages Deployment Strategies

| Strategy | Trigger | Hugo Build Location | Reliability | Control Level |
|---|---|---|---|---|
| Native Git Integration | Git push only | Cloudflare CI | High | Low |
| GitHub Actions + Deploy Hook | Cron / manual / push | Cloudflare CI | High (with `workflow_dispatch`) | High |
| GitHub Actions + `git push` | Cron creates empty commit | Cloudflare CI | Medium (pollutes history) | Medium |
| Cloudflare Workers Cron Triggers | CF Cron | Workers environment | Medium (Hugo support limited) | Medium |
| External scheduler (e.g., Pipedream) | Third-party cron | Cloudflare CI via hook | Medium | Low–Medium |

The **GitHub Actions + Deploy Hook** approach wins on control. You can add pre-deploy steps — fetch external data, validate content, run `hugo check` — plus conditional logic and Slack notifications. None of that is possible with native Git integration alone.

Native Git integration wins on simplicity. If you don't need scheduling and just want push-to-deploy, skip Actions entirely and use Cloudflare's built-in builder.

The `git push` empty-commit approach works but it's a hack. It creates noise in your git history and will confuse future contributors who see daily "chore: trigger build" commits with no actual changes.

---

## Practical Implications: Three Scenarios, Three Fixes

**Scenario 1: Repo has been inactive for 60+ days, cron stopped working.**
The fix is immediate. Go to your GitHub repository → Actions → find the workflow → click "Enable workflow." Then run it manually once via `workflow_dispatch`. Going forward, add `workflow_dispatch` to your trigger list so you can reset the clock without a code push.

**Scenario 2: Cron runs, but Cloudflare Pages doesn't build.**
Check two things in order: First, does your workflow have a Deploy Hook URL configured as a secret? If you're using OAuth-based integration and trying to trigger builds via Actions, there's no mechanism connecting the two. Generate a Deploy Hook in Cloudflare Pages → Settings → Builds & Deployments. Second, check your workflow logs for the `curl` step — a 200 response from the Deploy Hook URL confirms the trigger landed.

**Scenario 3: Builds trigger but Hugo outputs the wrong content (stale data).**
This is a build-time data problem, not a trigger problem. Hugo fetches external data sources (via `getJSON` or `resources.GetRemote`) at build time, but Cloudflare's build cache may serve cached versions of remote resources. Disable the Cloudflare Pages build cache for data-heavy Hugo sites, or pass `--ignoreCache` in your Hugo build command configured in the dashboard.

---

## Conclusion & Future Outlook

The Hugo + Cloudflare Pages + GitHub Actions cron troubleshooting problem in 2026 comes down to three documented behaviors colliding:

- **GitHub disables `schedule` triggers on inactive repos** after 60 days — add `workflow_dispatch` to prevent this
- **Cloudflare Pages native integration bypasses GitHub Actions** — use Deploy Hooks for programmatic triggers
- **GitHub cron runs UTC-only with up to 15-minute delay** — account for timezone math and loose timing dependencies

The working architecture is: `schedule` + `workflow_dispatch` triggers → optional pre-deploy Hugo data fetch steps → `curl POST` to Cloudflare Deploy Hook → Hugo builds on Cloudflare CI.

In the next 6–12 months, Cloudflare Pages is likely to expand its Workers-based build pipeline — as discussed in the Hugo Discourse community threads — which could eventually support native cron scheduling without needing GitHub Actions as a coordinator. Until that ships, the Deploy Hook approach remains the most stable path.

> **Key Takeaways**
> - GitHub silently disables `schedule` triggers after 60 days of repo inactivity — `workflow_dispatch` is your reset switch
> - Cloudflare Pages' OAuth integration and GitHub Actions operate independently; Deploy Hooks are the bridge
> - Deploy Hook URLs are unauthenticated — treat them like passwords and rotate if exposed
> - UTC-only cron timing catches most teams at least once; do the timezone math before you write the expression
> - The `git push` empty-commit workaround functions but pollutes history — use it only as a last resort

If your scheduled Hugo deploy has been silent for more than two weeks, re-enable the workflow manually and add `workflow_dispatch` to your triggers before you change anything else. That single fix resolves the majority of these cases.

The longest these failures go unnoticed tends to surprise teams. Static sites look fine until the moment they don't — and by then, the data is already stale.

## References

1. [Hugo support in Cloudflare Workers - support - HUGO](https://discourse.gohugo.io/t/hugo-support-in-cloudflare-workers/54866)
2. [How to Deploy a Hugo Site to Cloudflare Pages With Github Actions | Caktus Group](https://www.caktusgroup.com/blog/2025/08/20/how-to-deploy-a-hugo-site-to-cloudflare-pages-with-github-actions/)
3. [Hugo · Cloudflare Pages docs](https://developers.cloudflare.com/pages/framework-guides/deploy-a-hugo-site/)


---

*Photo by [NASA](https://unsplash.com/@nasa) on [Unsplash](https://unsplash.com/photos/photo-of-outer-space-Q1p7bh3SHj8)*
