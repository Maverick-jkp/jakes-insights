---
title: "GitHub Actions Workflow Not Triggering on Schedule: Cron UTC Offset Fix"
date: 2026-03-29T19:52:16+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "workflow", "REST API"]
description: "Fix GitHub Actions workflow not triggering on schedule by mastering UTC offsets — cron runs in UTC only, so 0 9 * * * may never fire locally."
image: "/images/20260329-github-actions-workflow-not-tr.webp"
technologies: ["REST API", "GitHub Actions", "Rust", "Go"]
faq:
  - question: "github actions workflow not triggering on schedule cron UTC offset fix"
    answer: "GitHub Actions cron schedules run exclusively in UTC, so your cron expression must account for your local timezone offset. For example, if you want a job to run at 11:00 PM EST (UTC-5), you need to write '0 4 * * *' instead of '0 23 * * *'. The most reliable fix is to explicitly calculate the UTC-equivalent time and optionally add a 'workflow_dispatch' trigger for manual recovery."
  - question: "why is my github actions scheduled workflow not running"
    answer: "There are four common reasons a GitHub Actions scheduled workflow silently fails: incorrect UTC offset in your cron expression, platform load delays of up to 45+ minutes, repository inactivity (GitHub disables schedules after 60 days with no commits), or a misconfigured cron syntax. Check each of these before assuming the workflow is broken at the code level."
  - question: "github actions cron schedule delayed or not firing on time"
    answer: "GitHub officially documents that scheduled workflows can be delayed up to 15 minutes during high-load periods, but real-world reports show delays exceeding 45 minutes on busy repositories. This is expected platform behavior and not a bug in your workflow. If timing precision is critical, consider using an external scheduler to trigger your workflow via the GitHub API instead."
  - question: "github actions schedule disabled inactive repository how to re-enable"
    answer: "GitHub automatically disables scheduled workflows on repositories that have had no activity for 60 or more days, with no warning or notification. To re-enable the schedule, you need to either push a new commit to the repository or manually trigger a workflow run. This policy was introduced in 2022 and commonly affects teams running infrequent jobs like quarterly compliance scripts or archival tools."
  - question: "github actions cron daylight saving time timezone not adjusting"
    answer: "GitHub Actions cron expressions do not automatically adjust for Daylight Saving Time because the platform only supports UTC and has no timezone field in the schedule block. This means your job will shift by one hour relative to local time twice a year unless you manually update your cron expression. Using the github actions workflow not triggering on schedule cron UTC offset fix approach — recalculating your UTC offset each time DST changes — is currently the only reliable solution."
---

Scheduled workflows silently failing is one of the most frustrating debugging experiences in CI/CD. No red run. No notification. Just a job that didn't execute — and the culprit is almost always the same: UTC offset confusion combined with GitHub's documented-but-ignored delay behavior.

> **Key Takeaways**
> - GitHub Actions cron schedules run exclusively in UTC, meaning a `0 9 * * *` expression fires at 9:00 AM UTC, not your local time — a mismatch that catches engineers in every timezone.
> - GitHub officially documents that scheduled workflows can be delayed by up to 15 minutes during high-load periods, but real-world reports on Reddit's r/github thread from 2025 show delays exceeding 45 minutes on busy repositories.
> - Inactive repositories (no commits in 60+ days) have their scheduled workflows automatically disabled by GitHub — a policy introduced in 2022 that still trips up teams in 2026.
> - The most reliable fix combines an explicit UTC offset correction in your cron expression with a `workflow_dispatch` fallback trigger for manual recovery.

---

## Why Cron Scheduling in GitHub Actions Goes Wrong

GitHub Actions launched scheduled workflow triggers in late 2019. The feature looked straightforward: write a cron expression, set a time, get automation.

But cron in GitHub Actions has always been UTC-only. There's no timezone field in the `schedule` block. No `TZ` variable that changes when the job fires. The platform evaluates your expression against Coordinated Universal Time, full stop.

