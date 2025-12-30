# Architecture Overview

This project is designed as a **modular agentic AI system** that evolves incrementally.

## Day 3 Architecture (Planner + Orchestrator Loop)

User (CLI)\
↓\
Profile Loader / Onboarding\
↓\
Intent Classifier (LLM-based)\
↓\
Planner (Plan JSON)\
↓\
Orchestrator (control flow)\
├─ if needs clarification -> ask user enrich question -> loop back to IntentClassifier (bounded)\
└─ else continue\
↓\
ToolExecutor (only for research steps)\
↓\
Pedagogy (mode/spec)
↓\
Generator -> Answer (sectioned output + sources)\
↓\
Structured Response


### Core Components

- **app_cli.py**
  - CLI entry point
  - Handles user interaction and rendering

- **User Profile**
  - Captures background, goals, level, and preferences
  - Persisted locally for reuse across sessions

- **Intent Classifier**
  - LLM-based classification with structured JSON output
  - Determines learning intent and suggested response style

- **Planner**
  - Generates multi-step plan to answer user's query, considering user profile and additional clariying context
  - Decides what tool to use
  - Only include tool use for research steps

- **Tool Executor**
  - Execute tool calls
  - Handle tool errors gracefully

- **Pedagogy**
  - Deterministic learning intent -> learning mode mapping
  - learning mode -> generation spec mapping
  - spec-driven generation
  - parseable output format

- **Orchestrator**
  - Coordinates intent + plan -> generation pipeline
  - Decides whether clarification is requried (intent or plan)
  - Enforces bounded clarification turns
  - Supports `force_final` mode to generate a best-effort answer with explicit assumptions for better user experience and robustness
  - Returns structured results (action + debug info) for inspectability

- **LLMClient**
  - Thin abstraction over OpenAI Chat Completions
  - Centralized model configuration

- **Schemas**
  - Pydantic models enforce contracts between components
  - Enables safe evolution of agent behavior

This architecture emphasizes **clarity, inspectability, and incremental evlution**.

## Design Principles

- Explicit data models over ad-hoc strings
- Clear separation of concerns
- Architecture first, features second
- Designed for incremental agent evolution

## Tool Use

### Grounding and Sources
- Tool results are the single source of truth for citations
- Generator receives _evidence snippets_ but does not output URLs
- `Sources` in agent asnwer is built from actual tool calling results, not from LLM answer

### Failure model
- tools uses timeout + retries
- tool failure yields `ToolResult.error`
- agent contintues and answer best-effort
- CLI prints tool errors (for debug)


