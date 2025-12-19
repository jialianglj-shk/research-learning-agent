import uuid
from rich.console import Console

from .schemas import UserProfile, UserLevel, OutputPreference


console = Console()


def onboard_user() -> UserProfile:
    console.print("[bold]Let's set up your profile (one-time).[/bold]")

    background = console.input("Your background (1 sentence): ").strip()
    goals = console.input("What are you using this assistant for? ").strip()

    level_raw = console.input("Your level (beginner/intermediate/advanced): ").strip().lower()
    level = UserLevel(level_raw) if level_raw in UserLevel._value2member_map_ else UserLevel.intermediate

    pref_raw = console.input("Preferred output (concise/balanced/detailed): ").strip().lower()
    preferred_output = (
        OutputPreference(pref_raw)
        if pref_raw in OutputPreference._value2member_map_
        else OutputPreference.balanced
    )

    profile = UserProfile(
        user_id=str(uuid.uuid4()),
        background=background or "Not provided",
        goals=goals or "Not provided",
        level=level,
        preferred_output=preferred_output,
        preferred_resources=[]
    )

    return profile