That creates an immediate problem for most teams. A developer in New York (UTC-5 in winter, UTC-4 in summer) who wants a nightly build at 11:00 PM needs to write `0 4 * * *` — not `0 23 * * *`. A developer in Berlin (UTC+1 in winter, UTC+2 in summer) wanting the same 11:00 PM local run needs `0 22 * * *` in winter and `0 21 * * *` in summer. Daylight saving time makes it worse. The offset shifts twice a year, and your cron expression doesn't move with it.

GitHub's official Actions documentation states clearly that the `schedule` event uses "POSIX cron syntax" and runs on UTC. That's clearly stated. But between timezone offsets, DST transitions, platform load delays, and the repository inactivity policy, there are at least four distinct reasons a debugging search lands someone on a thread at 2 AM.

The inactivity policy is particularly sharp. GitHub disables scheduled workflows on repositories with no activity for 60 days. No warning email, no dashboard alert — the workflow just stops running. Thibaut Donis documented this behavior in detail on Medium, noting that re-enabling requires manually triggering a run or pushing a commit. Teams running quarterly compliance scripts or archival tooling hit this window regularly and have no idea until something downstream breaks.

---

## The UTC Offset Calculation Problem

The core mechanical issue is straightforward once you see it. GitHub evaluates your cron expression against UTC. If your mental model is local time, every expression you write is off by your UTC offset.

The calculation pattern that works:

**Local time → UTC = Local time minus your UTC offset**

- PST (UTC-8): want 6:00 AM → write `0 14 * * *`
- IST (UTC+5:30): want 6:00 AM → write `30 0 * * *`
- AEST (UTC+10): want 6:00 AM → write `0 20 * * *` (previous UTC day)

The DST trap hits teams running time-sensitive jobs. A workflow set to fire at `0 7 * * *` (targeting 2:00 AM EST) silently shifts to 3:00 AM EDT when clocks spring forward — because the UTC expression doesn't change, but the local offset does. Teams running database maintenance windows or nightly reports during low-traffic hours feel this every March and November.

The fix for DST is either accepting the one-hour drift twice a year or maintaining two separate workflow files that you swap manually. Neither is elegant. That's the honest answer.

---

## The Platform Delay Problem

Separate from UTC offset issues, GitHub's infrastructure introduces scheduling delays that aren't bugs — they're documented behavior.

GitHub's official documentation states scheduled workflows "may be delayed during periods of high loads of GitHub Actions." The platform processes `schedule` events in a queue. During peak CI traffic (typically 9 AM–2 PM UTC on weekdays), that queue backs up.

The r/github community thread on this topic shows engineers reporting 30–60 minute delays on shared runners during business hours UTC. The `0 * * * *` (every hour) expression is the most commonly reported trigger for delay complaints, since it compounds: an hour-interval job delayed by 45 minutes effectively fires at irregular 45-minute intervals.

The practical workaround: schedule intensive jobs during UTC off-peak windows, roughly 18:00–04:00 UTC. That maps to late evening in Europe and the Americas' working hours — convenient for teams running nightly builds.

This approach can fail when your team spans multiple continents and "off-peak UTC" is someone's core business hours. There's no perfect answer there. You're choosing whose timezone gets the short end.

---

## The Repository Inactivity Kill Switch

GitHub's 60-day inactivity policy disables scheduled workflows automatically. The condition is simple: no pushes, no merged PRs, no manual workflow triggers for 60 consecutive days.

This catches maintenance scripts and archival tooling hardest. A monthly data export job on a stable, finished repository hits the 60-day window in two missed cycles. A quarterly compliance report generator never survives.

The fix is a `workflow_dispatch` trigger added alongside `schedule`. It doesn't prevent disabling, but it lets you re-enable with one click from the Actions tab instead of requiring a code push. For teams without direct repo write access, that distinction matters.

---

## Scheduling Approaches: A Reliability Comparison

