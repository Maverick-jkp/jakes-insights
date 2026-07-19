---
title: "GitHub Actions Self-Hosted ARM64 Mac Mini Cost vs Hosted Minutes"
date: 2026-04-10T20:06:56+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "github", "actions", "self-hosted", "React"]
description: "Compare self-hosted runner arm64 Mac mini costs vs GitHub-hosted minutes at $0.08/min before the 2026 pricing shift hits your CI budget."
image: "/images/20260410-github-actions-selfhosted-runn.webp"
technologies: ["React", "GitHub Actions", "Linux", "Go"]
faq:
  - question: "github actions self-hosted runner arm64 mac mini cost vs github hosted minutes which is cheaper"
    answer: "A self-hosted ARM64 Mac mini costs approximately $0.006–$0.009 per minute of active build time when factoring in hardware amortization, power, and network overhead, compared to $0.08 per minute for GitHub-hosted macOS runners. This makes the Mac mini approach roughly 8-10x cheaper per minute, but only makes financial sense if your team runs enough builds to offset the operational overhead of managing physical hardware."
  - question: "how much do github hosted macos runner minutes cost in 2026"
    answer: "GitHub-hosted macOS runners are billed at $0.08 per minute as of 2026, which is 10 times the Linux runner rate of $0.008 per minute. For a team running a 20-minute build 50 times per month, that adds up to $80 per month just for macOS CI minutes, scaling to $800–$1,200 per month for larger teams with frequent PR builds."
  - question: "does github charge per minute for self-hosted runners in 2026"
    answer: "GitHub has proposed introducing per-minute fees for self-hosted runners as part of a 2026 pricing shift, which previously allowed teams to use self-hosted infrastructure without additional GitHub billing charges. The community has reacted sharply to this change in GitHub Discussions thread #182089, as it directly impacts teams who switched to self-hosted Mac minis specifically to avoid high GitHub-hosted macOS minute costs."
  - question: "is a mac mini worth it for github actions ios ci self-hosted runner"
    answer: "An M2 Mac mini priced at around $599 and amortized over three years costs roughly $0.004 per minute in hardware alone, making it significantly cheaper than GitHub-hosted macOS runners at $0.08 per minute. However, a self-hosted ARM64 Mac mini setup is only cost-effective if your team generates enough build volume to justify the operational overhead of maintaining physical hardware."
  - question: "github actions self-hosted runner arm64 mac mini cost vs github hosted minutes breakeven point"
    answer: "When comparing github actions self-hosted runner arm64 mac mini cost vs github hosted minutes, the breakeven calculation depends on total monthly build minutes consumed by your team. At $0.08 per GitHub-hosted minute versus roughly $0.009 per minute all-in for a self-hosted Mac mini, teams running several hundred or more macOS build minutes per month will typically see meaningful savings, though GitHub's proposed new self-hosted runner fees could shift that threshold higher."
aliases:
  - "/tech/2026-04-10-github-actions-selfhosted-runner-arm64-mac-mini-co/"

---

Build costs just got complicated.

GitHub's 2026 pricing shift—introducing per-minute fees on self-hosted runners—has forced engineering teams to actually do the math on infrastructure they previously treated as "free." For macOS CI specifically, where GitHub-hosted runners already cost **$0.08/minute** (10x the Linux rate), the calculation matters a lot.

Most iOS and macOS teams have run self-hosted ARM64 Mac minis precisely to escape those steep GitHub-hosted macOS costs. An M2 Mac mini at ~$599 amortized over three years runs roughly **$0.004/minute** in hardware cost alone—a stark contrast. But GitHub's proposed per-minute fee for self-hosted runners changes that math entirely, and the community reaction on GitHub Discussions (thread #182089) has been sharp.

This analysis breaks down the actual numbers across three scenarios: what GitHub-hosted macOS minutes cost at scale in 2026, what a self-hosted ARM64 Mac mini setup actually costs all-in, and whether GitHub's new self-hosted runner fees make the Mac mini approach less attractive.

The thesis: even with new per-minute charges on self-hosted runners, an ARM64 Mac mini still undercuts GitHub-hosted macOS minutes by a wide margin—but only if your team runs enough builds to justify the operational overhead.

---

> **In brief:** GitHub-hosted macOS runners cost $0.08/minute, making them expensive at any meaningful CI volume. A self-hosted ARM64 Mac mini drops that effective rate to under $0.01/minute even after accounting for hardware, power, and maintenance costs.
>
> 1. GitHub-hosted macOS minutes are billed at $0.08/minute as of 2026—10x the Linux rate—per GitHub's official billing documentation.
> 2. An M2 Mac mini amortized over 36 months with power and network overhead costs approximately $0.006–$0.009/minute of active build time.
> 3. GitHub's proposed per-minute fee for self-hosted runners (discussed in community thread #182089) would add cost on top of hardware, but the final rate will determine whether self-hosted remains viable.

