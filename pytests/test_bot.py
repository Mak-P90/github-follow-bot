import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot import (
    BotConfig,
    BotStorage,
    FollowBackService,
    GitHubClient,
    JsonFormatter,
    SQLiteStorageAdapter,
    SecretRedactionFilter,
    build_storage,
    doctor_report,
    export_otel_bootstrap,
    export_otel_operations_profile,
    export_postgres_cutover_profile,
    export_dual_write_consistency_report,
    export_queue_worker_topology_profile,
    export_release_integrity_profile,
    export_zero_trust_profile,
    issue_github_app_installation_token,
    issue_github_app_installation_token_details,
    load_postgres_schema_sql,
    redact_sensitive_text,
    sanitize_error_payload,
    normalize_repository_full_name,
    runtime_file_hardening_check,
    setup_logger,
)


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text="", headers=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._payload


def test_normalize_repository_full_name_ok():
    owner, repo = normalize_repository_full_name(" octo-org/my-repo ")
    assert owner == "octo-org"
    assert repo == "my-repo"


def test_normalize_repository_full_name_invalid():
    try:
        normalize_repository_full_name("invalid")
    except ValueError as exc:
        assert "owner/repo" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid repository full name")



def test_config_require_github_app_auth(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_REQUIRE_GITHUB_APP_AUTH", "true")

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "BOT_REQUIRE_GITHUB_APP_AUTH" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError when requiring github_app auth")


def test_json_formatter_includes_reason_field():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="github_follower_bot",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="expand_candidate_skipped",
        args=(),
        exc_info=None,
    )
    record.event = "expand_candidate_skipped"
    record.reason = "already_followed_historically"
    payload = json.loads(formatter.format(record))
    assert payload["event"] == "expand_candidate_skipped"
    assert payload["reason"] == "already_followed_historically"


def test_export_enterprise_profiles_payloads():
    config = BotConfig(
        github_user="u",
        github_token="t",
        otel_enabled=True,
        otel_exporter_otlp_endpoint="http://collector:4318",
        cosign_enabled=True,
        cosign_key_ref="cosign.pub",
        release_manifest_require_signature=True,
        follow_job_max_attempts=5,
    )
    otel_ops = export_otel_operations_profile(config)
    assert otel_ops["status"] == "configured"
    assert len(otel_ops["alerts"]) >= 3
    assert set(otel_ops["environment_assets"].keys()) == {"dev", "staging", "prod"}

    queue_profile = export_queue_worker_topology_profile(config)
    assert queue_profile["run_queue_contract"]["retry_budget"] == 5
    assert queue_profile["distributed_worker_plan"]["dead_letter_transport_required"] is True

    pg_cutover = export_postgres_cutover_profile()
    assert "dual_write_shadow" in pg_cutover["phases"]

    release_profile = export_release_integrity_profile(config)
    assert release_profile["cosign_enforced"] is True
    assert release_profile["manifest_signature_required"] is True



def test_config_from_env_otel(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_OTEL_ENABLED", "true")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "gh-bot-service")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318")

    config = BotConfig.from_env()
    assert config.otel_enabled is True
    assert config.otel_service_name == "gh-bot-service"
    assert config.otel_exporter_otlp_endpoint == "http://collector:4318"


def test_export_otel_bootstrap_payload(monkeypatch):
    config = BotConfig(
        github_user="u",
        github_token="t",
        otel_enabled=True,
        otel_service_name="gh-bot-service",
        otel_exporter_otlp_endpoint="http://collector:4318",
    )
    payload = export_otel_bootstrap(config)
    assert payload["enabled"] is True
    assert payload["status"] == "configured"
    assert payload["resource_attributes"]["service.name"] == "gh-bot-service"
    assert payload["sample_trace_context"]["traceparent"].startswith("00-")



