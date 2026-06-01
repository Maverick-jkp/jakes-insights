---
title: "Claude API Streaming Response Next.js 14 App Router Edge Function Timeout Fix"
date: 2026-05-20T21:29:11+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-web", "claude", "api", "streaming", "TypeScript"]
description: "Fix Claude API streaming timeouts in Next.js 14 App Router edge functions. Silent failures and partial completions have a straightforward solution."
image: "/images/20260520-claude-api-streaming-response-.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "Claude", "Anthropic"]
faq:
  - question: "Claude API streaming response Next.js 14 app router edge function timeout fix - what is it?"
    answer: "The Claude API streaming response Next.js 14 app router edge function timeout fix refers to solving silent failures and truncated responses that occur when streaming long Claude AI outputs through Vercel's Edge Runtime, which enforces a hard 25-second wall-clock limit. The core fix involves switching from the Edge Runtime to the Node.js runtime for AI route handlers using an explicit runtime export in your Next.js 14 App Router project. Additional mitigations address idle stream timeouts, which are a separate failure mode that drops connections when no bytes are written for 10-15 seconds."
  - question: "why does my Claude API streaming stop halfway through in Next.js app router"
    answer: "Your Claude API stream is likely stopping mid-response because Vercel's Edge Runtime enforces a 25-second wall-clock execution limit, and longer Claude completions from models like claude-opus-4 or claude-sonnet-4 can take 30-60 seconds to complete. A second cause is idle stream timeouts, where the connection drops if no bytes are written for a set interval, even if the overall function is still within its time limit. Switching your API route to the Node.js runtime and implementing keep-alive strategies are the two primary fixes."
  - question: "Next.js 14 edge function timeout how long before it kills the connection"
    answer: "Vercel's Edge Runtime enforces a default 25-second wall-clock limit, meaning any function still running after that threshold is forcibly terminated regardless of activity. This is separate from idle stream timeouts, which can drop connections after just 10-15 seconds of no byte activity on the stream. Both limits are documented in Vercel's platform documentation and directly impact long-running AI streaming use cases."
  - question: "how to switch from edge runtime to node runtime in Next.js 14 app router api route"
    answer: "In Next.js 14 App Router, you can switch an API route from the Edge Runtime to the Node.js runtime by adding a single named export to your route file: export const runtime = 'nodejs'. This tells Next.js to use the Node.js runtime for that specific route handler, removing the 25-second wall-clock limit that causes the Claude API streaming response Next.js 14 app router edge function timeout fix to become necessary in the first place. This change only affects the specific route file where it is declared, leaving other routes on their default runtime."
  - question: "what is an idle stream timeout and how is it different from a wall clock timeout in Next.js"
    answer: "A wall-clock timeout kills a function after a fixed total duration regardless of what it is doing, while an idle stream timeout drops a connection specifically when no bytes have been written to the stream for a set interval, typically 10-15 seconds. These are two distinct failure modes, and fixing one does not automatically fix the other, which is why generic advice about edge function timeouts often fails to fully resolve Claude API streaming issues. Addressing idle stream timeouts requires explicit keep-alive strategies, such as periodically flushing data to the client to reset the inactivity timer."
---

Edge functions are fast. They're also brutally unforgiving when you're streaming long AI responses.

If you've wired up a Claude API streaming response in a Next.js 14 App Router project and started hitting silent failures, partial completions, or outright timeouts — you're running into one of the most common production pain points in AI-powered web apps right now.

The fix isn't complicated. But finding it without a map costs hours.

This piece breaks down exactly why the Claude API streaming response Next.js 14 App Router edge function timeout problem happens, what your architectural options look like, and how production teams are solving it in 2026.

---

**In brief:** Edge function runtimes impose hard execution limits that conflict with long-running AI streams. The fix requires deliberate runtime selection, correct `ReadableStream` handling, and explicit keep-alive strategies.

1. Vercel's Edge Runtime enforces a default 25-second wall-clock limit — Claude's longer completions routinely exceed this.
2. Switching to Node.js runtime within the App Router eliminates the primary timeout source but requires explicit `runtime` exports.
3. Idle stream timeouts are a separate failure mode from wall-clock limits and need their own mitigation.

---

## Why Edge Functions and Long AI Streams Conflict

