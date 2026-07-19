---
title: "Claude API Streaming Response in Next.js App Router: Fixing Server Action Latency"
date: 2026-03-21T19:46:48+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "claude", "api", "streaming", "TypeScript"]
description: "Fix Claude API streaming in Next.js App Router server actions and eliminate the 2-4 second silence killing your UI's perceived performance."
image: "/images/20260321-claude-api-streaming-response-.webp"
technologies: ["TypeScript", "Next.js", "Node.js", "Claude", "Anthropic"]
faq:
  - question: "why do next.js server actions not work with streaming responses"
    answer: "Next.js server actions buffer the full response before returning it to the client, meaning they wait for the entire promise to resolve before sending anything. This makes them structurally incompatible with token-by-token streaming because all chunks pile up in memory until the response is complete, causing 2-4 seconds of silence before the UI shows anything."
  - question: "claude api streaming response nextjs app router server action latency fix"
    answer: "The fix is to replace server actions with an App Router Route Handler at `app/api/chat/route.ts`, which supports streaming `Response` objects natively. Using the Claude SDK's `stream()` method combined with `ReadableStream` on Vercel's Edge runtime can reduce time-to-first-token from 2,000–4,000ms down to under 200ms."
  - question: "how to stream claude api responses in nextjs app router"
    answer: "Create a Route Handler instead of a server action, then use the Anthropic SDK's `client.messages.stream()` method combined with a `ReadableStream` or `TransformStream` to pipe tokens to the client as they arrive. Running this on Vercel's Edge runtime further reduces latency by eliminating Node.js cold start overhead."
  - question: "claude api streaming response nextjs app router server action latency fix edge vs nodejs runtime"
    answer: "The Edge runtime is recommended for Claude streaming in Next.js because it eliminates cold start delays that can add 800ms or more to response time. This matters especially because Claude's first token can arrive in approximately 180ms, meaning a slow runtime startup can negate the streaming benefit entirely."
  - question: "nextjs route handler vs server action for ai streaming which is better"
    answer: "Route Handlers are the correct choice for AI streaming use cases like Claude API integration because they support streaming `Response` objects natively, while server actions are designed for mutations and type-safe RPC and buffer responses by design. For long-running AI tasks that can take 30–60 seconds, Route Handlers with proper stream handling are the only production-viable option."
aliases:
  - "/tech/2026-03-21-claude-api-streaming-response-nextjs-app-router-se/"

---

Streaming Claude responses through a Next.js App Router server action feels like it should just work.

It doesn't.

And the latency penalty for wiring this up wrong isn't 50ms — it's closer to 2-4 seconds of dead silence before your UI shows anything. That gap destroys perceived performance. In 2026, with Claude 3.7 Sonnet handling complex multi-step reasoning tasks that run 30-60 seconds, getting the streaming architecture right is the difference between a product that feels alive and one that feels broken.

Server actions buffer responses by design. They're not meant for streaming. But with the right architecture — switching to Route Handlers or using `ReadableStream` carefully — you can get token-by-token output with sub-200ms time-to-first-token on Vercel's Edge runtime.

What follows covers why server actions silently kill streaming, the Route Handler alternative and its trade-offs, Edge vs. Node.js runtime latency differences, and a direct comparison of three implementation patterns.

> **Key Takeaways**
> - Next.js server actions buffer the full response before returning, making them structurally incompatible with token-by-token Claude API streaming.
> - Switching to an App Router Route Handler with `ReadableStream` cuts time-to-first-token from 2,000–4,000ms to under 200ms on Vercel Edge, according to benchmarks in the Tech Edu Byte production implementation guide.
> - The Claude SDK's `stream()` method combined with `StreamingTextResponse` (or a manual `TransformStream`) is the current production pattern that handles backpressure correctly.
> - Edge runtime eliminates Node.js cold start overhead — critical when Claude's initial token can arrive in ~180ms but your runtime takes 800ms to wake up.

---

## The Architecture Trap: Why Server Actions Break Streaming

Server actions in Next.js App Router are a clean abstraction. You call a function, await it, get a result. The problem is that "await it" part.

The App Router's server action implementation waits for the full promise to resolve before sending anything to the client. There's no mechanism to flush partial output mid-execution.

The Anthropic SDK's `client.messages.stream()` returns an async iterator — it yields chunks as Claude generates them. Inside a server action, those chunks pile up in memory. The client sees nothing. When Claude finally finishes — 30 seconds later for a complex task — everything dumps at once.

This is well-documented in Next.js GitHub issues. The framework team's position, as of early 2026, hasn't changed: server actions aren't designed for streaming responses. They're designed for mutations and data fetching with type-safe RPC semantics.

The fix isn't a workaround. It's a pattern change.

---

## The Route Handler Solution (And the Runtime Decision)

Swap the server action for an App Router Route Handler at `app/api/chat/route.ts`. Route Handlers support `Response` objects with streaming bodies directly. That's the foundation.

The production pattern looks like this:

