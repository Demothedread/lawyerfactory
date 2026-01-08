import asyncio
from pathlib import Path
from typing import Any

from .database import Database
from .bots.research_bot import ResearchBot
from .bots.legal_editor import LegalEditorBot
from .bots.writer_bot import WriterBot
from .bots.step_planner_bot import StepPlannerBot
from lawyerfactory.ai_vector import VectorStore
from lawyerfactory.research_artifacts import ResearchArtifact


class Maestro:
    """Directs output between bots and tracks asynchronous operations."""

    def __init__(self) -> None:
        self.db = Database()
        self.vector_store = VectorStore(
            storage_path=Path(".vector_store/vector_store.pkl")
        )
        self.planner_bot = StepPlannerBot()
        self.research_bot = ResearchBot()
        self.editor_bot = LegalEditorBot()
        self.writer_bot = WriterBot()

    async def research_and_write(self, topic: str) -> str:
        plan = await self.planner_bot.process(topic)
        research = await self.research_bot.process(topic)
        self._store_research_artifact(research)
        retrieved = self.vector_store.search(
            topic,
            filters=research.filters.to_dict(),
        )
        feedback = await self.editor_bot.process(self._format_retrieved(retrieved))
        article = await self.writer_bot.process(research.summary)
        return f"{plan}\n{article}\n{feedback}"

    def _format_retrieved(self, retrieved: list[dict[str, Any]]) -> str:
        lines = []
        for item in retrieved:
            metadata = item.get("metadata", {})
            citation = metadata.get("citation", "Unknown citation")
            lines.append(f"{item.get('text', '')} ({citation})")
        return "\n".join(lines)

    def _store_research_artifact(self, artifact: ResearchArtifact) -> None:
        self.db.add(artifact.to_dict())
        self.vector_store.add_entries(artifact.vector_entries())


async def demo():
    maestro = Maestro()
    output = await maestro.research_and_write("contract law")
    print(output)


if __name__ == "__main__":
    asyncio.run(demo())
