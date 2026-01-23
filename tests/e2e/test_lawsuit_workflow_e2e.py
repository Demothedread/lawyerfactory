"""
End-to-end tests for the lawsuit creation workflow phases and transitions.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
import sys
import types

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))

from lawyerfactory.agents.orchestration import maestro as maestro_module
from lawyerfactory.storage.core.unified_storage_api import EnhancedUnifiedStorageAPI

LAW_LAWSUIT_PHASE_SEQUENCE = [
    "phaseA01_intake",
    "phaseA02_research",
    "phaseA03_outline",
    "phaseB01_review",
    "phaseB02_drafting",
    "phaseC01_editing",
    "phaseC02_orchestration",
]


@dataclass(frozen=True)
class LawsuitPhaseExpectation:
    """Expected transition outcomes after executing a single phase."""

    phase_id: str
    expected_current_phase: str
    expected_next_phase: str | None
    is_terminal: bool


def lawsuit_build_phase_expectations() -> list[LawsuitPhaseExpectation]:
    """Build expected transition outcomes from the phase sequence."""
    expectations = []
    last_index = len(LAW_LAWSUIT_PHASE_SEQUENCE) - 1
    for idx, phase_id in enumerate(LAW_LAWSUIT_PHASE_SEQUENCE):
        expected_current = (
            LAW_LAWSUIT_PHASE_SEQUENCE[idx + 1]
            if idx < last_index
            else LAW_LAWSUIT_PHASE_SEQUENCE[-1]
        )
        expected_next = (
            LAW_LAWSUIT_PHASE_SEQUENCE[idx + 2]
            if idx < last_index - 1
            else None
        )
        expectations.append(
            LawsuitPhaseExpectation(
                phase_id=phase_id,
                expected_current_phase=expected_current,
                expected_next_phase=expected_next,
                is_terminal=idx == last_index,
            )
        )
    return expectations


LAW_LAWSUIT_PHASE_EXPECTATIONS = lawsuit_build_phase_expectations()


@dataclass(frozen=True)
class LawsuitWorkflowFixture:
    """Shared workflow fixtures for lawsuit E2E tests."""

    maestro: maestro_module.Maestro
    storage: EnhancedUnifiedStorageAPI
    storage_registry_path: Path


def lawsuit_build_case_data() -> dict[str, str]:
    """Return consistent case data for end-to-end tests."""
    return {
        "case_type": "contract_dispute",
        "content": "Plaintiff alleges breach of contract and damages from late delivery.",
        "plaintiff": "Ada Lovelace",
        "defendant": "Analytical Engines LLC",
    }


@pytest.fixture()
def lawsuit_workflow_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> LawsuitWorkflowFixture:
    """Provide a Maestro instance backed by temporary storage."""
    storage_path = tmp_path / "storage"
    storage = EnhancedUnifiedStorageAPI(storage_path=str(storage_path))
    monkeypatch.setattr(
        maestro_module,
        "get_enhanced_unified_storage_api",
        lambda: storage,
    )
    return LawsuitWorkflowFixture(
        maestro=maestro_module.Maestro(),
        storage=storage,
        storage_registry_path=storage_path / "object_registry.json",
    )


def lawsuit_run(coro):
    """Run an async coroutine in the current event loop."""
    return asyncio.run(coro)


@pytest.mark.parametrize(
    "phase_index, expectation",
    list(enumerate(LAW_LAWSUIT_PHASE_EXPECTATIONS)),
)
def test_lawsuit_phase_transition_per_phase(
    lawsuit_workflow_fixture: LawsuitWorkflowFixture,
    phase_index: int,
    expectation: LawsuitPhaseExpectation,
):
    """Validate each phase transition in isolation."""
    workflow_id = lawsuit_run(
        lawsuit_workflow_fixture.maestro.start_workflow(
            case_data=lawsuit_build_case_data()
        )
    )

    for idx in range(phase_index + 1):
        lawsuit_run(
            lawsuit_workflow_fixture.maestro.orchestrate_phase(
                workflow_id=workflow_id,
                phase_id=LAW_LAWSUIT_PHASE_EXPECTATIONS[idx].phase_id,
            )
        )

    status = lawsuit_run(
        lawsuit_workflow_fixture.maestro.get_workflow_status(workflow_id)
    )

    assert status["current_phase"] == expectation.expected_current_phase
    assert status["next_phase"] == expectation.expected_next_phase

    expected_status = "completed" if expectation.is_terminal else "active"
    assert status["status"] == expected_status

    assert expectation.phase_id in status["completed_phases"]


def test_lawsuit_workflow_end_to_end(
    lawsuit_workflow_fixture: LawsuitWorkflowFixture,
):
    """Run the entire workflow and confirm final outputs."""
    workflow_id = lawsuit_run(
        lawsuit_workflow_fixture.maestro.start_workflow(
            case_data=lawsuit_build_case_data()
        )
    )

    for expectation in LAW_LAWSUIT_PHASE_EXPECTATIONS:
        lawsuit_run(
            lawsuit_workflow_fixture.maestro.orchestrate_phase(
                workflow_id=workflow_id,
                phase_id=expectation.phase_id,
            )
        )

    summary = lawsuit_run(
        lawsuit_workflow_fixture.maestro.generate_workflow_summary(workflow_id)
    )

    assert summary["status"] == "completed"
    assert summary["total_phases_completed"] == len(LAW_LAWSUIT_PHASE_EXPECTATIONS)
    assert summary["progress_percentage"] == 100.0

    registry_path = lawsuit_workflow_fixture.storage_registry_path
    assert registry_path.exists()
    registry_contents = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry_contents) >= len(LAW_LAWSUIT_PHASE_EXPECTATIONS) + 1
