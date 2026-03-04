---
title: "When AI Writes Software, Who Verifies Correctness?"
date: 2026-03-04T19:48:07+0900
draft: false
author: "Jake Park"
categories: ["tech"]
tags: ["subtopic-ai", "writes", "software", "Python"]
description: "40% of code is now AI-assisted. But who verifies it's actually correct? Explore the formal verification gap threatening production software quality."
image: "/images/20260304-when-ai-writes-software-who-ve.webp"
technologies: ["Python", "AWS", "Go", "Copilot", "Cursor"]
faq:
  - question: "when AI writes software who verifies correctness formal verification explained"
    answer: "When AI writes software, verifying correctness falls to a combination of traditional testing and formal verification tools like Lean, Coq, and TLA+. Formal verification uses mathematical proof to guarantee code behaves as specified, not just in tested cases. However, current tools require significant human effort and don't yet scale easily to all AI-generated code."
  - question: "what is formal verification and why does it matter for AI generated code"
    answer: "Formal verification is a technique that mathematically proves software correctness by checking that an implementation satisfies a written specification, leaving no edge cases unexamined. It matters for AI-generated code because traditional testing can only catch bugs in scenarios developers think to test, not prove their absence. As AI produces more than 40% of code in assisted repositories, formal verification is considered the only method capable of truly certifying correctness at scale."
  - question: "can AI generated code be trusted without formal verification"
    answer: "AI-generated code can look syntactically clean and logically structured without being provably correct, making reliance on appearance alone risky. Traditional testing improves quality but cannot guarantee the absence of bugs, especially in critical systems like medical devices or financial infrastructure. Experts like Lean creator Leonardo de Moura argue that solving formal proof is a prerequisite for safely deploying AI-written software at scale."
  - question: "when AI writes software who verifies correctness if testing isnt enough"
    answer: "When AI writes software faster than humans can review it, testing alone creates a verification bottleneck because it only covers anticipated scenarios. Formal verification tools such as TLA+, Coq, and Lean can fill this gap by mathematically proving correctness, as demonstrated in Amazon's S3 and DynamoDB protocols. The most promising near-term solution is AI-assisted formal verification, where models generate both code and corresponding correctness proofs simultaneously."
  - question: "what are the limitations of formal verification tools like Lean Coq TLA+"
    answer: "Tools like Lean, Coq, and TLA+ are highly effective within narrow, well-defined domains but currently require significant human expertise and effort to apply broadly. They don't yet scale easily to full-stack or general systems code without substantial manual work, limiting their widespread adoption. This gap between their theoretical power and practical usability is one of the central challenges in verifying AI-generated code at scale."
---

AI is writing more production code than ever. The verification gap — proving that code is actually *correct* — hasn't been solved. And that's becoming a serious problem.

According to GitHub's 2025 Octoverse report, over 40% of code committed in repositories using Copilot was AI-assisted. That number is climbing fast in 2026. The models are getting better at writing syntactically clean, logically structured code. But "looks right" and "is provably correct" are very different things. As AI-generated code enters more critical systems — financial infrastructure, medical devices, aerospace software — the question of *who verifies correctness* matters enormously.

The core tension: AI generates code faster than humans can review it. Traditional testing catches many bugs but can't prove their absence. Formal verification can — but it doesn't scale easily. Something has to give.

This piece covers why testing alone isn't enough when AI writes software at scale, what formal verification actually offers and where it falls short today, how the field is evolving, and what engineers and engineering leaders should do right now.

> **Key Takeaways**
> - Over 40% of code in AI-assisted repositories is AI-generated (GitHub Octoverse 2025), creating a verification bottleneck that traditional code review can't keep pace with.
> - Formal verification uses mathematical proof to guarantee correctness — not just test coverage — making it the only technique that can truly certify AI-generated code at scale.
> - Leonardo de Moura, creator of the Lean proof assistant, argues publicly that AI writing software at scale *requires* solving the formal proof problem first — otherwise correctness guarantees collapse entirely.
> - Current formal verification tools (Lean, Coq, TLA+) cover narrow domains well but don't yet apply broadly to full-stack or systems code without significant human effort.
> - The most credible near-term path is AI-assisted formal verification — models that generate both code *and* correctness proofs simultaneously.

## How We Got Here

Software verification has always been a weak link. For decades, the industry settled on a practical compromise: write tests, run them, ship it. Test-driven development, integration suites, and fuzzing all improved quality. But they share a fundamental limitation — they can only test the cases you think to test.

