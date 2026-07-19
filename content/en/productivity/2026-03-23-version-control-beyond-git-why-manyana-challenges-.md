---
title: "Version Control Beyond Git: Why Manyana Challenges Everything You Know"
date: 2026-03-23T20:11:01+0900
draft: false
author: "Jake Park"
categories: ["productivity"]
tags: ["subtopic-devtools", "version", "control", "beyond", "React"]
description: "Git has dominated version control since 2005. Discover why BitTorrent's creator Bram Cohen believes Manyana exposes its fundamental flaws."
image: "/images/20260323-version-control-beyond-git-why.webp"
technologies: ["React", "Linux", "Go", "Copilot", "Cursor"]
faq:
  - question: "what is Manyana version control and who made it"
    answer: "Manyana is a version control system designed by Bram Cohen, the engineer who created BitTorrent, and published in early 2026. It uses a patch-theory mathematical foundation instead of Git's snapshot-based model, aiming to make merge conflicts rare by design rather than by developer discipline."
  - question: "version control beyond Git why Manyana challenges everything you know explained simply"
    answer: "The core argument in 'version control beyond Git: why Manyana challenges everything you know' is that Git's merge conflicts are a structural consequence of its architecture, not a workflow problem. Manyana treats changes as composable mathematical objects, meaning two logically independent edits that happen to overlap textually no longer automatically produce a conflict."
  - question: "how is Manyana different from Git and Pijul"
    answer: "Like Pijul, Manyana uses patch theory rather than Git's directed acyclic graph of snapshots, meaning it has a formal model of what a change means rather than just recording states. Pijul is currently the most mature patch-theory system, having been in development since 2014, making it the closest real-world benchmark for evaluating Manyana's claimed properties."
  - question: "why don't more developers switch away from Git if better alternatives exist"
    answer: "The main barrier to adopting alternatives isn't technical correctness — it's ecosystem lock-in. Git has over two decades of institutional muscle memory behind it, plus deep integration with platforms like GitHub and GitLab and the entire CI/CD toolchain industry."
  - question: "version control beyond Git why Manyana challenges everything you know — is it worth switching"
    answer: "As covered in 'version control beyond Git: why Manyana challenges everything you know,' Manyana enters a growing conversation alongside alternatives like Jujutsu and Sapling, but adoption curves are still early. Teams dealing with large-scale monorepos or distributed collaboration pain points have the most to gain from watching its development, though ecosystem maturity remains a significant practical barrier."
aliases:
  - "/tech/2026-03-23-version-control-beyond-git-why-manyana-challenges-/"

---

Git shipped in 2005. Twenty-one years later, it's the default — so embedded in developer workflow that questioning it feels almost absurd. Manyana makes the case for questioning it anyway.

Bram Cohen, the engineer who built BitTorrent, published his design for Manyana in early 2026. The core argument: Git's model for tracking changes is fundamentally broken for anything beyond single-developer linear history. Merge conflicts aren't bugs in your workflow. They're a structural consequence of how Git represents change. Manyana proposes a different mathematical foundation — one where conflicts become rare by design, not by discipline.

This matters right now because distributed teams are the norm, not the exception. Monorepos at companies like Google and Meta expose Git's scaling limits daily. And a new generation of version control tools — Pijul, Jujutsu, Sapling — is proving there's real appetite for alternatives. Manyana enters that conversation with the credibility of its author and a genuinely different set of tradeoffs.

The analysis below covers why Git's directed acyclic graph model creates structural merge pain, what Manyana's patch-theory approach actually changes, how it compares to Pijul, Jujutsu, and Git on practical dimensions, and what teams should watch for as adoption curves develop.

---

