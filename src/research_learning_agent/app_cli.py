import sys
import logging
from typing import final
from rich.console import Console
from rich.panel import Panel

from .schemas import UserQuery, OrchestratorActionType
from .simple_agent import SimpleAgent
from .storage import ProfileStore
from .user_profile import onboard_user
from .intent_classifier import IntentClassifier
from .orchestrator import Orchestrator

from dotenv import load_dotenv

load_dotenv()

MAX_CLARIFY_TURNS = 2
console = Console()


def main() -> None:
    console.print(
        "[bold green]Personal Research & Learning Agent[/bold green] "
        "(Day 2- Intent and user profiling)"
    )

    store = ProfileStore()
    profile = store.load()
    if profile is None:
        profile = onboard_user()
        store.save(profile)

    console.print("Type your question, or 'quit' to exist.\n")

    orchestrator = Orchestrator()
    
    while True:
        try:
            question = console.input("[bold cyan]> [/bold cyan]")
            console.print(f"[dim]DEBUG got input: {question!r}[/dim]")
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye!")
            sys.exit(0)

        if not question:
            continue
        if question.lower() in {"q", "quit", "exit"}:
            console.print("Goodbye!")
            break

        try:
            original_question = question
            current_question = original_question
            answer = None
            force_final = False

            for turn in range(MAX_CLARIFY_TURNS + 1):
                result = orchestrator.run(UserQuery(question=current_question), profile, force_final=False)

                if result.action.kind == OrchestratorActionType.final:
                    # Able to generate final answer
                    answer = result.answer
                    break

                # Clarification required
                cq = result.action.clarifying_question
                extra_user_input = console.input(f"\n[bold magenta]Clarify:[/bold magenta] {cq}\n>")

                # If user provides nothing, don't loop forever 
                if not extra_user_input:
                    extra_user_input = "(No additional context provided.)"
                    force_final = True
                
                current_question = (original_question + "\n\nAdditional context from user:\n" + extra_user_input.strip())

                if force_final:
                    break

            if answer is None and (turn == MAX_CLARIFY_TURNS or force_final):
                # Clarification is still required but force final
                forced_question = (current_question + "\n\nProvide a best-effort answer using reasonable assumptions.")

                result = orchestrator.run(UserQuery(question=forced_question), profile, force_final=True)
                answer = result.answer

        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            continue

        console.print(Panel.fit(answer.explanation, title="Explanation"))

        if answer.bullet_summary:
            console.print("\n[bold]Key Takeaways:[/bold]")
            for i, bullet in enumerate(answer.bullet_summary, start=1):
                console.print(f"  {i}. {bullet}")
        
        if answer.sources:
            console.print("\n[bold]Sources:[/bold]")
            for i, src in enumerate(answer.sources, start=1):
                console.print(f"  {i}. {src.title} | {src.url}")
        
        for tr in result.tool_results:
            if tr.error:
                console.print(f"[dim]Tool Error {tr.tool} failed: {tr.error.error_type} ({tr.query})[/dim]")
    
        console.print("\n")


if __name__ == "__main__":
    main()