---
title: "Apple M4 Neural Engine Reverse Engineering Reveals ML Secrets"
date: 2026-03-03T08:38:29+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-ai", "apple", "neural", "engine", "reverse"]
description: "Unlock Apple M4 Neural Engine secrets through reverse engineering and discover how its ML architecture delivers groundbreaking AI performance."
image: "/images/20260303-apple-m4-neural-engine-reverse.webp"
technologies: ["Python", "Linux", "Rust", "Go", "PyTorch"]
faq:
  - question: "Apple M4 Neural Engine reverse engineering secrets ML how does it actually work"
    answer: "The Apple M4 Neural Engine delivers 38 TOPS of ML throughput but Apple publishes no official low-level architecture documentation for developers. Community reverse engineers discovered that the ANE is optimized specifically for channel-first tensor layouts and 1×1 convolution operations, which are architectural preferences baked into the hardware itself. Developers who don't restructure their models around these patterns risk having workloads silently fall back to CPU or GPU with no warning."
  - question: "why won't my CoreML model run on Apple Neural Engine"
    answer: "Apple's CoreML compiler makes ANE routing decisions internally without exposing any explanation to developers, so models can silently fall back to CPU or GPU with zero error or warning. The ANE has strict hardware-level preferences, including channel-first tensor layouts and specific operation types like 1×1 convolutions, and models that don't conform to these patterns are often rerouted automatically. To reliably target the ANE, developers must restructure their PyTorch or CoreML models around ANE-specific architectural patterns."
  - question: "what repositories exist for Apple M4 Neural Engine reverse engineering secrets ML internals"
    answer: "As of early 2026, the most complete public technical map of ANE internals comes from four community repositories: hollance/neural-engine for behavioral benchmarks, eiln/ane from the Asahi Linux project for kernel-level IOKit and memory interface details, mdaiter/ane for additional architectural findings, and Apple's own apple/ml-ane-transformers which confirms key hardware design preferences. Together these represent deeper ANE documentation than anything Apple has officially published for developers. The Asahi Linux driver project in particular surfaces low-level details that no official Apple SDK exposes."
  - question: "how do I force CoreML to use Neural Engine instead of CPU"
    answer: "There is no official API to directly force ANE execution in CoreML, as Apple's compiler makes routing decisions internally without developer control. The most reliable approach is to restructure your model around ANE-preferred patterns such as channel-first tensor layouts and 1×1 convolution operations, which reverse engineering of the M4 ANE has confirmed are architectural requirements rather than optional suggestions. You can verify ANE utilization after the fact using Apple's Instruments tool, but without model restructuring, workloads frequently fall back silently to CPU or GPU."
  - question: "Apple Neural Engine 38 TOPS M4 how to actually use it for ML inference"
    answer: "The M4 Neural Engine is capable of 38 TOPS of ML throughput but most developers fail to access it because Apple provides almost no low-level documentation on how the hardware routes or executes workloads. Community reverse engineering has revealed that standard PyTorch or CoreML models often need to be significantly restructured around ANE-specific operation patterns before the hardware will accept them. Without these optimizations, models silently execute on CPU or GPU instead, resulting in worse performance and higher power consumption."
---

Apple ships tens of millions of M4-class devices every year. Each one contains a Neural Engine capable of 38 TOPS of ML throughput. And most developers are getting zero of it — not because the hardware fails, but because Apple tells you almost nothing about how it actually works.

That gap is what a loose coalition of reverse engineers, Linux kernel contributors, and ML researchers spent early 2026 closing. The findings are scattered across four public repositories. Together, they represent the most complete technical map of ANE internals that exists outside Apple's own walls.

> **Key Takeaways**
> - The Apple M4 Neural Engine delivers up to 38 TOPS of ML throughput, but Apple publishes no official low-level architecture documentation for developers.
> - Community reverse engineering via `hollance/neural-engine`, `eiln/ane` (Asahi Linux), and `mdaiter/ane` together form the most complete public technical map of ANE internals available as of early 2026.
> - Apple's own `apple/ml-ane-transformers` repository confirms that channel-first tensor layouts and 1×1 convolution operations are architectural preferences baked into the ANE hardware design — not optional software suggestions.
> - Kernel-level documentation from the Asahi Linux driver project surfaces IOKit dispatch and memory interface details that no official Apple SDK exposes.
> - Developers targeting ANE must restructure standard PyTorch or CoreML models around ANE-specific patterns — or accept significant performance penalties as workloads silently fall back to CPU or GPU.

