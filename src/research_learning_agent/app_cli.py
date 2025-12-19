import sys
import logging
from rich.console import Console
from rich.panel import Panel

from .schemas import UserQuery
from .simple_agent import SimpleAgent
from .storage import ProfileStore
from .user_profile import onboard_user
from .intent_classifier import IntentClassifier


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

    intent_classifier = IntentClassifier()
    agent = SimpleAgent()
    
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
            intent = intent_classifier.classify(question, profile)
            console.print(f"[dim]DEBUG Intent: {intent.intent} ({intent.confidence})[/dim]")
            if (
                intent.should_ask_clarifying_question 
                and getattr(intent, "clarifying_question", None)
            ):
                extra = console.input(f"{intent.clarifying_question}\n")
                question = question + "\n\nAdditional context: " + extra

            query = UserQuery(question=question)
            console.print("\n[bold yellow]Thinking...[/bold yellow]\n")

            answer = agent.answer(query, profile=profile, intent=intent)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            continue

        console.print(Panel.fit(answer.explanation, title="Explanation"))

        if answer.bullet_summary:
            console.print("\n[bold]Key Takeaways:[/bold]")
            for i, bullet in enumerate(answer.bullet_summary, start=1):
                console.print(f"  {i}. {bullet}")
        
        console.print("\n")


if __name__ == "__main__":
    main()