# Learning Modes

This document defines the **learning modes** used by the Research & Learning Agent. Each mode determines **how the agent structures its output**, based on **user intent** and **background level**.

The agent selects a mode deterministically via the **Pedagogy module** -- the LLM does NOT decide the format.


## Overview
|Mode|Primary Use Case|
|:----|:---|
|Quick Explan|Fast understanding, casual learning|
|Guided Study|Structured self-study over days|
|Deep Research|Professional / academic investigation|
|Fix My Problem|Troubleshooting and task resolution|

Mode selection depends on:
- **User intent** (from intent classifier)
- **User background level** (from user profile, beginner / intermediate / advanced)
- (Future) explicit user preference overrides

## 1. Quick Explain

### Purpose
Provide a **fast, intuitive understanding** of a topic with minimal congnitive load.
### Trigger Conditions
- Intent:
  - `casual_curiosity`
  - general "what is X" questions
- User level:
  - beginner or unspecified
### Required Sections
- **Explanation**
- **Analogy**
- **Key Points**
- **Next Steps**
### Output Constraints
- Length: short (~ 3-5 paragraphs total)
- Tone: friendly, accessible, non-technical
- Avoid formulas and heavy jargon
- Prefer examples and intuition
### Resource Usage Rules
- Include **few sources** (1-3) only if useful
- Sources should be:
  - high-level overviews
  - official introductory pages
- If tools return no results, answer from general knowledge

## 2. Guided Study

### Purpose
Hep users **systematically learn a topic over time** with a clear progression.
### Trigger Conditions
- Intent:
  - `guided_study`
  - "I want to learn X" / "How should I study X"
- User level:
  - beginner -> intermediate
### Required Sections
- **Overview**
- **7-10 Day Plan**
- **Resources**
- **Checkpoints**
### Output Constraints
- Length: medium to long
- Tone: instuctional, encouraging, structured
- Must include:
  - daily or phased goals
  - increasing difficulty over time
- Avoid overwhelming depth per day
###  Resources Usage Rules
- Sources are  **required**
- Resources should be categorized:
  - videos
  - documentation
  - articales / tutorials
- Prefer:
  - official docs
  - well-known courses
- Do **not** invent reading material -- all sources come from tool results

## 3. Deep Research

## Purpose
Support **professional, academic, or advanced technical research**.
## Trigger Conditions
- Intent:
  - `professional_research'
  - "compare", "survey", "state of the art"
- User leve:
  - intermediate -> advanced
## Required Sections
- **Executive Summary**
- **Key Concepts**
- **Reading List**
- **Open Questions**
## Output Constraints
- Length: long, dense
- Tone: precise, technical, neutral
- Allowed:
  - technical terminlology
  - assumptions and trade-offs
- Must distinguish:
  - established knowledge vs open research areas
## Resource Usage Rules
- Sources are **mandatory**
- Prefer:
  - papers
  - offical technical blogs
  - authoritative documentation
- Multiple sources expected (3-8)
- Sources are attached deterministically from tool results

## 4. Fix My Problem

### Purpose
Help users **resolve a concrete problem or task** efficiently.
## Trigger Conditions
- Intent:
  - `urgent_troubleshooting`
  - "hot do I fix", "why does this fial"
- User level:
  - any
## Required Sections
- **Clarify Goal**
- **Diagnosis Checklist**
- **Step-by-step Fix**
- **Verification**
## Output Constraints
- Length: medium
- Tone: direct, pragmatic, actionale
- Emphasis on:
  - ordering steps correctly
  - common failure points
  - verification after each step
- Avoid theory unless necessary for diagnosis
## Resource Usage Rules
- Include sources **only when helpful**:
  - offical docs
  - error references
- Prefer authoritative sources over blogs
- If no tools succeed, proceed with best-effort assumptions

## Design Principles

### Deterministic Mode Selection
- Mode is chosen by the **Pedagogy module**
- The LLM is instructed to follow the selected format
- This ensures:
  - consistent outputs
  - predictable behavior
  - testable logic
### Separation of Converns
- LLM generates **content**
- System code:
  - selects mode
  - enforces structure
  - attaches sources
- LLM does **not** generate citations

## Future Extensions

Planned enhancements include:
- User-selectable mode overrides
- Quizzzes and self-assessment steps
- Spaced repetition integration
- Continously update user profile automatically based on user interactions with the agent assistant to adpat user's personal learning style