---

## Background & Context

Apple introduced the Neural Engine with the A11 Bionic in 2017. Two cores. Narrow use cases. Essentially inaccessible to third-party developers. By the time M1 shipped in late 2020, the ANE had grown to 16-core designs running at 11 TOPS. M4, released in mid-2024 across iPad Pro and MacBook Pro, pushed that to 38 TOPS across a still-undisclosed core configuration.

The problem isn't the hardware. It's the tooling around it.

Apple's developer-facing stack — Core ML, `coremltools`, Create ML — abstracts the hardware almost entirely. You don't target the ANE directly. You compile a model, cross your fingers, and check Instruments to see whether the ANE got used. If it didn't, your model silently fell back to CPU or GPU with zero explanation. No error. No warning. Just worse performance and higher power draw.

This opacity frustrated ML engineers running production inference. CoreML's compiler makes ANE routing decisions internally, but the logic was undocumented. Teams building iOS ML features had no reliable way to ensure ANE utilization without sustained trial and error — which is an expensive way to optimize infrastructure.

The reverse engineering community responded. According to the Hacker News discussion around the M4 ANE series, four repositories emerged as the canonical references:

- **`hollance/neural-engine`** — behavioral benchmarks and supported operation documentation
- **`mdaiter/ane`** — early reverse engineering with working Python and Objective-C code targeting `ANECompiler` and `IOKit` dispatch
- **`eiln/ane`** — Asahi Linux's kernel-level driver, reverse-engineered from bare metal
- **`apple/ml-ane-transformers`** — Apple's own optimized transformer reference, which inadvertently confirmed several architectural constraints the community had already identified

The Asahi Linux work is particularly significant. Building a Linux driver requires understanding memory-mapped interfaces, interrupt handling, and command dispatch at a level Apple's SDK never surfaces. That kernel work became the foundation for everything else.

---

## What the Reverse Engineering Actually Shows

### The ANE isn't a general-purpose compute unit

The clearest finding from community work is structural: the ANE isn't a GPU-style compute unit. It's a fixed-function accelerator with specific dataflow preferences that differ sharply from CUDA or Metal compute.

Two architectural constraints dominate everything:

**Channel-first tensor layout (NCHW).** The ANE processes channels as the primary dimension. Standard PyTorch defaults to NCHW on CPU, but many mobile frameworks default to NHWC. Misaligned tensor formats cause silent fallbacks. Your model keeps running. Just not where you think.

**1×1 convolutions over linear layers.** The ANE's execution units are optimized for convolutional operations. A standard `nn.Linear` layer won't route to the ANE. The same operation expressed as `Conv2d(1, 1, kernel_size=1)` will.

This isn't a quirk or an oversight. It's a deliberate design choice — and Apple's own `ml-ane-transformers` implementation confirms it. Apple rewrote transformer attention and FFN layers as 1×1 convolutions specifically to hit the ANE path. That repository is as close to an official architecture guide as developers have, even though it was published as an "optimization reference."

### The Asahi Linux driver: rare kernel-level insight

The `eiln/ane` repository, developed as part of the Asahi Linux project, is structurally different from user-space reverse engineering. A working kernel driver requires verified understanding of register maps, DMA buffer formats, and interrupt handling. You can't fake it — the hardware either responds correctly or it doesn't.

This work revealed that ANE dispatch involves multi-stage command queue population with specific header formats. The IOKit path Apple uses on macOS wraps this behind several abstraction layers. The Linux driver strips those away.

The practical implication for ML engineers: operations that don't conform to expected buffer formats get rejected at the kernel boundary, not at the model compiler level. CoreML catches these failures silently and reroutes to CPU or GPU. Debugging that with only CoreML tooling isn't just difficult — it's nearly impossible without the kernel-level context the Asahi work provides.

### Apple's ml-ane-transformers: an accidental architecture guide

