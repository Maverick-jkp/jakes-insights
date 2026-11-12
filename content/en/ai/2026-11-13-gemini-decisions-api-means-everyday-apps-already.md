---
title: "Gemini Decisions API: What It Means for Everyday Apps You Already Use"
date: 2026-11-13T03:20:55+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "gemini", "decisions", "api:"]
description: "Google's Gemini Decisions API delivers structured AI decisions in under 250ms — here's how it's already reshaping the apps on your phone."
image: "/images/20261113-gemini-decisions-api-means.webp"
faq:
  - question: "How does batching questions actually save money with this API?"
    answer: "The Gemini Decisions API bills the input content only once regardless of how many questions you attach to it, up to 1,000 per request. So if you're running 50 classification checks on the same document, you pay for the document once instead of 50 separate calls. The more questions you batch together, the lower your effective cost per decision."
  - question: "What apps are already using it without anyone announcing anything?"
    answer: "Google deployed the underlying model internally before the public launch — Gemini Notebook uses it for routing queries to the right model, which cut latency by 40%. Google Search is also running it in production. Most users touched it without knowing it existed."
  - question: "Is the pricing actually competitive or just Google being Google?"
    answer: "At $0.10 per million input tokens it's roughly 2.4x more expensive than OpenAI and TypeSafe Jev, which both charge $0.042. The tradeoff is native multimodal support — audio, video, and PDFs work without preprocessing pipelines that competitors require. Whether that math works depends heavily on how much your current pipeline costs to maintain."
  - question: "Why would I use this instead of just prompting a regular model?"
    answer: "Prompting a regular model returns text you then have to parse, validate, and handle edge cases for when the model goes off-format — it's slow and brittle at scale. This returns calibrated probability scores directly with no output tokens, in under 250 milliseconds flat regardless of question count. For content moderation or routing logic running millions of times a day, that's a completely different cost and reliability profile."
  - question: "Does it handle PDFs natively or is that just marketing?"
    answer: "It genuinely handles PDFs, audio, video, and images in a single API call without you converting them first — that's not standard across competitors at launch. TypeSafe Jev and OpenAI's versions require preprocessing pipelines to handle anything beyond text. Eliminating that layer is the actual practical win for teams dealing with mixed-format content."
---

Google dropped the Gemini Decisions API on November 11, 2026 — and it's quietly doing something most AI announcements don't: solving a real production problem that's been irritating backend engineers for two years. Not text generation. Not chat. Pure structured decisions, at scale, in under 250 milliseconds.

The core idea is deceptively simple. Send a document, image, audio file, or video to `gemini-decision-1`. Attach up to 1,000 questions. Get calibrated probability scores back — no text, no tokens wasted on words you're going to discard anyway. The model does one forward pass for the entire batch. Latency stays flat whether you ask 1 question or 100.

That's not a minor optimization. For apps doing content moderation, routing logic, or classification at scale, this changes the cost-performance math entirely.

The real story isn't futuristic AI — it's the infrastructure layer already running inside tools like Gemini Notebook, Google Search, and Stitch. Apps millions of people touched yesterday.

**Key points covered below:**
- How `gemini-decision-1` works technically, and why the architecture matters
- Where it already runs in production (with real latency numbers)
- How it compares to OpenAI's Decisions API and TypeSafe Jev on price and capability
- What this means for the apps you're building or using right now

---

**In brief:** The Gemini Decisions API processes up to 1,000 structured questions against a single multimodal input in one pass, returning calibrated probabilities at $0.10/million input tokens with zero output token billing. It's the first hosted decision model to natively handle audio, video, and PDFs — a gap that eliminates entire preprocessing pipelines for real-world production systems.

1. Google deployed it internally before launch: Gemini Notebook achieved 40% lower latency on everyday queries using it for model routing.
2. The pricing model rewards batching — shared input is billed once, so more questions per request means lower effective cost per decision.
3. No context caching at launch is a real limitation that affects cost at high-volume, repeated-context workloads.

---

## Background: Why "Decisions as a Service" Is a Thing Now

For the past three years, production AI pipelines have had an ugly pattern: send content to a large language model, get a paragraph back, parse that paragraph with regex or a JSON schema validator, handle edge cases when the model decides to get creative with formatting. Engineers hate it. It's slow and brittle.

