---
title: "Claude API Streaming Timeouts in Next.js Edge Runtime: Fixes"
date: 2026-04-04T19:43:14+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-web", "claude", "api", "streaming", "TypeScript"]
description: "Beat Vercel's 25-second edge runtime timeout when streaming Claude API responses in Next.js App Router with practical workarounds that keep long generations alive."
image: "/images/20260404-claude-api-streaming-response-.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "Claude", "Anthropic"]
faq:
  - question: "claude api streaming response next.js app router edge runtime timeout workaround that actually works"
    answer: "The most reliable claude api streaming response next.js app router edge runtime timeout workaround is using the ReadableStream and TransformStream pattern with proper flush intervals to keep the connection alive. Alternatively, switching your route handler to Node.js runtime by adding 'export const runtime = nodejs' removes the timeout ceiling entirely, though you lose Edge cold-start performance benefits."
  - question: "why does my Claude streaming response timeout on Vercel edge functions"
    answer: "Vercel's Edge Runtime enforces hard execution limits of 25 seconds on Pro plans and 15 seconds on Hobby plans, which is shorter than many Claude streaming responses in production. Claude 3.5 Sonnet can take 30-45 seconds to stream a 2,000-token response under normal load, causing the connection to drop before generation completes."
  - question: "next.js app router route handler edge runtime vs nodejs runtime for LLM streaming"
    answer: "Node.js runtime route handlers have no hard execution timeout ceiling, making them better suited for long-running Claude API streaming calls that can last 60+ seconds. Edge Runtime offers faster cold starts globally but is designed for short-lived tasks like auth checks and redirects, not persistent LLM streaming connections."
  - question: "how to stream Claude API response in next.js app router without timeout"
    answer: "You can avoid timeouts by either switching your route handler from Edge to Node.js runtime using 'export const runtime = nodejs', or by implementing a hybrid architecture where Edge handles routing and a separate Node.js serverless function manages the Claude streaming connection. Both approaches are valid claude api streaming response next.js app router edge runtime timeout workarounds depending on your performance requirements."
  - question: "how to connect Anthropic SDK AsyncIterable to ReadableStream in edge runtime"
    answer: "The Anthropic SDK returns streaming responses as an AsyncIterable of MessageStreamEvents, which must be explicitly bridged to the Web Streams API ReadableStream supported by Edge Runtime. Missing any step in this conversion can cause silent connection drops with no useful client-side error message, making careful stream construction essential."
aliases:
  - "/tech/2026-04-04-claude-api-streaming-response-nextjs-app-router-ed/"

---

Edge functions promised low latency and global distribution. What they didn't advertise was a hard ceiling that'll break your Claude integration in production.

Vercel's Edge Runtime enforces a maximum execution duration — 25 seconds on the Pro plan, 15 seconds on Hobby — and that limit bites hard when you're streaming long-form Claude responses. Claude 3.5 Sonnet can generate 2,000-token responses that stream for 30–45 seconds under normal load. Do the math. The default setup fails.

This isn't a fringe problem. As of Q1 2026, Claude API adoption across Next.js App Router projects has grown sharply, with Anthropic reporting developer API usage doubling year-over-year. The timeout issue is now one of the most-discussed pain points in the Next.js Discord and Anthropic's developer forums. A practical breakdown follows: what causes it, what actually fixes it, and which workaround fits your architecture.

> **Key Takeaways**
> - Vercel Edge Runtime caps execution at 25 seconds (Pro) and 15 seconds (Hobby) — shorter than many Claude streaming responses in production.
> - The `ReadableStream` + `TransformStream` pattern with proper flush intervals is the most reliable claude api streaming response next.js app router edge runtime timeout workaround for most teams.
> - Switching route handlers to Node.js runtime (`export const runtime = 'nodejs'`) eliminates the timeout ceiling but trades away Edge cold-start performance.
> - Hybrid architectures — Edge for routing, Node.js serverless for Claude streaming — offer the best of both worlds but require deliberate route segmentation.

---

## Background: Why Edge Runtime and LLM Streaming Collide

