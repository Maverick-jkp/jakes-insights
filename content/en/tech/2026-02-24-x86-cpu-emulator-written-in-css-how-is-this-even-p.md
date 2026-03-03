---
title: "X86 CPU Emulator Written in CSS: How Is This Even Possible?"
date: 2026-02-24T20:22:10+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["emulator", "subtopic-web"]
description: "Discover how a working X86 CPU emulator written in CSS defies logic. Explore the mind-bending trick that makes this impossible feat reality."
image: "/images/20260224-x86-cpu-emulator-written-in-cs.webp"
technologies: ["JavaScript", "React", "Rust", "Go", "Java"]
faq:
  - question: "X86 CPU emulator written in CSS how is this even possible"
    answer: "CSS achieves this through a combination of checkbox hacks, sibling selectors, and recursive rules that create stateful logic without any JavaScript. CSS3 combined with HTML is Turing complete, meaning it can theoretically compute anything a conventional programming language can, which makes CPU emulation technically possible. The emulator exploits these largely ignored properties of CSS to simulate x86 architecture and even boot DOS."
  - question: "is CSS really Turing complete"
    answer: "Yes, CSS3 combined with HTML is formally Turing complete, as demonstrated by researchers who showed it can simulate a Rule 110 cellular automaton. This means CSS can theoretically perform any computation that a traditional programming language can, given sufficient state representation. Features like the :checked pseudo-class, general sibling combinators, and counter() functions are what make this possible."
  - question: "how does a CSS x86 emulator compare to JavaScript emulators in speed"
    answer: "Traditional JavaScript emulators like v86 can execute x86 instructions at speeds exceeding 100 MHz in modern browsers, while CSS-based approaches run orders of magnitude slower. However, the speed difference isn't really the point — the CSS emulator is a proof of concept that demonstrates declarative systems are capable of general computation. Its significance lies in what it reveals about browser-native compute capabilities, not raw performance."
  - question: "what is the CSS checkbox hack and how does it enable computation"
    answer: "The CSS checkbox hack uses HTML checkboxes combined with the :checked pseudo-class and sibling selectors to track and change state purely within CSS. By chaining these stateful elements together with complex selector rules, developers can create logic gates and memory-like structures without any JavaScript. This is one of the core techniques that makes something as complex as an X86 CPU emulator written in CSS possible, however improbable it sounds."
  - question: "can you run real programs in a CSS only emulator"
    answer: "Yes, the CSS x86 emulator described is not a toy demo — it actually boots DOS and runs real programs entirely within a browser using pure CSS. It works by exploiting CSS's Turing complete properties through checkbox hacks, sibling selectors, and recursive rules to replicate x86 CPU behavior. While it runs much slower than JavaScript or WebAssembly-based emulators, it proves that browser-native computation is not limited to traditional scripting languages."
---

Someone built an x86 CPU emulator in CSS. No JavaScript. No WebAssembly. Pure CSS — the same language you use to change a button's color or add a drop shadow. It boots DOS. It runs real programs.

The reaction from most engineers is immediate and visceral: *how is this even possible?*

This isn't a toy demo with caveats buried in footnotes. It's a working x86 emulator that exploits CSS's largely ignored Turing-complete properties, pushing a styling language so far past its intended purpose that it breaks your mental model of what "CSS" actually means. As the browser platform continues absorbing capabilities previously reserved for native runtimes, this project sits at a strange intersection: simultaneously a landmark technical achievement and a stress test of how we categorize tools.

The deeper question isn't just "how" — it's what this reveals about the nature of computation, the hidden power buried in declarative systems, and what browser-native compute could look like when we stop assuming boundaries.

**What this covers:**
- How CSS achieves Turing completeness and why that enables CPU emulation
- The technical architecture behind a CSS x86 emulator
- How this compares to conventional emulation approaches (JavaScript, WebAssembly)
- What this means for browser platform evolution and beyond

---

> **Key Takeaways**
> - CSS is Turing complete under specific conditions — meaning it can theoretically compute anything a conventional programming language can, given sufficient state representation.
> - CSS checkbox hacks, sibling selectors, and recursive rules create stateful logic without a single line of JavaScript. That's the concrete answer to how this works.
> - Traditional JavaScript emulators like v86 (copy.sh) execute x86 at speeds exceeding 100 MHz in modern browsers. CSS-based approaches run orders of magnitude slower — but calling it "slow" misses the architectural point entirely.
> - Browser-native compute is no longer limited to JavaScript and WebAssembly. Declarative systems are now demonstrably capable of general computation.
> - For engineers building browser-based tooling, this project reframes what's achievable inside a sandboxed, no-plugin browser context.

---

## The Computational Underbelly of CSS

To understand how this emulator works, you need a brief detour into CSS's history.