Apple's repository restructures standard transformer blocks — attention, layer norm, feed-forward — entirely around ANE routing rules. Layer norm becomes a sequence of element-wise operations. Linear projections become 1×1 convolutions. Tensor shapes get explicitly manipulated to maintain channel-first ordering throughout.

Reading this code alongside the community reverse engineering creates a consistent picture: the ANE is powerful but narrow. It rewards models specifically designed for its constraints. Everything else gets penalized.

---

## ANE vs. GPU vs. CPU: The Real Trade-offs

| Criteria | Apple Neural Engine | Apple GPU (M4) | CPU (M4, Performance Cores) |
|---|---|---|---|
| Peak throughput | 38 TOPS | ~5 TFLOPS FP32 | ~1.8 TFLOPS FP32 |
| Power efficiency | Highest | Medium | Lowest |
| Model compatibility | Narrow (specific ops/layouts) | Broad | Broadest |
| Developer visibility | Opaque (no public ISA) | Metal / documented | Standard LLVM |
| Fallback behavior | Silent (no error) | Explicit | Explicit |
| Optimal for | Quantized CNNs, ANE-adapted transformers | General inference, LLMs | Small models, dynamic shapes |
| Debugging tools | Instruments (limited) | Metal Frame Debugger | LLDB / standard |

ANE wins on efficiency — dramatically. But it demands model changes that aren't trivial. A standard HuggingFace transformer loaded via `coremltools` won't hit the ANE without explicit restructuring. The GPU path is far more forgiving. CPU handles everything, but handles it badly.

For production use cases where battery life and thermal headroom matter — on-device inference on iPhone or MacBook — ANE targeting is worth the engineering investment. For prototyping or models with dynamic shapes, GPU fallback is the pragmatic choice. This isn't always the answer, and forcing ANE targeting on the wrong model architecture costs more time than it saves.

---

## Practical Implications

**For ML engineers building CoreML pipelines:** audit whether your models actually hit the ANE. Instruments' Neural Engine trace category shows utilization directly. If it's zero on an M4 device, your ops or tensor formats likely don't conform to ANE routing rules — and the community's documented patterns show exactly where to look.

**For teams shipping iOS/macOS ML features:** the competitive gap is real. Teams that understand ANE constraints can ship faster, lower-power inference than teams relying on default CoreML compilation. That translates to better user experience and lower thermal throttling on sustained workloads — camera, audio, health monitoring, anything running continuous inference.

**Short-term actions worth taking now:**
- Profile existing CoreML models in Instruments specifically for ANE utilization rates
- Review `apple/ml-ane-transformers` for concrete op restructuring patterns
- Test tensor layout alignment — switch linear layers to 1×1 convolutions in candidate models and measure the difference

**Longer-term:**
- Build ANE-aware model design into ML pipeline templates from the start, not as a retrofit
- Track `eiln/ane` and `hollance/neural-engine` for M4-specific updates as hardware analysis deepens
- Watch whether Apple expands Core ML documentation in response to community pressure — WWDC 2026 is the most likely venue

The hardest challenge remains debugging opacity. Silent fallbacks are the worst class of performance bug to catch. A model that *works* but runs entirely on CPU wastes the hardware and drains battery — and nothing tells you it happened unless you're actively profiling. Build ANE utilization checks into CI pipelines. Don't wait to discover it in production.

---

## What Comes Next

The community has done something Apple hasn't: produced a usable technical map of how the ANE actually works. Channel-first layouts, 1×1 convolution patterns, kernel-level buffer alignment requirements — all documented, all confirmed by Apple's own reference code even when not explicitly stated.

Over the next 6-12 months, expect more M4-specific analysis as Asahi Linux support deepens and more developers run structured benchmarks. Apple will likely respond at WWDC 2026 with expanded Core ML documentation — community pressure on ANE transparency has been building for two years. Whether that means opening the ISA or just improving tooling is the key open question.

The hardware is already in hundreds of millions of devices. The patterns are documented. The only thing missing is developers using them.

Check your ANE utilization rate on M-series devices. That single number tells you exactly where to start.

---

*Photo by [BoliviaInteligente](https://unsplash.com/@boliviainteligente) on [Unsplash](https://unsplash.com/photos/an-apple-m4-processor-in-front-of-a-computer-circuit-8-GcGLKBk0s)*
