# Troubleshooting

> Status: ✅ Completed in British English.

## 401 / authentication error

- Verify `BOT_AUTH_MODE`.
- Validate minimum variables for the selected mode.
- For `github_app`, confirm **one key source only**.
- Run `python bot.py doctor` and review `auth_mode`, `github_app_configured`.

## Rate limit

- Review `check_all_followers.py` and metrics.
- Reduce execution frequency.
- Apply `BOT_MAX_FOLLOWS_PER_RUN` for operational control.

## Incomplete configuration

Common errors:

- Missing `GITHUB_USER`.
- Missing token/credentials for active mode.
- `GITHUB_APP_PRIVATE_KEY_FILE` points to a non-existent path.

## Issues with GitHub App key

- `GITHUB_APP_PRIVATE_KEY_FILE`: check file existence/permissions.
- `GITHUB_APP_PRIVATE_KEY_COMMAND`: check non-empty output and timeout.
- Do not combine inline/file/command simultaneously.

## Dry run

If in doubt, use:

```env
BOT_DRY_RUN=true
```

This validates flow without real follow actions.

## Windows environment issues

- venv activation fails due to execution policy:
    - run PowerShell with a policy suitable for local scripts.
- Paths with spaces:
    - use quoted paths when required.

## Path/permission errors

- Unwritable DB: check directory/file permissions for `BOT_DB_PATH`.
- Secret mount unavailable: verify effective path in `doctor`.

## Logs and interpretation

- The bot emits structured JSON logs.
- Correlate using `run_id` and `trace_id`.
- Review security events when auth or queue failures occur.

## Expand circuit breaker (`expand_circuit_breaker_open`)

If repeated 429/5xx responses exceed threshold (`BOT_EXPAND_HTTP_ERROR_THRESHOLD`) within window (`BOT_EXPAND_HTTP_ERROR_WINDOW`):

- the bot aborts expand for the current run;
- records `security_event=expand_circuit_breaker_open`;
- emits a structured log with `seed_login`, `phase`, `page`, `status_code`;
- optionally falls back to `followers` if `BOT_EXPAND_FALLBACK_TO_FOLLOWERS=true`.

Operational steps:

1. Review `python bot.py export-audit --output artifacts/commands/audit.json` and filter `security_events`.
2. Adjust cadence/cron and budgets (`BOT_MAX_API_CALLS_PER_RUN`, `BOT_MAX_EXPAND_SEEDS_PER_RUN`).
3. Confirm whether temporary fallback to followers is appropriate.

## Inconsistent expand cursor

If `expand_seed_index` is out of range or `expand_seed_page` is invalid (zero/negative/non-numeric), runtime redirects to a safe state (index 0 / page 1) and continues without a fatal exception.

The `follow_jobs` queue keeps uniqueness by (`run_id`, `github_login`), preventing duplicates in a single run even with a corrupted cursor.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

