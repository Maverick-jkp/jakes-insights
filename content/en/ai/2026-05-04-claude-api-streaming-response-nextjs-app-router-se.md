---
title: "Claude API Streaming in Next.js App Router With Cost Per Token Tracking"
date: 2026-05-04T20:53:35+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "claude", "api", "streaming", "React"]
description: "Track real-time Claude API streaming costs in Next.js App Router Server Components — avoid billing surprises before token charges silently compound at scale."
image: "/images/20260504-claude-api-streaming-response-.webp"
technologies: ["React", "Next.js", "Node.js", "Claude", "Anthropic"]
faq:
  - question: "how to implement claude api streaming response nextjs app router server component cost per token tracker"
    answer: "To implement a Claude API streaming response in Next.js App Router with cost-per-token tracking, you should use a Route Handler (app/api/route.ts) that returns a ReadableStream rather than calling the API directly from a Server Component. Build your cost-per-token tracker at the middleware layer to capture Anthropic's usage metadata — including input_tokens and output_tokens — before the stream closes, ensuring accurate per-request billing attribution."
  - question: "why does nextjs app router break claude streaming responses"
    answer: "Next.js App Router Server Components render once and flush, meaning they don't handle streaming the same way Edge Functions do, which can cause buffered responses instead of progressive text delivery. Next.js 15's stable App Router introduced additional caching behavior that can silently buffer streamed responses, breaking token attribution and causing billing metadata to be lost if the component finishes rendering before the stream closes."
  - question: "how much does claude api cost per token for streaming in production"
    answer: "As of May 2026, Claude 3.5 Sonnet costs $3.00 per million input tokens and $15.00 per million output tokens, with output tokens being the dominant cost driver in streaming scenarios. At scale, unattributed output token costs from poorly architected streaming implementations can reach hundreds of dollars per day, making accurate per-token tracking a critical production concern."
  - question: "how to track anthropic api token usage in nextjs route handlers"
    answer: "Anthropic's API returns usage metadata — including input_tokens, output_tokens, cache_read_input_tokens, and cache_creation_input_tokens — at the end of each stream, which must be captured before the stream closes. The most reliable approach is building a cost tracker at the middleware layer rather than the component layer, so token attribution logic isn't duplicated across routes and metadata is never lost due to early component rendering."
  - question: "does prompt caching reduce claude api streaming costs"
    answer: "Yes, prompt caching on Claude 3.5 Sonnet and Claude 3 Haiku can reduce repeat-context input token costs by up to 90%, according to Anthropic's official documentation. This makes caching a high-impact optimization for streaming applications that frequently send similar system prompts or context, and the savings are trackable via the cache_read_input_tokens field in Anthropic's usage metadata."
---

Streaming LLM responses in production sounds straightforward. It isn't.

Add Next.js App Router's Server Components, Anthropic's token-based billing, and real-time cost attribution — and you've got a genuinely tricky engineering problem that most tutorials skip past entirely. A poorly architected implementation doesn't just create technical debt. It creates billing surprises. At scale, we're talking hundreds of dollars per day in unattributed output token costs.

This breaks down what a production-grade Claude API streaming setup in Next.js App Router actually looks like, what the data shows about cost at scale, and how to architect it without surprises on your billing dashboard.

---

> **Key Takeaways**
> - Claude 3.5 Sonnet costs $3.00 per million input tokens and $15.00 per million output tokens as of May 2026, per ClaudeAPIPricing.com — output tokens are the dominant cost driver in streaming scenarios.
> - Next.js App Router's Server Components don't handle streaming the same way Edge Functions do; the wrong rendering model adds latency and breaks token attribution.
> - A cost-per-token tracker built at the middleware layer — not the component layer — gives accurate per-request attribution without duplicating logic across routes.
> - Prompt caching on Claude 3.5 Sonnet and Claude 3 Haiku can cut repeat-context input costs by up to 90%, per Anthropic's official documentation.

---

## Why This Problem Got Hard in 2026

A year ago, most Claude integrations used simple `fetch` + `await` patterns. One request, one response, one bill line item. Clean.

App Router changed the rules. React Server Components run on the server, but they're not Edge Functions. They don't stream the same way. `ReadableStream` handling, `TransformStream` chaining, and Suspense boundaries all interact in ways that break naive streaming implementations. Next.js 15's stable App Router — released late 2025 — introduced additional caching behavior that can silently buffer streamed responses. That's exactly what you don't want when you're paying per output token and trying to show users progressive text.

The cost visibility problem runs parallel. Anthropic's API returns `usage` metadata — `input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens` — at the end of each stream. But if your Server Component finishes rendering before the stream closes, that metadata never reaches your logging layer. You end up with usage you can't attribute.

Teams that handle this well treat token tracking as a first-class infrastructure concern, not a `console.log` afterthought.

---

## The Streaming Architecture That Actually Works

The core issue with a Claude API streaming setup in Next.js App Router is where you put the stream handler. Server Components can't be async in the traditional Express sense — they render once and flush. For real streaming, you need a Route Handler (`app/api/route.ts`) returning a `ReadableStream`, not a Server Component directly calling `Anthropic.messages.stream()`.

The pattern that works in production:

1. **Route Handler** at `app/api/chat/route.ts` opens the Anthropic stream using the official `@anthropic-ai/sdk` Node SDK
2. A `TransformStream` intercepts chunks, extracts token metadata from the final `message_stop` event, and logs it before passing data downstream
3. The Server Component fetches from this route and passes the stream to a Client Component via Suspense

According to the TechEduByte production implementation guide, running the stream handler at the Edge runtime — add `export const runtime = 'edge'` to your route — cuts cold start latency by roughly 60% compared to Node.js serverless. For a cost-per-token tracker, Edge also means lower Vercel compute costs on the infrastructure side, not just on the Anthropic API bill.