> **Key Takeaways**
> - Manyana was designed by Bram Cohen (BitTorrent's creator) and published in 2026 as a patch-theory-based alternative to Git's DAG model.
> - Git's merge conflicts are a structural artifact of its snapshot-and-pointer architecture, not a tooling failure — patch-theory systems treat changes as composable mathematical objects instead.
> - Pijul, the most mature patch-theory VCS, has been in active development since 2014 and provides the closest real-world benchmark for Manyana's claimed properties.
> - The real barrier to adoption isn't correctness — it's ecosystem: Git has GitHub, GitLab, CI/CD toolchains, and over two decades of institutional muscle memory working against any challenger.

---

## Git's Architecture: Elegant, but Not Conflict-Free

Git tracks history as a directed acyclic graph (DAG) of snapshots. Each commit is a pointer to a full tree state. Merging means reconciling two diverged snapshot sequences — and when two branches touch the same lines, Git asks a human to decide. That's the model, not a flaw.

For solo developers or small teams with disciplined branching, this works. For fifty engineers hitting the same service layer across three time zones, it doesn't scale gracefully. According to Cohen's Manyana writeup, the root issue is that Git has no formal model of *what a change means* — only of *what state existed*. Two changes can be logically independent but textually overlapping, and Git treats them as a conflict regardless.

The broader VCS research community has known this for over a decade. Darcs, published in 2002, was the first widely discussed patch-theory system. It modeled history as a set of composable patches rather than a sequence of snapshots. The math was sound; the performance wasn't. Darcs hit exponential time complexity on certain merge patterns — a known pathology that limited adoption despite its correctness properties.

Pijul launched in 2014 specifically to fix Darcs' performance problems while keeping patch theory's correctness guarantees. By 2026, Pijul has a working hosted platform at pijul.org and an active developer community, though it's nowhere near Git's adoption footprint.

Manyana enters this lineage with full awareness of what came before.

---

## What Manyana Actually Proposes

Cohen's design centers on a specific claim: patches should be first-class mathematical objects with well-defined composition rules. When two patches are *independent* — meaning neither one logically depends on the other — they should merge automatically, every time, without human intervention. No conflict. Not because the tool is smart, but because the math guarantees it.

This isn't just cleaner merging. It changes what "history" means. In Git, history is a linear or branched sequence of snapshots. In Manyana's model, history is a partially ordered set of patches. You can apply them in different orders and arrive at the same result. That property — confluence — is what makes automatic merging provably safe rather than heuristically safe.

The practical implications are significant for long-lived feature branches. One of Git's most painful real-world patterns is the stale branch problem: a branch diverges for two weeks, accumulates dozens of commits, and produces a merge that touches hundreds of lines. With Manyana's model, patches that genuinely don't interact with anything on the trunk don't conflict — regardless of how long the branch sat open.

Cohen also addresses one of Darcs' failure modes directly. The exponential complexity issue came from certain non-commutative patch sequences that forced exhaustive search. Manyana's patch algebra is designed to avoid those cases structurally, though the full implementation is still in progress as of early 2026.

This approach can fail, or at least disappoint, when patches *aren't* truly independent — when changes touch shared abstractions or interface boundaries in ways that are semantically coupled but textually separate. Patch theory handles the mathematical case cleanly. It doesn't resolve design-level conflicts that Git was never responsible for in the first place.

---

## Comparison: Git vs. Pijul vs. Manyana

| Dimension | Git | Pijul | Manyana |
|---|---|---|---|
| **History model** | DAG of snapshots | Set of patches | Partially ordered patches |
| **Merge conflicts** | Structural (line-level) | Reduced by design | Minimal by proof |
| **Conflict resolution** | Manual, heuristic | Rare, semantic | Rare, mathematical |
| **Performance at scale** | Proven (Linux kernel) | Good, improving | Unknown (early design) |
| **Ecosystem** | Massive (GitHub, GitLab, CI/CD) | Small but active | Pre-launch |
| **Learning curve** | High (but familiar) | Medium | Unknown |
| **Maturity** | 21 years | ~12 years | 2026 design phase |
| **Best for** | Everything, today | Teams testing patch theory | Early adopters watching the space |

The tradeoffs are stark. Git wins on ecosystem, tooling, and institutional knowledge — full stop. Pijul is the only patch-theory system with a production-viable implementation you can use today. Manyana is the most theoretically rigorous of the three, but it's not shipping software yet.

The Pijul community's reaction to Manyana has been cautiously interested. A thread on the Pijul discourse forum asks directly whether Manyana is "same/same/different" — whether it's a Pijul variant or genuinely distinct. Cohen's design has meaningful differences in its patch algebra, but both systems share the same core bet: patch theory produces better merge semantics than snapshot DAGs.

---

## What Teams Should Actually Do With This

The core challenge isn't picking the right VCS today. It's avoiding lock-in to assumptions that become harder to shed later. Git's data model shapes how teams think about branching, review, and deployment. Those habits compound over years.

**Running a growing monorepo?** Git's performance at large scale is a known pain point — Meta's Sapling fork and Google's internal Piper system exist precisely because vanilla Git buckles under that weight. Watching Manyana's development is worth the time. If it ships with the confluence properties Cohen describes, monorepo teams are the first clear beneficiary.

**Evaluating VCS tooling for a new project in 2026?** Jujutsu — Google's open-source VCS, distinct from Piper — is the most practical Git alternative right now. It uses Git's storage layer but replaces the CLI and branching model entirely. Pijul is viable for smaller teams willing to accept a thinner ecosystem. Manyana isn't ready for this decision yet.

**A tooling engineer or OSS contributor?** Cohen's Manyana writeup is worth reading as primary source material. The patch algebra design is specific enough to engage with technically, and early contributors to emerging VCS tools tend to have outsized influence on the final shape of the system.

Watch for: a working Manyana prototype, Pijul's continued performance improvements, and whether Jujutsu's Git-compatible approach captures enough mindshare to become the practical migration path for teams unwilling to leave GitHub behind.

---

## Where This Goes Over the Next 12 Months

The version control space is more active in 2026 than at any point since Git displaced SVN. That's not coincidence — it's the accumulated friction of distributed teams, AI-assisted coding generating higher commit volumes, and engineers who've shipped enough large projects to feel Git's structural limits firsthand.

The pattern to track: Git's merge conflicts are architectural, not accidental, and patch-theory systems address the root cause rather than the symptom. Pijul is the most mature alternative available today, with Jujutsu as the most accessible migration path for teams already deep in the GitHub ecosystem. Manyana brings the strongest theoretical foundation but remains pre-implementation. And ecosystem lock-in, not correctness, is the real adoption barrier for any Git alternative — that's been true since Darcs, and it's still true now.

Near-term, expect a Manyana prototype in the second half of 2026 if Cohen's development pace follows BitTorrent's early trajectory. Medium-term, watch whether AI coding tools like Cursor and GitHub Copilot begin generating commit patterns that stress Git's merge model enough to push enterprise teams toward alternatives. That's the pressure point most likely to accelerate the timeline.

Git won't disappear. But the technical argument for version control beyond Git is real — not marketing. The question isn't *if* a patch-theory system reaches critical mass. It's *which one*, and *when*.

What's your team's biggest merge pain point right now? That answer probably tells you how urgently this matters.

## References

1. [Manyana - by Bram Cohen - Bram’s Thoughts](https://bramcohen.com/p/manyana)
2. [Version control - Wikipedia](https://en.wikipedia.org/wiki/Version_control)
3. [Manyana - Same/Same/Different? - Question - Pijul](https://discourse.pijul.org/t/manyana-same-same-different/1335)


---

*Photo by [Etienne Girardet](https://unsplash.com/@etiennegirardet) on [Unsplash](https://unsplash.com/photos/text-K1UZglGfX-E)*
