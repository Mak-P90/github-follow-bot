"""Application use-cases for follower bot workflows."""

from __future__ import annotations

from core.domain.contracts import RunExecutor


def execute_run(run_executor: RunExecutor) -> dict:
    """Execute run workflow through an explicit application-layer contract."""

    return run_executor.run()