| Approach | UTC Awareness | DST Handling | Delay Tolerance | Inactivity Risk |
|---|---|---|---|---|
| Raw cron (schedule only) | Manual calculation required | Drifts 1 hour twice/year | High — no fallback | Disabled at 60 days |
| Cron + `workflow_dispatch` | Manual calculation required | Drifts 1 hour twice/year | Medium — manual recovery | Re-enable without push |
| External scheduler (cron-job.org, Pipedream) calling `workflow_dispatch` | Full timezone support | Handles DST natively | Low — external trigger | No inactivity risk |
| Self-hosted runner with cron | Full control | Configure locally | Low | No GitHub queue |

External schedulers calling the GitHub API's `workflow_dispatch` endpoint solve every problem simultaneously. Cron-job.org supports timezone-aware scheduling with DST handling built in. The tradeoff is an external dependency and the need to store a GitHub personal access token as a secret in your trigger service.

This isn't always the right answer. For low-stakes jobs where a one-hour DST drift is acceptable, the added operational complexity of an external scheduler isn't worth it. But for high-stakes scheduled jobs — market open triggers, SLA-bound reports, billing cycles — the external approach earns its complexity.

---

## Three Scenarios, Three Fixes

**Scenario 1 — Nightly build fires at the wrong local time.**
Cause: raw UTC offset miscalculation. Fix: recalculate using `target_local_hour - UTC_offset = cron_hour`. If DST affects your timezone, add a calendar reminder to update the expression twice a year, or accept the one-hour drift.

**Scenario 2 — Scheduled workflow stops running with no error.**
Cause: repository inactivity policy (60 days). Fix: add `workflow_dispatch` to every scheduled workflow. Audit your `.github/workflows/` directory quarterly for jobs that haven't produced a run in 45+ days.

**Scenario 3 — Cron fires but timing is unpredictable.**
Cause: GitHub platform queue delays during peak UTC hours. Fix: shift schedules to the UTC 18:00–04:00 window. For jobs where timing precision matters, move to an external scheduler hitting `workflow_dispatch` via the GitHub REST API.

The fix most teams need isn't one change — it's three: correct the UTC offset, add `workflow_dispatch` as a fallback, and reschedule away from peak UTC hours.

---

## What Comes Next

The scheduled trigger problem in GitHub Actions isn't new, but it keeps catching engineers because the failure modes are silent. No red workflow run. No notification. Just a job that didn't run.

GitHub's Actions team has had timezone-aware scheduling on community request lists for years. The `gh` CLI team acknowledged the request in 2024 feedback threads. Native TZ support in the `schedule` block would eliminate the UTC offset problem entirely. It hasn't shipped as of early 2026, but the volume of debugging threads on this topic makes the demand obvious.

Until it does: calculate your UTC offset explicitly, add `workflow_dispatch` to everything scheduled, stay out of peak UTC hours, and consider an external scheduler for anything time-sensitive. Four changes that make scheduled workflows actually reliable.

What's your most painful scheduled workflow failure? Drop it in the comments — especially if DST was involved.

## References

1. [r/github on Reddit: GH Action Workflow Cron Scheduled runs do not trigger at the exact time?](https://www.reddit.com/r/github/comments/1kn6s7e/gh_action_workflow_cron_scheduled_runs_do_not/)
2. [Automating Your Workflows on a Schedule: GitHub Actions + Cron | by Thibaut Donis | Medium](https://medium.com/@thibautdonis1998/automating-your-workflows-on-a-schedule-github-actions-cron-fd7e662083c6)
3. [Automate Your CI/CD Workflows Using Cron Jobs in GitHub Actions](https://innosufiyan.hashnode.dev/automate-your-cicd-workflows-using-cron-jobs-in-github-actions)


---

*Photo by [Shantanu Kumar](https://unsplash.com/@theshantanukr) on [Unsplash](https://unsplash.com/photos/a-cell-phone-sitting-on-top-of-an-open-book-xvdkNBaja90)*
