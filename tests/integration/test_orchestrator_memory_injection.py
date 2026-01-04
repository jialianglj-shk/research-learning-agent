from __future__ import annotations

import json
import copy
from pathlib import Path

import pytest

from research_learning_agent.orchestrator import Orchestrator
from research_learning_agent.memory import MemoryManager
from research_learning_agent.stores.memory_store import MemoryStore
from research_learning_agent.schemas import (
    AgentAnswer,
    IntentResult,
    LearningMode,
    Plan,
    PlanStep,
    StepType,
    ToolResult,
    UserMemory,
    UserProfile,
    UserQuery,
    GenerationSpec,
    UserLevel,
)


# ------------------------------
# Fakes / Captures
# ------------------------------

class FakeIntentClassifier:
    def classify(self, query: str, profile: UserProfile) -> IntentResult:
        # No clarifying in this test
        return IntentResult(
            intent="guided_study",
            confidence=0.9,
            rationale="definition question",
            suggested_output="balanced",
            should_ask_clarifying_question=False,
            clarifying_question=None,
        )


class FakePlanner:
    def create_plan(self, question: str, profile: UserProfile, intent: IntentResult) -> Plan:
        # Minimal plan; Orchestrator should proceed to generator
        return Plan(
            goal=f"Learn: {question}",
            intent=intent.intent,
            steps=[
                PlanStep(step_id="s1", type=StepType.finalize, description="finalize"),
            ]
        )


class FakeToolExecutor:
    def execute_step(self, step: PlanStep) -> list[ToolResult]:
        # No tools needed for this memory injeciton test
        return []


class FakePedagogy:
    def choose_mode(self, intent: IntentResult, profile: UserProfile) -> LearningMode:
        return LearningMode.quick_explain

    def build_spec(self, mode: LearningMode, profile: UserProfile) -> GenerationSpec:
        return GenerationSpec(
            mode=mode,
            required_sections=[],
            style_notes="",
        )


class CaptureGenerator:
    """Capture what orchestreator passes into generator."""
    def __init__(self) -> None:
        self.last_memory: UserMemory | None = None
    
    def generate(self, *args, **kwargs) -> AgentAnswer:
        # Capture memory passed by orchestrator
        if "memory" in kwargs and kwargs["memory"] is not None:
            self.last_memory = copy.deepcopy(kwargs["memory"])

        # Return minimal valid AgentAnswer
        mode = None
        if "spec" in kwargs and kwargs["spec"] is not None and hasattr(kwargs["spec"], "mode"):
            mode = kwargs["spec"].mode
        else:
            mode = LearningMode.quick_explain

        return AgentAnswer(
            explanation="x",
            bullet_summary=["b1", "b2"],
            model_name=None,
            sections=[],
            mode=mode,
            sources=[],
        )


# ------------------------------
# Helpers
# ------------------------------    

def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ------------------------------
# Test
# ------------------------------    

def test_orchestrator_memory_injection_two_runs(tmp_path: Path) -> None:
    """
    First run:
      - memory empty -> generator receives an empty memory object
      - memory saved to disk
    
    Second run:
      - memory pre-seeded with topic 'RL basics'
      - generator receives memory containing 'RL basiscs' and 'avoid repeating basics'
      - memory updated/saved after run
    """
    # Use a tmp memory store so test is isolated
    mem_path = tmp_path / "test_memory.json"
    store = MemoryStore(mem_path)
    mgr = MemoryManager(store)

    orch = Orchestrator()

    # Inject fakes
    orch.intent = FakeIntentClassifier()
    orch.planner = FakePlanner()
    orch.tools = FakeToolExecutor()
    orch.pedagogy = FakePedagogy()
    cap_gen = CaptureGenerator()
    orch.generator = cap_gen
    orch.memory_store = store
    orch.memory = mgr

    profile = UserProfile(user_id="default", level=UserLevel.beginner, background="", goals="", preferred_output="balanced")

    # ----------------------
    # Run 1: empty memory
    # ----------------------
    q1 = UserQuery(question="What is reinforcement learning?")
    res1 = orch.run(q1, profile, force_final=True, user_id="default")

    #  Capture memory
    assert cap_gen.last_memory is not None
    assert cap_gen.last_memory.topics == []

    # Memory should be saved after run 1
    assert mem_path.exists()
    saved1 = _read_json(mem_path)
    assert "topics" in saved1
    assert "history" in saved1
    # Should have at least 1 history item after run 1
    assert len(saved1["history"]) >= 1

    # ----------------------
    # Seed memory with a known topic for run 2
    # ----------------------
    mem = mgr.load("default")
    # Ensure topic exists in memory before second run
    if "RL basics" in mem.topics:
        pass
    else:
        mem.topics.append("RL basics")
    mem.last_topic = "RL basics"
    mgr.save(mem)

    # ----------------------
    # Run 2: memory has topic 'RL basiscs'
    # ----------------------
    cap_gen.last_memory = None

    q2 = UserQuery(question="What is backprop?")
    res2 = orch.run(q2, profile, force_final=True, user_id="default")

    assert cap_gen.last_memory is not None
    assert "RL basics" in cap_gen.last_memory.topics

    # Memory should be updated/saved after run 2
    saved2 = _read_json(mem_path)
    assert len(saved2["history"]) > len(saved1["history"]) # grew
    # topics should still include 'RL basics'
    assert any(t.lower() == "rl basics" for t in saved2.get("topics", []))



