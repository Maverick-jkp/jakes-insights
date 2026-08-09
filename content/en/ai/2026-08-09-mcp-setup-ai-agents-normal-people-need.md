---
title: "MCP setup for AI agents: what is it and do normal people need it"
date: 2026-08-09T19:39:40+0900
draft: false
author: "Jake Park"
categories: ["ai"]
tags: ["subtopic-ai", "mcp", "setup", "agents:"]
description: "MCP setup explained: 97M monthly downloads but should you bother? Find out if this AI agent protocol actually matters for what you're building."
image: "/images/20260809-mcp-setup-ai-agents-normal.webp"
faq:
  - question: "What actually is MCP and why does everyone suddenly care?"
    answer: "MCP (Model Context Protocol) is an open standard that lets AI agents connect to external tools like databases, filesystems, and APIs through one consistent interface instead of hundreds of custom integrations. Anthropic released it in November 2024, and by early 2026 OpenAI, Google, and Apple had all adopted it. The rapid cross-vendor adoption is why developers are paying attention now."
  - question: "Do I need to configure anything for Claude or Cursor to use it?"
    answer: "Most regular users never touch MCP directly — it runs as background infrastructure inside tools like Claude Desktop or Cursor. Developers building agentic systems are the ones who actually set up MCP servers, which takes under 10 minutes mechanically but requires judgment about what to connect. If you're not writing code that calls external APIs, you probably won't configure it yourself."
  - question: "How is this different from just calling an API normally?"
    answer: "Before MCP, every AI model needed custom code to talk to every external service — if you had 10 models and 10 tools, that meant up to 100 separate integrations to maintain. MCP replaces that with a single standard interface, similar to how USB replaced a mess of incompatible peripheral connectors. Agents route all external calls through MCP servers instead of hitting services directly."
  - question: "Is this an Anthropic-only thing or does it work across tools?"
    answer: "It started as Anthropic's internal solution but is now genuinely cross-vendor. OpenAI adopted it in March 2025, Google confirmed Gemini support in April 2025, and Anthropic donated the whole project to the Linux Foundation in December 2025. It now ships inside GitHub Copilot, Cursor, Claude, and OpenAI's Codex."
  - question: "When should a solo developer actually bother setting this up?"
    answer: "If you're building an agent that needs to read files, query databases, or call external APIs, MCP is worth learning now since it's becoming the default interface in major dev tools. If you're just prompting Claude or ChatGPT for personal use, skip it — you'll benefit from it without ever touching the config. The tipping point is when you need your agent to do things in the real world, not just generate text."
---

The Python and TypeScript SDKs for Model Context Protocol hit **97 million monthly downloads** by March 2026. Six months ago, most developers hadn't heard of it. That trajectory signals something important — but it doesn't tell you whether *you* should care.

The honest answer: it depends entirely on what you're building. For most non-developers, MCP is background infrastructure you'll benefit from without touching. For engineers building agentic systems, it's becoming unavoidable.

The protocol started as Anthropic's solution to a specific engineering headache. It's now under Linux Foundation governance and shipping in GitHub Copilot, Cursor, Claude, and OpenAI's Codex. That kind of cross-vendor adoption doesn't happen by accident.

---

**In brief:** MCP is an open protocol that standardizes how AI agents connect to external tools, replacing hundreds of custom integrations with one consistent interface. It reached 97 million monthly SDK downloads by March 2026, with adoption from Anthropic, OpenAI, Google, and Apple confirming it's not a niche experiment.

1. MCP was open-sourced by Anthropic in November 2024 and donated to the Linux Foundation's Agentic AI Foundation in December 2025.
2. Practical MCP setup takes under 10 minutes in tools like Claude Code or Cursor — but knowing *what* to connect requires engineering judgment.
3. Normal users don't configure MCP; developers building agents do.

---

## What MCP Is and Why It Exists

