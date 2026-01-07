from __future__ import annotations

import uuid
import traceback
import streamlit as st
from typing import Callable

from research_learning_agent.orchestrator import Orchestrator
from research_learning_agent.schemas import (
    UserProfile, UserLevel, OutputPreference, ResourcePreference, UIResponseAction, UIChatHistoryItem, AgentAnswer
)
from research_learning_agent.logging_utils import get_logger

from dotenv import load_dotenv

load_dotenv()

# Constants
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
PROMPT_DEFAULT = "Ask a question..."
DEFAULT_CLARIFY_QUESTION = "I need one clarification before answering. What specifically do you mean?"
FALLBACK_ERROR_MESSAGE = "I'm sorry, I don't know how to answer that. Please try rephrasing your question."

# Logger
logger = get_logger("WebUI")


def _render_plan(plan_md: str) -> None:
    with st.expander("Plan", expanded=False):
        st.code(plan_md, language="json")


RENDERERS: dict[str, Callable[[str], None]] = {
    "st.markdown": st.markdown,
    "st.caption": st.caption,
    "_render_plan": _render_plan,
}


def _init_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "user_id" not in st.session_state:
        st.session_state.user_id = st.session_state.session_id
    if "messages" not in st.session_state:
        st.session_state.messages = []  # list[dict(role, content)]
    if "show_plan" not in st.session_state:
        st.session_state.show_plan = False
    
    # Clarification flow state
    if "pending_clarification" not in st.session_state:
        st.session_state.pending_clarification = False
    if "clarifying_question" not in st.session_state:
        st.session_state.clarifying_question = ""
    if "original_question" not in st.session_state:
        st.session_state.original_question = ""


def _sidebar_profile() -> UserProfile:
    st.sidebar.header("User Profile")

    st.sidebar.text_input("User ID", value=st.session_state.user_id, disabled=True)

    level = st.sidebar.selectbox(
        "Level",
        [UserLevel.beginner.value, UserLevel.intermediate.value, UserLevel.advanced.value], 
        index=0
    )
    background = st.sidebar.text_area("Background", value="", height=80)
    goals = st.sidebar.text_area("Goals", value="", height=60)
    preferred_output = st.sidebar.selectbox(
        "Preferred output", 
        [OutputPreference.concise.value, OutputPreference.balanced.value, OutputPreference.detailed.value], 
        index=1
    )
    preferred_resources = st.sidebar.multiselect(
        "Preferred resources", 
        [ResourcePreference.video.value, ResourcePreference.text.value, ResourcePreference.mixed.value], 
        default=[ResourcePreference.video.value, ResourcePreference.text.value]
    )

    st.sidebar.divider()
    st.session_state.show_plan = st.sidebar.checkbox("Show plan", value=st.session_state.show_plan)

    return UserProfile(
        user_id=st.session_state.user_id, 
        level=level, 
        background=background, 
        goals=goals, 
        preferred_output=preferred_output, 
        preferred_resources=preferred_resources
    )


def _append_chat_history(role: str, content: list[UIChatHistoryItem] | str) -> None:
    st.session_state.messages.append({"role": role, "content": content})


def _build_assistant_chat_history(res) -> list[UIChatHistoryItem]:
    ans = getattr(res, "answer", None)

    if ans is None:
        return []

    content = []

    # Mode indicator
    mode = getattr(res, "mode", None)
    if mode is not None:
        mode_s = mode.value if hasattr(mode, "value") else str(mode)
        content.append(UIChatHistoryItem(
            render_function_name="st.caption",
            message_md=f"Mode: **{mode_s}**"
        ))

    # Plan (if enabled)
    if st.session_state.show_plan:
        plan = getattr(res, "plan", None)
        if plan is not None:
            plan_json = plan.model_dump_json(indent=2)
            content.append(UIChatHistoryItem(
                render_function_name="_render_plan",
                message_md=f"### Plan\n```json\n{plan_json}\n```"
            ))

    # Answer
    content.append(UIChatHistoryItem(
        render_function_name="st.markdown",
        message_md=_build_assistant_answer_md(ans)
    ))

    return content


def _build_assistant_answer_md(ans: AgentAnswer) -> str:
    """
    Build complete assistant message for history in markdown format.
    
    Args:
        ans: AgentAnswer object containing the answer data
        
    Returns:
        Formatted markdown string for the assistant's answer
    """
    md_parts = []

    # Explanation
    explanation = ans.explanation
    if explanation:
        md_parts.append("### Explanation")
        md_parts.append(explanation)
        md_parts.append("---")

    # Bullets
    bullets = ans.bullet_summary
    if bullets:
        md_parts.append("### Key takeaways")
        for b in bullets:
            md_parts.append("- " + b)
        md_parts.append("---")

    # Sections
    sections = ans.sections
    if sections:
        md_parts.append("### Detailed explanation")
        for s in sections:
            md_parts.append(f"#### {s.title}")
            md_parts.append(s.content)
        md_parts.append("---")

    # Sources
    sources = ans.sources
    if sources:
        md_parts.append("### Sources")
        for s in sources:
            if s.url:
                md_parts.append(f"- [{s.title}]({s.url})")
        md_parts.append("---")

    # Follow-ups
    followups = ans.follow_up_questions
    if followups:
        md_parts.append("### Follow-ups")
        for q in followups:
            md_parts.append(f"- {q}")
        
    return "\n\n".join(md_parts)


