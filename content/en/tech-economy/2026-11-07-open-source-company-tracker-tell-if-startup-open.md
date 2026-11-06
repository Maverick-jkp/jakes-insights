---
title: "Open Source Company Tracker: How to Tell If a Startup Is Actually Open Source"
date: 2026-11-07T02:34:46+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-web", "open", "source", "company"]
description: "Most 'open source' startups in 2026 aren't. Use this open source company tracker to spot open-washing before it locks you into the wrong infrastructure."
image: "/images/20261107-open-source-company-tracker.webp"
faq:
  - question: "How do you actually verify a startup's code is open source?"
    answer: "Check three things: whether model weights, training code, and training data documentation are all publicly available under an OSI-approved license. Publishing weights alone — which most companies do — doesn't meet the Open Source Initiative's formal AI Definition 1.0 from October 2024. If any of those three elements is missing or restricted, the project is open-weights at best, not open source."
  - question: "What is open-washing and why should I care about it?"
    answer: "Open-washing is when a company markets itself as open source while keeping critical components — like training data or inference code — proprietary. It matters because building your infrastructure on an open-washed product carries the same vendor lock-in risk as any closed system. The EU AI Act also grants real regulatory benefits only to genuinely open-source models, so the label has legal weight now, not just reputational weight."
  - question: "Is Llama actually open source or just free to download?"
    answer: "Llama is open-weights, not open source — there's a real difference. Meta releases the model files, but the training data and full pipeline aren't publicly documented to the standard required by the OSI AI Definition 1.0, and earlier versions carried commercial use restrictions. Models like OLMo and Pythia cleared that bar; Llama hasn't."
  - question: "Does an OSI-approved license automatically mean open source for AI models?"
    answer: "Not quite — the license is necessary but not sufficient. The OSI's 2024 AI definition requires weights, complete code, and training data documentation together, so a permissive license on weights alone still falls short. A company can ship under Apache 2.0 and still be open-washing if the training pipeline is a black box."
  - question: "Why are so many AI companies suddenly calling themselves open source in 2026?"
    answer: "The EU AI Act offers lighter regulatory obligations to genuinely open-source AI systems, which created a strong financial incentive to claim the label. Radboud University's European Open Source AI Index found a consistent pattern: companies publish weights, announce openness loudly, then keep training data and code entirely closed. The regulatory carrot predictably produced a lot of open-washed branding."
---

Most startups calling themselves "open source" in 2026 aren't.

They're open-weights at best, open-washed at worst — and the difference carries real consequences for your infrastructure decisions, compliance posture, and vendor lock-in risk.

The EU AI Act grants lighter regulatory obligations to genuinely open-source models. That regulatory carrot has predictably created a surge of "open" branding with zero accompanying substance. According to Radboud University's European Open Source AI Index, researchers find a consistent pattern across AI releases: companies publish model weights, declare openness in their press releases, then keep training data and code entirely proprietary. That's not open source. That's marketing.

Using a systematic framework to evaluate whether a startup is actually open source isn't optional anymore. It's how you avoid betting your production stack on a closed system wearing an open-source costume.

**In brief:** The Open Source Initiative's formal AI Definition 1.0 (October 2024) requires three elements — weights, complete training and inference code, and sufficient training data documentation — yet most "open" releases deliver only the first. This gap determines offline capability, auditability, and regulatory classification.

Three things you need to know going in:
1. The OSI AI Definition 1.0 sets a clear three-part bar that most "open" releases fail to clear.
2. Radboud University's European Open Source AI Index scores models across 14 openness dimensions, exposing open-washing patterns with objective data.
3. Six concrete verification checks exist that any engineer can run in under 20 minutes.

---

## How "Open Source" Became a Marketing Term

For traditional software, open source meant one thing: source code you could read, modify, and redistribute under an OSI-approved license. Apache 2.0. MIT. GPL. The definition was crisp.

AI changed the picture fast. When Meta released Llama 2, the press called it open source. Technically, it was open weights — downloadable model files under a custom license that restricted commercial use for companies above a certain scale. When Mistral shipped Mixtral, same story. These are genuinely useful releases, but they're not open source by any definition that existed before 2023.

The Open Source Initiative published its formal AI Definition 1.0 in October 2024 specifically to address this drift. The OSI definition requires three things: model weights, complete training *and* inference code, and enough training data documentation for a skilled practitioner to independently replicate the system. Models that cleared this bar include Pythia, OLMo, Amber, CrystalCoder, and T5. Llama 2, Grok, Phi-2, and Mixtral failed — missing components or carrying restrictive licensing terms.

The regulatory dimension sharpened the stakes. The EU AI Act offers reduced compliance obligations to open-source systems but contains no internal definition of what "open" means. That gap is an incentive structure for misrepresentation, and companies have responded accordingly.

---

## The Three-Tier Reality Behind Every "Open" Announcement

When a startup announces an open-source release, it's almost always one of three things. Understanding which one changes everything.

**Fully open source** means weights, training code, and training data are all accessible under an OSI-approved license. OLMo from Ai2 is the benchmark here — weights and code under Apache 2.0, training data via the published Dolma dataset. You can replicate the system from scratch. This is rare.

**Open weights** means downloadable model files, typically with an MIT or custom license, but no training code or data disclosure. DeepSeek-V4.1-Flash, scored in October 2026, falls here: MIT license, free downloads, 763B parameters — but zero training data or code disclosure. According to Radboud University's European Open Source AI Index, this is the most common pattern. You can run inference. You can't audit or replicate.

