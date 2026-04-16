---
title: "Vercel Serverless Function Timeout: Streaming & Queue Fixes"
date: 2026-04-16T20:27:13+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-cloud", "vercel", "serverless", "function", "TypeScript"]
description: "Hit Vercel's 10-second serverless timeout in Next.js App Router? Stream responses instead — a faster, production-ready fix for AI and async pipelines."
image: "/images/20260416-vercel-serverless-function-tim.webp"
technologies: ["TypeScript", "React", "Next.js", "Node.js", "Redis"]
faq:
  - question: "vercel serverless function timeout 10 seconds workaround streaming response nextjs app router 2025"
    answer: "The most effective workaround for Vercel's 10-second serverless function timeout in Next.js App Router is using streaming responses via the Web Streams API (ReadableStream), which keeps the connection alive without holding the function open past the limit. This approach works natively in App Router Route Handlers and is especially useful for AI features like LLM completions that typically take 15-40 seconds. For workloads exceeding even the 900-second Enterprise limit, tools like Inngest offer durable background function execution outside the request lifecycle entirely."
  - question: "how to fix vercel 10 second timeout on hobby plan nextjs api route"
    answer: "On Vercel's Hobby plan, serverless functions are hard-capped at 10 seconds, which blocks AI features, webhooks, and async pipelines from completing successfully. You can work around this by implementing streaming responses using ReadableStream in Next.js App Router Route Handlers, which avoids holding the function open for the full execution duration. Upgrading to Vercel Pro raises the limit to 60 seconds, and Enterprise extends it to 900 seconds if streaming isn't sufficient for your use case."
  - question: "nextjs app router streaming response vs pages router res.write difference"
    answer: "Next.js App Router Route Handlers use the Web Streams API (ReadableStream, TransformStream) for streaming, which is fundamentally different from the Pages Router pattern that used Node.js ServerResponse streams via res.write(). Copy-pasting Pages Router streaming code into App Router contexts will fail silently without clear error messages, which is a common source of confusion during migration. App Router's streaming approach is natively supported and works directly with React Server Components."
  - question: "does vercel edge function have longer timeout than serverless function"
    answer: "No — Vercel Edge Functions actually have a shorter or equal timeout cap compared to serverless functions depending on your plan. Edge Functions are hard-limited to 30 seconds maximum regardless of whether you're on Hobby, Pro, or Enterprise, meaning they won't rescue you from timeout issues on long-running tasks. Serverless functions on Enterprise can reach up to 900 seconds, making them the better choice for extended workloads."
  - question: "how does streaming response help with vercel serverless function timeout 10 seconds workaround nextjs app router 2025"
    answer: "Streaming responses help bypass the vercel serverless function timeout 10 seconds workaround challenge in Next.js App Router by sending data to the client incrementally rather than waiting for the full response to complete before responding. This keeps the HTTP connection alive and delivers partial results — like LLM token output — without the function needing to stay open for the entire computation. It's considered a better architectural pattern, not just a workaround, because it also improves perceived performance for end users."
---

Vercel's default serverless function timeout is 10 seconds on the Hobby plan — and it kills more production apps than most engineers expect. If you're building AI features, processing webhooks, or running any async pipeline in Next.js App Router, you've almost certainly hit this wall.

Streaming responses aren't just a workaround. They're a better architectural pattern. The problem: most documentation still points to outdated Pages Router patterns that break silently in App Router without any clear error message telling you why.

This is a data-driven look at what's actually happening with Vercel's timeout constraints in 2025-2026 — what the limits are, why streaming changes the equation, and which approach fits which use case.

---

**In brief:** Vercel's 10-second default timeout on Hobby tier blocks entire categories of modern app functionality. Streaming responses via the Web Streams API in Next.js App Router sidestep this constraint by keeping connections alive without holding a function open.

Three concrete points:
1. Vercel Hobby plan caps serverless functions at 10 seconds; Pro raises that to 60 seconds; Enterprise goes to 900 seconds — per Vercel's official documentation.
2. Next.js App Router supports streaming natively through React Server Components and `ReadableStream`, replacing the Pages Router `res.write()` pattern entirely.
3. For workloads exceeding even the 900-second limit — or requiring reliable background execution — tools like Inngest provide durable function orchestration outside the request lifecycle.

---

## Why This Problem Got Worse in 2025

