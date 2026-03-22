from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable


def handle_control_plane_status(storage: Any, config: Any) -> tuple[int, dict[str, Any]]:
    stats = storage.get_stats()
    followers_total = stats.get("followers_total", stats.get("followers", 0))
    followers_followed = stats.get("followers_followed", stats.get("followed", 0))
    runs_total = stats.get("runs_total", stats.get("runs", 0))
    security_events_total = stats.get("security_events_total", stats.get("actions", 0))

    payload = {
        "service": "github_follower_bot_control_plane",
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "db_engine": config.db_engine,
        "auth_mode": config.auth_mode,
        "commands": {
            "run": "available",
            "worker": "available",
            "resume": "available",
            "abort": "available",
            "scheduler": "available",
        },
        "stats": {
            "followers_total": followers_total,
            "followers_followed": followers_followed,
            "runs_total": runs_total,
            "security_events_total": security_events_total,
            # Backward-compatible aliases for existing dashboards/clients.
            "followers": followers_total,
            "followed": followers_followed,
            "runs": runs_total,
            "actions": security_events_total,
        },
    }
    return 0, payload


def _try_acquire_scheduler_lock(storage: Any, lock_key: str, lock_ttl_seconds: int) -> tuple[bool, int]:
    now_epoch = int(time.time())
    lock_until = now_epoch + lock_ttl_seconds
    acquired = storage.try_acquire_distributed_lock(lock_key=lock_key, lock_until_epoch=lock_until, now_epoch=now_epoch)
    return acquired, lock_until


def _release_scheduler_lock(storage: Any, lock_key: str, expected_lock_until: int) -> None:
    storage.release_distributed_lock(lock_key=lock_key, expected_lock_until_epoch=expected_lock_until)


def handle_scheduler_command(
    service: Any,
    run_executor: Callable[[Any], dict[str, Any]],
    *,
    interval_seconds: float,
    max_ticks: int,
    sleep_fn: Callable[[float], None] = time.sleep,
    storage: Any | None = None,
    lock_key: str = "default",
    lock_ttl_seconds: int = 300,
) -> tuple[int, dict[str, Any]]:
    if interval_seconds <= 0:
        return 2, {"error": "invalid_interval", "interval_seconds": interval_seconds}

    if max_ticks <= 0:
        return 2, {"error": "invalid_max_ticks", "max_ticks": max_ticks}

    if lock_ttl_seconds <= 0:
        return 2, {"error": "invalid_lock_ttl_seconds", "lock_ttl_seconds": lock_ttl_seconds}

    lock_acquired = True
    lock_until = 0
    if storage is not None:
        lock_acquired, lock_until = _try_acquire_scheduler_lock(storage, lock_key=lock_key, lock_ttl_seconds=lock_ttl_seconds)
        if not lock_acquired:
            return 2, {
                "status": "lock_not_acquired",
                "lock_key": lock_key,
                "lock_until_epoch": storage.get_setting(f"scheduler_lock:{lock_key}"),
            }

    ticks: list[dict[str, Any]] = []
    try:
        for tick in range(1, max_ticks + 1):
            started_at = datetime.now(timezone.utc).isoformat()
            try:
                result = run_executor(service)
                ticks.append({"tick": tick, "status": "ok", "started_at": started_at, "result": result})
            except Exception as exc:  # noqa: BLE001 - scheduler must capture failures and continue
                ticks.append({"tick": tick, "status": "error", "started_at": started_at, "error": str(exc)})

            if tick < max_ticks:
                sleep_fn(interval_seconds)
    finally:
        if storage is not None and lock_acquired:
            _release_scheduler_lock(storage, lock_key=lock_key, expected_lock_until=lock_until)

    errors = sum(1 for item in ticks if item["status"] == "error")
    return (0 if errors == 0 else 2), {
        "status": "completed_with_errors" if errors else "completed",
        "interval_seconds": interval_seconds,
        "max_ticks": max_ticks,
        "errors": errors,
        "lock_key": lock_key,
        "lock_ttl_seconds": lock_ttl_seconds,
        "ticks": ticks,
    }
