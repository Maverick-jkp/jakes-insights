---
title: "ChatGPT Codex Limits for Plus Users: What You Actually Get"
date: 2026-11-07T02:15:41+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "chatgpt", "codex", "limits"]
description: "ChatGPT Codex hits Plus users hard: the $20 plan caps agentic coding tasks fast. Here's exactly where the limits land in 2025."
image: "/images/20261107-chatgpt-codex-limits-plus.webp"
faq:
  - question: "How many Codex tasks do Plus users actually get per day?"
    answer: "Plus users don't have a daily cap — they get a 5-hour rolling window that resets continuously. Within that window, task limits range from 5–45 on GPT-6 Astra up to 350–3,000 on lower-tier Luna models, depending on which model you're running."
  - question: "What kills your allowance faster than expected on the $20 plan?"
    answer: "Fast mode and Ultrafast mode apply 2.5x and 8x consumption multipliers respectively, so a single intensive refactoring session can drain your entire Plus budget in under an hour. Most users don't realize the multipliers are active until the limit hits mid-task."
  - question: "Does regular ChatGPT usage eat into Codex tasks now?"
    answer: "Yes, as of December 2026 both products draw from one shared token pool. Heavy API chat usage directly competes with your Codex task budget, so a busy conversation day can quietly reduce how many coding tasks you have left."
  - question: "Is Pro worth $200 just to remove the rolling cap?"
    answer: "If you're running Codex in production — multi-file edits, automated PRs, test suite runs — the 5-hour cap on Plus will interrupt real work at the worst moments. Pro removes the cap entirely across all models, which is less a luxury and more a baseline for sustained engineering use."
  - question: "When does the 5-hour window actually reset for Plus accounts?"
    answer: "The reset is rolling and continuous, not tied to midnight or a fixed daily schedule. As tasks age out of the 5-hour window, capacity frees up gradually — which helps users who spread work across the day rather than coding in one long session."
---

The gap between what OpenAI markets and what Plus users actually receive has never been sharper than it is right now. Codex — OpenAI's agentic coding assistant — arrived with serious promise: autonomous task execution, multi-file edits, CLI integration, GitHub connections. But if you're on the $20 Plus plan, the ceiling comes fast, and it's lower than the marketing suggests.

This matters because Codex isn't a novelty anymore. As of late 2026, it's a production tool that engineers are building workflows around — running test suites, drafting PRs, refactoring legacy code. When you hit a limit mid-task, it's not an inconvenience. It breaks your day.

The core argument: ChatGPT Codex limits for Plus users represent a carefully engineered upsell architecture. The access is real, the restrictions are significant, and knowing exactly where the walls are is the difference between a tool that works for you and one that constantly fails you at the wrong moment.

This analysis covers how the 5-hour rolling window actually works, which models Plus users can access versus what's locked behind Pro, consumption multipliers that drain your allowance faster than expected, and what December's consolidation means for your existing ChatGPT usage budget.

---

> **Key Takeaways**
> - Plus users get 5–45 tasks per 5-hour window on GPT-6 Astra, dropping sharply compared to the 350–3,000 range available on Luna-tier models within the same plan.
> - OpenAI's rolling reset mechanism frees up limits continuously rather than at midnight — a genuine advantage for users who spread work across the day.
> - Fast mode and Ultrafast mode carry 2.5x and 8x consumption multipliers respectively, meaning a single intensive session can exhaust a Plus allowance in under an hour.
> - Starting December 2026, ChatGPT and Codex draw from one shared token pool — heavy API chat usage now competes directly with your Codex task budget.
> - Pro at $200/month removes the 5-hour cap entirely across all models, the clearest line between "usable for production work" and "usable for experimentation."

---

## Background & Context

Codex launched as a separate product with its own interface and pricing ambiguity. Through early 2026, it existed somewhat independently of the main ChatGPT subscription tiers — confusing for users who weren't sure whether their Plus plan covered it or not.

