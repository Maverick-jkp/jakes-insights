---
title: "Signal and DuckDuckGo threatening to leave Canada: what privacy users need to know"
date: 2026-06-08T23:22:49+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-web", "signal", "duckduckgo", "threatening"]
description: "Signal, DuckDuckGo & 3 other privacy tools may exit Canada over Bill C-22. Here's what zero-knowledge encryption users must do now."
image: "/images/20260608-signal-duckduckgo-threatening.webp"
faq:
  - question: "Why are Signal and DuckDuckGo actually threatening to leave Canada?"
    answer: "Canada's Bill C-22 requires service providers to build technical interception capabilities and retain user metadata for up to one year. For apps built on zero-knowledge encryption, there's no technical way to comply without fundamentally breaking their privacy architecture — so leaving is their only real option."
  - question: "What does Bill C-22 actually force companies to store about users?"
    answer: "The bill mandates retention of metadata including contacts, message timing, and location data for up to 12 months. Beyond storage, it allows the Public Safety Minister to issue secret orders requiring companies to build specific surveillance capabilities, with no public disclosure or court warrant required."
  - question: "Is end-to-end encryption actually banned under the new Canadian law?"
    answer: "Not explicitly banned, but the bill leaves 'encryption' deliberately undefined and defers the actual definition to regulation. That gap means ministerial secret orders could effectively override encryption protections, which is why Signal's legal team treats the current text as a de facto threat to end-to-end encryption."
  - question: "How is this different from what happened with Apple in the UK?"
    answer: "Apple withdrew its Advanced Data Protection cloud encryption feature from the UK after receiving a lawful access order with similar interception requirements. That precedent matters because it proves market exits over encryption aren't just negotiating tactics — companies have already done it rather than comply."
  - question: "Can Canadian users do anything before this bill actually passes?"
    answer: "Yes — parliamentary committee amendments are still being debated, making this the critical window for public and industry pressure. Organizations like the Canadian Civil Liberties Association are actively challenging the bill's framework, and public submissions to the committee are still being accepted."
---

Canada's Bill C-22 has triggered one of the most coordinated privacy tech standoffs since the UK's Investigatory Powers Act. Signal, DuckDuckGo, NordVPN, Windscribe, and Tailscale have all issued formal withdrawal threats — not as negotiating bluster, but as technical necessity. When your architecture is built around zero-knowledge encryption, there's no middle ground with a law that mandates interception capability.

The stakes extend well beyond Canada's 40 million users. This is a test case for whether democratic governments can legislate surveillance infrastructure into privacy-first products. The outcome will shape similar bills already circulating in the EU and Australia.

> **Key Takeaways**
> - Canada's Bill C-22 mandates up to one year of metadata retention and requires service providers to build technical interception capabilities for law enforcement and intelligence agencies.
> - Signal VP Udbhav Tiwari stated the platform would "rather pull out of the country than compromise privacy promises," citing fundamental incompatibility with end-to-end encryption.
> - A joint Citizen Lab and Canadian Civil Liberties Association analysis characterizes the bill's framework as offering "maximum flexibility, minimal restrictions, and minimal judicial scrutiny."
> - Apple previously withdrew cloud encryption services from the UK under a similar lawful access order — establishing that market exits over encryption are not hypothetical.
> - Parliamentary committee amendments in the coming weeks will determine the bill's final scope, making this the critical window for industry and user advocacy.

---

## What Bill C-22 Actually Requires

Bill C-22 is Canada's lawful access legislation, and it's more aggressive than its predecessors in two specific ways: the scope of secret ministerial authority and the breadth of the metadata retention mandate.

Under the bill, electronic service providers must retain user metadata — contacts, message timing, location data — for **up to one year**. That alone mirrors frameworks in France and Germany that privacy advocates have challenged for years. But C-22 goes further. The Public Safety Minister can issue **secret orders** requiring companies to develop specific surveillance capabilities. Those orders can't be publicly disclosed. They require only intelligence-commissioner approval, not a court warrant. And there's no challenge process built into the current text.

