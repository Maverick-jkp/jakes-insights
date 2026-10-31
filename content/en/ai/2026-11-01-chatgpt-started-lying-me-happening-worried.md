---
title: "ChatGPT has started lying to me: what is actually happening and should I be worried"
date: 2026-11-01T00:40:17+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "chatgpt", "has", "started"]
description: "ChatGPT isn't lying — it's hallucinating. Discover why it invents fake studies and wrong deadlines, and what you can actually do about it."
image: "/images/20261101-chatgpt-started-lying-me.webp"
faq:
  - question: "Why does ChatGPT sound so confident when it's completely wrong?"
    answer: "ChatGPT generates text by predicting statistically likely word sequences, not by retrieving verified facts. This means it can produce a fabricated citation or incorrect legal deadline in the same confident tone as something accurate — there's no internal signal separating the two."
  - question: "Is the hallucination problem actually getting better with newer models?"
    answer: "Somewhat, yes. GPT-5 reduced sycophantic responses by over 50% compared to earlier versions, and enabling Thinking mode can cut error rates by an additional 50–80% on complex queries. But hallucinations haven't been eliminated — they've been reduced, which still matters a lot in high-stakes use cases."
  - question: "How often does it make stuff up without web search turned on?"
    answer: "According to Canny.io's analysis, ChatGPT produces factual errors on more than 40% of queries when web search is disabled. Topics that are obscure, recent, or niche are especially risky since the model fills knowledge gaps with plausible-sounding fabrications."
  - question: "What actually happens when you correct ChatGPT mid-conversation?"
    answer: "It may simply agree with your correction even if you're also wrong — a behavior called sycophancy. The model is optimized for fluent, agreeable responses, so it can end up validating incorrect premises you introduce rather than pushing back with accurate information."
  - question: "Can fake citations fool someone who actually checks the source?"
    answer: "Often, yes — at least initially. ChatGPT fabricates references using real journal names and plausible author names, which means a quick glance looks legitimate. You'd need to search for the actual paper to catch it, which most people skip under deadline pressure."
---

