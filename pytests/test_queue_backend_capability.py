from core.application.capabilities.queue_backend import verify_queue_backend, smoke_test_queue_backend


class FakeAdapter:
    def __init__(self, **_kwargs):
        pass

    def ensure_topology(self):
        return None


class FailingAdapter:
    def __init__(self, **_kwargs):
        pass

    def ensure_topology(self):
        raise RuntimeError("cannot_connect")


def test_verify_queue_backend_sqlite_ready():
    status, payload = verify_queue_backend(
        backend="sqlite",
        amqp_url="",
        queue_name="follow_jobs",
        dlq_name="follow_jobs.dead_letter",
        max_attempts=3,
        adapter_factory=FakeAdapter,
    )
    assert status == 0
    assert payload["status"] == "verified"


def test_verify_queue_backend_rabbitmq_missing_url():
    status, payload = verify_queue_backend(
        backend="rabbitmq",
        amqp_url="",
        queue_name="follow_jobs",
        dlq_name="follow_jobs.dead_letter",
        max_attempts=3,
        adapter_factory=FakeAdapter,
    )
    assert status == 2
    assert payload["error"] == "missing_amqp_url"


def test_verify_queue_backend_rabbitmq_failed_connectivity():
    status, payload = verify_queue_backend(
        backend="rabbitmq",
        amqp_url="amqp://guest:guest@localhost:5672/",
        queue_name="follow_jobs",
        dlq_name="follow_jobs.dead_letter",
        max_attempts=3,
        adapter_factory=FailingAdapter,
    )
    assert status == 2
    assert payload["error"] == "topology_check_failed"


class SmokeAdapter:
    def __init__(self, **_kwargs):
        self.job = None
        self.acked = False
        self.requeued = False

    def ensure_topology(self):
        return None

    def publish(self, job):
        self.job = job

    def consume_once(self):
        if self.requeued and self.job is not None:
            return self.job, {"lease_until_epoch": 124}
        return self.job, {"lease_until_epoch": 123}

    def retry(self, _job, _lease_meta, _error):
        self.requeued = True
        return "requeued"

    def ack(self, _lease_meta):
        self.acked = True

    def requeue_or_dead_letter(self, _job, _error):
        return "requeued"


def test_smoke_test_queue_backend_sqlite_ok():
    status, payload = smoke_test_queue_backend(
        backend="sqlite",
        amqp_url="",
        queue_name="follow_jobs",
        dlq_name="follow_jobs.dead_letter",
        max_attempts=3,
        adapter_factory=SmokeAdapter,
    )
    assert status == 0
    assert payload["status"] == "smoke_ok"


def test_smoke_test_queue_backend_rabbitmq_missing_url():
    status, payload = smoke_test_queue_backend(
        backend="rabbitmq",
        amqp_url="",
        queue_name="follow_jobs",
        dlq_name="follow_jobs.dead_letter",
        max_attempts=3,
        adapter_factory=SmokeAdapter,
    )
    assert status == 2
    assert payload["error"] == "missing_amqp_url"


def test_smoke_test_queue_backend_rabbitmq_ok():
    status, payload = smoke_test_queue_backend(
        backend="rabbitmq",
        amqp_url="amqp://guest:guest@localhost:5672/",
        queue_name="follow_jobs",
        dlq_name="follow_jobs.dead_letter",
        max_attempts=3,
        adapter_factory=SmokeAdapter,
    )
    assert status == 0
    assert payload["status"] == "smoke_ok"
    assert payload["retry_disposition"] == "requeued"
    assert payload["acknowledged"] is True
