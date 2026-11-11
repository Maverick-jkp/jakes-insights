---
title: "AI Built Netflix-Style Home Server App: 15MB, Real Results"
date: 2026-11-12T02:46:30+0900
draft: false
author: "Jake Park"
categories: ["side-income"]
tags: ["subtopic-ai", "built", "netflix-style", "home"]
description: "A Reddit user built a Netflix-style home server app with AI that runs 12,800 titles at just 70MB RAM. Real results, not hype."
image: "/images/20261112-ai-built-netflix-style-home.webp"
faq:
  - question: "How much RAM does a media server actually need to index movies?"
    answer: "Holyarrs, built with Claude, indexes 12,800 movies and TV shows using only 70MB of RAM — far below the 110–140MB each individual *arr app typically consumes. The key was giving the AI strict performance constraints during development rather than letting it bloat the codebase freely."
  - question: "What happens when you replace the entire arr stack with one app?"
    answer: "Replacing Sonarr, Radarr, Prowlarr, and the rest with a single unified tool dramatically cuts memory overhead and eliminates the hassle of managing five separate update cycles and UIs. Holyarrs collapsed that entire stack into a 15MB app with a single Spotify-style interface."
  - question: "Is vibe coding actually usable for real production tools yet?"
    answer: "Based on Holyarrs, yes — when the developer sets tight guardrails around performance and scope, Claude can produce a functional, low-footprint app rather than bloated boilerplate. The workflow still requires an experienced developer guiding constraints, not just prompting blindly."
  - question: "Why does Jellyfin still need Sonarr and Radarr running alongside it?"
    answer: "Jellyfin handles media playback and library browsing but doesn't manage downloading, indexing sources, or automating new content — that's what the *arr tools do. The two systems solve different layers of the problem, which is why most self-hosters end up running both stacks simultaneously."
  - question: "Can a Raspberry Pi actually run a decent home media server in 2026?"
    answer: "It depends heavily on the software stack — running five separate *arr apps plus a media frontend can strain low-power hardware fast given the combined memory footprint. A lightweight unified app like Holyarrs at 70MB RAM changes the math significantly for devices like a Pi 5 or old NUC."
---

A Reddit user built a fully functional Netflix-style media server app using Claude — and the whole thing weighs 15MB. That's not a prototype. It's running 12,800 movies and TV shows indexed at 70MB RAM.

That number alone reframes what AI-assisted development can produce in 2026.

The home media server space has been fragmented for years. Running a serious setup meant juggling Sonarr, Radarr, Lidarr, Bazarr, Prowlarr, and Seerr as separate installs — each weighing 110–140MB. CoderLuii, a Reddit developer, decided to collapse the entire stack into one app. The tool: Anthropic's Claude, used through a vibe-coding workflow. The result: **Holyarrs**, a unified web app with a Spotify-inspired UI, available at holyarrs.coderluii.dev.

This isn't about the novelty of using AI to write code. It's about what the *output benchmarks* tell us about where AI-assisted development actually stands in late 2026.

Three things this piece covers:
1. Why the existing home media server ecosystem created the conditions for this to work
2. What the technical benchmarks actually reveal about Claude's development output
3. What this signals for solo developers building production tools right now

---

## Background: Why Home Media Servers Are Still a Mess in 2026

The *arr stack — Sonarr, Radarr, Lidarr, and friends — emerged as the community answer to media library management when Plex became increasingly commercial. Each tool does one thing well. Sonarr handles TV. Radarr handles movies. Prowlarr manages indexers. Seerr ties requests together.

