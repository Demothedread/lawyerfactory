import asyncio
from .database import Database
from .bots.research_bot import ResearchBot
from .bots.legal_editor import LegalEditorBot
from .bots.writer_bot import WriterBot
from .bots.step_planner_bot import StepPlannerBot
from lawyerfactory.ai_vector import VectorStore


class Maestro:
    """Directs output between bots and tracks asynchronous operations."""

    def __init__(self) -> None:
        self.db = Database()
        self.vector_store = VectorStore()
        self.planner_bot = StepPlannerBot()
        self.research_bot = ResearchBot()
        self.editor_bot = LegalEditorBot()
        self.writer_bot = WriterBot()

    async def research_and_write(self, topic: str) -> str:
        plan = await self.planner_bot.process(topic)
        research = await self.research_bot.process(topic)
        self.db.add(research)
        self.vector_store.add(research)
        retrieved = self.vector_store.search(topic)
        feedback = await self.editor_bot.process("\n".join(retrieved))
        article = await self.writer_bot.process(research)
        return f"{plan}\n{article}\n{feedback}"


async def demo():
    maestro = Maestro()
    output = await maestro.research_and_write("contract law")
    print(output)

if __name__ == "__main__":
    asyncio.run(demo())