Edge Runtime was designed for speed, not longevity. It runs V8 isolates stripped of full Node.js APIs — no `fs`, no native modules, limited `fetch` behavior. The tradeoff: sub-5ms cold starts globally. For auth checks, redirects, and lightweight API transformations, it's excellent.

LLM streaming is the opposite use case. A single Claude API call via `@anthropic-ai/sdk` opens a persistent HTTP connection that stays alive until the model finishes generating. That can be 5 seconds for a short answer. It can be 60+ seconds for a detailed technical document with `max_tokens` set high.

Next.js App Router introduced Route Handlers in version 13.2 (released early 2023), making it easy to run backend logic close to route files. The default export for Route Handlers in `/app/api/` runs on Node.js unless you explicitly set `export const runtime = 'edge'`. Developers chasing performance flip that flag — and walk straight into the timeout wall.

The Anthropic SDK's streaming interface returns an `AsyncIterable<MessageStreamEvent>`. Edge Runtime supports `ReadableStream` via the Web Streams API, but bridging async iterables to web streams requires explicit construction. Miss a beat in that plumbing, and you don't just timeout — you get silent connection drops with no useful error message on the client.

The situation got more complex in mid-2025 when Vercel updated its Edge Middleware behavior, tightening memory limits to 128MB per invocation. Large Claude responses buffered incorrectly now hit memory caps before the timeout ceiling. Two failure modes. One wrong config.

---

## Main Analysis

### The Core Streaming Pattern: ReadableStream + Encoder

The foundational workaround is constructing a `ReadableStream` manually inside your Route Handler, then flushing chunks as they arrive from Claude.

```typescript
// app/api/chat/route.ts
export const runtime = 'edge';

import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export async function POST(req: Request) {
  const { messages } = await req.json();

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      const response = await client.messages.stream({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 1024,
        messages,
      });

      for await (const event of response) {
        if (
          event.type === 'content_block_delta' &&
          event.delta.type === 'text_delta'
        ) {
          controller.enqueue(encoder.encode(event.delta.text));
        }
      }

      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Transfer-Encoding': 'chunked',
      'X-Accel-Buffering': 'no',
    },
  });
}
```

The `X-Accel-Buffering: no` header matters. Without it, Vercel's CDN layer — or any nginx proxy in front — may buffer the entire response before forwarding to the client. That negates streaming entirely and can cause apparent timeouts even when the Edge function itself completes correctly.

This pattern works for responses under the Edge timeout ceiling. It doesn't solve the underlying duration limit.

### Escaping the Ceiling: Node.js Runtime Route Handlers

The cleanest fix for long-running streams: abandon Edge Runtime for that specific route.

```typescript
// app/api/chat/route.ts
export const runtime = 'nodejs'; // ← one line change
```

Node.js serverless functions on Vercel default to 10 seconds but can be configured up to 900 seconds on Pro plans via `vercel.json`:

```json
{
  "functions": {
    "app/api/chat/route.ts": {
      "maxDuration": 300
    }
  }
}
```

The cost is cold start latency. Node.js serverless functions on Vercel cold-start at 200–800ms depending on bundle size and region. For a chat interface where the first response token matters perceptually, that delay is noticeable. The Anthropic SDK adds roughly 15MB to bundle size, which keeps cold starts toward the higher end without careful tree-shaking.

### The Hybrid Architecture: Segment Your Routes

The approach that scales best: keep Edge Runtime for everything except the Claude streaming route. Route segmentation is clean in App Router — each `route.ts` file declares its own runtime independently.

```
app/
  api/
    auth/route.ts         ← runtime: 'edge' (fast, lightweight)
    search/route.ts       ← runtime: 'edge' (fast, lightweight)
    chat/
      route.ts            ← runtime: 'nodejs' (Claude streaming)
      [sessionId]/
        route.ts          ← runtime: 'nodejs' (Claude streaming)
```

This keeps 90% of API traffic on Edge with its latency benefits while routing Claude calls through Node.js serverless where timeouts aren't a ceiling problem.

### Comparison: Timeout Workaround Approaches