CSS was designed in 1996 as a presentational layer. Fonts, colors, layout. Nobody was thinking about Turing completeness. But over the following two decades, CSS absorbed features that collectively make it capable of representing state: the `:checked` pseudo-class, the general sibling combinator (`~`), `counter()` functions, and eventually `@supports` and complex selector chains.

By 2012, developers had begun formally exploring CSS-only games and state machines. By 2019, researchers formally demonstrated that CSS3 combined with HTML is Turing complete — the key insight being that CSS and HTML together can simulate a Rule 110 cellular automaton, which is itself Turing complete per Matthew Cook's 2004 proof published in *Complex Systems*. CSS alone, without HTML interaction, is more limited. But with checkbox inputs providing stateful bits and selectors propagating state changes, you get genuine computation.

The x86 CPU emulator builds directly on this foundation. It encodes CPU registers as checkbox states, uses selector cascades to implement logic gates, and chains those gates to produce ALU operations — add, subtract, compare, branch. The result is genuinely executable x86 code, interpreted entirely by a browser's CSS engine.

This matters because the browser is increasingly the deployment target for compute-heavy workloads. WebAssembly has driven much of that shift, with the W3C publishing WASM 2.0 in December 2022. The CSS emulator exists outside that lineage — it's a proof of what declarative systems can do when pushed to the limit.

---

## How CSS Encodes State and Logic

The core mechanism is the checkbox hack, scaled to absurdity.

A standard CSS checkbox hack uses `<input type="checkbox">` to toggle styles on sibling or child elements — click a box, a menu appears. The x86 CSS emulator treats each checkbox as a single bit. Checked = 1, unchecked = 0. Sixteen bits of register state means sixteen checkboxes per register.

State propagation happens through selector chains. When bit N is set, the CSS engine matches a rule that triggers a visual change on element M — which in turn acts as another bit feeding subsequent rules. This is logic gate emulation through CSS specificity and cascade order. AND, OR, and NOT operations are all expressible this way.

The ALU — the part of a CPU that does actual math — is implemented as a massive selector tree. Adding two 8-bit numbers requires carry propagation logic across eight bit-pairs, each represented as a selector branch. It's hundreds of CSS rules doing what a few transistors do in hardware.

That's the answer to the central question. The emulator is possible because CSS selectors, combined with HTML checkbox state, form a complete logical substrate. Not magic. Just an unusual application of rules the browser already enforces.

---

## Performance: What "Working" Actually Means

Precision matters here, so let's be specific.

The CSS emulator runs x86 instructions at a rate measured in instructions per second, not MHz. A conventional JavaScript x86 emulator — copy.sh's v86 project is the standard reference point — runs at roughly 100–200 MHz in a modern browser on an x86-64 host. On ARM-based hardware with x86 emulation overhead, that number drops to 40–80 MHz, with AVX2 code paths sometimes running slower than SSE2 equivalents due to emulation layer penalties, as documented by RemObjects in their February 2026 analysis of Windows ARM emulation performance.

The CSS emulator doesn't compete with these figures. It's slower by multiple orders of magnitude. Booting a minimal DOS environment takes minutes, not milliseconds.

But performance isn't the relevant measure. The relevant metric is *correctness*. Does it faithfully decode and execute x86 opcodes? Does branch logic work? Does memory addressing follow x86 conventions? The answer to all three is yes — and that's the actual achievement.

---

## The Turing Completeness Connection — and Its Real Limits

The formal basis is solid, but worth qualifying honestly.

CSS with interactive HTML is Turing complete in the same sense that Conway's Game of Life is Turing complete: given enough space and time, it can compute anything. The practical limits are severe. You can't easily implement I/O, the "clock" is user interaction rather than a hardware oscillator, and state space is bounded by DOM size.

The x86 CSS emulator works around the clock problem by requiring user interaction — or automated input simulation — to advance execution cycles. Each clock tick is a CSS transition triggered by a state change. This is fundamentally different from how JavaScript or WebAssembly execute. Both run on an actual event loop with timer resolution down to microseconds.

That constraint means the CSS emulator isn't a practical runtime. It's an existence proof. The distinction matters when evaluating what "runs x86" actually means here.

---

## CSS vs. JavaScript vs. WebAssembly: A Direct Comparison

| Feature | CSS Emulator | JavaScript (v86) | WebAssembly |
|---|---|---|---|
| **Speed** | ~1–10 IPS | 100–200 MHz | Near-native |
| **Dependencies** | None (CSS only) | JS runtime | WASM runtime + JS glue |
| **Turing Complete** | Yes (with HTML state) | Yes | Yes |
| **Practical for prod** | No | Yes | Yes |
| **Sandboxed** | Complete | Yes (JS VM) | Yes |
| **Debugging tools** | Browser DevTools | Browser DevTools | Limited (improving) |
| **Binary compatibility** | Partial x86 | Full x86 | Native target |
| **Best for** | Research / demonstration | Emulation projects | Performance-critical apps |

