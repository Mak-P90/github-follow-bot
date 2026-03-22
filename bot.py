"""GitHub follower bot with SQLite persistence, structured logs and guardrails.

Usage:
    python bot.py run
    python bot.py stats
    python bot.py doctor
    python bot.py export-audit --output audit.json
"""

from __future__ import annotations

import argparse
from collections import deque
from contextlib import contextmanager
import hashlib
import hmac
import importlib.metadata as importlib_metadata
import json
import logging
import os
import random
import re
import shlex
import sqlite3
import stat
import subprocess
import sys
import time
from urllib.parse import quote
from time import perf_counter
from dataclasses import dataclass
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Iterable, Any
from uuid import uuid4

import requests
import jwt
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from requests.exceptions import RequestException

from core.application.capabilities.follow_back import (
    handle_abort_command,
    handle_default_run_command,
    handle_resume_command,
    handle_worker_command,
)
from core.application.capabilities.follow_back_service import FollowBackService
from core.application.capabilities.fork_discovery import handle_fork_repos_command
from core.application.capabilities.control_plane import (
    handle_control_plane_status,
    handle_scheduler_command,
)
from core.application.control_plane_adapter import ControlPlaneAdapter
from core.application.capabilities.queue_backend import verify_queue_backend, smoke_test_queue_backend
from core.domain.contracts import StoragePort
from core.application.use_cases import execute_run
from infra.policy import PolicyEngine
from interfaces.api.control_plane_server import serve_control_plane
from interfaces.gui.app import run_gui
from adapters.queue import RabbitMQFollowQueueAdapter
from interfaces.cli.command_dispatcher import CliCommandContext, dispatch_cli_command

API_BASE = "https://api.github.com"
PER_PAGE = 100
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0
RATE_LIMIT_THRESHOLD = 100
DELAY_BETWEEN_FOLLOWS = 1.0
RUNTIME_DIR = Path("runtime")
RUNTIME_DATA_DIR = RUNTIME_DIR / "data"
RUNTIME_LOG_DIR = RUNTIME_DIR / "logs"
DB_FILE = str(RUNTIME_DATA_DIR / "bot_state.db")
DB_ENGINE_DEFAULT = "sqlite"
POSTGRES_SCHEMA_VERSION = "postgres-v1"
POSTGRES_SCHEMA_FILE = Path(__file__).resolve().parent / "scripts" / "sql" / "postgres_schema_v1.sql"
LOG_FILE = str(RUNTIME_LOG_DIR / f"bot-{datetime.now().strftime('%Y-%m-%d')}.log")
COMMAND_OUTPUT_DIR = Path("artifacts") / "commands"
LEGACY_FILES = ["followers.txt", "last_followed_user.txt", "last_checked_follower.txt"]
FILE_PERMISSION_POLICY = {
    "db": 0o600,
    "log": 0o640,
}

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=False)


def _file_mode(path: str) -> int | None:
    try:
        return stat.S_IMODE(os.stat(path).st_mode)
    except FileNotFoundError:
        return None


def enforce_runtime_file_permissions(path: str, file_role: str) -> dict[str, Any]:
    expected = FILE_PERMISSION_POLICY[file_role]
    report: dict[str, Any] = {
        "path": path,
        "role": file_role,
        "exists": os.path.exists(path),
        "expected_mode_octal": oct(expected),
        "mode_octal": None,
        "compliant": False,
        "status": "pending",
    }
    if os.name != "posix":
        report["status"] = "unsupported_platform"
        report["compliant"] = True
        return report

    if not os.path.exists(path):
        report["status"] = "missing"
        return report

    try:
        os.chmod(path, expected)
        mode = _file_mode(path)
        report["mode_octal"] = oct(mode) if mode is not None else None
        report["compliant"] = mode == expected
        report["status"] = "ok" if report["compliant"] else "mismatch"
        stat_info = os.stat(path)
        report["owner_uid"] = stat_info.st_uid
        report["owner_gid"] = stat_info.st_gid
    except OSError as exc:
        report["status"] = "error"
        report["error"] = str(exc)
    return report


def ensure_parent_dir(path: str) -> None:
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def collect_runtime_file_permission_report(config: "BotConfig") -> dict[str, dict[str, Any]]:
    return {
        "db": enforce_runtime_file_permissions(config.db_path, "db"),
        "log": enforce_runtime_file_permissions(LOG_FILE, "log"),
    }


def runtime_file_hardening_check(config: "BotConfig") -> dict[str, Any]:
    report = collect_runtime_file_permission_report(config)
    db_ok = bool(report["db"].get("compliant"))
    log_ok = bool(report["log"].get("compliant"))
    ok = db_ok and log_ok
    return {"ok": ok, "files": report}


