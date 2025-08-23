"""
# Script Name: compat_wrappers.py
# Description: Handles compat wrappers functionality in the LawyerFactory system.
# Relationships:
#   - Entity Type: Module
#   - Directory Group: Orchestration
#   - Group Tags: orchestration
"""
import inspect
from typing import Any, Iterable, Optional


async def _maybe_await(result: Any) -> Any:
    """Await result if it's awaitable, else return directly."""
    if inspect.isawaitable(result):
        return await result
    return result


async def _call_candidate(obj: Any, candidate_names: Iterable[str], *args, **kwargs) -> Any:
    """
    Try candidate attribute names on obj and call the first callable found.
    Handles both sync and async callables. Raises AttributeError if none found.
    """
    last_exc: Optional[Exception] = None
    for name in candidate_names:
        fn = getattr(obj, name, None)
        if callable(fn):
            try:
                result = fn(*args, **kwargs)
                return await _maybe_await(result)
            except Exception as exc:
                last_exc = exc
                continue
    raise AttributeError(f"No supported method found among: {list(candidate_names)}; last error: {last_exc}")


class AgentPoolManagerWrapper:
    """Wrapper that exposes select_best_agent/select_agent uniformly."""

    def __init__(self, impl: Any):
        self._impl = impl

    async def select_best_agent(self, task_type: str, requirements: dict) -> Any:
        candidates = (
            "select_best_agent",
            "select_agent",
            "choose_best",
            "choose_agent",
            "pick_agent",
            "get_best_agent",
            "find_agent",
        )
        return await _call_candidate(self._impl, candidates, task_type, requirements)

    async def select_agent(self, task_type: str, requirements: dict) -> Any:
        return await self.select_best_agent(task_type, requirements)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._impl, name)


class StateManagerWrapper:
    """Wrapper that normalizes save/load/list/close APIs for state managers."""

    def __init__(self, impl: Any):
        self._impl = impl

    async def save_state(self, *args, **kwargs) -> Any:
        candidates = ("save_state", "persist_state", "store_state", "save")
        return await _call_candidate(self._impl, candidates, *args, **kwargs)

    async def load_state(self, *args, **kwargs) -> Any:
        candidates = ("load_state", "get_state", "load", "restore_state")
        return await _call_candidate(self._impl, candidates, *args, **kwargs)

    async def list_all_states(self, *args, **kwargs) -> Any:
        candidates = ("list_all_states", "list_states", "all_states", "list")
        try:
            return await _call_candidate(self._impl, candidates, *args, **kwargs)
        except AttributeError:
            # Graceful fallback to an empty list if listing isn't supported
            return []

    async def close(self, *args, **kwargs) -> None:
        candidates = ("close", "shutdown", "stop", "dispose")
        try:
            await _call_candidate(self._impl, candidates, *args, **kwargs)
        except AttributeError:
            # no-op if close/shutdown not provided
            return None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._impl, name)


class CheckpointManagerWrapper:
    """Wrapper that normalizes checkpoint manager lifecycle APIs."""

    def __init__(self, impl: Any):
        self._impl = impl

    async def close(self, *args, **kwargs) -> None:
        candidates = ("close", "shutdown", "stop", "dispose")
        try:
            await _call_candidate(self._impl, candidates, *args, **kwargs)
        except AttributeError:
            return None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._impl, name)