The problem: running all five means managing five separate processes, five separate update cycles, five different UIs, and five memory footprints. Each app clocks in at 110–140MB individually, [according to XDA Developers](https://www.xda-developers.com/someone-used-claude-to-make-their-own-plex-like-app-and-its-only-15mb/). On a low-power home server — a Raspberry Pi 5, an old NUC, a repurposed ThinkPad — that overhead compounds fast.

Plex tried to be the unified solution but moved toward subscription monetization. Jellyfin filled part of the gap as an open-source alternative. But neither solves the management layer. The *arr stack still runs alongside either one.

So the gap CoderLuii targeted was real. Not hypothetical, not a niche edge case. Anyone running a self-hosted media setup has lived with exactly this friction.

Vibe-coding — iterative AI-assisted development where the developer guides constraints rather than writing every line — has matured significantly through 2025 and into 2026. Claude has moved from "writes decent boilerplate" to "can produce a working, constrained-performance app when given specific guardrails." Holyarrs is evidence of that shift in practice.

---

## The Performance Constraints That Made This Work

CoderLuii didn't just ask Claude to build an app. The critical detail, [reported by XDA Developers](https://www.xda-developers.com/someone-used-claude-to-make-their-own-plex-like-app-and-its-only-15mb/), is that hard performance limits were enforced *during* the development process — memory caps, boot speed targets, and total file size ceilings.

That constraint-first approach changed the output significantly. Claude generated two distinct versions of the app. The selected build was **3x lighter and faster** than the alternative. Without those upfront constraints, the default output would have been heavier — probably closer to what any developer naturally produces without thinking carefully about resource budgets from the start.

This is the real finding. AI development tools don't automatically produce efficient code. They produce *constrained* efficient code when you specify the constraints clearly. The developer's job in a vibe-coding workflow isn't just to describe features. It's to define the performance envelope first.

Holyarrs running at 70MB RAM with 12,800 items indexed — across a function set that previously required five separate apps — validates that the constraint approach works at a level that matters for real hardware.

This approach can fail, though. Developers who treat AI tools as autocomplete for feature lists — describing *what* they want without specifying performance limits — tend to get bloated output that requires significant manual optimization afterward. The constraint-first discipline is the differentiator, not the AI tool itself.

---

## What 15MB Actually Means at Scale

Size alone isn't the story. Context is.

| Metric | Holyarrs | Individual *arr App | Full *arr Stack (5 apps) |
|--------|----------|---------------------|--------------------------|
| Download Size | 15MB | 110–140MB each | ~600MB total |
| RAM Usage | 70MB (12,800 items) | ~100–200MB each | ~600MB–1GB combined |
| Number of Processes | 1 | 1 per tool | 5+ |
| UI Consistency | Single Spotify-style UI | 5 different UIs | Fragmented |
| Update Surface | 1 app | 1 per tool | 5 separate update cycles |

*Source: [XDA Developers](https://www.xda-developers.com/someone-used-claude-to-make-their-own-plex-like-app-and-its-only-15mb/)*

The operational simplification matters as much as the raw memory numbers. Fewer processes mean fewer failure points. One update cycle instead of five. One UI to learn. On a home server running headless, that reduction in management overhead is the actual value delivered — not just the smaller binary.

Whether these numbers hold at higher library sizes — 50,000+ items, for instance — remains an open question. The community will stress-test that once the open-source release lands.

---

## The Vibe-Coding Workflow Under the Hood

CoderLuii's approach illustrates something worth watching in 2026 developer workflows. Traditional development on a project like Holyarrs would require significant experience across multiple domains: system design, frontend UI, API integration with existing arr tools, and performance profiling for resource-constrained hardware.

Vibe-coding with Claude shifted the work. The developer focused on constraint specification and architectural decisions — which version to ship, what trade-offs to accept — while the AI handled code generation across those domains. That's a different skill set than writing the code directly. It's closer to technical product ownership than traditional programming.

This isn't always the answer. Projects requiring deep domain expertise — security-critical infrastructure, real-time systems, complex distributed architectures — still demand hands-on engineering judgment that constraint prompting alone won't cover. But for a self-contained media server targeting specific hardware limits, the workflow fits cleanly.

The community response on r/ClaudeAI has been positive, and CoderLuii has committed to open-sourcing the project. The public roadmap is already live. That signals this isn't a one-off experiment — it's a project with ongoing development intent.

---

## What This Signals for Developers in 2026

For solo developers targeting fragmented ecosystems, Holyarrs is a concrete case that AI-assisted development can produce a production-quality tool — not a demo — when the developer specifies performance constraints upfront. The gap CoderLuii targeted existed because the *arr ecosystem was never designed for consolidation. Similar gaps exist in other self-hosted tooling spaces: home automation dashboards, local network monitoring, NAS management interfaces.

The pattern worth extracting: identify a fragmented tool ecosystem, define the performance envelope before writing a single line, then use Claude or comparable tools to build toward those constraints iteratively.

For the open-source community, the planned release matters for a different reason. Once the codebase is public, the community can inspect exactly how Claude-generated code performs under real usage, which parts required heavy manual editing, and whether the architecture holds up to contributions. That transparency will be more informative than any benchmark CoderLuii can self-report.

**Three things worth watching over the next 3–6 months:**
- Whether the open-source release happens on the stated timeline
- Community-reported RAM and performance numbers at higher library sizes (50,000+ items)
- Whether competing projects emerge using similar constraint-first AI workflows

---

## What Comes Next

Holyarrs is a 15MB app that consolidates five separate tools, runs on 70MB RAM with 12,800 items indexed, and was built by one developer using Claude with strict performance constraints. Those numbers are real and documented.

The broader signal is specific: AI-assisted development produces meaningfully better output when performance constraints are defined before generation begins — not after. CoderLuii's decision to enforce hard limits on memory, boot speed, and file size is what separated the winning build from an alternative that was 3x heavier. The AI didn't make that call. The developer did.

> **Key Takeaways**
> - Constraint-first prompting drives measurably better AI output — define limits before generating code
> - One developer consolidated a 600MB+ fragmented tool ecosystem into a single 15MB app
> - The *arr community now has a viable lightweight alternative in active development
> - Vibe-coding in 2026 shifts developer work toward constraint design and architectural judgment, not line-by-line code writing
> - Performance at scale (50,000+ library items) remains unverified — the open-source release will be the real test

Over the next 6–12 months, watch whether Holyarrs' open-source release triggers similar projects. The home server community has always been willing to build — the toolchain has now changed what a solo developer can realistically ship in a reasonable timeframe.

The question worth sitting with: if one developer with Claude can consolidate five apps into 15MB, what fragmented tool ecosystem in your own workflow is overdue for the same treatment?

---

*Sources: [XDA Developers — Holyarrs coverage](https://www.xda-developers.com/someone-used-claude-to-make-their-own-plex-like-app-and-its-only-15mb/) | [Hacker News discussion](https://news.ycombinator.com/item?id=50439000)*

## References

1. [r/SideProject on Reddit: I built a Netflix-style streaming request app for my home server. 6 months,](https://www.reddit.com/r/SideProject/comments/1xcrmr8/i_built_a_netflixstyle_streaming_request_app_for/)
2. [Someone used Claude to make their own all-in-one Plex-like app, and it's only 15mb](https://www.xda-developers.com/someone-used-claude-to-make-their-own-plex-like-app-and-its-only-15mb/)
3. [Show HN: A 15 MB self-hosted Netflix and Spotify for your media server | Hacker News](https://news.ycombinator.com/item?id=50439000)


---

*Photo by [Igor Omilaev](https://unsplash.com/@omilaev) on [Unsplash](https://unsplash.com/photos/a-computer-chip-with-the-letter-a-on-top-of-it-eGGFZ5X2LnA)*
