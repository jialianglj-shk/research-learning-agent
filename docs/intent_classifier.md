# Intent Classification Design

## Overview

Intent classificaiton is a **core control mechanism** in the Research & Learning Agent.\
It determines **why** the user is asking a question, which directly drives:
- planning strategy
- tool usage
- learning mode selection
- whether clarification is required
This document explains the **design rational, decision logic**, and **trade-offs** behind the intent classification system.

## Goals

The intent classifier must:
1. Correctly infer **user motivation**, not answer format.
2. Avoid LLM bias toward a single intent (e.g. "guided study" collapse)
3. Be **stable, explainable, and testable**
4. Ask clrifying questions only when intent is genuinely ambiguous
5. Minimize reliance on potentially inaccurate uesr profile data

## Intent Taxonomy

The system currently supports four intents:

### 1. `casual_curiosity`

#### Definition:
Lightweight interest or exploratory understanding.

#### Typical queries:
- "What is X"
- "Explain how X works"
- "How does X works"

### 2. `guided_study`

#### Definition:
Explicit intent to **learn systematically over time**.

#### Typical queries:
- "How should I learn X?"
- "Create a 10-day study plan for X"
- "What's a good roadmap to learn X?"

### 3. `professional_research`

#### Definition:
Advanced, professional, or academic investigation.

#### Typical queries:
- "Compare X vs Y with references"
- "Survey recent approaches to do X"
- "What are the trade-offs between X and Y?"

### 4. `urgent_troubleshooting`

#### Definition:
Fixing a concrete failure, error, or mulfunction.

#### Typical queries:
- "I get X error in Y, how do I fix it?"
- "This Python script crashes with X error"
- "Why does X don't work?"

## Design Principles

### Query-First Reasoning

The **current query** is the strongest signal.
- User profile is treated as **secondary context***
- An advanced profile does **not** automatically imply professional research
- Simple queries remain casual even for expert users

### Guided Study Is Not the Default

A major observed failure mode of LLM-only systems i **over-classifying guided study**.\
This system only assigns `guided_study` when the user explicitly signals:
- desire for a plan, roadmap, schedule, or structure learning

### Clarifying Questions Disambiguate Intent, Not Format

Clarifying questions exist to determine **why the user is aksing**, not how verbose the answer should be.

**Good clarifying question:**
> "Is this out of general curiosity, or are you planning to study this topic more deeply?"
**Bad clarifying question:**
> "Do you want a detailed or high-level answer?"

## Two-Stage Classification Architecture

To balance accuracy and stability, the system users a **two-stage approach**.

### Stage 1 - Rule-based Heuristics (Fast, Stable)

This first stage uses deterministic signals extracted from the query:
- keyword patterns (e.g. "error", "copmpare", "roadmap")
- structural cues (stack traces, numbered plans)
- linguistic patterns ("what is X" -> casual curiosity)

Each intent receives a **signal score**, and an initial intent + confidence is produced.

**Benefit:**
- fast
- predictable
- debuggable
- prevents intent collapse

### Stage 2 - LLM Fallback (Contextual, Flexible)

The LLM is invoke **only when Stage 1 is uncertain**, for example:
- low confidence (<0.70)
- conflicting intent signals
- extremely short or ambiguous queries

The LLM is instructed to:
- prioritize the query over profile
- avoid format-based reasoning
- propose an intent-focused clarifying question if needed

### Conflict Resolution & Guardrails

Final intent is chosen using:
- rule-based confidence as a prior
- blended confidence (rules dominate)
- explicit guardrails, e.g.:
> "What is X" should almost never result in `guided_study` unless the user explicitly signals learning intent.

## Confidence Calibration

Confidence values are **not raw LLM outputs**.\
They are calibrated based on:
- strength of detected signals
- separation between top intent and runner-up
- known ambiguity patterns

Typical ranges:
- **0.85-0.90** -> strong, unambiguous intent
- **0.70-0.80** -> clear but not explicit
- **0.55-0.65** -> ambiguous (clarification recommended)

## Clarifying Question Pollicy

A clarifying question is asked **only if**:
- intent confidence is low
- multiple intents are plausible
- the query does not indicate urgency

Clarifying questions:
- are **single, focused**
- ask about **purpose**, not output format
- never stack multiple sub-questions

## Telemetry & Evaluation

To support iterative tuning, the system logs **intent events** (privacy-safe):
- truncated query
- predicted intent
- confidence
- whether clarification was requested
- detected signal scores

This enables:
- monitoring intent distribution
- detecting bias or drift
- prompt and heuristic refinement

No credentials or sensitive data are logged.

## Security & Privacy Considerations
- Query text is truncated in logs
- (LLM cals) No headers, tokens, or request bodies are recorded
- Clarifying questions are generated without revealing internal logic
- LLM outputs are validated before use

## Known Limitations
- Very shot queries (e.g. "RL") remain ambiguous
- Domain-specific jargon may require new heuristics
- Multilingual intent detection is not yet supported

## Future Improvements

Planned enhancements include:
- explicit user intent overrides
- per-user preference learning
- additional intent classes (e.g. "implementation help" vs troubleshooting)
- intent-aware cost control (tool usage budgets)

## Summary

This intent classification system demonstrates:
- agentic reasoning beyond rat LLM prompting
- deterministic control with probabilistic fallback
- explainable decisions
- production-grade safty and observability

It forms the foundation for **learning mode selection, planning, and personalization** across the agent.