# Personal Research & Learning Agent Weekly Notes

## Day 1 - Core Skeleton

Goal for Day 1:
- Set up a clean Python project.
- Implement a minimal agent that:
  - Accepts a user question via CLI.
  - Sends it to an LLM.
  - Returns:
    - A short explanation.
    - A bullet-point summary.

This is the baseline "brain" that later days will extend with:
- Intent understanding
- Planning
- Tool use (web / docs / even videos)
- Personalization and memory

Day 1 "Definition of Done"
1. [x] Project created with **us** (`uv init --app iipackage research-learning-agent`)
2. [x] Python pinned to**3.13** (`us python pin 3.13`)
3. [x] Dependencies added via `uv add pydantic rich python-dotenv openai`.
4. [x] Environment variables configured in `.env` nad **not** committed.
5. [x] `research-learning-agent` (or `uv run python -m ...`) lets user:
    - types: "What is reinforcement learning?"
    - sees a clear **Explanation + Key Takeaways.**
6. [x] Code is organized under `src/research_learning_agent/` with:
    - `config.py`, `schemas.py`, `llm_client.py`, `simple_agent.py`, `app_cli.py`
7. [x] README explains what Day 1 does and mentions roadmap.

