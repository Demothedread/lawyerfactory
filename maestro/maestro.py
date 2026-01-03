import asyncio
from typing import Any

from lawyerfactory.ai_vector import VectorStore

from .bots.legal_editor import LegalEditorBot
from .bots.research_bot import ResearchBot
from .bots.step_planner_bot import StepPlannerBot
from .bots.writer_bot import WriterBot
from .database import Database
from .job_store import JOB_STORE_STAGE_ORDER, JobStore


class Maestro:
    """Directs output between bots and tracks asynchronous operations."""

    def __init__(self, job_store: JobStore | None = None) -> None:
        self.db = Database()
        self.vector_store = VectorStore()
        self.planner_bot = StepPlannerBot()
        self.research_bot = ResearchBot()
        self.editor_bot = LegalEditorBot()
        self.writer_bot = WriterBot()
        self.job_store = job_store or JobStore()

    async def research_and_write(self, topic: str) -> str:
        plan = await self.planner_bot.process(topic)
        research = await self.research_bot.process(topic)
        self.db.add(research)
        self.vector_store.add(research)
        retrieved = self.vector_store.search(topic)
        feedback = await self.editor_bot.process("\n".join(retrieved))
        article = await self.writer_bot.process(research)
        return f"{plan}\n{article}\n{feedback}"

    async def run_pipeline(
        self,
        job_id: str,
        stage_start: str = "ocr",
        stage_end: str = "review",
        topic: str | None = None,
    ) -> dict[str, Any]:
        stage_handlers = {
            "ocr": self._maestro_stage_ocr,
            "shotlist": self._maestro_stage_shotlist,
            "research": self._maestro_stage_research,
            "drafting": self._maestro_stage_drafting,
            "review": self._maestro_stage_review,
        }
        stage_sequence = list(JOB_STORE_STAGE_ORDER)
        if stage_start not in stage_sequence or stage_end not in stage_sequence:
            raise ValueError("Unknown pipeline stage requested.")
        start_index = stage_sequence.index(stage_start)
        end_index = stage_sequence.index(stage_end)
        for stage in stage_sequence[start_index : end_index + 1]:
            await self._maestro_run_stage(
                job_id,
                stage,
                stage_handlers[stage],
                topic,
            )
        job_state = self.job_store.job_store_get_job(job_id)
        if job_state:
            final_status = "completed" if stage_end == "review" else "in_progress"
            self.job_store.job_store_update_job(
                job_id,
                final_status,
                job_state["current_stage"],
            )
        return job_state or {}

    async def _maestro_run_stage(
        self,
        job_id: str,
        stage: str,
        handler: Any,
        topic: str | None,
    ) -> None:
        job_state = self.job_store.job_store_get_job(job_id)
        if not job_state:
            return
        self.job_store.job_store_update_stage(
            job_state["job_id"],
            stage,
            "in_progress",
            None,
        )
        output = await handler(job_state, topic)
        self.job_store.job_store_update_stage(
            job_state["job_id"],
            stage,
            "completed",
            output,
        )

    async def _maestro_stage_ocr(
        self, job_state: dict[str, Any], _topic: str | None
    ) -> dict[str, Any]:
        documents = job_state["metadata"].get("documents", [])
        combined_text = "\n\n".join(
            document.get("content", "") for document in documents
        ).strip()
        return {"text": combined_text, "documents": len(documents)}

    async def _maestro_stage_shotlist(
        self, job_state: dict[str, Any], _topic: str | None
    ) -> dict[str, Any]:
        ocr_output = (
            self.job_store.job_store_stage_output(job_state["job_id"], "ocr") or {}
        )
        text = ocr_output.get("text", "")
        summary = text[:240] if text else "No intake text provided."
        return {
            "summary": summary,
            "shotlist": ["Identify parties", "Extract key facts"],
        }

    async def _maestro_stage_research(
        self, job_state: dict[str, Any], topic: str | None
    ) -> dict[str, Any]:
        shotlist_output = (
            self.job_store.job_store_stage_output(job_state["job_id"], "shotlist")
            or {}
        )
        research_topic = topic or shotlist_output.get("summary", "legal research")
        research = await self.research_bot.process(research_topic)
        self.db.add(research)
        self.vector_store.add(research)
        return {"topic": research_topic, "research": research}

    async def _maestro_stage_drafting(
        self, job_state: dict[str, Any], topic: str | None
    ) -> dict[str, Any]:
        research_output = (
            self.job_store.job_store_stage_output(job_state["job_id"], "research")
            or {}
        )
        drafting_topic = topic or research_output.get("topic", "drafting")
        draft_text = await self.writer_bot.process(
            research_output.get("research", "")
        )
        sections = [
            {
                "section_key": "draft_intro",
                "title": "Introduction",
                "content": f"Draft overview for {drafting_topic}.",
            },
            {
                "section_key": "draft_analysis",
                "title": "Analysis",
                "content": draft_text,
            },
            {
                "section_key": "draft_conclusion",
                "title": "Conclusion",
                "content": "Summary of arguments and requested relief.",
            },
        ]
        for section in sections:
            self.job_store.job_store_add_section(
                job_state["job_id"],
                section["section_key"],
                section["title"],
                section["content"],
            )
        return {
            "topic": drafting_topic,
            "draft": draft_text,
            "sections": sections,
        }

    async def _maestro_stage_review(
        self, job_state: dict[str, Any], _topic: str | None
    ) -> dict[str, Any]:
        draft_output = (
            self.job_store.job_store_stage_output(job_state["job_id"], "drafting")
            or {}
        )
        review_input = draft_output.get("draft", "")
        review_notes = await self.editor_bot.process(review_input)
        return {"review": review_notes, "export_ready": True}


async def demo():
    maestro = Maestro()
    output = await maestro.research_and_write("contract law")
    print(output)

if __name__ == "__main__":
    asyncio.run(demo())
