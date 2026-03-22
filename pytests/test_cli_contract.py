import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bot


class DummyService:
    def __init__(self, *_args, **_kwargs):
        pass

    def process_follow_queue(self, run_id, trace_id, max_jobs=None):
        assert run_id == 5
        assert trace_id.startswith("trace-")
        assert max_jobs == 2
        return 2


def _set_base_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_DB_PATH", str(tmp_path / "state.db"))


def test_cli_stats_contract(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    exit_code = bot.main(["stats"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert "followers_total" in payload
    assert "last_run" in payload


def test_cli_doctor_contract(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_MAX_FORKS_PER_RUN", "4")

    exit_code = bot.main(["doctor"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["db_exists"] is True
    assert payload["db_engine"] == "sqlite"
    assert "follow_job_max_attempts" in payload
    assert payload["max_forks_per_run"] == 4


def test_cli_worker_contract(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setattr(bot, "FollowBackService", DummyService)

    exit_code = bot.main(["worker", "--run-id", "5", "--max-jobs", "2"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["run_id"] == 5
    assert payload["processed"] == 2


def test_cli_export_postgres_profile_contract(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    output = tmp_path / "postgres-profile.json"

    exit_code = bot.main(["export-postgres-migration-profile", "--output", str(output)])
    assert exit_code == 0
    assert output.exists()

    written_payload = json.loads(output.read_text(encoding="utf-8"))
    assert "tables" in written_payload
    assert "avg_query_ms" in written_payload["horizontal_scaling_profile"]
    assert "written" in json.loads(capsys.readouterr().out)


def test_cli_export_defaults_to_command_artifacts_dir(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)

    exit_code = bot.main(["export-audit", "--output", "audit.json"])
    assert exit_code == 0

    written_path = tmp_path / "artifacts" / "commands" / "audit.json"
    assert written_path.exists()
    assert "written" in json.loads(capsys.readouterr().out)


def test_cli_run_uses_application_use_case(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    class FakeRunService:
        def __init__(self, _config, _logger):
            self.logger = logging.getLogger("fake")

    def fake_execute_run(service):
        assert isinstance(service, FakeRunService)
        return {"run_id": 9, "followers_fetched": 0, "followers_followed": 0, "trace_id": "trace-test"}

    monkeypatch.setattr(bot, "FollowBackService", FakeRunService)
    monkeypatch.setattr(bot, "execute_run", fake_execute_run)

    exit_code = bot.main(["run"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["run_id"] == 9


def test_cli_check_file_hardening_contract(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    log_path = tmp_path / "bot.log"
    log_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(bot, "LOG_FILE", str(log_path))

    exit_code = bot.main(["check-file-hardening"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert "db" in payload["files"]
    assert "log" in payload["files"]


def test_cli_resume_contract(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    class ResumeService:
        def __init__(self, *_args, **_kwargs):
            pass

        def process_follow_queue(self, run_id, trace_id, max_jobs=None):
            assert trace_id.startswith("trace-")
            assert max_jobs == 2
            return 1

    monkeypatch.setattr(bot, "FollowBackService", ResumeService)

    storage = bot.build_storage(bot.BotConfig.from_env())
    run_id = storage.begin_run(trace_id="trace-resume")
    storage.upsert_follow_job(run_id, "alice", "pending")
    storage.commit()

    exit_code = bot.main(["resume", "--run-id", str(run_id), "--max-jobs", "2"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["run_id"] == run_id
    assert payload["processed"] == 1
    assert payload["queue"]["total"] >= 0


def test_cli_abort_contract(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    storage = bot.build_storage(bot.BotConfig.from_env())
    run_id = storage.begin_run(trace_id="trace-abort")
    storage.commit()

    exit_code = bot.main(["abort", "--run-id", str(run_id), "--reason", "operator_request"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["run_id"] == run_id
    assert payload["aborted"] is True
    assert payload["status"] == "aborted"


def test_cli_fork_repos_requires_filter(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    exit_code = bot.main(["fork-repos", "--username", "alice"])
    assert exit_code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] == "no_filters_selected"


def test_cli_fork_repos_contract(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    class ForkService:
        def __init__(self, *_args, **_kwargs):
            pass

        def fork_repositories_for_user(self, **kwargs):
            assert kwargs["target_username"] == "alice"
            assert kwargs["include_owned"] is True
            assert kwargs["include_forked"] is False
            assert kwargs["include_profile_readme"] is True
            assert kwargs["fork_sources_for_forks"] is True
            assert kwargs["follow_fork_owners"] is True
            return {"target_username": "alice", "scanned": 3, "forked": 2, "failed": 1}

    monkeypatch.setattr(bot, "FollowBackService", ForkService)
    exit_code = bot.main(
        [
            "fork-repos",
            "--username",
            "alice",
            "--owned",
            "--profile-readme",
            "--fork-source",
            "--follow-fork-owners",
        ]
    )
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["target_username"] == "alice"
    assert payload["forked"] == 2


def test_cli_export_governance_profile_contract(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    output = tmp_path / "governance-profile.json"

    exit_code = bot.main(["export-governance-profile", "--output", str(output)])
    assert exit_code == 0
    assert output.exists()

    written_payload = json.loads(output.read_text(encoding="utf-8"))
    assert written_payload["status"] == "defined"
    assert written_payload["policy_controls"]["consent_required"] is True
    assert "written" in json.loads(capsys.readouterr().out)


def test_cli_serve_control_plane_contract(monkeypatch, tmp_path):
    _set_base_env(monkeypatch, tmp_path)

    captured = {"storage_ids": []}

    class DummyStorage:
        counter = 0

        def __init__(self):
            DummyStorage.counter += 1
            self.uid = DummyStorage.counter

        def close(self):
            return None

    def fake_build_storage(_config):
        return DummyStorage()

    def fake_handle_control_plane_status(storage, _config):
        captured["storage_ids"].append(storage.uid)
        return 0, {"status": "ok", "stats": {}}

    def fake_serve_control_plane(host, port, status_provider, command_runner=None):
        captured["host"] = host
        captured["port"] = port
        first = status_provider()
        second = status_provider()
        assert first["status"] == "ok"
        assert second["status"] == "ok"

    monkeypatch.setattr(bot, "build_storage", fake_build_storage)
    monkeypatch.setattr(bot, "handle_control_plane_status", fake_handle_control_plane_status)
    monkeypatch.setattr(bot, "serve_control_plane", fake_serve_control_plane)

    exit_code = bot.main(["serve-control-plane", "--host", "0.0.0.0", "--port", "8090"])
    assert exit_code == 0
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 8090
    assert len(set(captured["storage_ids"])) == 2


def test_cli_queue_backend_status_default_sqlite(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    exit_code = bot.main(["queue-backend-status"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["backend"] == "sqlite"
    assert payload["ready"] is True


def test_cli_queue_backend_status_rabbitmq_requires_amqp_url(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_QUEUE_BACKEND", "rabbitmq")
    monkeypatch.delenv("BOT_RABBITMQ_AMQP_URL", raising=False)

    exit_code = bot.main(["queue-backend-status"])
    assert exit_code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["backend"] == "rabbitmq"
    assert payload["ready"] is False
    assert payload["amqp_url_configured"] is False


def test_cli_otel_runtime_status_partial_when_missing_endpoint(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_OTEL_ENABLED", "true")
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)

    exit_code = bot.main(["otel-runtime-status"])
    assert exit_code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "partial"
    assert payload["otel_enabled"] is True


def test_cli_otel_runtime_status_ready(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_OTEL_ENABLED", "true")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")

    exit_code = bot.main(["otel-runtime-status"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ready"
    assert payload["exporter_otlp_endpoint_configured"] is True


def test_cli_compliance_evidence_status_incomplete(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    evidence = tmp_path / "enterprise-evidence"
    evidence.mkdir()
    (evidence / "doctor_report.json").write_text("{}", encoding="utf-8")

    exit_code = bot.main(["compliance-evidence-status", "--evidence-dir", str(evidence)])
    assert exit_code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "incomplete"
    assert payload["missing_count"] > 0


def test_cli_compliance_evidence_status_ready(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    evidence = tmp_path / "enterprise-evidence"
    evidence.mkdir()
    for name in [
        "doctor_report.json",
        "audit.json",
        "sbom_ci.json",
        "release_manifest_ci.json",
        "queue_backend_status_report.json",
        "otel_runtime_status_report.json",
    ]:
        (evidence / name).write_text("{}", encoding="utf-8")

    exit_code = bot.main(["compliance-evidence-status", "--evidence-dir", str(evidence)])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ready"
    assert payload["missing_count"] == 0


def test_cli_queue_backend_verify_sqlite(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    exit_code = bot.main(["queue-backend-verify"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["backend"] == "sqlite"
    assert payload["status"] == "verified"


def test_cli_queue_backend_verify_rabbitmq_with_fake_adapter(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_QUEUE_BACKEND", "rabbitmq")
    monkeypatch.setenv("BOT_RABBITMQ_AMQP_URL", "amqp://guest:guest@localhost:5672/")

    class FakeAdapter:
        def __init__(self, **_kwargs):
            pass

        def ensure_topology(self):
            return None

    monkeypatch.setattr(bot, "RabbitMQFollowQueueAdapter", FakeAdapter)

    exit_code = bot.main(["queue-backend-verify"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["backend"] == "rabbitmq"
    assert payload["status"] == "verified"


def test_cli_export_enterprise_readiness_report_partial(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    output = tmp_path / "enterprise-readiness.json"

    exit_code = bot.main(["export-enterprise-readiness-report", "--output", str(output), "--evidence-dir", str(tmp_path / "missing")])
    assert exit_code == 2
    assert output.exists()

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "partial"
    assert "blocking_items" in payload
    cli_payload = json.loads(capsys.readouterr().out)
    assert "written" in cli_payload


def test_cli_export_enterprise_readiness_report_ready(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_OTEL_ENABLED", "true")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")
    evidence = tmp_path / "enterprise-evidence"
    evidence.mkdir()
    for name in [
        "doctor_report.json",
        "audit.json",
        "sbom_ci.json",
        "release_manifest_ci.json",
        "queue_backend_status_report.json",
        "otel_runtime_status_report.json",
    ]:
        (evidence / name).write_text("{}", encoding="utf-8")

    output = tmp_path / "enterprise-readiness-ready.json"
    exit_code = bot.main(["export-enterprise-readiness-report", "--output", str(output), "--evidence-dir", str(evidence)])
    assert exit_code == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "ready"
    assert payload["blocking_items"] == []
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["status"] == "ready"


def test_cli_queue_backend_smoke_sqlite(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    exit_code = bot.main(["queue-backend-smoke"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["backend"] == "sqlite"
    assert payload["status"] == "smoke_ok"


def test_cli_queue_backend_smoke_rabbitmq_with_fake_adapter(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_QUEUE_BACKEND", "rabbitmq")
    monkeypatch.setenv("BOT_RABBITMQ_AMQP_URL", "amqp://guest:guest@localhost:5672/")

    class FakeAdapter:
        def __init__(self, **_kwargs):
            self.job = None
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
            return None

        def requeue_or_dead_letter(self, _job, _error):
            return "requeued"

    monkeypatch.setattr(bot, "RabbitMQFollowQueueAdapter", FakeAdapter)

    exit_code = bot.main(["queue-backend-smoke"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["backend"] == "rabbitmq"
    assert payload["status"] == "smoke_ok"


def test_cli_enterprise_readiness_gate_fail(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    exit_code = bot.main(["enterprise-readiness-gate", "--evidence-dir", str(tmp_path / "missing")])
    assert exit_code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["gate"] == "fail"
    assert payload["overall_status"] == "partial"


def test_cli_enterprise_readiness_gate_warn_when_allow_partial(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    exit_code = bot.main(["enterprise-readiness-gate", "--evidence-dir", str(tmp_path / "missing"), "--allow-partial"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["gate"] == "warn"
    assert payload["allow_partial"] is True


def test_cli_enterprise_backlog_status_in_progress(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    exit_code = bot.main(["enterprise-backlog-status", "--evidence-dir", str(tmp_path / "missing")])
    assert exit_code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_status"] == "in_progress"
    assert payload["pending_count"] >= 1


def test_cli_enterprise_backlog_status_closed(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_OTEL_ENABLED", "true")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")
    evidence = tmp_path / "enterprise-evidence"
    evidence.mkdir()
    for name in [
        "doctor_report.json",
        "audit.json",
        "sbom_ci.json",
        "release_manifest_ci.json",
        "queue_backend_status_report.json",
        "otel_runtime_status_report.json",
    ]:
        (evidence / name).write_text("{}", encoding="utf-8")

    exit_code = bot.main(["enterprise-backlog-status", "--evidence-dir", str(evidence)])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_status"] == "closed"
    assert payload["pending_count"] == 0


def test_cli_enterprise_remaining_work_has_pending(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    exit_code = bot.main(["enterprise-remaining-work", "--evidence-dir", str(tmp_path / "missing")])
    assert exit_code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_status"] == "remaining_work"
    assert payload["pending_count"] >= 1


def test_cli_enterprise_remaining_work_none_pending(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_OTEL_ENABLED", "true")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")

    evidence = tmp_path / "enterprise-evidence"
    evidence.mkdir()
    for name in [
        "doctor_report.json",
        "audit.json",
        "sbom_ci.json",
        "release_manifest_ci.json",
        "queue_backend_status_report.json",
        "otel_runtime_status_report.json",
    ]:
        (evidence / name).write_text("{}", encoding="utf-8")

    exit_code = bot.main(["enterprise-remaining-work", "--evidence-dir", str(evidence)])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["overall_status"] == "no_remaining_work"
    assert payload["pending_count"] == 0


def test_cli_enterprise_handoff_report_pending(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    exit_code = bot.main(["enterprise-handoff-report", "--evidence-dir", str(tmp_path / "missing")])
    assert exit_code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["closure_ready"] is False
    assert payload["handoff_status"] == "pending_operational_closeout"


def test_cli_enterprise_handoff_report_ready(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_OTEL_ENABLED", "true")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")

    evidence = tmp_path / "enterprise-evidence"
    evidence.mkdir()
    for name in [
        "doctor_report.json",
        "audit.json",
        "sbom_ci.json",
        "release_manifest_ci.json",
        "queue_backend_status_report.json",
        "otel_runtime_status_report.json",
    ]:
        (evidence / name).write_text("{}", encoding="utf-8")

    exit_code = bot.main(["enterprise-handoff-report", "--evidence-dir", str(evidence)])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["closure_ready"] is True
    assert payload["handoff_status"] == "ready_for_closeout"
