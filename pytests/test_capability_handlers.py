import json

from core.application.capabilities.follow_back import (
    handle_abort_command,
    handle_default_run_command,
    handle_resume_command,
    handle_worker_command,
)
from core.application.capabilities.fork_discovery import handle_fork_repos_command


class DummyFollowService:
    def __init__(self):
        self.calls = []

    def process_follow_queue(self, run_id: int, trace_id: str, max_jobs=None):
        self.calls.append((run_id, trace_id, max_jobs))
        return 3




class DummyTelemetry:
    def __init__(self):
        self.spans = []

    class _SpanCtx:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    def span(self, name, attributes):
        self.spans.append((name, attributes))
        return self._SpanCtx()


class DummyFollowServiceWithTelemetry(DummyFollowService):
    def __init__(self):
        super().__init__()
        self.telemetry = DummyTelemetry()

class DummyStorage:
    def __init__(self, run=None, abort_result=True):
        self.run = run
        self.abort_result = abort_result
        self.security_events = []
        self.commits = 0

    def get_run(self, run_id: int):
        return self.run

    def get_follow_job_stats(self, run_id: int):
        return {"pending": 0, "done": 3, "failed": 0, "dead_letter": 0, "run_id": run_id}

    def abort_run(self, run_id: int, reason: str):
        return self.abort_result

    def add_security_event(self, event: str, detail: str, run_id: int | None = None):
        self.security_events.append((event, detail, run_id))

    def commit(self):
        self.commits += 1


class DummyForkService:
    def __init__(self):
        self.kwargs = None

    def fork_repositories_for_user(self, **kwargs):
        self.kwargs = kwargs
        return {"ok": True, "count": 1, "target": kwargs["target_username"]}


def test_handle_worker_command_returns_payload():
    service = DummyFollowService()
    status, payload = handle_worker_command(service, run_id=12, max_jobs=5)
    assert status == 0
    assert payload["run_id"] == 12
    assert payload["processed"] == 3
    assert payload["trace_id"].startswith("trace-")


def test_handle_resume_command_requires_resumable_status():
    storage = DummyStorage(run={"status": "completed", "trace_id": "trace-fixed"})
    service = DummyFollowService()
    status, payload = handle_resume_command(storage, service, run_id=7)
    assert status == 2
    assert payload["error"] == "run_not_resumable"


def test_handle_abort_command_writes_security_event_when_aborted():
    storage = DummyStorage(run={"status": "running"}, abort_result=True)
    status, payload = handle_abort_command(storage, run_id=99, reason="operator_request")
    assert status == 0
    assert payload["aborted"] is True
    assert storage.commits == 1
    assert storage.security_events
    event, detail, run_id = storage.security_events[0]
    assert event == "run_aborted"
    assert run_id == 99
    assert json.loads(detail)["reason"] == "operator_request"


def test_handle_fork_repos_command_requires_filters():
    service = DummyForkService()
    status, payload = handle_fork_repos_command(
        service,
        target_username="octocat",
        owned=False,
        forked=False,
        include_profile_readme=False,
        fork_source=False,
        follow_fork_owners=False,
    )
    assert status == 2
    assert payload["error"] == "no_filters_selected"


def test_handle_fork_repos_command_delegates_to_service():
    service = DummyForkService()
    status, payload = handle_fork_repos_command(
        service,
        target_username="octocat",
        owned=True,
        forked=False,
        include_profile_readme=False,
        fork_source=True,
        follow_fork_owners=True,
    )
    assert status == 0
    assert payload["ok"] is True
    assert service.kwargs["target_username"] == "octocat"
    assert service.kwargs["fork_sources_for_forks"] is True
    assert service.kwargs["follow_fork_owners"] is True


def test_handle_worker_command_emits_worker_span_when_telemetry_available():
    service = DummyFollowServiceWithTelemetry()
    status, payload = handle_worker_command(service, run_id=33, max_jobs=2)
    assert status == 0
    assert payload["run_id"] == 33
    assert service.telemetry.spans
    name, attrs = service.telemetry.spans[0]
    assert name == "worker.run"
    assert attrs["run_id"] == 33
    assert attrs["capability"] == "worker"
    assert attrs["max_jobs"] == 2
    assert attrs["trace_id"].startswith("trace-")

def test_handle_default_run_command_returns_structured_auth_error():
    status, payload = handle_default_run_command(object(), run_executor=lambda _svc: (_ for _ in ()).throw(RuntimeError("failed status=401")))
    assert status == 2
    assert payload["ok"] is False
    assert payload["error"] == "github_auth_invalid"