The M×N problem is the fastest way to explain MCP's origin. Before a standard protocol existed, connecting M AI models to N external tools required M×N custom integrations — every model needed bespoke code to talk to every API. According to Towards Data Science, this is exactly what motivated Anthropic to create MCP, released as open source in **November 2024**.

Think of USB. Before it existed, every peripheral used a different connector. MCP does the same thing for AI tools: one standard interface replaces hundreds of point-to-point connectors.

Architecturally, three components make every MCP interaction work: the **host** (the AI application managing context — think Claude Desktop or VS Code), the **client** (lives inside the host, manages connections), and the **server** (the middleware exposing tools). Agents never talk directly to underlying services like databases or filesystems. Everything routes through MCP servers.

Three capability types exist: **Tools** (executable functions — most powerful, highest risk), **Resources** (read-only data access), and **Prompts** (reusable instruction templates). Tools dominate practical usage.

The adoption timeline moved fast. Launched with roughly 100,000 monthly SDK downloads in November 2024, OpenAI adopted MCP in March 2025, Google confirmed Gemini support in April 2025, and Anthropic donated the project to the **Linux Foundation's Agentic AI Foundation** — co-founded with Block and OpenAI — in December 2025. The combined Python/TypeScript SDKs reached 97 million monthly downloads by March 2026.

That's not incremental growth. That's a standard being settled.

---

## How MCP Setup Actually Works

Setup complexity varies significantly by deployment pattern.

According to Uno Platform's configuration breakdown, configurations split into two deployment patterns:

- **Remote MCP servers**: Always-on URL-based endpoints hosted by vendors. No local installation. Simpler.
- **Local MCP servers**: Spawned on-demand as child processes on the developer's machine. More control, more maintenance.

Configuration also operates at two scopes: **project-level** (committed to repos, shared across teams) and **developer-level** (user-scoped, outside repos — for API keys and personal preferences).

### Agent Configuration Comparison

| Agent | Config File | Location | Format | Server Type Support |
|-------|-------------|----------|--------|---------------------|
| GitHub Copilot | `mcp.json` | `.github/`, `.vscode/`, `.vs/` | JSON | Remote + Local |
| Claude Code | `mcp.json` | `.claude/` | JSON | Remote + Local |
| OpenAI Codex | `config.toml` | `.codex/` | TOML | Remote + Local |
| Cursor | `mcp.json` | `.cursor/` | JSON | Remote + Local |
| Antigravity (Google) | `mcp_config.json` | Project root | JSON | Remote + Local |

*Source: Uno Platform MCP Configuration Guide*

Codex is the outlier — TOML instead of JSON. Antigravity uses a slightly different schema with root-level access requirements. But the underlying logical structure is consistent across all five: declare either a URL (remote) or a command with arguments (local).

Two transport methods handle the actual communication. **Stdio** runs the server as a subprocess communicating via standard input/output — fine for local development. **HTTP with Server-Sent Events** handles remote, production, and multi-tenant deployments. Most developers doing anything serious end up on the HTTP/SSE path.

Pre-built MCP servers already exist for GitHub, Slack, PostgreSQL, Docker, and Kubernetes, all browsable via the MCP Registry. Connecting Claude Code to GitHub's MCP server takes one JSON entry and a restart. The configuration overhead is genuinely low. Knowing *what* to connect and *why* is the harder question.

---

## The Security Picture Nobody's Talking About Enough

The security concerns around MCP are real and underreported.

According to MindStudio, three documented risks exist:

1. **Prompt injection via tool output** — a rogue or compromised tool response can embed instructions that hijack the agent's next action
2. **Tool poisoning** — malicious servers mimicking trusted ones
3. **Over-permissioned access** — broad tool grants creating wide attack surfaces

The MCP specification requires explicit user consent before tool invocation and recommends least-privilege permissions. But enforcement depends on the host application, not the protocol itself. That gap matters.

Authentication follows a clear progression: static environment variables work for development only, OAuth 2.0 is the production standard for delegated per-user access, and runtime API key injection sits in between. Skipping OAuth in production isn't a shortcut — it's a liability.