---

## Why macOS CI Has Always Been Expensive

macOS CI has never been cheap. Apple's hardware restrictions mean you can't legally run macOS on non-Apple hardware—unlike Linux, where you can spin up a $0.008/minute x86 instance anywhere. GitHub reflects this reality directly in its pricing: macOS runners cost **$0.08/minute** on the hosted tier vs. **$0.008/minute** for Linux, per GitHub's current billing page.

Teams building iOS apps, macOS utilities, or Electron apps hit this ceiling fast. A single release pipeline with a 20-minute build, running 50 times per month, racks up **1,000 minutes × $0.08 = $80/month** on macOS alone. Scale to 10 developers with multiple PRs per day and you're looking at $800–$1,200/month purely on macOS CI minutes.

The self-hosted runner path emerged as the obvious workaround. Buy an M1 or M2 Mac mini, register it as a GitHub Actions runner, and your "minute" cost collapses to electricity and depreciation. Laurent Meyer's devblog documented this setup in detail—the process is straightforward, though it does require persistent uptime management.

The disruption in early 2026: GitHub floated introducing per-minute charges for self-hosted runners, surfaced in community discussion #182089. The r/devops community flagged this quickly. The core concern is that GitHub would charge for self-hosted runner minutes *in addition to* your hardware costs—effectively taxing infrastructure you already own.

## The True Cost of GitHub-Hosted macOS Minutes at Scale

GitHub-hosted macOS runners (currently M1/M2-based on the `macos-14` image) bill at **$0.08/minute**. GitHub's free tier provides 2,000 minutes/month for free accounts and 3,000 for Pro—but these are shared across all runner types, and macOS minutes count at **10x** the Linux multiplier under the minute-multiplier system.

So 500 macOS minutes effectively consume 5,000 "counted" minutes from your quota. For teams on GitHub Team ($4/user/month), the included minutes disappear fast. At 10 developers each triggering 5 macOS builds per day at 15 minutes per build:

> 10 × 5 × 15 × 22 workdays = **16,500 macOS minutes/month**
> Cost: 16,500 × $0.08 = **$1,320/month**

That's real money. And it scales linearly—there's no volume discount on macOS minutes.

## What an ARM64 Mac Mini Self-Hosted Setup Actually Costs

An M2 Mac mini (base model) retails at $599 as of April 2026. Running it as a dedicated CI machine means accounting for:

- **Hardware depreciation**: $599 ÷ 36 months = **$16.64/month**
- **Power consumption**: ~6W idle, ~30W under load; at 24/7 operation, ~$3–$5/month at US average electricity rates
- **Network/infrastructure**: Negligible if colocated in an existing office
- **Maintenance overhead**: Estimated 1–2 hours/month for a solo DevOps engineer

Total hard cost: roughly **$20–$25/month** per Mac mini runner.

Apply that same 16,500 minutes/month workload from above and the effective rate becomes:

> $22 ÷ 16,500 minutes = **$0.0013/minute**

That's a **98% cost reduction** vs. GitHub-hosted. Even adding $0.003/minute for engineer time amortized, you're still at **$0.004–$0.006/minute** total.

## GitHub's Proposed Self-Hosted Runner Fee: The Threat Vector

Community discussion #182089 on GitHub sparked significant pushback. GitHub's proposed model would charge a per-minute fee for self-hosted runner compute—not for the hardware itself, but for GitHub's orchestration layer: queue management, workflow coordination, secrets injection.

The exact rate hasn't been finalized as of April 2026, but the community discussion suggests a potential fee in the **$0.004–$0.008/minute** range. At the lower end, the Mac mini approach still wins handily. At $0.008/minute—matching GitHub-hosted Linux pricing—the combined cost looks like this:

> Hardware cost ($0.006) + GitHub fee ($0.008) = **$0.014/minute**

Still 82% cheaper than GitHub-hosted macOS at $0.08/minute. But the value proposition narrows for teams running low build volumes where setup overhead isn't justified.

This approach can fail when teams underestimate maintenance burden. A Mac mini that goes offline during a critical deployment window, or requires OS updates that break runner compatibility, creates indirect costs that don't show up in the spreadsheet. That risk is real.

## Comparison: GitHub-Hosted vs. Self-Hosted ARM64 Mac Mini

