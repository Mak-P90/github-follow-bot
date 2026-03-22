from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable

from core.application.telemetry_attrs import build_telemetry_attributes


@contextmanager
def _null_span():
    yield None


class ForkDiscoveryService:
    def __init__(
        self,
        config: Any,
        logger: Any,
        storage: Any,
        *,
        github: Any,
        sanitize_error_payload_fn: Callable[[Any, list[str] | None], str],
        telemetry: Any | None = None,
    ) -> None:
        self.config = config
        self.logger = logger
        self.storage = storage
        self.github = github
        self._sanitize_error_payload = sanitize_error_payload_fn
        self.telemetry = telemetry

    def _span(self, name: str, attributes: dict[str, Any]):
        span = getattr(self.telemetry, "span", None)
        if callable(span):
            return span(name, attributes)
        return _null_span()

    def _repo_is_profile_readme(self, repo: dict, username: str) -> bool:
        owner = str((repo.get("owner") or {}).get("login") or "")
        name = str(repo.get("name") or "")
        return owner.lower() == username.lower() and name.lower() == username.lower()

    def _resolve_repository_root(self, repo: dict) -> tuple[str, list[str]]:
        chain: list[str] = []
        cursor = repo
        while isinstance(cursor, dict):
            current_full_name = str(cursor.get("full_name") or "").strip()
            if not current_full_name:
                break
            chain.append(current_full_name)
            source = cursor.get("source")
            parent = cursor.get("parent")
            next_ref = source or parent
            if not isinstance(next_ref, dict):
                break
            next_full_name = str(next_ref.get("full_name") or "").strip()
            if not next_full_name or next_full_name == current_full_name:
                break
            loaded = self.github.get_repository(next_full_name)
            if loaded is None:
                break
            cursor = loaded
        return chain[-1] if chain else str(repo.get("full_name") or ""), chain

    def fork_repositories_for_user(
        self,
        *,
        target_username: str,
        include_owned: bool,
        include_forked: bool,
        include_profile_readme: bool,
        fork_sources_for_forks: bool,
        follow_fork_owners: bool,
        run_id: int | None = None,
        trace_id: str | None = None,
    ) -> dict[str, object]:
        page = 1
        scanned = 0
        queued = 0
        forked = 0
        failed = 0
        skipped = 0
        followed_owners = 0
        seen_follow_users: set[str] = set()
        with self._span(
            "fork_repos.run",
            build_telemetry_attributes(
                capability="fork-repos",
                run_id=run_id,
                trace_id=trace_id,
                target_username=target_username,
                include_owned=include_owned,
                include_forked=include_forked,
            ),
        ):
            while True:
                repos = self.github.fetch_user_repositories(target_username, page=page, per_page=self.config.per_page)
                if not repos:
                    break
                for repo in repos:
                    if self.config.max_forks_per_run is not None and queued >= self.config.max_forks_per_run:
                        self.logger.info(
                            "fork_repos_budget_reached",
                            extra={
                                "event": "fork_repos_budget_reached",
                                "target_username": target_username,
                                "max_forks_per_run": self.config.max_forks_per_run,
                                "queued": queued,
                            },
                        )
                        return {
                            "target_username": target_username,
                            "scanned": scanned,
                            "queued": queued,
                            "forked": forked,
                            "failed": failed,
                            "skipped": skipped,
                            "followed_owners": followed_owners,
                            "max_forks_per_run": self.config.max_forks_per_run,
                        }
                    scanned += 1
                    owner_login = str((repo.get("owner") or {}).get("login") or "")
                    full_name = str(repo.get("full_name") or "")
                    is_fork = bool(repo.get("fork"))
                    is_profile_readme = self._repo_is_profile_readme(repo, target_username)

                    if is_profile_readme and not include_profile_readme:
                        skipped += 1
                        continue

                    should_include = False
                    if include_owned and owner_login.lower() == target_username.lower() and not is_fork:
                        should_include = True
                    if include_forked and is_fork:
                        should_include = True
                    if not should_include:
                        skipped += 1
                        continue

                    target_full_name = full_name
                    source_root_full_name = None
                    chain: list[str] = [full_name]
                    status_code: int | None = None
                    err: str | None = None
                    ok = False

                    try:
                        if is_fork and fork_sources_for_forks:
                            source_root_full_name, chain = self._resolve_repository_root(repo)
                            if source_root_full_name:
                                target_full_name = source_root_full_name

                        queued += 1
                        ok, status_code, err = self.github.fork_repository(target_full_name)
                        if ok:
                            forked += 1
                        else:
                            failed += 1
                    except Exception as exc:
                        failed += 1
                        err = self._sanitize_error_payload(exc, [self.config.github_token])
                        status_code = None
                        self.logger.warning(
                            "fork_repository_failed_exception",
                            extra={
                                "event": "fork_repository_failed_exception",
                                "target_username": target_username,
                                "repository": full_name,
                                "fork_target": target_full_name,
                                "reason": err,
                            },
                        )

                    self.storage.upsert_repository_catalog_entry(
                        full_name=full_name,
                        owner_login=owner_login,
                        repo_name=str(repo.get("name") or ""),
                        is_fork=is_fork,
                        parent_full_name=str((repo.get("parent") or {}).get("full_name") or "") or None,
                        source_root_full_name=source_root_full_name,
                        repo_updated_at=str(repo.get("updated_at") or "") or None,
                        stargazers_count=repo.get("stargazers_count"),
                        forks_count=repo.get("forks_count"),
                        watchers_count=repo.get("watchers_count"),
                        open_issues_count=repo.get("open_issues_count"),
                        language=str(repo.get("language") or "") or None,
                        default_branch=str(repo.get("default_branch") or "") or None,
                        archived=bool(repo.get("archived")) if repo.get("archived") is not None else None,
                        disabled=bool(repo.get("disabled")) if repo.get("disabled") is not None else None,
                        pushed_at=str(repo.get("pushed_at") or "") or None,
                        last_forked_at=datetime.now(timezone.utc).isoformat(),
                        last_fork_status="success" if ok else (f"http_{status_code}" if status_code is not None else "exception"),
                        last_fork_error=err,
                    )

                    if follow_fork_owners:
                        owners = {str(target_full_name).split("/", 1)[0]}
                        for item in chain:
                            owners.add(str(item).split("/", 1)[0])
                        for owner in owners:
                            owner_normalized = owner.strip().lstrip("@")
                            if not owner_normalized or owner_normalized.lower() == self.config.github_user.lower():
                                continue
                            if owner_normalized.lower() in seen_follow_users:
                                continue
                            seen_follow_users.add(owner_normalized.lower())
                            try:
                                followed_ok, _status, _reason = self.github.follow_user(owner_normalized)
                                if followed_ok:
                                    followed_owners += 1
                            except Exception as exc:
                                self.logger.warning(
                                    "fork_repos_follow_owner_failed",
                                    extra={
                                        "event": "fork_repos_follow_owner_failed",
                                        "target_username": target_username,
                                        "repository": full_name,
                                        "owner": owner_normalized,
                                        "reason": self._sanitize_error_payload(exc, [self.config.github_token]),
                                    },
                                )

                self.storage.commit()
                page += 1

        return {
            "target_username": target_username,
            "scanned": scanned,
            "queued": queued,
            "forked": forked,
            "failed": failed,
            "skipped": skipped,
            "followed_owners": followed_owners,
            "max_forks_per_run": self.config.max_forks_per_run,
        }
