---
title: "Claude API Streaming Response Next.js App Router Edge Runtime Timeout Fix"
date: 2026-03-27T20:01:59+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "claude", "api", "streaming", "TypeScript"]
description: "Fix Claude API streaming timeouts in Next.js App Router: edge runtime kills requests at exactly 10s on Vercel — here's why and how to configure around it."
image: "/images/20260327-claude-api-streaming-response-.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "AWS", "Claude"]
faq:
  - question: "Claude API streaming response Next.js App Router edge runtime timeout fix"
    answer: "The fix is to switch from the edge runtime to the Node.js runtime by adding `export const runtime = 'nodejs'` to your route handler and using the Web Streams API with ReadableStream for streaming responses. Vercel's edge runtime enforces a hard 10-second timeout that kills long-running Claude API streams, while the Node.js serverless runtime allows up to 60 seconds on Pro plans and 900 seconds on Enterprise."
  - question: "why does my Claude API streaming stop at 10 seconds on Vercel"
    answer: "Your request is hitting Vercel's edge runtime hard timeout, which terminates all connections at exactly 10 seconds with no error message sent to the client. This happens when your Next.js route handler has `export const runtime = 'edge'` set, either explicitly or inherited from middleware configuration."
  - question: "Next.js App Router edge runtime vs nodejs runtime for AI streaming"
    answer: "For AI streaming use cases like Claude API, the Node.js runtime is the correct choice because it supports longer execution times and full Node.js APIs. The edge runtime is better suited for fast, simple API proxies under 10 seconds, not LLM responses that commonly take 30–90 seconds in production."
  - question: "how to stream Claude API response in Next.js App Router route handler"
    answer: "Use a ReadableStream with TransformStream inside a Next.js App Router route handler, and ensure you have `export const runtime = 'nodejs'` set in the file. This pattern, combined with the Node.js runtime, is the recommended approach for Claude API streaming in Next.js App Router as of 2026."
  - question: "Vercel serverless function timeout limit for AI chatbot Next.js"
    answer: "Vercel's timeout limits vary by plan: 10 seconds on Hobby, 60 seconds on Pro, and up to 900 seconds on Enterprise for Node.js serverless functions. The Claude API streaming response Next.js App Router edge runtime timeout fix requires upgrading from the Hobby plan if your prompts consistently need more than 10 seconds to complete."
---

Your Claude API streaming works flawlessly on localhost. You push to Vercel. Requests start dying at exactly 10 seconds. That's not a coincidence — it's the edge runtime timeout, and it catches nearly every team building AI features in Next.js App Router for the first time.

This piece breaks down why it happens, how the underlying architecture creates the problem, and the specific configuration changes that actually fix it.

> **Key Takeaways**
> - Vercel's edge runtime enforces a hard 10-second execution timeout. Claude API streaming responses routinely exceed this for complex prompts — 30–90 seconds is common in production.
> - Next.js App Router defaults route handlers to Node.js runtime, but many teams explicitly set `runtime = 'edge'` for perceived latency benefits, inadvertently triggering timeout failures.
> - Switching to Node.js runtime with `export const runtime = 'nodejs'` and enabling response streaming via the Web Streams API resolves the timeout for the vast majority of deployments.
> - The Vercel Pro plan raises the Node.js serverless function timeout to 60 seconds; Enterprise allows up to 900 seconds — critical data points when choosing deployment tiers.
> - `ReadableStream` with `TransformStream` in App Router route handlers is the correct pattern for Claude API streaming in Next.js App Router as of 2026.

---

## The Architecture Problem Nobody Warns You About

Next.js App Router ships with two distinct execution environments: the Node.js runtime and the edge runtime. They are not interchangeable.

The edge runtime runs on V8 isolates — Vercel uses Cloudflare's infrastructure for this layer — which means no Node.js APIs, limited CPU time, and a hard 10-second wall clock timeout. No exceptions.