This approach can fail when your system prompt exceeds Edge runtime memory limits or when you're using Node-only SDK features. In those cases, stay on the Node runtime and accept the cold start tradeoff.

---

## Token Cost Reality at Scale

The numbers matter more than most teams realize early on.

According to ClaudeAPIPricing.com (May 2026):

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Context Window |
|---|---|---|---|
| Claude 3.5 Sonnet | $3.00 | $15.00 | 200K |
| Claude 3.5 Haiku | $0.80 | $4.00 | 200K |
| Claude 3 Opus | $15.00 | $75.00 | 200K |
| Claude 3 Haiku | $0.25 | $1.25 | 200K |

Output tokens cost 5x input tokens on Sonnet. That ratio holds across the entire model lineup. For a streaming chat interface where users ask open-ended questions and expect detailed answers, average responses can hit 800–1,200 output tokens per turn. At 10,000 requests per day on Sonnet, that's $120–$180/day in output costs alone — before counting input.

A cost-per-token tracker that surfaces this per-user, per-session, or per-feature is the difference between a product that scales and one that quietly burns cash.

---

## Building the Cost Attribution Layer

The tracker needs to live in the stream transform, not in React state.

When Anthropic's streaming SDK emits a `message_delta` event, the `usage` field contains cumulative token counts. On `message_stop`, you get the final totals. Capture those in your `TransformStream`'s `flush()` method and POST them to a logging endpoint before closing.

What to log per request:
- `session_id` (user or anonymous)
- `model` (critical — don't assume)
- `input_tokens`, `output_tokens`
- `cache_read_input_tokens` (billed at 10% of normal input cost)
- Calculated cost in USD — compute at log time, not query time
- Route or feature identifier

Store this in Postgres or ClickHouse. ClickHouse handles high-frequency append-only writes better for real-time dashboards. A simple Postgres table works fine under roughly 50K daily requests.

---

## Prompt Caching: The Cost Variable Most Teams Miss

Claude 3.5 Sonnet and Claude 3 Haiku both support prompt caching. Per Anthropic's official documentation, cache hits on input tokens are billed at $0.30 per million on Sonnet — versus $3.00 normal — a 90% reduction.

For a streaming app with a large system prompt (documentation context, product knowledge base, persona instructions), caching the system prompt is the single highest-ROI optimization available. A 4,000-token system prompt repeated across 10,000 daily requests costs $120/day uncached on Sonnet. Cached: $12/day.

Your tracker should log `cache_read_input_tokens` separately. Without it, average cost-per-request calculations are wrong — often by a factor of 3–5x for content-heavy applications.

---

## Three Scenarios Worth Planning For

**Early-stage SaaS with a free tier.** Running Claude 3.5 Haiku to keep costs down. The tracker matters because you need a hard token budget per free user. Implement a middleware check before the Anthropic call: if the user's 30-day token total exceeds your threshold, return a 402 before ever opening a stream. This prevents a single heavy user from distorting your unit economics.

**Enterprise feature with per-department billing.** A `department_id` header flows through to the Route Handler and gets logged with every token event. Finance pulls a monthly report. Straightforward to implement, but almost nobody sets it up before their first billing conversation with a department head. Set it up on day one.

**Multi-model routing.** Some queries go to Haiku (simple lookups), others to Sonnet (complex reasoning). The router decides at request time. Your tracker must capture which model was actually used — not which model was configured as default. Log the model from the stream's `message_start` event, not from your config file.

One thing worth monitoring: Anthropic is expanding prompt caching to more models throughout 2026. When Opus gets full caching support, the cost calculus for complex reasoning tasks shifts significantly. Track the Anthropic changelog.

---

## What to Build First

The pieces connect directly:

- **Architecture**: Route Handlers with Edge runtime handle the Claude streaming pattern cleanly; Server Components alone cannot
- **Cost**: Output tokens dominate spending — Sonnet's 5:1 output/input price ratio means your tracker must weight them correctly
- **Caching**: Prompt cache hits at 10% cost are invisible without explicit tracking, and they represent your biggest savings lever
- **Attribution**: Build the logging layer into the stream transform, not the UI layer

Over the next 6–12 months, expect Anthropic to release more granular usage APIs and potentially real-time cost webhooks. Next.js will likely add first-class streaming primitives that reduce the Route Handler boilerplate currently required. Both changes will make cost tracking easier to maintain — but the architectural decisions made today still determine whether your cost data is accurate when you actually need it.

Start with the stream transform logger. Everything else is a dashboard built on top of good data.

---

*References: [ClaudeAPIPricing.com](https://claudeapipricing.com/) (May 2026 pricing data) | [TechEduByte — Claude Streaming API with Next.js Edge](https://www.techedubyte.com/claude-streaming-api-nextjs-edge-guide/) | [Anthropic Official Docs — Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)*

## References

1. [Claude Streaming API with Next.js Edge: Production-Ready Implementation Guide - Tech Edu Byte](https://www.techedubyte.com/claude-streaming-api-nextjs-edge-guide/)
2. [Claude API Pricing: Per-Token Costs for Every Model (2026) - ClaudeAPIPricing.com](https://claudeapipricing.com/)
3. [Claude Code Pricing: Subscriptions vs API, Token Visibility, and the Models That Actually Work](https://www.productcompass.pm/p/claude-code-pricing)


---

*Photo by [Bernd 📷 Dittrich](https://unsplash.com/@hdbernd) on [Unsplash](https://unsplash.com/photos/a-pixelated-orange-character-with-a-hat-GPPbPWwTHdg)*