OpenAI clarified the picture in stages. By September 2026, the official Codex pricing page confirmed that Codex access is bundled directly into subscription tiers, not sold separately. That resolved one confusion but introduced another: if Codex lives inside your plan, it also competes with everything else inside your plan.

The model landscape shifted significantly during this period. GPT-5.5, GPT-5.6, and the GPT-6 family (Sol, Luna, Astra, Terra) all rolled out with different capability and cost profiles. Each carries different task allowances for Plus users. GPT-6 Astra, the most capable reasoning model in the lineup, gives Plus users just 5–45 tasks per 5-hour window, according to OpenAI's pricing documentation. GPT-6 Luna, meanwhile, grants 350–3,000 tasks — but it's a less capable model for complex coding work.

The December 2026 consolidation is the most consequential change. According to the OpenAI Help Center, OpenAI is merging ChatGPT and Codex allowances into a single shared token pool for Plus, Pro, and Business subscribers. If you're currently burning through ChatGPT for research or writing while also running Codex for code tasks, those two pools are about to become one.

## How the 5-Hour Window Actually Works

Forget daily resets. Codex operates on a rolling 5-hour token allowance per model. Usage spent at 9am frees at 2pm — not at midnight, not weekly.

This design is smarter than it looks. A developer who does heavy morning work and lighter afternoon work gets a partial recovery before end-of-day. Hitting a wall at 10am isn't catastrophic — 15 tasks might free up by 11:30am depending on when you burned them.

A separate weekly cap is layered on top. OpenAI doesn't publish the exact number. That opacity is a real problem for anyone trying to plan production workflows around Codex. You can track current usage at the Codex settings dashboard or via `/status` in CLI sessions — but there's no projected weekly burn rate in any official dashboard.

The meter counts tokens, not tasks. That distinction matters. A "task" that generates 4,000 tokens of output costs significantly more than one generating 400 tokens, even if both register as a single Codex operation.

## The Consumption Multiplier Problem

This is where Plus users get burned most often. Three usage patterns carry aggressive multipliers:

- **Fast mode**: 2.5x standard consumption rate
- **Ultrafast mode** (available on Astra and GPT-6.1 Sol): 8x standard rate
- **Image generation**: 3–5x faster burn

An 8x multiplier on GPT-6 Astra — which already gives Plus users just 5–45 tasks — means Ultrafast mode can exhaust the high end of that allowance in roughly 5–6 task-equivalent actions. Voice adds $0.05/minute on top of model billing.

Cloud tasks also consume more than local messages. Running Codex via CLI locally versus triggering cloud-based agent turns burns at different rates. Most users don't discover this distinction until they're already over the limit.

## What Plus Actually Gets: Model-by-Model

The range between Plus models is wider than it appears at first glance:

| Model | Plus Tasks (per 5-hr window) | Capability Level | Best For |
|---|---|---|---|
| GPT-6 Astra | 5–45 | Highest reasoning | Complex architecture decisions |
| GPT-6.1 Sol | 15–160 | High reasoning | Multi-file refactoring |
| GPT-6 Sol | 15–150 | High reasoning | Standard coding tasks |
| GPT-6.1 Terra | 35–285 | Mid-high | Iterative edits |
| GPT-6 Luna | 350–3,000 | Mid | High-volume simple tasks |
| GPT-5.6 Luna | 250–2,000 | Mid | Routine automation |
| GPT-5.5 | 15–80 | Lower | Legacy support |

Sources: Codex pricing page and McKelvey's 2026 limits breakdown.

The strategic read: Luna-tier models give generous task counts but lower reasoning quality. Astra-tier gives better output but tiny allowances. Plus users who want real coding horsepower are constantly making a quantity-versus-quality trade-off that Pro users ($200/month) don't face — Pro removes the 5-hour cap entirely across all models.

This approach can fail when your tasks don't map cleanly to one tier. A refactor that starts simple can escalate mid-session into something that demands Astra-level reasoning. At that point, switching models mid-task isn't seamless, and you're burning Astra allocation you hadn't planned for.

## The Luna Reserve and Mid-Task Behavior

Two mechanics worth knowing about.

