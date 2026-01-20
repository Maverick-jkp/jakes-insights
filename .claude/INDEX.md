# .claude Directory Index

Complete navigation guide for all Claude agent documentation, workflows, templates, and project resources.

**Last Updated**: 2026-01-20
**Purpose**: Quick reference for all .claude/ resources and project documentation

---

## Quick Start

### First Time Working on This Project?
1. Read [instructions.md](#core-documentation) - Quick reference for Claude work principles
2. Review [PROJECT_CONTEXT.md](#core-documentation) - Project overview and structure
3. Check [MASTER.md](#agent-definitions) - Understand Master agent workflow
4. Browse [Feature Workflow](#workflow-documentation) - Learn development process

### Common Tasks
- **Start a new feature**: [feature-workflow.md](#workflow-documentation)
- **Understand git branching**: [branching-strategy.md](#workflow-documentation)
- **Create a report**: [agent-report-template.md](#templates)
- **Create a task**: [task-template.md](#templates)

---

## Core Documentation

### Instructions & Context
- **[instructions.md](instructions.md)** - Quick reference for Claude: work principles, Hugo server, git workflow, prohibitions
- **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** - Project overview: tech stack, structure, categories, quick links
- **[README.md](README.md)** - .claude directory overview and agent system explanation

### Configuration
- **[settings.local.json](settings.local.json)** - Local Claude settings and preferences

---

## Agent Definitions

### Primary Agents
- **[MASTER.md](agents/MASTER.md)** - Master agent: task decomposition, parallel workflows, integration, commit/push decisions
- **[CTO.md](agents/CTO.md)** - CTO agent: technical implementation, architecture, performance, testing
- **[DESIGNER.md](agents/DESIGNER.md)** - Designer agent: UI/UX, layouts, responsive design, accessibility
- **[QA.md](agents/QA.md)** - QA agent: testing, validation, quality checks, bug detection

### Agent Examples
- **[MASTER_EXAMPLES.md](agents/MASTER_EXAMPLES.md)** - Example workflows and scenarios for Master agent
- **[CTO_EXAMPLES.md](agents/CTO_EXAMPLES.md)** - Example technical implementations and solutions
- **[DESIGNER_EXAMPLES.md](agents/DESIGNER_EXAMPLES.md)** - Example design decisions and UI improvements
- **[QA_EXAMPLES.md](agents/QA_EXAMPLES.md)** - Example test cases and quality validations

---

## Workflow Documentation

### Development Workflows
- **[feature-workflow.md](workflows/feature-workflow.md)** - Complete feature development process: planning, implementation, testing, deployment
- **[branching-strategy.md](workflows/branching-strategy.md)** - Git branch management: naming conventions, merge strategies, conflict resolution

---

## Templates

### Report Templates
- **[agent-report-template.md](templates/agent-report-template.md)** - Standard report format for CTO, Designer, QA agents to report work completion

### Task Templates
- **[task-template.md](templates/task-template.md)** - Standard format for creating tasks in .claude/tasks/active/

---

## Reports

### Active Reports
**Location**: `.claude/reports/active/`
**Status**: No active reports currently

Reports are created by agents (CTO, Designer, QA) during work and moved to archive after Master review and commit.

### Archived Reports
**Location**: `.claude/reports/archive/YYYY-MM/`

#### 2026-01
- **[cto-domain-investigation-2026-01-20.md](reports/archive/2026-01/cto-domain-investigation-2026-01-20.md)** - CTO investigation of domain configuration and deployment
- **[workflow-failure-analysis-2026-01-20.md](reports/archive/2026-01/workflow-failure-analysis-2026-01-20.md)** - Analysis of workflow implementation issues and solutions

---

## Tasks

### Active Tasks
**Location**: `.claude/tasks/active/`

- **[TASK_POST_INCIDENT_2026-01-20.md](tasks/active/TASK_POST_INCIDENT_2026-01-20.md)** - Post-incident task and improvements

### Task Management
- **[tasks/README.md](tasks/README.md)** - Task system documentation and guidelines

---

## Project Documentation

**Location**: `docs/` (project root)

### Core Documentation
- **[docs/PROJECT_OVERVIEW.md](../docs/PROJECT_OVERVIEW.md)** - High-level project overview and goals
- **[docs/TECH_STACK.md](../docs/TECH_STACK.md)** - Technology stack and dependencies
- **[docs/ARCHITECTURE_DECISIONS.md](../docs/ARCHITECTURE_DECISIONS.md)** - Architectural decision records (ADRs)

### Development Guides
- **[docs/CLAUDE_GUIDELINES.md](../docs/CLAUDE_GUIDELINES.md)** - Claude work principles, common issues, and solutions
- **[docs/CONTENT_WRITING_POLICY.md](../docs/CONTENT_WRITING_POLICY.md)** - Content creation standards and policies
- **[docs/CONTENT_GUIDELINES.md](../docs/CONTENT_GUIDELINES.md)** - Writing style and quality guidelines
- **[docs/QUALITY_STANDARDS.md](../docs/QUALITY_STANDARDS.md)** - Quality benchmarks and validation criteria

### Setup & Configuration
- **[docs/GOOGLE_API_SETUP.md](../docs/GOOGLE_API_SETUP.md)** - Google API configuration and authentication
- **[docs/HUGO_CONFIG.md](../docs/HUGO_CONFIG.md)** - Hugo configuration and customization
- **[docs/WINDOWS_SETUP.md](../docs/WINDOWS_SETUP.md)** - Windows environment setup guide

### Strategy & Planning
- **[docs/KEYWORD_STRATEGY.md](../docs/KEYWORD_STRATEGY.md)** - Keyword research and SEO strategy
- **[docs/KEYWORD_CURATION_GUIDE.md](../docs/KEYWORD_CURATION_GUIDE.md)** - Weekly keyword curation process
- **[docs/AUTOMATION_STRATEGY.md](../docs/AUTOMATION_STRATEGY.md)** - Content automation approach and workflows
- **[docs/MONETIZATION.md](../docs/MONETIZATION.md)** - AdSense and revenue strategy

### Technical Documentation
- **[docs/PYTHON_AUDIT_2026-01-20.md](../docs/PYTHON_AUDIT_2026-01-20.md)** - Python code audit results and recommendations
- **[docs/ERROR_HANDLING_IMPROVEMENTS.md](../docs/ERROR_HANDLING_IMPROVEMENTS.md)** - Error handling enhancements and best practices
- **[docs/DESIGN_SYSTEM.md](../docs/DESIGN_SYSTEM.md)** - UI design system and component library
- **[docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)** - Common issues and solutions

---

## Project Root Files

### Essential Files
- **[README.md](../README.md)** - Project README: overview, quick start, architecture, automation
- **[SECURITY.md](../SECURITY.md)** - Security policies and vulnerability reporting

---

## Search by Category

### Agent Work
- Agent definitions: [MASTER.md](#agent-definitions), [CTO.md](#agent-definitions), [DESIGNER.md](#agent-definitions), [QA.md](#agent-definitions)
- Agent examples: [MASTER_EXAMPLES.md](#agent-definitions), [CTO_EXAMPLES.md](#agent-definitions), etc.
- Reports: [reports/archive/](#reports)

### Workflows & Processes
- Development: [feature-workflow.md](#workflow-documentation)
- Git: [branching-strategy.md](#workflow-documentation)
- Automation: [docs/AUTOMATION_STRATEGY.md](#project-documentation)

### Templates & Standards
- Report templates: [agent-report-template.md](#templates)
- Task templates: [task-template.md](#templates)
- Quality standards: [docs/QUALITY_STANDARDS.md](#project-documentation)
- Content guidelines: [docs/CONTENT_GUIDELINES.md](#project-documentation)

### Configuration & Setup
- Hugo: [docs/HUGO_CONFIG.md](#project-documentation)
- Google API: [docs/GOOGLE_API_SETUP.md](#project-documentation)
- Windows: [docs/WINDOWS_SETUP.md](#project-documentation)
- Settings: [settings.local.json](#core-documentation)

### Strategy & Business
- Keywords: [docs/KEYWORD_STRATEGY.md](#project-documentation), [docs/KEYWORD_CURATION_GUIDE.md](#project-documentation)
- Monetization: [docs/MONETIZATION.md](#project-documentation)
- Content policy: [docs/CONTENT_WRITING_POLICY.md](#project-documentation)

### Technical References
- Tech stack: [docs/TECH_STACK.md](#project-documentation)
- Architecture: [docs/ARCHITECTURE_DECISIONS.md](#project-documentation)
- Design system: [docs/DESIGN_SYSTEM.md](#project-documentation)
- Python audit: [docs/PYTHON_AUDIT_2026-01-20.md](#project-documentation)
- Error handling: [docs/ERROR_HANDLING_IMPROVEMENTS.md](#project-documentation)

---

## Directory Structure

```
.claude/
├── INDEX.md                          # This file - complete navigation index
├── instructions.md                   # Quick reference for Claude
├── PROJECT_CONTEXT.md                # Project overview
├── README.md                         # .claude directory overview
├── settings.local.json               # Local settings
│
├── agents/                           # Agent definitions
│   ├── MASTER.md                     # Master agent definition
│   ├── CTO.md                        # CTO agent definition
│   ├── DESIGNER.md                   # Designer agent definition
│   ├── QA.md                         # QA agent definition
│   ├── MASTER_EXAMPLES.md            # Master agent examples
│   ├── CTO_EXAMPLES.md               # CTO agent examples
│   ├── DESIGNER_EXAMPLES.md          # Designer agent examples
│   └── QA_EXAMPLES.md                # QA agent examples
│
├── workflows/                        # Development workflows
│   ├── feature-workflow.md           # Feature development process
│   └── branching-strategy.md         # Git branching strategy
│
├── templates/                        # Document templates
│   ├── agent-report-template.md      # Agent work report template
│   └── task-template.md              # Task creation template
│
├── reports/                          # Agent work reports
│   ├── active/                       # Current work reports (empty)
│   └── archive/                      # Completed work reports
│       └── 2026-01/                  # January 2026 reports
│           ├── cto-domain-investigation-2026-01-20.md
│           └── workflow-failure-analysis-2026-01-20.md
│
└── tasks/                            # Task management
    ├── README.md                     # Task system documentation
    ├── active/                       # Current tasks
    │   └── TASK_POST_INCIDENT_2026-01-20.md
    └── archive/                      # Completed tasks
```

---

## Usage Tips

### For Claude Agents
1. Start with [instructions.md](instructions.md) to understand work principles
2. Check [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for project structure
3. Use appropriate agent definition ([MASTER.md](#agent-definitions), [CTO.md](#agent-definitions), etc.)
4. Follow [feature-workflow.md](workflows/feature-workflow.md) for development
5. Create reports using [agent-report-template.md](templates/agent-report-template.md)

### For Finding Information
- Use "Search by Category" section above to find relevant docs quickly
- Check agent examples for practical implementation patterns
- Review archived reports for similar past work
- Reference workflow docs for process questions

### For New Features
1. Create task in `.claude/tasks/active/` using [task-template.md](templates/task-template.md)
2. Follow [feature-workflow.md](workflows/feature-workflow.md)
3. Create report using [agent-report-template.md](templates/agent-report-template.md)
4. Archive task and report after completion

---

**Maintained by**: Master Agent
**Version**: 1.0
**File Count**: 40+ documentation files indexed
