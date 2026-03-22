from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable


class ControlPlaneServer:
    def __init__(self, *, status_provider: Callable[[], dict[str, Any]], command_runner: Callable[[list[str]], dict[str, Any]]):
        self._status_provider = status_provider
        self._command_runner = command_runner

    def make_handler(self) -> type[BaseHTTPRequestHandler]:
        server = self

        class Handler(BaseHTTPRequestHandler):
            def _write_json(self, code: int, payload: dict[str, Any]) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802
                code, payload = server.handle_request("GET", self.path, None)
                self._write_json(code, payload)

            def _read_body(self) -> dict[str, Any] | None:
                length_raw = self.headers.get("Content-Length", "0")
                try:
                    content_length = int(length_raw)
                except ValueError:
                    return None
                if content_length <= 0:
                    return None

                raw = self.rfile.read(content_length)
                if not raw:
                    return None

                try:
                    parsed = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return None
                return parsed if isinstance(parsed, dict) else None

            def do_POST(self) -> None:  # noqa: N802
                body = self._read_body()
                code, payload = server.handle_request("POST", self.path, body)
                self._write_json(code, payload)

            def log_message(self, _format: str, *_args: Any) -> None:
                return

        return Handler

    def handle_request(self, method: str, raw_path: str, body: dict[str, Any] | None) -> tuple[int, dict[str, Any]]:
        path = urlparse(raw_path).path

        if method == "GET" and path == "/healthz":
            return 200, {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

        if method == "GET" and path == "/status":
            return 200, self._status_provider()

        if method == "POST" and path == "/run":
            return 202, self._command_runner(["run"])

        if method == "POST" and path == "/scheduler":
            return 202, self._command_runner(["scheduler", "--interval-seconds", "60", "--max-ticks", "1"])

        if method == "POST" and path == "/abort":
            run_id = _coerce_run_id((body or {}).get("run_id"))
            if run_id is None:
                return 400, {"error": "invalid_run_id"}
            reason = str((body or {}).get("reason") or "aborted_by_control_plane")
            return 202, self._command_runner(["abort", "--run-id", str(run_id), "--reason", reason])

        if method == "POST" and path == "/resume":
            run_id = _coerce_run_id((body or {}).get("run_id"))
            if run_id is None:
                return 400, {"error": "invalid_run_id"}

            command = ["resume", "--run-id", str(run_id)]
            max_jobs = (body or {}).get("max_jobs")
            if max_jobs is not None:
                max_jobs_num = _coerce_positive_int(max_jobs)
                if max_jobs_num is None:
                    return 400, {"error": "invalid_max_jobs"}
                command.extend(["--max-jobs", str(max_jobs_num)])

            return 202, self._command_runner(command)

        return 404, {"error": "not_found", "path": path}


def _coerce_positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _coerce_run_id(value: Any) -> int | None:
    return _coerce_positive_int(value)


def run_bot_subcommand(command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(["python", "bot.py", *command], capture_output=True, text=True, shell=False, check=False)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    payload: dict[str, Any] = {
        "command": command,
        "exit_code": proc.returncode,
        "stdout": stdout,
    }
    if stderr:
        payload["stderr"] = stderr
    return payload


def serve_control_plane(host: str, port: int, *, status_provider: Callable[[], dict[str, Any]], command_runner: Callable[[list[str]], dict[str, Any]] = run_bot_subcommand) -> None:
    server = ControlPlaneServer(status_provider=status_provider, command_runner=command_runner)
    httpd = ThreadingHTTPServer((host, port), server.make_handler())
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
