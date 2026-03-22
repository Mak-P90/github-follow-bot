from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

from core.application.telemetry_attrs import build_telemetry_attributes


@contextmanager
def _null_span():
    yield None


def _telemetry_span(service: Any, name: str, attributes: dict[str, Any]):
    telemetry = getattr(service, "telemetry", None)
    span = getattr(telemetry, "span", None)
    if callable(span):
        return span(name, attributes)
    return _null_span()


def handle_worker_command(service: Any, run_id: int, max_jobs: int | None = None) -> tuple[int, dict[str, Any]]:
    trace_id = f"trace-{uuid4()}"
    with _telemetry_span(
        service,
        "worker.run",
        build_telemetry_attributes(capability="worker", run_id=run_id, trace_id=trace_id, max_jobs=max_jobs or 0),
    ):
        processed = service.process_follow_queue(run_id=run_id, trace_id=trace_id, max_jobs=max_jobs)
    return 0, {"run_id": run_id, "processed": processed, "trace_id": trace_id}


def handle_resume_command(storage: Any, service: Any, run_id: int, max_jobs: int | None = None) -> tuple[int, dict[str, Any]]:
    run = storage.get_run(run_id)
    if not run:
        return 2, {"run_id": run_id, "error": "run_not_found"}

    if run.get("status") not in {"running", "failed", "aborted"}:
        return 2, {"run_id": run_id, "error": "run_not_resumable", "status": run.get("status")}

    trace_id = str(run.get("trace_id") or f"trace-{uuid4()}")
    processed = service.process_follow_queue(run_id=run_id, trace_id=trace_id, max_jobs=max_jobs)
    queue_stats = storage.get_follow_job_stats(run_id=run_id)
    return 0, {"run_id": run_id, "processed": processed, "trace_id": trace_id, "queue": queue_stats}


def handle_abort_command(storage: Any, run_id: int, reason: str) -> tuple[int, dict[str, Any]]:
    run = storage.get_run(run_id)
    if not run:
        return 2, {"run_id": run_id, "error": "run_not_found"}

    aborted = storage.abort_run(run_id, reason)
    if aborted:
        storage.add_security_event("run_aborted", json.dumps({"reason": reason}), run_id=run_id)
        storage.commit()

    return 0 if aborted else 2, {
        "run_id": run_id,
        "aborted": aborted,
        "status": "aborted" if aborted else run.get("status"),
    }


def handle_default_run_command(service: Any, run_executor: Any) -> tuple[int, dict[str, Any]]:
    try:
        result = run_executor(service)
        return 0, result
    except RuntimeError as exc:
        message = str(exc)
        payload: dict[str, Any] = {
            "ok": False,
            "error": "run_failed",
            "message": message,
        }
        if "status=401" in message:
            payload["error"] = "github_auth_invalid"
        return 2, payload
