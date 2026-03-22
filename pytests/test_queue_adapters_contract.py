from adapters.queue import QueueJob
from adapters.queue.rabbitmq_adapter import RabbitMQFollowQueueAdapter
from adapters.queue.redis_streams_adapter import RedisStreamsFollowQueueAdapter
from adapters.queue.sqs_adapter import SQSFollowQueueAdapter
import adapters.queue.sqs_adapter as sqs_module


def test_queue_job_defaults_attempts_to_zero():
    job = QueueJob(run_id=123, github_login="octocat")
    assert job.attempts == 0


def test_rabbitmq_adapter_requires_optional_dependency():
    try:
        RabbitMQFollowQueueAdapter(amqp_url="amqp://guest:guest@localhost:5672/")
    except RuntimeError as exc:
        assert "pika dependency is required" in str(exc)


def test_redis_adapter_requires_optional_dependency():
    try:
        RedisStreamsFollowQueueAdapter(redis_url="redis://localhost:6379/0")
    except RuntimeError as exc:
        assert "redis dependency is required" in str(exc)


def test_sqs_adapter_requires_optional_dependency():
    try:
        SQSFollowQueueAdapter(
            queue_url="https://sqs.us-east-1.amazonaws.com/123/follow-jobs",
            dlq_url="https://sqs.us-east-1.amazonaws.com/123/follow-jobs-dlq",
        )
    except RuntimeError as exc:
        assert "boto3 dependency is required" in str(exc)


class _FakeSQSClient:
    def __init__(self, queue_url: str, dlq_url: str):
        self.queue_url = queue_url
        self.dlq_url = dlq_url
        self._now = 0
        self._messages: dict[str, list[dict]] = {queue_url: [], dlq_url: []}
        self._inflight: dict[str, tuple[str, dict, int]] = {}
        self._receipt_seq = 0

    def advance_time(self, seconds: int) -> None:
        self._now += seconds

    def _restore_expired_leases(self) -> None:
        expired: list[str] = []
        for receipt_handle, (queue_url, message, visible_at) in self._inflight.items():
            if self._now >= visible_at:
                self._messages[queue_url].append(message)
                expired.append(receipt_handle)
        for receipt_handle in expired:
            self._inflight.pop(receipt_handle, None)

    def get_queue_attributes(self, QueueUrl, AttributeNames):
        assert QueueUrl in {self.queue_url, self.dlq_url}
        assert "QueueArn" in AttributeNames
        return {"Attributes": {"QueueArn": f"arn:aws:sqs:::{QueueUrl}"}}

    def send_message(self, QueueUrl, MessageBody, MessageAttributes):
        self._messages[QueueUrl].append({"Body": MessageBody, "MessageAttributes": MessageAttributes})
        return {"MessageId": f"mid-{len(self._messages[QueueUrl])}"}

    def receive_message(self, QueueUrl, MaxNumberOfMessages, VisibilityTimeout, WaitTimeSeconds, MessageAttributeNames):
        self._restore_expired_leases()
        assert MaxNumberOfMessages == 1
        assert WaitTimeSeconds == 1
        assert MessageAttributeNames == ["All"]
        if not self._messages[QueueUrl]:
            return {"Messages": []}
        message = self._messages[QueueUrl].pop(0)
        self._receipt_seq += 1
        receipt_handle = f"rh-{self._receipt_seq}"
        self._inflight[receipt_handle] = (QueueUrl, message, self._now + VisibilityTimeout)
        return {"Messages": [{"Body": message["Body"], "ReceiptHandle": receipt_handle}]}

    def delete_message(self, QueueUrl, ReceiptHandle):
        queue_url, _message, _visible_at = self._inflight.get(ReceiptHandle, (None, None, None))
        if queue_url == QueueUrl:
            self._inflight.pop(ReceiptHandle, None)


def test_sqs_retry_exhaustion_routes_job_to_dead_letter(monkeypatch):
    queue_url = "https://sqs.us-east-1.amazonaws.com/123/follow-jobs"
    dlq_url = "https://sqs.us-east-1.amazonaws.com/123/follow-jobs-dlq"
    fake_client = _FakeSQSClient(queue_url=queue_url, dlq_url=dlq_url)

    class _FakeBoto3:
        @staticmethod
        def client(_service, region_name):
            assert region_name == "us-east-1"
            return fake_client

    monkeypatch.setattr(sqs_module, "boto3", _FakeBoto3)

    adapter = SQSFollowQueueAdapter(queue_url=queue_url, dlq_url=dlq_url, max_attempts=3, visibility_timeout_seconds=5)
    adapter.publish(QueueJob(run_id=41, github_login="octocat", attempts=2))

    consumed, lease_meta = adapter.consume_once()
    assert consumed is not None
    assert consumed.attempts == 2

    disposition = adapter.retry(consumed, lease_meta, "server_error")
    assert disposition == "dead_letter"

    dlq_job, _ = adapter.consume_once()
    assert dlq_job is None

    dlq_entry = fake_client._messages[dlq_url][0]
    assert '"attempts": 3' in dlq_entry["Body"]
    assert '"error": "server_error"' in dlq_entry["Body"]


def test_sqs_worker_crash_recovers_job_after_visibility_timeout(monkeypatch):
    queue_url = "https://sqs.us-east-1.amazonaws.com/123/follow-jobs"
    dlq_url = "https://sqs.us-east-1.amazonaws.com/123/follow-jobs-dlq"
    fake_client = _FakeSQSClient(queue_url=queue_url, dlq_url=dlq_url)

    class _FakeBoto3:
        @staticmethod
        def client(_service, region_name):
            assert region_name == "us-east-1"
            return fake_client

    monkeypatch.setattr(sqs_module, "boto3", _FakeBoto3)

    adapter = SQSFollowQueueAdapter(queue_url=queue_url, dlq_url=dlq_url, max_attempts=3, visibility_timeout_seconds=5)
    adapter.publish(QueueJob(run_id=77, github_login="alice", attempts=0))

    leased_job, _lease_meta = adapter.consume_once()
    assert leased_job is not None
    assert leased_job.github_login == "alice"

    nothing, _ = adapter.consume_once()
    assert nothing is None

    fake_client.advance_time(6)
    recovered_job, recovered_lease_meta = adapter.consume_once()
    assert recovered_job is not None
    assert recovered_job.run_id == 77

    adapter.ack(recovered_lease_meta)
    none_after_ack, _ = adapter.consume_once()
    assert none_after_ack is None
