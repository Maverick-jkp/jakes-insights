---
title: "Anthropic and OpenAI Hit Real Revenue, Developer Lock-In Grows"
date: 2026-05-28T22:55:00+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-ai", "anthropic", "openai", "product-market", "AWS"]
description: "Anthropic and OpenAI now generate billions in recurring revenue. Here's what real developer dependency risk looks like when lock-in stops being theoretical."
image: "/images/20260528-anthropic-openai-productmarket.webp"
technologies: ["AWS", "Azure", "Claude", "GPT", "OpenAI"]
faq:
  - question: "what is developer dependency risk when building on Anthropic or OpenAI APIs"
    answer: "Developer dependency risk refers to the switching costs and structural lock-in that occur when production applications are deeply integrated with a single AI provider like Anthropic or OpenAI. Once Claude or GPT-4o is embedded in production pipelines through prompt engineering and fine-tuning layers, migrating to a different provider typically requires a 3–6 month re-architecture effort. This mirrors historical SaaS lock-in patterns seen with platforms like AWS and Stripe."
  - question: "have Anthropic and OpenAI actually achieved product market fit"
    answer: "According to analyst Simon Willison's May 2026 analysis, both Anthropic and OpenAI have genuinely crossed the product-market fit threshold, driven by deep workflow integration rather than consumer hype. Anthropic's annualized revenue grew approximately 6x in 12 months to over $2 billion, while OpenAI surpassed $3.4 billion in annualized revenue by early 2026. These numbers reflect real enterprise demand and critical infrastructure status, not experimental API usage."
  - question: "Anthropic OpenAI product-market fit developer dependency risk how to protect your engineering team"
    answer: "Engineering teams can hedge against Anthropic OpenAI product-market fit developer dependency risk by implementing multi-provider abstraction layers and model-agnostic frameworks that avoid hard-coding to a single provider's API. However, these hedging strategies carry real performance and cost trade-offs that most teams underestimate. Evaluating these trade-offs early in architecture decisions is far less costly than attempting migration after deep production integration."
  - question: "how fast is Anthropic revenue growing in 2025 2026"
    answer: "Anthropic's annualized revenue grew from approximately $300 million at the end of 2024 to over $2 billion in early 2026, representing roughly 6x growth in 12 months according to Sacra's tracking data. This growth trajectory signals genuine enterprise demand rather than experimental usage. The company also raised over $10 billion across multiple funding rounds between 2023 and 2025, reflecting strong investor confidence in retention and expansion revenue."
  - question: "Anthropic OpenAI product-market fit developer dependency risk is building on one AI API too risky"
    answer: "Building exclusively on a single AI provider's API carries measurable risk because switching costs compound quickly once integrations reach the prompt engineering and fine-tuning layers, with migration typically taking 3–6 months. Both Anthropic and OpenAI have transitioned from experimental tools to critical infrastructure for thousands of production applications, making dependency a live strategic concern rather than a theoretical one. Teams should weigh this lock-in risk against the performance and cost trade-offs of maintaining multi-provider flexibility."
---

Two AI companies are now generating billions in recurring revenue. That changes everything.

For three years, the AI industry ran on hype and venture capital. Now Anthropic and OpenAI are posting numbers that look like real SaaS businesses — and that shift raises a harder question: what happens when developers and enterprises are genuinely locked in?

The product-market fit and developer dependency risk question isn't theoretical anymore. It's a live strategic problem for every engineering team building on these APIs today.

- Anthropic's annualized revenue crossed $2 billion in early 2026, up from roughly $300 million at end of 2024, according to Sacra's tracking data.
- OpenAI reportedly surpassed $3.4 billion in annualized revenue by early 2026, driven heavily by API and enterprise contracts.
- Simon Willison's May 2026 analysis argues both companies have genuinely crossed the product-market fit threshold — not through consumer hype, but through deep workflow integration.
- Developer dependency risk is now the dominant strategic concern: once Claude or GPT-4o is embedded in production pipelines, switching costs compound fast.

