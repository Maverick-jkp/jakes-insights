---
title: "Bun JavaScript Runtime Rewritten in Rust from Zig: What It Means for Developers"
date: 2026-05-05T20:18:14+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "bun", "javascript", "runtime", "TypeScript"]
description: "Bun's JavaScript runtime is ditching Zig for Rust. Here's what that shift means for the 3x Node.js speed advantage developers rely on daily."
image: "/images/20260505-bun-javascript-runtime-rewritt.webp"
technologies: ["JavaScript", "TypeScript", "Node.js", "Rust", "Go"]
faq:
  - question: "why is Bun JavaScript runtime being rewritten in Rust from Zig"
    answer: "Bun is being rewritten from Zig to Rust primarily because Zig lacks the mature package ecosystem, debugging tooling, and community scale that Rust offers, making long-term maintenance harder for a growing team. The decision is pragmatic rather than performance-driven, as Rust's cargo ecosystem and memory safety guarantees make it easier to ship new features without introducing low-level bugs."
  - question: "will Bun JavaScript runtime rewritten in Rust from Zig affect performance for developers"
    answer: "Developers should not expect a performance regression from the Bun JavaScript runtime rewritten in Rust from Zig, as the rewrite is a tooling and ergonomics decision rather than a speed trade-off. Production users can expect continuity in performance characteristics, with potential improvements in stability and edge-case reliability over the next 6–12 months."
  - question: "is Bun still faster than Node.js in 2026"
    answer: "Yes, Bun remains significantly faster than Node.js, with benchmarks showing it runs server-side JavaScript roughly 3x faster in common HTTP workloads and delivers dramatically faster npm install times. The ongoing rewrite from Zig to Rust is not expected to eliminate this performance advantage."
  - question: "what is Zig programming language and why did Bun use it"
    answer: "Zig is a low-level systems language that offers C-level memory control without garbage collection, compiles to tiny binaries, and allows zero-overhead calls to C code. Bun originally used Zig because these characteristics made it ideal for building a high-performance JavaScript runtime that could squeeze maximum speed out of every operation."
  - question: "should teams running Bun in production worry about the Bun JavaScript runtime rewritten in Rust from Zig"
    answer: "Teams running Bun in production should not be alarmed by the Bun JavaScript runtime rewritten in Rust from Zig, as the migration is designed to improve long-term maintainability rather than change runtime behavior. The rewrite is expected to enhance stability and reduce low-level bugs, making production deployments more reliable over time."
---

Bun launched in 2022 promising to be the fastest JavaScript runtime on the planet. It delivered — benchmarks showed Bun running server-side JavaScript 3x faster than Node.js in common HTTP workloads, and its npm install times were genuinely shocking. The foundation? Zig. A low-level systems language so raw and unforgiving that most developers haven't even heard of it.

Now the team is rewriting Bun's core in Rust.

That's not a minor configuration change. Rewriting a runtime's foundation in a different systems language mid-stream — while the product has millions of weekly downloads and real production deployments — is the kind of decision that signals something specific about where the JavaScript ecosystem is heading in 2026. Either the original bet on Zig didn't pan out the way Oven (Bun's creator) expected, or the calculus around tooling, team velocity, and ecosystem support shifted enough to justify the cost.

Both things are probably true.

The Hacker News and Lobsters discussions that surfaced this migration in early 2026 generated hundreds of comments, mostly from developers asking the same thing: does this mean Bun's performance advantage disappears? Does this mean Zig was the wrong call? And what does this mean for teams already running Bun in production?

What's actually happening, why Zig's limits matter, and what the Rust migration signals for the next two years of JavaScript runtime development — that's what we're digging into.

---

> **In brief:** Bun's rewrite from Zig to Rust is a pragmatic tooling decision, not a performance regression. The shift trades Zig's raw speed potential for Rust's mature ecosystem and better developer ergonomics.
>
> 1. Zig offers exceptional performance but lacks Rust's package ecosystem, debugging tooling, and community scale — making long-term maintenance harder for a growing team.
> 2. Rust's memory safety guarantees and `cargo` ecosystem make it easier to ship new Bun features without introducing low-level bugs.
> 3. Developers running Bun in production should expect continuity in performance characteristics, with potential improvements in stability and edge-case reliability over the next 6–12 months.

---

## How Bun Got Here — And Why Zig Was the Original Bet