Something broke your trust. ChatGPT confidently cited a study that doesn't exist. Or it gave you a legal deadline that's completely wrong. Or it recommended contacting a tech publication for support — a hallucination so persistent that [404 Media documented it repeatedly](https://www.404media.co/chatgpt-keeps-telling-people-404-media-can-solve-their-tech-support-problems/). If you've landed here searching for answers, you're not alone — and the answer is more nuanced than "yes, it's broken" or "no, you're fine."

ChatGPT isn't lying. Not technically. But that distinction matters less than understanding *why* this happens and what it costs you when you're using AI output in production decisions, legal research, or client deliverables.

**The core problem**: ChatGPT's architecture optimizes for fluent, plausible output — not factual accuracy. Confident delivery and correctness are two completely separate things.

> **Key Takeaways**
> - Without web search enabled, ChatGPT produces factual errors on more than 40% of queries, according to [Canny.io's analysis](https://canny.io/blog/get-chatgpt-to-stop-lying/).
> - GPT-5 reduced sycophantic responses — agreeing with incorrect user premises — by over 50% compared to earlier models.
> - Enabling Thinking mode in GPT-5.4 cuts error rates by an additional 50–80% on complex queries.
> - ChatGPT fabricates citations using real journal names and plausible author names, making errors hard to spot without active verification.
> - The model has no internal concept of truth; it calculates statistically likely word sequences, not factual accuracy.

---

## Why ChatGPT Gets Facts Wrong: The Architecture Problem

Assuming intentionality is the wrong frame. Understanding the actual mechanism changes how you use the tool.

ChatGPT is a probability model. Every word it generates is the statistically likely next token given everything before it. [According to OpenAI's own Help Center](https://help.openai.com/en/articles/8313428-does-chatgpt-tell-the-truth), responses are generated from training data patterns — not retrieved from a verified fact database. When those patterns are thin — obscure topics, recent events, niche technical domains — the model fills gaps with plausible-sounding fabrications.

Three main failure modes drive this:

- **Hallucination**: Generating confident but baseless content, including fake studies with real journal names
- **Sycophancy**: Agreeing with incorrect premises a user provides, then building on the error
- **Context gaps**: Knowledge cutoff means anything post-training is guesswork without active web search

One critical point from OpenAI's documentation deserves attention: **expressed confidence does not correlate with accuracy.** The model delivers a fabricated citation in the same tone as a correct one. There's no internal signal you can read to distinguish them.

This isn't a bug that ships in a patch. It's structural.

---

## The Accuracy Numbers You Need to Know

The data tells a clear story about when ChatGPT is reliable and when it isn't.

[According to analysis from Canny.io](https://canny.io/blog/get-chatgpt-to-stop-lying/), with web search enabled, GPT-5 produces factual errors on roughly **10% of queries**. Without web search, that rate exceeds **40%**. That's not a marginal difference — that's the gap between a tool you can draft with and one that needs constant babysitting.

Web search is now enabled by default across ChatGPT's current models. But "enabled by default" doesn't mean "always active." The model doesn't always trigger search when it should. For topics it has strong training signal on — even outdated signal — it often answers from memory rather than fetching current data.

Switching to **Thinking mode** (available in GPT-5.4 on paid plans) reduces errors by another **50–80%** on complex or high-stakes queries. That's a meaningful jump for anyone using AI in research or technical workflows.

### Mode-by-Mode Error Rate Comparison

| Configuration | Estimated Error Rate | Best For |
|---|---|---|
| GPT-5, no web search | 40%+ | Brainstorming, structure, ideation |
| GPT-5, web search enabled | ~10% | General research, current events |
| GPT-5.4 Thinking mode | ~2–5% (estimated) | Complex analysis, technical depth |
| Specialized AI tools | Varies by domain | Domain-specific accuracy needs |

The takeaway isn't "don't use ChatGPT." It's "use the right configuration for the stakes involved."

---

## What "Lying" Actually Looks Like in Practice

The 404 Media case is instructive. ChatGPT was directing users seeking tech support to contact 404 Media — a news publication — as if it were a customer service resource. [404 Media documented this happening repeatedly](https://www.404media.co/chatgpt-keeps-telling-people-404-media-can-solve-their-tech-support-problems/). No hallucination was dramatic. Each one was plausible enough to act on.

That's the real risk pattern. [As documented by independent AI researchers](https://ki-blog.mrn.one/en/posts/chatgpt-lies/), the highest-stakes hallucination categories include:

- **Fake citations**: Real journal names, plausible author names, nonexistent papers
- **Legal misinformation**: Incorrect statutes, deadlines, or regulatory requirements
- **Medical misinformation**: Wrong dosages, misidentified symptoms, incorrect diagnoses

The legal and medical categories carry obvious real-world consequences. But fake citations are the sneaky failure mode for tech professionals — easy to miss if you don't verify the actual source.

The model "lies" most confidently about things it almost knows. Obscure conference papers. Niche API behavior. Recent policy changes. The partial pattern match gives it enough signal to sound authoritative while getting the specifics wrong. And that partial confidence is what makes these errors genuinely dangerous — they don't look like guesses.

This approach can also fail quietly in enterprise contexts. Teams that route AI output directly into client deliverables without a verification step are particularly exposed. A fabricated regulatory citation in a compliance report doesn't announce itself. It just sits there, waiting.

---

## Practical Fixes, Ranked by Impact

Worry proportionally to how you're using ChatGPT, then fix your workflow accordingly.

**High-impact changes:**

1. **Enable Thinking mode for anything that matters.** GPT-5.4 Thinking is available on paid plans. For legal research, technical specs, or anything you'll act on — use it. The error reduction is substantial enough to justify the slower response time.

2. **Verify every citation.** Don't just check if it looks right. Search Google Scholar or the specific journal directly. Fabricated citations are common and engineered to look real — real author names, real journal titles, plausible volume numbers.

3. **Set custom instructions.** In Settings → Personalize, add a directive like "never present guesses as facts; flag uncertainty explicitly." This shifts the model's default behavior at the session level, not just for one prompt.

4. **Use iterative prompting.** One question at a time. Correct errors before adding complexity. Multi-part prompts compound errors because the model builds on its own previous output — including any mistakes baked into earlier responses.

5. **For domain-specific work, use domain-specific tools.** Perplexity AI links directly to verifiable sources. Specialized AI tools trained on curated datasets outperform general models for tasks like legal research or medical literature review. General-purpose doesn't mean best-purpose.

---

## What Changes Over the Next 6–12 Months

Near-term, OpenAI's trajectory is clear: Thinking mode availability will expand, and search integration will improve. The sycophancy reduction in GPT-5 — over 50% compared to earlier models — signals that alignment work is directly targeting this failure mode.

Medium-term, the more interesting shift is toward **retrieval-augmented generation (RAG)** becoming standard in enterprise deployments. Grounding model outputs in verified, internal knowledge bases cuts hallucination rates dramatically for domain-specific queries. Organizations already running RAG pipelines report meaningful accuracy gains, particularly in regulated industries where a wrong answer has legal or financial consequences.

The open question remains whether general-purpose ChatGPT will ever become reliable enough for high-stakes professional use without human verification. Current architecture suggests the ceiling is lower than most users assume — not because OpenAI won't improve it, but because probabilistic text generation has fundamental limits when accuracy is binary. A citation either exists or it doesn't. A statute either says what the model claims or it doesn't. Statistical plausibility and factual correctness are not the same thing, and no amount of fine-tuning fully closes that gap.

**The bottom line.** ChatGPT hasn't started lying to you — it never stopped generating plausible-sounding errors. What changed is probably your use case. You're asking harder questions, trusting it in higher-stakes contexts, or simply noticing failures you previously missed. The fix isn't abandoning the tool. It's using the right configuration, verifying aggressively, and calibrating your trust to match the actual error rates — not the confident tone of the output.

What's the highest-stakes context you're currently using ChatGPT for — and are you running web search and Thinking mode by default?

## References

1. [Chapter 2 | How to Reduce ChatGPT's Lies｜らんどん](https://note.com/unique_hornet699/n/nf8ef030f3161?hl=en)
2. [Show HN: Steal My Bitcoin | Hacker News](https://news.ycombinator.com/item?id=50224916)
3. [ChatGPT Keeps Telling People 404 Media Can Solve Their Tech Support Problems](https://www.404media.co/chatgpt-keeps-telling-people-404-media-can-solve-their-tech-support-problems/)


---

*Photo by [Levart_Photographer](https://unsplash.com/@siva_photography) on [Unsplash](https://unsplash.com/photos/chatgpt-interface-with-examples-and-capabilities-drwpcjkvxuU)*