> **Key Takeaways**
> - Anthropic's revenue grew approximately 6x in 12 months — a trajectory that signals genuine enterprise demand rather than experimental API usage, according to Sacra's 2026 data.
> - Both Anthropic and OpenAI have shifted from "AI curiosity" to critical infrastructure status for thousands of production applications, creating measurable switching costs.
> - The developer dependency dynamic mirrors historical SaaS lock-in patterns — think AWS in 2012, Stripe in 2016 — where early convenience calcified into structural dependency.
> - Developers building on a single provider's API today face a 3–6 month re-architecture effort to migrate, based on typical integration depth at the prompt engineering and fine-tuning layers.
> - Hedging strategies exist — multi-provider abstraction layers, model-agnostic frameworks — but they carry real performance and cost trade-offs that most teams underestimate.

---

## From Experiment to Infrastructure

Twelve months ago, most enterprise AI usage was exploratory. Proof-of-concepts, internal demos, the occasional chatbot. Budget owners treated AI API spend like a research line item — discretionary, not mission-critical.

That's changed. Anthropic's funding trajectory tells part of the story: the company raised $7.3 billion across its Series C and D rounds (2023–2024), then secured an additional $3.5 billion in early 2025, according to Sacra. Investors don't write checks that size without evidence of real retention and expansion revenue.

OpenAI's path is parallel but faster. Consumer products like ChatGPT drove initial scale, but the API business — powering everything from legal research tools to code review platforms — became the durable revenue engine. By Q1 2026, enterprise and API revenue represented the majority of OpenAI's reported $3.4 billion run rate.

Simon Willison's May 2026 piece at simonwillison.net puts it plainly: product-market fit in AI isn't about people *liking* the chatbot. It's about teams *restructuring workflows* around it. That's the signal. And both companies now have thousands of engineering teams that have done exactly that.

The dependency problem emerged specifically from this transition. When AI was a nice-to-have, switching providers was academic. Now it's an architectural decision with real consequences.

---

## The Revenue Numbers Signal Real Retention

Product-market fit has a specific meaning in SaaS: customers expand usage over time instead of churning. Vanity metrics — signups, free tier users — don't count. Expansion revenue does.

Anthropic's 6x revenue growth in 12 months (Sacra, 2026) isn't explained by new customer acquisition alone. That trajectory requires existing customers increasing their API spend, embedding Claude deeper into production systems, and renewing enterprise contracts. That's retention and expansion — the PMF signal.

OpenAI shows the same pattern. The $3.4 billion annualized run rate in early 2026 reflects customers who started with small API experiments and grew into large committed contracts. GitHub Copilot — built on OpenAI models — crossed 1.8 million paid subscribers by late 2025, according to Microsoft's earnings reports. That's a downstream dependency chain: developers depend on Copilot, Copilot depends on OpenAI. Remove the middle layer and the dependency becomes direct.

---

## How Dependency Actually Accumulates

Developers don't plan to get locked in. It happens incrementally.

Stage one: a team writes a few prompts against the Anthropic API. Low commitment. Stage two: those prompts get tuned specifically for Claude's behavior — its context window handling, its instruction-following quirks, its response formatting tendencies. Stage three: the application's UX gets designed around Claude's specific output patterns. Stage four: the company builds internal tooling that assumes Claude's API contract.

By stage four, switching isn't a weekend project. It's a quarter-long re-architecture. The dependency isn't just technical — it's organizational. Teams have trained intuitions around specific model behaviors. Documentation references specific prompting patterns. On-call runbooks assume specific failure modes. That's where dependency risk becomes genuinely expensive.

---

## The Switching Cost Calculus

Migrating from Claude to GPT-4o (or vice versa) sounds straightforward — they're both LLM APIs. It isn't.

Model behavior diverges at the margins in ways that break production systems. Claude's handling of long-context documents differs from GPT-4o's. System prompt interpretation varies. Output formatting defaults differ. JSON mode implementations have subtle inconsistencies. Any team that's run A/B tests across providers knows exactly how quickly those differences surface in production.

---

## Provider Comparison: Strategic Risk Profile

| Dimension | Anthropic (Claude) | OpenAI (GPT-4o) |
|---|---|---|
| 2026 ARR (est.) | ~$2B (Sacra) | ~$3.4B (reported) |
| Primary strength | Long context, instruction-following | Ecosystem breadth, multimodal |
| Enterprise contracts | Strong (AWS partnership) | Strong (Microsoft/Azure) |
| Cloud lock-in risk | High via AWS Bedrock | High via Azure OpenAI |
| Model switching cost | High (prompt re-tuning) | High (behavior differences) |
| Abstraction layer support | LangChain, LiteLLM | LangChain, LiteLLM |
| Pricing predictability | Moderate | Moderate |
| **Best for** | Document-heavy, complex reasoning | Broad integrations, existing Azure infra |