def _render_chat(content: list[UIChatHistoryItem] | str) -> None:
    if content:
        if isinstance(content, list):
            for item in content:
                RENDERERS[item.render_function_name](item.message_md)
        else:
            st.markdown(content)


def _render_history() -> None:
    """Render all messages in chat history."""
    for i,m in enumerate(st.session_state.messages):
        with st.container(key=f"msg-{i}-{m['role']}"):
            with st.chat_message(m["role"]):
                _render_chat(m["content"])
            

def _is_need_clarification(res) -> bool:
    return res.action is UIResponseAction.clarify


def _get_clarifying_question(res) -> str:
    if _is_need_clarification(res):
        cq = getattr(res, "clarifying_question", "") or ""
        return str(cq).strip()
    return ""


def _set_clarification_state(cq: str, original_question: str | None = None) -> None:
    """Set UI state to indicate we're waiting for clarification."""
    st.session_state.pending_clarification = True
    st.session_state.clarifying_question = cq
    if original_question and not st.session_state.original_question:
        st.session_state.original_question = original_question


def _reset_clarification_state() -> None:
    """Reset clarification state after receiving an answer."""
    st.session_state.pending_clarification = False
    st.session_state.clarifying_question = ""
    st.session_state.original_question = ""
    st.session_state.prompt = PROMPT_DEFAULT


def main() -> None:
    st.set_page_config(page_title="Research Learning Agent", layout="wide")
    _init_state()

    st.title("Personal Research & Learning Agent")

    profile = _sidebar_profile()
    orch = Orchestrator()

    # Render history first - this ensures all previous messages are displayed
    _render_history()
    
    user_text = st.chat_input(PROMPT_DEFAULT)
    if not user_text:
        return

    # Handle new question while in clarification mode
    # If user asks a new question (not answering clarification), reset clarification state
    if st.session_state.pending_clarification:
        # Simple heuristic: if the user's input looks like a new question (contains "?" or starts with question words)
        # treat it as a new question, not a clarification answer
        is_new_question = (
            "?" in user_text or
            user_text.strip().lower().startswith(("what", "how", "why", "when", "where", "who", "can", "could", "should", "is", "are", "do", "does"))
        )
        if is_new_question:
            # User asked a new question, reset clarification state
            _reset_clarification_state()

    with st.chat_message(ROLE_USER):
        _render_chat(user_text)
    _append_chat_history(ROLE_USER, user_text)

    # Decide what to send to orchestrator:
    # - normal: send as-is
    # - clarification: merge original user query + clarification
    if st.session_state.pending_clarification:
        original = st.session_state.original_question
        cq = st.session_state.clarifying_question

        merged = (
            f"Original question:\n{original}\n\n"
            f"Clarifying question:\n{cq}\n\n"
            f"User clarification answer:\n{user_text}\n"
        )
        message_for_orch = merged
    else:
        message_for_orch = user_text

    # Render assistant message
    with st.chat_message(ROLE_ASSISTANT):
        try:
            with st.spinner("Thinking..."):
                # Call orchestrator
                res = orch.chat(
                    session_id=st.session_state.session_id, 
                    message=message_for_orch, 
                    profile=profile, 
                    force_final=False,  # let clarification happen naturally in UI
                )
        except Exception as e:
            # Log full traceback to console/terminal
            logger.error(f"Exception occurred while processing user request: {str(e)}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            
            error_message = f"I encountered an error while processing your request: {str(e)}. Please try again."
            st.error(error_message)
            _append_chat_history(ROLE_ASSISTANT, error_message)
            _reset_clarification_state()
            return
        
        # If needs clarification: show question and set UI state
        if _is_need_clarification(res):
            cq = _get_clarifying_question(res) or DEFAULT_CLARIFY_QUESTION

            # Store state so next user input is treated as clarification answer
            _set_clarification_state(cq, original_question=user_text)

            assistant_text = cq
            _render_chat(cq)

        # Otherwise: final/normal answer path
        else:
            _reset_clarification_state()
            ans = getattr(res, "answer", None)
            if ans is None:
                # Defensive fallback: if orchestrator returns no answer and no clarify action
                assistant_text = FALLBACK_ERROR_MESSAGE
                _render_chat(FALLBACK_ERROR_MESSAGE)           
            
            else:
                assistant_text = _build_assistant_chat_history(res)
                _render_chat(assistant_text)      
    
    _append_chat_history(ROLE_ASSISTANT, assistant_text)


if __name__ == "__main__":
    main()
