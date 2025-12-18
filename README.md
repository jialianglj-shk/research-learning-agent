# Personal Research & Learning Agent

> A modular, agentic AI system for personalized learning, research, and problem-solving.

This project explores how modern LLMs can be orchestrated into **goal-aware, step-based learning agents** that adapt to a user's intent, background, and preferred learning style.

The long-term vision is to build **general agentic AI systems** that can reason, plan, use tools, and eventually interface with real-world robotic systems.

## Project Status

**Current stage:** Day 1 -- Core Skelenton & Baseline Agent

This initial version implements a **minimal but production-quality foundation**:
* Clean project structure
* Modern Python tooling
* A working CLI-based AI assistant
* Strong typing and schemas for future expansion

Later weeks will add planning, tool use, personalization, memory, and a web UI.

## What the Week 1 Agent Does
The current agent:
* Accepts a natural-language question via CLI
* Sends the question to an OpenAI LLM
* Returns:
  * A concise explanatory answer
  * A bullet-point summary of key takeaways
* Users structured schemas so outputs are machine-readable and extensible

Example:
```markdown
> What is reinforcement learning?

Explanation:
<2–5 paragraph explanation>

Key Takeaways:
1. ...
2. ...
3. ...
```

This is the **baseline "brain"** that future agent capabilities will build on.

## Tech Stack
* **Python:** 3.13 (explicitly pinned)
* **Environment & Dependency Management:** `uv`
* **LLM Provider:** OpenAI (Chat Completions API)
* **Data Modeling:** Pydantic
* **CLI Rendering:** Rich
* **IDE:** Cursor (AI-assisted development)

## Project Structure
```
research-learning-agent/
├── pyproject.toml
├── uv.lock
├── README.md
├── .python-version
├── .env                # not committed
└── src/
    └── research_learning_agent/
        ├── __init__.py
        ├── config.py           # model & runtime configuration
        ├── schemas.py          # typed request / response models
        ├── llm_client.py       # OpenAI wrapper
        ├── simple_agent.py     # Week 1 baseline agent
        └── app_cli.py          # CLI entry point
```

The codebase is intentionally modular to support incremental agent evolution without rewrites.

## Running the Agent (Day 1)

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
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

### Run
```bash
uv run python -m research_learning_agent.app_cli
```

## Why This Project Exists
This project is part of a longer-term transition toward **applied agentic AI**, with goals including:
* Multi-step reasoning and planning
* Tool use(web, documents, video, code)
* Personalization and long-term memory
* Human-AI collaboration workflows
Eventual extension toward **robotic and embodied AI system**

Day 1 focuses on correctness, structure, and clarity -- not features.

## Roadmap (High-Level)
* **Day 2:** User intent classification & profiling
* **Day 3:** Planner module (reasoning about steps)
* **Day 4:** Tool integration (web, docs, videos)
* **Day 5:** Learning modes & teaching methods
* **Day 6:** Personalization & memory
* **Day 7:** Orchestration + web UI
* **Day 8:** Evaluation, refinement, and portfolio polish

Each stage builds on the same codebase.

## Design Philosophy
* Architecture > hacks
* Clarity > cleverness
* Explicit schemas over ad-hoc strings
* Incremental agent evolution
* Treat AI as a system component, not a magic box

## Notes on AI-Assited Development
AI tools (e.g., Cursor, Claude Code, ChatGPT) are used **intentionally**:
* To accelerate biolerplate and refactoring
* While product features, architectural decisions, interfaces, and system design remain human-driven

This mirrors how morden AI teams build real systems.

## License
MIT

