# Architecture Overview

This project is designed as a **modular agentic AI system** that evolves incrementally.

## Week 1 Architecture (Current)

User (CLI)\
↓\
SimpleAgent\
↓\
LLMClient (OpenAI)\
↓\
Structured Response


### Core Components

- **app_cli.py**
  - CLI entry point
  - Handles user interaction and rendering

- **SimpleAgent**
  - Single-step reasoning agent
  - Formats prompts and parses structured output

- **LLMClient**
  - Thin abstraction over OpenAI Chat Completions
  - Centralized model configuration

- **Schemas (Pydantic)**
  - Typed request/response contracts
  - Foundation for future planning, memory, and tool use

## Design Principles

- Explicit data models over ad-hoc strings
- Clear separation of concerns
- Architecture first, features second
- Designed for incremental agent evolution

## Planned Extensions

- Intent classification & user profiling
- Multi-step planning and reasoning
- Tool use (web, documents, video)
- Long-term memory and personalization
- Web-based UI