Zig is a fascinating language. It gives you C-level control over memory without garbage collection, compiles to tiny binaries, and lets you call C code directly with zero overhead. When Jarred Sumner started building Bun at Oven, Zig was the logical choice for a runtime that needed to squeeze every microsecond out of JavaScript execution. The JavaScriptCore engine — borrowed from WebKit, the same engine Safari uses — did the heavy lifting on JS parsing, and Zig handled the surrounding infrastructure.

The bet paid off early. By 2023, Bun's benchmark numbers were real — not cherry-picked. Its `bun:test` runner, HTTP server, and file I/O consistently outperformed Node.js 20 on comparable hardware. The Zig foundation wasn't the bottleneck; it was genuinely fast.

But Zig has a ceiling. Not a performance ceiling — a *developer ecosystem ceiling*. As of early 2026, Zig still doesn't have a package manager with anything close to the depth of Rust's `cargo`. Its standard library is minimal by design. Debugging tooling is improving but remains immature compared to what Rust offers via LLDB integration and the broader toolchain. And perhaps most critically: the pool of developers who know Zig well enough to contribute to a production runtime is tiny.

Rust doesn't have these problems. The Rust ecosystem in 2026 is deep. According to crates.io, `cargo` now hosts over 150,000 published packages. Tokio handles async I/O with years of production hardening. `rustfmt`, `clippy`, and the broader toolchain make onboarding new contributors dramatically faster than Zig ever could.

The migration is being described — partly tongue-in-cheek, partly accurately — as "vibe-ported," referencing AI-assisted code translation. That framing matters. It suggests Oven is using LLM tooling to accelerate what would otherwise be a multi-year rewrite into something more manageable.

---

## Zig's Honest Strengths — and the Walls It Builds

Zig is direct about what it is. No hidden control flow. No implicit allocations. The language forces you to think about memory at every level, which is exactly what you want when building something that needs to handle thousands of concurrent connections with sub-millisecond latency.

For Bun's early phases, that directness was an asset. Sumner could write exactly the behavior he needed without fighting a language's abstractions. Zig's `comptime` feature — compile-time code execution — let the team do things that would require macros in Rust, and it's genuinely elegant.

The wall appears when you need to scale your *team*, not your *code*. Zig's community, while passionate, is smaller by an order of magnitude. When a production bug surfaces at 2am deep in a Zig memory management path, the number of people who can meaningfully help is limited. That's a real operational risk for a company shipping a product used in production. Industry reports on open-source contributor retention consistently flag ecosystem size as a top factor in long-term project health — and Zig simply can't compete with Rust on that dimension yet.

## Why Rust Makes Sense for the Next Phase

Rust's ownership model catches entire classes of memory bugs at compile time. For a JavaScript runtime — which handles untrusted code, manages complex heap interactions with JavaScriptCore, and needs to be rock-solid on memory safety — that matters enormously.

The practical difference: in Zig, the developer is responsible for memory correctness. Zig trusts you. In Rust, the compiler enforces correctness. That enforcement has a cost in developer ergonomics (the borrow checker is famously strict), but the payoff is fewer use-after-free bugs, fewer data races, fewer late-night incident postmortems.

This approach can fail when teams underestimate the Rust learning curve. The borrow checker genuinely slows down developers unfamiliar with ownership semantics, and a rushed migration can introduce logic errors even while eliminating memory errors. Oven's "vibe-port" strategy — using AI-assisted translation with human review — is a reasonable hedge against that risk, but it isn't foolproof. The proof will be in the stability metrics over the next two quarters.

For Bun's maturity phase — where stability and feature velocity matter more than squeezing the last 2% of performance — Rust's trade-off is the right one. That said, this isn't always the answer. Teams building greenfield systems tools with tiny contributor bases might still reach for Zig's simplicity and get exactly what they need.

## The "Vibe-Ported" Approach and What It Signals

The "vibe-ported" framing in the Lobsters discussion is worth taking seriously. It suggests Oven is using AI-assisted translation tools to convert Zig code to Rust at scale, rather than rewriting from scratch. LLMs are now capable enough to translate between systems languages with reasonable accuracy, requiring human review rather than human authorship for each function.

If this approach holds — and the community discussion suggests it's moving faster than a manual rewrite would — it signals that large-scale language migrations in systems software are becoming more tractable. That has implications well beyond Bun.

## Runtime Comparison: Bun vs. Node.js vs. Deno in 2026

