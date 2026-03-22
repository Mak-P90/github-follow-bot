"""Redis Streams adapter with deterministic retry/DLQ semantics."""

from __future__ import annotations

import json
from typing import Any

from .base import QueueJob

try:
    import redis
except Exception:  # pragma: no cover - optional dependency in local/dev
    redis = None


class RedisStreamsFollowQueueAdapter:
    def __init__(
        self,
        redis_url: str,
        stream_name: str = "follow_jobs",
        dlq_stream_name: str = "follow_jobs.dead_letter",
        consumer_group: str = "follow-workers",
        consumer_name: str = "worker-1",
        max_attempts: int = 3,
        visibility_timeout_seconds: int = 120,
    ) -> None:
        if redis is None:
            raise RuntimeError("redis dependency is required for Redis Streams adapter")
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.dlq_stream_name = dlq_stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.max_attempts = max_attempts
        self.visibility_timeout_seconds = visibility_timeout_seconds

    def _client(self):
        return redis.Redis.from_url(self.redis_url, decode_responses=True)

    def ensure_topology(self) -> None:
        client = self._client()
        try:
            client.xgroup_create(self.stream_name, self.consumer_group, id="0", mkstream=True)
        except redis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise
        try:
            client.xgroup_create(self.dlq_stream_name, self.consumer_group, id="0", mkstream=True)
        except redis.ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def publish(self, job: QueueJob) -> None:
        client = self._client()
        client.xadd(
            self.stream_name,
            {
                "run_id": str(job.run_id),
                "github_login": job.github_login,
                "attempts": str(job.attempts),
            },
        )

    def consume_once(self) -> tuple[QueueJob | None, dict[str, Any] | None]:
        client = self._client()
        entries = client.xreadgroup(
            groupname=self.consumer_group,
            consumername=self.consumer_name,
            streams={self.stream_name: ">"},
            count=1,
            block=50,
        )
        if not entries:
            return None, None

        _, stream_entries = entries[0]
        message_id, payload = stream_entries[0]
        attempts = int(payload.get("attempts", "0"))
        job = QueueJob(run_id=int(payload["run_id"]), github_login=str(payload["github_login"]), attempts=attempts)
        return job, {"message_id": message_id, "attempts": attempts, "lease_timeout_seconds": self.visibility_timeout_seconds}

    def ack(self, lease_meta: dict[str, Any] | None) -> None:
        # Ack path is a no-op in the current simplified stream consumer contract.
        return None

    def retry(self, job: QueueJob, lease_meta: dict[str, Any] | None, error: str) -> str:
        return self.requeue_or_dead_letter(job, error)

    def requeue_or_dead_letter(self, job: QueueJob, error: str) -> str:
        client = self._client()
        next_attempts = int(job.attempts) + 1
        target_stream = self.stream_name if next_attempts < self.max_attempts else self.dlq_stream_name
        client.xadd(
            target_stream,
            {
                "run_id": str(job.run_id),
                "github_login": job.github_login,
                "attempts": str(next_attempts),
                "error": error,
            },
        )
        return "requeued" if target_stream == self.stream_name else "dead_letter"
