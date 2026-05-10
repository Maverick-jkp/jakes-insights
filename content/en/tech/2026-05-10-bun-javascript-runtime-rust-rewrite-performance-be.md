---
title: "Bun JavaScript Runtime Rust Rewrite: Performance Benchmark 2026"
date: 2026-05-10T20:10:50+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-web", "bun", "javascript", "runtime", "TypeScript"]
description: "Bun's Zig-to-Rust rewrite is reshaping JavaScript runtime performance in 2026. See what the early benchmark data reveals about startup speed gains."
image: "/images/20260510-bun-javascript-runtime-rust-re.webp"
technologies: ["JavaScript", "TypeScript", "Node.js", "AWS", "Claude"]
faq:
  - question: "Bun JavaScript runtime Rust rewrite performance benchmark 2026 results"
    answer: "Early 2026 benchmarks from the Bun JavaScript runtime Rust rewrite show improved tail latency and reduced crash frequency compared to the original Zig-based implementation. However, raw throughput gains remain modest so far, meaning the biggest wins are in stability and sustained load performance rather than peak speed."
  - question: "why is Bun rewriting from Zig to Rust"
    answer: "Bun is migrating from Zig to Rust primarily to address memory safety bugs and contributor scalability issues that emerged as adoption grew in production environments. Zig's smaller talent pool and maturing standard library made it difficult to maintain development velocity, while Rust's ecosystem tools like cargo, clippy, and tokio lower the barrier for open-source contributors."
  - question: "how does Bun JavaScript runtime Rust rewrite performance benchmark 2026 compare to Node.js and Deno"
    answer: "The Bun JavaScript runtime Rust rewrite performance benchmarks in 2026 are being compared against Node.js 22 and Deno 2.x, with early data showing Bun's strongest improvements in tail latency under sustained load rather than raw throughput. Teams evaluating runtimes should watch the next six months of benchmark data as the migration is still in progress."
  - question: "did AI help rewrite Bun in Rust"
    answer: "Yes, Anthropic's Claude was used to assist in migrating Bun's codebase from Zig to Rust, accelerating the rewrite through late 2025 and into 2026. This makes Bun one of the first large-scale JavaScript runtime rewrites to be partly driven by LLM-assisted tooling."
  - question: "is Bun safe to use in production after the Rust rewrite"
    answer: "Bun's Rust rewrite is specifically aimed at improving production reliability by eliminating memory safety issues like use-after-free patterns and buffer mishandling that appeared under concurrent load in the Zig version. Early 2026 data shows reduced crash frequency, though the migration is still ongoing and teams should monitor stability updates before fully committing."
---

Bun's decision to migrate its core from Zig to Rust isn't a minor refactor. It's a foundational bet that could reshape JavaScript runtime performance benchmarks in 2026 — and the early data is worth examining closely.

Bun launched in 2022 as a speed-first alternative to Node.js and Deno, built on JavaScriptCore and written in Zig. The pitch was simple: faster installs, faster startup, faster everything. It delivered. But as Bun's adoption grew — particularly in production environments at companies running high-throughput TypeScript services — cracks appeared in the Zig foundation. Memory safety issues, tooling limitations, and maintainability costs started dragging on development velocity.

So Jarred Sumner's team made the call: rewrite critical components in Rust. The migration, which accelerated through late 2025 and into 2026 with notable AI-assisted tooling from Anthropic's Claude, is still in progress. But partial benchmarks and community testing already show meaningful shifts in how Bun performs under sustained load — and what that means for teams choosing a JavaScript runtime today.

This analysis covers:

- Why Zig worked initially but created long-term friction
- What the Rust rewrite actually changes at the implementation level
- How current Bun Rust rewrite performance benchmarks compare against Node.js 22 and Deno 2.x
- What teams should watch over the next 6 months

---

**In brief:** Bun's Zig-to-Rust migration addresses memory safety and contributor scalability — two problems Zig couldn't solve at production scale. Early benchmarks in 2026 show improved tail latency and reduced crash frequency, though raw throughput gains remain modest so far.

1. Bun's Zig codebase produced measurable memory unsafety bugs that complicated production deployments.
2. Rust's ecosystem — `cargo`, `clippy`, `tokio` — dramatically lowers the contributor barrier compared to Zig's smaller toolchain.
3. Anthropic's AI-assisted code migration accelerated the rewrite, making this one of the first large-scale runtime rewrites partly driven by LLM tooling.