Serverless functions have always had timeout limits. But two things dramatically raised the stakes over the past 18 months.

First, AI features became standard. Calling OpenAI's GPT-4o, Anthropic's Claude, or any LLM endpoint from a Next.js API route means waiting for model inference — often 15-40 seconds for longer completions. That's a direct collision with a 10-second ceiling.

Second, Next.js App Router shipped with a fundamentally different model for API routes. The old `pages/api` pattern used Node.js `ServerResponse` streams directly. App Router's Route Handlers use the Web Streams API — `ReadableStream`, `TransformStream`. Migration guides lagged behind adoption. Engineers copy-pasted Pages Router solutions into App Router contexts and wondered why nothing worked.

Vercel's own documentation (as of April 2026) confirms the tiered limits:

- **Hobby**: 10 seconds (serverless), 10 seconds (Edge)
- **Pro**: 60 seconds (serverless), 30 seconds (Edge)
- **Enterprise**: 900 seconds (serverless), 30 seconds (Edge)

Edge Functions have a hard 30-second cap regardless of plan. That matters — Edge doesn't rescue you from timeout problems on long-running tasks.

According to Inngest's engineering blog, the most common timeout failure pattern isn't a single slow function. It's chained async operations — database queries, external API calls, third-party webhooks — that each look safe individually but stack past the limit in production.

---

## The Streaming Fix: How It Actually Works in App Router

Streaming doesn't increase your timeout limit. It changes what "timeout" means in practice.

A standard serverless function holds the connection open until it returns a complete response. Exceed the limit and Vercel kills it. A streaming response starts sending data immediately and keeps the connection alive incrementally. Vercel's timeout clock still runs — but for many use cases, the first byte goes out within a second, keeping the user experience intact while the rest processes.

In Next.js App Router, a streaming Route Handler looks like this:

```ts
// app/api/stream/route.ts
export async function GET() {
  const stream = new ReadableStream({
    async start(controller) {
      const encoder = new TextEncoder();
      for await (const chunk of someLongAsyncGenerator()) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });

  return new Response(stream, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
```

No `res.write()`. No `res.end()`. The Web Streams API is native here — and that's the critical shift from Pages Router patterns that breaks most copy-pasted code.

For AI streaming specifically, Vercel's AI SDK (v3+) wraps this pattern with `StreamingTextResponse` and framework-aware helpers, cutting the boilerplate significantly.

### When Streaming Isn't Enough

Streaming solves the user-facing timeout problem. It doesn't solve background processing.

Imagine a webhook from Stripe that triggers a multi-step fulfillment pipeline: update database, send email, call a third-party inventory API, log to a data warehouse. Each step is sequential. The whole thing might take 2-3 minutes. You can't stream a response to Stripe — it expects a 200 OK within seconds and moves on.

This is where the streaming pattern breaks down. Streaming keeps the client happy; it doesn't keep long jobs alive.

The architectural answer: decouple the job from the request. Acknowledge the webhook immediately, then hand the work off to a background queue or durable function system.

---

## Background Execution: The Inngest Approach

Inngest's documented approach to Next.js timeouts treats functions as durable workflows rather than single-execution units. A function registered with Inngest can run for hours, retry on failure, and be inspected through a dashboard — none of which are available with raw serverless functions.

The integration with Next.js App Router is a Route Handler that Inngest uses as an endpoint:

```ts
// app/api/inngest/route.ts
import { serve } from "inngest/next";
import { inngest } from "@/inngest/client";
import { myLongRunningFunction } from "@/inngest/functions";

export const { GET, POST, PUT } = serve({
  client: inngest,
  functions: [myLongRunningFunction],
});
```

The function itself runs outside the HTTP request lifecycle. Vercel's timeout doesn't apply. Steps within the function have their own timeout windows, and Inngest handles retry logic automatically.

---

## Comparing Timeout Workaround Strategies

| Strategy | Timeout Limit | Streaming Support | Background Jobs | Complexity | Best For |
|---|---|---|---|---|---|
| Vercel Pro upgrade | 60s | No | No | Low | Simple API calls, most LLM completions |
| Edge Functions | 30s (hard cap) | Yes | No | Low | Ultra-fast, CPU-light tasks |
| Streaming (ReadableStream) | Plan limit, but incremental | Yes | No | Medium | AI chat, progressive rendering |
| Queue + background worker (e.g., Inngest) | Unlimited | N/A | Yes | High | Webhooks, pipelines, multi-step jobs |
| Self-hosted compute (e.g., Railway, Fly.io) | Configurable | Yes | Yes | High | Full control, cost optimization at scale |

