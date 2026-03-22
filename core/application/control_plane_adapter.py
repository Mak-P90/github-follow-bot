from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class ControlPlaneAdapter:
    """Thin orchestration adapter for GUI/API surfaces.

    This adapter reuses existing capability handlers and keeps responses structured.
    """

    config: Any
    logger: Any
    storage: Any
    build_storage: Callable[[Any], Any]
    build_follow_back_service: Callable[..., Any]
    handle_default_run_command: Callable[..., tuple[int, dict[str, Any]]]
    handle_resume_command: Callable[..., tuple[int, dict[str, Any]]]
    handle_abort_command: Callable[..., tuple[int, dict[str, Any]]]
    handle_control_plane_status: Callable[..., tuple[int, dict[str, Any]]]
    execute_run: Callable[..., dict[str, Any]]
    doctor_report: Callable[..., dict[str, Any]]
    resolve_command_output_path: Callable[[str], Path]

    def _with_storage(self, callback: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
        storage = self.build_storage(self.config)
        try:
            return callback(storage)
        finally:
            close = getattr(storage, "close", None)
            if callable(close):
                close()

    def dashboard(self) -> dict[str, Any]:
        def _callback(storage: Any) -> dict[str, Any]:
            status, payload = self.handle_control_plane_status(storage, self.config)
            return {"status_code": status, "event": "control_plane_dashboard", "payload": payload}

        return self._with_storage(_callback)

    def runs(self) -> dict[str, Any]:
        return self._with_storage(
            lambda storage: {
                "event": "control_plane_runs",
                "last_run": storage.get_last_run(),
                "stats": storage.get_stats(),
            }
        )

    def run_start(self) -> dict[str, Any]:
        service = self.build_follow_back_service(self.config, self.logger)
        status, payload = self.handle_default_run_command(service, run_executor=self.execute_run)
        return {"status_code": status, "event": "run_started", "payload": payload, "run_id": payload.get("run_id"), "trace_id": payload.get("trace_id")}

    def run_resume(self, run_id: int, max_jobs: int | None = None) -> dict[str, Any]:
        def _callback(storage: Any) -> dict[str, Any]:
            service = self.build_follow_back_service(self.config, self.logger, storage=storage)
            status, payload = self.handle_resume_command(storage, service, run_id=run_id, max_jobs=max_jobs)
            return {"status_code": status, "event": "run_resumed", "payload": payload, "run_id": run_id, "trace_id": payload.get("trace_id")}

        return self._with_storage(_callback)

    def run_abort(self, run_id: int, reason: str) -> dict[str, Any]:
        def _callback(storage: Any) -> dict[str, Any]:
            status, payload = self.handle_abort_command(storage, run_id=run_id, reason=reason)
            return {"status_code": status, "event": "run_aborted", "payload": payload, "run_id": run_id}

        return self._with_storage(_callback)

    def diagnostics(self) -> dict[str, Any]:
        return self._with_storage(lambda storage: {"event": "diagnostics", "payload": self.doctor_report(self.config, storage)})

    def queue_metrics(self, run_id: int | None = None) -> dict[str, Any]:
        return self._with_storage(lambda storage: {"event": "queue_metrics", "payload": storage.get_follow_job_stats(run_id=run_id)})

    def export_audit(self, output: str) -> dict[str, Any]:
        def _callback(storage: Any) -> dict[str, Any]:
            payload = storage.export_audit_payload()
            output_path = self.resolve_command_output_path(output)
            output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            return {"event": "export_audit", "output": str(output_path), "records": len(payload.get("follow_actions", []))}

        return self._with_storage(_callback)