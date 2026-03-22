import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.application.control_plane_adapter import ControlPlaneAdapter


class DummyStorage:
    def get_last_run(self):
        return {"id": 7}

    def get_stats(self):
        return {"followers_total": 3}

    def get_follow_job_stats(self, run_id=None):
        return {"run_id": run_id, "pending": 1}

    def export_audit_payload(self):
        return {"follow_actions": [{"id": 1}]}

    def close(self):
        return None


def test_control_plane_adapter_contract(tmp_path):
    storage = DummyStorage()

    adapter = ControlPlaneAdapter(
        config=object(),
        logger=logging.getLogger("test"),
        storage=storage,
        build_storage=lambda _cfg: storage,
        build_follow_back_service=lambda *_a, **_k: object(),
        handle_default_run_command=lambda _svc, run_executor: (0, {"run_id": 11, "trace_id": "trace-1"}),
        handle_resume_command=lambda _st, _svc, run_id, max_jobs=None: (0, {"run_id": run_id, "trace_id": "trace-2", "processed": max_jobs}),
        handle_abort_command=lambda _st, run_id, reason: (0, {"run_id": run_id, "aborted": True, "reason": reason}),
        handle_control_plane_status=lambda _st, _cfg: (0, {"status": "ok"}),
        execute_run=lambda _svc: {"run_id": 11, "trace_id": "trace-1"},
        doctor_report=lambda _cfg, _st: {"ok": True},
        resolve_command_output_path=lambda output: tmp_path / output,
    )

    assert adapter.dashboard()["status_code"] == 0
    assert adapter.runs()["last_run"]["id"] == 7
    assert adapter.run_start()["run_id"] == 11
    assert adapter.run_resume(run_id=9, max_jobs=5)["payload"]["processed"] == 5
    assert adapter.run_abort(run_id=9, reason="ops")["payload"]["aborted"] is True
    assert adapter.diagnostics()["payload"]["ok"] is True
    assert adapter.queue_metrics(run_id=4)["payload"]["run_id"] == 4

    export = adapter.export_audit("audit.json")
    assert export["records"] == 1
    written = json.loads((tmp_path / "audit.json").read_text(encoding="utf-8"))
    assert "follow_actions" in written
