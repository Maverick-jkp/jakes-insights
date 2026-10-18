---
title: "Can AI Really Find New Scientific Discoveries? The NASA Planet Story"
date: 2026-10-18T22:50:18+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "can", "really", "find"]
description: "An amateur developer used AI to find a potential exoplanet 116 light-years away — now NASA is pointing telescopes at it. What this means for AI scientific discovery."
image: "/images/20261018-ai-find-new-scientific.webp"
faq:
  - question: "How did one developer get NASA to actually schedule telescope time?"
    answer: "Pavel Rabtsevich, a Spain-based developer with no astronomy degree, used Claude Code and OpenAI's Codex to analyze publicly available NASA TESS data and identified a credible exoplanet candidate 116 light-years away. NASA deemed the signal worth following up on and scheduled official observations — a rare institutional response to an outside, AI-assisted submission."
  - question: "Is the planet he found actually confirmed or still just a maybe?"
    answer: "It's still unconfirmed as of the time of writing. The candidate shows 22 consistent dimming events across three TESS datasets, but instrumental artifacts from TESS thruster firings remain a live concern. AI detection and formal scientific validation are still two very different steps in the process."
  - question: "What kind of AI was used to find this exoplanet candidate?"
    answer: "Rabtsevich used Claude Code and OpenAI's Codex, running them against publicly available NASA TESS light curve data over two weeks. The process generated 74 analyses and over 1,000 scripts to identify and cross-validate the recurring dimming signal across multiple datasets."
  - question: "Can regular people actually do real science with AI now or is this a one-off?"
    answer: "This case isn't entirely isolated — a separate University of Warwick study from May 2026 used AI to find over 100 previously hidden planets in existing NASA data. The combination of publicly accessible datasets and AI coding agents has genuinely lowered the barrier for non-specialists to run workflows that used to require institutional resources."
  - question: "Why didn't professional astronomers catch this signal first?"
    answer: "The signal was actually flagged by a TESS detection filter back in 2020 but was rejected as inconclusive. The core problem isn't access — NASA's TESS data covers over 200,000 stars and is publicly available — it's volume. Spotting a star dimming by fractions of a percent across thousands of data points is exactly the kind of pattern-matching problem modern AI agents handle well."
---

An amateur developer with no astronomy degree just prompted NASA into scheduling telescope time. That's not a thought experiment — it happened in October 2026.

Pavel Rabtsevich, a Spain-based developer, spent two weeks running Claude Code and OpenAI's Codex against publicly available NASA TESS data. The result: a credible exoplanet candidate 116 light-years away that NASA deemed worth following up on. According to Cybernews, the AI produced 74 analyses and over 1,000 scripts during that process. Professional astronomers didn't find this signal first. An AI-assisted outsider did.

So the question worth asking now isn't "can AI help with science?" We're past that. The sharper question is: what does this specific case tell us about where AI-assisted discovery actually works, where it falls short, and what it means for scientific institutions?

> **Key Takeaways**
> - Pavel Rabtsevich used Claude Code and OpenAI's Codex to identify exoplanet candidate TIC 4206066, prompting NASA to schedule follow-up observations — a notable institutional response to an individual's AI-assisted submission.
> - The candidate planet is estimated at 1.4× Earth's radius with a ~3-day orbital period, identified through 22 confirmed dimming events across three separate TESS datasets spanning 2018–2025.
> - A separate University of Warwick study published May 2026 confirmed AI's detection power at scale, identifying over 100 previously hidden planets in existing NASA data.
> - The planet remains unconfirmed — instrumental artifacts from TESS thruster firings remain a live concern — showing that AI detection and scientific validation are still distinct steps.
> - This case represents a structural shift: publicly available datasets plus AI coding agents now let non-specialists execute scientific workflows that previously required institutional access.

---

## The Data Was Always There

NASA's TESS satellite has been collecting light curves from over 200,000 stars since 2018. The raw data is publicly accessible. The problem was never availability — it was volume. Identifying a planetary transit means spotting a star dimming by fractions of a percent, repeatedly, across thousands of data points, then ruling out every other explanation for that dimming.