The pattern is clear: no single approach covers every use case. Streaming handles the user-facing timeout experience. Background queues handle the processing-side timeout problem. They're complements, not substitutes.

Upgrading to Pro ($20/month as of April 2026) is the lowest-friction fix for most teams — 60 seconds covers the vast majority of LLM API calls. But if you're on Hobby or building something that genuinely runs longer, streaming plus a background worker is the production-grade answer.

---

## Practical Scenarios and Decisions

**Scenario 1: AI chat completions timing out**

The fix is streaming — specifically, streaming the LLM response token-by-token as it arrives from the model API. Vercel's AI SDK does this out of the box. The function stays within timeout limits because it's not waiting for the full completion before responding.

Concrete action: Switch from `await openai.chat.completions.create()` to the streaming variant, then pipe through `ReadableStream` in your Route Handler.

**Scenario 2: Webhook processing exceeds 10 seconds**

Streaming doesn't help here. The webhook caller — Stripe, GitHub, whoever — needs a synchronous 200 response. The fix is immediate acknowledgment plus async execution. Inngest, Trigger.dev, and QStash (from Upstash) all provide this pattern for Next.js. Trigger.dev has native TypeScript-first ergonomics; QStash is dead-simple if you're already on Upstash Redis.

Concrete action: Return 200 within the function, enqueue the payload, process in a background job.

**Scenario 3: Large file processing or data export**

Neither streaming nor short-lived background jobs are the right shape here. This is a self-hosted compute problem — or a job for Vercel Cron combined with a stateful worker on Railway or Fly.io. Vercel's serverless architecture wasn't designed for 10-minute batch jobs, and fighting that constraint costs more than accepting it.

This approach can fail when teams treat background job systems as a universal fix. Inngest and Trigger.dev add real operational overhead — dashboards to monitor, retry logic to configure, event schemas to maintain. For simple use cases, a Pro plan upgrade and a well-placed streaming response is faster and cheaper.

**What to watch:** Vercel has been expanding its compute offerings. The January 2026 announcement of longer-running function support on Enterprise points toward a future where the 60-second Pro cap may shift. Watch the Vercel changelog — the limits in the table above could change by Q3 2026.

---

## Conclusion

The timeout problem in Next.js App Router breaks down into two separate issues that need separate solutions.

> **Key Takeaways**
> - Streaming responses (via Web Streams API in App Router) address user-facing timeout symptoms without changing underlying function limits
> - Vercel's plan tiers matter: 10s → 60s → 900s — evaluate whether a Pro upgrade removes the problem entirely before adding architectural complexity
> - Background job systems (Inngest, Trigger.dev, QStash) are the right tool for webhook and pipeline workloads, not streaming
> - Edge Functions don't help with long-running tasks; the 30-second hard cap is lower than Pro serverless
> - No single pattern solves both sides — streaming and background queues are complements, not substitutes

Expect Vercel to keep expanding Enterprise limits, with possible trickle-down to Pro over the next 6-12 months. The AI SDK team has been shipping streaming helpers fast — the ergonomics of streaming in App Router will keep improving. Background job providers are consolidating features quickly; Inngest and Trigger.dev both shipped major workflow versioning features in early 2026.

The clearest action: audit your current App Router API routes. Which ones have async chains that could exceed 10 seconds under load? Those are your risk spots. Fix the user-facing ones with streaming. Fix the background ones with a queue. Don't try to make one pattern do both jobs — that's where production incidents come from.

---

*References: [Vercel Functions Limitations](https://vercel.com/docs/functions/limitations) | [Inngest: How to Solve Next.js Timeouts](https://www.inngest.com/blog/how-to-solve-nextjs-timeouts)*

## References

1. [How to solve Next.js timeouts - Inngest Blog](https://www.inngest.com/blog/how-to-solve-nextjs-timeouts)
2. [Vercel Functions Limits](https://vercel.com/docs/functions/limitations)


---

*Photo by [Conny Schneider](https://unsplash.com/@choys_) on [Unsplash](https://unsplash.com/photos/a-blue-background-with-lines-and-dots-xuTJZ7uD7PI)*