The Node.js serverless runtime is different. According to [Vercel's official platform documentation](https://vercel.com/docs/functions/runtimes), the default timeout for serverless functions is 10 seconds on the Hobby plan, 60 seconds on Pro, and configurable up to 900 seconds on Enterprise.

The failure mode plays out predictably. A route handler tagged with `export const runtime = 'edge'` starts streaming from Claude's API. The first tokens arrive in 1–2 seconds. The stream looks healthy. At second 10, Vercel's edge network terminates the connection — mid-response, no error message to the client, just a truncated stream or a hanging request.

Teams spend hours debugging this. The Claude API itself is working fine. The problem lives entirely in the deployment layer.

---

## Why Teams End Up on Edge Runtime Accidentally

Two paths lead to this misconfiguration.

**Path 1: Following outdated tutorials.** A significant number of Next.js AI integration guides written in 2024 recommended `runtime = 'edge'` for lower cold start latency. That advice made sense for simple, fast API proxies. It does not hold for LLM streaming, where response time is measured in tens of seconds, not milliseconds.

**Path 2: Copying middleware configuration.** Middleware in Next.js *always* runs on the edge runtime — that's non-negotiable. Teams sometimes copy the runtime export from middleware files into route handlers without realizing they've opted into a 10-second ceiling for their AI responses.

The confusion compounds because `runtime = 'edge'` in a route handler and in middleware look syntactically identical. In middleware, it's a constraint. In a route handler, it's a choice — and usually the wrong one.

---

## The Fix: Runtime Switch + Proper Streaming Pattern

### Step 1: Change the Runtime Declaration

In your route handler (`app/api/chat/route.ts` or similar), set:

```typescript
export const runtime = 'nodejs';
export const maxDuration = 60; // seconds — Pro plan max
```

Remove any `export const runtime = 'edge'` line. If there's no runtime export at all, App Router defaults to Node.js, so you may not need to add anything — but being explicit prevents future accidents.

### Step 2: Implement Web Streams Correctly

The Claude API client (`@anthropic-ai/sdk`) supports streaming via `.stream()`. The correct pattern for App Router uses `ReadableStream` from the Web Streams API, which Node.js 18+ supports natively:

```typescript
import Anthropic from '@anthropic-ai/sdk';
import { NextRequest } from 'next/server';

const client = new Anthropic();

export async function POST(req: NextRequest) {
  const { prompt } = await req.json();

  const stream = new ReadableStream({
    async start(controller) {
      const anthropicStream = await client.messages.stream({
        model: 'claude-opus-4-5',
        max_tokens: 1024,
        messages: [{ role: 'user', content: prompt }],
      });

      for await (const chunk of anthropicStream) {
        if (
          chunk.type === 'content_block_delta' &&
          chunk.delta.type === 'text_delta'
        ) {
          controller.enqueue(new TextEncoder().encode(chunk.delta.text));
        }
      }
      controller.close();
    },
  });

  return new Response(stream, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
```

The stream stays open, tokens flow to the client incrementally, and the 60-second Node.js timeout gives Claude enough runway for complex completions.

### Edge vs. Node.js Runtime for AI Streaming

| Criteria | Edge Runtime | Node.js Serverless |
|---|---|---|
| Max timeout (Vercel Pro) | 10 seconds | 60 seconds |
| Cold start latency | ~50ms | 250–500ms |
| Node.js API support | ❌ Limited | ✅ Full |
| Streaming support | Partial | ✅ Full Web Streams |
| Suitable for Claude streaming | ❌ No | ✅ Yes |
| Max timeout (Enterprise) | 10 seconds | 900 seconds |
| Best for | Auth checks, redirects | LLM responses, file processing |

The cold start difference — 50ms versus roughly 350ms — sounds significant until you remember that Claude responses take 15–45 seconds for anything non-trivial. That edge runtime speed advantage gets completely swamped by actual response duration. You're optimizing the wrong variable.

---

## Practical Deployment Scenarios

**Scenario 1: Short summarization tasks (typically under 8 seconds)**

Edge runtime *could* work here, but it's fragile. One slow Claude response under load and requests start dying. Node.js runtime is the right call even for fast tasks — the downside risk isn't worth the marginal cold start improvement.

**Scenario 2: Multi-turn chat with large context windows**

Responses regularly hit 30–60 seconds. Node.js runtime on Vercel Pro (60-second max) is the minimum viable configuration. For production workloads with p95 response times above 45 seconds, you need Enterprise-tier timeouts or a self-hosted deployment without the Vercel constraint entirely.

**Scenario 3: Document analysis or code generation**

Responses can reach 90+ seconds for complex tasks. Vercel's 60-second Pro ceiling becomes the bottleneck. Two options: switch to a container-based deployment — Fly.io, Railway, or AWS ECS — where you control timeouts directly, or break the task into smaller streaming chunks with a progress pattern on the frontend.

The runtime fix works cleanly for scenarios 1 and 2. Scenario 3 requires rethinking the deployment target, not just the runtime configuration. This approach can fail when task complexity consistently pushes past 60 seconds — no amount of configuration tuning on Vercel Pro will save you there.

---

## What to Expect in the Next 6–12 Months

The edge runtime timeout issue is well-documented enough that Vercel will likely address it more directly. A few things worth tracking:

**Vercel's AI Gateway product** (in beta as of Q1 2026) promises managed streaming with extended timeouts — potentially removing the need for custom route handler patterns entirely.

**Anthropic's streaming API** continues to evolve. The `claude-opus-4-5` model's median time-to-first-token has dropped measurably since mid-2025, which improves edge runtime viability for short prompts specifically.

**Next.js 15.x** is adding more granular timeout controls per-route, expected to land in Q2–Q3 2026 based on the open RFC.

---

Four things worth locking in before you ship anything:

- Edge runtime is wrong for LLM streaming. Node.js runtime is right. This isn't a close call.
- `export const maxDuration = 60` is required on Vercel Pro. Without it, you get the 10-second default even on Node.js runtime.
- Web Streams API (`ReadableStream`) is the correct abstraction. Node.js `stream.Readable` doesn't map cleanly to Next.js App Router's response model.
- Container deployments remove the timeout ceiling entirely for long-running tasks — worth the added operational complexity if your use case demands it.

The fix takes about 10 minutes once you know what's wrong. The hard part is diagnosing that the edge runtime is the culprit in the first place.

Now you know where to look.

## References

1. [Routing: API Routes | Next.js](https://nextjs.org/docs/pages/building-your-application/routing/api-routes)
2. [How to Fix 'API Route' Timeout Errors in Next.js](https://oneuptime.com/blog/post/2026-01-24-fix-api-route-timeout-errors-nextjs/view)


---

*Photo by [Vitaly Gariev](https://unsplash.com/@silverkblack) on [Unsplash](https://unsplash.com/photos/beekeeper-in-yellow-suit-holding-honeycomb-frame-zU54lfe2d3I)*
