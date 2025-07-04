import asyncio
from .database import Database
from .bots.research_bot import ResearchBot
from .bots.legal_editor import LegalEditorBot
from .bots.writer_bot import WriterBot


class Maestro:
    """Directs output between bots and tracks asynchronous operations."""

    def __init__(self) -> None:
        self.db = Database()
        self.research_bot = ResearchBot()
        self.editor_bot = LegalEditorBot()
        self.writer_bot = WriterBot()

    async def research_and_write(self, topic: str) -> str:
        research = await self.research_bot.process(topic)
        self.db.add(research)
        feedback = await self.editor_bot.process(research)
        article = await self.writer_bot.process(research)
        return f"{article}\n{feedback}"


async def demo():
    maestro = Maestro()
    output = await maestro.research_and_write("contract law")
    print(output)

if __name__ == "__main__":
    asyncio.run(demo())