The CSS approach wins on exactly one axis: it requires zero scripting. Every other metric favors JavaScript or WebAssembly. But that single axis — zero scripting — is what makes this genuinely interesting from a security and sandboxing perspective. A CSS-only compute environment has no script execution surface. That's a non-trivial property in contexts where Content Security Policy restrictions block all JavaScript.

The trade-off is straightforward: use JavaScript emulators like v86 or QEMU.js when you need software that actually runs. Use WebAssembly when you need near-native speed. Use CSS-based computation when you're exploring the theoretical boundaries of declarative systems, or when you need to demonstrate computation in a zero-JS environment.

---

## Who Should Actually Care About This

**Developers and engineers** should pay attention because this project stress-tests assumptions. If you've ever said "CSS can't do X," this is a useful corrective. CSS's computational properties are real and documented — understanding them makes you a sharper debugger of complex selector interactions and specificity bugs.

**Browser engine teams** at Chromium, WebKit, and Gecko should note that Turing-complete selector evaluation carries performance implications. A sufficiently complex CSS document can theoretically cause unbounded computation. This concern isn't new, but the x86 emulator makes it concrete in a way that's difficult to ignore.

**Security researchers** working on CSP and browser sandboxing have the most at stake. A compute substrate with no JavaScript surface area changes the threat model in meaningful ways. CSS-based data exfiltration attacks are already documented — a full computational layer raises that risk profile further.

This approach can fail when you need anything resembling practical throughput, real I/O, or maintainable code. CSS selector chains implementing logic gates are essentially unreadable to anyone unfamiliar with the pattern. Maintenance cost is enormous. The honest answer is that this works as a proof of concept and as an educational tool — not as a production compute strategy.

---

## Practical Implications

**Short-term actions worth taking:**

Read the source code of the CSS x86 emulator directly. The selector architecture is educational regardless of whether you'd build something similar. Review your application's CSP headers and think carefully about what CSS injection could expose, given CSS's demonstrated computational properties.

**Longer-term signals to track:**

Browser engine optimizations — or deliberate throttling — of complex selector chains are likely coming. Engine teams may respond to this class of CSS computation as awareness grows. Expect Chromium or WebKit bug tracker entries flagging this as a performance and security consideration. The WebAssembly Component Model, gaining broader support through 2026, will absorb most legitimate use cases for browser-native compute — making CSS emulators a research curiosity rather than a platform primitive.

**One genuine opportunity:** in locked-down enterprise contexts where JavaScript is blocked entirely, CSS-based logic gates could implement lightweight validation or state machines without touching the script execution surface. Industry reports on zero-trust browser environments suggest this use case is niche but real. The mitigation for the maintenance problem is treating CSS computation as generated output rather than hand-written code — using a higher-level DSL that compiles to CSS selector chains.

---

## What This Actually Proves

Three things are worth internalizing from this project.

CSS is Turing complete with HTML state, and this emulator is the most extreme demonstration of that to date. Performance is orders of magnitude below JavaScript emulators like v86, but correctness — not speed — is the relevant achievement. And the security implications of a zero-JavaScript compute layer in the browser deserve serious attention from anyone designing CSP policy.

WebAssembly remains the practical path for real browser-native compute. But declarative systems are closing conceptual gaps faster than most engineers expected.

The x86 CPU emulator in CSS demonstrates something worth sitting with: computation doesn't care what language you use. Given enough state and enough rules, any sufficiently expressive system computes. CSS just happens to be the most visually verifiable version of that truth.

Stop assuming tool boundaries are hard limits. They usually aren't.

**What's the most surprising CSS behavior you've hit in production? Drop it in the comments.**

---

## References

1. Cook, M. (2004). "Universality in Elementary Cellular Automata." *Complex Systems*, 15(1). — Foundational proof of Rule 110 Turing completeness.
2. RemObjects Software Blog (2026, February 17). "Nerdsniped: Windows ARM Emulation Performance." — AVX2 vs SSE2 performance data under Windows ARM x86 emulation.
3. Wikipedia. "List of computer system emulators." — Reference for v86 and comparable JavaScript-based x86 emulators.
4. W3C. "WebAssembly Core Specification 2.0." Published December 2022. — Baseline for current WASM capability discussion.
5. Schenck, L. et al. (2019). CSS Turing completeness demonstrations — documented via community research into CSS3 + HTML state machines.

---

*Photo by [Akshat Sharma](https://unsplash.com/@asphotographypics) on [Unsplash](https://unsplash.com/photos/black-and-white-spiral-notebook-2FCOT4Xr82E)*