Formal verification has existed since the 1970s. The idea is mathematically rigorous: write a *specification* of what the code should do, then prove the implementation satisfies that specification. No edge case left unexamined. Tools like Coq (developed at INRIA), TLA+ (Leslie Lamport's work at Microsoft Research), and Lean (built by Leonardo de Moura, now at AWS) have seen real adoption in high-stakes domains. Amazon used TLA+ to verify distributed systems protocols in S3 and DynamoDB. The seL4 microkernel was fully formally verified in 2009.

Impressive results. But each required enormous human effort, domain-specific expertise, and years of work. That tradeoff made sense when humans wrote software at human speed.

Now AI writes software at machine speed. The volume of unverified code entering production is scaling faster than any review process can handle. Christian Szegedy, formerly of Google Brain, has been vocal about this since at least 2023 — arguing that AI-generated code without formal verification is building on sand. De Moura made the same case publicly in early 2026: AI will write most of the world's software, but only if the proof problem gets solved first.

The timing matters. 2026 is when this concern shifted from theoretical to operational. Companies are actually deploying AI-generated code into critical paths now, not just experimenting.

## Why Testing Can't Keep Up

Testing scales linearly with engineer effort. AI code generation scales exponentially with compute. That's an arithmetic problem.

Consider a moderately complex AI-generated function with 10 input parameters, each with 10 valid values. Exhaustive testing requires 10 billion test cases. Nobody runs that. Instead, engineers sample the space and hope they've covered the important cases. That works reasonably well when humans write code — because human developers usually understand what the edge cases *are*.

AI models don't reason about edge cases the same way. They generate code that satisfies the training distribution. If the training data under-represented certain error conditions, the generated code might handle them incorrectly — and do so in ways that look entirely plausible during review. AWS's 2024 internal analysis, cited in their re:Invent talks, found that AI-generated code had similar defect density to human code, but the *type* of defects differed: AI code showed higher rates of subtle logical errors and fewer syntactic mistakes.

Subtle logical errors are exactly what testing is worst at catching.

## What Formal Verification Actually Provides

Formal verification doesn't test code. It *proves* it. The distinction matters more than it might seem.

When Amazon's team used TLA+ to verify their distributed consensus protocol, they found 10 bugs — including one that had survived years of testing and code review. Those bugs weren't visible through normal inspection. They only appeared under specific interleavings of concurrent operations that tests hadn't exercised.

That's the value proposition. For the question of *when AI writes software, who verifies correctness*, formal verification is the only technique that answers: nobody needs to — the math does.

But current tooling has real limits. Writing formal specifications is hard, often harder than writing the code itself. Lean and Coq require expertise that's rare outside academic and research settings. TLA+ is more accessible but works best for protocol-level reasoning, not algorithmic correctness. The gap between "this is theoretically possible" and "an average engineering team can actually do this" remains wide.

This approach can also fail when specifications are themselves incorrect — a formally verified implementation of a wrong spec is still wrong. Garbage in, proof out.

## AI-Assisted Formal Verification: Where the Field Is Headed

The most significant development in 2026 is using AI to *write* formal proofs, not just code. This is where momentum is building fast.

Lean 4, released in mature form in late 2023, has become the focal point for this work. DeepMind's AlphaProof system demonstrated in 2024 that language models could generate valid Lean proofs for competition-level mathematics. The jump from math competition problems to software verification proofs is non-trivial — but the architectural path is clear.

Microsoft Research's work on Copilot combined with formal verification, announced in late 2025, takes a different angle: generating lightweight *contracts* alongside code — preconditions, postconditions, invariants — that can be checked automatically without full proof. It's weaker than complete formal verification but dramatically more practical for teams that aren't staffed with proof engineers.

This isn't always the answer, though. AI-generated proofs can be subtly wrong in ways that pass automated checkers — a known failure mode in the AlphaProof research. The confidence that comes from "the model proved it" is only as good as the proof-checking infrastructure underneath it.

## Verification Approaches: A Practical Comparison

| Approach | Correctness Guarantee | Tooling Maturity | Engineer Effort | Best For |
|---|---|---|---|---|
| Unit/Integration Testing | Partial (sampled) | High | Low-Medium | General application code |
| Property-Based Testing (QuickCheck/Hypothesis) | Partial (broad) | Medium | Medium | Algorithmic functions, parsers |
| Static Analysis (Semgrep, CodeQL) | Narrow (pattern-matched) | High | Low | Security vulnerabilities, common bugs |
| Lightweight Contracts (Dafny, Copilot+) | Partial (specified) | Medium | Medium | Critical functions with clear specs |
| Full Formal Verification (Lean, Coq, TLA+) | Complete (proven) | Low-Medium | Very High | Safety-critical, distributed protocols |
| AI-Generated Proofs (AlphaProof-style) | Complete (if proof checks) | Emerging | Low (when it works) | Math-heavy, well-specified code |

The analysis isn't about picking one row. It's about matching the verification approach to the risk profile of the code. AI-generated UI components don't need TLA+. AI-generated consensus algorithms probably do.

## Who Should Care — And What To Do About It

**Developers and engineers** working in safety-critical or high-availability domains need to understand this now. If you're using Copilot or Cursor to generate systems code, distributed algorithms, or anything touching financial transactions, your testing regime needs to account for the specific failure modes of AI-generated code — subtle logical errors in edge cases, not syntactic blunders.

**Engineering leaders** face a structural decision. The speed gain from AI code generation is real. The verification gap is also real. Shipping faster with less confidence in correctness is a legitimate business choice in some contexts — a wrong one in others. The organizations that will get hurt are the ones who don't make that tradeoff consciously.

**End users** of software in regulated industries — healthcare, finance, aerospace — should push companies to answer clearly: when AI writes your software, who verifies correctness? If the answer is "our existing QA process," that's worth scrutinizing hard.

**Short-term actions (next 1-3 months):**
- Audit which parts of your codebase AI tools are contributing to most heavily
- Apply property-based testing (Python's Hypothesis, Haskell's QuickCheck) to AI-generated algorithmic code — it's a practical step up from unit tests with minimal tooling overhead
- Start tracking defect sources: is AI-generated code failing in production at different rates or with different error types than human-written code?

**Longer-term investments (next 6-12 months):**
- Evaluate Dafny or lightweight contract tooling for critical-path functions — Microsoft has been investing in accessibility here
- Follow Lean 4 and AI proof-generation developments closely; the tooling is moving fast enough that the "too hard for regular teams" barrier could drop significantly within a year
- Build specification-writing skills on your team; even without full formal verification, the habit of writing precise specs improves AI prompting and code review quality

## Where This Is Going

The question of *when AI writes software, who verifies correctness* doesn't have a clean answer today. That's the honest assessment.

Testing scales poorly against AI's code generation velocity. Formal verification provides complete correctness guarantees but requires expertise that's currently scarce. AI-assisted proof generation — Lean 4 combined with models like AlphaProof — is the most credible path to bridging that gap. The near-term practical path is layered: better testing, lightweight contracts, and selective formal verification for the highest-risk code.

Watch two developments in the next 6-12 months. First, whether Microsoft's Copilot plus contracts integration gains real adoption — that's the most direct test of whether lightweight formal methods can go mainstream. Second, whether AI proof-generation research translates from competition mathematics to production software verification. DeepMind and others are actively pushing on this, and the gap is narrowing.

The mindset shift is this: correctness verification isn't a QA problem anymore. When AI writes software at scale, verification becomes a first-class engineering concern that deserves its own tooling, investment, and team capability — not a checkbox at the end of the sprint.

Ask your team this week: if AI wrote that function, how do you *know* it's correct?



## Related Posts


- [GPT-5.3 Instant: OpenAI's New Model Sparks Developer Confusion](/en/tech/gpt53-instant-openai-new-model-branding-confusion-/)
- [GRAM Editor: The Zed Fork Ditching AI in 2026 Open Source Space](/en/tech/gram-editor-zed-fork-no-ai-open-source-2026/)
- [Ars Technica Reporter Fired Over AI Fabricated Quotes](/en/tech/ars-technica-reporter-fired-ai-fabricated-quotes-j/)
- [Meta AI Smart Glasses Privacy: Workers Who See Everything](/en/tech/meta-ai-smart-glasses-privacy-workers-surveillance/)
- [Sub-500ms Voice Agent Latency: How to Build It in 2026](/en/tech/sub500ms-voice-agent-latency-build-from-scratch-20/)

## References

1. [The Man Who Built Lean Says AI Will Write the World's Software — But Only If We Solve the Proof Prob](https://www.webpronews.com/the-man-who-built-lean-says-ai-will-write-the-worlds-software-but-only-if-we-solve-the-proof-problem-first/)
2. [An AI Odyssey, Part 1: Correctness Conundrum](https://www.johndcook.com/blog/2026/03/02/an-ai-odyssey-part-1-correctness-conundrum/)
3. [Why AI Needs Formal Verification - Alex Skidanov + Christian Szegedy - YouTube](https://www.youtube.com/watch?v=d385TTn-0L8)


---

*Photo by [Jonathan Kemper](https://unsplash.com/@jupp) on [Unsplash](https://unsplash.com/photos/a-close-up-of-a-computer-screen-with-a-blurry-background-MMUzS5Qzuus)*
