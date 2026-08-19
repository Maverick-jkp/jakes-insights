---
title: "Amazon Destroying Rare Books to Train AI: What It Means for Your Data"
date: 2026-08-19T19:42:38+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-ai", "amazon", "destroying", "rare"]
description: "Amazon destroyed 1,000 rare books to train AI at a Las Vegas warehouse. Here's what this means for your data and digital rights."
image: "/images/20260819-amazon-destroying-rare-books.webp"
faq:
  - question: "Why are AI companies buying physical books instead of just scraping the web?"
    answer: "Most major LLMs have already processed the bulk of publicly available internet content, creating what the industry calls a 'data wall.' Physical books — especially pre-2022 ones that predate widespread AI-generated text — are one of the last guaranteed sources of clean, human-authored writing."
  - question: "What happens to a model trained on AI-generated content?"
    answer: "It degrades through a process called 'model collapse,' where errors compound and output drifts further from authentic human language patterns over successive training runs. This is why rare physical books are so valuable — they're provably human-written in a way that most modern internet text no longer is."
  - question: "Is Amazon actually destroying rare books to feed an AI?"
    answer: "Yes — a bookseller tracked a shipment of 1,000 rare books using an Apple AirTag, and the tracker led to an Amazon warehouse in Las Vegas (facility VGT3) where spines are cut and pages are scanned at high speed. This was reported by 404 Media in August 2026 and the books were not returned."
  - question: "Does it matter legally if a company buys books before destroying them for training?"
    answer: "Buying the physical copies appears to sidestep the kind of copyright exposure Anthropic faced — they settled for $1.5 billion in July 2026 after using pirated books in training data. Purchasing doesn't necessarily grant rights to reproduce or train on the text, though, and legal clarity on that question is still unsettled."
  - question: "How does this affect regular people who publish or create content online?"
    answer: "If rare physical texts are being destroyed and locked inside proprietary models, it sets a precedent for how AI companies treat all source material — including yours. Once that content is ingested into a closed model with no public access, the original is effectively gone from the cultural record."
---

A bookseller embeds an Apple AirTag in a shipment of 1,000 rare books sold through the Biblio marketplace. The tracker leads straight to an Amazon warehouse in Las Vegas — facility VGT3, identifiable by an internal logo of a T-Rex consuming a book. Workers there cut the spines off each volume and feed the pages through high-speed scanners. The books don't come back.

That's not a hypothetical. That's August 2026.

This isn't just a story about old books. It's about who controls the last reservoirs of verified human-written text, what happens when that text gets locked inside a proprietary model, and what precedent that sets for every piece of content you create.

> **Key Takeaways**
> - Amazon operates a dedicated book-destruction scanning facility (VGT3) in Las Vegas, confirmed by a 404 Media AirTag investigation published August 17, 2026.
> - The "data wall" problem — most LLMs have already processed the majority of public internet content — is driving AI companies toward physical media as the last untapped source of guaranteed human-authored text.
> - Training on AI-generated content causes "model collapse," a documented quality degradation; pre-2022 physical books are one of the few remaining clean data sources.
> - Anthropic reached a $1.5 billion copyright settlement in July 2026 for using pirated books in training data, establishing a legal baseline that Amazon appears to be sidestepping through direct purchase.
> - Once a rare physical text is destroyed and ingested into a proprietary model, no public access to that content exists — the cultural record is gone.

---

## The Data Wall That's Driving This

Large language models run on text. Lots of it. The original training runs for GPT-3, LLaMA, and their successors drew heavily from Common Crawl, Wikipedia, GitHub, and scraped web content. That well is largely dry now. Most major LLMs have already processed the majority of publicly available internet content — a situation the industry calls the "data wall."

