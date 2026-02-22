---
title: "# How Taalas Prints an LLM onto a Chip With $169M in Funding"
date: 2026-02-22T19:30:17+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["How", "Taalas", "prints"]
description: "Discover how Taalas prints LLM onto a chip, revolutionizing AI deployment with faster, efficient on-device intelligence. Learn the process now."
image: "/images/20260222-how-taalas-prints-llm-onto-a-c.jpg"
technologies: ["GPT", "OpenAI", "Anthropic", "Go", "Llama"]
faq:
  - question: "How Taalas prints LLM onto a chip and why does it matter"
    answer: "Taalas physically encodes LLM weights into the silicon structure of a custom ASIC using analog resistor networks and fixed-function datapaths, meaning the model is permanently hardwired rather than loaded from memory at runtime. This eliminates the need for HBM or external weight storage entirely, resulting in dramatically lower power consumption, latency, and cost per inference token. The company raised $169 million in early 2026 to commercialize this approach."
  - question: "what is the difference between Taalas AI chip and Nvidia H100 for inference"
    answer: "Nvidia's H100 is a general-purpose AI accelerator that can load and run any model by storing weights in high-bandwidth memory, making it flexible but memory-bandwidth-constrained. Taalas takes the opposite approach by hardwiring a single specific LLM directly into the chip's physical transistor layout, which removes memory bottlenecks entirely but means the chip can only ever run one fixed model. For high-volume inference on a deployed, stable model, Taalas's architecture could offer significant efficiency advantages over general-purpose chips."
  - question: "How Taalas prints LLM onto a chip using analog computing"
    answer: "Taalas likely encodes model weights as physical resistor values in analog circuits, where a single transistor can perform a multiplication operation at a fraction of the power cost of traditional digital multiply-accumulate operations. Log-domain arithmetic further reduces computational complexity within the fixed datapath. Because the weights are baked into the physical structure rather than stored digitally, no programmable memory or weight-loading step is required at inference time."
  - question: "can Taalas chip be used for training AI models"
    answer: "No, Taalas chips are architecturally incapable of training AI models because the weights are permanently encoded into the physical silicon and cannot be updated or rewritten. The chip is designed exclusively for inference on a single, fixed, already-trained model version. Any updates to the underlying model would require a completely new chip to be manufactured."
  - question: "what happens to Taalas chip when the AI model becomes outdated"
    answer: "Because each Taalas chip is hardcoded to a specific model version, it carries zero residual value once that model is superseded by a newer or better-performing version. This model obsolescence risk is considered the primary economic downside of the approach, as the physical chip cannot be reprogrammed or reused for a different model. The business case therefore depends heavily on deploying chips against models with long, stable production lifespans."
---

Taalas just raised $169 million to do something most chip engineers considered a category error: permanently bake a specific LLM into silicon. Not "optimized for AI workloads." Not "runs transformers efficiently." Literally hard-wired — weights, architecture, and all — into the physical transistor layout of a custom ASIC.

That's a different bet entirely.

Most of the AI chip industry in early 2026 is still fighting the same war: more SRAM bandwidth, better memory hierarchies, faster HBM interconnects. Nvidia's H100 and B200 ecosystems dominate training. Even inference-focused players like Groq and Cerebras are building general-purpose fast-memory chips that can load *any* model. Taalas is going the opposite direction. One chip. One model. No reloading weights. No HBM at all.

The thesis is straightforward: if the model never changes, you don't need programmable memory. Encode the weights into the chip's physical structure — analog resistor networks, log-domain arithmetic, fixed-function datapaths — and you get radical efficiency gains on inference. Power consumption drops. Latency drops. Cost per token drops.

Whether that trade-off makes economic sense at scale is the real question. And it's not obvious.

---

> **Key Takeaways**
> - Taalas raised $169 million in early 2026 to build ASICs where LLM weights are physically encoded into the chip's silicon structure, eliminating the need for HBM or external weight storage entirely.
> - The core mechanism likely involves analog computing techniques — resistor network weight encoding and log-domain arithmetic — enabling single-transistor multiplication at a fraction of the power cost of digital MAC operations.
> - Because the model is non-rewritable, Taalas chips are viable exclusively for inference workloads on fixed, deployed models. Training is architecturally impossible on this approach.
> - Developer comparisons to Nintendo DS cartridges and H.264 media processor ASICs frame Taalas as a natural evolution of fixed-function hardware — not a fringe idea.
> - The primary economic risk is model obsolescence: a chip hardcoded to a specific model version carries zero residual value once that model gets superseded.

---

## Fixed-Function Hardware Isn't New. The Target Is.

Fixed-function acceleration for compute-intensive tasks has a long track record. The H.264 video codec ASIC is the clearest precedent. When mobile video encoding became ubiquitous around 2010–2015, chip designers didn't build general-purpose processors fast enough to handle it in real time — they built dedicated silicon that did *one thing* with extreme efficiency. Your iPhone's media engine still has dedicated fixed-function blocks for AV1, HEVC, and ProRes. You can't reprogram them. You don't need to.