def resolve_command_output_path(raw_output_path: str) -> Path:
    output_path = Path(raw_output_path)
    if not output_path.is_absolute() and len(output_path.parts) == 1:
        output_path = COMMAND_OUTPUT_DIR / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer|token)\s+)([^\s,;\"']+)"),
    re.compile(r"(?i)(\"?authorization\"?\s*[:=]\s*\"?(?:bearer|token)\s+)([^\s,;\"'}]+)"),
    re.compile(r"(?i)(x-?(?:api-)?token\s*[:=]\s*\"?)([^\s,;\"'}]+)"),
    re.compile(r"(?i)(\"?private_key\"?\s*[:=]\s*\"?)([^\s,;\"'}]+)"),
    re.compile(r"(?i)(\"?token\"?\s*[:=]\s*\"?)([^\s,;\"'}]+)"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
)


def redact_sensitive_text(value: str, secrets: list[str] | None = None) -> str:
    redacted = value
    for secret in secrets or []:
        if secret:
            redacted = redacted.replace(secret, "***REDACTED***")
    for pattern in SENSITIVE_TEXT_PATTERNS:
        if pattern.groups >= 2:
            redacted = pattern.sub(r"\1***REDACTED***", redacted)
        else:
            redacted = pattern.sub("***REDACTED_PRIVATE_KEY***", redacted)
    return redacted


def sanitize_error_payload(payload: Any, secrets: list[str] | None = None) -> str:
    if isinstance(payload, BaseException):
        return redact_sensitive_text(str(payload), secrets)
    if isinstance(payload, (dict, list, tuple)):
        return redact_sensitive_text(json.dumps(payload, ensure_ascii=False), secrets)
    return redact_sensitive_text(str(payload), secrets)


def normalize_repository_full_name(full_name: str) -> tuple[str, str]:
    cleaned = full_name.strip().strip("/")
    if cleaned.count("/") != 1:
        raise ValueError("repository full_name must use owner/repo format")
    owner, repo = cleaned.split("/", 1)
    owner = owner.strip()
    repo = repo.strip()
    if not owner or not repo:
        raise ValueError("repository full_name must include owner and repo")
    return owner, repo

def load_postgres_schema_sql() -> str:
    if not POSTGRES_SCHEMA_FILE.exists():
        raise RuntimeError(f"Missing PostgreSQL schema file: {POSTGRES_SCHEMA_FILE}")
    return POSTGRES_SCHEMA_FILE.read_text(encoding="utf-8")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        for extra_key in (
            "event",
            "run_id",
            "trace_id",
            "username",
            "status_code",
            "seed_login",
            "seed_index",
            "phase",
            "page",
            "limit_type",
            "current_value",
            "window",
            "threshold",
            "reason",
        ):
            if hasattr(record, extra_key):
                payload[extra_key] = getattr(record, extra_key)
        return json.dumps(payload, ensure_ascii=False)


@contextmanager
def null_span() -> Iterable[None]:
    yield None


class TelemetryRuntime:
    def __init__(self, config: "BotConfig"):
        self.enabled = config.otel_enabled
        self.provider: TracerProvider | None = None
        self.tracer: trace.Tracer | None = None

        if not self.enabled:
            return

        resource = Resource.create({"service.name": config.otel_service_name})
        provider = TracerProvider(resource=resource)
        if config.otel_exporter_otlp_endpoint:
            exporter = OTLPSpanExporter(endpoint=config.otel_exporter_otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        else:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(provider)
        self.provider = provider
        self.tracer = trace.get_tracer(config.otel_service_name)

    @contextmanager
    def span(self, name: str, attributes: dict[str, str | int | bool] | None = None) -> Iterable[object | None]:
        if not self.tracer:
            with null_span() as s:
                yield s
            return

        with self.tracer.start_as_current_span(name) as span:
            for key, value in (attributes or {}).items():
                span.set_attribute(key, value)
            yield span

    def shutdown(self) -> None:
        if self.provider:
            self.provider.shutdown()


class SecretRedactionFilter(logging.Filter):
    """Best-effort redaction to avoid token leaks in logs."""

    def __init__(self, secrets: list[str] | None = None):
        super().__init__()
        self.secrets = [s for s in (secrets or []) if s]

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_sensitive_text(str(record.msg), self.secrets)
        if record.args:
            record.args = tuple(sanitize_error_payload(arg, self.secrets) for arg in record.args)
        return True


def setup_logger(redact_secrets: list[str] | None = None) -> logging.Logger:
    logger = logging.getLogger("github_follower_bot")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    redaction_filter = SecretRedactionFilter(redact_secrets)

    ensure_parent_dir(LOG_FILE)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5)
    enforce_runtime_file_permissions(LOG_FILE, "log")
    file_handler.setFormatter(JsonFormatter())
    file_handler.addFilter(redaction_filter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonFormatter())
    console_handler.addFilter(redaction_filter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


@dataclass(frozen=True)
class BotConfig:
    github_user: str
    github_token: str
    db_engine: str = DB_ENGINE_DEFAULT
    db_path: str = DB_FILE
    postgres_dsn: str | None = None
    per_page: int = PER_PAGE
    dry_run: bool = False
    max_follows_per_run: int | None = None
    max_forks_per_run: int | None = None
    max_candidates_per_run: int | None = None
    max_api_calls_per_run: int | None = None
    max_expand_seeds_per_run: int | None = None
    discovery_mode: str = "followers"
    expand_http_error_window: int = 20
    expand_http_error_threshold: int = 5
    expand_fallback_to_followers: bool = False
    cleanup_legacy_files: bool = True
    auth_mode: str = "pat"
    release_manifest_signing_key: str | None = None
    release_manifest_require_signature: bool = False
    release_manifest_max_age_seconds: int | None = None
    github_app_id: str | None = None
    github_app_installation_id: str | None = None
    github_app_private_key: str | None = None
    github_app_private_key_file: str | None = None
    github_app_private_key_file_candidates: tuple[str, ...] = ()
    github_app_private_key_command: str | None = None
    follow_job_max_attempts: int = 3
    github_app_private_key_command_timeout_seconds: int = 10
    github_app_token_refresh_skew_seconds: int = 60
    verify_follow_after_put: bool = True
    follow_verify_max_retries: int = 2
    follow_verify_retry_delay_seconds: float = 1.0
    otel_enabled: bool = False
    otel_service_name: str = "github_follower_bot"
    otel_exporter_otlp_endpoint: str | None = None
    cosign_key_ref: str | None = None
    cosign_enabled: bool = False
    require_github_app_auth: bool = False
    gui_enabled: bool = False
    gui_host: str = "127.0.0.1"
    gui_port: int = 8081
    gui_locale: str = "en"

    def github_app_private_key_source(self) -> str:
        if self.github_app_private_key_command:
            return "command"
        if self.github_app_private_key_file:
            return "file"
        if self.github_app_private_key:
            return "inline"
        return "none"

    def resolve_github_app_private_key(self) -> str:
        if self.github_app_private_key_command:
            command_parts = shlex.split(self.github_app_private_key_command)
            if not command_parts:
                raise RuntimeError("GITHUB_APP_PRIVATE_KEY_COMMAND resolved to empty argv")
            completed = subprocess.run(
                command_parts,
                check=True,
                text=True,
                capture_output=True,
                timeout=self.github_app_private_key_command_timeout_seconds,
            )
            output = completed.stdout.strip()
            if output:
                return output.replace("\\n", "\n")
            raise RuntimeError("GITHUB_APP_PRIVATE_KEY_COMMAND returned empty output")
        if self.github_app_private_key_file:
            return Path(self.github_app_private_key_file).read_text(encoding="utf-8").strip()
        if self.github_app_private_key:
            return self.github_app_private_key
        raise RuntimeError("GitHub App private key is not configured")

    @classmethod
    def from_env(cls) -> "BotConfig":
        github_user = os.getenv("GITHUB_USER", "").strip()
        github_token = os.getenv("PERSONAL_GITHUB_TOKEN", "").strip()
        app_installation_token = os.getenv("GITHUB_APP_INSTALLATION_TOKEN", "").strip()
        github_app_id = os.getenv("GITHUB_APP_ID", "").strip() or None
        github_app_installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID", "").strip() or None
        github_app_private_key = os.getenv("GITHUB_APP_PRIVATE_KEY", "").strip() or None
        raw_private_key_file = os.getenv("GITHUB_APP_PRIVATE_KEY_FILE", "").strip()
        github_app_private_key_file_candidates: tuple[str, ...] = ()
        github_app_private_key_file = None
        if raw_private_key_file:
            candidate_delimiter = "," if "," in raw_private_key_file else os.pathsep
            raw_candidates = [part.strip() for part in raw_private_key_file.split(candidate_delimiter)]
            github_app_private_key_file_candidates = tuple(part for part in raw_candidates if part)
            if not github_app_private_key_file_candidates:
                raise EnvironmentError("GITHUB_APP_PRIVATE_KEY_FILE must include at least one file path")
            github_app_private_key_file = github_app_private_key_file_candidates[0]
        github_app_private_key_command = os.getenv("GITHUB_APP_PRIVATE_KEY_COMMAND", "").strip() or None
        if github_app_private_key:
            github_app_private_key = github_app_private_key.replace("\\n", "\n")
        if github_app_private_key and (github_app_private_key_file or github_app_private_key_command):
            raise EnvironmentError(
                "Use only one private key source: GITHUB_APP_PRIVATE_KEY, GITHUB_APP_PRIVATE_KEY_FILE, or GITHUB_APP_PRIVATE_KEY_COMMAND"
            )
        if github_app_private_key_file and github_app_private_key_command:
            raise EnvironmentError(
                "Use only one private key source: GITHUB_APP_PRIVATE_KEY_FILE or GITHUB_APP_PRIVATE_KEY_COMMAND"
            )
        if github_app_private_key_file:
            existing_candidates = [path for path in github_app_private_key_file_candidates if Path(path).is_file()]
            if not existing_candidates:
                raise EnvironmentError(
                    "GITHUB_APP_PRIVATE_KEY_FILE must point to an existing file (or list candidates separated by ','/pathsep)"
                )
            github_app_private_key_file = existing_candidates[0]
        db_engine = os.getenv("BOT_DB_ENGINE", DB_ENGINE_DEFAULT).strip().lower() or DB_ENGINE_DEFAULT
        if db_engine not in {"sqlite", "postgres"}:
            raise EnvironmentError("BOT_DB_ENGINE must be one of: sqlite, postgres")
        db_path = os.getenv("BOT_DB_PATH", DB_FILE).strip() or DB_FILE
        postgres_dsn = os.getenv("BOT_POSTGRES_DSN", "").strip() or None
        if db_engine == "postgres" and not postgres_dsn:
            raise EnvironmentError("BOT_POSTGRES_DSN is required when BOT_DB_ENGINE=postgres")
        dry_run = os.getenv("BOT_DRY_RUN", "false").strip().lower() in {"1", "true", "yes", "on"}
        cleanup_legacy_files = os.getenv("BOT_CLEANUP_LEGACY_FILES", "true").strip().lower() not in {"0", "false", "no", "off"}
        release_manifest_signing_key = os.getenv("RELEASE_MANIFEST_SIGNING_KEY", "").strip() or None
        release_manifest_require_signature = os.getenv("RELEASE_MANIFEST_REQUIRE_SIGNATURE", "false").strip().lower() in {"1", "true", "yes", "on"}

        release_manifest_max_age_seconds = None
        raw_manifest_max_age = os.getenv("RELEASE_MANIFEST_MAX_AGE_SECONDS", "").strip()
        if raw_manifest_max_age:
            parsed_max_age = int(raw_manifest_max_age)
            if parsed_max_age < 1:
                raise EnvironmentError("RELEASE_MANIFEST_MAX_AGE_SECONDS must be >= 1")
            release_manifest_max_age_seconds = parsed_max_age

        max_follows_per_run = None
        raw_limit = os.getenv("BOT_MAX_FOLLOWS_PER_RUN", "").strip()
        if raw_limit:
            value = int(raw_limit)
            if value < 1:
                raise EnvironmentError("BOT_MAX_FOLLOWS_PER_RUN must be >= 1")
            max_follows_per_run = value

        max_forks_per_run = None
        raw_max_forks_per_run = os.getenv("BOT_MAX_FORKS_PER_RUN", "").strip()
        if raw_max_forks_per_run:
            parsed_max_forks = int(raw_max_forks_per_run)
            if parsed_max_forks < 1:
                raise EnvironmentError("BOT_MAX_FORKS_PER_RUN must be >= 1")
            max_forks_per_run = parsed_max_forks

        max_candidates_per_run = None
        raw_max_candidates_per_run = os.getenv("BOT_MAX_CANDIDATES_PER_RUN", "").strip()
        if raw_max_candidates_per_run:
            parsed_max_candidates = int(raw_max_candidates_per_run)
            if parsed_max_candidates < 1:
                raise EnvironmentError("BOT_MAX_CANDIDATES_PER_RUN must be >= 1")
            max_candidates_per_run = parsed_max_candidates

        max_api_calls_per_run = None
        raw_max_api_calls_per_run = os.getenv("BOT_MAX_API_CALLS_PER_RUN", "").strip()
        if raw_max_api_calls_per_run:
            parsed_max_api_calls = int(raw_max_api_calls_per_run)
            if parsed_max_api_calls < 1:
                raise EnvironmentError("BOT_MAX_API_CALLS_PER_RUN must be >= 1")
            max_api_calls_per_run = parsed_max_api_calls

        max_expand_seeds_per_run = None
        raw_max_expand_seeds_per_run = os.getenv("BOT_MAX_EXPAND_SEEDS_PER_RUN", "").strip()
        if raw_max_expand_seeds_per_run:
            parsed_max_expand_seeds = int(raw_max_expand_seeds_per_run)
            if parsed_max_expand_seeds < 1:
                raise EnvironmentError("BOT_MAX_EXPAND_SEEDS_PER_RUN must be >= 1")
            max_expand_seeds_per_run = parsed_max_expand_seeds

        expand_http_error_window = 20
        raw_expand_http_error_window = os.getenv("BOT_EXPAND_HTTP_ERROR_WINDOW", "").strip()
        if raw_expand_http_error_window:
            parsed_expand_http_error_window = int(raw_expand_http_error_window)
            if parsed_expand_http_error_window < 1:
                raise EnvironmentError("BOT_EXPAND_HTTP_ERROR_WINDOW must be >= 1")
            expand_http_error_window = parsed_expand_http_error_window

        expand_http_error_threshold = 5
        raw_expand_http_error_threshold = os.getenv("BOT_EXPAND_HTTP_ERROR_THRESHOLD", "").strip()
        if raw_expand_http_error_threshold:
            parsed_expand_http_error_threshold = int(raw_expand_http_error_threshold)
            if parsed_expand_http_error_threshold < 1:
                raise EnvironmentError("BOT_EXPAND_HTTP_ERROR_THRESHOLD must be >= 1")
            expand_http_error_threshold = parsed_expand_http_error_threshold

        expand_fallback_to_followers = os.getenv("BOT_EXPAND_FALLBACK_TO_FOLLOWERS", "false").strip().lower() in {"1", "true", "yes", "on"}

        discovery_mode = os.getenv("BOT_DISCOVERY_MODE", "followers").strip().lower() or "followers"
        if discovery_mode not in {"followers", "expand"}:
            raise EnvironmentError("BOT_DISCOVERY_MODE must be one of: followers, expand")

        follow_job_max_attempts = 3
        raw_follow_job_max_attempts = os.getenv("BOT_FOLLOW_JOB_MAX_ATTEMPTS", "").strip()
        if raw_follow_job_max_attempts:
            parsed_attempts = int(raw_follow_job_max_attempts)
            if parsed_attempts < 1:
                raise EnvironmentError("BOT_FOLLOW_JOB_MAX_ATTEMPTS must be >= 1")
            follow_job_max_attempts = parsed_attempts

        github_app_private_key_command_timeout_seconds = 10
        raw_private_key_command_timeout = os.getenv("BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS", "").strip()
        if raw_private_key_command_timeout:
            parsed_timeout = int(raw_private_key_command_timeout)
            if parsed_timeout < 1:
                raise EnvironmentError("BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS must be >= 1")
            github_app_private_key_command_timeout_seconds = parsed_timeout

        github_app_token_refresh_skew_seconds = 60
        raw_github_app_token_refresh_skew = os.getenv("BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS", "").strip()
        if raw_github_app_token_refresh_skew:
            parsed_skew = int(raw_github_app_token_refresh_skew)
            if parsed_skew < 0:
                raise EnvironmentError("BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS must be >= 0")
            github_app_token_refresh_skew_seconds = parsed_skew

        verify_follow_after_put = os.getenv("BOT_VERIFY_FOLLOW_AFTER_PUT", "true").strip().lower() not in {
            "0",
            "false",
            "no",
            "off",
        }

        follow_verify_max_retries = 2
        raw_follow_verify_max_retries = os.getenv("BOT_FOLLOW_VERIFY_MAX_RETRIES", "").strip()
        if raw_follow_verify_max_retries:
            parsed_follow_verify_max_retries = int(raw_follow_verify_max_retries)
            if parsed_follow_verify_max_retries < 1:
                raise EnvironmentError("BOT_FOLLOW_VERIFY_MAX_RETRIES must be >= 1")
            follow_verify_max_retries = parsed_follow_verify_max_retries

        follow_verify_retry_delay_seconds = 1.0
        raw_follow_verify_retry_delay_seconds = os.getenv("BOT_FOLLOW_VERIFY_RETRY_DELAY_SECONDS", "").strip()
        if raw_follow_verify_retry_delay_seconds:
            parsed_follow_verify_retry_delay_seconds = float(raw_follow_verify_retry_delay_seconds)
            if parsed_follow_verify_retry_delay_seconds < 0:
                raise EnvironmentError("BOT_FOLLOW_VERIFY_RETRY_DELAY_SECONDS must be >= 0")
            follow_verify_retry_delay_seconds = parsed_follow_verify_retry_delay_seconds

        otel_enabled = os.getenv("BOT_OTEL_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
        otel_service_name = os.getenv("OTEL_SERVICE_NAME", "github_follower_bot").strip() or "github_follower_bot"
        otel_exporter_otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip() or None

        cosign_key_ref = os.getenv("COSIGN_KEY_REF", "").strip() or None
        cosign_enabled = os.getenv("BOT_COSIGN_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
        require_github_app_auth = os.getenv("BOT_REQUIRE_GITHUB_APP_AUTH", "false").strip().lower() in {"1", "true", "yes", "on"}
        gui_enabled = os.getenv("BOT_GUI_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
        gui_host = os.getenv("BOT_GUI_HOST", "127.0.0.1").strip() or "127.0.0.1"
        gui_port_raw = os.getenv("BOT_GUI_PORT", "8081").strip() or "8081"
        gui_port = int(gui_port_raw)
        if gui_port <= 0:
            raise EnvironmentError("BOT_GUI_PORT must be >= 1")
        gui_locale = os.getenv("BOT_GUI_LOCALE", "en").strip().lower() or "en"

        auth_mode_env = os.getenv("BOT_AUTH_MODE", "").strip().lower()
        auth_mode = "pat"

        if auth_mode_env:
            if auth_mode_env not in {"pat", "github_app_installation_token", "github_app"}:
                raise EnvironmentError("BOT_AUTH_MODE must be one of: pat, github_app_installation_token, github_app")
            auth_mode = auth_mode_env

        if auth_mode == "github_app_installation_token":
            if not app_installation_token:
                raise EnvironmentError("BOT_AUTH_MODE=github_app_installation_token requires GITHUB_APP_INSTALLATION_TOKEN")
            github_token = app_installation_token
        elif auth_mode == "github_app":
            required_missing = [
                name
                for name, value in {
                    "GITHUB_APP_ID": github_app_id,
                    "GITHUB_APP_INSTALLATION_ID": github_app_installation_id,
                    "GITHUB_APP_PRIVATE_KEY*": (
                        github_app_private_key or github_app_private_key_file or github_app_private_key_command
                    ),
                }.items()
                if not value
            ]
            if required_missing:
                missing_str = ", ".join(required_missing)
                raise EnvironmentError(f"BOT_AUTH_MODE=github_app requires: {missing_str}")
            github_token = "__github_app_runtime_token__"
        if not github_user or not github_token:
            raise EnvironmentError(
                "Missing GITHUB_USER and auth token. "
                "Set PERSONAL_GITHUB_TOKEN (legacy-compatible default), "
                "or set BOT_AUTH_MODE=github_app_installation_token with GITHUB_APP_INSTALLATION_TOKEN, "
                "or set BOT_AUTH_MODE=github_app with app credentials."
            )
        if require_github_app_auth and auth_mode != "github_app":
            raise EnvironmentError("BOT_REQUIRE_GITHUB_APP_AUTH=true requires BOT_AUTH_MODE=github_app")

        return cls(
            github_user=github_user,
            github_token=github_token,
            db_engine=db_engine,
            db_path=db_path,
            postgres_dsn=postgres_dsn,
            dry_run=dry_run,
            max_follows_per_run=max_follows_per_run,
            max_forks_per_run=max_forks_per_run,
            max_candidates_per_run=max_candidates_per_run,
            max_api_calls_per_run=max_api_calls_per_run,
            max_expand_seeds_per_run=max_expand_seeds_per_run,
            discovery_mode=discovery_mode,
            expand_http_error_window=expand_http_error_window,
            expand_http_error_threshold=expand_http_error_threshold,
            expand_fallback_to_followers=expand_fallback_to_followers,
            cleanup_legacy_files=cleanup_legacy_files,
            auth_mode=auth_mode,
            release_manifest_signing_key=release_manifest_signing_key,
            release_manifest_require_signature=release_manifest_require_signature,
            release_manifest_max_age_seconds=release_manifest_max_age_seconds,
            github_app_id=github_app_id,
            github_app_installation_id=github_app_installation_id,
            github_app_private_key=github_app_private_key,
            github_app_private_key_file=github_app_private_key_file,
            github_app_private_key_file_candidates=github_app_private_key_file_candidates,
            github_app_private_key_command=github_app_private_key_command,
            follow_job_max_attempts=follow_job_max_attempts,
            github_app_private_key_command_timeout_seconds=github_app_private_key_command_timeout_seconds,
            github_app_token_refresh_skew_seconds=github_app_token_refresh_skew_seconds,
            verify_follow_after_put=verify_follow_after_put,
            follow_verify_max_retries=follow_verify_max_retries,
            follow_verify_retry_delay_seconds=follow_verify_retry_delay_seconds,
            otel_enabled=otel_enabled,
            otel_service_name=otel_service_name,
            otel_exporter_otlp_endpoint=otel_exporter_otlp_endpoint,
            cosign_key_ref=cosign_key_ref,
            cosign_enabled=cosign_enabled,
            require_github_app_auth=require_github_app_auth,
            gui_enabled=gui_enabled,
            gui_host=gui_host,
            gui_port=gui_port,
            gui_locale=gui_locale,
        )


def launch_gui(config: "BotConfig", logger: logging.Logger, storage: StoragePort) -> tuple[int, dict[str, Any]]:
    if not config.gui_enabled:
        return 2, {"event": "gui_disabled", "error": "set BOT_GUI_ENABLED=true to start GUI"}

    try:
        __import__("nicegui")
    except ModuleNotFoundError:
        return 2, {
            "event": "gui_dependency_missing",
            "error": "NiceGUI is not installed. Install with: pip install nicegui",
        }

    adapter = ControlPlaneAdapter(
        config=config,
        logger=logger,
        storage=storage,
        build_storage=build_storage,
        build_follow_back_service=build_follow_back_service,
        handle_default_run_command=handle_default_run_command,
        handle_resume_command=handle_resume_command,
        handle_abort_command=handle_abort_command,
        handle_control_plane_status=handle_control_plane_status,
        execute_run=execute_run,
        doctor_report=doctor_report,
        resolve_command_output_path=resolve_command_output_path,
    )
    run_gui(adapter, host=config.gui_host, port=config.gui_port, locale=config.gui_locale)
    return 0, {"event": "gui_started", "host": config.gui_host, "port": config.gui_port, "locale": config.gui_locale}


class SQLiteStorageAdapter:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        ensure_parent_dir(db_path)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        enforce_runtime_file_permissions(db_path, "db")
        self._configure()
        self._migrate()

    def _configure(self) -> None:
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")

    def _migrate(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS bot_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              started_at TEXT NOT NULL,
              finished_at TEXT,
              status TEXT NOT NULL,
              trace_id TEXT,
              followers_fetched INTEGER NOT NULL DEFAULT 0,
              followers_followed INTEGER NOT NULL DEFAULT 0,
              error_message TEXT
            );

            CREATE TABLE IF NOT EXISTS followers (
              github_login TEXT PRIMARY KEY,
              first_seen_at TEXT NOT NULL,
              last_seen_at TEXT NOT NULL,
              followed INTEGER NOT NULL DEFAULT 0,
              followed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS follow_actions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER NOT NULL,
              github_login TEXT NOT NULL,
              success INTEGER NOT NULL,
              status_code INTEGER,
              error_message TEXT,
              discovery_context TEXT,
              created_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES bot_runs(id)
            );

            CREATE TABLE IF NOT EXISTS settings (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS security_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER,
              event TEXT NOT NULL,
              details TEXT,
              created_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES bot_runs(id)
            );

            CREATE TABLE IF NOT EXISTS rate_limit_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER,
              remaining INTEGER,
              reset_at INTEGER,
              captured_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES bot_runs(id)
            );

            CREATE TABLE IF NOT EXISTS follow_jobs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER NOT NULL,
              github_login TEXT NOT NULL,
              status TEXT NOT NULL,
              attempts INTEGER NOT NULL DEFAULT 0,
              last_error TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              UNIQUE(run_id, github_login),
              FOREIGN KEY(run_id) REFERENCES bot_runs(id)
            );

            CREATE TABLE IF NOT EXISTS repository_catalog (
              full_name TEXT PRIMARY KEY,
              owner_login TEXT NOT NULL,
              repo_name TEXT NOT NULL,
              is_fork INTEGER NOT NULL DEFAULT 0,
              parent_full_name TEXT,
              source_root_full_name TEXT,
              last_seen_at TEXT NOT NULL,
              repo_updated_at TEXT,
              stargazers_count INTEGER,
              forks_count INTEGER,
              watchers_count INTEGER,
              open_issues_count INTEGER,
              language TEXT,
              default_branch TEXT,
              archived INTEGER,
              disabled INTEGER,
              pushed_at TEXT,
              last_forked_at TEXT,
              last_fork_status TEXT,
              last_fork_error TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_followers_followed ON followers(followed);
            CREATE INDEX IF NOT EXISTS idx_follow_actions_run ON follow_actions(run_id);
            CREATE INDEX IF NOT EXISTS idx_rate_limit_snapshots_run ON rate_limit_snapshots(run_id);
            CREATE INDEX IF NOT EXISTS idx_follow_jobs_run_status ON follow_jobs(run_id, status);
            CREATE INDEX IF NOT EXISTS idx_repository_catalog_owner ON repository_catalog(owner_login);
            """
        )

    def upsert_repository_catalog_entry(
        self,
        *,
        full_name: str,
        owner_login: str,
        repo_name: str,
        is_fork: bool,
        parent_full_name: str | None,
        source_root_full_name: str | None,
        repo_updated_at: str | None,
        stargazers_count: int | None,
        forks_count: int | None,
        watchers_count: int | None,
        open_issues_count: int | None,
        language: str | None,
        default_branch: str | None,
        archived: bool | None,
        disabled: bool | None,
        pushed_at: str | None,
        last_forked_at: str | None,
        last_fork_status: str | None,
        last_fork_error: str | None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT INTO repository_catalog(
              full_name, owner_login, repo_name, is_fork, parent_full_name, source_root_full_name,
              last_seen_at, repo_updated_at, stargazers_count, forks_count, watchers_count,
              open_issues_count, language, default_branch, archived, disabled, pushed_at,
              last_forked_at, last_fork_status, last_fork_error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(full_name) DO UPDATE SET
              owner_login=excluded.owner_login,
              repo_name=excluded.repo_name,
              is_fork=excluded.is_fork,
              parent_full_name=excluded.parent_full_name,
              source_root_full_name=excluded.source_root_full_name,
              last_seen_at=excluded.last_seen_at,
              repo_updated_at=excluded.repo_updated_at,
              stargazers_count=excluded.stargazers_count,
              forks_count=excluded.forks_count,
              watchers_count=excluded.watchers_count,
              open_issues_count=excluded.open_issues_count,
              language=excluded.language,
              default_branch=excluded.default_branch,
              archived=excluded.archived,
              disabled=excluded.disabled,
              pushed_at=excluded.pushed_at,
              last_forked_at=excluded.last_forked_at,
              last_fork_status=excluded.last_fork_status,
              last_fork_error=excluded.last_fork_error
            """,
            (
                full_name,
                owner_login,
                repo_name,
                int(is_fork),
                parent_full_name,
                source_root_full_name,
                now,
                repo_updated_at,
                stargazers_count,
                forks_count,
                watchers_count,
                open_issues_count,
                language,
                default_branch,
                int(bool(archived)) if archived is not None else None,
                int(bool(disabled)) if disabled is not None else None,
                pushed_at,
                last_forked_at,
                last_fork_status,
                last_fork_error,
            ),
        )

        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(security_events)").fetchall()}
        if "run_id" not in columns:
            self.conn.execute("ALTER TABLE security_events ADD COLUMN run_id INTEGER")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_security_events_run ON security_events(run_id)")
        follow_action_columns = {row[1] for row in self.conn.execute("PRAGMA table_info(follow_actions)").fetchall()}
        if "discovery_context" not in follow_action_columns:
            self.conn.execute("ALTER TABLE follow_actions ADD COLUMN discovery_context TEXT")
        run_columns = {row[1] for row in self.conn.execute("PRAGMA table_info(bot_runs)").fetchall()}
        if "trace_id" not in run_columns:
            self.conn.execute("ALTER TABLE bot_runs ADD COLUMN trace_id TEXT")
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            ("schema_version", "sqlite-v1"),
        )
        self.conn.commit()

    def begin_run(self, trace_id: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cur = self.conn.execute("INSERT INTO bot_runs(started_at, status, trace_id) VALUES (?, ?, ?)", (now, "running", trace_id))
        self.conn.commit()
        return int(cur.lastrowid)

    def finish_run(self, run_id: int, followers_fetched: int, followers_followed: int, error_message: str | None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        status = "failed" if error_message else "completed"
        self.conn.execute(
            "UPDATE bot_runs SET finished_at=?, status=?, followers_fetched=?, followers_followed=?, error_message=? WHERE id=?",
            (now, status, followers_fetched, followers_followed, error_message, run_id),
        )
        self.conn.commit()

    def upsert_follower_seen(self, username: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO followers(github_login, first_seen_at, last_seen_at) VALUES (?, ?, ?) "
            "ON CONFLICT(github_login) DO UPDATE SET last_seen_at=excluded.last_seen_at",
            (username, now, now),
        )

    def is_followed(self, username: str) -> bool:
        row = self.conn.execute("SELECT followed FROM followers WHERE github_login=?", (username,)).fetchone()
        return bool(row and row["followed"])

    def has_successful_follow_action(self, username: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM follow_actions WHERE github_login=? AND success=1 LIMIT 1",
            (username,),
        ).fetchone()
        return bool(row)

    def mark_followed(self, username: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute("UPDATE followers SET followed=1, followed_at=? WHERE github_login=?", (now, username))

    def add_follow_action(
        self,
        run_id: int,
        username: str,
        success: bool,
        status_code: int | None,
        error_message: str | None,
        discovery_context: dict[str, object] | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO follow_actions(run_id, github_login, success, status_code, error_message, discovery_context, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, username, int(success), status_code, error_message, json.dumps(discovery_context) if discovery_context else None, now),
        )

    def add_security_event(self, event: str, details: str | None, run_id: int | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO security_events(run_id, event, details, created_at) VALUES (?, ?, ?, ?)",
            (run_id, event, details, now),
        )

    def add_rate_limit_snapshot(self, run_id: int, remaining: int | None, reset_at: int | None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO rate_limit_snapshots(run_id, remaining, reset_at, captured_at) VALUES (?, ?, ?, ?)",
            (run_id, remaining, reset_at, now),
        )

    def export_prometheus_metrics(self) -> str:
        stats = self.get_stats()
        pending = max(stats["followers_total"] - stats["followers_followed"], 0)

        actions_success = self.conn.execute("SELECT COUNT(*) c FROM follow_actions WHERE success=1").fetchone()["c"]
        actions_failed = self.conn.execute("SELECT COUNT(*) c FROM follow_actions WHERE success=0").fetchone()["c"]
        runs_completed = self.conn.execute("SELECT COUNT(*) c FROM bot_runs WHERE status='completed'").fetchone()["c"]
        runs_failed = self.conn.execute("SELECT COUNT(*) c FROM bot_runs WHERE status='failed'").fetchone()["c"]
        last_rate_limit = self.conn.execute(
            "SELECT remaining, reset_at FROM rate_limit_snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()

        lines = [
            "# HELP github_follower_bot_followers_total Total followers seen in persistence.",
            "# TYPE github_follower_bot_followers_total gauge",
            f"github_follower_bot_followers_total {int(stats['followers_total'])}",
            "# HELP github_follower_bot_followers_followed Total followers already followed.",
            "# TYPE github_follower_bot_followers_followed gauge",
            f"github_follower_bot_followers_followed {int(stats['followers_followed'])}",
            "# HELP github_follower_bot_followers_pending Total followers pending follow-back.",
            "# TYPE github_follower_bot_followers_pending gauge",
            f"github_follower_bot_followers_pending {int(pending)}",
            "# HELP github_follower_bot_runs_total Total bot runs by status.",
            "# TYPE github_follower_bot_runs_total counter",
            f'github_follower_bot_runs_total{{status="completed"}} {int(runs_completed)}',
            f'github_follower_bot_runs_total{{status="failed"}} {int(runs_failed)}',
            "# HELP github_follower_bot_follow_actions_total Total follow actions by result.",
            "# TYPE github_follower_bot_follow_actions_total counter",
            f'github_follower_bot_follow_actions_total{{result="success"}} {int(actions_success)}',
            f'github_follower_bot_follow_actions_total{{result="failed"}} {int(actions_failed)}',
        ]

        if last_rate_limit:
            remaining = 0 if last_rate_limit["remaining"] is None else int(last_rate_limit["remaining"])
            reset_at = 0 if last_rate_limit["reset_at"] is None else int(last_rate_limit["reset_at"])
            lines.extend(
                [
                    "# HELP github_follower_bot_rate_limit_remaining Last known GitHub core rate-limit remaining.",
                    "# TYPE github_follower_bot_rate_limit_remaining gauge",
                    f"github_follower_bot_rate_limit_remaining {remaining}",
                    "# HELP github_follower_bot_rate_limit_reset_at_unix Last known GitHub core rate-limit reset timestamp.",
                    "# TYPE github_follower_bot_rate_limit_reset_at_unix gauge",
                    f"github_follower_bot_rate_limit_reset_at_unix {reset_at}",
                ]
            )

        return "\n".join(lines) + "\n"

    def upsert_follow_job(
        self,
        run_id: int,
        username: str,
        status: str,
        last_error: str | None = None,
        *,
        increment_attempt: bool = False,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        attempts_initial = 1 if increment_attempt else 0
        attempts_increment = 1 if increment_attempt else 0
        self.conn.execute(
            """
            INSERT INTO follow_jobs(run_id, github_login, status, attempts, last_error, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id, github_login) DO UPDATE SET
              status=excluded.status,
              attempts=follow_jobs.attempts + ?,
              last_error=excluded.last_error,
              updated_at=excluded.updated_at
            """,
            (run_id, username, status, attempts_initial, last_error, now, now, attempts_increment),
        )

    def get_follow_job_stats(self, run_id: int | None = None) -> dict[str, int]:
        params: tuple = ()
        where = ""
        if run_id is not None:
            where = "WHERE run_id=?"
            params = (run_id,)

        rows = self.conn.execute(
            f"SELECT status, COUNT(*) c FROM follow_jobs {where} GROUP BY status",
            params,
        ).fetchall()
        stats = {"pending": 0, "done": 0, "failed": 0, "dead_letter": 0}
        for row in rows:
            key = str(row["status"])
            if key in stats:
                stats[key] = int(row["c"])
        stats["total"] = sum(stats.values())
        return stats

    def fetch_follow_jobs(self, run_id: int, statuses: tuple[str, ...] = ("pending",), limit: int = 100) -> list[sqlite3.Row]:
        placeholders = ",".join("?" for _ in statuses)
        params = (run_id, *statuses, limit)
        query = (
            f"SELECT github_login, status, attempts, last_error FROM follow_jobs "
            f"WHERE run_id=? AND status IN ({placeholders}) ORDER BY id ASC LIMIT ?"
        )
        return self.conn.execute(query, params).fetchall()

    def get_follow_job(self, run_id: int, username: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT github_login, status, attempts, last_error FROM follow_jobs WHERE run_id=? AND github_login=?",
            (run_id, username),
        ).fetchone()


    def get_run(self, run_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT id, started_at, finished_at, status, followers_fetched, followers_followed, error_message, trace_id FROM bot_runs WHERE id=?",
            (run_id,),
        ).fetchone()
        return dict(row) if row else None

    def abort_run(self, run_id: int, reason: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        cur = self.conn.execute(
            "UPDATE bot_runs SET finished_at=?, status='aborted', error_message=? WHERE id=? AND status='running'",
            (now, reason, run_id),
        )
        return cur.rowcount > 0

    @staticmethod
    def _build_manifest_signing_payload(artifacts: list[dict[str, str | int]]) -> str:
        stable = [
            {
                "path": str(item.get("path", "")),
                "sha256": str(item.get("sha256", "")),
                "size": int(item.get("size", 0)),
            }
            for item in artifacts
        ]
        stable.sort(key=lambda x: x["path"])
        return json.dumps(stable, sort_keys=True, separators=(",", ":"))

    def export_release_manifest(self, signing_key: str | None = None) -> dict:
        root = Path(__file__).resolve().parent
        files = ["bot.py", "check_all_followers.py", "README.md", "requirements.txt"]
        artifacts: list[dict[str, str | int]] = []
        for rel in files:
            path = root / rel
            if not path.exists():
                continue
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            artifacts.append({"path": rel, "sha256": digest, "size": len(data)})

        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "algorithm": "sha256",
            "artifacts": artifacts,
        }

        if signing_key:
            serialized = self._build_manifest_signing_payload(artifacts)
            signature = hmac.new(signing_key.encode("utf-8"), serialized.encode("utf-8"), hashlib.sha256).hexdigest()
            payload["signature"] = {"method": "hmac-sha256", "value": signature}

        return payload

    def verify_release_manifest(
        self,
        manifest_path: str,
        signing_key: str | None = None,
        require_signature: bool = False,
        max_age_seconds: int | None = None,
    ) -> dict:
        payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        artifacts = payload.get("artifacts", [])
        generated_at_raw = payload.get("generated_at")
        verified = 0
        mismatches: list[dict[str, str]] = []
        root = Path(__file__).resolve().parent

        for item in artifacts:
            rel = str(item.get("path", ""))
            expected = str(item.get("sha256", ""))
            path = root / rel
            if not rel or not path.exists():
                mismatches.append({"path": rel, "reason": "missing_file"})
                continue
            current = hashlib.sha256(path.read_bytes()).hexdigest()
            if current != expected:
                mismatches.append({"path": rel, "reason": "digest_mismatch"})
                continue
            verified += 1


        age_state = {"checked": False, "max_age_seconds": max_age_seconds, "manifest_age_seconds": None, "reason": None}
        if max_age_seconds is not None:
            age_state["checked"] = True
            try:
                generated_dt = datetime.fromisoformat(str(generated_at_raw).replace("Z", "+00:00"))
                if generated_dt.tzinfo is None:
                    generated_dt = generated_dt.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                manifest_age_seconds = int((now - generated_dt).total_seconds())
                age_state["manifest_age_seconds"] = manifest_age_seconds
                if manifest_age_seconds < 0:
                    age_state["reason"] = "manifest_from_future"
                    mismatches.append({"path": "<manifest>", "reason": "manifest_from_future"})
                elif manifest_age_seconds > max_age_seconds:
                    age_state["reason"] = "manifest_expired"
                    mismatches.append({"path": "<manifest>", "reason": "manifest_expired"})
            except (TypeError, ValueError):
                age_state["reason"] = "invalid_generated_at"
                mismatches.append({"path": "<manifest>", "reason": "invalid_generated_at"})

        signature_state = {"required": bool(require_signature), "verified": None, "reason": None}
        signature_block = payload.get("signature")
        if not signature_block and require_signature:
            signature_state["verified"] = False
            signature_state["reason"] = "missing_signature"
            mismatches.append({"path": "<manifest>", "reason": "missing_signature"})
        if signature_block:
            signature_state["required"] = True
            method = str(signature_block.get("method", ""))
            expected_sig = str(signature_block.get("value", ""))
            if method != "hmac-sha256":
                signature_state["verified"] = False
                signature_state["reason"] = "unsupported_signature_method"
                mismatches.append({"path": "<manifest>", "reason": "unsupported_signature_method"})
            elif not signing_key:
                signature_state["verified"] = False
                signature_state["reason"] = "missing_signing_key"
                mismatches.append({"path": "<manifest>", "reason": "missing_signing_key"})
            else:
                serialized = self._build_manifest_signing_payload(artifacts)
                current_sig = hmac.new(signing_key.encode("utf-8"), serialized.encode("utf-8"), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(current_sig, expected_sig):
                    signature_state["verified"] = False
                    signature_state["reason"] = "signature_mismatch"
                    mismatches.append({"path": "<manifest>", "reason": "signature_mismatch"})
                else:
                    signature_state["verified"] = True

        return {
            "manifest_path": manifest_path,
            "verified": verified,
            "total": len(artifacts),
            "mismatches": mismatches,
            "signature": signature_state,
            "age": age_state,
            "ok": len(mismatches) == 0,
        }

    def export_sbom(self) -> dict:
        requirements_path = Path(__file__).with_name("requirements.txt")
        components: list[dict[str, str | None]] = []
        if requirements_path.exists():
            for raw in requirements_path.read_text(encoding="utf-8").splitlines():
                pkg = raw.strip()
                if not pkg or pkg.startswith("#"):
                    continue
                package_name = pkg.split("==")[0].strip()
                version = None
                try:
                    version = importlib_metadata.version(package_name)
                except importlib_metadata.PackageNotFoundError:
                    version = None
                components.append(
                    {
                        "name": package_name,
                        "version": version,
                        "purl": f"pkg:pypi/{package_name}@{version}" if version else f"pkg:pypi/{package_name}",
                    }
                )

        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": {"type": "application", "name": "GitHub_Follower_and_Fork_Bot_Automated-main"},
            },
            "components": components,
        }

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )

    def get_setting(self, key: str) -> str | None:
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def try_acquire_distributed_lock(self, lock_key: str, lock_until_epoch: int, now_epoch: int) -> bool:
        key = f"scheduler_lock:{lock_key}"
        cur = self.conn.execute("UPDATE settings SET value=? WHERE key=? AND CAST(value AS INTEGER) <= ?", (str(lock_until_epoch), key, now_epoch))
        if cur.rowcount == 1:
            self.commit()
            return True
        cur = self.conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (key, str(lock_until_epoch)))
        self.commit()
        return cur.rowcount == 1

    def release_distributed_lock(self, lock_key: str, expected_lock_until_epoch: int) -> bool:
        key = f"scheduler_lock:{lock_key}"
        cur = self.conn.execute("UPDATE settings SET value='0' WHERE key=? AND value=?", (key, str(expected_lock_until_epoch)))
        self.commit()
        return cur.rowcount == 1

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def get_table_counts(self, table_names: list[str]) -> dict[str, int]:
        return {
            table: int(self.conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"])
            for table in table_names
        }

    def check_connection(self) -> tuple[bool, str]:
        try:
            self.conn.execute("SELECT 1")
            return True, "ok"
        except sqlite3.Error as exc:
            return False, str(exc)

    def db_integrity_status(self) -> str:
        return str(self.conn.execute("PRAGMA integrity_check").fetchone()[0])

    def get_schema_version(self) -> str:
        return self.get_setting("schema_version") or "sqlite-v1"

    def storage_adapter_name(self) -> str:
        return "sqlite"

    def get_stats(self) -> dict[str, int]:
        followers_total = self.conn.execute("SELECT COUNT(*) c FROM followers").fetchone()["c"]
        followers_followed = self.conn.execute("SELECT COUNT(*) c FROM followers WHERE followed=1").fetchone()["c"]
        runs_total = self.conn.execute("SELECT COUNT(*) c FROM bot_runs").fetchone()["c"]
        security_events_total = self.conn.execute("SELECT COUNT(*) c FROM security_events").fetchone()["c"]
        return {
            "followers_total": int(followers_total),
            "followers_followed": int(followers_followed),
            "runs_total": int(runs_total),
            "security_events_total": int(security_events_total),
        }

    def get_last_run(self) -> dict | None:
        row = self.conn.execute(
            "SELECT id, started_at, finished_at, status, trace_id, followers_fetched, followers_followed, error_message "
            "FROM bot_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    def export_recent_audit(self, limit: int = 200) -> dict:
        run_rows = [dict(r) for r in self.conn.execute("SELECT * FROM bot_runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
        action_rows = [
            dict(r)
            for r in self.conn.execute(
                "SELECT id, run_id, github_login, success, status_code, error_message, discovery_context, created_at "
                "FROM follow_actions ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        ]
        security_rows = [
            dict(r)
            for r in self.conn.execute(
                "SELECT id, run_id, event, details, created_at FROM security_events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        ]
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "db_path": self.db_path,
            "runs": run_rows,
            "actions": action_rows,
            "security_events": security_rows,
        }

    def export_postgres_migration_profile(self) -> dict:
        tables = [
            "bot_runs",
            "followers",
            "follow_actions",
            "settings",
            "security_events",
            "rate_limit_snapshots",
            "follow_jobs",
            "repository_catalog",
        ]
        row_counts = {
            table: int(self.conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"])
            for table in tables
        }

        benchmark_samples = 50

        def timed_avg_ms(query: str, params: tuple = ()) -> float:
            elapsed: list[float] = []
            for _ in range(benchmark_samples):
                started = perf_counter()
                self.conn.execute(query, params).fetchone()
                elapsed.append((perf_counter() - started) * 1000)
            return round(sum(elapsed) / len(elapsed), 4)

        horizontal_scaling_profile = {
            "benchmark_samples": benchmark_samples,
            "avg_query_ms": {
                "followers_total_count": timed_avg_ms("SELECT COUNT(*) FROM followers"),
                "pending_follow_jobs": timed_avg_ms("SELECT COUNT(*) FROM follow_jobs WHERE status='pending'"),
                "latest_run_lookup": timed_avg_ms("SELECT id FROM bot_runs ORDER BY id DESC LIMIT 1"),
            },
            "recommended_indexes_postgres": [
                "CREATE INDEX IF NOT EXISTS idx_follow_actions_run_id_created_at ON follow_actions(run_id, created_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_security_events_run_id_created_at ON security_events(run_id, created_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_follow_jobs_status_run_id ON follow_jobs(status, run_id);",
            ],
            "capacity_guidance": {
                "single_writer_recommended_up_to_runs": 1_000_000,
                "follow_jobs_rows_before_partitioning": 5_000_000,
                "note": "Use table partitioning for follow_jobs/follow_actions when sustained growth exceeds thresholds.",
            },
        }

        ddl = {
            "bot_runs": """
CREATE TABLE IF NOT EXISTS bot_runs (
  id BIGSERIAL PRIMARY KEY,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL,
  trace_id TEXT,
  followers_fetched INTEGER NOT NULL DEFAULT 0,
  followers_followed INTEGER NOT NULL DEFAULT 0,
  error_message TEXT
);
""".strip(),
            "followers": """
CREATE TABLE IF NOT EXISTS followers (
  github_login TEXT PRIMARY KEY,
  seen_at TIMESTAMPTZ NOT NULL,
  followed BOOLEAN NOT NULL DEFAULT FALSE,
  followed_at TIMESTAMPTZ
);
""".strip(),
            "follow_actions": """
CREATE TABLE IF NOT EXISTS follow_actions (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT REFERENCES bot_runs(id) ON DELETE SET NULL,
  github_login TEXT NOT NULL,
  success BOOLEAN NOT NULL,
  status_code INTEGER,
  error_message TEXT,
  discovery_context JSONB,
  created_at TIMESTAMPTZ NOT NULL
);
""".strip(),
            "settings": """
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
""".strip(),
            "security_events": """
CREATE TABLE IF NOT EXISTS security_events (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT REFERENCES bot_runs(id) ON DELETE SET NULL,
  event TEXT NOT NULL,
  details TEXT,
  created_at TIMESTAMPTZ NOT NULL
);
""".strip(),
            "rate_limit_snapshots": """
CREATE TABLE IF NOT EXISTS rate_limit_snapshots (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT REFERENCES bot_runs(id) ON DELETE SET NULL,
  remaining INTEGER,
  reset_epoch INTEGER,
  captured_at TIMESTAMPTZ NOT NULL
);
""".strip(),
            "follow_jobs": """
CREATE TABLE IF NOT EXISTS follow_jobs (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL REFERENCES bot_runs(id) ON DELETE CASCADE,
  github_login TEXT NOT NULL,
  status TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  UNIQUE (run_id, github_login)
);
CREATE INDEX IF NOT EXISTS idx_follow_jobs_status ON follow_jobs(status);
""".strip(),
            "repository_catalog": """
CREATE TABLE IF NOT EXISTS repository_catalog (
  full_name TEXT PRIMARY KEY,
  owner_login TEXT NOT NULL,
  repo_name TEXT NOT NULL,
  is_fork BOOLEAN NOT NULL DEFAULT FALSE,
  parent_full_name TEXT,
  source_root_full_name TEXT,
  last_seen_at TIMESTAMPTZ NOT NULL,
  repo_updated_at TIMESTAMPTZ,
  stargazers_count INTEGER,
  forks_count INTEGER,
  watchers_count INTEGER,
  open_issues_count INTEGER,
  language TEXT,
  default_branch TEXT,
  archived BOOLEAN,
  disabled BOOLEAN,
  pushed_at TIMESTAMPTZ,
  last_forked_at TIMESTAMPTZ,
  last_fork_status TEXT,
  last_fork_error TEXT
);
CREATE INDEX IF NOT EXISTS idx_repository_catalog_owner ON repository_catalog(owner_login);
""".strip(),
        }
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_engine": "sqlite",
            "target_engine": "postgresql",
            "tables": tables,
            "row_counts": row_counts,
            "ddl": ddl,
            "horizontal_scaling_profile": horizontal_scaling_profile,
            "migration_notes": [
                "Use COPY/UPSERT for followers/settings to preserve idempotency.",
                "Migrate bot_runs first, then dependent tables with run_id foreign keys.",
                "Create indexes and analyze tables after bulk load for query parity.",
            ],
        }


def issue_github_app_installation_token_details(
    app_id: str,
    installation_id: str,
    private_key_pem: str,
    session: requests.Session | None = None,
) -> tuple[str, int | None]:
    now = int(time.time())
    jwt_token = jwt.encode(
        {
            "iat": now - 60,
            "exp": now + 540,
            "iss": app_id,
        },
        private_key_pem,
        algorithm="RS256",
    )
    active_session = session or requests.Session()
    response = active_session.post(
        f"{API_BASE}/app/installations/{installation_id}/access_tokens",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {jwt_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"failed to issue GitHub App installation token status={response.status_code}")
    payload = response.json()
    token = str(payload.get("token") or "").strip()
    if not token:
        raise RuntimeError("GitHub App installation token response missing token")

    expires_at_raw = str(payload.get("expires_at") or "").strip()
    expires_at_epoch = None
    if expires_at_raw:
        expires_at_epoch = int(datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00")).timestamp())

    return token, expires_at_epoch


def issue_github_app_installation_token(app_id: str, installation_id: str, private_key_pem: str, session: requests.Session | None = None) -> str:
    token, _expires_at_epoch = issue_github_app_installation_token_details(
        app_id=app_id,
        installation_id=installation_id,
        private_key_pem=private_key_pem,
        session=session,
    )
    return token




class PostgresStorageAdapter:
    """PostgreSQL storage adapter (MVP) using DB-API compatible operations."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        try:
            import psycopg
            from psycopg.rows import dict_row
        except Exception as exc:  # pragma: no cover - environment dependent
            raise EnvironmentError("PostgreSQL engine requires psycopg. Install dependency 'psycopg[binary]'.") from exc
        self._psycopg = psycopg
        self.conn = psycopg.connect(dsn, row_factory=dict_row)
        self._configure()
        self._migrate()

    def _configure(self) -> None:
        self.conn.autocommit = False

    def _migrate(self) -> None:
        self.conn.execute(load_postgres_schema_sql())
        self.set_setting("schema_version", POSTGRES_SCHEMA_VERSION)
        self.commit()

    def begin_run(self, trace_id: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        row = self.conn.execute(
            "INSERT INTO bot_runs(started_at, status, trace_id) VALUES (%s, %s, %s) RETURNING id",
            (now, "running", trace_id),
        ).fetchone()
        self.commit()
        return int(row["id"])

    def finish_run(self, run_id: int, followers_fetched: int, followers_followed: int, error_message: str | None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        status = "failed" if error_message else "completed"
        self.conn.execute(
            "UPDATE bot_runs SET finished_at=%s, status=%s, followers_fetched=%s, followers_followed=%s, error_message=%s WHERE id=%s",
            (now, status, followers_fetched, followers_followed, error_message, run_id),
        )
        self.commit()

    def upsert_follower_seen(self, username: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO followers(github_login, first_seen_at, last_seen_at) VALUES (%s, %s, %s) "
            "ON CONFLICT(github_login) DO UPDATE SET last_seen_at=excluded.last_seen_at",
            (username, now, now),
        )

    def is_followed(self, username: str) -> bool:
        row = self.conn.execute("SELECT followed FROM followers WHERE github_login=%s", (username,)).fetchone()
        return bool(row and row["followed"])

    def has_successful_follow_action(self, username: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM follow_actions WHERE github_login=%s AND success=1 LIMIT 1",
            (username,),
        ).fetchone()
        return bool(row)

    def mark_followed(self, username: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute("UPDATE followers SET followed=1, followed_at=%s WHERE github_login=%s", (now, username))

    def add_follow_action(
        self,
        run_id: int,
        username: str,
        success: bool,
        status_code: int | None,
        error_message: str | None,
        discovery_context: dict[str, object] | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO follow_actions(run_id, github_login, success, status_code, error_message, discovery_context, created_at) VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)",
            (run_id, username, int(success), status_code, error_message, json.dumps(discovery_context) if discovery_context else None, now),
        )

    def add_security_event(self, event: str, details: str | None, run_id: int | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO security_events(run_id, event, details, created_at) VALUES (%s, %s, %s, %s)",
            (run_id, event, details, now),
        )

    def add_rate_limit_snapshot(self, run_id: int, remaining: int | None, reset_at: int | None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO rate_limit_snapshots(run_id, remaining, reset_at, captured_at) VALUES (%s, %s, %s, %s)",
            (run_id, remaining, reset_at, now),
        )

    def upsert_repository_catalog_entry(
        self,
        *,
        full_name: str,
        owner_login: str,
        repo_name: str,
        is_fork: bool,
        parent_full_name: str | None,
        source_root_full_name: str | None,
        repo_updated_at: str | None,
        stargazers_count: int | None,
        forks_count: int | None,
        watchers_count: int | None,
        open_issues_count: int | None,
        language: str | None,
        default_branch: str | None,
        archived: bool | None,
        disabled: bool | None,
        pushed_at: str | None,
        last_forked_at: str | None,
        last_fork_status: str | None,
        last_fork_error: str | None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT INTO repository_catalog(
              full_name, owner_login, repo_name, is_fork, parent_full_name, source_root_full_name,
              last_seen_at, repo_updated_at, stargazers_count, forks_count, watchers_count,
              open_issues_count, language, default_branch, archived, disabled, pushed_at,
              last_forked_at, last_fork_status, last_fork_error
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(full_name) DO UPDATE SET
              owner_login=excluded.owner_login,
              repo_name=excluded.repo_name,
              is_fork=excluded.is_fork,
              parent_full_name=excluded.parent_full_name,
              source_root_full_name=excluded.source_root_full_name,
              last_seen_at=excluded.last_seen_at,
              repo_updated_at=excluded.repo_updated_at,
              stargazers_count=excluded.stargazers_count,
              forks_count=excluded.forks_count,
              watchers_count=excluded.watchers_count,
              open_issues_count=excluded.open_issues_count,
              language=excluded.language,
              default_branch=excluded.default_branch,
              archived=excluded.archived,
              disabled=excluded.disabled,
              pushed_at=excluded.pushed_at,
              last_forked_at=excluded.last_forked_at,
              last_fork_status=excluded.last_fork_status,
              last_fork_error=excluded.last_fork_error
            """,
            (
                full_name,
                owner_login,
                repo_name,
                bool(is_fork),
                parent_full_name,
                source_root_full_name,
                now,
                repo_updated_at,
                stargazers_count,
                forks_count,
                watchers_count,
                open_issues_count,
                language,
                default_branch,
                archived,
                disabled,
                pushed_at,
                last_forked_at,
                last_fork_status,
                last_fork_error,
            ),
        )

    def export_prometheus_metrics(self) -> str:
        stats = self.get_stats()
        pending = max(stats["followers_total"] - stats["followers_followed"], 0)
        actions_success = self.conn.execute("SELECT COUNT(*) c FROM follow_actions WHERE success=1").fetchone()["c"]
        actions_failed = self.conn.execute("SELECT COUNT(*) c FROM follow_actions WHERE success=0").fetchone()["c"]
        latest = self.conn.execute(
            "SELECT remaining, reset_at FROM rate_limit_snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
        rate_remaining = int(latest["remaining"]) if latest and latest["remaining"] is not None else 0
        rate_reset = int(latest["reset_at"]) if latest and latest["reset_at"] is not None else 0
        lines = [
            "# HELP bot_followers_total Followers tracked in persistence.",
            "# TYPE bot_followers_total gauge",
            f"bot_followers_total {stats['followers_total']}",
            "# HELP bot_followers_followed_total Followers already followed.",
            "# TYPE bot_followers_followed_total gauge",
            f"bot_followers_followed_total {stats['followers_followed']}",
            "# HELP bot_followers_pending_total Followers pending follow action.",
            "# TYPE bot_followers_pending_total gauge",
            f"bot_followers_pending_total {pending}",
            "# HELP bot_runs_total Total bot runs recorded.",
            "# TYPE bot_runs_total counter",
            f"bot_runs_total {stats['runs_total']}",
            "# HELP bot_follow_actions_success_total Successful follow actions.",
            "# TYPE bot_follow_actions_success_total counter",
            f"bot_follow_actions_success_total {actions_success}",
            "# HELP bot_follow_actions_failed_total Failed follow actions.",
            "# TYPE bot_follow_actions_failed_total counter",
            f"bot_follow_actions_failed_total {actions_failed}",
            "# HELP bot_security_events_total Security events recorded.",
            "# TYPE bot_security_events_total counter",
            f"bot_security_events_total {stats['security_events_total']}",
            "# HELP bot_rate_limit_remaining Latest observed GitHub rate limit remaining.",
            "# TYPE bot_rate_limit_remaining gauge",
            f"bot_rate_limit_remaining {rate_remaining}",
            "# HELP bot_rate_limit_reset_epoch Latest observed GitHub rate limit reset epoch.",
            "# TYPE bot_rate_limit_reset_epoch gauge",
            f"bot_rate_limit_reset_epoch {rate_reset}",
        ]
        return "\n".join(lines) + "\n"

    def upsert_follow_job(self, run_id: int, username: str, status: str, error_message: str | None = None, increment_attempt: bool = False) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT INTO follow_jobs(run_id, github_login, status, attempts, last_error, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(run_id, github_login) DO UPDATE SET
              status=EXCLUDED.status,
              attempts=CASE WHEN %s THEN follow_jobs.attempts + 1 ELSE follow_jobs.attempts END,
              last_error=EXCLUDED.last_error,
              updated_at=EXCLUDED.updated_at
            """,
            (run_id, username, status, 1 if increment_attempt else 0, error_message, now, now, increment_attempt),
        )

    def get_follow_job_stats(self, run_id: int | None = None) -> dict[str, int]:
        params: list[object] = []
        where = ""
        if run_id is not None:
            where = "WHERE run_id = %s"
            params.append(run_id)
        rows = self.conn.execute(
            f"SELECT status, COUNT(*) as c FROM follow_jobs {where} GROUP BY status",
            tuple(params),
        ).fetchall()
        payload = {"pending": 0, "failed": 0, "done": 0, "dead_letter": 0}
        for row in rows:
            payload[str(row["status"])] = int(row["c"])
        return payload

    def fetch_follow_jobs(self, run_id: int, statuses: tuple[str, ...] = ("pending",), limit: int = 100) -> list[dict]:
        placeholders = ",".join(["%s"] * len(statuses))
        rows = self.conn.execute(
            f"SELECT run_id, github_login, status, attempts, last_error FROM follow_jobs WHERE run_id=%s AND status IN ({placeholders}) ORDER BY id ASC LIMIT %s",
            (run_id, *statuses, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_follow_job(self, run_id: int, username: str) -> dict | None:
        row = self.conn.execute(
            "SELECT run_id, github_login, status, attempts, last_error FROM follow_jobs WHERE run_id=%s AND github_login=%s",
            (run_id, username),
        ).fetchone()
        return dict(row) if row else None


    def get_run(self, run_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT id, started_at, finished_at, status, followers_fetched, followers_followed, error_message, trace_id FROM bot_runs WHERE id=%s",
            (run_id,),
        ).fetchone()
        return dict(row) if row else None

    def abort_run(self, run_id: int, reason: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        row = self.conn.execute(
            "UPDATE bot_runs SET finished_at=%s, status='aborted', error_message=%s WHERE id=%s AND status='running' RETURNING id",
            (now, reason, run_id),
        ).fetchone()
        return bool(row)

    @staticmethod
    def _build_manifest_signing_payload(artifacts: list[dict[str, str | int]]) -> str:
        canonical = [
            {
                "path": str(item["path"]),
                "size": int(item["size"]),
                "sha256": str(item["sha256"]),
            }
            for item in artifacts
        ]
        return json.dumps(canonical, separators=(",", ":"), sort_keys=True)

    def export_release_manifest(self, signing_key: str | None = None) -> dict:
        root = Path(__file__).resolve().parent
        files = ["bot.py", "check_all_followers.py", "README.md", "requirements.txt"]
        artifacts: list[dict[str, str | int]] = []
        for rel in files:
            path = root / rel
            if not path.exists():
                continue
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            artifacts.append({"path": rel, "sha256": digest, "size": len(data)})

        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "algorithm": "sha256",
            "artifacts": artifacts,
        }
        if signing_key:
            serialized = self._build_manifest_signing_payload(artifacts)
            signature = hmac.new(signing_key.encode("utf-8"), serialized.encode("utf-8"), hashlib.sha256).hexdigest()
            payload["signature"] = {"method": "hmac-sha256", "value": signature}
        return payload

    def verify_release_manifest(self, manifest_path: str, signing_key: str | None = None, require_signature: bool = False, max_age_seconds: int | None = None) -> dict:
        payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        artifacts = payload.get("artifacts", [])
        generated_at_raw = payload.get("generated_at")
        verified = 0
        mismatches: list[dict[str, str]] = []
        root = Path(__file__).resolve().parent
        for item in artifacts:
            rel = str(item.get("path", ""))
            expected = str(item.get("sha256", ""))
            path = root / rel
            if not rel or not path.exists():
                mismatches.append({"path": rel, "reason": "missing_file"})
                continue
            current = hashlib.sha256(path.read_bytes()).hexdigest()
            if current != expected:
                mismatches.append({"path": rel, "reason": "digest_mismatch"})
                continue
            verified += 1
        age_state = {"checked": False, "max_age_seconds": max_age_seconds, "manifest_age_seconds": None, "reason": None}
        if max_age_seconds is not None:
            age_state["checked"] = True
            try:
                generated_dt = datetime.fromisoformat(str(generated_at_raw).replace("Z", "+00:00"))
                if generated_dt.tzinfo is None:
                    generated_dt = generated_dt.replace(tzinfo=timezone.utc)
                manifest_age_seconds = int((datetime.now(timezone.utc) - generated_dt).total_seconds())
                age_state["manifest_age_seconds"] = manifest_age_seconds
                if manifest_age_seconds < 0:
                    age_state["reason"] = "manifest_from_future"
                    mismatches.append({"path": "<manifest>", "reason": "manifest_from_future"})
                elif manifest_age_seconds > max_age_seconds:
                    age_state["reason"] = "manifest_expired"
                    mismatches.append({"path": "<manifest>", "reason": "manifest_expired"})
            except (TypeError, ValueError):
                age_state["reason"] = "invalid_generated_at"
                mismatches.append({"path": "<manifest>", "reason": "invalid_generated_at"})
        signature_state = {"required": bool(require_signature), "verified": None, "reason": None}
        signature_block = payload.get("signature")
        if not signature_block and require_signature:
            signature_state["verified"] = False
            signature_state["reason"] = "missing_signature"
            mismatches.append({"path": "<manifest>", "reason": "missing_signature"})
        if signature_block:
            signature_state["required"] = True
            method = str(signature_block.get("method", ""))
            expected_sig = str(signature_block.get("value", ""))
            if method != "hmac-sha256":
                signature_state["verified"] = False
                signature_state["reason"] = "unsupported_signature_method"
                mismatches.append({"path": "<manifest>", "reason": "unsupported_signature_method"})
            elif not signing_key:
                signature_state["verified"] = False
                signature_state["reason"] = "missing_signing_key"
                mismatches.append({"path": "<manifest>", "reason": "missing_signing_key"})
            else:
                serialized = self._build_manifest_signing_payload(artifacts)
                current_sig = hmac.new(signing_key.encode("utf-8"), serialized.encode("utf-8"), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(current_sig, expected_sig):
                    signature_state["verified"] = False
                    signature_state["reason"] = "signature_mismatch"
                    mismatches.append({"path": "<manifest>", "reason": "signature_mismatch"})
                else:
                    signature_state["verified"] = True
        return {
            "manifest_path": manifest_path,
            "verified": verified,
            "total": len(artifacts),
            "mismatches": mismatches,
            "signature": signature_state,
            "age": age_state,
            "ok": len(mismatches) == 0,
        }

    def export_sbom(self) -> dict:
        requirements_path = Path(__file__).with_name("requirements.txt")
        components: list[dict[str, str | None]] = []
        if requirements_path.exists():
            for raw in requirements_path.read_text(encoding="utf-8").splitlines():
                pkg = raw.strip()
                if not pkg or pkg.startswith("#"):
                    continue
                package_name = pkg.split("==")[0].strip()
                try:
                    version = importlib_metadata.version(package_name)
                except importlib_metadata.PackageNotFoundError:
                    version = None
                components.append({
                    "name": package_name,
                    "version": version,
                    "purl": f"pkg:pypi/{package_name}@{version}" if version else f"pkg:pypi/{package_name}",
                })
        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": {"type": "application", "name": "GitHub_Follower_and_Fork_Bot_Automated-main"},
            },
            "components": components,
        }

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES (%s, %s) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value",
            (key, value),
        )

    def get_setting(self, key: str) -> str | None:
        row = self.conn.execute("SELECT value FROM settings WHERE key=%s", (key,)).fetchone()
        return str(row["value"]) if row else None

    def try_acquire_distributed_lock(self, lock_key: str, lock_until_epoch: int, now_epoch: int) -> bool:
        key = f"scheduler_lock:{lock_key}"
        cur = self.conn.execute(
            "UPDATE settings SET value=%s WHERE key=%s AND CAST(value AS BIGINT) <= %s",
            (str(lock_until_epoch), key, now_epoch),
        )
        if cur.rowcount == 1:
            self.commit()
            return True
        cur = self.conn.execute(
            "INSERT INTO settings(key, value) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (key, str(lock_until_epoch)),
        )
        self.commit()
        return cur.rowcount == 1

    def release_distributed_lock(self, lock_key: str, expected_lock_until_epoch: int) -> bool:
        key = f"scheduler_lock:{lock_key}"
        cur = self.conn.execute(
            "UPDATE settings SET value='0' WHERE key=%s AND value=%s",
            (key, str(expected_lock_until_epoch)),
        )
        self.commit()
        return cur.rowcount == 1

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def get_stats(self) -> dict[str, int]:
        followers_total = self.conn.execute("SELECT COUNT(*) c FROM followers").fetchone()["c"]
        followers_followed = self.conn.execute("SELECT COUNT(*) c FROM followers WHERE followed=1").fetchone()["c"]
        runs_total = self.conn.execute("SELECT COUNT(*) c FROM bot_runs").fetchone()["c"]
        security_events_total = self.conn.execute("SELECT COUNT(*) c FROM security_events").fetchone()["c"]
        return {
            "followers_total": int(followers_total),
            "followers_followed": int(followers_followed),
            "runs_total": int(runs_total),
            "security_events_total": int(security_events_total),
        }

    def get_last_run(self) -> dict | None:
        row = self.conn.execute("SELECT * FROM bot_runs ORDER BY id DESC LIMIT 1").fetchone()
        return dict(row) if row else None

    def export_recent_audit(self, limit: int = 200) -> dict:
        runs = [dict(row) for row in self.conn.execute("SELECT * FROM bot_runs ORDER BY id DESC LIMIT %s", (limit,)).fetchall()]
        actions = [dict(row) for row in self.conn.execute("SELECT * FROM follow_actions ORDER BY id DESC LIMIT %s", (limit,)).fetchall()]
        events = [dict(row) for row in self.conn.execute("SELECT * FROM security_events ORDER BY id DESC LIMIT %s", (limit,)).fetchall()]
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "runs": runs,
            "actions": actions,
            "security_events": events,
        }

    def export_postgres_migration_profile(self) -> dict:
        table_counts = self.get_table_counts(["bot_runs", "followers", "follow_actions", "security_events", "follow_jobs", "rate_limit_snapshots"])
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_engine": "postgres",
            "target_engine": "postgresql",
            "db_path": self.dsn,
            "tables": table_counts,
            "horizontal_scaling_profile": {
                "avg_query_ms": {},
                "recommended_indexes_postgres": [],
                "notes": ["Runtime already uses PostgreSQL adapter; cutover profile is informational."],
            },
            "migration_notes": ["PostgreSQL adapter active."],
        }

    def get_table_counts(self, table_names: list[str]) -> dict[str, int]:
        return {
            table: int(self.conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"])
            for table in table_names
        }

    def check_connection(self) -> tuple[bool, str]:
        try:
            self.conn.execute("SELECT 1")
            return True, "ok"
        except Exception as exc:  # pragma: no cover - depends on runtime networking
            return False, str(exc)

    def db_integrity_status(self) -> str:
        ok, detail = self.check_connection()
        return "ok" if ok else f"error:{detail}"

    def get_schema_version(self) -> str:
        return self.get_setting("schema_version") or POSTGRES_SCHEMA_VERSION

    def storage_adapter_name(self) -> str:
        return "postgres"


BotStorage = SQLiteStorageAdapter


def build_storage(config: BotConfig) -> StoragePort:
    if config.db_engine == "postgres":
        if not config.postgres_dsn:
            raise EnvironmentError("BOT_POSTGRES_DSN is required when BOT_DB_ENGINE=postgres")
        return PostgresStorageAdapter(config.postgres_dsn)
    return SQLiteStorageAdapter(config.db_path)


class GitHubClient:
    def __init__(
        self,
        user: str,
        token: str,
        logger: logging.Logger,
        token_provider: Callable[[], str] | None = None,
        token_expiring_soon: Callable[[], bool] | None = None,
        tracer: trace.Tracer | None = None,
        auth_mode: str = "pat",
        verify_follow_after_put: bool = True,
        follow_verify_max_retries: int = 2,
        follow_verify_retry_delay_seconds: float = 1.0,
    ) -> None:
        self.user = user
        self.token = token
        self.logger = logger
        self.token_provider = token_provider
        self.token_expiring_soon = token_expiring_soon
        self.tracer = tracer
        self.auth_mode = auth_mode
        self.verify_follow_after_put = verify_follow_after_put
        self.follow_verify_max_retries = max(1, follow_verify_max_retries)
        self.follow_verify_retry_delay_seconds = max(0.0, follow_verify_retry_delay_seconds)
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "GitHubFollowerBot/2.2",
            "Accept": "application/vnd.github+json",
            "Authorization": self._authorization_header_for(token),
        }

    def _authorization_header_for(self, token: str) -> str:
        scheme = "Bearer" if self.auth_mode in {"github_app", "github_app_installation_token"} else "token"
        return f"{scheme} {token}"

    def _refresh_runtime_token(self, reason: str = "manual") -> bool:
        if self.token_provider is None:
            return False

        refreshed_token = self.token_provider().strip()
        if not refreshed_token:
            raise RuntimeError("token_provider returned empty token")

        self.token = refreshed_token
        self.headers["Authorization"] = self._authorization_header_for(refreshed_token)
        self.logger.info(
            "github_app_token_refreshed",
            extra={"event": "github_app_token_refreshed", "username": reason},
        )
        return True

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        refreshed_on_unauthorized = False
        span_ctx = self.tracer.start_as_current_span("github.request") if self.tracer else null_span()
        with span_ctx as span:
            if span:
                span.set_attribute("http.method", method)
                span.set_attribute("http.url", url)
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    if self.token_expiring_soon and self.token_expiring_soon():
                        self._refresh_runtime_token(reason="preemptive")
                    resp = self.session.request(method, url, headers=self.headers, timeout=30, **kwargs)
                    if span:
                        span.set_attribute("http.status_code", resp.status_code)
                        span.set_attribute("github.request_attempt", attempt)
                    if resp.status_code == 401 and not refreshed_on_unauthorized and self._refresh_runtime_token(reason="401"):
                        refreshed_on_unauthorized = True
                        continue
                    if resp.status_code in (403, 422, 429) and self._handle_rate_limit(resp):
                        continue
                    return resp
                except RequestException as exc:
                    sleep_time = (BACKOFF_FACTOR ** attempt) + random.uniform(0, 1)
                    self.logger.warning(
                        f"request_error attempt={attempt} sleep={sleep_time:.2f}s error={sanitize_error_payload(exc, [self.token])}",
                        extra={"event": "request_error"},
                    )
                    if span:
                        span.record_exception(exc)
                        span.set_attribute("github.request_attempt", attempt)
                    time.sleep(sleep_time)
        raise RequestException(sanitize_error_payload(f"request failed after {MAX_RETRIES} retries for {url}", [self.token]))

    def _is_rate_limited_or_abuse(self, response: requests.Response) -> bool:
        message = response.text.lower()
        return (
            response.status_code in {429, 422}
            and (
                "rate limit" in message
                or "secondary rate limit" in message
                or "abuse" in message
                or "too many" in message
            )
        )

    def _handle_rate_limit(self, response: requests.Response) -> bool:
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            time.sleep(retry_after)
            return True

        if self._is_rate_limited_or_abuse(response) or response.status_code == 403:
            reset = int(response.headers.get("X-RateLimit-Reset", str(int(time.time()) + 60)))
            wait_for = max(reset - int(time.time()), 1)
            time.sleep(wait_for)
            return True
        return False

    def check_rate_limit(self) -> tuple[int | None, int | None]:
        response = self._request("GET", f"{API_BASE}/rate_limit")
        if response.status_code >= 400:
            return None, None
        data = response.json()
        return int(data["resources"]["core"]["remaining"]), int(data["resources"]["core"]["reset"])

    def fetch_followers(self, page: int, per_page: int) -> list[dict]:
        response = self._request(
            "GET", f"{API_BASE}/users/{self.user}/followers", params={"page": page, "per_page": per_page}
        )
        if response.status_code >= 400:
            raise RequestException(f"failed to fetch followers page={page} status={response.status_code}")
        return response.json()

    def fetch_my_following(self, page: int, per_page: int) -> list[dict]:
        response = self._request(
            "GET", f"{API_BASE}/users/{self.user}/following", params={"page": page, "per_page": per_page}
        )
        if response.status_code >= 400:
            raise RequestException(f"failed to fetch following page={page} status={response.status_code}")
        return response.json()

    def fetch_user_followers(self, username: str, page: int, per_page: int) -> list[dict]:
        encoded_username = quote(username.strip().lstrip("@"), safe="")
        response = self._request(
            "GET", f"{API_BASE}/users/{encoded_username}/followers", params={"page": page, "per_page": per_page}
        )
        if response.status_code >= 400:
            raise RequestException(
                f"failed to fetch user followers username={encoded_username} page={page} status={response.status_code}"
            )
        return response.json()

    def fetch_user_following(self, username: str, page: int, per_page: int) -> list[dict]:
        encoded_username = quote(username.strip().lstrip("@"), safe="")
        response = self._request(
            "GET", f"{API_BASE}/users/{encoded_username}/following", params={"page": page, "per_page": per_page}
        )
        if response.status_code >= 400:
            raise RequestException(
                f"failed to fetch user following username={encoded_username} page={page} status={response.status_code}"
            )
        return response.json()

    def fetch_user_repositories(self, username: str, page: int, per_page: int) -> list[dict]:
        encoded_username = quote(username.strip().lstrip("@"), safe="")
        response = self._request(
            "GET",
            f"{API_BASE}/users/{encoded_username}/repos",
            params={"page": page, "per_page": per_page, "sort": "updated", "direction": "desc"},
        )
        if response.status_code >= 400:
            raise RequestException(
                f"failed to fetch user repositories username={encoded_username} page={page} status={response.status_code}"
            )
        return response.json()

    def get_repository(self, full_name: str) -> dict | None:
        owner, repo = normalize_repository_full_name(full_name)
        response = self._request("GET", f"{API_BASE}/repos/{quote(owner, safe='')}/{quote(repo, safe='')}")
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise RequestException(f"failed to fetch repository full_name={owner}/{repo} status={response.status_code}")
        return response.json()

    def fork_repository(self, full_name: str) -> tuple[bool, int, str | None]:
        owner, repo = normalize_repository_full_name(full_name)
        response = self._request("POST", f"{API_BASE}/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/forks")
        if response.status_code in {202, 201}:
            return True, response.status_code, None
        return False, response.status_code, sanitize_error_payload(response.text[:500], [self.token])

    def _verify_follow_applied(self, normalized_username: str, encoded_username: str) -> tuple[bool, int | None, str | None]:
        for attempt in range(1, self.follow_verify_max_retries + 1):
            probe = self._request("GET", f"{API_BASE}/user/following/{encoded_username}")
            if probe.status_code == 204:
                return True, 204, None
            if probe.status_code == 404 and attempt < self.follow_verify_max_retries:
                time.sleep(self.follow_verify_retry_delay_seconds)
                continue
            reason = (
                f"follow_verification_failed username={normalized_username} "
                f"status={probe.status_code} attempt={attempt}/{self.follow_verify_max_retries}"
            )
            if probe.status_code == 404:
                inferred_visibility = self._infer_profile_visibility(normalized_username, encoded_username)
                if inferred_visibility:
                    reason = f"{reason} inferred_visibility={inferred_visibility}"
            return False, probe.status_code, reason
        reason = (
            f"follow_verification_failed username={normalized_username} "
            f"status=404 attempt={self.follow_verify_max_retries}/{self.follow_verify_max_retries}"
        )
        inferred_visibility = self._infer_profile_visibility(normalized_username, encoded_username)
        if inferred_visibility:
            reason = f"{reason} inferred_visibility={inferred_visibility}"
        return False, 404, reason

    def _infer_profile_visibility(self, normalized_username: str, encoded_username: str) -> str | None:
        user_lookup = self._request("GET", f"{API_BASE}/users/{encoded_username}")
        if user_lookup.status_code == 200:
            return "private_or_restricted"
        if user_lookup.status_code == 404:
            return "not_found_or_blocked"
        self.logger.info(
            "follow_visibility_inference_failed",
            extra={
                "event": "follow_visibility_inference_failed",
                "username": normalized_username,
                "status_code": user_lookup.status_code,
            },
        )
        return None

    def follow_user(self, username: str) -> tuple[bool, int | None, str | None]:
        normalized_username = username.strip().lstrip("@")
        encoded_username = quote(normalized_username, safe="")
        response = self._request("PUT", f"{API_BASE}/user/following/{encoded_username}")
        if response.status_code == 204:
            if self.verify_follow_after_put:
                return self._verify_follow_applied(normalized_username, encoded_username)
            return True, 204, None
        if response.status_code == 422 and self._is_rate_limited_or_abuse(response):
            reason = (
                "follow_throttled_by_github "
                f"username={normalized_username} upstream_status=422 "
                "reason=secondary_rate_limit_or_abuse"
            )
            return False, 429, reason
        if response.status_code == 404:
            user_lookup = self._request("GET", f"{API_BASE}/users/{encoded_username}")
            if user_lookup.status_code == 200:
                auth_probe = self._request("GET", f"{API_BASE}/user")
                authenticated_as = None
                oauth_scopes = ""
                accepted_scopes = ""
                if auth_probe.status_code == 200:
                    authenticated_as = str(auth_probe.json().get("login") or "").strip() or None
                oauth_scopes = (auth_probe.headers.get("X-OAuth-Scopes") or "").strip()
                accepted_scopes = (auth_probe.headers.get("X-Accepted-OAuth-Scopes") or "").strip()

                hint_parts = [
                    "GitHub returned 404 on follow endpoint although target profile exists.",
                    f"auth_mode={self.auth_mode}",
                ]
                if authenticated_as:
                    hint_parts.append(f"authenticated_as={authenticated_as}")
                if oauth_scopes:
                    hint_parts.append(f"token_scopes={oauth_scopes}")
                if accepted_scopes:
                    hint_parts.append(f"accepted_scopes={accepted_scopes}")

                if self.auth_mode == "pat":
                    normalized_scopes = {scope.strip() for scope in oauth_scopes.split(",") if scope.strip()}
                    if oauth_scopes and "user:follow" not in normalized_scopes:
                        hint_parts.append("missing_scope=user:follow")
                    hint_parts.append("Ensure PAT is classic with user:follow scope.")
                elif self.auth_mode == "github_app_installation_token":
                    hint_parts.append("Ensure installation token has Followers write permission.")
                else:
                    hint_parts.append("Ensure GitHub App installation has Followers write permission.")
                return False, 404, " ".join(hint_parts)
        return False, response.status_code, sanitize_error_payload(response.text[:500], [self.token])




def build_follow_back_service(
    config: BotConfig,
    logger: logging.Logger,
    *,
    storage: StoragePort | None = None,
) -> FollowBackService:
    try:
        return FollowBackService(
            config,
            logger,
            storage=storage,
            telemetry_runtime_factory=TelemetryRuntime,
            storage_builder=build_storage,
            github_client_cls=GitHubClient,
            policy_engine_cls=PolicyEngine,
            issue_token_details=issue_github_app_installation_token_details,
            sanitize_error_payload_fn=sanitize_error_payload,
            legacy_files=LEGACY_FILES,
            rate_limit_threshold=RATE_LIMIT_THRESHOLD,
            delay_between_follows=DELAY_BETWEEN_FOLLOWS,
        )
    except TypeError:
        if storage is not None:
            return FollowBackService(config, logger, storage=storage)
        return FollowBackService(config, logger)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GitHub follower bot")
    sub = parser.add_subparsers(dest="command", required=False)

    sub.add_parser("run", help="Run follower synchronization")
    sub.add_parser("stats", help="Show persisted stats")
    sub.add_parser("doctor", help="Show runtime diagnostics")
    sub.add_parser("control-plane-status", help="Show control-plane status payload")
    sub.add_parser("metrics", help="Export Prometheus metrics to stdout")
    sub.add_parser("check-file-hardening", help="Validate runtime file permissions for DB/log")
    sub.add_parser("queue-backend-status", help="Show distributed queue backend readiness")
    sub.add_parser("queue-backend-verify", help="Verify queue backend topology/runtime connectivity")
    sub.add_parser("queue-backend-smoke", help="Run smoke test for configured queue backend")
    compliance_parser = sub.add_parser("compliance-evidence-status", help="Check governance/compliance evidence bundle completeness")
    compliance_parser.add_argument("--evidence-dir", default="artifacts/enterprise-evidence", help="Evidence directory to validate")

    queue_parser = sub.add_parser("queue-stats", help="Show follow queue stats")
    queue_parser.add_argument("--run-id", type=int, required=False, help="Optional run ID filter")

    worker_parser = sub.add_parser("worker", help="Process queued follow jobs for a run")
    worker_parser.add_argument("--run-id", type=int, required=True, help="Run ID to process")
    worker_parser.add_argument("--max-jobs", type=int, required=False, help="Optional processing cap")

    resume_parser = sub.add_parser("resume", help="Resume queued follow jobs for an existing run")
    resume_parser.add_argument("--run-id", type=int, required=True, help="Run ID to resume")
    resume_parser.add_argument("--max-jobs", type=int, required=False, help="Optional processing cap")

    abort_parser = sub.add_parser("abort", help="Abort a running run while preserving persisted progress")
    abort_parser.add_argument("--run-id", type=int, required=True, help="Run ID to abort")
    abort_parser.add_argument("--reason", default="aborted_by_operator", help="Abort reason stored in run record")

    export_parser = sub.add_parser("export-audit", help="Export audit information to JSON")
    export_parser.add_argument("--output", required=True, help="Output JSON file")

    sbom_parser = sub.add_parser("export-sbom", help="Export CycloneDX-like SBOM JSON")
    sbom_parser.add_argument("--output", required=True, help="Output SBOM JSON file")

    manifest_parser = sub.add_parser("export-release-manifest", help="Export release artifact digest manifest")
    manifest_parser.add_argument("--output", required=True, help="Output manifest JSON file")

    verify_manifest_parser = sub.add_parser("verify-release-manifest", help="Verify artifact digests against a manifest")
    verify_manifest_parser.add_argument("--manifest", required=True, help="Manifest JSON path")
    verify_manifest_parser.add_argument("--require-signature", action="store_true", help="Fail if manifest has no signature")
    verify_manifest_parser.add_argument("--max-age-seconds", type=int, required=False, help="Fail if manifest is older than this TTL")

    postgres_profile_parser = sub.add_parser("export-postgres-migration-profile", help="Export PostgreSQL migration/bootstrap profile")
    postgres_profile_parser.add_argument("--output", required=True, help="Output JSON profile path")

    otel_parser = sub.add_parser("export-otel-bootstrap", help="Export OTel bootstrap/profile payload")
    otel_parser.add_argument("--output", required=True, help="Output OTel bootstrap JSON path")

    otel_ops_parser = sub.add_parser("export-otel-operations-profile", help="Export OTel operations profile (collector/alerts/dashboards)")
    otel_ops_parser.add_argument("--output", required=True, help="Output OTel operations JSON path")

    sub.add_parser("otel-runtime-status", help="Show runtime OTel readiness and trace correlation status")

    queue_topology_parser = sub.add_parser("export-queue-topology-profile", help="Export distributed queue/worker topology profile")
    queue_topology_parser.add_argument("--output", required=True, help="Output queue topology JSON path")

    postgres_cutover_parser = sub.add_parser("export-postgres-cutover-profile", help="Export Postgres dual-write/cutover profile")
    postgres_cutover_parser.add_argument("--output", required=True, help="Output Postgres cutover JSON path")

    dual_write_parser = sub.add_parser("export-dual-write-consistency-report", help="Export SQLite/Postgres dual-write consistency report")
    dual_write_parser.add_argument("--output", required=True, help="Output dual-write consistency JSON path")

    zero_trust_parser = sub.add_parser("export-zero-trust-profile", help="Export zero-trust/cosign bootstrap profile")
    zero_trust_parser.add_argument("--output", required=True, help="Output zero-trust JSON path")

    release_integrity_parser = sub.add_parser("export-release-integrity-profile", help="Export release integrity/SBOM signing enforcement profile")
    release_integrity_parser.add_argument("--output", required=True, help="Output release integrity JSON path")

    governance_parser = sub.add_parser("export-governance-profile", help="Export governance/compliance policy profile")
    governance_parser.add_argument("--output", required=True, help="Output governance profile JSON path")

    readiness_parser = sub.add_parser("export-enterprise-readiness-report", help="Export aggregated enterprise readiness report")
    readiness_parser.add_argument("--output", required=True, help="Output enterprise readiness JSON path")
    readiness_parser.add_argument("--evidence-dir", default="artifacts/enterprise-evidence", help="Evidence directory for compliance bundle checks")

    readiness_gate_parser = sub.add_parser("enterprise-readiness-gate", help="Evaluate and enforce enterprise readiness gate")
    readiness_gate_parser.add_argument("--evidence-dir", default="artifacts/enterprise-evidence", help="Evidence directory for compliance bundle checks")
    readiness_gate_parser.add_argument("--allow-partial", action="store_true", help="Return success even when readiness is partial")

    backlog_parser = sub.add_parser("enterprise-backlog-status", help="Report remaining enterprise closure items")
    backlog_parser.add_argument("--evidence-dir", default="artifacts/enterprise-evidence", help="Evidence directory for compliance bundle checks")

    remaining_parser = sub.add_parser("enterprise-remaining-work", help="Export actionable remaining work items for enterprise closure")
    remaining_parser.add_argument("--evidence-dir", default="artifacts/enterprise-evidence", help="Evidence directory for compliance bundle checks")

    handoff_parser = sub.add_parser("enterprise-handoff-report", help="Export final handoff summary for enterprise closure")
    handoff_parser.add_argument("--evidence-dir", default="artifacts/enterprise-evidence", help="Evidence directory for compliance bundle checks")

    fork_parser = sub.add_parser("fork-repos", help="Fork repositories from a GitHub username with granular filters")
    fork_parser.add_argument("--username", required=True, help="GitHub username to inspect")
    fork_parser.add_argument("--owned", action="store_true", help="Include repositories owned by the user (non-forks)")
    fork_parser.add_argument("--forked", action="store_true", help="Include repositories that are forks")
    fork_parser.add_argument("--all", action="store_true", help="Include both owned and forked repositories")
    fork_parser.add_argument("--profile-readme", action="store_true", help="Include profile README repo (<user>/<user>)")
    fork_parser.add_argument("--fork-source", action="store_true", help="When repo is a fork, fork the source root repository")
    fork_parser.add_argument("--follow-fork-owners", action="store_true", help="Follow owners discovered in fork chains while processing")

    scheduler_parser = sub.add_parser("scheduler", help="Run dedicated scheduler loop that triggers run capability")
    scheduler_parser.add_argument("--interval-seconds", type=float, default=60.0, help="Seconds between scheduler ticks")
    scheduler_parser.add_argument("--max-ticks", type=int, default=1, help="How many ticks to execute before exiting")
    scheduler_parser.add_argument("--lock-key", default="default", help="Scheduler lock key to avoid concurrent schedules")
    scheduler_parser.add_argument("--lock-ttl-seconds", type=int, default=300, help="Scheduler lock TTL in seconds")

    serve_cp_parser = sub.add_parser("serve-control-plane", help="Run minimal HTTP control-plane server")
    serve_cp_parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    serve_cp_parser.add_argument("--port", type=int, default=8080, help="Bind port")

    sub.add_parser("gui", help="Run optional NiceGUI operational interface")
    return parser


def export_otel_bootstrap(config: BotConfig) -> dict:
    trace_id_hex = uuid4().hex
    span_id_hex = uuid4().hex[:16]
    traceparent = f"00-{trace_id_hex}-{span_id_hex}-01"
    return {
        "enabled": config.otel_enabled,
        "service_name": config.otel_service_name,
        "exporter_otlp_endpoint": config.otel_exporter_otlp_endpoint,
        "resource_attributes": {
            "service.name": config.otel_service_name,
            "service.version": "2.2",
            "deployment.environment": os.getenv("APP_ENV", "local"),
        },
        "sample_trace_context": {
            "trace_id": trace_id_hex,
            "span_id": span_id_hex,
            "traceparent": traceparent,
        },
        "status": "configured" if config.otel_enabled and config.otel_exporter_otlp_endpoint else "partial",
    }


def export_zero_trust_profile(config: BotConfig) -> dict:
    release_artifacts = ["bot.py", "check_all_followers.py", "requirements.txt"]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cosign_enabled": config.cosign_enabled,
        "cosign_key_ref": config.cosign_key_ref,
        "critical_artifacts": release_artifacts,
        "recommended_commands": {
            "sign": "cosign sign --key $COSIGN_KEY_REF <image-or-artifact>",
            "verify": "cosign verify --key $COSIGN_KEY_REF <image-or-artifact>",
        },
        "status": "configured" if config.cosign_enabled and config.cosign_key_ref else "partial",
    }




def export_otel_runtime_status(config: BotConfig) -> dict:
    enabled = bool(config.otel_enabled)
    endpoint_configured = bool(config.otel_exporter_otlp_endpoint)
    status = "ready" if enabled and endpoint_configured else ("partial" if enabled else "disabled")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "otel_enabled": enabled,
        "service_name": config.otel_service_name,
        "exporter_otlp_endpoint_configured": endpoint_configured,
        "trace_correlation_fields": ["run_id", "trace_id", "event"],
        "runtime_spans": [
            "github.request",
            "follow_queue.process",
            "follow_queue.follow_user",
        ],
        "alerts_expected": [
            "high_follow_error_rate",
            "zero_progress_window",
            "auth_failures",
        ],
        "next_actions": (
            [
                "Set BOT_OTEL_ENABLED=true",
                "Set OTEL_EXPORTER_OTLP_ENDPOINT to collector endpoint",
                "Enable dashboards/alerts from export-otel-operations-profile",
            ]
            if status != "ready"
            else ["Observability runtime contract ready"]
        ),
    }


def export_otel_operations_profile(config: BotConfig) -> dict:
    environment_assets = {
        "dev": {
            "alerts_file": "observability/alerts/github_follower_bot_rules.dev.yml",
            "dashboard_file": "observability/dashboards/github_follower_bot.dev.json",
        },
        "staging": {
            "alerts_file": "observability/alerts/github_follower_bot_rules.staging.yml",
            "dashboard_file": "observability/dashboards/github_follower_bot.staging.json",
        },
        "prod": {
            "alerts_file": "observability/alerts/github_follower_bot_rules.prod.yml",
            "dashboard_file": "observability/dashboards/github_follower_bot.prod.json",
        },
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "service_name": config.otel_service_name,
        "collector_pipeline": {
            "required_processors": ["batch", "memory_limiter"],
            "required_exporters": ["otlp"],
            "healthcheck_extension": True,
        },
        "alerts": [
            {"name": "github_bot_high_error_rate", "promql": 'sum(rate(github_api_requests_total{status=~"5.."}[5m])) > 0.5'},
            {"name": "github_bot_no_progress", "promql": 'increase(follow_attempts_total[15m]) == 0'},
            {"name": "github_bot_low_rate_limit", "promql": 'rate_limit_remaining < 100'},
        ],
        "dashboards": [
            "runtime-latency",
            "github-api-health",
            "queue-throughput",
            "security-events",
        ],
        "environment_assets": environment_assets,
        "status": "configured" if config.otel_enabled and config.otel_exporter_otlp_endpoint else "partial",
    }


def export_queue_worker_topology_profile(config: BotConfig) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_queue_contract": {
            "primary_store": "sqlite.follow_jobs",
            "statuses": ["pending", "done", "failed", "dead_letter"],
            "retry_budget": config.follow_job_max_attempts,
        },
        "distributed_worker_plan": {
            "recommended_transports": ["sqs", "rabbitmq", "kafka"],
            "partition_key": "run_id",
            "dead_letter_transport_required": True,
            "idempotency_key": "run_id:github_login",
        },
        "status": "configured",
    }


def export_postgres_cutover_profile() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phases": [
            "baseline_snapshot",
            "dual_write_shadow",
            "read_switch_canary",
            "full_cutover",
            "sqlite_decommission",
        ],
        "dual_write_contract": {
            "required_tables": ["bot_runs", "followers", "follow_actions", "follow_jobs", "security_events", "repository_catalog"],
            "consistency_check_queries": [
                "SELECT COUNT(*) FROM followers",
                "SELECT COUNT(*) FROM follow_jobs WHERE status='pending'",
                "SELECT COUNT(*) FROM follow_actions",
            ],
        },
        "rollback": {
            "switch_reads_back_to_sqlite": True,
            "replay_queue_from_postgres_delta": True,
        },
        "status": "configured",
    }


def export_release_integrity_profile(config: BotConfig) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sbom_required": True,
        "manifest_signature_required": config.release_manifest_require_signature,
        "cosign_enforced": bool(config.cosign_enabled and config.cosign_key_ref),
        "recommended_gate_order": [
            "pip-audit",
            "export-sbom",
            "export-release-manifest",
            "verify-release-manifest",
            "cosign verify",
        ],
        "status": "configured" if config.cosign_enabled and config.cosign_key_ref else "partial",
    }
def export_dual_write_consistency_report(config: BotConfig, storage: StoragePort) -> dict:
    tables = ["bot_runs", "followers", "follow_actions", "follow_jobs", "security_events", "repository_catalog"]
    sqlite_counts = storage.get_table_counts(tables)
    postgres_dsn = config.postgres_dsn or os.getenv("BOT_POSTGRES_DSN", "").strip()
    report: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dual_write_dry_run_enabled": os.getenv("BOT_DUAL_WRITE_DRY_RUN", "false").strip().lower() in {"1", "true", "yes", "on"},
        "sqlite_counts": sqlite_counts,
        "postgres_configured": bool(postgres_dsn),
        "status": "shadow_not_configured",
        "consistency": "unknown",
    }

    if config.db_engine == "postgres":
        report["status"] = "runtime_postgres"
        report["consistency"] = "n/a"
        report["next_steps"] = [
            "Dual-write consistency report is not applicable when PostgreSQL is the active runtime engine.",
            "Use export-postgres-cutover-profile for rollback and operational validation guidance.",
        ]
        return report

    if not postgres_dsn:
        return report

    report["status"] = "shadow_configured"
    report["consistency"] = "pending_validation"
    report["postgres_tables_expected"] = list(sqlite_counts.keys())
    report["next_steps"] = [
        "Provision PostgreSQL schema from export-postgres-migration-profile DDL.",
        "Enable BOT_DUAL_WRITE_DRY_RUN=true in worker/runtime environment.",
        "Compare row counts and hash samples per table before cutover.",
    ]
    return report


def doctor_report(config: BotConfig, storage: StoragePort) -> dict:
    db_exists = Path(config.db_path).exists() if config.db_engine == "sqlite" else bool(config.postgres_dsn)
    integrity = storage.db_integrity_status()
    db_ok, db_detail = storage.check_connection()
    return {
        "db_exists": db_exists,
        "db_integrity": integrity,
        "db_engine": config.db_engine,
        "db_engine_configured": (config.db_engine == "sqlite") or bool(config.postgres_dsn),
        "db_connection_status": "ok" if db_ok else "error",
        "db_connection_detail": db_detail,
        "schema_version": storage.get_schema_version(),
        "storage_adapter": storage.storage_adapter_name(),
        "dry_run": config.dry_run,
        "max_follows_per_run": config.max_follows_per_run,
        "max_forks_per_run": config.max_forks_per_run,
        "max_candidates_per_run": config.max_candidates_per_run,
        "max_api_calls_per_run": config.max_api_calls_per_run,
        "max_expand_seeds_per_run": config.max_expand_seeds_per_run,
        "discovery_mode": config.discovery_mode,
        "expand_http_error_window": config.expand_http_error_window,
        "expand_http_error_threshold": config.expand_http_error_threshold,
        "expand_fallback_to_followers": config.expand_fallback_to_followers,
        "legacy_migration_done": storage.get_setting("legacy_migration_done") == "1",
        "cleanup_legacy_files": config.cleanup_legacy_files,
        "auth_mode": config.auth_mode,
        "github_app_configured": bool(
            config.github_app_id
            and config.github_app_installation_id
            and (config.github_app_private_key or config.github_app_private_key_file or config.github_app_private_key_command)
        ),
        "github_app_private_key_source": config.github_app_private_key_source(),
        "github_app_private_key_file_candidates": list(config.github_app_private_key_file_candidates),
        "github_app_private_key_command_timeout_seconds": config.github_app_private_key_command_timeout_seconds,
        "github_app_token_refresh_skew_seconds": config.github_app_token_refresh_skew_seconds,
        "verify_follow_after_put": config.verify_follow_after_put,
        "follow_verify_max_retries": config.follow_verify_max_retries,
        "follow_verify_retry_delay_seconds": config.follow_verify_retry_delay_seconds,
        "otel_enabled": config.otel_enabled,
        "otel_service_name": config.otel_service_name,
        "otel_exporter_otlp_endpoint_configured": bool(config.otel_exporter_otlp_endpoint),
        "cosign_enabled": config.cosign_enabled,
        "cosign_key_ref_configured": bool(config.cosign_key_ref),
        "require_github_app_auth": config.require_github_app_auth,
        "follow_job_max_attempts": config.follow_job_max_attempts,
        "release_manifest_signing_enabled": bool(config.release_manifest_signing_key),
        "release_manifest_require_signature": config.release_manifest_require_signature,
        "release_manifest_max_age_seconds": config.release_manifest_max_age_seconds,
        "file_hardening": collect_runtime_file_permission_report(config),
    }


def export_queue_backend_status(config: BotConfig) -> dict:
    backend = os.getenv("BOT_QUEUE_BACKEND", "sqlite").strip().lower() or "sqlite"
    amqp_url = os.getenv("BOT_RABBITMQ_AMQP_URL", "").strip()
    queue_name = os.getenv("BOT_RABBITMQ_QUEUE", "follow_jobs").strip() or "follow_jobs"
    dlq_name = os.getenv("BOT_RABBITMQ_DLQ", "follow_jobs.dead_letter").strip() or "follow_jobs.dead_letter"

    if backend not in {"sqlite", "rabbitmq"}:
        return {
            "backend": backend,
            "status": "invalid",
            "ready": False,
            "error": "unsupported_queue_backend",
            "supported_backends": ["sqlite", "rabbitmq"],
        }

    if backend == "sqlite":
        return {
            "backend": "sqlite",
            "status": "ready",
            "ready": True,
            "storage_adapter": config.db_engine,
            "notes": [
                "Uses transactional follow_jobs table in configured storage adapter",
                "For distributed workers use BOT_QUEUE_BACKEND=rabbitmq with external broker",
            ],
        }

    return {
        "backend": "rabbitmq",
        "status": "ready" if bool(amqp_url) else "partial",
        "ready": bool(amqp_url),
        "transport": "amqp",
        "amqp_url_configured": bool(amqp_url),
        "queue_name": queue_name,
        "dead_letter_queue": dlq_name,
        "max_attempts": config.follow_job_max_attempts,
        "notes": [
            "RabbitMQ adapter available at adapters/queue/rabbitmq_adapter.py",
            "Set BOT_RABBITMQ_AMQP_URL to enable external distributed queue runtime",
        ],
    }


def export_compliance_evidence_status(evidence_dir: str) -> dict:
    root = Path(evidence_dir)
    required = [
        "doctor_report.json",
        "audit.json",
        "sbom_ci.json",
        "release_manifest_ci.json",
        "queue_backend_status_report.json",
        "otel_runtime_status_report.json",
    ]
    present = []
    missing = []
    for name in required:
        if (root / name).is_file():
            present.append(name)
        else:
            missing.append(name)

    status = "ready" if not missing else "incomplete"
    return {
        "evidence_dir": str(root),
        "status": status,
        "required_count": len(required),
        "present_count": len(present),
        "missing_count": len(missing),
        "present": present,
        "missing": missing,
    }


def export_enterprise_readiness_report(config: BotConfig, storage: StoragePort, evidence_dir: str) -> dict:
    queue_status = export_queue_backend_status(config)
    otel_status = export_otel_runtime_status(config)
    compliance_status = export_compliance_evidence_status(evidence_dir)
    governance = export_governance_profile(config)
    control_plane_status_code, control_plane = handle_control_plane_status(storage, config)

    checks = {
        "queue_backend": queue_status.get("status"),
        "otel_runtime": otel_status.get("status"),
        "compliance_evidence": compliance_status.get("status"),
        "governance_profile": governance.get("status"),
        "control_plane": control_plane.get("status") if control_plane_status_code == 0 else "error",
    }

    blocking = []
    if not queue_status.get("ready"):
        blocking.append("queue_backend_not_ready")
    if otel_status.get("status") != "ready":
        blocking.append("otel_runtime_not_ready")
    if compliance_status.get("status") != "ready":
        blocking.append("compliance_evidence_incomplete")

    overall = "ready" if not blocking else "partial"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall,
        "blocking_items": blocking,
        "checks": checks,
        "details": {
            "queue_backend": queue_status,
            "otel_runtime": otel_status,
            "compliance_evidence": compliance_status,
            "governance_profile": governance,
            "control_plane": control_plane,
        },
    }


def evaluate_enterprise_readiness_gate(config: BotConfig, storage: StoragePort, evidence_dir: str, allow_partial: bool) -> tuple[int, dict]:
    report = export_enterprise_readiness_report(config, storage, evidence_dir=evidence_dir)
    status = report.get("overall_status", "partial")
    blocking_items = list(report.get("blocking_items") or [])

    if status == "ready":
        return 0, {
            "gate": "pass",
            "overall_status": status,
            "blocking_items": blocking_items,
        }

    if allow_partial:
        return 0, {
            "gate": "warn",
            "overall_status": status,
            "blocking_items": blocking_items,
            "allow_partial": True,
        }

    return 2, {
        "gate": "fail",
        "overall_status": status,
        "blocking_items": blocking_items,
        "allow_partial": False,
    }


def export_enterprise_backlog_status(config: BotConfig, storage: StoragePort, evidence_dir: str) -> dict:
    readiness = export_enterprise_readiness_report(config, storage, evidence_dir=evidence_dir)
    checks = readiness.get("checks") or {}

    items = [
        {
            "id": "distributed_runtime_workers",
            "title": "Workers distribuidos sobre broker externo en runtime productivo",
            "status": "completed" if checks.get("queue_backend") in {"ready", "verified"} else "pending",
        },
        {
            "id": "observability_e2e_runtime",
            "title": "Observabilidad E2E multi-servicio (collector + dashboards + alerting) operativa",
            "status": "completed" if checks.get("otel_runtime") == "ready" else "pending",
        },
        {
            "id": "compliance_e2e_evidence",
            "title": "Evidencia compliance end-to-end en corridas reales",
            "status": "completed" if checks.get("compliance_evidence") == "ready" else "pending",
        },
    ]

    pending = [item for item in items if item["status"] != "completed"]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "closed" if not pending else "in_progress",
        "pending_count": len(pending),
        "completed_count": len(items) - len(pending),
        "items": items,
        "readiness_overview": readiness.get("overall_status"),
        "blocking_items": readiness.get("blocking_items", []),
    }


def export_enterprise_remaining_work(config: BotConfig, storage: StoragePort, evidence_dir: str) -> dict:
    backlog = export_enterprise_backlog_status(config, storage, evidence_dir=evidence_dir)
    items = list(backlog.get("items") or [])
    pending_items = [item for item in items if item.get("status") != "completed"]

    recommendations = []
    for item in pending_items:
        item_id = item.get("id")
        if item_id == "distributed_runtime_workers":
            recommendations.append({
                "id": item_id,
                "next_action": "Deploy external RabbitMQ/SQS worker topology in non-local environment and attach runtime evidence",
                "owner": "platform",
            })
        elif item_id == "observability_e2e_runtime":
            recommendations.append({
                "id": item_id,
                "next_action": "Enable OTel collector + dashboards + alerts in target environment and attach screenshots/exports",
                "owner": "observability",
            })
        elif item_id == "compliance_e2e_evidence":
            recommendations.append({
                "id": item_id,
                "next_action": "Attach end-to-end compliance execution evidence for real runs",
                "owner": "security_compliance",
            })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "no_remaining_work" if not pending_items else "remaining_work",
        "pending_count": len(pending_items),
        "pending_items": pending_items,
        "recommendations": recommendations,
        "backlog_overview": backlog.get("overall_status"),
    }


def export_enterprise_handoff_report(config: BotConfig, storage: StoragePort, evidence_dir: str) -> dict:
    readiness = export_enterprise_readiness_report(config, storage, evidence_dir=evidence_dir)
    backlog = export_enterprise_backlog_status(config, storage, evidence_dir=evidence_dir)
    remaining = export_enterprise_remaining_work(config, storage, evidence_dir=evidence_dir)

    closure_ready = (
        readiness.get("overall_status") == "ready"
        and backlog.get("overall_status") == "closed"
        and remaining.get("overall_status") == "no_remaining_work"
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "handoff_status": "ready_for_closeout" if closure_ready else "pending_operational_closeout",
        "closure_ready": closure_ready,
        "readiness_overview": readiness.get("overall_status"),
        "backlog_overview": backlog.get("overall_status"),
        "remaining_work_overview": remaining.get("overall_status"),
        "blocking_items": readiness.get("blocking_items", []),
        "pending_items": remaining.get("pending_items", []),
        "recommendations": remaining.get("recommendations", []),
        "notes": [
            "Use this report as final handoff checklist for enterprise closure decisions.",
            "If pending_operational_closeout, complete pending items and regenerate report.",
        ],
    }


def export_governance_profile(config: BotConfig) -> dict:
    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "generated_at": generated_at,
        "status": "defined",
        "policy_controls": {
            "consent_required": True,
            "retention_policy_defined": True,
            "deletion_workflow_defined": True,
            "audit_trail_required": True,
            "kill_switch_defined": True,
        },
        "operational_contract": {
            "require_github_app_auth": config.require_github_app_auth,
            "release_manifest_require_signature": config.release_manifest_require_signature,
            "cosign_enabled": config.cosign_enabled,
        },
        "required_evidence": [
            "pytest_report",
            "doctor_report",
            "security_scan_report",
            "sbom",
            "release_manifest_verification",
            "consent_retention_policy_logs",
        ],
        "incident_response": {
            "run_abort_command": "python bot.py abort --run-id <id> --reason <text>",
            "investigation_fields": ["run_id", "trace_id", "event"],
            "security_events_table": "security_events",
        },
    }



def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    command = args.command or "run"

    config = BotConfig.from_env()
    logger = setup_logger(redact_secrets=[config.github_token, config.github_app_private_key or ""])
    storage = build_storage(config)

    context = CliCommandContext(
        config=config,
        logger=logger,
        storage=storage,
        build_follow_back_service=build_follow_back_service,
        build_storage=build_storage,
        execute_run=execute_run,
        handle_default_run_command=handle_default_run_command,
        handle_worker_command=handle_worker_command,
        handle_resume_command=handle_resume_command,
        handle_abort_command=handle_abort_command,
        handle_fork_repos_command=handle_fork_repos_command,
        handle_scheduler_command=handle_scheduler_command,
        handle_control_plane_status=handle_control_plane_status,
        serve_control_plane=serve_control_plane,
        verify_queue_backend=verify_queue_backend,
        smoke_test_queue_backend=smoke_test_queue_backend,
        queue_adapter_factory=RabbitMQFollowQueueAdapter,
        doctor_report=doctor_report,
        runtime_file_hardening_check=runtime_file_hardening_check,
        export_queue_backend_status=export_queue_backend_status,
        export_compliance_evidence_status=export_compliance_evidence_status,
        export_otel_runtime_status=export_otel_runtime_status,
        export_otel_bootstrap=export_otel_bootstrap,
        export_otel_operations_profile=export_otel_operations_profile,
        export_queue_worker_topology_profile=export_queue_worker_topology_profile,
        export_postgres_cutover_profile=export_postgres_cutover_profile,
        export_dual_write_consistency_report=export_dual_write_consistency_report,
        export_zero_trust_profile=export_zero_trust_profile,
        export_release_integrity_profile=export_release_integrity_profile,
        export_governance_profile=export_governance_profile,
        export_enterprise_readiness_report=export_enterprise_readiness_report,
        evaluate_enterprise_readiness_gate=evaluate_enterprise_readiness_gate,
        export_enterprise_backlog_status=export_enterprise_backlog_status,
        export_enterprise_remaining_work=export_enterprise_remaining_work,
        export_enterprise_handoff_report=export_enterprise_handoff_report,
        resolve_command_output_path=resolve_command_output_path,
        launch_gui=launch_gui,
    )
    return dispatch_cli_command(command, args, context)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(
            json.dumps(
                {
                    "event": "shutdown_requested",
                    "message": "Interrupted by user (Ctrl+C). Exiting gracefully.",
                }
            )
        )
        raise SystemExit(130)
