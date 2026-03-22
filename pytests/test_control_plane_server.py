from types import SimpleNamespace

from interfaces.api.control_plane_server import ControlPlaneServer, run_bot_subcommand


def test_run_bot_subcommand_uses_safe_subprocess(monkeypatch):
    captured = {}

    def fake_run(args, capture_output, text, shell, check):
        captured["args"] = args
        captured["shell"] = shell
        return SimpleNamespace(returncode=0, stdout='{"ok": true}\n', stderr="")

    monkeypatch.setattr("interfaces.api.control_plane_server.subprocess.run", fake_run)
    payload = run_bot_subcommand(["run"])

    assert payload["exit_code"] == 0
    assert payload["command"] == ["run"]
    assert captured["args"][:2] == ["python", "bot.py"]
    assert captured["shell"] is False


def test_control_plane_handler_factory_returns_handler_class():
    server = ControlPlaneServer(status_provider=lambda: {"status": "ok"}, command_runner=lambda _cmd: {"ok": True})
    handler_cls = server.make_handler()
    assert handler_cls.__name__ == "Handler"


def test_control_plane_endpoints_cover_minimum_contract():
    commands = []
    server = ControlPlaneServer(
        status_provider=lambda: {"status": "ok", "stats": {"runs": 1}},
        command_runner=lambda cmd: commands.append(cmd) or {"command": cmd, "exit_code": 0},
    )

    code, payload = server.handle_request("GET", "/healthz", None)
    assert code == 200
    assert payload["status"] == "ok"

    code, payload = server.handle_request("GET", "/status", None)
    assert code == 200
    assert payload["stats"]["runs"] == 1

    code, payload = server.handle_request("POST", "/run", None)
    assert code == 202
    assert payload["command"] == ["run"]

    code, payload = server.handle_request("POST", "/abort", {"run_id": 9, "reason": "operator_request"})
    assert code == 202
    assert payload["command"] == ["abort", "--run-id", "9", "--reason", "operator_request"]

    code, payload = server.handle_request("POST", "/resume", {"run_id": 9, "max_jobs": 5})
    assert code == 202
    assert payload["command"] == ["resume", "--run-id", "9", "--max-jobs", "5"]

    assert commands == [
        ["run"],
        ["abort", "--run-id", "9", "--reason", "operator_request"],
        ["resume", "--run-id", "9", "--max-jobs", "5"],
    ]


def test_control_plane_rejects_invalid_abort_resume_payload():
    server = ControlPlaneServer(status_provider=lambda: {"status": "ok"}, command_runner=lambda _cmd: {"ok": True})

    code, payload = server.handle_request("POST", "/abort", {"run_id": 0})
    assert code == 400
    assert payload["error"] == "invalid_run_id"

    code, payload = server.handle_request("POST", "/resume", {"run_id": "abc"})
    assert code == 400
    assert payload["error"] == "invalid_run_id"

    code, payload = server.handle_request("POST", "/resume", {"run_id": 1, "max_jobs": 0})
    assert code == 400
    assert payload["error"] == "invalid_max_jobs"
