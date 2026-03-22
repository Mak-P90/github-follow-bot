import logging

from bot import BotConfig, FollowBackService
from core.application.capabilities.fork_discovery_service import ForkDiscoveryService


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


def test_fork_discovery_service_profile_readme_requires_opt_in(monkeypatch, tmp_path):
    config = BotConfig(github_user="me", github_token="token", db_path=str(tmp_path / "state.db"))
    follow_service = FollowBackService(config, logging.getLogger("fork_discovery_opt_in"))

    monkeypatch.setattr(
        follow_service.github,
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
    monkeypatch.setattr(follow_service.github, "fork_repository", lambda full_name: (seen_forks.append(full_name) or True, 202, None))

    service = ForkDiscoveryService(
        config,
        logging.getLogger("fork_discovery_service"),
        follow_service.storage,
        github=follow_service.github,
        sanitize_error_payload_fn=follow_service._sanitize_error_payload,
    )

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


def test_fork_discovery_service_continues_after_repository_exception(monkeypatch, tmp_path):
    config = BotConfig(github_user="me", github_token="token", db_path=str(tmp_path / "state.db"))
    follow_service = FollowBackService(config, logging.getLogger("fork_discovery_recovery"))

    monkeypatch.setattr(
        follow_service.github,
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

    monkeypatch.setattr(follow_service.github, "fork_repository", fake_fork)

    service = ForkDiscoveryService(
        config,
        logging.getLogger("fork_discovery_service"),
        follow_service.storage,
        github=follow_service.github,
        sanitize_error_payload_fn=follow_service._sanitize_error_payload,
    )

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


def test_fork_discovery_service_emits_runtime_span(monkeypatch, tmp_path):
    config = BotConfig(github_user="me", github_token="token", db_path=str(tmp_path / "state.db"))
    follow_service = FollowBackService(config, logging.getLogger("fork_discovery_span"))
    telemetry = DummyTelemetry()

    monkeypatch.setattr(
        follow_service.github,
        "fetch_user_repositories",
        lambda username, page, per_page: ([] if page > 1 else [{"full_name": "alice/project", "name": "project", "owner": {"login": "alice"}, "fork": False}]),
    )
    monkeypatch.setattr(follow_service.github, "fork_repository", lambda full_name: (True, 202, None))

    service = ForkDiscoveryService(
        config,
        logging.getLogger("fork_discovery_service"),
        follow_service.storage,
        github=follow_service.github,
        sanitize_error_payload_fn=follow_service._sanitize_error_payload,
        telemetry=telemetry,
    )

    payload = service.fork_repositories_for_user(
        target_username="alice",
        include_owned=True,
        include_forked=False,
        include_profile_readme=False,
        fork_sources_for_forks=False,
        follow_fork_owners=False,
    )
    assert payload["forked"] == 1
    assert telemetry.spans
    name, attributes = telemetry.spans[0]
    assert name == "fork_repos.run"
    assert attributes["target_username"] == "alice"
    assert attributes["capability"] == "fork-repos"