Synthetic data seemed like the obvious workaround. Train a model, use it to generate more text, train the next model on that. Clean, scalable, self-sustaining. Except it doesn't work. "Model collapse" is a documented phenomenon: when models train on AI-generated content, output quality degrades systematically, errors compound, and the model's distribution drifts from authentic human language patterns. [According to TechCrunch](https://techcrunch.com/2026/08/17/amazon-once-an-online-bookseller-is-destroying-rare-books-to-train-ai-models/), sources describe this as comparable to "digital inbreeding" — an evocative but technically accurate framing.

So the industry needs human-written text. Pre-2022 text specifically, because anything written after mid-2022 risks contamination from publicly released LLM output. Rare, never-digitized physical books are one of the only remaining sources that guarantee 100% human authorship. That's why Amazon is buying them in bulk and destroying them.

The Anthropic copyright settlement adds important context. In July 2026, Anthropic settled for $1.5 billion after using pirated books for training data. Amazon's approach — purchasing books through commercial channels — appears designed to avoid that legal exposure. A court ruling from the Anthropic case established that converting physical books to digital files before destroying the originals qualifies as "transformative use," exempting it from copyright infringement, [according to Futurism](https://futurism.com/artificial-intelligence/amazon-destroying-rare-books-ai). Amazon is working within that ruling.

This approach can fail when the content quality doesn't hold — if the physical texts sourced are damaged, incomplete, or too niche to generalize well, the training signal deteriorates. Buying in bulk doesn't guarantee clean data. It just guarantees scale.

---

## What VGT3 Actually Does

The 404 Media investigation gives unusually specific operational detail. The bookseller shipped approximately 1,000 rare books — some with very few surviving copies — and embedded an AirTag. The package went to VGT3, Amazon's Las Vegas facility. Workers there operate an assembly-line process: receiving, spine-cutting, and scanning are separate assigned roles.

The facility's internal T-Rex logo isn't subtle. It reflects the operation's actual nature.

[According to Futurism](https://futurism.com/artificial-intelligence/amazon-destroying-rare-books-ai), booksellers have identified behavioral patterns pointing to systematic AI procurement: unusually large orders, seemingly random book selections, and a consistent requirement that books carry ISBNs. That ISBN filter matters. ISBNs create a machine-readable catalog of every formally published work. If Amazon — or other AI companies — are working from ISBN databases, they may be attempting to digitize every formally published book, not just cherry-picking titles.

Amazon's only public statement: it "purchases books through commercial channels to improve the products and services customers use." No disclosure of volume. No acknowledgment of physical destruction. No comment on the cultural significance of the texts involved.

---

## Google Books vs. Amazon VGT3: A Key Distinction

This isn't the first time a tech giant has digitized physical books at scale. But the differences between Google Books and Amazon's VGT3 program matter significantly.

| Dimension | Google Books | Amazon VGT3 |
|---|---|---|
| **Stated purpose** | Public accessibility | Proprietary AI training |
| **Physical books destroyed?** | No — scanned intact | Yes — spines cut, books destroyed |
| **Access to digitized content** | Partial public access, library partnerships | Fully proprietary, no public access |
| **Legal framework** | Authors Guild lawsuit settled 2016 | Operates under 2026 Anthropic "transformative use" ruling |
| **Target texts** | Wide range, including in-print | Specifically out-of-print, no existing digital equivalent |
| **Volume transparency** | Reported ~40 million books by 2015 | Not disclosed |

Google's digitization effort was legally contested and culturally controversial, but the scanned content at least fed into a partially public index. Amazon's ingestion is entirely proprietary. The digital record of a destroyed rare book lives inside Amazon's model weights — accessible only through API calls, on Amazon's terms, at Amazon's price.

That's a meaningful shift in who controls cultural memory.

---

## What This Means for Creators, Publishers, and Developers

**For publishers and authors:** The Anthropic settlement established $1.5 billion as a legal floor for mass book ingestion without permission. Amazon's commercial-purchase approach sidesteps that. But it doesn't address a harder question: even if purchase is legal, is permanent destruction of unique cultural artifacts an acceptable practice for commercial AI development? That's a policy question, not a legal one, and it's heading toward legislatures faster than most people expect.

**For rare book sellers:** The ISBN-filter pattern [documented by Futurism](https://futurism.com/artificial-intelligence/amazon-destroying-rare-books-ai) suggests sellers should assume that bulk orders with random-seeming title selections may be AI procurement. Some sellers may consider that an acceptable transaction. Others won't. Either way, it's worth knowing who you're actually selling to — and what happens to the inventory afterward.

**For developers building on Amazon's AI products:** Training data provenance matters for reliability. Models trained on verified pre-2022 human text should theoretically be more resistant to model collapse than those with synthetic data contamination. That's a genuine quality argument in Amazon's favor. But it only holds if the methodology scales cleanly and the sourced content maintains quality — neither of which is guaranteed when you're buying books by the pallet.

**What to watch:** Expect regulatory pressure on physical artifact destruction within 6–12 months. The EU AI Act's data governance provisions are already moving in this direction. A second signal worth tracking: whether other AI companies — OpenAI, Google DeepMind, Meta — have equivalent undisclosed physical scanning programs. The ISBN-pattern behavior suggests Amazon isn't operating alone.

---

## What Comes Next

The core dynamic isn't going away. Human-written, pre-2022 text is a finite resource, and every major AI lab is competing for the same pool. Physical books are the last large reservoir. Some combination of new legal frameworks, regulatory intervention, or data licensing deals is the probable endpoint — but that could take years to resolve, and a lot of irreplaceable texts will be gone before it does.

A few reasonable predictions for the next 12 months:

- **More investigations**: The AirTag approach works. Expect more booksellers and journalists to run similar operations targeting other AI companies.
- **Legislative action**: At least one major jurisdiction — likely the EU — will propose specific rules around physical artifact destruction for AI training purposes.
- **Disclosure pressure**: Amazon and peers will face increasing calls to disclose training data provenance, volume, and destruction methodology, regardless of current legal permissibility.

This ultimately comes down to a concentration-of-knowledge problem. When unique texts exist only inside proprietary models, access to that knowledge is metered, monetized, and controlled by a single company. That's a structural shift in how information works — not just for AI researchers or rare book collectors, but for anyone who assumes that published cultural knowledge remains publicly accessible over time.

The question worth sitting with: if an AirTag can expose this operation, what else is happening that nobody's tracked yet?

---

**Sources:**
- [TechCrunch — Amazon Destroying Rare Books to Train AI](https://techcrunch.com/2026/08/17/amazon-once-an-online-bookseller-is-destroying-rare-books-to-train-ai-models/)
- [Futurism — Amazon Caught Destroying Rare Books to Train AI](https://futurism.com/artificial-intelligence/amazon-destroying-rare-books-ai)

## References

1. [Amazon, which started off selling books, is destroying rare texts to train AI | TechCrunch](https://techcrunch.com/2026/08/17/amazon-once-an-online-bookseller-is-destroying-rare-books-to-train-ai-models/)
2. [Amazon joins the list of companies destroying rare books to feed to the AI machine](https://appleinsider.com/articles/26/08/17/amazon-joins-the-list-of-companies-destroying-rare-books-to-feed-to-the-ai-machine)
3. [Amazon Caught Destroying Rare Books to Train AI](https://futurism.com/artificial-intelligence/amazon-destroying-rare-books-ai)


---

*Photo by [Growtika](https://unsplash.com/@growtika) on [Unsplash](https://unsplash.com/photos/an-abstract-image-of-a-sphere-with-dots-and-lines-nGoCBxiaRO0)*