One practical problem that trips up first-time implementations: large tool response payloads rapidly consume context windows. An MCP server that returns entire database dumps instead of filtered results will burn tokens fast and produce worse outputs. Raw API wrapping without data transformation produces agent-unreadable output. Good MCP server design requires the same discipline as good API design — and teams that treat it as boilerplate tend to regret it within weeks.

This approach can also fail when MCP servers are poorly scoped. Granting an agent broad filesystem access because it's convenient creates an attack surface that grows every time a new tool connects. The architecture rewards restraint.

---

## Who Actually Needs to Configure This

**Developers building agentic applications:** MCP is now the path of least resistance. Writing custom tool integrations per model is the old approach. With 97 million monthly SDK downloads and support from every major LLM vendor, custom integrations are technical debt from day one. Start with pre-built servers from the MCP Registry, then write custom ones using Python's `FastMCP` SDK — the `@mcp.tool()` decorator auto-generates JSON schemas from type hints, cutting boilerplate significantly.

**Platform and DevOps engineers:** The shift to project-level MCP configuration means it's coming to your repos. Agree on configuration scoping conventions *before* API keys start appearing in committed `mcp.json` files. The developer-level scope exists precisely to keep credentials out of version control. This isn't a theoretical problem — it's the kind of thing that shows up in post-incident reviews.

**Normal users — meaning non-developers:** Practically nothing changes operationally. Apps like Claude Desktop or GitHub Copilot handle MCP connections internally. You'll benefit from better tool access without touching a config file. The protocol is plumbing. Good plumbing is invisible.

**What to watch in the next 6 months:**
- Apple's App Intents/Siri alignment with MCP, confirmed as converging, could bring MCP-style tool access to consumer devices at scale
- Linux Foundation's AAIF governance producing formal security standards — the spec currently recommends least-privilege but doesn't enforce it
- Enterprise-grade MCP registries with signed, verified servers — the current trust model is too loose for regulated industries

---

## Where This Goes Next

Three months from now, MCP will be as assumed as npm in a JavaScript project. The cross-vendor convergence is done. The SDK numbers confirm real usage, not just enthusiasm.

> **Key Takeaways**
> - MCP eliminates the M×N integration problem by standardizing tool communication across all major LLM platforms
> - Setup is low-friction — the hard part is good server design, not configuration syntax
> - Security gaps in the current spec are real and will drive the next wave of enterprise tooling
> - Non-developers don't need to configure anything; developers building agents have little justification left to avoid it

**Near-term:** Expect enterprise MCP registries with signed servers to emerge by Q1 2027, directly addressing tool poisoning risks.

**Potential shift:** Apple's consumer-scale MCP alignment could normalize agentic tool access outside developer audiences entirely — which would make MCP one of the few developer protocols to achieve genuine mainstream reach.

The bottom line is straightforward. If you're building agents, MCP setup is no longer optional research — it's baseline infrastructure. If you're not building agents, you'll use it without knowing it. Which is exactly how good standards work.

What's your current tool integration stack? If you're still writing per-model adapters, that's worth reconsidering today.

## References

1. [MCP Explained: How Modern AI Agents Connect to the Real World | Towards Data Science](https://towardsdatascience.com/mcp-explained-how-modern-ai-agents-connect-to-the-real-world/)
2. [What is the Model Context Protocol (MCP)? - Model Context Protocol](https://modelcontextprotocol.io/)
3. [How we built an MCP bridge to give our AgentCore-hosted AI agent access to local MCP tools | Artific](https://aws.amazon.com/blogs/machine-learning/how-we-built-an-mcp-bridge-to-give-our-agentcore-hosted-ai-agent-access-to-local-mcp-tools/)


---

*Photo by [Growtika](https://unsplash.com/@growtika) on [Unsplash](https://unsplash.com/photos/an-abstract-image-of-a-sphere-with-dots-and-lines-nGoCBxiaRO0)*