| Approach | Timeout Risk | Cold Start | Complexity | Cost Impact |
|---|---|---|---|---|
| Edge + ReadableStream (≤25s responses) | High for long replies | ~5ms | Low | Lowest |
| Node.js runtime (`maxDuration: 300`) | None (configurable) | 200–800ms | Low | Low–Medium |
| Hybrid (Edge routing + Node.js for Claude) | None for Claude routes | Mixed | Medium | Low–Medium |
| External streaming proxy (e.g., separate worker) | None | Variable | High | Higher |

For most teams shipping a chat feature on Next.js, the Node.js runtime switch with a configured `maxDuration` is the right answer. One config change. The cold start hit is a UX issue, not a correctness issue — and it's fixable with warmup strategies or Vercel's Fluid Compute (available on Enterprise as of Q4 2025).

The Edge + ReadableStream approach only makes sense if responses are consistently short — summarization features, single-turn Q&A with tight `max_tokens` limits — and you can guarantee they'll stay under the timeout ceiling. That's a fragile guarantee in production.

---

## Practical Implications: Scenarios and Recommendations

**Scenario 1: Chat interface with open-ended generation**
Users ask long-form questions. Responses vary from 200 to 3,000 tokens. Use the Node.js runtime route with `maxDuration: 300`. Implement a client-side typing indicator that appears immediately on POST to mask the cold start. Reduce cold start time by keeping the Claude SDK import isolated — don't bundle other heavy dependencies into the same route file.

**Scenario 2: Autocomplete or short-answer features**
Responses are capped at 150–200 tokens. Latency is critical — results need to land in under 2 seconds. Stay on Edge Runtime with the ReadableStream pattern. Set `max_tokens: 200` explicitly in every request. Monitor p95 latency in Vercel Analytics; if it creeps toward 20 seconds, lower the token limit or move to Node.js.

**Scenario 3: Background document processing**
Long documents, no real-time streaming needed. Don't use Edge or serverless at all — use Vercel's background functions or a separate worker queue. The workaround for this case is architectural: move the work out of the request-response cycle entirely.

**What to watch in the next 6 months:**
- Vercel's Fluid Compute GA release is expected mid-2026, which promises to hold function instances warm between requests — potentially cutting Node.js cold starts below 50ms.
- Anthropic's streaming API is adding server-sent events (SSE) format improvements in their SDK v1.x roadmap, which may simplify the ReadableStream bridging code.
- Next.js 15.x has signaled improvements to `maxDuration` handling in App Router Route Handlers, currently tracked in the Next.js GitHub repository under RFC discussions.

---

## Conclusion & Future Outlook

This isn't going away soon. The timeout problem is a fundamental tension between Edge Runtime's design goals and LLM streaming's requirements. But it's solvable. It just requires choosing the right tool for the job.

Edge Runtime's 15–25 second ceiling will break production Claude integrations for any non-trivial generation task. The `ReadableStream` pattern is necessary regardless of runtime — it's how you stream correctly. Node.js runtime with configured `maxDuration` is the pragmatic default for most chat and generation features. Hybrid route segmentation keeps Edge benefits everywhere else.

Expect the gap to narrow over 2026. Vercel Fluid Compute and Next.js runtime improvements will make Node.js serverless more competitive on latency. Anthropic's SDK improvements will reduce boilerplate. But today, the configuration choices above are what keep your users from staring at a spinner that never resolves.

Pick the pattern that matches your response length profile. Ship it. Then measure actual p95 streaming durations in production — not just happy-path local testing. That number tells you whether you've actually solved the problem.

## References

1. [Building a Production-Ready Claude Streaming API with Next.js Edge Runtime - DEV Community](https://dev.to/bydaewon/building-a-production-ready-claude-streaming-api-with-nextjs-edge-runtime-3e7)
2. [API Reference: Edge Runtime | Next.js](https://nextjs.org/docs/pages/api-reference/edge)


---

*Photo by [Growtika](https://unsplash.com/@growtika) on [Unsplash](https://unsplash.com/photos/a-digital-image-of-a-brain-with-the-word-change-in-it-hJUl5BAhJec)*