That's a pattern-matching and elimination problem. Exactly what modern AI agents are built for.

Rabtsevich scanned data from over 126,000 target stars, according to TechTimes. He focused on star TIC 4206066 after the AI flagged a recurring dimming pattern: brightness drops of roughly 0.05% for approximately two hours every 3.18 days. Tight. Repeating. The AI cross-validated it across TESS datasets from 2018, 2020, and 2025.

Separately, MIT doctoral student Pablo Mercader Perez confirmed the signal had been flagged by a TESS detection filter back in 2020 — but was rejected as inconclusive. Astronomer Michelle Kunimoto's LEO-Vetter software independently flagged the same candidate in 2026. Three independent systems, one signal. That's not noise.

The University of Warwick's AI system, published in May 2026, adds scale to what Rabtsevich demonstrated individually. According to ScienceDaily, that system identified over 100 previously undetected planets in existing NASA data — including planets described as "rare and extreme." The data was sitting there. Human reviewers missed it.

---

## The Signal Was Real Enough to Pass Multiple Filters

The credibility of TIC 4206066 doesn't rest on one algorithm's output. It passed three independent checks: Rabtsevich's custom pipeline, LEO-Vetter, and the retrospective confirmation from the 2020 TESS filter. That's meaningful signal stacking.

The candidate's characteristics are internally consistent. A 1.4× Earth-radius planet with a 3-day orbital period puts it close to its host star — hence the estimated surface temperature of around 1,000°F (540°C). Hot, fast-orbiting super-Earths are a well-documented exoplanet category. The signal fits the profile.

What keeps this unconfirmed is a legitimate methodological concern: some of the 2018 dimming events coincided with TESS thruster firings. Instrumental artifacts can mimic transits. The AI flagged and tested for this, but NASA's follow-up observations are necessary to rule it out definitively. The AI found a candidate. It cannot confirm one. Those are different things.

## What the Methodology Actually Looked Like

Two weeks. Seventy-four analyses. Over 1,000 scripts.

Claude Code handled TESS data processing, transit fitting, and alternative explanation testing. OpenAI's Codex independently reviewed portions of the work. Multiple AI agents wrote code, executed analyses, and cross-checked results against each other. Yale astronomer Greg Laughlin, quoted in TechTimes, characterized this as a human-AI collaboration model — Rabtsevich retained control over research design and publication decisions throughout.

That framing matters. Rabtsevich directed the investigation. The AI executed it at scale. Neither alone gets you to a NASA follow-up observation.

## Where AI-Assisted Discovery Works — and Where It Doesn't

| Dimension | AI-Assisted Detection | Traditional Peer Review |
|---|---|---|
| **Data volume** | Scales to 126,000+ stars | Limited by human bandwidth |
| **Speed** | 2 weeks, 1,000+ scripts | Months to years per study |
| **False positive screening** | Automated, multi-layer | Expert judgment, slower |
| **Institutional credibility** | Requires external validation | Built into process |
| **Confirmation** | Cannot confirm independently | Required for publication |
| **Access** | Open to non-specialists | Requires institutional affiliation |

The table tells a clear story. AI accelerates detection and screening. It doesn't replace confirmation. These are different scientific acts, and conflating them is where hype outpaces reality.

The Warwick study's 100+ planet detections demonstrate the detection side at bulk scale. Individual candidates like TIC 4206066 still need follow-up spectroscopy, additional photometry, and peer review before they enter the confirmed exoplanet catalog. That pipeline hasn't changed. What changed is the front end — how candidates get surfaced in the first place.

This approach can also fail in specific ways. When training data is sparse or the signal-to-noise ratio is low, AI screening produces false positives that waste institutional follow-up resources. The thruster-firing artifact concern in this case is a real example of where automated systems can be fooled by data quality issues that an experienced astronomer might flag immediately. AI doesn't have intuition about instrumentation quirks. Domain experts do.

## The Institutional Shift Nobody's Talking About

