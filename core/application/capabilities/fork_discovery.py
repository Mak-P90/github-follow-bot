from __future__ import annotations

from typing import Any
from uuid import uuid4


def handle_fork_repos_command(service: Any, target_username: str, *, owned: bool, forked: bool, include_profile_readme: bool, fork_source: bool, follow_fork_owners: bool) -> tuple[int, dict[str, Any]]:
    include_owned = bool(owned)
    include_forked = bool(forked)

    if not include_owned and not include_forked and not include_profile_readme:
        return 2, {
            "error": "no_filters_selected",
            "hint": "use --owned, --forked, --all and/or --profile-readme",
        }

    trace_id = f"trace-{uuid4()}"
    payload = service.fork_repositories_for_user(
        target_username=target_username,
        include_owned=include_owned,
        include_forked=include_forked,
        include_profile_readme=include_profile_readme,
        fork_sources_for_forks=fork_source,
        follow_fork_owners=follow_fork_owners,
        trace_id=trace_id,
    )
    payload["trace_id"] = trace_id
    return 0, payload