First, the Luna Reserve: a secondary fallback allowance that kicks in for selected personal Plus accounts after primary limits are exhausted, granting access to GPT-5.6 Luna. The reserve size isn't published and it's unavailable on Business or Enterprise accounts. It's a safety valve, not something you can plan production workflows around.

Second, mid-task behavior. When a limit is reached during an active agent turn, the current turn completes. The system blocks the *next* instruction, not the one in progress. This matters for long-running agent sessions — you won't get cut off mid-refactor, but you won't be able to chain the next task until limits reset.

## Practical Implications

**The December pool merge demands a workflow audit now.**

Starting this December, ChatGPT Work, Codex CLI, and ChatGPT for Excel all draw from the same allowance. If you're a Plus user running ChatGPT heavily for non-coding tasks — research, drafting, analysis — that consumption now competes directly with Codex task capacity.

Three concrete scenarios and what to do about each:

**Scenario 1: You use ChatGPT for writing and Codex for code.**
Your combined usage is about to get squeezed into one pool. Run the usage dashboard for two weeks before December to get a baseline. If you're regularly hitting 60–70% of either current limit, you're likely to feel the crunch post-merge.

**Scenario 2: You run Codex in Ultrafast mode for quick iterations.**
Stop doing this on Plus. The 8x multiplier against a 5–45 task window on Astra is a budget killer. Reserve Ultrafast for tasks where the speed genuinely changes your output — not just convenience.

**Scenario 3: You're evaluating Plus versus Pro for a small engineering team.**
The math shifts at two or more engineers using Astra-tier models daily. Premium Business seats carry a 5x allowance multiplier over Standard Business, with no 5-hour cap. The $20 Business plan gets limited Astra access; the $100 Business plan gets full access with credits available for overages. At that point, the per-seat cost comparison changes significantly.

**What to watch before December 15:**
- OpenAI's official communication on exactly how the "instant chat" exemption works post-merge (currently exempt from token counting)
- Whether the Luna Reserve persists for Plus users after pool consolidation
- Any changes to the weekly cap structure — still unpublished as of November 2026

## Conclusion & Future Outlook

The data points to a clear picture:

ChatGPT Codex limits for Plus users are real and meaningful constraints, not soft suggestions. Five to 45 tasks on Astra per 5-hour window is a tight ceiling for production work. Consumption multipliers — especially the 8x Ultrafast rate — are the hidden drain most users don't account for until they're already over the limit. And the December 2026 pool consolidation is the most significant structural change for Plus users since Codex launched.

The jump from Plus to Pro isn't about feature access. It's about removing rate limits entirely on GPT-6 reasoning models.

Over the next six months, expect OpenAI to publish clearer weekly cap figures as the unified pool rolls out — user pressure will force more transparency. Credits as an add-on for Plus, already available for Astra overages, will likely expand to cover more model tiers. The open question worth tracking: whether the Luna Reserve becomes a formal, documented feature or quietly disappears post-consolidation.

This isn't always the answer, but if you're serious about using Codex in production, don't evaluate Plus limits in isolation. Run your actual usage numbers across both ChatGPT and Codex before December, then decide whether the shared pool works for your workflow or whether Pro math starts to make sense. The limits are structured, predictable, and workable — if you know where they are before you hit them.

What's your current Codex usage pattern — local CLI, cloud tasks, or mostly chat-based? The answer changes the math significantly.

## References

1. [Codex Pricing](https://chatgpt.com/codex/pricing/)
2. [Understanding ChatGPT and Codex usage limits | OpenAI Help Center](https://help.openai.com/en/articles/20001625-understanding-chatgpt-and-codex-usage-limits)
3. [Codex Usage Limits: 5-Hour Window, Weekly Cap, What Resets (2026)](https://justinmckelvey.com/blog/codex-usage-limits)


---

*Photo by [Levart_Photographer](https://unsplash.com/@siva_photography) on [Unsplash](https://unsplash.com/photos/chatgpt-interface-with-examples-and-capabilities-drwpcjkvxuU)*