NASA scheduling observations based on an individual developer's AI-assisted submission is the part of this story that deserves more attention.

Scientific institutions aren't known for speed or openness to outside submissions. The fact that this case cleared that bar signals something structural: when the methodology is transparent, the data is public, and multiple independent systems corroborate the finding, the institution responds. That's how it should work — and it rarely does this fast.

The open question is whether this scales. If AI systems can surface 100+ candidate planets from existing data, institutions need faster, more structured review pipelines for AI-generated candidates. NASA scheduling individual follow-ups case by case won't hold if submissions start arriving in volume. That's an infrastructure problem, not a science problem.

And it's not just astronomy. Data-rich fields — genomics, materials science, climate modeling — have the same structural situation: public datasets, human review as the bottleneck. If an amateur with AI agents can surface a credible exoplanet candidate from TESS data, the honest question is what's sitting undiscovered in public genomics repositories right now.

---

## Three Groups, Three Takeaways

**For developers and engineers:** The Rabtsevich workflow is replicable. Claude Code, public NASA data, two weeks. The barrier to contributing to scientific discovery has dropped to technical skill plus access to a public API. The pattern worth studying — AI agents for hypothesis generation and screening, human for research design and judgment calls — applies well beyond astronomy.

**For scientific institutions:** Detection is no longer the bottleneck. Confirmation is. If AI systems can surface candidates faster than review pipelines can process them, the constraint shifts entirely. Institutions that don't build faster, more scalable follow-up mechanisms will find themselves with growing queues of credible, unreviewed signals.

**For domain experts:** The LEO-Vetter and MIT cross-validation in this case show that expertise remains critical — not for running the initial analysis, but for designing validation criteria and catching edge cases like thruster-fire artifacts. Experts who learn to direct AI workflows rather than compete with them are positioned well. Experts who don't are increasingly easy to route around.

**What to watch:** NASA's follow-up observation results on TIC 4206066. If confirmed, it establishes a documented precedent for AI-assisted independent discovery. If ruled out as an artifact, that's equally instructive — it'll define exactly where current AI screening fails and where human judgment is non-negotiable. Either result moves the field forward.

---

## What This Actually Means

The NASA planet story isn't evidence that AI does science. It's evidence that AI dramatically lowers the cost of surfacing candidates worth investigating.

Three things are clear from the data so far:

**Detection works at scale.** Over 100 hidden planets from Warwick's AI system, one credible candidate from a solo developer — same principle, different scope. The pattern holds across both.

**Human direction still matters.** Rabtsevich designed the investigation. The AI executed it. Laughlin called it a collaboration model for a reason — because that's what it was. The AI didn't decide what to look for or why. A person did.

**Confirmation remains the hard part.** Multiple independent flags on TIC 4206066 are compelling. An artifact from a thruster firing is still a live concern. Compelling and confirmed are not the same thing, and the gap between them is where scientific credibility lives.

The mindset shift worth making: stop asking whether AI can find discoveries and start asking which datasets haven't been systematically searched yet. There's a long list. Most of it is publicly accessible. And the tools to start searching are already available to anyone with the technical skill to use them.

## References

1. [Powerful AI finds 100+ hidden planets in NASA data including rare and extreme worlds | ScienceDaily](https://www.sciencedaily.com/releases/2026/05/260502233926.htm)
2. [Could AI Discover a New Planet? Amateur Astronomer Finds Promising Signal in NASA Data](https://www.techtimes.com/articles/329085/20261015/could-ai-discover-new-planet-amateur-astronomer-finds-promising-signal-nasa-data.htm)
3. [Amateur astronomer harnesses AI to find a possible hidden exoplanet | Scientific American](https://www.scientificamerican.com/article/amateur-astronomer-harnesses-ai-to-find-a-possible-hidden-exoplanet/)


---

*Photo by [Igor Omilaev](https://unsplash.com/@omilaev) on [Unsplash](https://unsplash.com/photos/a-computer-chip-with-the-letter-a-on-top-of-it-eGGFZ5X2LnA)*
