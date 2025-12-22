# Personal Research & Learning Agent

> A modular, agentic AI system for personalized learning, research, and problem-solving.

This project explores how modern LLMs can be orchestrated into **goal-aware, step-based learning agents** that adapt to a user's intent, background, and preferred learning style.

The long-term vision is to build **general agentic AI systems** that can reason, plan, use tools, and eventually interface with real-world robotic systems.

## Project Status

**Current stage:** Day 3 -- Planned Execution & Clarification Loop

This initial version implements a **minimal but production-quality foundation**:
- Clean project structure
- Modern Python tooling
- A working CLI-based AI assistant
- Strong typing and schemas for future expansion
- Planning and clarification loop

Later weeks will add tool use, personalization, memory, and a web UI.

## What the Agent Does
The agent is a CLI-based AI assistant that supports **personalized learning and research**.

Current capabilities include:
- Accepts natural-language questions via CLI
- Maintains a persistent **user profile** (background, goals, level, preferences)
- Classifies **user intent** for each query:
  - Casual curiosity
  - Guided study
  - Professional research
  - Urgent troubleshooting
- Generates an explicit multi-step plan before answering (inspectable)
- Runs a clarificatino loop when needed (bounded turns), then procedds
- Falls back to best-effort answers with stated assunmptions when ambiguity remains
- Adapts explanation style and depth based on:
  - User profile
  - Classified intent
- Users structured schemas to ensure inspectable, debuggable behavior
- Returns:
  - A clear explanation
  - A concise bullet-point summary

The assistant is designed to evolve incrementally into a fully agentic system with planning, tool use, and long-term memory.

Example:
```markdown
> What is reinforcement learning?

Do you want a concise overview or detailed explanation?
> overview

Explanation:
<2–5 paragraph explanation>

Key Takeaways:
1. ...
2. ...
3. ...
```

## Tech Stack
- **Python:** 3.13 (explicitly pinned)
- **Environment & Dependency Management:** `uv`
- **LLM Provider:** OpenAI (Chat Completions API)
- **Data Modeling:** Pydantic
- **CLI Rendering:** Rich
- **IDE:** Cursor (AI-assisted development)

## High-Level Architecture

The system is designed as a modular, schema-driven agent pipeline:

- User Input
- Profile & Context
- Intent Classification
- Planner (structured plan)
- Orchestrator (clarify loop / execution control)
- Generator (final response)
- Structured Output

Each stage is explicit and inspectable, allowing the agent to evolve incrementally toward planning, tool use, and long-term personalization.

For implementation details and design rationale, see:
- [`docs/architecture.md`](docs/architecture.md)

## Running the Agent (Day 3)

### Prerequisites
- `uv` installed
- OpenAI API key

### Setup
```bash
# from project root
uv python pin 3.13
uv sync
```
Create a `.env` file:
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

### Run
```bash
uv run python -m research_learning_agent.app_cli
```
On first run, the assistant will prompt for basic profile informaiton.

Subsequent runs resue the saved profile automatically.

The agent may ask up to a few clarifying questions before producing the final answer.


## Why This Project Exists
This project is part of a longer-term transition toward **applied agentic AI**, with goals including:
- Multi-step reasoning and planning
- Tool use(web, documents, video, code)
- Personalization and long-term memory
- Human-AI collaboration workflows
Eventual extension toward **robotic and embodied AI system**

Day 1 focuses on correctness, structure, and clarity -- not features.

## Roadmap (High-Level)
- [x] **Day 1:** Core agent skelenton and CLI
- [x] **Day 2:** User intent classification & profiling
- [x] **Day 3:** Planner module (reasoning about steps)
- [ ] **Day 4:** Tool integration (web, docs, videos)
- [ ] **Day 5:** Learning modes & teaching methods
- [ ] **Day 6:** Personalization & memory
- [ ] **Day 7:** Orchestration + web UI
- [ ] **Day 8:** Evaluation, refinement, and portfolio polish

Each stage builds on the same codebase.

## Design Philosophy
- Architecture > hacks
- Clarity > cleverness
- Explicit schemas over ad-hoc strings
- Incremental agent evolution
- Treat AI as a system component, not a magic box

## Notes on AI-Assited Development
AI tools (e.g., Cursor, Claude Code, ChatGPT) are used **intentionally**:
- To accelerate biolerplate and refactoring
- While product features, architectural decisions, interfaces, and system design remain human-driven

This mirrors how morden AI teams build real systems.

## License
MIT