```typescript
// app/api/chat/route.ts
export const runtime = 'edge';

export async function POST(req: Request) {
  const { messages } = await req.json();
  
  const stream = await anthropic.messages.stream({
    model: 'claude-3-7-sonnet-20250219',
    max_tokens: 2048,
    messages,
  });

  const readable = new ReadableStream({
    async start(controller) {
      for await (const chunk of stream) {
        if (chunk.type === 'content_block_delta') {
          controller.enqueue(
            new TextEncoder().encode(chunk.delta.text)
          );
        }
      }
      controller.close();
    },
  });

  return new Response(readable, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
```

Setting `runtime = 'edge'` matters more than most teams realize. According to the Tech Edu Byte production implementation guide, Edge runtime eliminates the cold start penalty that Node.js Lambda-style functions carry — often 600–900ms on first invocation. Claude's API can return the first token in ~180ms. Paying 900ms of runtime overhead before that token even arrives is the silent latency killer most teams never profile.

This approach can fail when your implementation depends on native Node.js modules or packages that don't run in V8 isolates. In those cases, Edge isn't an option — which leads to the three-way decision below.

---

## Comparing the Three Implementation Patterns

Not every team can move everything to Edge. Node.js runtime sometimes wins on compatibility: native modules, larger memory requirements, specific npm packages that haven't been ported to the edge environment. So the real decision is three-way:

| Pattern | Time-to-First-Token | Cold Start | Streaming Support | Complexity |
|---|---|---|---|---|
| **Server Action** | 2,000–4,000ms (buffered) | Low | ❌ None | Low |
| **Route Handler (Node.js)** | 300–800ms | 600–900ms | ✅ Full | Medium |
| **Route Handler (Edge)** | 150–250ms | ~0ms | ✅ Full | Medium |

The server action pattern loses on latency regardless of cold starts — it's structurally incompatible with streaming, full stop. Between the two Route Handler approaches, Edge wins on time-to-first-token. Node.js is the fallback when you need packages that don't run in V8 isolates.

One more consideration that gets skipped in most tutorials: backpressure. If the client reads slowly — rare but possible on degraded connections — an unmanaged `ReadableStream` can buffer Claude's output in memory. For production, wrapping the stream in a `TransformStream` with a finite queue size prevents memory bloat on long-running requests. This isn't a theoretical concern; it surfaces on mobile clients with inconsistent connectivity.

---

## What This Means for Your Deployment Stack

The core challenge isn't the streaming code itself. It's that this fix requires teams to rethink where their LLM calls live in the Next.js architecture.

**Scenario 1: You're already using server actions for Claude calls.** The migration path is straightforward — extract the Claude call into a Route Handler, keep the server action for anything that needs type-safe RPC (form submissions, database mutations). Don't try to bridge them with `fetch()` inside a server action; that adds a network hop and gains nothing.

**Scenario 2: You need authentication before the Claude call.** Route Handlers support middleware and `cookies()` from `next/headers` — the same tools available in server actions. JWT validation or session checks before the stream starts adds ~5–10ms, not hundreds. Authentication isn't a reason to stay on server actions.

**Scenario 3: You're on a self-hosted Next.js deployment** (not Vercel). Edge runtime availability depends on your adapter. The `@next/node-server` adapter supports Edge functions locally, but production behavior varies by host. If Edge isn't available, a Node.js Route Handler with proper streaming still delivers 300–500ms TTFT — vastly better than server actions regardless.

Worth watching: Next.js 16, expected mid-2026, with signals from the Vercel team about first-class streaming primitives that could eventually close the gap for server actions. That's not a reason to wait. Production deployments need solutions that work today, and the Route Handler pattern is stable.

---

## Conclusion

The situation comes down to a few clean facts.

Server actions buffer Claude output — they're the wrong tool for streaming, period. App Router Route Handlers with `ReadableStream` deliver token-by-token output with real latency numbers. Edge runtime cuts time-to-first-token to under 250ms by eliminating cold start overhead that otherwise dwarfs Claude's own response time. And the migration is low-risk: Route Handlers and server actions coexist without friction in the App Router.

The Vercel AI SDK already moves toward higher-level abstractions for LLM streaming with `StreamingTextResponse`, and that direction will continue. But the underlying routing architecture stays the same either way.

So the action is simple: profile your current time-to-first-token. If it's above 500ms and you're using server actions for Claude calls, you've found the problem. The fix is a Route Handler and 30 lines of streaming code.

What's your current TTFT on Claude responses in production? That number tells you whether this belongs in the current sprint or the next one.

## References

1. [Next.js Optimization Recipes | Cursor, Claude Code & Codex | Developer Toolkit](https://developertoolkit.ai/en/cookbook/frontend-recipes/nextjs-patterns/)
2. [Claude Streaming API with Next.js Edge: Production-Ready Implementation Guide - Tech Edu Byte](https://www.techedubyte.com/claude-streaming-api-nextjs-edge-guide/)
3. [How to Use Claude Code for Next.js Development | Beam Terminal Organizer](https://getbeam.dev/blog/claude-code-nextjs-development.html)


---

*Photo by [Vitaly Gariev](https://unsplash.com/@silverkblack) on [Unsplash](https://unsplash.com/photos/beekeeper-in-yellow-suit-holding-honeycomb-frame-zU54lfe2d3I)*
