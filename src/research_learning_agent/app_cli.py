import sys
from rich.console import Console
from rich.panel import Panel

from .schemas import UserQuery
from .simple_agent import SimpleAgent

console = Console()

def main() -> None:
    console.print(
        "[bold green]Personal Research & Learning Agent[/bold green] "
        "(Day 1 - Simple Q&A)"
    )
    console.print("Type your question, or 'quit' to exist.\n")

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
            
        query = UserQuery(question=question)
        console.print("\n[bold yellow]Thinking...[/bold yellow]\n")

        try:
            answer = agent.answer(query)
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