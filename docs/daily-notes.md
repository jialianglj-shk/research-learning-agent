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

## Day 2 - Intent & User Profiling

**Goal**: Make the agent understand what kind of learning the user wants and who they are.

**Features**:
- When user first open the assistant, ask few smart questions:
  - What is your backgroup
  - What is your purpose of using this assistant (casual curiosity, guided study, serious research, urgent problem solving)?
  - What is your current level of the topic (biginner, intermediate, advanced)
  - What is your preferred answer style (concise, balanced, detailed)?
- Store user's profile in a simple JSON file
- From then on, for every qeury:
  - Run an `intent` classification
  - Ask clarifying question if needed
  - Send all information (user profile, intent, user query, clarifying question) to LLM and generate asnwer

**End of Day 2**, the agent:
- Knows why the user is asking
- Knows their level/background
- Can slightly adapt tone and depth

**Day 2 Definition of Done**
1. [x] First run prompts for profile, then sotre `data/user_profile.json`
2. [x] Subsequent runs skip onboarding and load the profile
3. [x] Every question produces and intent classification (`IntentResult`)
4. [x] They response style clearly changes between intents (you can feel it)
5. [x] Show at least 4 saved eval scenarios in `docs/day2-eval.md`
6. [x] README udpated: "Now supports intent classification and user profiling"

## Day 3 - Planner + Orchestrator Loop
**Goal**: build the "agent brain" (not tools):
1. loads user profile
2. classifies intent
3. generates a plan
4. executes the plan ("think steps")
5. generates final answer
6. print the plan (inspectable) + answer

**Features:**
- Added structured planning (Plan/StepStep schemas)
- Added orchestrator control flow with bounded clarification loop
- Added `force_final` fallback for assumption-based answers
- Observability: log raw planner/generator outputs in DEBUG mode

**Day 3 Definition of Done""
1. [x] Every query produces a `plan` (stuctured steps)
2. [x] They system run s through an **orchestrator pipeline**, not ad-hoc glue in CLI
3. [x] Ask for clarification if required but bounded to a maximum times for better UX
4. [x] Have `docs/day3-eval.md` with scenarios showing: user query, intent output, plan output, final response
5. [x] Have basic logging for "what went in/out" of planner + generator (at DEBUG)