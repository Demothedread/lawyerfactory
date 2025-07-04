from dataclasses import dataclass
from enum import Enum


class Stage(Enum):
    PREPRODUCTION_PLANNING = "Preproduction Planning"
    RESEARCH_AND_DEVELOPMENT = "Research and Development"
    ORGANIZATION_DATABASE_BUILDING = "Organization / Database Building"
    FIRST_PASS = "1st Pass All Parts"
    COMBINING = "Combining"
    EDITING = "Editing"
    SECOND_PASS = "2nd Pass"
    HUMAN_FEEDBACK = "Human Feedback"
    FINAL_DRAFT = "Final Draft"


STAGE_SEQUENCE = [
    Stage.PREPRODUCTION_PLANNING,
    Stage.RESEARCH_AND_DEVELOPMENT,
    Stage.ORGANIZATION_DATABASE_BUILDING,
    Stage.FIRST_PASS,
    Stage.COMBINING,
    Stage.EDITING,
    Stage.SECOND_PASS,
    Stage.HUMAN_FEEDBACK,
    Stage.FINAL_DRAFT,

]


@dataclass
class Task:
    id: int
    title: str
    stage: Stage = Stage.PREPRODUCTION_PLANNING
    description: str = ""
    assignee: str | None = None

    def assign(self, agent: str) -> None:
        """Assign this task to an agent."""
        self.assignee = agent

    def advance(self) -> None:
        """Advance the task to the next stage."""
        current_index = STAGE_SEQUENCE.index(self.stage)
        if current_index < len(STAGE_SEQUENCE) - 1:
            self.stage = STAGE_SEQUENCE[current_index + 1]
