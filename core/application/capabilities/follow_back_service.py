from __future__ import annotations

import json
import logging
import os
import random
import re
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from requests.exceptions import RequestException

from core.application.capabilities.fork_discovery_service import ForkDiscoveryService
from core.application.telemetry_attrs import build_telemetry_attributes
from core.domain.contracts import StoragePort

def _resolve_default_dependencies() -> dict[str, Any]:
    from bot import (
        DELAY_BETWEEN_FOLLOWS,
        LEGACY_FILES,
        RATE_LIMIT_THRESHOLD,
        GitHubClient,
        PolicyEngine,
        TelemetryRuntime,
        build_storage,
        issue_github_app_installation_token_details,
        sanitize_error_payload,
    )

    return {
        "telemetry_runtime_factory": TelemetryRuntime,
        "storage_builder": build_storage,
        "github_client_cls": GitHubClient,
        "policy_engine_cls": PolicyEngine,
        "issue_token_details": issue_github_app_installation_token_details,
        "sanitize_error_payload_fn": sanitize_error_payload,
        "legacy_files": list(LEGACY_FILES),
        "rate_limit_threshold": RATE_LIMIT_THRESHOLD,
        "delay_between_follows": DELAY_BETWEEN_FOLLOWS,
    }


class FollowBackService:
    EXPAND_CURSOR_INDEX_KEY = "expand_seed_index"
    EXPAND_CURSOR_LOGIN_KEY = "expand_seed_login"
    EXPAND_CURSOR_PHASE_KEY = "expand_seed_phase"
    EXPAND_CURSOR_PAGE_KEY = "expand_seed_page"

    def _issue_runtime_token(self) -> str:
        token, expires_at_epoch = self._issue_token_details(
            app_id=str(self.config.github_app_id),
            installation_id=str(self.config.github_app_installation_id),
            private_key_pem=self.config.resolve_github_app_private_key(),
        )
        self._runtime_token_expires_at_epoch = expires_at_epoch
        return token

    def _runtime_token_expiring_soon(self) -> bool:
        if self._runtime_token_expires_at_epoch is None:
            return False
        return int(time.time()) + self.config.github_app_token_refresh_skew_seconds >= self._runtime_token_expires_at_epoch

    def __init__(
        self,
        config: Any,
        logger: logging.Logger,
        storage: StoragePort | None = None,
        *,
        telemetry_runtime_factory: Callable[[Any], Any] | None = None,
        storage_builder: Callable[[Any], StoragePort] | None = None,
        github_client_cls: Any | None = None,
        policy_engine_cls: Any | None = None,
        issue_token_details: Callable[..., tuple[str, int]] | None = None,
        sanitize_error_payload_fn: Callable[[Any, list[str] | None], str] | None = None,
        legacy_files: list[str] | None = None,
        rate_limit_threshold: int | None = None,
        delay_between_follows: float | None = None,
    ) -> None:
        defaults = _resolve_default_dependencies()
        telemetry_runtime_factory = telemetry_runtime_factory or defaults["telemetry_runtime_factory"]
        storage_builder = storage_builder or defaults["storage_builder"]
        github_client_cls = github_client_cls or defaults["github_client_cls"]
        policy_engine_cls = policy_engine_cls or defaults["policy_engine_cls"]
        issue_token_details = issue_token_details or defaults["issue_token_details"]
        sanitize_error_payload_fn = sanitize_error_payload_fn or defaults["sanitize_error_payload_fn"]
        legacy_files = legacy_files or defaults["legacy_files"]
        rate_limit_threshold = rate_limit_threshold if rate_limit_threshold is not None else defaults["rate_limit_threshold"]
        delay_between_follows = delay_between_follows if delay_between_follows is not None else defaults["delay_between_follows"]

        self.config = config
        self.logger = logger
        self.telemetry = telemetry_runtime_factory(config)
        self.storage: StoragePort = storage or storage_builder(config)
        policy_denylist = {entry.strip().lower() for entry in os.getenv("BOT_POLICY_DENYLIST", "").split(",") if entry.strip()}
        self.policy_engine = policy_engine_cls(
            require_consent=os.getenv("BOT_POLICY_REQUIRE_CONSENT", "false").strip().lower() in {"1", "true", "yes", "on"},
            denylist=policy_denylist,
            retention_window_days=int(os.getenv("BOT_POLICY_RETENTION_DAYS", "365") or "365"),
        )


        self._issue_token_details = issue_token_details
        self._sanitize_error_payload = sanitize_error_payload_fn
        self._legacy_files = legacy_files
        self._rate_limit_threshold = int(rate_limit_threshold)
        self._delay_between_follows = float(delay_between_follows)

        runtime_token = config.github_token
        token_provider: Callable[[], str] | None = None
        token_expiring_soon: Callable[[], bool] | None = None
        self._runtime_token_expires_at_epoch: int | None = None
        if config.auth_mode == "github_app":
            token_provider = self._issue_runtime_token
            token_expiring_soon = self._runtime_token_expiring_soon
            runtime_token = token_provider()
            self.logger.info("github_app_token_issued", extra={"event": "github_app_token_issued"})

        self.github = github_client_cls(
            config.github_user,
            runtime_token,
            logger,
            token_provider=token_provider,
            token_expiring_soon=token_expiring_soon,
            tracer=self.telemetry.tracer,
            auth_mode=config.auth_mode,
            verify_follow_after_put=config.verify_follow_after_put,
            follow_verify_max_retries=config.follow_verify_max_retries,
            follow_verify_retry_delay_seconds=config.follow_verify_retry_delay_seconds,
        )
        self._expand_api_calls = 0
        self._expand_error_status_window: deque[int] = deque(maxlen=self.config.expand_http_error_window)
        self._expand_breaker_open = False
        self._candidate_context_by_run: dict[int, dict[str, dict[str, object]]] = {}

    def _archive_legacy_file(self, path: Path) -> str:
        archived_path = path.with_name(f"{path.name}.migrated")
        if archived_path.exists():
            suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            archived_path = path.with_name(f"{path.name}.migrated.{suffix}")
        path.rename(archived_path)
        return str(archived_path)

    def migrate_legacy_files(self, run_id: int, trace_id: str) -> int:
        if self.storage.get_setting("legacy_migration_done") == "1":
            return 0

        imported = 0
        archived_files: list[dict[str, str]] = []

        for file_name in self._legacy_files:
            path = Path(file_name)
            if not path.exists():
                continue

            content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in content:
                username = line.strip()
                if not username:
                    continue
                self.storage.upsert_follower_seen(username)
                imported += 1

            if self.config.cleanup_legacy_files:
                archived_to = self._archive_legacy_file(path)
                archived_files.append({"source": file_name, "archived_to": archived_to})
                self.logger.info(
                    f"legacy_file_archived source={file_name} archived_to={archived_to}",
                    extra={"event": "legacy_file_archived", "run_id": run_id, "trace_id": trace_id},
                )

        self.storage.set_setting("legacy_migration_done", "1")
        self.storage.add_security_event(
            "legacy_migration",
            json.dumps({
                "imported_candidates": imported,
                "cleanup_enabled": self.config.cleanup_legacy_files,
                "archived_files": archived_files,
            }),
            run_id=run_id,
        )
        self.storage.commit()
        return imported

    def _is_private_or_restricted_failure(self, diagnostic: str | None) -> bool:
        return "inferred_visibility=private_or_restricted" in str(diagnostic or "")

    def fork_repositories_for_user(
        self,
        *,
        target_username: str,
        include_owned: bool,
        include_forked: bool,
        include_profile_readme: bool,
        fork_sources_for_forks: bool,
        follow_fork_owners: bool,
    ) -> dict[str, object]:
        service = ForkDiscoveryService(
            self.config,
            self.logger,
            self.storage,
            github=self.github,
            sanitize_error_payload_fn=self._sanitize_error_payload,
            telemetry=self.telemetry,
        )
        return service.fork_repositories_for_user(
            target_username=target_username,
            include_owned=include_owned,
            include_forked=include_forked,
            include_profile_readme=include_profile_readme,
            fork_sources_for_forks=fork_sources_for_forks,
            follow_fork_owners=follow_fork_owners,
        )

    def process_follow_queue(self, run_id: int, trace_id: str, max_jobs: int | None = None) -> int:
        followed = 0
        processed_in_invocation: set[str] = set()
        with self.telemetry.span(
            "follow_queue.process",
            build_telemetry_attributes(
                capability="follow",
                run_id=run_id,
                trace_id=trace_id,
                max_jobs=max_jobs or 0,
            ),
        ):
            while True:
                remaining_budget = None if max_jobs is None else max(max_jobs - followed, 0)
                if remaining_budget == 0:
                    break

                jobs = self.storage.fetch_follow_jobs(
                    run_id,
                    statuses=("pending", "failed"),
                    limit=remaining_budget if remaining_budget is not None else 100,
                )
                if not jobs:
                    break

                iteration_progress = False

                for job in jobs:
                    username = str(job["github_login"])
                    if username in processed_in_invocation:
                        continue
                    iteration_progress = True
                    processed_in_invocation.add(username)

                    if self.storage.is_followed(username):
                        self.storage.upsert_follow_job(run_id, username, "done")
                        continue

                    if int(job["attempts"]) >= self.config.follow_job_max_attempts:
                        self.storage.upsert_follow_job(run_id, username, "dead_letter", str(job["last_error"] or "retry_budget_exhausted"))
                        self.storage.add_security_event(
                            "follow_job_dead_lettered",
                            json.dumps({"username": username, "attempts": int(job["attempts"]), "max_attempts": self.config.follow_job_max_attempts}),
                            run_id=run_id,
                        )
                        self.logger.warning(
                            f"follow_job_dead_lettered username={username}",
                            extra={"event": "follow_job_dead_lettered", "run_id": run_id, "trace_id": trace_id, "username": username},
                        )
                        continue

                    decision = self.policy_engine.evaluate_follow(username=username, has_consent=True)
                    if not decision.allowed:
                        self.storage.upsert_follow_job(run_id, username, "dead_letter", decision.reason)
                        self.storage.add_security_event(
                            "follow_blocked_by_policy",
                            json.dumps({"username": username, "reason": decision.reason}),
                            run_id=run_id,
                        )
                        self.logger.warning(
                            f"follow_blocked_by_policy username={username} reason={decision.reason}",
                            extra={"event": "follow_blocked_by_policy", "run_id": run_id, "trace_id": trace_id, "username": username},
                        )
                        continue

                    if self.config.dry_run:
                        self.storage.add_follow_action(run_id, username, True, 200, "dry_run", self._pop_discovery_context(run_id, username))
                        self.storage.upsert_follow_job(run_id, username, "done")
                        followed += 1
                        self.logger.info(
                            f"dry_run_follow username={username}",
                            extra={"event": "dry_run_follow", "run_id": run_id, "trace_id": trace_id, "username": username},
                        )
                        continue

                    with self.telemetry.span(
                        "follow_queue.follow_user",
                        build_telemetry_attributes(
                            capability="follow",
                            run_id=run_id,
                            trace_id=trace_id,
                            job_id=username,
                            username=username,
                        ),
                    ):
                        ok, status_code, err = self.github.follow_user(username)
                    self.storage.add_follow_action(run_id, username, ok, status_code, err, self._pop_discovery_context(run_id, username))
                    if ok:
                        self.storage.mark_followed(username)
                        self.storage.upsert_follow_job(run_id, username, "done")
                        followed += 1
                        self.logger.info(
                            f"follow_success username={username}",
                            extra={"event": "follow_success", "run_id": run_id, "trace_id": trace_id, "username": username, "status_code": 204},
                        )
                    else:
                        diagnostic = (err or "")[:300]
                        if self._is_private_or_restricted_failure(diagnostic):
                            self.storage.upsert_follow_job(run_id, username, "dead_letter", err, increment_attempt=True)
                            self.storage.add_security_event(
                                "follow_job_private_or_restricted",
                                json.dumps({"username": username, "status_code": status_code}),
                                run_id=run_id,
                            )
                            self.logger.warning(
                                f"follow_job_private_or_restricted username={username}",
                                extra={
                                    "event": "follow_job_private_or_restricted",
                                    "run_id": run_id,
                                    "trace_id": trace_id,
                                    "username": username,
                                    "status_code": status_code,
                                },
                            )
                        else:
                            self.storage.upsert_follow_job(run_id, username, "failed", err, increment_attempt=True)
                            updated_job = self.storage.get_follow_job(run_id, username)
                            attempts = int(updated_job["attempts"]) if updated_job else 0
                            if attempts >= self.config.follow_job_max_attempts:
                                self.storage.upsert_follow_job(run_id, username, "dead_letter", err)
                                self.storage.add_security_event(
                                    "follow_job_dead_lettered",
                                    json.dumps({"username": username, "attempts": attempts, "max_attempts": self.config.follow_job_max_attempts}),
                                    run_id=run_id,
                                )
                                self.logger.warning(
                                    f"follow_job_dead_lettered username={username}",
                                    extra={"event": "follow_job_dead_lettered", "run_id": run_id, "trace_id": trace_id, "username": username},
                                )
                        self.logger.warning(
                            f"follow_failed username={username} status={status_code} reason={diagnostic}",
                            extra={
                                "event": "follow_failed",
                                "run_id": run_id,
                                "trace_id": trace_id,
                                "username": username,
                                "status_code": status_code,
                                "reason": diagnostic,
                            },
                        )
                    time.sleep(self._delay_between_follows + random.uniform(0, 0.5))

                self.storage.commit()

                if not iteration_progress:
                    break

        return followed

    def _get_setting_int(self, key: str, default: int = 0) -> int:
        value = self.storage.get_setting(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def _historically_followed_successfully(self, username: str) -> bool:
        return self.storage.has_successful_follow_action(username)

    def _record_expand_cursor(self, seed_index: int, seed_login: str, phase: str, page: int) -> None:
        self.storage.set_setting(self.EXPAND_CURSOR_INDEX_KEY, str(seed_index))
        self.storage.set_setting(self.EXPAND_CURSOR_LOGIN_KEY, seed_login)
        self.storage.set_setting(self.EXPAND_CURSOR_PHASE_KEY, phase)
        self.storage.set_setting(self.EXPAND_CURSOR_PAGE_KEY, str(page))

    def _push_discovery_context(self, run_id: int, username: str, context: dict[str, object] | None = None) -> None:
        if context is None:
            return
        per_run = self._candidate_context_by_run.setdefault(run_id, {})
        per_run[username] = context

    def _pop_discovery_context(self, run_id: int, username: str) -> dict[str, object] | None:
        per_run = self._candidate_context_by_run.get(run_id, {})
        ctx = per_run.pop(username, None)
        if not per_run and run_id in self._candidate_context_by_run:
            self._candidate_context_by_run.pop(run_id, None)
        return ctx

    def _extract_status_code(self, exc: RequestException) -> int | None:
        match = re.search(r"status=(\d{3})", str(exc))
        if not match:
            return None
        return int(match.group(1))

    def _record_expand_error(self, status_code: int | None) -> bool:
        if status_code is None:
            return False
        self._expand_error_status_window.append(status_code)
        counts = {"429": 0, "5xx": 0}
        for value in self._expand_error_status_window:
            if value == 429:
                counts["429"] += 1
            if 500 <= value <= 599:
                counts["5xx"] += 1
        for error_kind, count in counts.items():
            if count >= self.config.expand_http_error_threshold:
                self._expand_breaker_open = True
                return True
        return False

    def _fetch_expand_page(
        self,
        *,
        run_id: int,
        trace_id: str,
        seed_login: str,
        seed_index: int,
        phase: str,
        page: int,
    ) -> list[dict]:
        if self.config.max_api_calls_per_run is not None and self._expand_api_calls >= self.config.max_api_calls_per_run:
            self.logger.info(
                "expand_budget_reached",
                extra={
                    "event": "expand_budget_reached",
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "limit_type": "max_api_calls_per_run",
                    "current_value": self._expand_api_calls,
                },
            )
            return []
        self._expand_api_calls += 1
        try:
            if phase == "followers":
                return self.github.fetch_user_followers(seed_login, page=page, per_page=self.config.per_page)
            return self.github.fetch_user_following(seed_login, page=page, per_page=self.config.per_page)
        except RequestException as exc:
            status_code = self._extract_status_code(exc)
            if self._record_expand_error(status_code):
                details = {
                    "seed_login": seed_login,
                    "seed_index": seed_index,
                    "phase": phase,
                    "page": page,
                    "status_code": status_code,
                    "window": self.config.expand_http_error_window,
                    "threshold": self.config.expand_http_error_threshold,
                }
                self.storage.add_security_event("expand_circuit_breaker_open", json.dumps(details), run_id=run_id)
                self.logger.warning(
                    "expand_circuit_breaker_open",
                    extra={
                        "event": "expand_circuit_breaker_open",
                        "run_id": run_id,
                        "trace_id": trace_id,
                        "seed_login": seed_login,
                        "seed_index": seed_index,
                        "phase": phase,
                        "page": page,
                        "status_code": status_code,
                        "window": self.config.expand_http_error_window,
                        "threshold": self.config.expand_http_error_threshold,
                    },
                )
            raise

    def _enqueue_discovered_candidate(
        self,
        run_id: int,
        trace_id: str,
        username: str,
        discovery_context: dict[str, object] | None = None,
    ) -> bool:
        normalized_username = str(username or "").strip().lstrip("@")
        if not normalized_username:
            return False

        if normalized_username.lower() == self.config.github_user.lower():
            self.logger.info(
                "expand_candidate_skipped",
                extra={
                    "event": "expand_candidate_skipped",
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "username": normalized_username,
                    "reason": "self",
                },
            )
            return False

        self.storage.upsert_follower_seen(normalized_username)

        if self.storage.is_followed(normalized_username):
            self.logger.info(
                "expand_candidate_skipped",
                extra={
                    "event": "expand_candidate_skipped",
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "username": normalized_username,
                    "reason": "already_followed",
                },
            )
            return False

        if self.config.discovery_mode == "expand" and self._historically_followed_successfully(normalized_username):
            self.logger.info(
                "expand_candidate_skipped",
                extra={
                    "event": "expand_candidate_skipped",
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "username": normalized_username,
                    "reason": "already_followed_historically",
                },
            )
            return False

        existing_job = self.storage.get_follow_job(run_id, normalized_username)
        existing_job_status = ""
        if existing_job:
            try:
                existing_job_status = str(existing_job["status"] or "")
            except (KeyError, TypeError):
                existing_job_status = ""
        if existing_job_status in {"pending", "done"}:
            self.logger.info(
                "expand_candidate_skipped",
                extra={
                    "event": "expand_candidate_skipped",
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "username": normalized_username,
                    "reason": "already_queued",
                },
            )
            return False

        self.storage.upsert_follow_job(run_id, normalized_username, "pending")
        self._push_discovery_context(run_id, normalized_username, discovery_context)
        return True

    def _fetch_all_following_seeds(self, run_id: int, trace_id: str) -> list[str]:
        page = 1
        seeds: list[str] = []
        while True:
            if self.config.max_api_calls_per_run is not None and self._expand_api_calls >= self.config.max_api_calls_per_run:
                self.logger.info(
                    "expand_budget_reached",
                    extra={
                        "event": "expand_budget_reached",
                        "run_id": run_id,
                        "trace_id": trace_id,
                        "limit_type": "max_api_calls_per_run",
                        "current_value": self._expand_api_calls,
                    },
                )
                break
            self._expand_api_calls += 1
            try:
                following = self.github.fetch_my_following(page=page, per_page=self.config.per_page)
            except RequestException as exc:
                status_code = self._extract_status_code(exc)
                if self._record_expand_error(status_code):
                    details = {
                        "seed_login": None,
                        "seed_index": -1,
                        "phase": "seed_collection",
                        "page": page,
                        "status_code": status_code,
                        "window": self.config.expand_http_error_window,
                        "threshold": self.config.expand_http_error_threshold,
                    }
                    self.storage.add_security_event("expand_circuit_breaker_open", json.dumps(details), run_id=run_id)
                    self.logger.warning(
                        "expand_circuit_breaker_open",
                        extra={
                            "event": "expand_circuit_breaker_open",
                            "run_id": run_id,
                            "trace_id": trace_id,
                            "phase": "seed_collection",
                            "page": page,
                            "status_code": status_code,
                            "window": self.config.expand_http_error_window,
                            "threshold": self.config.expand_http_error_threshold,
                        },
                    )
                break
            if not following:
                break
            for entry in following:
                login = str(entry.get("login") or "").strip().lstrip("@")
                if login:
                    seeds.append(login)
            page += 1
        return seeds

    def _discover_candidates_from_expand_seed(
        self,
        run_id: int,
        trace_id: str,
        seed_index: int,
        seed_login: str,
        max_candidates_remaining: int | None = None,
    ) -> int:
        discovered = 0
        phase = self.storage.get_setting(self.EXPAND_CURSOR_PHASE_KEY) or "followers"
        if phase not in {"followers", "following"}:
            phase = "followers"
        page = self._get_setting_int(self.EXPAND_CURSOR_PAGE_KEY, default=1)
        if page < 1:
            self.logger.warning(
                "expand_cursor_recovered",
                extra={"event": "expand_cursor_recovered", "run_id": run_id, "trace_id": trace_id, "seed_login": seed_login, "phase": phase, "page": page},
            )
            page = 1

        while True:
            if self._expand_breaker_open:
                return discovered
            if max_candidates_remaining is not None and discovered >= max_candidates_remaining:
                self.logger.info(
                    "expand_budget_reached",
                    extra={
                        "event": "expand_budget_reached",
                        "run_id": run_id,
                        "trace_id": trace_id,
                        "limit_type": "max_candidates_per_run",
                        "current_value": discovered,
                    },
                )
                return discovered
            self._record_expand_cursor(seed_index, seed_login, phase, page)
            try:
                entries = self._fetch_expand_page(
                    run_id=run_id,
                    trace_id=trace_id,
                    seed_login=seed_login,
                    seed_index=seed_index,
                    phase=phase,
                    page=page,
                )
            except RequestException:
                return discovered

            if not entries:
                if phase == "followers":
                    phase = "following"
                    page = 1
                    continue
                break

            for entry in entries:
                if max_candidates_remaining is not None and discovered >= max_candidates_remaining:
                    self.logger.info(
                        "expand_budget_reached",
                        extra={
                            "event": "expand_budget_reached",
                            "run_id": run_id,
                            "trace_id": trace_id,
                            "limit_type": "max_candidates_per_run",
                            "current_value": discovered,
                        },
                    )
                    return discovered
                context = {
                    "seed_login": seed_login,
                    "seed_index": seed_index,
                    "phase": phase,
                    "page": page,
                    "discovery_mode": "expand",
                }
                if self._enqueue_discovered_candidate(
                    run_id=run_id,
                    trace_id=trace_id,
                    username=str(entry.get("login") or ""),
                    discovery_context=context,
                ):
                    discovered += 1
            page += 1

        self._record_expand_cursor(seed_index, seed_login, "followers", 1)
        return discovered

    def _discover_candidates_followers(self, run_id: int, trace_id: str) -> int:
        fetched = 0
        page = 1
        while True:
            with self.telemetry.span(
                "followers.fetch_page",
                build_telemetry_attributes(
                    capability="run",
                    run_id=run_id,
                    trace_id=trace_id,
                    page=page,
                ),
            ):
                followers = self.github.fetch_followers(page=page, per_page=self.config.per_page)
            if not followers:
                break

            for entry in followers:
                username = str(entry.get("login") or "")
                if username.strip():
                    fetched += 1
                context = {"discovery_mode": "followers", "page": page}
                if self._enqueue_discovered_candidate(run_id=run_id, trace_id=trace_id, username=username, discovery_context=context):
                    continue
            self.storage.commit()
            page += 1
        return fetched

    def _discover_candidates(self, run_id: int, trace_id: str) -> int:
        self._expand_api_calls = 0
        self._expand_error_status_window.clear()
        self._expand_breaker_open = False

        if self.config.discovery_mode != "expand":
            return self._discover_candidates_followers(run_id=run_id, trace_id=trace_id)

        seeds = self._fetch_all_following_seeds(run_id=run_id, trace_id=trace_id)
        if not seeds:
            return 0

        start_index = self._get_setting_int(self.EXPAND_CURSOR_INDEX_KEY, default=0)
        if start_index < 0 or start_index >= len(seeds):
            self.logger.warning(
                "expand_cursor_recovered",
                extra={"event": "expand_cursor_recovered", "run_id": run_id, "trace_id": trace_id, "seed_index": start_index},
            )
            start_index = 0

        max_seed_iterations = len(seeds)
        if self.config.max_expand_seeds_per_run is not None:
            max_seed_iterations = min(max_seed_iterations, self.config.max_expand_seeds_per_run)

        total_discovered = 0
        for offset in range(max_seed_iterations):
            if self._expand_breaker_open:
                break
            remaining_candidates = None
            if self.config.max_candidates_per_run is not None:
                remaining_candidates = max(self.config.max_candidates_per_run - total_discovered, 0)
                if remaining_candidates == 0:
                    self.logger.info(
                        "expand_budget_reached",
                        extra={
                            "event": "expand_budget_reached",
                            "run_id": run_id,
                            "trace_id": trace_id,
                            "limit_type": "max_candidates_per_run",
                            "current_value": total_discovered,
                        },
                    )
                    break
            seed_index = (start_index + offset) % len(seeds)
            seed_login = seeds[seed_index]
            self.logger.info(
                "expand_seed_started",
                extra={
                    "event": "expand_seed_started",
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "seed_index": seed_index,
                    "seed_login": seed_login,
                },
            )
            discovered = self._discover_candidates_from_expand_seed(
                run_id=run_id,
                trace_id=trace_id,
                seed_index=seed_index,
                seed_login=seed_login,
                max_candidates_remaining=remaining_candidates,
            )
            total_discovered += discovered
            self.storage.set_setting(self.EXPAND_CURSOR_INDEX_KEY, str((seed_index + 1) % len(seeds)))
            self.storage.commit()
            self.logger.info(
                "expand_seed_completed",
                extra={
                    "event": "expand_seed_completed",
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "seed_index": seed_index,
                    "seed_login": seed_login,
                    "discovered": discovered,
                },
            )
            if self.config.max_candidates_per_run is not None and total_discovered >= self.config.max_candidates_per_run:
                self.logger.info(
                    "expand_budget_reached",
                    extra={
                        "event": "expand_budget_reached",
                        "run_id": run_id,
                        "trace_id": trace_id,
                        "limit_type": "max_candidates_per_run",
                        "current_value": total_discovered,
                    },
                )
                break

        if self.config.max_expand_seeds_per_run is not None and max_seed_iterations == self.config.max_expand_seeds_per_run:
            self.logger.info(
                "expand_budget_reached",
                extra={
                    "event": "expand_budget_reached",
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "limit_type": "max_expand_seeds_per_run",
                    "current_value": max_seed_iterations,
                },
            )

        if self._expand_breaker_open and self.config.expand_fallback_to_followers:
            self.logger.info("expand_fallback_to_followers", extra={"event": "expand_fallback_to_followers", "run_id": run_id, "trace_id": trace_id})
            total_discovered += self._discover_candidates_followers(run_id=run_id, trace_id=trace_id)

        return total_discovered

    def run(self) -> dict[str, int | bool | str]:
        trace_id = f"trace-{uuid4()}"
        run_id = self.storage.begin_run(trace_id=trace_id)
        imported = self.migrate_legacy_files(run_id=run_id, trace_id=trace_id)
        fetched = 0
        followed = 0
        error_message = None

        try:
            with self.telemetry.span(
                "bot.run",
                build_telemetry_attributes(capability="run", run_id=run_id, trace_id=trace_id),
            ):
                remaining, reset_at = self.github.check_rate_limit()
                self.storage.add_rate_limit_snapshot(run_id, remaining, reset_at)
                if remaining is not None and remaining < self._rate_limit_threshold:
                    self.logger.warning(
                        f"low_rate_limit remaining={remaining}",
                        extra={"event": "low_rate_limit", "run_id": run_id, "trace_id": trace_id},
                    )

                fetched = self._discover_candidates(run_id=run_id, trace_id=trace_id)

                followed = self.process_follow_queue(
                    run_id=run_id,
                    trace_id=trace_id,
                    max_jobs=self.config.max_follows_per_run,
                )

                if self.config.max_follows_per_run and followed >= self.config.max_follows_per_run:
                    self.logger.info(
                        "max_follows_per_run_reached",
                        extra={"event": "max_follows_reached", "run_id": run_id, "trace_id": trace_id},
                    )


        except Exception as exc:
            error_message = str(exc)
            self.storage.add_security_event("run_failed", error_message, run_id=run_id)
            self.logger.exception("run_failed", extra={"event": "run_failed", "run_id": run_id, "trace_id": trace_id})
        finally:
            self.storage.commit()
            self.storage.finish_run(run_id, fetched, followed, error_message)
            self.telemetry.shutdown()

        result = {
            "run_id": run_id,
            "followers_fetched": fetched,
            "followers_followed": followed,
            "dry_run": self.config.dry_run,
            "legacy_imported": imported,
            "trace_id": trace_id,
        }
        if error_message:
            raise RuntimeError(error_message)
        return result
