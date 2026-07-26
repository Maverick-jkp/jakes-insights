---
title: "AI Security Flaw: What Happens When Your AI Chat Gets Leaked"
date: 2026-07-26T20:22:29+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "security", "flaw:", "happens"]
description: "300M leaked messages exposed an AI security flaw in a misconfigured database. Here's what the Chat & Ask AI breach means for your privacy."
image: "/images/20260726-ai-security-flaw-happens-ai.webp"
faq:
  - question: "How does a Firebase misconfiguration actually expose your chat history?"
    answer: "Firebase defaults to a 'public' database setting if a developer doesn't explicitly lock it down, meaning anyone with the project URL can read stored data. For AI chat apps, that data often includes full message logs tied to real user accounts — not anonymized."
  - question: "Is my data stored by the AI app or the actual AI provider?"
    answer: "Usually the intermediary app, not OpenAI or Google or whoever's model is running underneath. These 'wrapper apps' handle their own backend storage independently, which is where most security exposure actually happens."
  - question: "What kind of messages got leaked in that 300 million record breach?"
    answer: "The Chat & Ask AI breach exposed messages that included sensitive personal content — mental health conversations, legal questions, private concerns — all linked to identifiable user accounts. Nothing was anonymized or tokenized before storage."
  - question: "Does the EU AI Act actually require apps to secure their databases?"
    answer: "Not directly. Both the EU AI Act and California SB 243 are now in force, but neither specifically mandates backend storage security standards for AI apps. The gap between AI regulation and basic infrastructure security remains wide open."
  - question: "Why are so many AI apps shipping with the same basic security mistakes?"
    answer: "The short answer is speed — AI wrapper apps are being built and shipped faster than security practices can catch up. Firebase misconfigurations alone showed a 51.5% failure rate across 200 tested iOS apps, on a vulnerability that's been publicly documented since 2018."
---

300 million messages. 25 million users. One database setting left at "public."

That's the scale of the Chat & Ask AI breach discovered in early 2026 — and it's not an edge case. It's a window into a structural problem sitting underneath the entire AI wrapper app ecosystem. When users type sensitive questions into AI chat apps — about mental health, legal situations, or anything they'd rather keep private — they're trusting intermediary apps they know almost nothing about. Not the foundational AI providers whose names appear on the interface. The wrapper developers. The ones nobody audits.

This isn't just a cautionary tale about one bad actor. It's a pattern. Misconfigured backends, exposed authentication tokens, unprotected Elasticsearch instances — these aren't exotic vulnerabilities. They're basic infrastructure mistakes that security teams have understood for years, now appearing across an entire generation of AI products built fast and shipped faster.

AI adoption has outpaced security practice. Millions of users now interact daily with apps that route queries through OpenAI, Claude, or Gemini while independently managing data storage — and that storage layer is where the real exposure risk lives.

---

> **Key Takeaways**
> - A Firebase misconfiguration in Chat & Ask AI exposed 300 million messages from 25 million users, including sensitive content linked to identifiable accounts — not anonymized, not tokenized. Linked.
> - Security researcher Harry's automated scan found 103 of 200 iOS apps tested contained the same Firebase misconfiguration. That's an industry-wide failure rate, not an isolated incident.
> - AI wrapper apps create a structural security gap: users trust the AI provider's brand, but data storage is controlled entirely by the intermediary developer.
> - Vyro AI's separate breach exposed bearer authentication tokens — meaning attackers could hijack full accounts, not just read chat logs.
> - California SB 243 and the EU AI Act are both in force, but neither directly mandates backend storage security standards for AI apps.

---

## How Firebase Became a Security Liability

Firebase is Google's cloud backend platform — widely used in mobile development because it's fast to set up and cheap to run. It handles databases, authentication, file storage, and real-time syncing. The default configuration, if a developer isn't careful, leaves data accessible to anyone with the project URL. The setting is literally called "public."

This isn't a new problem. Firebase misconfiguration vulnerabilities have been documented since at least 2018. Security researchers have flagged them repeatedly. Yet according to [Malwarebytes](https://www.malwarebytes.com/blog/news/2026/02/ai-chat-app-leak-exposes-300-million-messages-tied-to-25-million-users), when Harry built an automated scanning tool and ran it against 200 iOS apps, 103 came back positive for the same flaw. A 51.5% failure rate on a well-documented, preventable misconfiguration.

