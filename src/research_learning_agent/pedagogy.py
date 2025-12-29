from .schemas import LearningIntent, LearningMode, GenerationSpec, UserProfile, IntentResult


class Pedagogy:
    def choose_mode(self, intent: IntentResult, profile: UserProfile) -> LearningMode:
        """ Simple deterministic mapping, improve with more sophisticated logic later"""
        if intent.intent in {LearningIntent.urgent_troubleshooting}:
            return LearningMode.fix_my_problem
        if intent.intent in {LearningIntent.professional_research}:
            return LearningMode.deep_research
        if intent.intent in {LearningIntent.guided_study}:
            return LearningMode.guided_study
        return LearningMode.quick_explain

    def build_spec(self, mode: LearningMode, profile: UserProfile) -> GenerationSpec:
        if mode == LearningMode.quick_explain:
            return GenerationSpec(
                mode=mode,
                required_sections=["Explanation", "Analogy", "Key Points", "Next Steps"],
                style_notes="Be concise, friendly, and beginner-appropriate unless user is advanced."
            )
        if mode == LearningMode.guided_study:
            return GenerationSpec(
                mode=mode,
                required_sections=["Overview", "7-10 Day Study Plan", "Resources", "Checkpoints"],
                style_notes="Provide a daily plan with goals, key concepts, actionable instructions, and 2-4 resources per day."
            )
        if mode == LearningMode.deep_research:
            return GenerationSpec(
                mode=mode,
                required_sections=["Executive Summary", "Key Concepts", "Logical Progression Flow", "Reading List", "Open Questions"],
                style_notes="Be technical, structured, and include distinctions/assumptions."
            )
        # Fix my problem
        return GenerationSpec(
            mode=mode,
            required_sections=["Clarify Goal", "Diagnosis Checklist", "Step-by-Step Fix", "Verification"],
            style_notes="Prioritize actional steps, verify each step, include common pitfalls."
        )