def test_config_from_env_cosign(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_COSIGN_ENABLED", "true")
    monkeypatch.setenv("COSIGN_KEY_REF", "cosign.pub")

    config = BotConfig.from_env()
    assert config.cosign_enabled is True
    assert config.cosign_key_ref == "cosign.pub"


def test_export_zero_trust_profile_payload():
    config = BotConfig(
        github_user="u",
        github_token="t",
        cosign_enabled=True,
        cosign_key_ref="cosign.pub",
    )
    payload = export_zero_trust_profile(config)
    assert payload["cosign_enabled"] is True
    assert payload["status"] == "configured"
    assert "verify" in payload["recommended_commands"]

def test_storage_migrations_and_stats(tmp_path):
    db = tmp_path / "state.db"
    storage = BotStorage(str(db))

    run_id = storage.begin_run(trace_id="trace-unit")
    storage.upsert_follower_seen("alice")
    storage.mark_followed("alice")
    storage.add_follow_action(run_id, "alice", True, 204, None)
    storage.add_security_event("test", "ok")
    storage.commit()
    storage.finish_run(run_id, 1, 1, None)

    stats = storage.get_stats()
    assert stats["followers_total"] == 1
    assert stats["followers_followed"] == 1
    assert stats["runs_total"] == 1
    assert stats["security_events_total"] == 1
    assert storage.get_last_run()["status"] == "completed"
    assert storage.get_last_run()["trace_id"] == "trace-unit"


def test_github_client_follow_user_success(monkeypatch):
    logger = logging.getLogger("test")
    client = GitHubClient("me", "token", logger, verify_follow_after_put=False)

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        assert method == "PUT"
        return DummyResponse(status_code=204)

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.follow_user("alice")
    assert ok is True
    assert status == 204
    assert err is None


def test_github_client_fetch_user_repositories(monkeypatch):
    logger = logging.getLogger("test_fetch_repos")
    client = GitHubClient("me", "token", logger, verify_follow_after_put=False)

    def fake_request(method, url, headers=None, timeout=None, params=None, **kwargs):
        assert method == "GET"
        assert url == "https://api.github.com/users/alice/repos"
        assert params["sort"] == "updated"
        return DummyResponse(status_code=200, payload=[{"full_name": "alice/repo1"}])

    monkeypatch.setattr(client.session, "request", fake_request)
    repos = client.fetch_user_repositories("alice", page=1, per_page=100)
    assert repos[0]["full_name"] == "alice/repo1"


def test_github_client_fork_repository(monkeypatch):
    logger = logging.getLogger("test_fork_repo")
    client = GitHubClient("me", "token", logger, verify_follow_after_put=False)

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        assert method == "POST"
        assert url == "https://api.github.com/repos/octo/repo/forks"
        return DummyResponse(status_code=202)

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.fork_repository("octo/repo")
    assert ok is True
    assert status == 202
    assert err is None


def test_github_client_follow_user_normalizes_and_encodes_username(monkeypatch):
    logger = logging.getLogger("test_follow_user_username_normalization")
    client = GitHubClient("me", "token", logger, verify_follow_after_put=False)

    seen_urls: list[str] = []

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        seen_urls.append(url)
        return DummyResponse(status_code=204)

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.follow_user(" @alice/ops ")
    assert ok is True
    assert status == 204
    assert err is None
    assert seen_urls == [f"https://api.github.com/user/following/alice%2Fops"]


def test_github_client_follow_user_404_returns_auth_hint_when_profile_exists(monkeypatch):
    logger = logging.getLogger("test_follow_user_404_auth_hint")
    client = GitHubClient("me", "token", logger)

    requests_seen: list[tuple[str, str]] = []

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        requests_seen.append((method, url))
        if method == "PUT":
            return DummyResponse(status_code=404, text="Not Found")
        if method == "GET" and url.endswith("/users/alice"):
            return DummyResponse(status_code=200, payload={"login": "alice"})
        if method == "GET" and url.endswith("/user"):
            return DummyResponse(
                status_code=200,
                payload={"login": "me"},
                headers={"X-OAuth-Scopes": "repo", "X-Accepted-OAuth-Scopes": "user:follow"},
            )
        raise AssertionError(f"unexpected method={method} url={url}")

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.follow_user("alice")
    assert ok is False
    assert status == 404
    assert "user:follow" in str(err)
    assert "missing_scope=user:follow" in str(err)
    assert "authenticated_as=me" in str(err)
    assert requests_seen == [
        ("PUT", "https://api.github.com/user/following/alice"),
        ("GET", "https://api.github.com/users/alice"),
        ("GET", "https://api.github.com/user"),
    ]

def test_github_client_pat_uses_token_authorization_scheme(monkeypatch):
    logger = logging.getLogger("test_pat_scheme")
    client = GitHubClient("me", "pat-token", logger, verify_follow_after_put=False)

    seen_headers: list[str] = []

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        seen_headers.append(str(headers.get("Authorization", "")))
        return DummyResponse(status_code=204)

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.follow_user("alice")
    assert ok is True
    assert status == 204
    assert err is None
    assert seen_headers == ["token pat-token"]


def test_github_client_refreshes_token_on_401(monkeypatch):
    logger = logging.getLogger("test_refresh")
    tokens_seen: list[str] = []
    token_provider_calls = {"count": 0}

    def provider() -> str:
        token_provider_calls["count"] += 1
        return "new-token"

    client = GitHubClient("me", "old-token", logger, token_provider=provider, verify_follow_after_put=False)

    responses = [DummyResponse(status_code=401, text="Unauthorized"), DummyResponse(status_code=204)]

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        tokens_seen.append(str(headers.get("Authorization", "")))
        return responses.pop(0)

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.follow_user("alice")
    assert ok is True
    assert status == 204
    assert err is None
    assert token_provider_calls["count"] == 1
    assert tokens_seen[0] == "token old-token"
    assert tokens_seen[1] == "token new-token"


def test_github_client_preemptive_refresh_before_request(monkeypatch):
    logger = logging.getLogger("test_refresh_preemptive")
    token_provider_calls = {"count": 0}
    checks = {"count": 0}

    def provider() -> str:
        token_provider_calls["count"] += 1
        return f"new-token-{token_provider_calls['count']}"

    def expiring() -> bool:
        checks["count"] += 1
        return checks["count"] == 1

    client = GitHubClient("me", "old-token", logger, token_provider=provider, token_expiring_soon=expiring)

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        assert headers is not None
        return DummyResponse(status_code=204)

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.follow_user("alice")
    assert ok is True
    assert status == 204
    assert err is None
    assert token_provider_calls["count"] == 1
    assert client.token == "new-token-1"


def test_github_client_github_app_uses_bearer_scheme(monkeypatch):
    logger = logging.getLogger("test_github_app_scheme")
    client = GitHubClient("me", "inst-token", logger, auth_mode="github_app", verify_follow_after_put=False)

    seen_headers: list[str] = []

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        seen_headers.append(str(headers.get("Authorization", "")))
        return DummyResponse(status_code=204)

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.follow_user("alice")
    assert ok is True
    assert status == 204
    assert err is None
    assert seen_headers == ["Bearer inst-token"]


def test_service_run_logs_follow_failure_reason(monkeypatch, tmp_path, caplog):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db))
    logger = logging.getLogger("service_failure_reason_test")

    service = FollowBackService(config, logger)

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_followers", lambda page, per_page: [[{"login": "alice"}], []][page - 1])
    monkeypatch.setattr(
        service.github,
        "follow_user",
        lambda username: (
            False,
            404,
            "GitHub returned 404 on follow endpoint although target profile exists. auth_mode=pat missing_scope=user:follow",
        ),
    )
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    with caplog.at_level(logging.WARNING):
        service.run()

    assert any(
        "follow_failed username=alice status=404 reason=GitHub returned 404" in record.getMessage()
        for record in caplog.records
    )


def test_service_run_processes_followers(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db))
    logger = logging.getLogger("service_test")

    service = FollowBackService(config, logger)

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(
        service.github,
        "fetch_followers",
        lambda page, per_page: [[{"login": "alice"}, {"login": "bob"}], []][page - 1],
    )
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_fetched"] == 2
    assert result["followers_followed"] == 2
    assert str(result["trace_id"]).startswith("trace-")
    queue_stats = service.storage.get_follow_job_stats(run_id=result["run_id"])
    assert queue_stats["done"] == 2
    snapshot = service.storage.conn.execute("SELECT remaining FROM rate_limit_snapshots ORDER BY id DESC LIMIT 1").fetchone()
    assert snapshot is not None
    assert snapshot[0] == 5000


def test_service_respects_max_follows(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), max_follows_per_run=1)
    logger = logging.getLogger("service_test_limit")
    service = FollowBackService(config, logger)

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(
        service.github,
        "fetch_followers",
        lambda page, per_page: [[{"login": "alice"}, {"login": "bob"}], []][page - 1],
    )
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_followed"] == 1


