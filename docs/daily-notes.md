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

## Day 4 - tool integration
**Goal:**\
Enable the agent to:
1. Dicide when external informaiton is needed
2. Select appropriate tools (web, docs, videos)
3. Execute tool calls
4. Incorporate retrieved evidence into the final answer
5. Expose sources transparently

> The planner decides _what to do_
> The orchestrator decides _when to act_
> Tools do _one thing well_

**Day 4 Definition of Done**
1. [x] Agent can call **external tools**
2. [x] Planner includes `research` steps that map to tools
3. [x] Tool cals are **explicit, logged, inspectable**
4. [x] Show sources sued (URLs/titles)
5. [x] Agent still works **whithout tools** when not needed
6. [x] Tool failures are handled gracefully, not crashing the agent
7. [x] `docs/day4-eval.md` shows evidence-based answers

## Day 5 - Learning Modes & Answer styles (pedagogy)

**Goal:**\
Agent can adapt to different answer style based on user intent and profile.

**High-level flow**
1. Orchestrator runs intent + plan (existing)
2. ToolExecutor runs tool_calls (existing)
3. **Pedagogy decides mode and builds a "generation spec"**
4. **Generator uses the spec to produce output sections required by the mode**
5. System attaches sources from ToolResults (existing)

**Day 5 Definition of Done**
1. [x] Agent selects a **Learning Mode** based on **intent + profile**
2. [x] Agent produces mode-specific structured outputs:
  - [x] **Quick Explain**: explanation + bullets + analogy + "next steps"
  - [x] **Guided Study**: 7-10 day plan with daily topics + resources
  - [x] **Deep Research**: executive summary + key concepts + reading list (papers/docs) + "open questions"
  - [x] **Fix My Problem**: diagnosis checklist + step-by-step plan + verification steps
3. [x] Mode selection and output are **deterministic & testable** (mode is not "whatever the LLM feels like")
4. [x] `docs/day5-eval.md` shows evidence-based answers

## Day 6 - Personalization & Context Adaptation

**Goal:**\
Make it feel like the agent knows the user over time

**Approach:**\
Enhance user_profile + add memory

**Features:**
- Track topics the user has studied (e.g., "RL basics", "transformers")
- Track:
  - preferred explanation style (examples vs formulas)
  - preferred resource types (videos vs text)
- Use this context in prompts:
  - "User has already studied X and prefers examples and diagrams. Avoid repeating basics."

**Behavior examples:**
- If user previously studied "neural networks basics," and now asks "What is backprop?", agent:
  - Skips super-basic "what is neuron" explanation
  - Goes a bit deeper
- Suggests follow-up topics:
  - "Last time you studied RL. Want to connect this new topic to RL?"

**End of Day 6:"
- Have a **persistent, evolving personal tutor**, not just a one-off answer bot.

**Day 6 - Definition of Done**
1. [ ] Persistent **user memory** implemented (topics, history, preferences)
2. [ ] Memory stored locally and **survivces multiple runs**
3. [ ] Orchestrator:
  - loads memory at start
  - injects memory context into generator
  - updates and saves memory after final answer
4. [ ] Generator output is **memory-aware**:
  - avoids repeating basics for known topics
  - adpats tone/style using stored preferences
5. [ ] User preferences inferred deterministically (examples vs formulas, video vs text, concise vs detailed)
6. [ ] Context-aware **follow-up suggestions** generated when applicable
7. [ ] Unit tests added for(memory store, memory update logic, preference inference)
8. [ ] Integration test confirm:
 - memory passed through orchestrator -> generator
 - memory updated after interaction
9. [ ] all existing tests pass
10. [ ] Docs updated: `architectured.md`, `README.md`, `day6_eval.md`