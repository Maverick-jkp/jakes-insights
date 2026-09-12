---
title: "MCP Server Generators vs Manual Setup: What the Tools Actually Cover"
date: 2026-09-12T22:39:23+0900
draft: false
author: "Jake Park"
categories: ["tech-economy"]
tags: ["subtopic-devtools", "api", "docs", "sdk"]
description: "Cut MCP server setup from 3 engineering days to one click. See how Cortex's MCP server generator stacks up against manual API wiring."
image: "/images/20260912-api-docs-sdk-one-click-cortex.webp"
faq:
  - question: "How long does wiring an MCP server actually take manually?"
    answer: "Manual MCP server setup typically costs two to three engineering days per API when you factor in JSON-RPC 2.0 transport, OAuth wiring, and hosting infrastructure. Automated generators like Speakeasy or Gram can collapse that to minutes, but the output often needs significant curation before it's production-ready."
  - question: "What breaks when you auto-generate from an OpenAPI spec?"
    answer: "Auto-generated MCP servers map every endpoint to a tool, so a 100-route API produces 100 tools flooding the agent's context window. This hurts tool selection accuracy noticeably, because the model struggles to pick the right action when dozens of similar-looking options exist."
  - question: "Is Speakeasy worth it over just writing the server yourself?"
    answer: "Speakeasy makes sense if you need typed SDK output alongside your MCP server, with Zod schema validation and OAuth 2.0 handled automatically. It's harder to justify when your use case demands task-shaped tools or a custom auth flow that doesn't map cleanly to what the generator assumes."
  - question: "Does Gram require you to host your own MCP infrastructure?"
    answer: "No — Gram hosts the MCP server for you after a single OpenAPI file upload, which is the main reason teams pick it over alternatives. The tradeoff is less control over how tools are structured and where your API traffic actually flows."
  - question: "When does manual setup still make sense in 2026?"
    answer: "Manual builds are still worth the sprint cost when you need task-shaped tools instead of endpoint mirrors, custom authentication flows, or a federated gateway architecture. If your API has under 20 meaningful agent-facing actions, the generator output may need so much editing that starting from scratch is faster."
---

Manual MCP server wiring used to eat two or three engineering days per API. That number keeps shrinking fast.

---

## The Automation Gap Is Closing

Anthropic introduced the Model Context Protocol in November 2024. By mid-2026, it's no longer a research curiosity—it's the wiring standard that connects AI agents to real production APIs. Claude Desktop, Cursor, and a growing list of agentic frameworks all speak MCP natively. The question teams are asking isn't *should we expose our API as an MCP server?* It's *how much engineering time should this cost?*

Manual setup has a real price tag. Implementing JSON-RPC 2.0 transport from scratch, keeping tool definitions in sync with API changes, wiring OAuth 2.1, and standing up separate hosting infrastructure can consume a full sprint for a two-person team. Generators like Cortex, Speakeasy, and Gram promise to collapse that timeline to minutes.

The tradeoff isn't obvious. Auto-generated MCP servers from OpenAPI specs have a structural problem: they map endpoints, not tasks. A 100-route REST API produces 100 tools, and that floods an agent's context window to the point where tool selection accuracy degrades noticeably.

What follows breaks down:
- What automated MCP generation actually produces vs. what production requires
- How the leading generators—Speakeasy, Gram, FastMCP, and the open-source `openapi-mcp-generator`—stack up on the criteria that matter
- Where manual setup still earns its cost
- What to watch in the next six months as the tooling matures

**The short version:** Automated OpenAPI-to-MCP generators cut initial setup from days to minutes, but produce endpoint-mapped tools that hurt context efficiency at scale. Tool curation and auth architecture are where the real production cost hides.

Three things to hold onto as you read:

1. Speakeasy generates typed SDKs alongside MCP servers with full Zod schema validation and OAuth 2.0 support.
2. Gram delivers an instantly hosted MCP server from a single OpenAPI upload, targeting teams that don't want to self-host.
3. Manual builds remain the right call when task-shaped tools, custom auth flows, or federated gateway architecture are non-negotiable.

---

## Why This Problem Exists Right Now

REST APIs were designed for human-authored requests. OpenAPI specs describe endpoints, parameters, and response shapes—but they don't encode *intent*. A `POST /orders` endpoint and a `GET /orders/{id}` endpoint are described with equal weight in a spec file, even though the agent workflow that needs them might only care about the second one.

