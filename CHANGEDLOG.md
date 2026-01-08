# Changelog

All notable changes to this project are documented here.

This project follows a pragmatic interpretation of Semantic Versioning:
- Major/minor versions reflect meaningful capability milestones
- Patch versions are used for fixes and internal refinements


## [v0.2.0] – Product MVP: Web UI + Agentic Orchestration
**Release date:** 2026-01-08

### Added
- Streamlit-based Web UI with chat interface
- End-to-end orchestrator integrating:
  - intent classification
  - pedagogy (learning mode selection)
  - planning
  - tool execution
  - generation
- Clarification loop handled in UI
- Learning modes:
  - Quick Explain
  - Guided Study
  - Deep Research
  - Fix My Problem
- Tool-backed research:
  - Web search (Serper, DuckDuckGo IA fallback)
  - Video search (YouTube Data API)
  - Documentation search via site-restricted queries
- Deterministic source attribution from tool results
- Lightweight persistent user memory:
  - recent topics
  - inferred preferences
- Context-aware follow-up suggestions
- Workflow export:
  - save full chat sessions as JSON for demos and evaluation

### Improved
- Intent classification accuracy via two-stage system:
  - rule-based signals
  - LLM fallback only when needed
- Prompt efficiency by injecting memory only when meaningful
- Error handling and logging for tool failures
- Repository structure separating core engine (`src/`) and UI (`app/`)

### Fixed
- Prevented sensitive credential leakage in HTTP logging
- Stabilized clarification loop edge cases
- Improved test coverage and regression stability

### Notes
- This version represents a **Product MVP**.
- Interfaces may evolve prior to `v1.0.0`.
- Focus is on clarity, inspectability, and system-level design over feature breadth.

---

## [v0.1.0] – Core Agent Foundation
- Initial CLI-based agent
- Modular project structure
- Schema-driven responses
- Baseline planning and generation
