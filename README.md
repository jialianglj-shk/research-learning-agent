# Personal Research & Learning Agent

> A modular, agentic AI tool for personalized learning, research, and problem-solving.

This project explores how modern LLMs can be orchestrated into **goal-aware, step-based learning agents** that adapt to a user’s **intent**, **background**, and **learning preferences**.


## Project Status

**Current version:** `v0.2.0`\
**Milestone:** Product MVP — Orchestration + Tools + Memory + Web UI

This version delivers a **production-quality foundation** with:

* Clean, modular project structure
* Explicit orchestration and planning pipeline
* Tool-backed research with deterministic citations
* Learning modes and adaptive answer styles
* Lightweight, persistent user memory
* CLI and Web UI interfaces
* Workflow export for demos and evaluation


## Screenshots / Demo

> **Coming soon**\
> (Will add 1–2 screenshots or a short GIF of the Web UI)


## What the Agent Does

The agent is an AI assistant for **personalized learning and research**, designed as an explicit, inspectable system rather than a single prompt.

### Core capabilities

* Accepts natural-language questions via **CLI** or **Web UI**
* Maintains a persistent **user profile**:
  * background
  * goals
  * level
  * preferences
* Classifies **user intent** per query:
  * Casual curiosity
  * Guided study
  * Professional research
  * Urgent troubleshooting
* **Two-stage intent system**:
  * Heuristic-first classification (fast, stable)
  * LLM fallback only when uncertain (avoids mode collapse)
* Runs a **bounded clarification loop** when needed:
  * Clarifies *why* the user is asking
  * Not about formatting preferences
  * Falls back to best-effort answers with stated assumptions
* Generates an explicit **multi-step plan** before answering (inspectable)
* Plans research steps with structured tool calls:
  * web search
  * documentation search
  * video search
* Executes tools with retries and graceful failure handling
* Grounds answers in retrieved evidence
* Attaches **sources deterministically from tool results**
  * No LLM-generated citations
* Intent-driven **Learning Modes**:
  * Quick Explain
  * Guided Study
  * Deep Research
  * Fix My Problem
* Returns structured output:
  * Clear explanation
  * Bullet-point summary
  * Mode-specific sections
  * Sources
  * Follow-up suggestions

### Example interaction

```markdown
> What is reinforcement learning?

Do you want a high-level overview or are you studying this for work?

> Just an overview.

### Explanation
<2–5 paragraph explanation>

### Key takeaways
- ...
- ...

### Detailed explanation
<section 1>
<section 2>

### Sources
- ...
- ...
```


## Personalization & Memory

The assistant maintains **lightweight, persistent user memory** to improve responses over time.

Key behaviors:
* **Recent topic memory** — tracks what the user has already studied
* **Preference adaptation** — infers and respects:
  * examples vs formulas
  * video vs text resources
  * concise vs detailed explanations
* **Avoids repeating basics** for previously covered topics
* **Context-aware follow-up suggestions** that connect new topics to prior learning

Memory is:
* deterministic
* compact
* fully testable
* injected into prompts only when it adds signal

The LLM never directly controls memory state.


## High-Level Architecture

The system is designed as a **schema-driven, modular agent pipeline**:

* User Input
* Profile & Memory
* Intent Classification
* Pedagogy (mode selection)
* Planner (structured plan)
* Orchestrator (clarification & execution control)
* Tool Executor
* Generator (memory-aware)
* Structured Output
* Memory Update

Each stage is explicit and inspectable, enabling incremental evolution toward more advanced agentic behavior.

For design rationale and diagrams, see:
[`docs/architecture.md`](docs/architecture.md)


## Intent Classification (Query-first, Two-stage)

* Stage 1: rule-based signals (fast, stable)
* Stage 2: LLM fallback only when uncertainty remains
* Confidence is calibrated (not raw LLM confidence)
* Clarifying questions disambiguate **intent**, not output format


## Tools

* **Web search**: Serper (primary), DuckDuckGo Instant Answer (fallback)
* **Video search**: YouTube Data API v3
* **Docs search**: Serper with `site:` queries
  (e.g. `site:docs.python.org`, `site:docs.ros.org`)
* **Failure handling**:
  * timeouts
  * retries
  * tool failures never crash the agent


## Running the Agent (CLI)

### Prerequisites

* `uv` installed
* OpenAI API key

### Setup

```bash
# from project root
uv python pin 3.13
uv sync
```

Create a `.env` file:

```env
# required
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
SERPER_API_KEY=
YOUTUBE_API_KEY=

# optional
TOOL_TIMEOUT_SECONDS=
TOOL_MAX_RETRIES=
```

### Run (CLI)

```bash
uv run python -m research_learning_agent.app_cli
```

On first run, the assistant will prompt for basic profile information.
Subsequent runs reuse the saved profile automatically.


## Web UI

A Streamlit-based web interface exposes the agent as a **product-like experience**.

Features:
* Chat-style interface (user / assistant)
* Mode indicator (Quick Explain, Guided Study, etc.)
* Optional plan inspection (sidebar toggle)
* Source links panel
* Persistent session memory
* Clarification loop handled in UI
* Workflow export for demo and review

### Run the Web UI

```bash
uv run streamlit run app/webui.py
```


## Workflows

Chat sessions can be exported as **reproducible workflow JSON files**.

* Triggered via **“Save session”** in the UI sidebar
* Stored in `app/workflows/`
* Intended for:
  * demos
  * regression review
  * design discussion

Each workflow includes:
* session metadata
* ordered user / assistant messages
* rendered assistant output (flattened markdown)


## Roadmap (High-Level)

* [x] **Day 1:** Core agent skeleton & CLI
* [x] **Day 2:** User intent classification & profiling
* [x] **Day 3:** Planner module (reasoning about steps)
* [x] **Day 4:** Tool integration (web, docs, videos)
* [x] **Day 5:** Learning modes & teaching strategies
* [x] **Day 6:** Personalization & memory
* [x] **Day 7:** Orchestration + Web UI
* [ ] **Day 8:** Evaluation, refinement, and portfolio polish

Each stage builds on the same codebase.


## Why This Project Exists

This project supports a longer-term transition toward **applied agentic AI**, with goals including:

* Multi-step reasoning and planning
* Tool use (web, documents, video, code)
* Personalization and long-term memory
* Human–AI collaboration workflows


## Design Philosophy

* Architecture > hacks
* Clarity > cleverness
* Explicit schemas over ad-hoc strings
* Incremental agent evolution
* Treat AI as a system component, not a magic box


## Notes on AI-Assisted Development

AI tools (e.g. Cursor, Claude Code, ChatGPT) are used **intentionally**:

* To accelerate boilerplate and refactoring
* While product features, architectural decisions, interfaces, and system design remain human-driven

This mirrors how modern AI teams build real systems.


## License

MIT