The Chat & Ask AI app sits on top of OpenAI's ChatGPT, Anthropic's Claude, and Google's Gemini. Codeway, the developer behind it, built a polished interface that routes user queries to those models. The underlying AI infrastructure is fine. The storage layer — Codeway's responsibility alone — wasn't.

Separately, Vyro AI (behind ImagineArt, with 10M+ Google Play downloads) left an Elasticsearch instance completely open: no password, no authentication, no network restrictions. [Malwarebytes reported](https://www.malwarebytes.com/blog/news/2025/09/when-ai-chatbots-leak-and-how-it-happens) that 116GB of real-time logs were accessible for months after the database was indexed by IoT search engines in February 2025.

Two different companies. Two different technical stacks. Same root failure: shipping AI products without treating data storage as a security-critical component.

---

## The Firebase Vulnerability: Simple Flaw, Massive Footprint

The Chat & Ask AI breach is technically unimpressive. No exploit. No zero-day. A researcher typed a URL, hit an API endpoint, and data came back. That simplicity is the problem.

[According to the Fox News analysis](https://www.foxnews.com/tech/millions-ai-chat-messages-exposed-app-data-leak), Harry sampled 60,000 users and one million messages to confirm scope before responsible disclosure. The exposed records included complete chat histories, timestamps, user-assigned chatbot names, AI model configurations, and model identity. None of it was encrypted at rest in any meaningful way — the database was open.

What makes this worse: Chat & Ask AI captured data across all of Codeway's apps simultaneously. One misconfiguration. Multiple products. Millions of users who had no idea their conversations were being stored this way at all.

Conversations about suicide methods, drug manufacturing, and hacking were sitting in plaintext, associated with real user accounts. Not anonymized. Linked.

## The Authentication Token Problem: From Data Leak to Account Takeover

Exposed chat logs are bad. Exposed bearer tokens are catastrophic.

[Malwarebytes documented](https://www.malwarebytes.com/blog/news/2025/09/when-ai-chatbots-leak-and-how-it-happens) that the 116GB Elasticsearch database included active bearer authentication tokens. These aren't just read credentials — they grant full account access. An attacker with a valid bearer token can impersonate a user, access their complete history, make purchases using stored payment methods, and potentially pivot to connected services.

The Vyro database stored rolling logs covering 2–7 days at any time. That's a continuous, live exposure window indexed by public IoT search engines. Anyone who knew where to look could pull fresh tokens in real time.

## Why AI Wrapper Apps Are a Structural Risk

This is the piece that gets missed in breach coverage.

When you use Chat & Ask AI, you see ChatGPT-powered responses. You associate the experience with OpenAI's security practices, OpenAI's privacy policies, OpenAI's brand trust. None of that applies to how your data gets stored.

OpenAI's infrastructure didn't fail here. Anthropic's didn't either. Codeway's did. The intermediary layer — the wrapper — is entirely responsible for storage security, and users have almost no visibility into who that is or what they're doing.

This creates an information asymmetry that attackers can exploit without touching the underlying AI providers at all. It's a supply chain problem disguised as a product problem.

## Backend Security: A Direct Comparison

| Approach | Firebase (Default Public) | Firebase (Hardened) | Self-Hosted Elasticsearch | Managed Cloud DB (RDS/Firestore w/ IAM) |
|---|---|---|---|---|
| **Setup Speed** | Minutes | Hours | Days | Hours |
| **Default Security** | ❌ Open | ✅ Restricted | ❌ Open | ✅ Restricted |
| **Auth Required** | No | Yes (Rules-based) | No | Yes (IAM) |
| **Breach Risk** | Critical | Low | Critical | Low |
| **Dev Experience** | Easy | Moderate | Complex | Moderate |
| **Best For** | Prototyping only | Production mobile apps | Internal tools (airgapped) | Production SaaS |

The pattern across both breaches is identical: developers chose the fast path and never revisited defaults. Firebase's "public" rule and Elasticsearch's no-auth default are designed for prototyping. Neither belongs in a production app handling sensitive conversation data. The misconfiguration isn't accidental — it's a process failure. Specifically, the absence of any security review step before launch.

---

## What This Means for You

AI app security failures don't announce themselves. Databases sit open for months. Users don't know. Developers sometimes don't know. The breach only surfaces when a researcher runs a scan or a search engine indexes the endpoint.

**If you use third-party AI chat apps regularly:** Assume your conversations are stored somewhere, by someone, with infrastructure quality you can't audit. Check each app's privacy policy specifically for data retention and storage terms — not just the AI provider's policy, but the wrapper developer's. If the app has no published security policy, that's a signal worth taking seriously. Delete conversation histories when possible. For anything genuinely sensitive — medical, legal, financial — use the primary providers directly (ChatGPT.com, Claude.ai), not wrappers.

**If you're building an AI product on Firebase or Elasticsearch:** The fix for the Chat & Ask AI breach was deployed within hours of disclosure. That means the technical fix is trivial. The failure was in never checking. Run a security audit against your Firebase Security Rules before launch and after any major update. Elasticsearch should never be publicly accessible — put it behind a VPC with authentication required at the network level. The [Firehound scanner at firehound.covertlabs.io](https://firehound.covertlabs.io) now indexes vulnerable apps publicly, which means an exposed database gets discovered faster than you expect.

**If you're evaluating AI vendors for enterprise use:** Don't assess the AI provider's security posture alone. Map the full data path: where does the query go, what gets logged, who stores it, and what's their security certification? SOC 2 Type II reports, penetration test summaries, and published incident response policies are baseline requirements — not nice-to-haves.

**On the regulatory side:** California SB 243 (effective September 2025) targets AI companion apps specifically but doesn't mandate storage security standards. The EU AI Act's three-tier risk classification leaves most general-purpose chat apps in the unregulated category. Meaningful regulatory pressure on backend security practices hasn't arrived yet — and may not for some time.

---

## Where This Goes Next

The data tells a consistent story across both breaches:

- **51.5% of scanned iOS apps** contained the same Firebase misconfiguration
- **116GB of live logs** sat open on Vyro AI's Elasticsearch instance for months
- **300 million messages** from 25 million users were exposed through one setting left at "public"
- Bearer token exposure meant affected users faced account takeover risk, not just data exposure

The next 6–12 months will likely see more disclosures, not fewer. Harry's automated scanning tool exists. Firehound is public. Security researchers now have infrastructure to scan app stores at scale, and the vulnerability rate suggests there's a long queue of incidents not yet disclosed.

One regulatory shift worth tracking: if app store listing requirements become tied to basic backend security attestation, the incentive structure changes overnight. Apple and Google have the distribution leverage to enforce this. They just haven't.

The mindset shift that matters most is simpler. Stop evaluating AI app security by the AI provider's reputation. The model is probably fine. The storage layer is where you should be asking questions.

The breaches covered here are preventable. The technical fixes are trivial. The failures are in process — in defaults that never got reviewed, and products that shipped without anyone asking where the data actually goes.

What would it take for your organization to audit every third-party AI app your team uses today?

---

*Sources: [Malwarebytes — Chat & Ask AI breach](https://www.malwarebytes.com/blog/news/2026/02/ai-chat-app-leak-exposes-300-million-messages-tied-to-25-million-users) | [Malwarebytes — Vyro AI breach](https://www.malwarebytes.com/blog/news/2025/09/when-ai-chatbots-leak-and-how-it-happens) | [Fox News — Chat & Ask AI analysis](https://www.foxnews.com/tech/millions-ai-chat-messages-exposed-app-data-leak)*

## References

1. [Is ChatGPT safe? The ultimate guide for privacy](https://us.norton.com/blog/ai/is-chatgpt-safe)
2. [AI agent security: four July attacks, one shared flaw](https://thenextweb.com/news/ai-agent-security-four-attacks-one-flaw)
3. [AI agent went rogue and hacked startup by itself, OpenAI reveals | OpenAI | The Guardian](https://www.theguardian.com/technology/2026/jul/22/openai-says-its-models-went-rogue-and-hacked-startup-in-unprecedented-incident)


---

*Photo by [Igor Omilaev](https://unsplash.com/@omilaev) on [Unsplash](https://unsplash.com/photos/a-computer-chip-with-the-letter-a-on-top-of-it-eGGFZ5X2LnA)*