| Feature | Bun (Rust/Zig transition) | Node.js 22 | Deno 2 |
|---|---|---|---|
| **JS Engine** | JavaScriptCore | V8 | V8 |
| **Systems Language** | Rust (migrating from Zig) | C++ | Rust |
| **npm Compatibility** | Full | Full | Full (since Deno 2) |
| **TypeScript Support** | Native, no transpile | Requires `tsx`/`ts-node` | Native |
| **HTTP Benchmarks** | ~330k req/s (Techempower) | ~110k req/s | ~140k req/s |
| **Package Manager** | Built-in (`bun install`) | `npm`/`pnpm`/`yarn` | Built-in (`deno add`) |
| **Production Maturity** | Growing | Battle-tested | Growing |
| **Best For** | Speed-critical APIs, scripts | Enterprise Node.js workloads | Security-focused apps |

*Benchmark figures reference Techempower Framework Benchmarks Round 22 data; exact results vary by hardware configuration.*

The pattern is clear: Bun leads on raw throughput, Node.js leads on production maturity, and Deno carves out a security-focused niche. The Rust migration doesn't change Bun's benchmark position meaningfully — JavaScriptCore does most of the performance work. What it changes is Bun's trajectory on stability and contributor velocity.

---

## What This Means If You're Running Bun Right Now

**For individual developers and small teams**: nothing breaks. The migration is happening at the systems layer — your `bun run`, `bun test`, and `bun install` commands aren't changing. Watch the Bun GitHub releases closely over the next 3–4 months; stability improvements in edge cases (particularly around complex module resolution and native addons) are likely the first tangible benefit you'll see.

**For engineering teams evaluating Bun for production**: this rewrite actually strengthens the case for adoption. One of the legitimate hesitations about Bun has been operational risk — what happens when something breaks in the runtime itself? A Zig codebase with a small contributor pool is harder to get help with than a Rust codebase backed by a massive ecosystem. The migration reduces that risk over a 12-month horizon.

**For teams already running Node.js**: the competitive pressure just increased. Node.js 22's performance improvements are real, but the gap with Bun on I/O-heavy workloads remains significant. If you're running microservices that bottleneck on HTTP throughput or file I/O, a Bun migration benchmark is worth running in a staging environment now.

**Watch these signals over the next 6 months**:
- Whether the AI-assisted "vibe-port" approach maintains Bun's performance characteristics as more of the codebase migrates
- Rust contribution rates on the Bun GitHub repository — a spike would confirm the ecosystem hypothesis
- Node.js 23's planned V8 upgrades, which could narrow the benchmark gap

---

## Where This Goes From Here

The Zig-to-Rust migration represents a bet on long-term ecosystem health over short-term purity. Zig was the right tool for building a fast prototype and proving the concept. Rust is the right tool for building something that a larger team can maintain, extend, and trust in production.

> **Key Takeaways:**
> - **Performance won't regress** — JavaScriptCore drives Bun's speed, not the surrounding systems language
> - **Stability should improve** — Rust's compiler catches memory errors that Zig leaves to developer discipline
> - **Contributor velocity will increase** — the depth of the Rust ecosystem makes onboarding meaningfully faster
> - **AI-assisted migration is now viable for production systems code** — the "vibe-port" approach is a real signal, not a gimmick
> - **Watch Deno** — with Zig no longer differentiating Bun at the systems layer, Deno's Rust-native foundation becomes a more interesting competitive variable

Over the next 12 months, expect Bun to ship more features faster, with fewer low-level bug reports. The project is growing up. That's good news for anyone who was waiting to see if Bun was a serious long-term bet before committing.

**Running Bun in production already, or still holding on Node.js stability guarantees? Drop your stack in the comments — the context always changes the calculus.**

## References

1. [Bun (the js runtime) is being vibe-ported from zig to rust | Lobsters](https://lobste.rs/s/otxkjw/bun_js_runtime_is_being_vibe_ported_from)
2. [Bun is being ported from Zig to Rust | Hacker News](https://news.ycombinator.com/item?id=48016880)
3. [Zig: The Honest Systems Language You Have Been Ignoring - DEV Community](https://dev.to/arshtechpro/zig-the-honest-systems-language-you-have-been-ignoring-45ei)


---

*Photo by [Patrick Martin](https://unsplash.com/@patrickmmartin) on [Unsplash](https://unsplash.com/photos/a-close-up-of-a-computer-screen-with-code-on-it-UMlT0bviaek)*
