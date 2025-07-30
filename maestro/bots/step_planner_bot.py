"""Generate a simple step plan for a given topic."""

from ..bot_interface import Bot


class StepPlannerBot(Bot):
    """Bot that produces a numbered plan."""

    async def process(self, topic: str) -> str:
        points = [
            f"1. Research {topic}",
            f"2. Draft outline for {topic}",
            f"3. Write content about {topic}",
            "4. Edit and finalize",
        ]
        return "\n".join(points)