TypeSafe Jev launched the first serious alternative in September 2026. The model returns structured probability scores — no text. OpenAI followed in early October 2026 with their own Decisions API. Both are priced at $0.042/million tokens, targeting the classification and routing workload that's currently burning through inference budgets at mid-size SaaS companies.

Google entered the category on November 11, 2026, with `gemini-decision-1`. Priced at $0.10/million input tokens — 2.4x more expensive than Jev — but with one differentiator that neither competitor has: native multimodal input across text, images, audio, video, and PDFs up to 256K tokens (262,144 to be precise), according to [Google DeepMind's official announcement](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-decisions-api/).

That difference matters more than the price gap implies. Transcribing audio before classification, running OCR on PDFs before routing — those steps add latency and cost that often exceed the inference cost itself. Eliminating the preprocessing pipeline changes the total-cost calculation significantly.

The API integrates with OpenRouter, LangChain, Vercel, LiteLLM, and Pydantic AI at launch, with Google Cloud/Vertex AI support still pending.

---

## Main Analysis

### Three Question Types, One Forward Pass

`gemini-decision-1` supports three structured decision types, each returning numbers instead of words:

- **`noul` (yes/no):** Returns a probability between 0.01 and 0.99. Set a threshold and it becomes a binary classifier. Useful for spam detection, policy compliance checks, content flagging.
- **`choice`:** Selects from 2–255 options with a normalized probability distribution. Built for routing, categorization, and intent classification across a known label set.
- **`score`:** Grades input against an ordered rubric, returning a continuous probability-weighted average. Powerful for quality assessment — resume screening against a job spec, customer support ticket prioritization, content quality scoring.

The critical architectural detail: all 1,000 questions run in a single forward pass. Latency is 150–250ms end-to-end, with model compute at 50–100ms. According to [eesel AI's analysis](https://www.eesel.ai/blog/gemini-decisions-api), that latency stays nearly flat from 1 to 100 questions per request. For apps currently firing 10 sequential classification calls per user action, that's a 10x throughput improvement with one API change.

This approach can fail when your decision logic requires reasoning chains — cases where the *why* behind a classification matters as much as the classification itself. Probability scores don't explain their logic. If your compliance team needs audit trails with justifications, you'll still need text generation somewhere in the pipeline.

### Where It's Already Running in Production

Google didn't launch this cold. Three internal deployments were already live before the public announcement.

**Gemini Notebook** uses `gemini-decision-1` for real-time model routing — deciding which underlying model handles which query. The result: 40% lower latency on everyday queries, according to [Google's official blog](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-decisions-api/). That's a meaningful number for a product at Gemini Notebook's scale.

**Google Search** applies it as a safety layer for MCP tool adversarial detection — checking whether tool calls coming through the Model Context Protocol are attempting unauthorized actions. This is a high-volume, low-latency requirement. Text generation would be absurdly expensive here. The fact that Google chose their own decision model for this workload rather than a standard LLM says something about their confidence in the architecture.

**CC from Google Labs** uses `choice` queries to select from 200+ emoji options in milliseconds. Smaller use case, but it illustrates how commodity the API already is internally — routine enough to handle something as mundane as emoji routing.

**Stitch** uses it for instant wireframe generation and voice/tap edits, with `noul` and `score` types classifying user intent before rendering UI changes.

### Comparison: Gemini Decision-1 vs. Competitors

| Feature | Gemini Decision-1 | OpenAI Decisions API | TypeSafe Jev |
|---|---|---|---|
| **Launch date** | Nov 11, 2026 | Early Oct 2026 | Sep 2026 |
| **Price (input)** | $0.10/M tokens | $0.10/M tokens | $0.042/M tokens |
| **Output billing** | Free | Free | Free |
| **Context window** | 262,144 tokens | Not published | Not published |
| **Multimodal** | Text, image, audio, video, PDF | Text, image | Text only |
| **Max questions/request** | 1,000 | Not published | Not published |
| **Latency** | 150–250ms | Not published | Not published |
| **Context caching** | ❌ Not available | Not confirmed | Not confirmed |
| **Self-hosting** | ❌ No | ❌ No | ❌ No |
| **Free tier** | ✅ Yes | Not confirmed | Not confirmed |

Sources: [Google DeepMind](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-decisions-api/), [eesel AI](https://www.eesel.ai/blog/gemini-decisions-api)

Gemini matches OpenAI on price and beats both on multimodal coverage. TypeSafe Jev wins on cost — 2.4x cheaper — but handles text only. For pipelines that never touch audio, video, or PDFs, Jev is worth evaluating seriously. For anything that processes documents or media natively, the preprocessing costs you'd eliminate likely close the price gap fast.

The missing context caching is Gemini's sharpest limitation right now. If your system prompt is 50K tokens and you're running thousands of classification requests against the same policy document, you're paying full price every time. OpenAI's standard API has caching. Google hasn't confirmed when it's arriving for the Decisions API. At high-volume, repeated-context workloads, that gap materially changes the cost comparison.

---

## Practical Implications: Who Builds What, Right Now

**For backend engineers building content pipelines:** The immediate win is replacing sequential LLM calls with batched `noul` queries. If your moderation pipeline runs 8 policy checks per piece of content, that's currently 8 API calls, 8 latency cycles, 8 output token bills. With `gemini-decision-1`, it's one call, one latency cycle, zero output tokens. The integration path is straightforward — LangChain and LiteLLM adapters are already available at launch.

**For product teams running SaaS apps:** The routing use case matters most. Gemini Notebook's 40% latency improvement came directly from using the API to route queries to the right underlying model. Any SaaS app with tiered AI features — premium vs. standard, complex vs. simple query handling — can apply the same pattern. The `choice` type with 2–255 options covers most routing trees a product team would realistically design.

**For teams processing documents or media:** Native PDF and audio support is the differentiator worth testing immediately. If you're currently running a Whisper transcription step before classification, or calling a document parser before routing, the total pipeline cost needs to be re-benchmarked against the new baseline. The 256K token context window is large enough to process substantial PDFs in a single request.

**What to watch:**
- Google Cloud/Vertex AI support is pending — enterprise teams with GCP commitments should hold architectural decisions until that ships
- Context caching availability will significantly change the cost math for repeated-context workloads
- OpenAI's response to Gemini's multimodal coverage, likely within Q1 2027

---

## Conclusion & Future Outlook

Structured decision-making is becoming a first-class API primitive, not a text-parsing workaround. That's the actual shift the Gemini Decisions API represents. Google's production deployments prove the architecture works at scale. The numbers — 40% latency reduction, 150ms end-to-end, $0.10/M with zero output billing — are real and independently verifiable.

This isn't always the right answer. Teams that need explainability, audit trails, or complex reasoning chains will still need text generation in the mix. But for classification, routing, and policy enforcement at volume, the case for dedicated decision models is now difficult to argue against.

> **Key Takeaways**
> - Native multimodal support across audio, video, and PDFs eliminates preprocessing steps that currently add both latency and cost to classification pipelines
> - Batching up to 1,000 questions per request fundamentally changes throughput economics for high-volume moderation and routing workloads
> - The absence of context caching is a real gap for repeated-context workloads — worth tracking on Google's roadmap before making architectural commitments
> - The free prototyping tier lowers the barrier to running your own benchmark significantly

Vertex AI integration will push this into enterprise adoption at speed over the next 6–12 months. Context caching will likely arrive by mid-2027, which shifts the cost comparison with TypeSafe Jev substantially. OpenAI will respond with broader multimodal coverage.

The practical next step: benchmark your current classification pipeline against `gemini-decision-1` on the free tier. The latency data alone will tell you whether migration makes sense. That answer is worth having before Q1 2027 pricing pressure arrives.

## References

1. [Gemini Decisions API: Fast, calibrated multimodal decisions](https://blog.google/innovation-and-ai/technology/developers-tools/gemini-decisions-api/)
2. [Gemini Decisions API (2026): how it works, pricing, vs OpenAI and Jev | eesel AI](https://www.eesel.ai/blog/gemini-decisions-api)
3. [Gemini Decisions API Explained: Scores, Not Text](https://aiera.blog/gemini-decisions-api-explained/)


---

*Photo by [Markus Winkler](https://unsplash.com/@markuswinkler) on [Unsplash](https://unsplash.com/photos/a-wooden-table-topped-with-scrabble-tiles-spelling-out-the-words-deep-mind-82vrrMlAyo4)*
