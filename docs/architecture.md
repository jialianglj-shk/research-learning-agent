# Architecture Overview

This project is designed as a **modular agentic AI system** that evolves incrementally.

## Day 2 Architecture (Current)

User (CLI)\
↓\
Profile Loader / Onboarding\
↓\
Intent Classifier (LLM-based)\
↓\
SimpleAgent (adaptive prompting)\
↓\
LLMClient (OpenAI)\
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

- **SimpleAgent**
  - Adapts prompts based on profile + intent
  - Produces consistent, structured outputs

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