Both options carry meaningful dependency risk. The cloud partnerships amplify it: if you're running Claude through AWS Bedrock, you've layered AWS dependency on top of Anthropic dependency. Same dynamic applies to Azure OpenAI Service.

The abstraction layer argument — use LangChain or LiteLLM to stay provider-agnostic — is real but oversold. These frameworks add latency, reduce access to provider-specific features, and require maintenance overhead. Teams that adopted them in 2024 often found themselves maintaining two codepaths anyway when one provider released a capability the other lacked. It helps. It doesn't solve the problem.

---

## What Engineering Teams Should Actually Do

The core challenge: you need to ship products today using the best available models, but every integration decision incrementally increases switching costs. Waiting for a "safe" time to commit doesn't exist — the market won't pause.

**Greenfield application, no existing AI dependency.**
Document your prompt logic separately from your application logic from day one. Use a provider-agnostic data format for storing completions and evaluations. This doesn't eliminate dependency, but it makes auditing your switching costs dramatically easier. Treat your system prompts as first-class artifacts with version control.

**Existing production system built on one provider.**
Run a shadow evaluation monthly. Pick a representative sample of 500–1,000 production inputs and run them through a competing model. Track divergence. This tells you exactly how brittle your provider dependency has become — and it builds organizational muscle for migration if pricing or availability forces the issue.

**Enterprise procurement decision.**
Negotiate data portability and API contract stability clauses. Both Anthropic and OpenAI have enterprise sales teams that will negotiate on these points. Get commitments on deprecation timelines. Historically, OpenAI has deprecated model versions with 6–12 months notice — build that assumption into your architecture lifecycle planning.

**Watch these developments in the next 6 months:**
- Anthropic's Claude 4 release timeline and whether it introduces breaking API changes
- OpenAI's continued Azure integration depth — pricing changes on Azure OpenAI Service would cascade to thousands of enterprise deployments
- Open-source model performance (Llama 4, Mistral's enterprise tier) closing the capability gap, which would change the switching cost calculus significantly

---

## Where This Is Heading

The data makes the conclusion hard to avoid. Both Anthropic and OpenAI have crossed into genuine product-market fit — not as consumer apps, but as infrastructure. The revenue trajectories confirm it. The workflow integration depth confirms it.

That's genuinely good news for AI capability advancement. It's a real risk for teams that haven't thought carefully about the dependency embedded in their stack.

Switching costs compound at the prompt, workflow, and organizational layers simultaneously. Cloud partnerships multiply the dependency surface area. And abstraction layers, while useful, don't eliminate the underlying exposure — model behavior divergence is real and it will catch teams off guard.

In the next 6–12 months, expect open-source models to become a more credible alternative as Llama 4 and similar models narrow the performance gap on specific tasks. That won't eliminate dependency risk for teams already deep in a provider's ecosystem, but it will shift the negotiating dynamics.

The one mindset shift worth making now: treat your AI provider relationship the way you'd treat any critical infrastructure vendor. Audit your switching costs quarterly. Keep a shadow evaluation pipeline running. Dependency isn't inherently bad — *unexamined* dependency is how teams get caught flat-footed when pricing changes or a provider pivots.

So ask yourself this: if your primary AI provider doubled API pricing next quarter, what's your plan? If that question doesn't have a clear answer, that's the gap worth closing first.

## References

1. [I think Anthropic and OpenAI have found product-market fit](https://simonwillison.net/2026/May/27/product-market-fit/)
2. [I think Anthropic and OpenAI have found product-market fit | Hacker News](https://news.ycombinator.com/item?id=48296794)
3. [Anthropic revenue, valuation & funding | Sacra](https://sacra.com/c/anthropic/)


---

*Photo by [Igor Omilaev](https://unsplash.com/@omilaev) on [Unsplash](https://unsplash.com/photos/a-computer-chip-with-the-letter-a-on-top-of-it-eGGFZ5X2LnA)*