MCP flips that model. Instead of exposing every route, MCP servers expose *tools*—discrete, describable actions that an AI agent can discover and call. The protocol handles transport (Streamable HTTP, SSE), session lifecycle, version negotiation, and tool discovery in a standard way. According to Claude's MCP documentation, tools are the primary abstraction: each one needs a name, a description the model can reason about, and a JSON Schema for its inputs.

That's exactly what OpenAPI already contains. Endpoint paths, parameter schemas, response schemas, operation summaries—all present. So automated conversion is technically straightforward. The generator reads the spec, wraps each operation in an MCP tool definition, and emits a server. Done in seconds.

The production gap shows up immediately after. Context windows have real token budgets. Tool definitions are re-sent on every request. A 100-tool catalog burns tokens before the agent even starts reasoning. And shared API keys across all callers—the default in most quick-start generators—is a security model that won't survive a compliance review.

The tooling ecosystem responded fast. By Q1 2026, at least four distinct approaches had emerged, each with different assumptions about who owns the hosting, how auth is handled, and whether SDK generation is in scope.

---

## The Context Window Tax: Why Tool Count Is a First-Order Problem

According to Cortex Gateway's technical analysis, tool definitions are re-sent on every request. That makes large catalogs expensive in two ways: raw token cost, and degraded selection accuracy as the model tries to choose from a bloated list.

The fix isn't complicated, but it requires intentional design:

- Expose the minimum tools needed to complete real workflows
- Prefer coarse, task-shaped tools over granular route-mapped ones
- Scope-filter catalogs so each caller sees only what they're permitted to use
- Serve compact `tools/list` responses with on-demand full schema fetching for large API surfaces

None of the auto-generators do this by default. Speakeasy supports `x-speakeasy-mcp` extensions in the OpenAPI spec that let you assign custom tool names and scope labels (`read`, `write`, `destructive`). That's the closest thing to intentional curation in a generation flow. But it requires manual annotation of the spec—which is exactly the work the generator was supposed to eliminate.

Gram handles this differently at the platform level, offering toolset curation through a UI after the initial generation step. Not perfect, but it shifts the problem from code to configuration.

---

## Auth: The Invisible Production Blocker

Shared API keys are the default. They're also a non-starter for anything that acts on behalf of individual users.

According to Cortex Gateway's architecture documentation, user-specific agent actions require OAuth 2.1 resource server implementation so individual user identity persists through each call. A gateway architecture centralizes this perimeter once across all services. A wrapper-per-API approach means re-implementing it for every integration.

| Auth Approach | Wrapper Model | Gateway Model |
|---|---|---|
| Credential scope | Shared key per API | Per-user token propagated |
| OAuth perimeter | Per-service | Centralized once |
| Backend changes needed | Yes, each service | No, each service keeps own rules |
| Compliance surface | Fragmented | Single audit point |

This is the biggest practical gap between a quick-start generator and a production deployment. Teams routinely underestimate it until they're two weeks from launch.

---

## What the Four Main Generators Actually Offer

According to Speakeasy's published analysis, four tools dominate the current landscape:

| Feature | Speakeasy | Gram | FastMCP | openapi-mcp-generator |
|---|---|---|---|---|
| Hosting | Self-hosted | Managed cloud | Both | Self-hosted |
| SDK generation | Yes (7+ languages) | No | No | No |
| Tool curation | Via spec extensions | UI-based | Programmatic | None |
| Auth model | OAuth 2.0 | OAuth 2.0 | Manual implementation | Env variables only |
| Type safety | Zod schemas | N/A | Partial | Zod schemas |
| Best for | Teams needing SDKs + MCP | Instant hosted MCP | Python-native APIs | Open-source minimal setup |

**Speakeasy** is the only tool that treats SDK generation and MCP generation as a unified workflow. If your team publishes client libraries in multiple languages *and* wants MCP exposure, that's a real efficiency gain. The `x-speakeasy-mcp` extension system gives you customization hooks without forking the generator. The catch: getting full value out of it requires annotating your spec carefully, which isn't a five-minute job.

**Gram** optimizes for speed-to-hosted. Upload an OpenAPI doc, get a live MCP server within minutes. For teams prototyping agent workflows or evaluating MCP before committing to infrastructure, that's a compelling starting point. The UI-based curation layer is genuinely useful—but it doesn't replace the architectural thinking you'll need when real users arrive.