---

## How Bun Got Here: The Zig Problem Nobody Talks About

Zig was a deliberate choice in 2021–2022. It gave Bun low-level control, no GC overhead, and compile-time safety guarantees that felt sufficient at the time. For a startup runtime trying to beat Node.js on startup speed, it was the right call.

The cracks showed up later. Community discussions on Bun's GitHub — tracked across 2024–2025 issue threads — reveal a recurring class of bugs traced back to manual memory management in Zig: use-after-free patterns, buffer mishandling under concurrent load. These weren't catastrophic. But they were persistent. Zig's standard library was also still maturing, which meant Bun's team was often building infrastructure that Rust developers simply take for granted.

The contributor problem compounded this. Zig has a small talent pool. Rust has a large, battle-tested one. For an open-source project that needs external contributions to scale, that asymmetry matters — a lot. By mid-2025, the team began migrating networking and HTTP parsing components to Rust, starting with the highest-risk, highest-value subsystems.

The Anthropic angle is genuinely interesting. According to reporting from byteiota.com, Claude was used to assist with large portions of the Zig-to-Rust translation, handling mechanical rewrites that would've taken engineers weeks. This isn't replacing engineering judgment — the team still reviews and validates everything — but it dramatically compressed the migration timeline. Whether AI-assisted rewrites introduce subtle correctness issues at the margins is a question worth watching.

## What the 2026 Benchmarks Actually Show

Raw numbers first, with the caveat that Bun's Rust rewrite is partial. Not all components have migrated. So current benchmarks measure a hybrid runtime.

| Benchmark | Bun 1.x (Zig-dominant) | Bun 2.x (Partial Rust) | Node.js 22 | Deno 2.x |
|---|---|---|---|---|
| HTTP requests/sec (hello world) | ~210,000 | ~218,000 | ~95,000 | ~105,000 |
| Cold start time (simple script) | ~6ms | ~5.5ms | ~45ms | ~38ms |
| `npm install` (median, 50 deps) | ~0.9s | ~0.85s | ~8.2s | N/A |
| P99 latency (sustained load, 60s) | ~12ms | ~8.5ms | ~14ms | ~11ms |
| Memory crashes (stress test, 1hr) | Occasional | Rare | Rare | Rare |

*Note: Figures drawn from community benchmarks shared on Bun's GitHub and thecodersblog.com analysis, May 2026. "Occasional" and "Rare" reflect qualitative crash frequency categories, not precise incident counts.*

The headline numbers don't change dramatically. Bun was already fast on raw throughput, and the Rust rewrite doesn't suddenly double requests-per-second. That's not the point.

The P99 latency improvement is the story. Under sustained load — the kind production APIs actually face — the Rust components reduce tail latency measurably. Fewer memory mismanagement hiccups means more consistent performance. That's what enterprise teams care about. A runtime that hits 210,000 requests per second but spikes unpredictably at P99 is harder to operate than one that runs 10% slower but holds steady.

## The Rust Ecosystem Advantage: Why This Compounds Over Time

Short term, the benchmark gains look incremental. Long term, the Rust migration unlocks something more valuable: contribution velocity and library access.

Rust's `tokio` async runtime is production-hardened by companies including AWS and Discord. Bun can now build on top of that foundation rather than maintaining equivalent infrastructure in Zig. Similarly, Rust's `cargo` toolchain means new contributors can onboard faster — they don't need to learn Zig-specific memory management patterns before shipping useful code.

According to thecodersblog.com's 2026 analysis, the Rust migration is expected to accelerate Bun's WebSocket and fetch API performance improvements — areas where Zig's limitations were creating specific bottlenecks. Those haven't fully landed yet, but they're in active development.

The comparison to Deno's architecture is instructive. Deno also runs on Rust (via `deno_core` and `tokio`), and Deno's stability story has improved substantially since 2023. Bun's Rust migration effectively brings it onto similar infrastructure footing — meaning both runtimes can now compete on feature quality, not just language of implementation. This is a healthier competitive dynamic for the ecosystem overall.

This approach can fail, though, if the hybrid migration period introduces inconsistencies between Zig and Rust subsystems. Boundary bugs — where Zig-managed memory hands off to Rust-managed memory — are a legitimate risk in any partial rewrite of this complexity.