The same logic drove early GPU design, then TPUs for matrix math, then Apple's Neural Engine. Each generation of fixed-function acceleration trades flexibility for efficiency. Taalas is taking that curve to its logical extreme for LLM inference.

The specific trigger in 2026 is the economics of inference at the edge. Cloud-based LLM inference via API — OpenAI, Anthropic, Google — costs money per token and requires internet connectivity. As LLMs move into embedded systems, IoT devices, automotive hardware, and consumer products, the demand for local inference with near-zero marginal cost per query is real and growing. Groq's LPU approaches this from the programmable-chip direction. Taalas approaches it from the opposite end: eliminate the memory bottleneck entirely by making the weights part of the chip itself.

The $169M raise, reported by Yahoo Finance in 2026, signals that serious capital thinks this wedge is viable. The investor thesis presumably rests on enterprise or OEM deals where a specific model version gets locked for a product lifecycle — think automotive ECUs or industrial controllers, not consumer smartphones where users expect the latest model.

Mythic AI explored analog weight storage earlier and pivoted. That Taalas is raising at this scale suggests differentiated IP in the encoding mechanism itself.

---

## How Taalas Actually Encodes Weights Into Silicon

The phrase "prints the model onto the chip" sounds like marketing until you understand the physical mechanism.

Transformer model weights are, fundamentally, matrices of floating-point numbers. In a standard inference chip, those weights live in SRAM or HBM — loaded, read, and multiplied against input activations at runtime. The memory access cost, both in power and latency, is the bottleneck. Taalas eliminates that step.

The most plausible mechanism, consistent with what's technically feasible and what developer discussions on forums like r/singularity have explored, is **analog weight storage via resistor networks**. Weight values get encoded as physical conductance values in the chip's interconnect layer. When current flows through the network, Ohm's law performs the multiplication — current times conductance equals the weighted output. No clock cycles for a MAC operation. No memory fetch. The computation *is* the circuit.

Paired with **log-domain arithmetic** — where multiplication becomes addition in the logarithmic domain — you can further reduce transistor count per operation. Single-transistor multiplication becomes physically achievable.

The trade-off is noise sensitivity and limited precision. Analog circuits drift. Temperature changes resistance. This is exactly why digital chips won the last 40 years of computing: they're deterministic.

For LLMs, the precision tolerance is more forgiving than scientific computing. Quantized models running at INT8 or INT4 already demonstrate that 4–8 bits of precision is often sufficient for inference quality. Analog encoding at that precision range is more tractable than full FP32. It's not a solved problem, but it's not physically implausible either.

---

## Why "No HBM" Is the Key Technical Claim

HBM is expensive — in dollars and in power. An H100 SXM5 carries 80GB of HBM3e running at roughly 3.35 TB/s bandwidth. That bandwidth costs approximately 300–400W just for the memory subsystem on high-end configurations. For inference on a fixed model, you're spending all that power streaming weights you already know into compute units.

If the weights are encoded in the analog fabric of the chip itself, weight "retrieval" is instantaneous — it's literally just the resistance of a wire. Power consumption for weight access drops to near zero. This is why Taalas's efficiency claims aren't implausible on their face. The physics supports it, specifically for fixed-model inference.

The constraint is obvious: you can't change the weights. The chip *is* the model. A firmware update that improves model quality requires a new chip.

---

## Where the Fixed-Function Analogy Breaks Down

ALUs, FPUs, H.264 encoders, AV1 decoders — all fixed-function. All extraordinarily efficient for their target workload. All completely useless outside it. The historical pattern is consistent: fixed-function hardware wins on efficiency when the target computation is stable and high-volume.

LLMs have a stability problem that video codecs never did.

GPT-4 got superseded. Llama 2 got superseded by Llama 3, then 3.1, then a cascade of derivative fine-tunes. The model improvement cycle across 2024–2026 has moved faster than any previous software category. A chip hardcoded to `llama-3.1-70B-instruct` has a useful life tied directly to how long that specific checkpoint remains the preferred option for its target application.

This is where the Nintendo DS cartridge analogy from developer discussions is both apt and limited. DS cartridges were fixed-function per game — but games don't get superseded by better versions of themselves the way ML models do. A DS title from 2006 still performs as intended. An inference chip for a model that's been replaced by a successor with 3x better performance on standard benchmarks is just e-waste.

The economics work if — and this is the critical assumption — deployment use cases exist where model version stability is acceptable for 3–5 years. Automotive and industrial controls are the obvious candidates. Enterprise compliance environments where a model needs to be auditable and frozen also fit. Consumer applications almost certainly don't.

---

## Hardcoded ASIC vs. Programmable Inference Accelerators

