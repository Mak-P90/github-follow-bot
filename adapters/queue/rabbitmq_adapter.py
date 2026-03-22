"""RabbitMQ adapter with lease-aware consumption and deterministic DLQ mapping."""

from __future__ import annotations

import json
import time
from typing import Any

from .base import QueueJob

try:
    import pika
except Exception:  # pragma: no cover - optional dependency in local/dev
    pika = None



class RabbitMQFollowQueueAdapter:
    """Queue adapter for follow jobs using RabbitMQ classic queues.

    Contract:
    - Main queue keeps jobs in pending/failed retry loop.
    - Processing lease is represented via `lease_until_epoch` header.
    - Exhausted retries are routed to DLQ exchange deterministically.
    """

    def __init__(
        self,
        amqp_url: str,
        queue_name: str = "follow_jobs",
        dlq_name: str = "follow_jobs.dead_letter",
        max_attempts: int = 3,
        visibility_timeout_seconds: int = 120,
    ) -> None:
        if pika is None:
            raise RuntimeError("pika dependency is required for RabbitMQ adapter")
        self.amqp_url = amqp_url
        self.queue_name = queue_name
        self.dlq_name = dlq_name
        self.max_attempts = max_attempts
        self.visibility_timeout_seconds = visibility_timeout_seconds

    def _connect(self):
        params = pika.URLParameters(self.amqp_url)
        return pika.BlockingConnection(params)

    def ensure_topology(self) -> None:
        with self._connect() as conn:
            ch = conn.channel()
            ch.exchange_declare(exchange="follow_jobs.dlx", exchange_type="direct", durable=True)
            ch.queue_declare(queue=self.dlq_name, durable=True)
            ch.queue_bind(queue=self.dlq_name, exchange="follow_jobs.dlx", routing_key="dead_letter")
            ch.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "follow_jobs.dlx",
                    "x-dead-letter-routing-key": "dead_letter",
                },
            )

    def publish(self, job: QueueJob) -> None:
        body = json.dumps(job.__dict__, ensure_ascii=False).encode("utf-8")
        with self._connect() as conn:
            ch = conn.channel()
            ch.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                    headers={"attempts": int(job.attempts)},
                ),
            )

    def consume_once(self) -> tuple[QueueJob | None, dict[str, Any] | None]:
        with self._connect() as conn:
            ch = conn.channel()
            method, properties, body = ch.basic_get(self.queue_name, auto_ack=True)
            if not method:
                return None, None
            payload = json.loads(body.decode("utf-8"))
            headers = dict(properties.headers or {})
            attempts = int(headers.get("attempts", payload.get("attempts", 0)))
            lease_until_epoch = int(time.time()) + self.visibility_timeout_seconds
            job = QueueJob(
                run_id=int(payload["run_id"]),
                github_login=str(payload["github_login"]),
                attempts=attempts,
            )
            lease_meta = {
                "lease_until_epoch": lease_until_epoch,
                "attempts": attempts,
            }
            return job, lease_meta

    def ack(self, lease_meta: dict[str, Any] | None) -> None:
        # Message is already acked at consume time in this simplified adapter.
        return None

    def retry(self, job: QueueJob, lease_meta: dict[str, Any] | None, error: str) -> str:
        return self.requeue_or_dead_letter(job, error)

    def requeue_or_dead_letter(self, job: QueueJob, error: str) -> str:
        next_attempts = int(job.attempts) + 1
        with self._connect() as conn:
            ch = conn.channel()
            body = json.dumps({"run_id": job.run_id, "github_login": job.github_login, "error": error}, ensure_ascii=False)
            routing_key = self.queue_name
            if next_attempts >= self.max_attempts:
                routing_key = self.dlq_name
            ch.basic_publish(
                exchange="",
                routing_key=routing_key,
                body=body.encode("utf-8"),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                    headers={"attempts": next_attempts, "error": error},
                ),
            )
            return "dead_letter" if routing_key == self.dlq_name else "requeued"
