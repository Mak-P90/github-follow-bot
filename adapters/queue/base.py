"""Shared queue adapter contracts for distributed follow-job backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class QueueJob:
    run_id: int
    github_login: str
    attempts: int = 0


class FollowQueueAdapter(Protocol):
    def ensure_topology(self) -> None: ...

    def publish(self, job: QueueJob) -> None: ...

    def consume_once(self) -> tuple[QueueJob | None, dict[str, Any] | None]: ...

    def ack(self, lease_meta: dict[str, Any] | None) -> None: ...

    def retry(self, job: QueueJob, lease_meta: dict[str, Any] | None, error: str) -> str: ...

    def requeue_or_dead_letter(self, job: QueueJob, error: str) -> str: ...