### Bun vs. Deno 2.x vs. Node.js 22: Where Each Makes Sense

**Bun 2.x (Partial Rust):**
- **Strengths**: Fastest cold starts, built-in bundler/test runner, best `npm` compatibility speed
- **Weaknesses**: Rewrite still in progress; some edge case instability remains
- **Best for**: TypeScript-heavy projects, serverless functions, teams that want an all-in-one toolchain

**Deno 2.x:**
- **Strengths**: Full Rust foundation, strong security model, first-class TypeScript, stable contributor ecosystem
- **Weaknesses**: `npm` compatibility improved but still requires explicit flags; smaller package ecosystem familiarity
- **Best for**: Security-conscious teams, fresh projects without legacy npm dependencies

**Node.js 22:**
- **Strengths**: Widest ecosystem, battle-tested in every production context imaginable, V8 performance improvements ongoing
- **Weaknesses**: Slower startup, no built-in bundler, install speed lags far behind
- **Best for**: Existing production systems, teams where ecosystem compatibility is non-negotiable

The Rust rewrite doesn't make Bun the automatic winner. It makes Bun more trustworthy at scale — which is a different thing entirely.

## What Development Teams Should Watch Now

The practical question isn't "should we switch to Bun today?" It's "when does the Rust rewrite stabilize enough to justify migration planning?"

Three signals worth tracking:

**Crash rate telemetry.** Bun 2.x's GitHub issue tracker is a real-time signal. If memory-related crashes drop to near-zero through Q3 2026, that's the green light for production adoption in high-traffic services. Right now the trend is positive but not complete.

**WebSocket and fetch benchmarks.** The Rust networking components are the next major migration target. When those land — expected mid-2026 based on the team's public roadmap — expect another round of benchmarks that will be more definitive than current hybrid measurements.

**Enterprise adoption signals.** Vercel already runs Bun in parts of its edge infrastructure. Watch for announcements from Cloudflare Workers or AWS Lambda about Bun runtime support expansion. That kind of infrastructure endorsement carries more weight than any microbenchmark.

Teams running Node.js in production don't need to panic-migrate. But any team evaluating a new TypeScript service in Q3 or Q4 2026 should run Bun 2.x in staging now — the toolchain speed alone often justifies the switch before performance benchmarks even enter the conversation.

---

## The Bottom Line

The Bun JavaScript runtime Rust rewrite performance story in 2026 isn't about raw speed gains. Bun was already the fastest option on cold starts and throughput. The Rust migration is about making that speed *reliable* — eliminating the memory safety class of bugs that made production teams nervous, and building on infrastructure (`tokio`, `cargo`) that scales with contributor growth.

> **Key Takeaways**
> - P99 latency under sustained load improved roughly 30% in early Bun 2.x benchmarks versus Zig-dominant builds
> - Raw throughput gains are modest (under 5%) — consistent with a safety and stability-focused rewrite, not a performance-focused one
> - Anthropic's AI-assisted migration compressed what would've been a multi-year rewrite into a significantly shorter timeline — though AI-assisted boundary code warrants careful validation
> - Deno 2.x remains the more stable Rust-native option today, but Bun's trajectory is closing that gap fast

The next six months will answer whether Bun can complete the migration cleanly. If it does, the case for Node.js in new greenfield projects gets noticeably harder to make.

What's your current production runtime? If your team has already run Bun 2.x under load, the benchmark data you've collected is more valuable than any synthetic test — share it.

## References

1. [Bun’s Zig to Rust Rewrite: Anthropic’s AI Code Experiment | byteiota](https://byteiota.com/buns-zig-to-rust-rewrite-anthropics-ai-code-experiment/)
2. [Bun's Rust Pivot: What the Zig-to-Rust Migration Means for JavaScript Runtime Performance in 2026 | ](https://thecodersblog.com/bun-runtime-migration-from-zig-to-rust-2026/)
3. [Bun is Rewriting Itself in Rust And It Might Change Everything | by John Philip | Rustaceans | May, ](https://medium.com/rustaceans/bun-is-rewriting-itself-in-rust-and-it-might-change-everything-e1c80ef4b8aa)


---

*Photo by [Patrick Martin](https://unsplash.com/@patrickmmartin) on [Unsplash](https://unsplash.com/photos/a-close-up-of-a-computer-screen-with-code-on-it-UMlT0bviaek)*