| Criteria | Taalas Hardcoded ASIC | Groq LPU | Nvidia H100 (Inference) |
|---|---|---|---|
| **Weight Storage** | Encoded in silicon (analog) | SRAM on-chip | HBM3e external |
| **Model Flexibility** | Zero — one model per chip | Any model, load at runtime | Any model |
| **Inference Latency** | Potentially sub-millisecond | ~0.5–1ms (single token) | 5–20ms (single token) |
| **Power per Token** | Extremely low (theoretical) | Low | High |
| **Training Support** | None | None | Full |
| **Model Update Path** | New chip required | Firmware/software load | Firmware/software load |
| **Best For** | Edge inference, fixed-model products | Low-latency API inference | Training + flexible inference |

The comparison is sharp. Groq's LPU architecture — deterministic, SRAM-based, no external memory — is already pushing toward the efficiency frontier for programmable inference. Taalas's bet is that even Groq's approach leaves power and cost on the table because of programmability overhead. That may be true. But Groq can update its model without new hardware. Taalas can't.

For enterprise cloud inference, Groq or H100 clusters win on flexibility. For embedded, high-volume, stable-model deployments, Taalas's unit economics could be compelling — *if* the analog precision holds under real-world silicon conditions and the target model stays relevant long enough to justify the NRE cost.

---

## Who Should Actually Care About This

**Developers and ML engineers** building inference pipelines should watch the precision benchmarks when Taalas publishes them. Analog weight encoding introduces non-determinism. If your application requires deterministic outputs — compliance systems, safety-critical infrastructure — that's a hard constraint. If your application tolerates slight output variance, which most consumer-facing LLM products demonstrably do, it's less of an issue.

**Hardware product teams** at automotive OEMs, industrial IoT companies, and consumer electronics manufacturers should be evaluating their 2027–2028 inference requirements now. If the model being deployed is likely to stay fixed for a product lifecycle, Taalas's power and cost profile could be genuinely attractive.

**AI infrastructure investors** should pay attention to which model categories Taalas is targeting first. The $169M raise implies at least some design wins or letters of intent are in hand. The specific model checkpoint they're hardcoding first reveals a lot about their go-to-market thesis.

---

## The Opportunity and the Risk, Plainly Stated

**The opportunity is real.** For any product shipping millions of units with on-device AI, even a 10x reduction in inference power translates directly to battery life, thermals, or cost savings that affect product margins. If Taalas's power claims hold under real-world silicon validation, OEM demand could be substantial.

**The risk is also real.** The hardcoded approach creates a new category of tech debt. Shipping a product with a fixed-model chip means the AI component can't improve post-shipment. Customers who expect software-like update cycles will push back hard. Product teams need to set expectations clearly upfront — and verify that their deployment horizon actually matches the chip's useful life.

There's one scenario where the limitation becomes an asset: regulated industries. Healthcare, finance, and defense increasingly require auditable, frozen model deployments. A chip that *can't* update the model is a compliance feature in those contexts, not a constraint.

---

## What Comes Next

The core insight is this: Taalas isn't installing software onto a chip. The company is encoding weight values into the analog conductance properties of silicon fabric, making the model physically inseparable from the hardware. That's architecturally distinct from every other inference accelerator currently on the market.

Over the next 6–12 months, silicon benchmarks will be the deciding data. The gap between theoretical analog efficiency and real-world noise-tolerant performance is significant — that data will determine whether the $169M was well-placed. If the benchmarks hold, automotive and industrial OEM design wins should follow within 12–18 months of tape-out.

Taalas isn't trying to beat Nvidia at the general-purpose AI chip game. The company is carving out a narrow but defensible wedge where model stability meets power-constrained deployment. That wedge might be smaller than a $169M raise implies. Or it might be exactly where the next 500 million AI-enabled devices get their inference done.

The physics are credible. The market timing is plausible. The model obsolescence risk is real and not fully priced in by anyone yet.

Watch the benchmarks.

---

*References: Taalas $169M raise — Yahoo Finance (2026); architectural discussion — r/singularity via Reddit; WCCFTech coverage of Taalas silicon approach (2026).*

## References

1. [This New AI Chipmaker, Taalas, Hard-Wires AI Models Into Silicon to Make Them Faster and Cheaper; Ea](https://wccftech.com/this-new-ai-chipmaker-taalas-hard-wires-ai-models-into-silicon-to-make-them-faster/)
2. [r/singularity on Reddit: Taalas: LLMs baked into hardware. No HBM, weights and model architecture in](https://www.reddit.com/r/singularity/comments/1r9frzk/taalas_llms_baked_into_hardware_no_hbm_weights/)
3. [Chip startup Taalas raises $169 million to help build AI chips to take on Nvidia](https://finance.yahoo.com/news/chip-startup-taalas-raises-169-160249219.html)


---

*Photo by [Merakist](https://unsplash.com/@merakist) on [Unsplash](https://unsplash.com/photos/assorted-color-digital-nomad-letter-decor-zY7b8rTra3A)*
