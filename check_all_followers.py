"""Operational report utility for GitHub follower bot v2."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4

from bot import BotConfig, BotStorage, GitHubClient, JsonFormatter, SecretRedactionFilter, ensure_parent_dir


LOG_DIR = Path("runtime") / "logs"
CHECK_LOG_FILE = str(LOG_DIR / f"check-all-followers-{datetime.now().strftime('%Y-%m-%d')}.log")

logger = logging.getLogger("check_all_followers")
logger.setLevel(logging.INFO)


def main() -> int:
    config = BotConfig.from_env()
    run_id = f"report-{uuid4()}"
    trace_id = f"trace-{uuid4()}"

    if not logger.handlers:
        redaction = SecretRedactionFilter([config.github_token])
        ensure_parent_dir(CHECK_LOG_FILE)
        file_handler = RotatingFileHandler(
            CHECK_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=2
        )
        file_handler.setFormatter(JsonFormatter())
        file_handler.addFilter(redaction)
        logger.addHandler(file_handler)

    storage = BotStorage(config.db_path)
    github = GitHubClient(config.github_user, config.github_token, logger)

    stats = storage.get_stats()
    remaining, reset_at = github.check_rate_limit()

    report = {
        "run_id": run_id,
        "trace_id": trace_id,
        "followers_total_seen": stats["followers_total"],
        "followers_followed": stats["followers_followed"],
        "followers_pending": max(stats["followers_total"] - stats["followers_followed"], 0),
        "api_remaining": remaining,
        "api_reset_at": reset_at,
        "runs_total": stats["runs_total"],
        "last_run": storage.get_last_run(),
        "dry_run_mode": config.dry_run,
        "max_follows_per_run": config.max_follows_per_run,
        "auth_mode": config.auth_mode,
    }

    logger.info("operational_report", extra={"event": "operational_report", "run_id": run_id, "trace_id": trace_id})
    print(json.dumps(report, indent=2))
    return 0


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