**FastMCP** fits Python-native teams. FastAPI apps convert with minimal friction. The tradeoff is partial type safety and a more manual auth story. If you're already deep in the Python ecosystem and don't need multi-language SDKs, this is the path of least resistance.

**openapi-mcp-generator** is a CLI tool for teams that want zero dependencies and full control. No customization, no managed hosting, no auth beyond environment variables. It's a starting point, not a finish line.

---

## When Manual Setup Is Actually Worth It

Cortex Gateway's documentation makes a case that a compliant MCP backend requires approximately 120 dependency-free lines of code when transport and lifecycle functions are centralized. That's a surprisingly low bar.

Manual builds earn their cost when:
- Tool shapes don't map to API routes (aggregate operations, multi-step workflows)
- Auth requirements exceed what generators support
- A gateway architecture federates multiple APIs under one MCP server
- The team needs precise control over tool descriptions, which directly affect agent reasoning quality

This approach can fail when teams underestimate ongoing maintenance. Manually built servers need to stay in sync with API changes. There's no generator re-run when the spec updates—someone has to track that manually.

Generators earn their cost when speed matters more than precision, when the API surface is small enough that 1:1 route-to-tool mapping doesn't create context bloat, or when SDK generation is in scope.

---

## Three Scenarios, Three Decisions

**Scenario 1: Internal tooling for a single API with fewer than 20 routes.** Any of the auto-generators work fine. The context window tax is manageable, auth complexity is low, and the time savings are real. `openapi-mcp-generator` or FastMCP gets the job done in under an hour.

*Use a generator. Don't overthink it.*

**Scenario 2: Customer-facing MCP server for a multi-tenant SaaS product.** Shared API keys are a security problem. Tool count may be high. User identity needs to persist through agent calls. Gram or Speakeasy get you to a working prototype fast, but plan for a manual auth layer on top. The gateway model makes more architectural sense here.

*Start with Speakeasy for type-safe generation, then layer OAuth 2.1 before any production traffic.*

**Scenario 3: Agent workflow requiring composite, task-shaped tools.** Think a booking API where "reserve a seat and send confirmation" is one agent action, not two separate route calls. No generator handles this well. The spec doesn't encode intent; the generator can't infer it.

*Manual build. The 120-line baseline is real—start there and add only what the workflow needs.*

One thing worth tracking: Microsoft's skills repository is accumulating MCP server patterns for coding agents. If that project standardizes tool-shaping conventions, it could give generators the intent layer they currently lack.

---

## Where This Heads Next

The "API docs to SDK in one click" promise is real for simple cases and misleading for complex ones. Auto-generation from OpenAPI specs eliminates the transport and scaffolding work—that part is genuinely solved. The hard problems (tool count, auth architecture, task-shaped tool design) don't disappear. They just move downstream.

Over the next six months, expect the generator tooling to close the curation gap. Gram's UI-based toolset management points at where this is heading: generate first, curate second, without touching code. Speakeasy's extension system will likely get more sophisticated as teams report real-world context window problems.

The open question worth tracking: will any generator add semantic analysis of operation descriptions to auto-cluster related routes into composite tools? That's the missing piece that would make "one click" actually mean one click for production workloads.

> **Key Takeaways**
> - Auto-generators cut setup from days to under an hour, but produce endpoint-mapped tools by default—curation is a separate, manual step
> - Tool count is a token-efficiency problem that generators don't solve on their own
> - OAuth 2.1 with per-user identity is the production auth standard; most generators don't handle it out of the box
> - Manual builds (~120 lines) remain the right call for complex workflows and federated architectures
> - This isn't always the answer: generator-built servers need manual maintenance as APIs evolve

Start with a generator. Know exactly where it stops.

## References

1. [Connect to external tools with MCP - Claude Code Docs](https://code.claude.com/docs/en/agent-sdk/mcp)
2. [GitHub - microsoft/skills: Skills, MCP servers, Custom Agents, Agents.md for SDKs to ground Coding A](https://github.com/microsoft/skills)


---

*Photo by [Surface](https://unsplash.com/@surface) on [Unsplash](https://unsplash.com/photos/a-laptop-computer-sitting-on-top-of-a-white-table-F4ottWBnCpM)*
