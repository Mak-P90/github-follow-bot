"""AWS SQS adapter with deterministic retry and DLQ routing."""

from __future__ import annotations

import json
from typing import Any

from .base import QueueJob

try:
    import boto3
except Exception:  # pragma: no cover - optional dependency in local/dev
    boto3 = None


class SQSFollowQueueAdapter:
    def __init__(
        self,
        queue_url: str,
        dlq_url: str,
        region_name: str = "us-east-1",
        max_attempts: int = 3,
        visibility_timeout_seconds: int = 120,
    ) -> None:
        if boto3 is None:
            raise RuntimeError("boto3 dependency is required for SQS adapter")
        self.queue_url = queue_url
        self.dlq_url = dlq_url
        self.region_name = region_name
        self.max_attempts = max_attempts
        self.visibility_timeout_seconds = visibility_timeout_seconds

    def _client(self):
        return boto3.client("sqs", region_name=self.region_name)

    def ensure_topology(self) -> None:
        # Fail-fast validation for queue URLs by querying attributes.
        client = self._client()
        client.get_queue_attributes(QueueUrl=self.queue_url, AttributeNames=["QueueArn"])
        client.get_queue_attributes(QueueUrl=self.dlq_url, AttributeNames=["QueueArn"])

    def publish(self, job: QueueJob) -> None:
        client = self._client()
        payload = {"run_id": job.run_id, "github_login": job.github_login, "attempts": int(job.attempts)}
        client.send_message(QueueUrl=self.queue_url, MessageBody=json.dumps(payload), MessageAttributes={})

    def consume_once(self) -> tuple[QueueJob | None, dict[str, Any] | None]:
        client = self._client()
        resp = client.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=1,
            VisibilityTimeout=self.visibility_timeout_seconds,
            WaitTimeSeconds=1,
            MessageAttributeNames=["All"],
        )
        messages = resp.get("Messages", [])
        if not messages:
            return None, None

        msg = messages[0]
        payload = json.loads(msg["Body"])
        attempts = int(payload.get("attempts", 0))
        job = QueueJob(run_id=int(payload["run_id"]), github_login=str(payload["github_login"]), attempts=attempts)
        meta = {
            "receipt_handle": msg["ReceiptHandle"],
            "attempts": attempts,
            "visibility_timeout_seconds": self.visibility_timeout_seconds,
        }
        return job, meta

    def ack(self, lease_meta: dict[str, Any] | None) -> None:
        client = self._client()
        receipt_handle = (lease_meta or {}).get("receipt_handle")
        if not receipt_handle:
            return
        client.delete_message(QueueUrl=self.queue_url, ReceiptHandle=str(receipt_handle))

    def retry(self, job: QueueJob, lease_meta: dict[str, Any] | None, error: str) -> str:
        self.ack(lease_meta)
        return self.requeue_or_dead_letter(job, error)

    def requeue_or_dead_letter(self, job: QueueJob, error: str) -> str:
        client = self._client()
        next_attempts = int(job.attempts) + 1
        target_url = self.queue_url if next_attempts < self.max_attempts else self.dlq_url
        payload = {
            "run_id": job.run_id,
            "github_login": job.github_login,
            "attempts": next_attempts,
            "error": error,
        }
        client.send_message(QueueUrl=target_url, MessageBody=json.dumps(payload), MessageAttributes={})
        return "requeued" if target_url == self.queue_url else "dead_letter"