**Open-washed** means the press release says "open source" and nothing else does. Ultramarine 1 Flash, also reviewed in October 2026, launched with an "open-source" announcement while providing no downloadable weights, no license, and no published code at time of review. API-only. That's a closed product with open branding.

So the core tracker question becomes: which tier are you actually looking at?

---

## Six Verification Checks (Run These Before You Commit)

No tracker tool replaces direct verification. These six checks take under 20 minutes and answer the question definitively.

| Check | What to Look For | Passes | Fails |
|-------|-----------------|--------|-------|
| **Downloadable weights** | HuggingFace "Files and versions" tab | `.safetensors` or `.gguf` files, non-gated | Gated access, API-only |
| **License terms** | License file in repo | Apache 2.0, MIT, GPL | Custom clauses, user caps |
| **Training code** | Full training scripts, not just inference | Complete pipeline published | Inference-only release |
| **Training data** | Specific dataset names and sources | Named datasets (e.g., Dolma) | "Large web mix" or similar |
| **Offline capability** | Disable Wi-Fi, run the model | Works fully offline | Requires company servers |
| **Third-party rating** | European OS AI Index, Linux Foundation MOT | High openness score | Not rated or low score |

Llama 4's custom license illustrates what a license failure looks like in practice: it restricts companies with 700M+ monthly active users, requires "Built with Llama" attribution, and mandates that derivative models include "Llama" in their name. The OSI explicitly stated these terms fail the Open Source Definition. That's not open source — that's a franchise agreement.

---

## The Regulatory Incentive Driving Open-Washing

The EU AI Act created a legal arbitrage opportunity. Open-source models face lighter obligations. The Act has no formal openness definition. The result: companies have direct financial incentive to claim openness without meeting any standard.

According to Radboud University's research, this open-washing pattern appears consistently across releases. MiniCPU-V 4.7, for example, achieves open-weights status and runs on consumer hardware including mobile devices — genuinely useful. But it withholds training details entirely. The marketing says "open." The OSI definition says otherwise.

This approach can fail enterprise teams in ways that go beyond philosophy. Models you can't audit carry unknown training provenance. Models requiring company servers create vendor dependency. Models with restrictive licenses create legal exposure when you scale. None of these risks are theoretical at this point — they're appearing in procurement reviews and compliance audits right now.

---

## Three Scenarios That Change Your Decision

**Scenario 1 — You're evaluating a startup's infrastructure claim.** A vendor says their AI tooling is "fully open source." Run the six-check list before the second sales call. If weights aren't on HuggingFace without gating, the conversation about "openness" is over. Ask for the specific dataset names used in training. Vague answers confirm closed training data.

**Scenario 2 — You're assessing regulatory risk.** "Open source" claims from vendors aren't self-certifying under EU AI Act requirements. Cross-reference against the Linux Foundation's Model Openness Tool or the European Open Source AI Index before accepting any compliance argument based on a model's supposed open status. This isn't bureaucratic caution — it's the difference between a defensible audit trail and a liability.

**Scenario 3 — You're choosing between open-weights and fully open.** For most production use cases, open-weights is probably enough. You can run inference offline, audit output behavior, and avoid cloud dependency. The gap matters most when you need to retrain, fine-tune at the data level, or prove full auditability to regulators. OLMo-class fully open models are the only viable choice for that last scenario.

**What to watch:** The EU AI Act's definition gap will likely get patched in 2027 guidance documents. Watch for formal openness criteria to emerge from the European AI Office. When that happens, open-washing carries legal consequence, not just reputational risk.

---

## What Comes Next

The OSI AI Definition 1.0 gives you the standard. The European Open Source AI Index gives you scored comparisons. And six concrete checks give you the ability to verify any claim in under 20 minutes.

> **Key Takeaways**
> - Three tiers exist: fully open, open-weights, and open-washed — most "open" releases land in the middle tier
> - OSI validation passed for OLMo, Pythia, and T5; failed for Llama 2, Mixtral, and Grok
> - Regulatory arbitrage under the EU AI Act is actively driving open-washing in 2026
> - License terms alone don't determine openness — training code and data disclosure do

Over the next 6–12 months, expect the European AI Office to publish formal openness criteria, which will force clearer disclosure from vendors. The Linux Foundation's Model Openness Tool will likely become the de facto enterprise standard for scoring claims. That's good news — but it won't help you with the vendor call you have next week.

The action item is simple: before trusting any "open source" claim from a startup, run the six-check list. Downloadable weights, OSI license, training code, training data, offline capability, third-party rating. If a company can't clear all six, their definition of open source isn't yours.

---

*Sources: Alex Veremeyenko's open-source AI evaluation framework | Radboud University European Open Source AI Index | Open Source Initiative AI Definition 1.0 (October 2024)*

## References

1. [How I Vet an Open-Source Dependency Before Betting On It - DEV Community](https://dev.to/hoelee/how-i-vet-an-open-source-dependency-before-betting-on-it-73f)
2. [Open-source software - Wikipedia](https://en.wikipedia.org/wiki/Open-source_software)
3. [Council Post: Open-Source Dependencies: 19 Trust Signals Worth Checking](https://www.forbes.com/councils/forbestechcouncil/2026/11/05/open-source-dependencies-19-trust-signals-worth-checking/)


---

*Photo by [Vishnu Mohanan](https://unsplash.com/@vishnumaiea) on [Unsplash](https://unsplash.com/photos/a-close-up-of-a-printed-circuit-board-vE6WEdZA6Vg)*