def test_service_expand_mode_discovers_from_following_seed(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand")
    service = FollowBackService(config, logging.getLogger("service_expand_test"))

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [[{"login": "alice"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [[{"login": "bob"}], []][page - 1])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_fetched"] == 2
    assert result["followers_followed"] == 2
    assert service.storage.get_setting("expand_seed_index") == "0"


def test_service_expand_mode_skips_historically_followed(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand")
    service = FollowBackService(config, logging.getLogger("service_expand_history_test"))

    run_id = service.storage.begin_run(trace_id="trace-history")
    service.storage.add_follow_action(run_id, "alice", True, 204, None)
    service.storage.finish_run(run_id, 0, 1, None)
    service.storage.commit()

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [[{"login": "alice"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [][0:0])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_fetched"] == 0
    assert result["followers_followed"] == 0


def test_service_followers_mode_does_not_skip_historical_success(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="followers")
    service = FollowBackService(config, logging.getLogger("service_followers_history_test"))

    old_run = service.storage.begin_run(trace_id="trace-old")
    service.storage.add_follow_action(old_run, "alice", True, 204, None)
    service.storage.finish_run(old_run, 0, 1, None)
    service.storage.commit()

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_followers", lambda page, per_page: [[{"login": "alice"}], []][page - 1])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_fetched"] == 1
    assert result["followers_followed"] == 1


def test_service_expand_mode_respects_max_follows(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand", max_follows_per_run=1)
    service = FollowBackService(config, logging.getLogger("service_expand_limit_test"))

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [[{"login": "alice"}, {"login": "bob"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [][0:0])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_followed"] == 1


def test_service_run_with_otel_enabled(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(
        github_user="me",
        github_token="token",
        db_path=str(db),
        otel_enabled=True,
        otel_service_name="test-bot",
    )
    logger = logging.getLogger("service_test_otel")
    service = FollowBackService(config, logger)

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_followers", lambda page, per_page: [][0:0])

    result = service.run()
    assert result["followers_fetched"] == 0
    assert result["followers_followed"] == 0


def test_secret_redaction_filter():
    filt = SecretRedactionFilter(["super-secret-token"])
    record = logging.LogRecord(
        name="t", level=logging.INFO, pathname=__file__, lineno=1, msg="token super-secret-token", args=(), exc_info=None
    )
    filt.filter(record)
    assert "super-secret-token" not in record.msg


def test_secret_redaction_filter_nested_args_and_headers():
    filt = SecretRedactionFilter(["super-secret-token"])
    record = logging.LogRecord(
        name="t",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg="request failed authorization: Bearer super-secret-token",
        args=({"Authorization": "Bearer super-secret-token", "details": {"private_key": "abc"}},),
        exc_info=None,
    )
    filt.filter(record)
    rendered = str(record.msg) + " " + str(record.args[0])
    assert "super-secret-token" not in rendered
    assert "abc" not in rendered
    assert "***REDACTED***" in rendered


def test_redact_sensitive_text_private_key_block_and_token_patterns():
    text = (
        "authorization=Bearer abc123 token=xyz private_key=mykey "
        "-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----"
    )
    redacted = redact_sensitive_text(text)
    assert "abc123" not in redacted
    assert "xyz" not in redacted
    assert "mykey" not in redacted
    assert "secret" not in redacted


def test_sanitize_error_payload_with_serialized_exception():
    err = RuntimeError("Authorization: Bearer token-123 and private_key=inline-key")
    sanitized = sanitize_error_payload({"error": str(err), "nested": {"token": "token-123"}}, secrets=["token-123"])
    assert "token-123" not in sanitized
    assert "inline-key" not in sanitized

def test_github_client_follow_user_verifies_follow_membership(monkeypatch):
    logger = logging.getLogger("test_follow_verify_membership")
    client = GitHubClient("me", "token", logger)

    responses = [DummyResponse(status_code=204), DummyResponse(status_code=204)]

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.follow_user("alice")
    assert ok is True
    assert status == 204
    assert err is None


def test_github_client_follow_user_fails_when_membership_probe_fails(monkeypatch):
    logger = logging.getLogger("test_follow_verify_fail")
    client = GitHubClient("me", "token", logger, follow_verify_max_retries=2, follow_verify_retry_delay_seconds=0)

    responses = [
        DummyResponse(status_code=204),
        DummyResponse(status_code=404),
        DummyResponse(status_code=404),
        DummyResponse(status_code=200),
    ]

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.follow_user("alice")
    assert ok is False
    assert status == 404
    assert err is not None
    assert "follow_verification_failed" in err
    assert "inferred_visibility=private_or_restricted" in err


def test_github_client_follow_user_infers_not_found_or_blocked_on_verify_404(monkeypatch):
    logger = logging.getLogger("test_follow_verify_not_found")
    client = GitHubClient("me", "token", logger, follow_verify_max_retries=1, follow_verify_retry_delay_seconds=0)

    responses = [
        DummyResponse(status_code=204),
        DummyResponse(status_code=404),
        DummyResponse(status_code=404),
    ]

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.follow_user("alice")
    assert ok is False
    assert status == 404
    assert err is not None
    assert "inferred_visibility=not_found_or_blocked" in err


def test_github_client_follow_user_can_disable_membership_verification(monkeypatch):
    logger = logging.getLogger("test_follow_verify_disabled")
    client = GitHubClient("me", "token", logger, verify_follow_after_put=False)

    requests_seen: list[tuple[str, str]] = []

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        requests_seen.append((method, url))
        return DummyResponse(status_code=204)

    monkeypatch.setattr(client.session, "request", fake_request)
    ok, status, err = client.follow_user("alice")
    assert ok is True
    assert status == 204
    assert err is None
    assert requests_seen == [("PUT", "https://api.github.com/user/following/alice")]

def test_github_client_follow_user_maps_422_abuse_to_throttle(monkeypatch):
    logger = logging.getLogger("test_follow_422_throttle")
    client = GitHubClient("me", "runtime-token", logger)
    monkeypatch.setattr(
        client,
        "_request",
        lambda method, url, **kwargs: DummyResponse(
            status_code=422,
            text='{"message":"You have triggered an abuse detection mechanism. Please wait a few minutes before you try again."}',
        ),
    )

    ok, status, err = client.follow_user("alice")
    assert ok is False
    assert status == 429
    assert err is not None
    assert "follow_throttled_by_github" in err
    assert "upstream_status=422" in err


def test_github_client_follow_user_sanitizes_error_body(monkeypatch):
    logger = logging.getLogger("test_sanitize_follow_user")
    client = GitHubClient("me", "runtime-token", logger)
    monkeypatch.setattr(
        client,
        "_request",
        lambda method, url, **kwargs: DummyResponse(
            status_code=400,
            text='{"error":"authorization: Bearer runtime-token", "private_key":"abc"}',
        ),
    )
    ok, status, err = client.follow_user("alice")
    assert ok is False
    assert status == 400
    assert err is not None
    assert "runtime-token" not in err
    assert "abc" not in err




def test_runtime_file_hardening_check_reports_ok(tmp_path, monkeypatch):
    db = tmp_path / "state.db"
    log = tmp_path / "bot.log"
    db.write_text("", encoding="utf-8")
    log.write_text("", encoding="utf-8")

    monkeypatch.setattr("bot.LOG_FILE", str(log))
    config = BotConfig(github_user="u", github_token="t", db_path=str(db))

    report = runtime_file_hardening_check(config)
    assert report["ok"] is True
    assert report["files"]["db"]["expected_mode_octal"] == "0o600"
    assert report["files"]["log"]["expected_mode_octal"] == "0o640"


def test_doctor_report_includes_file_hardening(tmp_path, monkeypatch):
    db = tmp_path / "state.db"
    log = tmp_path / "bot.log"
    monkeypatch.setattr("bot.LOG_FILE", str(log))

    storage = SQLiteStorageAdapter(str(db))
    _ = setup_logger(redact_secrets=["t"])
    report = doctor_report(BotConfig(github_user="u", github_token="t", db_path=str(db)), storage)

    assert "file_hardening" in report
    assert report["file_hardening"]["db"]["expected_mode_octal"] == "0o600"
    assert report["file_hardening"]["log"]["expected_mode_octal"] == "0o640"

def test_config_from_env(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_DB_PATH", "x.db")
    monkeypatch.setenv("BOT_DRY_RUN", "true")
    monkeypatch.setenv("BOT_MAX_FOLLOWS_PER_RUN", "5")
    monkeypatch.setenv("BOT_CLEANUP_LEGACY_FILES", "false")
    monkeypatch.setenv("BOT_FOLLOW_JOB_MAX_ATTEMPTS", "4")
    monkeypatch.delenv("RELEASE_MANIFEST_SIGNING_KEY", raising=False)
    monkeypatch.delenv("RELEASE_MANIFEST_REQUIRE_SIGNATURE", raising=False)
    monkeypatch.delenv("RELEASE_MANIFEST_MAX_AGE_SECONDS", raising=False)
    monkeypatch.delenv("BOT_DISCOVERY_MODE", raising=False)
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_TOKEN", "app-token")
    monkeypatch.setenv("BOT_AUTH_MODE", "github_app_installation_token")

    config = BotConfig.from_env()
    assert config.github_user == "user"
    assert config.github_token == "app-token"
    assert config.db_engine == "sqlite"
    assert config.db_path == "x.db"
    assert config.dry_run is True
    assert config.max_follows_per_run == 5
    assert config.cleanup_legacy_files is False
    assert config.auth_mode == "github_app_installation_token"
    assert config.follow_job_max_attempts == 4
    assert config.discovery_mode == "followers"
    assert config.release_manifest_signing_key is None
    assert config.release_manifest_require_signature is False
    assert config.release_manifest_max_age_seconds is None


def test_config_from_env_follow_verification_controls(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_VERIFY_FOLLOW_AFTER_PUT", "false")
    monkeypatch.setenv("BOT_FOLLOW_VERIFY_MAX_RETRIES", "4")
    monkeypatch.setenv("BOT_FOLLOW_VERIFY_RETRY_DELAY_SECONDS", "0.25")

    config = BotConfig.from_env()
    assert config.verify_follow_after_put is False
    assert config.follow_verify_max_retries == 4
    assert config.follow_verify_retry_delay_seconds == 0.25


def test_config_from_env_pat_does_not_implicitly_use_installation_token(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_TOKEN", "app-token")
    monkeypatch.delenv("BOT_AUTH_MODE", raising=False)

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "PERSONAL_GITHUB_TOKEN" in str(exc)
        assert "BOT_AUTH_MODE=github_app_installation_token" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError when installation token is provided without explicit BOT_AUTH_MODE")


def test_config_from_env_postgres_requires_dsn(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_DB_ENGINE", "postgres")
    monkeypatch.delenv("BOT_POSTGRES_DSN", raising=False)

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "BOT_POSTGRES_DSN" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError when BOT_DB_ENGINE=postgres without DSN")


def test_config_from_env_invalid_db_engine(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_DB_ENGINE", "mysql")

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "BOT_DB_ENGINE" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError when BOT_DB_ENGINE is invalid")


def test_build_storage_defaults_to_sqlite(tmp_path):
    config = BotConfig(github_user="u", github_token="t", db_path=str(tmp_path / "state.db"))
    storage = build_storage(config)
    assert isinstance(storage, SQLiteStorageAdapter)


def test_config_from_env_invalid_discovery_mode(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_DISCOVERY_MODE", "invalid")

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "BOT_DISCOVERY_MODE" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError when BOT_DISCOVERY_MODE is invalid")


def test_load_postgres_schema_sql_contains_core_tables():
    sql = load_postgres_schema_sql()
    assert "CREATE TABLE IF NOT EXISTS bot_runs" in sql
    assert "CREATE TABLE IF NOT EXISTS follow_jobs" in sql


def test_legacy_migration(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "followers.txt").write_text("alice\nbob\n", encoding="utf-8")

    config = BotConfig(github_user="me", github_token="token", db_path=str(tmp_path / "state.db"), dry_run=True)
    service = FollowBackService(config, logging.getLogger("mig"))

    run_id = service.storage.begin_run(trace_id="trace-mig")
    imported = service.migrate_legacy_files(run_id=run_id, trace_id="trace-mig")
    assert imported == 2
    assert service.storage.get_setting("legacy_migration_done") == "1"
    assert not (tmp_path / "followers.txt").exists()
    assert (tmp_path / "followers.txt.migrated").exists()
    row = service.storage.conn.execute("SELECT run_id FROM security_events WHERE event=? ORDER BY id DESC LIMIT 1", ("legacy_migration",)).fetchone()
    assert row is not None
    assert row[0] == run_id


def test_doctor_and_export(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    report = doctor_report(BotConfig(github_user="u", github_token="t", db_path=str(tmp_path / "state.db")), storage)
    assert report["db_integrity"] == "ok"
    assert report["db_engine"] == "sqlite"
    assert report["db_engine_configured"] is True
    assert report["db_connection_status"] == "ok"
    assert report["schema_version"] == "sqlite-v1"
    assert report["storage_adapter"] == "sqlite"
    assert report["cleanup_legacy_files"] is True
    assert report["auth_mode"] == "pat"
    assert report["discovery_mode"] == "followers"
    assert report["github_app_configured"] is False
    assert report["otel_enabled"] is False
    assert report["cosign_enabled"] is False
    assert report["follow_job_max_attempts"] == 3
    assert report["release_manifest_signing_enabled"] is False
    assert report["release_manifest_require_signature"] is False
    assert report["release_manifest_max_age_seconds"] is None

    payload = storage.export_recent_audit(limit=10)
    parsed = json.loads(json.dumps(payload))
    assert "runs" in parsed
    assert "actions" in parsed


def test_dual_write_report_runtime_postgres_status(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    config = BotConfig(
        github_user="u",
        github_token="t",
        db_engine="postgres",
        postgres_dsn="postgresql://user:pass@localhost:5432/bot",
        db_path=str(tmp_path / "state.db"),
    )
    payload = export_dual_write_consistency_report(config, storage)
    assert payload["status"] == "runtime_postgres"
    assert payload["consistency"] == "n/a"


def test_prometheus_metrics_export(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    run_id = storage.begin_run(trace_id="trace-metrics")
    storage.upsert_follower_seen("alice")
    storage.mark_followed("alice")
    storage.upsert_follower_seen("bob")
    storage.add_follow_action(run_id, "alice", True, 204, None)
    storage.add_follow_action(run_id, "bob", False, 403, "forbidden")
    storage.add_rate_limit_snapshot(run_id, 4999, 1234567890)
    storage.commit()
    storage.finish_run(run_id, 2, 1, None)

    metrics = storage.export_prometheus_metrics()
    assert "github_follower_bot_followers_total 2" in metrics
    assert 'github_follower_bot_follow_actions_total{result="success"} 1' in metrics
    assert "github_follower_bot_rate_limit_remaining 4999" in metrics


def test_follow_job_stats_and_sbom_export(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    run_id = storage.begin_run(trace_id="trace-queue")
    storage.upsert_follow_job(run_id, "alice", "pending")
    storage.upsert_follow_job(run_id, "alice", "done")
    storage.upsert_follow_job(run_id, "bob", "failed", "rate_limit")
    storage.commit()

    stats = storage.get_follow_job_stats(run_id=run_id)
    assert stats["done"] == 1
    assert stats["failed"] == 1
    assert stats["dead_letter"] == 0
    assert stats["total"] == 2

    pending_jobs = storage.fetch_follow_jobs(run_id=run_id, statuses=("failed",))
    assert len(pending_jobs) == 1

    sbom = storage.export_sbom()
    assert sbom["bomFormat"] == "CycloneDX"
    assert isinstance(sbom["components"], list)
    assert any(c["name"] == "requests" for c in sbom["components"])


def test_process_follow_queue_worker_style(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), dry_run=True)
    service = FollowBackService(config, logging.getLogger("worker_test"))

    run_id = service.storage.begin_run(trace_id="trace-worker")
    service.storage.upsert_follow_job(run_id, "alice", "pending")
    service.storage.upsert_follow_job(run_id, "bob", "pending")
    service.storage.commit()

    processed = service.process_follow_queue(run_id=run_id, trace_id="trace-worker", max_jobs=1)
    assert processed == 1

    stats = service.storage.get_follow_job_stats(run_id=run_id)
    assert stats["done"] == 1
    assert stats["pending"] == 1


def test_process_follow_queue_dead_letters_private_or_restricted_profiles(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), dry_run=False)
    service = FollowBackService(config, logging.getLogger("worker_private_profile_test"))

    run_id = service.storage.begin_run(trace_id="trace-private")
    service.storage.upsert_follow_job(run_id, "alice", "pending")
    service.storage.commit()

    monkeypatch.setattr(
        service.github,
        "follow_user",
        lambda username: (
            False,
            404,
            "follow_verification_failed username=alice status=404 attempt=2/2 inferred_visibility=private_or_restricted",
        ),
    )
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    first = service.process_follow_queue(run_id=run_id, trace_id="trace-private")
    assert first == 0
    stats_after_first = service.storage.get_follow_job_stats(run_id=run_id)
    assert stats_after_first["dead_letter"] == 1
    assert stats_after_first["failed"] == 0

    second = service.process_follow_queue(run_id=run_id, trace_id="trace-private")
    assert second == 0
    stats_after_second = service.storage.get_follow_job_stats(run_id=run_id)
    assert stats_after_second["dead_letter"] == 1
    assert stats_after_second["pending"] == 0


def test_release_manifest_export(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    manifest = storage.export_release_manifest(signing_key="local-key")
    assert manifest["algorithm"] == "sha256"
    assert isinstance(manifest["artifacts"], list)
    assert any(item["path"] == "bot.py" for item in manifest["artifacts"])
    assert manifest["signature"]["method"] == "hmac-sha256"


def test_config_invalid_github_app_command_timeout(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS", "0")

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError for invalid command timeout")


def test_config_invalid_auth_mode(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_AUTH_MODE", "invalid")

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "BOT_AUTH_MODE" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError for invalid BOT_AUTH_MODE")



def test_config_from_env_github_app(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_APP_INSTALLATION_TOKEN", raising=False)
    monkeypatch.setenv("BOT_AUTH_MODE", "github_app")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "67890")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----")

    config = BotConfig.from_env()
    assert config.auth_mode == "github_app"
    assert config.github_app_id == "12345"
    assert config.github_app_installation_id == "67890"
    assert config.github_token == "__github_app_runtime_token__"




def test_config_github_app_private_key_file_must_exist(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("BOT_AUTH_MODE", "github_app")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "67890")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_FILE", "/tmp/non-existent-bot-key.pem")

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "GITHUB_APP_PRIVATE_KEY_FILE" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError for missing private-key file")


def test_config_from_env_github_app_private_key_file(tmp_path, monkeypatch):
    key_path = tmp_path / "github_app_key.pem"
    key_path.write_text("-----BEGIN PRIVATE KEY-----\nfrom-file\n-----END PRIVATE KEY-----\n", encoding="utf-8")

    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_APP_INSTALLATION_TOKEN", raising=False)
    monkeypatch.setenv("BOT_AUTH_MODE", "github_app")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "67890")
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_FILE", str(key_path))

    config = BotConfig.from_env()
    assert config.auth_mode == "github_app"
    assert config.github_app_private_key_file == str(key_path)
    assert config.resolve_github_app_private_key() == "-----BEGIN PRIVATE KEY-----\nfrom-file\n-----END PRIVATE KEY-----"


def test_config_from_env_github_app_private_key_file_candidates(tmp_path, monkeypatch):
    key_path = tmp_path / "github_app_key.pem"
    key_path.write_text("-----BEGIN PRIVATE KEY-----\nfrom-file\n-----END PRIVATE KEY-----\n", encoding="utf-8")

    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_APP_INSTALLATION_TOKEN", raising=False)
    monkeypatch.setenv("BOT_AUTH_MODE", "github_app")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "67890")
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_FILE", f"/tmp/missing-key.pem,{key_path}")

    config = BotConfig.from_env()
    assert config.auth_mode == "github_app"
    assert config.github_app_private_key_file == str(key_path)
    assert config.github_app_private_key_file_candidates == ("/tmp/missing-key.pem", str(key_path))


def test_config_github_app_private_key_file_candidates_must_exist(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("BOT_AUTH_MODE", "github_app")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "67890")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_FILE", "/tmp/missing-a.pem,/tmp/missing-b.pem")

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "existing file" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError when no private-key file candidate exists")


def test_config_from_env_github_app_token_refresh_skew(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_APP_INSTALLATION_TOKEN", raising=False)
    monkeypatch.setenv("BOT_AUTH_MODE", "github_app")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "67890")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----")
    monkeypatch.setenv("BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS", "120")

    config = BotConfig.from_env()
    assert config.github_app_token_refresh_skew_seconds == 120


def test_config_from_env_github_app_private_key_command_timeout(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_APP_INSTALLATION_TOKEN", raising=False)
    monkeypatch.setenv("BOT_AUTH_MODE", "github_app")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "67890")
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_FILE", raising=False)
    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY_COMMAND",
        "python -c \"print('-----BEGIN PRIVATE KEY-----\nfrom-command\n-----END PRIVATE KEY-----')\"",
    )
    monkeypatch.setenv("BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS", "3")

    config = BotConfig.from_env()
    assert config.github_app_private_key_command_timeout_seconds == 3


def test_config_from_env_github_app_private_key_command(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_APP_INSTALLATION_TOKEN", raising=False)
    monkeypatch.setenv("BOT_AUTH_MODE", "github_app")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "67890")
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("GITHUB_APP_PRIVATE_KEY_FILE", raising=False)
    monkeypatch.setenv(
        "GITHUB_APP_PRIVATE_KEY_COMMAND",
        "python -c \"print('-----BEGIN PRIVATE KEY-----\\nfrom-command\\n-----END PRIVATE KEY-----')\"",
    )

    config = BotConfig.from_env()
    assert config.auth_mode == "github_app"
    assert config.github_app_private_key_command is not None
    assert config.resolve_github_app_private_key() == "-----BEGIN PRIVATE KEY-----\nfrom-command\n-----END PRIVATE KEY-----"


def test_resolve_private_key_command_empty_argv_raises():
    config = BotConfig(
        github_user="u",
        github_token="t",
        auth_mode="github_app",
        github_app_id="123",
        github_app_installation_id="456",
        github_app_private_key_command="   ",
    )

    try:
        config.resolve_github_app_private_key()
    except RuntimeError as exc:
        assert "empty argv" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for empty command argv")


def test_config_github_app_rejects_multiple_private_key_sources(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("BOT_AUTH_MODE", "github_app")
    monkeypatch.setenv("GITHUB_APP_ID", "12345")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "67890")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "inline")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_FILE", "/tmp/key.pem")

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "Use only one private key source" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError for multiple key sources")


def test_config_github_app_missing_env(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.delenv("PERSONAL_GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("BOT_AUTH_MODE", "github_app")
    monkeypatch.delenv("GITHUB_APP_ID", raising=False)
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "67890")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "k")

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "GITHUB_APP_ID" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError for missing github app env")


def test_issue_github_app_installation_token_details(monkeypatch):
    monkeypatch.setattr("bot.jwt.encode", lambda payload, key, algorithm: "signed-jwt")

    class FakeSession:
        def post(self, url, headers=None, timeout=None):
            assert "Bearer signed-jwt" == headers.get("Authorization")
            return DummyResponse(status_code=201, payload={"token": "inst-token", "expires_at": "2030-01-01T00:00:00Z"})

    token, expires_at_epoch = issue_github_app_installation_token_details(
        app_id="123",
        installation_id="456",
        private_key_pem="-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
        session=FakeSession(),
    )
    assert token == "inst-token"
    assert isinstance(expires_at_epoch, int)


def test_issue_github_app_installation_token(monkeypatch):
    monkeypatch.setattr("bot.jwt.encode", lambda payload, key, algorithm: "signed-jwt")

    class FakeSession:
        def post(self, url, headers=None, timeout=None):
            assert "Bearer signed-jwt" == headers.get("Authorization")
            return DummyResponse(status_code=201, payload={"token": "inst-token"})

    token = issue_github_app_installation_token(
        app_id="123",
        installation_id="456",
        private_key_pem="-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
        session=FakeSession(),
    )
    assert token == "inst-token"


def test_followback_service_github_app_mode(monkeypatch, tmp_path):
    monkeypatch.setattr("bot.issue_github_app_installation_token_details", lambda app_id, installation_id, private_key_pem, session=None: ("inst-token", None))
    config = BotConfig(
        github_user="me",
        github_token="__github_app_runtime_token__",
        db_path=str(tmp_path / "state.db"),
        auth_mode="github_app",
        github_app_id="123",
        github_app_installation_id="456",
        github_app_private_key="pem",
    )
    service = FollowBackService(config, logging.getLogger("service_github_app"))
    assert service.github.token == "inst-token"


def test_followback_service_github_app_refresh_provider(monkeypatch, tmp_path):
    calls = {"count": 0}

    def fake_issue(app_id, installation_id, private_key_pem, session=None):
        calls["count"] += 1
        return f"inst-token-{calls['count']}", None

    monkeypatch.setattr("bot.issue_github_app_installation_token_details", fake_issue)
    config = BotConfig(
        github_user="me",
        github_token="__github_app_runtime_token__",
        db_path=str(tmp_path / "state.db"),
        auth_mode="github_app",
        github_app_id="123",
        github_app_installation_id="456",
        github_app_private_key="pem",
    )
    service = FollowBackService(config, logging.getLogger("service_github_app_refresh"))
    refreshed = service.github._refresh_runtime_token()
    assert refreshed is True
    assert calls["count"] == 2
    assert service.github.token == "inst-token-2"




def test_doctor_reports_private_key_source_and_timeout(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    config = BotConfig(
        github_user="u",
        github_token="t",
        db_path=str(tmp_path / "state.db"),
        auth_mode="github_app",
        github_app_id="123",
        github_app_installation_id="456",
        github_app_private_key_command="python -c \"print(\'k\')\"",
        github_app_private_key_command_timeout_seconds=7,
    )
    report = doctor_report(config, storage)
    assert report["github_app_private_key_source"] == "command"
    assert report["github_app_private_key_file_candidates"] == []
    assert report["github_app_private_key_command_timeout_seconds"] == 7
    assert report["github_app_token_refresh_skew_seconds"] == 60
    assert report["otel_exporter_otlp_endpoint_configured"] is False


def test_doctor_github_app_configured_with_private_key_file(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    config = BotConfig(
        github_user="u",
        github_token="t",
        db_path=str(tmp_path / "state.db"),
        auth_mode="github_app",
        github_app_id="123",
        github_app_installation_id="456",
        github_app_private_key_file="/tmp/app.pem",
    )
    report = doctor_report(config, storage)
    assert report["github_app_configured"] is True
    assert report["github_app_private_key_file_candidates"] == []


def test_doctor_reports_private_key_file_candidates(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    config = BotConfig(
        github_user="u",
        github_token="t",
        db_path=str(tmp_path / "state.db"),
        auth_mode="github_app",
        github_app_id="123",
        github_app_installation_id="456",
        github_app_private_key_file="/tmp/app-current.pem",
        github_app_private_key_file_candidates=("/tmp/app-next.pem", "/tmp/app-current.pem"),
    )
    report = doctor_report(config, storage)
    assert report["github_app_private_key_file_candidates"] == ["/tmp/app-next.pem", "/tmp/app-current.pem"]


def test_follow_jobs_dead_letter_after_retry_budget(monkeypatch, tmp_path):
    config = BotConfig(
        github_user="me",
        github_token="token",
        db_path=str(tmp_path / "state.db"),
        follow_job_max_attempts=2,
    )
    service = FollowBackService(config, logging.getLogger("service_dlq"))
    run_id = service.storage.begin_run(trace_id="trace-dlq")
    service.storage.upsert_follow_job(run_id, "alice", "pending")
    service.storage.commit()

    monkeypatch.setattr(service.github, "follow_user", lambda username: (False, 500, "server_error"))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    first = service.process_follow_queue(run_id=run_id, trace_id="trace-dlq")
    assert first == 0
    stats_first = service.storage.get_follow_job_stats(run_id=run_id)
    assert stats_first["failed"] == 1
    assert stats_first["dead_letter"] == 0

    second = service.process_follow_queue(run_id=run_id, trace_id="trace-dlq")
    assert second == 0
    stats_second = service.storage.get_follow_job_stats(run_id=run_id)
    assert stats_second["failed"] == 0
    assert stats_second["dead_letter"] == 1

    dead_letter_event = service.storage.conn.execute(
        "SELECT run_id FROM security_events WHERE event=? ORDER BY id DESC LIMIT 1",
        ("follow_job_dead_lettered",),
    ).fetchone()
    assert dead_letter_event is not None
    assert dead_letter_event[0] == run_id


def test_verify_release_manifest(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    manifest = storage.export_release_manifest(signing_key="local-key")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = storage.verify_release_manifest(str(path), signing_key="local-key")
    assert result["ok"] is True
    assert result["verified"] == result["total"]
    assert result["signature"]["verified"] is True


def test_verify_release_manifest_signature_missing_key(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    manifest = storage.export_release_manifest(signing_key="local-key")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = storage.verify_release_manifest(str(path))
    assert result["ok"] is False
    assert any(item["reason"] == "missing_signing_key" for item in result["mismatches"])


def test_verify_release_manifest_signature_mismatch(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    manifest = storage.export_release_manifest(signing_key="local-key")
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = storage.verify_release_manifest(str(path), signing_key="wrong-key")
    assert result["ok"] is False
    assert any(item["reason"] == "signature_mismatch" for item in result["mismatches"])


def test_verify_release_manifest_require_signature_without_signature(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    manifest = storage.export_release_manifest()
    path = tmp_path / "manifest_unsigned.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = storage.verify_release_manifest(str(path), require_signature=True)
    assert result["ok"] is False
    assert result["signature"]["required"] is True
    assert result["signature"]["reason"] == "missing_signature"
    assert any(item["reason"] == "missing_signature" for item in result["mismatches"])


def test_verify_release_manifest_expired(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    manifest = storage.export_release_manifest(signing_key="local-key")
    manifest["generated_at"] = "2000-01-01T00:00:00+00:00"
    path = tmp_path / "manifest_old.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = storage.verify_release_manifest(str(path), signing_key="local-key", require_signature=True, max_age_seconds=60)
    assert result["ok"] is False
    assert result["age"]["checked"] is True
    assert result["age"]["reason"] == "manifest_expired"
    assert any(item["reason"] == "manifest_expired" for item in result["mismatches"])


def test_verify_release_manifest_invalid_generated_at(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    manifest = storage.export_release_manifest(signing_key="local-key")
    manifest["generated_at"] = "not-a-timestamp"
    path = tmp_path / "manifest_bad_time.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = storage.verify_release_manifest(str(path), signing_key="local-key", max_age_seconds=60)
    assert result["ok"] is False
    assert result["age"]["checked"] is True
    assert result["age"]["reason"] == "invalid_generated_at"
    assert any(item["reason"] == "invalid_generated_at" for item in result["mismatches"])


def test_export_postgres_migration_profile_contains_tables(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    run_id = storage.begin_run(trace_id="trace-migrate")
    storage.upsert_follower_seen("alice")
    storage.add_follow_action(run_id, "alice", True, 204, None)
    storage.add_security_event("migration_test", "ok", run_id=run_id)
    storage.commit()

    payload = storage.export_postgres_migration_profile()
    assert payload["source_engine"] == "sqlite"
    assert payload["target_engine"] == "postgresql"
    assert "bot_runs" in payload["tables"]
    assert "follow_jobs" in payload["tables"]
    assert payload["row_counts"]["followers"] >= 1
    assert "CREATE TABLE IF NOT EXISTS bot_runs" in payload["ddl"]["bot_runs"]
    profile = payload["horizontal_scaling_profile"]
    assert profile["benchmark_samples"] == 50
    assert "avg_query_ms" in profile
    assert profile["avg_query_ms"]["followers_total_count"] >= 0


def test_policy_engine_blocks_denylisted_user(tmp_path):
    db = tmp_path / "state.db"
    logger = logging.getLogger("policy_test")
    config = BotConfig(github_user="u", github_token="t", db_path=str(db))
    service = FollowBackService(config, logger)
    service.policy_engine = service.policy_engine.__class__(denylist={"blocked-user"})
    decision = service.policy_engine.evaluate_follow("blocked-user")
    assert decision.allowed is False
    assert decision.reason == "denylist"


def test_export_dual_write_consistency_report_without_postgres(tmp_path, monkeypatch):
    db = tmp_path / "state.db"
    storage = BotStorage(str(db))
    config = BotConfig(github_user="u", github_token="t", db_path=str(db))
    monkeypatch.delenv("BOT_POSTGRES_DSN", raising=False)

    payload = export_dual_write_consistency_report(config, storage)
    assert payload["postgres_configured"] is False
    assert payload["status"] == "shadow_not_configured"
    assert payload["consistency"] == "unknown"


def test_config_from_env_expand_budgets_and_breaker(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_MAX_CANDIDATES_PER_RUN", "2")
    monkeypatch.setenv("BOT_MAX_API_CALLS_PER_RUN", "3")
    monkeypatch.setenv("BOT_MAX_EXPAND_SEEDS_PER_RUN", "4")
    monkeypatch.setenv("BOT_EXPAND_HTTP_ERROR_WINDOW", "6")
    monkeypatch.setenv("BOT_EXPAND_HTTP_ERROR_THRESHOLD", "2")

    config = BotConfig.from_env()
    assert config.max_candidates_per_run == 2
    assert config.max_api_calls_per_run == 3
    assert config.max_expand_seeds_per_run == 4
    assert config.expand_http_error_window == 6
    assert config.expand_http_error_threshold == 2


def test_config_from_env_invalid_expand_limits(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_MAX_API_CALLS_PER_RUN", "0")

    try:
        BotConfig.from_env()
    except EnvironmentError as exc:
        assert "BOT_MAX_API_CALLS_PER_RUN" in str(exc)
    else:
        raise AssertionError("Expected EnvironmentError for BOT_MAX_API_CALLS_PER_RUN=0")


def test_doctor_report_includes_expand_limits(tmp_path):
    storage = BotStorage(str(tmp_path / "state.db"))
    config = BotConfig(
        github_user="u",
        github_token="t",
        db_path=str(tmp_path / "state.db"),
        max_candidates_per_run=10,
        max_api_calls_per_run=20,
        max_expand_seeds_per_run=3,
        expand_http_error_window=15,
        expand_http_error_threshold=5,
    )
    report = doctor_report(config, storage)
    assert report["max_candidates_per_run"] == 10
    assert report["max_api_calls_per_run"] == 20
    assert report["max_expand_seeds_per_run"] == 3


def test_expand_limit_max_candidates_per_run(monkeypatch, tmp_path, caplog):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand", max_candidates_per_run=1)
    service = FollowBackService(config, logging.getLogger("expand_max_candidates_test"))

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [[{"login": "alice"}, {"login": "bob"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    with caplog.at_level(logging.INFO):
        result = service.run()
    assert result["followers_fetched"] == 1
    assert any(getattr(record, "event", "") == "expand_budget_reached" for record in caplog.records)


def test_expand_limit_max_candidates_per_run_applies_globally_across_seeds(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand", max_candidates_per_run=2)
    service = FollowBackService(config, logging.getLogger("expand_max_candidates_global_test"))

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}, {"login": "seed2"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [{"login": f"{username}-a"}, {"login": f"{username}-b"}] if page == 1 else [])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_fetched"] == 2
    assert result["followers_followed"] == 2



def test_expand_limit_max_api_calls_per_run(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand", max_api_calls_per_run=1)
    service = FollowBackService(config, logging.getLogger("expand_max_api_calls_test"))

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [{"login": "seed1"}] if page == 1 else [])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [{"login": "alice"}] if page == 1 else [])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_fetched"] == 0
    assert result["followers_followed"] == 0


def test_expand_limit_max_expand_seeds_per_run(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand", max_expand_seeds_per_run=1)
    service = FollowBackService(config, logging.getLogger("expand_max_seeds_test"))

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}, {"login": "seed2"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [{"login": f"{username}-candidate"}] if page == 1 else [])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_fetched"] == 1


def test_expand_circuit_breaker_opens_on_repeated_429(monkeypatch, tmp_path, caplog):
    db = tmp_path / "state.db"
    config = BotConfig(
        github_user="me",
        github_token="token",
        db_path=str(db),
        discovery_mode="expand",
        expand_http_error_window=5,
        expand_http_error_threshold=2,
    )
    service = FollowBackService(config, logging.getLogger("expand_breaker_429"))

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}, {"login": "seed2"}], []][page - 1])

    def raise_429(username, page, per_page):
        raise Exception("failed to fetch user followers username=x page=1 status=429")

    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: (_ for _ in ()).throw(__import__("requests").exceptions.RequestException(f"failed to fetch user followers username={username} page={page} status=429")))
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    with caplog.at_level(logging.WARNING):
        result = service.run()
    assert result["followers_fetched"] == 0
    assert any(getattr(r, "event", "") == "expand_circuit_breaker_open" for r in caplog.records)


def test_expand_circuit_breaker_opens_on_sustained_5xx(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand", expand_http_error_threshold=2)
    service = FollowBackService(config, logging.getLogger("expand_breaker_5xx"))

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}, {"login": "seed2"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: (_ for _ in ()).throw(__import__("requests").exceptions.RequestException(f"failed to fetch user followers username={username} page={page} status=502")))
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_fetched"] == 0


def test_expand_circuit_breaker_does_not_open_on_sporadic_errors(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand", expand_http_error_threshold=3)
    service = FollowBackService(config, logging.getLogger("expand_breaker_sporadic"))

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}, {"login": "seed2"}], []][page - 1])

    calls = {"count": 0}

    def followers(username, page, per_page):
        calls["count"] += 1
        if calls["count"] == 1:
            raise __import__("requests").exceptions.RequestException("failed to fetch user followers username=seed1 page=1 status=502")
        return [{"login": "alice"}] if page == 1 else []

    monkeypatch.setattr(service.github, "fetch_user_followers", followers)
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_fetched"] >= 1


def test_expand_cursor_invalid_values_recover_safely(monkeypatch, tmp_path, caplog):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand")
    service = FollowBackService(config, logging.getLogger("expand_cursor_recover"))

    service.storage.set_setting("expand_seed_index", "999")
    service.storage.set_setting("expand_seed_page", "-8")
    service.storage.commit()

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [{"login": "alice"}] if page == 1 else [])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    with caplog.at_level(logging.WARNING):
        result = service.run()
    assert result["followers_fetched"] == 1
    assert any(getattr(record, "event", "") == "expand_cursor_recovered" for record in caplog.records)




def test_expand_cursor_zero_page_recovers_to_first_page(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand")
    service = FollowBackService(config, logging.getLogger("expand_cursor_zero_page"))
    service.storage.set_setting("expand_seed_page", "0")
    service.storage.commit()

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [{"login": "alice"}] if page == 1 else [])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_fetched"] == 1


def test_expand_cursor_non_numeric_page_recover_safely(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand")
    service = FollowBackService(config, logging.getLogger("expand_cursor_non_numeric"))
    service.storage.set_setting("expand_seed_page", "NaN")
    service.storage.commit()

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [{"login": "alice"}] if page == 1 else [])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    assert result["followers_fetched"] == 1


def test_resume_after_partial_expand_seed_does_not_duplicate_follow_jobs(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand")
    service = FollowBackService(config, logging.getLogger("expand_resume_no_dups"))

    service.storage.set_setting("expand_seed_index", "0")
    service.storage.set_setting("expand_seed_login", "seed1")
    service.storage.set_setting("expand_seed_phase", "followers")
    service.storage.set_setting("expand_seed_page", "bad")
    service.storage.commit()

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [{"login": "alice"}] if page in {1, 2} else [])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    result = service.run()
    rows = service.storage.conn.execute(
        "SELECT COUNT(*) FROM follow_jobs WHERE run_id=? AND github_login='alice'",
        (result["run_id"],),
    ).fetchone()
    assert rows is not None
    assert int(rows[0]) == 1


def test_export_audit_includes_discovery_context(monkeypatch, tmp_path):
    db = tmp_path / "state.db"
    config = BotConfig(github_user="me", github_token="token", db_path=str(db), discovery_mode="expand")
    service = FollowBackService(config, logging.getLogger("audit_discovery_context"))

    monkeypatch.setattr(service.github, "check_rate_limit", lambda: (5000, 0))
    monkeypatch.setattr(service.github, "fetch_my_following", lambda page, per_page: [[{"login": "seed1"}], []][page - 1])
    monkeypatch.setattr(service.github, "fetch_user_followers", lambda username, page, per_page: [{"login": "alice"}] if page == 1 else [])
    monkeypatch.setattr(service.github, "fetch_user_following", lambda username, page, per_page: [])
    monkeypatch.setattr(service.github, "follow_user", lambda username: (True, 204, None))
    monkeypatch.setattr("bot.time.sleep", lambda *_: None)

    service.run()
    payload = service.storage.export_recent_audit(limit=20)
    assert payload["actions"]
    last_action = payload["actions"][0]
    assert "discovery_context" in last_action
    assert "seed_login" in str(last_action["discovery_context"])


def test_config_from_env_max_forks_per_run(monkeypatch):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_MAX_FORKS_PER_RUN", "7")

    config = BotConfig.from_env()
    assert config.max_forks_per_run == 7


def test_fork_repos_profile_readme_requires_explicit_flag(monkeypatch, tmp_path):
    config = BotConfig(github_user="me", github_token="token", db_path=str(tmp_path / "state.db"))
    service = FollowBackService(config, logging.getLogger("fork_profile_readme_opt_in"))

    monkeypatch.setattr(
        service.github,
        "fetch_user_repositories",
        lambda username, page, per_page: (
            [
                {"full_name": "alice/alice", "name": "alice", "owner": {"login": "alice"}, "fork": False},
                {"full_name": "alice/project", "name": "project", "owner": {"login": "alice"}, "fork": False},
            ]
            if page == 1
            else []
        ),
    )

    seen_forks: list[str] = []
    monkeypatch.setattr(service.github, "fork_repository", lambda full_name: (seen_forks.append(full_name) or True, 202, None))

    payload = service.fork_repositories_for_user(
        target_username="alice",
        include_owned=True,
        include_forked=False,
        include_profile_readme=False,
        fork_sources_for_forks=False,
        follow_fork_owners=False,
    )
    assert payload["forked"] == 1
    assert seen_forks == ["alice/project"]


def test_fork_repos_continues_after_repository_exception(monkeypatch, tmp_path):
    config = BotConfig(github_user="me", github_token="token", db_path=str(tmp_path / "state.db"))
    service = FollowBackService(config, logging.getLogger("fork_continue_after_error"))

    monkeypatch.setattr(
        service.github,
        "fetch_user_repositories",
        lambda username, page, per_page: (
            [
                {"full_name": "alice/bad", "name": "bad", "owner": {"login": "alice"}, "fork": False},
                {"full_name": "alice/good", "name": "good", "owner": {"login": "alice"}, "fork": False},
            ]
            if page == 1
            else []
        ),
    )

    def fake_fork(full_name: str):
        if full_name.endswith("bad"):
            raise RuntimeError("boom")
        return True, 202, None

    monkeypatch.setattr(service.github, "fork_repository", fake_fork)

    payload = service.fork_repositories_for_user(
        target_username="alice",
        include_owned=True,
        include_forked=False,
        include_profile_readme=False,
        fork_sources_for_forks=False,
        follow_fork_owners=False,
    )
    assert payload["queued"] == 2
    assert payload["failed"] == 1
    assert payload["forked"] == 1