| Criteria | GitHub-Hosted macOS | Self-Hosted Mac Mini (No Fee) | Self-Hosted Mac Mini (With Proposed Fee) |
|---|---|---|---|
| **Per-minute cost** | $0.08 | ~$0.006 | ~$0.014 |
| **Setup time** | Zero | 2–4 hours initial | 2–4 hours initial |
| **Monthly maintenance** | Zero | 1–2 hrs/month | 1–2 hrs/month |
| **Hardware investment** | $0 upfront | $599+ | $599+ |
| **Break-even point** | N/A | ~300 min/month | ~700 min/month |
| **Parallel runners** | On-demand | One per Mac mini | One per Mac mini |
| **macOS version control** | GitHub-managed | Full control | Full control |
| **Best for** | Low volume / zero ops teams | High-volume iOS/macOS CI | High-volume with fee tolerance |

The break-even calculus is the key insight. At **300 macOS minutes/month**—roughly a small solo project—the Mac mini pays for itself vs. GitHub-hosted in about two months, even before any proposed fee. At 700 minutes/month with the fee factored in, break-even extends to roughly four months. Still worth it for any serious iOS team.

## Three Scenarios Worth Modeling

**Small team, low build volume (under 500 macOS minutes/month).**
GitHub-hosted is probably fine. At 500 minutes × $0.08 = $40/month, the operational overhead of maintaining a Mac mini runner likely isn't worth it. The proposed self-hosted fee doesn't change this—the volume just isn't there to justify physical infrastructure.

**Mid-size iOS team (2,000–5,000 macOS minutes/month).**
This is where the self-hosted ARM64 Mac mini argument is strongest. At 3,000 minutes/month, GitHub-hosted costs $240/month. A Mac mini costs $22/month in hard costs, or ~$64/month with the proposed fee applied. That's a **$176–$218/month saving**—more than the hardware cost recovered in the first month alone. One Mac mini handles this volume easily if builds don't pile up simultaneously.

**High-volume CI pipeline (10,000+ macOS minutes/month).**
You likely need 2–3 Mac minis to handle concurrency. The math still works: three Mac minis at $22/month = $66/month in hardware vs. $800+ in GitHub-hosted minutes. Add proposed fees ($0.008 × 10,000 = $80/month) and the total lands at ~$146/month. GitHub-hosted equivalent: $800. Self-hosted wins by a factor of 5x.

This isn't always the answer, though. Teams without a dedicated DevOps function—where every hour of infrastructure maintenance pulls an engineer off product work—may find the true cost of self-hosted higher than the numbers suggest. The $22/month hardware figure assumes someone competent is managing the runner reliably. If that's not the case, GitHub-hosted's zero-ops model has real value.

**What to watch:** GitHub's final decision on the self-hosted runner pricing model is the key variable. If GitHub caps the fee at $0.004/minute or below—or exempts certain plan tiers—the Mac mini path remains clearly dominant for any team above ~300 monthly macOS minutes. If fees land at or above $0.01/minute, teams with moderate volumes will need to re-run the numbers. Watch GitHub's changelog and thread #182089 for the finalized rate.

## What the Numbers Actually Tell You

GitHub-hosted macOS CI is expensive by design—Apple hardware scarcity makes it so. An ARM64 Mac mini self-hosted runner cuts that effective rate by 80–95% depending on volume, even after accounting for all real-world costs.

Over the next 6–12 months, expect GitHub to finalize the self-hosted runner fee structure. Community pushback from thread #182089 and r/devops has been vocal, which may soften the final rate. Apple Silicon's continued performance-per-watt improvement—M3 and M4 Mac minis are already available—only strengthens the self-hosted case as build times shrink and throughput per machine increases.

> **Key Takeaways:**
> - GitHub-hosted macOS costs $0.08/minute—10x Linux pricing—making it unsustainable at scale
> - An M2 Mac mini runs $0.006–$0.009/minute all-in, rising to ~$0.014/minute with proposed GitHub self-hosted fees
> - Break-even vs. GitHub-hosted occurs at roughly 300–700 macOS minutes/month depending on fee structure
> - The self-hosted advantage holds even with proposed fees—but only above low build volumes, and only if your team can absorb the operational overhead

The clearest action: if your team exceeds 500 macOS CI minutes/month, model the numbers for your specific volume. The spreadsheet will tell you what you need to know.

## References

1. [r/devops on Reddit: Github Actions introducing a per-minute fee for self-hosted runners](https://www.reddit.com/r/devops/comments/1po8hj5/github_actions_introducing_a_perminute_fee_for/)
2. [Per minute charges for self hosted runners? Wtf? · community · Discussion #182089](https://github.com/orgs/community/discussions/182089)
3. [Using Github's self-hosted runners - Laurent Meyer's Devblog](https://meyer-laurent.com/using-github-self-hosted-runners)


---

*Photo by [Rubaitul Azad](https://unsplash.com/@rubaitulazad) on [Unsplash](https://unsplash.com/photos/a-white-dice-with-a-black-github-logo-on-it-HLQDfaJUTVI)*