The App Router shipped with edge-first defaults for a reason. Edge functions cold-start in under 50ms (according to Vercel's infrastructure documentation), distribute globally, and cost less at scale. For most API routes — auth checks, lightweight data fetches — they're ideal.

AI streaming breaks that contract.

When you're asking Claude to generate a 2,000-token response, you're holding an open HTTP connection for potentially 30–60 seconds depending on the model and prompt complexity. Anthropic's `claude-opus-4` and `claude-sonnet-4` — both released in early 2026 — handle complex reasoning tasks that can push response times well past the 25-second edge ceiling documented in Vercel's platform limits.

The failure mode is nasty. The stream doesn't error cleanly — it just stops. Your client receives a partial response with no error signal. Users see truncated output. Your error monitoring sees nothing. According to the LaoZha engineering blog, this "Partial Response Received" error is precisely the symptom of an idle stream timeout or wall-clock limit being hit mid-stream.

Two distinct problems are getting conflated here, and mixing them up is why generic advice doesn't help:

- **Wall-clock timeouts**: The runtime kills the function after a fixed duration regardless of activity.
- **Idle stream timeouts**: The connection drops if no bytes are written for a set interval — often 10–15 seconds between tokens.

Both need separate fixes.

---

## The Runtime Decision: Edge vs. Node.js

The fastest path out of this problem is exiting the Edge Runtime entirely for AI route handlers.

In Next.js 14 App Router, you control this with a single export:

```typescript
export const runtime = 'nodejs';
```

Drop that in your route file and the function runs in Node.js instead. Node.js routes on Vercel have a configurable timeout — up to 300 seconds on Pro plans, 800 seconds on Enterprise — which gives Claude's streaming responses room to breathe.

This isn't always the right call. The trade-offs are real:

| Criteria | Edge Runtime | Node.js Runtime | Self-Hosted Node |
|---|---|---|---|
| Cold start | ~50ms | ~200–400ms | Variable |
| Max timeout | 25s (Vercel default) | 300s (Pro) / 800s (Enterprise) | Unlimited |
| Global distribution | Yes | Regional | Manual |
| Streaming support | `ReadableStream` only | Full Node.js streams + `ReadableStream` | Full |
| Memory limit | 128MB | 1GB+ | Configurable |
| Claude long completions | ❌ Fails regularly | ✅ Works | ✅ Works |
| Cost at scale | Lower | Higher | Infrastructure cost |
| **Best for** | Short AI ops (<10s) | Long-form generation | Full control needed |

Switching to Node.js runtime adds cold-start latency and increases compute cost. For AI streaming specifically, it's the correct trade-off. Edge Runtime was built for edge *compute*, not edge *waiting*. Trying to force long-running AI streams through a runtime designed for sub-second operations is the architectural mismatch that causes this entire class of failures.

---

## Fixing the Stream Implementation Itself

Runtime selection solves the wall-clock problem. The idle timeout is different — and it'll still bite you in Node.js if Claude's responses have long pauses between token chunks.

The pattern that works in production uses a `ReadableStream` with an explicit keep-alive approach:

```typescript
export async function POST(req: Request) {
  const stream = new ReadableStream({
    async start(controller) {
      const response = await anthropic.messages.stream({
        model: 'claude-sonnet-4',
        max_tokens: 4096,
        messages: [{ role: 'user', content: await req.text() }],
      });

      for await (const chunk of response) {
        if (chunk.type === 'content_block_delta') {
          controller.enqueue(
            new TextEncoder().encode(chunk.delta.text)
          );
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

The `X-Accel-Buffering: no` header matters more than most tutorials mention. Without it, Nginx-based proxies — common in self-hosted and some cloud configurations — buffer the entire response before forwarding. That converts your stream into a slow batch response. You get none of the latency benefits of streaming, and you're still sitting exposed to timeout limits.

According to the Tech Edu Byte production implementation guide, setting `Transfer-Encoding: chunked` explicitly prevents reverse proxies from assuming a fixed content length, keeping the connection alive throughout the stream.

---

## What the Failure Scenarios Actually Look Like

Diagnosing which layer is failing changes the fix entirely. Three scenarios cover most production cases:

**Scenario 1 — Vercel Edge, no changes**: Claude stream starts, response cuts off at ~25 seconds. Client shows partial markdown, no error. Server logs show nothing. This is the wall-clock timeout. Fix: add `export const runtime = 'nodejs'`.

**Scenario 2 — Node.js runtime, complex prompt**: Claude's extended thinking mode pauses for 12+ seconds before emitting tokens. Connection drops. Fix: implement a keep-alive ping — write a zero-width space (`\u200B`) or comment byte every 8 seconds if no content chunk arrives.

**Scenario 3 — Self-hosted with Nginx**: Runtime is fine, timeouts are configured, but responses still buffer. Fix: `X-Accel-Buffering: no` in response headers, plus `proxy_read_timeout 300` in your Nginx config.

Each scenario has a different root cause. That's why "fix your timeout" advice from Stack Overflow usually doesn't land — the symptom looks identical across all three, but the solution is completely different each time.

---

## What Comes Next

The space is moving fast. Vercel announced longer edge function durations for AI workloads at their 2026 developer summit, with a 60-second limit reportedly in beta for select Pro accounts. That'll help for medium-length completions — but it won't fully close the gap for extended-context models running complex reasoning chains.

For now, the Node.js runtime remains the reliable path.

> **Key Takeaways**
>
> - Edge Runtime is the wrong default for Claude streaming — Node.js runtime is the correct starting point for any AI route handling long completions.
> - Wall-clock timeouts and idle timeouts are separate failure modes. Treating them as the same problem leads to fixes that only work half the time.
> - Proxy buffering via missing `X-Accel-Buffering` headers is an underdiagnosed failure mode that breaks streams silently and leaves no trace in logs.
> - The `ReadableStream` API in App Router handles Claude's streaming protocol correctly once the runtime and headers are right.
> - Extended thinking models introduce long inter-token pauses — keep-alive strategies are not optional for those use cases.

Don't fight the Edge Runtime. Switch to Node.js for your AI routes, set your headers explicitly, and handle idle gaps proactively. That combination covers the overwhelming majority of Claude streaming failures in production Next.js 14 deployments.

What failure mode are you hitting — wall-clock, idle timeout, or proxy buffering? The diagnosis changes everything.

## References

1. [Routing: API Routes | Next.js](https://nextjs.org/docs/pages/building-your-application/routing/api-routes)
2. [Claude Code Stream Idle Timeout? Fix the "Partial Response Received" Error Without Guessing | LaoZha](https://blog.laozhang.ai/en/posts/claude-code-stream-idle-timeout)
3. [Claude Streaming API with Next.js Edge: Production-Ready Implementation Guide - Tech Edu Byte](https://www.techedubyte.com/claude-streaming-api-nextjs-edge-guide/)


---

*Photo by [Bernd 📷 Dittrich](https://unsplash.com/@hdbernd) on [Unsplash](https://unsplash.com/photos/a-pixelated-orange-character-with-a-hat-GPPbPWwTHdg)*