According to [Global News](https://globalnews.ca/news/11886905/lawful-access-bill-c-22-companies-services-canada/), critics argue the bill's definition of "systemic vulnerability" is too broad, and the term "encryption" is deliberately left undefined — with the actual definition deferred to regulation. That means ministerial orders could override those regulations with no legal recourse. That's the clause keeping Signal's lawyers up at night.

Public Safety Minister Gary Anandasangaree has committed to amendments clarifying encryption can't be breached. But the government has also confirmed the one-year metadata retention period is staying. Those two positions are harder to reconcile than they sound.

---

## Why Privacy Companies Can't Comply — Technically

This isn't about corporate posturing. It's about architecture.

Signal's end-to-end encryption is designed so that Signal itself cannot read your messages. Building a "lawful interception" capability into that system requires one of two things: a backdoor into the encryption, or retention of decryption keys. Both options destroy the core security guarantee. Signal VP Udbhav Tiwari made this explicit, stating the platform would rather exit Canada than compromise its privacy promises, according to [Yahoo News](https://www.yahoo.com/news/politics/articles/signal-duckduckgo-more-threaten-canada-185322945.html).

NordVPN operates on a no-logs architecture — it doesn't store user activity data at all. Complying with a one-year metadata retention requirement would mean building logging infrastructure that doesn't currently exist and that would fundamentally gut its product's value proposition. NordVPN stated there's "no scenario" where it compromises that architecture.

DuckDuckGo's position is more targeted. Its threat focuses specifically on removing its VPN service from Canada, since that product would fall directly under the interception-capability mandate.

Windscribe, a Canadian-based VPN company, threatened to relocate its headquarters entirely. Tailscale, also Toronto-based, said it would redirect Canadian business and profits abroad. Apple and Google both warned the bill could force encryption backdoors — and Apple has demonstrated it follows through: it withdrew iCloud Advanced Data Protection from the UK in February 2025 after a similar lawful access order. That wasn't a negotiating tactic. It happened fast, with minimal user notice, and left UK users without a privacy feature they'd already enabled.

---

## How These Companies Compare on Compliance Risk

Different products face different exposure under C-22:

| Company | Product at Risk | Architecture Conflict | Stated Position |
|---|---|---|---|
| **Signal** | Messaging platform | E2E encryption incompatible with interception | Exit Canada entirely |
| **NordVPN** | VPN service | No-logs architecture conflicts with retention | Limit/remove Canadian presence |
| **DuckDuckGo** | VPN service | Interception capability mandate | Remove VPN from Canada |
| **Windscribe** | VPN service | Retention + interception mandate | Relocate headquarters |
| **Tailscale** | Network security | Business data routing rules | Redirect Canadian revenue abroad |
| **Apple** | iCloud encryption | Backdoor demand | Historical exit precedent (UK, 2025) |

Signal carries the highest visibility risk — losing messaging access for Canadian users who rely on it for journalist-source communication, legal privilege, and health privacy. NordVPN and DuckDuckGo exits would hit the consumer VPN market hard. But the Windscribe and Tailscale situations are arguably worse for Canada's tech ecosystem: these are Canadian companies threatening to leave their home jurisdiction because the regulatory environment is structurally incompatible with their products.

The [Citizen Lab and Canadian Civil Liberties Association joint analysis](https://globalnews.ca/news/11886905/lawful-access-bill-c-22-companies-services-canada/) published in June 2026 called the metadata retention and ministerial orders section "fundamentally flawed," citing maximum flexibility for the government, minimal restrictions on ministerial authority, and minimal judicial scrutiny over orders.

---

## What Canadian Privacy Users Should Do Right Now

**If you're a Canadian Signal user**: Nothing changes today. Signal hasn't exited. But download your conversation backups and watch parliamentary committee news closely. The amendment window closes within weeks.

**If you use a Canadian-based VPN service**: Windscribe's potential relocation could affect service continuity and jurisdiction for data handling. Check your provider's statements directly — don't rely on third-party summaries.

**If you're a developer or SaaS operator serving Canadian users**: C-22's ministerial order mechanism applies to "electronic service providers" broadly. If your product handles communications metadata, get a legal opinion on your exposure now, before the bill passes and the compliance clock starts.

**What to watch:**

- **Parliamentary committee amendments** in the next 4-6 weeks are the critical decision point. If the ministerial order override mechanism survives without a judicial warrant requirement, the exit threats become exits.
- **Apple's UK withdrawal** is the operational playbook here. It happened fast, with minimal user notice, and left UK users without a privacy feature they'd already enabled.
- **The "encryption" definition** deferred to regulation is a sleeper issue. How that term gets defined post-passage could expand or narrow the bill's reach dramatically.

---

## What Happens Next

Bill C-22 has put Canada at a decision point that other democracies are watching. The coordinated resistance from Signal, DuckDuckGo, NordVPN, Windscribe, and Tailscale is unprecedented in scale and specificity. And this approach can fail for everyone involved — companies exit, users lose tools, and governments claim the law still works because no one technically violated it.

A few things worth keeping clear:

- **Metadata retention at one year isn't a compromise** — for zero-knowledge products, it's a structural impossibility.
- **Secret ministerial orders without judicial oversight** are the clause drawing the hardest lines from companies like Signal.
- **Market exits are not hypothetical** — Apple's UK iCloud withdrawal in 2025 is the established precedent.
- **The amendment window is narrow** — parliamentary committee action in coming weeks determines the final text.

Over the next 6-12 months, expect escalation regardless of which direction Canada goes. If the bill passes unchanged, service withdrawals will prompt public backlash, which will either force amendments or entrench the government's position. If amendments narrow the ministerial order powers and clarify the encryption definition, that becomes the template other governments reference when drafting similar legislation. Either outcome shapes what's coming in the EU and Australia.

Signal and DuckDuckGo threatening to leave Canada isn't a PR move. It's an architectural statement. These companies aren't capable of compliance without destroying their products. Canadian users should treat the next legislative cycle as the window that determines whether privacy tooling remains available to them at all.

What amendment would change your assessment of this bill? Worth thinking through before the committee vote.

## References

1. [Signal, DuckDuckGo, and NordVPN threaten to exit Canada if metadata surveillance law passes | TechSp](https://www.techspot.com/news/112672-signal-duckduckgo-nordvpn-threaten-exit-canada-if-metadata.html)
2. [Signal, DuckDuckGo & More Threaten Canada Exodus Over Surveillance Bill](https://www.yahoo.com/news/politics/articles/signal-duckduckgo-more-threaten-canada-185322945.html)
3. [Signal, DuckDuckGo among firms weighing Canada exit over lawful access bill - National | Globalnews.](https://globalnews.ca/news/11886905/lawful-access-bill-c-22-companies-services-canada/)


---

*Photo by [Rostyslav Savchyn](https://unsplash.com/@ross_savchyn) on [Unsplash](https://unsplash.com/photos/yellow-duck-on-water-near-city-buildings-during-daytime--nqlMPecTWQ)*
