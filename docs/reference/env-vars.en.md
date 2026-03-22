# Environment Variables Reference

> Status: ✅ Completed in British English.

## Core runtime

- `GITHUB_USER`: GitHub account used by the bot.
- `BOT_DB_PATH`: SQLite path for operational persistence.
- `BOT_DRY_RUN`: if `true`, validates flow without real follow actions.
- `BOT_MAX_FOLLOWS_PER_RUN`: operational budget for follows per run.

## Authentication

- `BOT_AUTH_MODE`: `pat`, `github_app_installation_token`, or `github_app`.
- `PERSONAL_GITHUB_TOKEN`: required in `pat` mode.
- `GITHUB_APP_INSTALLATION_TOKEN`: required in `github_app_installation_token` mode.
- `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID`: required in `github_app` mode.
- Exactly one GitHub App key source:
    - `GITHUB_APP_PRIVATE_KEY`
    - `GITHUB_APP_PRIVATE_KEY_FILE`
    - `GITHUB_APP_PRIVATE_KEY_COMMAND`
- `BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS`: timeout for key command execution.
- `BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS`: preventive token-refresh skew.

## Discovery and resilience

- `BOT_DISCOVERY_MODE`: `followers` (default) or `expand`.
- `BOT_MAX_CANDIDATES_PER_RUN`: caps discovered candidates per run.
- `BOT_MAX_API_CALLS_PER_RUN`: caps API requests per run.
- `BOT_MAX_EXPAND_SEEDS_PER_RUN`: caps seed accounts in `expand` mode.
- `BOT_EXPAND_HTTP_ERROR_WINDOW`: sliding error window for `expand` circuit breaker.
- `BOT_EXPAND_HTTP_ERROR_THRESHOLD`: error threshold to open breaker.
- `BOT_EXPAND_FALLBACK_TO_FOLLOWERS`: fallback to `followers` if breaker opens.
- `BOT_FOLLOW_JOB_MAX_ATTEMPTS`: max retry attempts before `dead_letter`.
- `BOT_VERIFY_FOLLOW_AFTER_PUT`: verifies follow state after write operations when enabled.
- `BOT_FOLLOW_VERIFY_MAX_RETRIES`: retry budget for post-follow verification checks.
- `BOT_FOLLOW_VERIFY_RETRY_DELAY_SECONDS`: delay between verification retries.

## Observability and release integrity

- `BOT_OTEL_ENABLED`, `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`
- `APP_ENV`
- `RELEASE_MANIFEST_SIGNING_KEY`
- `RELEASE_MANIFEST_REQUIRE_SIGNATURE`
- `RELEASE_MANIFEST_MAX_AGE_SECONDS`
- `BOT_COSIGN_ENABLED`, `COSIGN_KEY_REF`

## Migration and policy controls

- `BOT_POSTGRES_DSN`, `BOT_DUAL_WRITE_DRY_RUN`
- `BOT_CLEANUP_LEGACY_FILES`
- `BOT_POLICY_REQUIRE_CONSENT`, `BOT_POLICY_DENYLIST`, `BOT_POLICY_RETENTION_DAYS`
- `BOT_REQUIRE_GITHUB_APP_AUTH`: fail-closed control to forbid non-GitHub-App auth in hardened environments.

## Additional variables covered in runtime

- `BOT_DB_ENGINE` (default `sqlite`)
    - Controls persistence engine selection (`sqlite` / `postgres`) for runtime paths that support both backends.
- `BOT_QUEUE_BACKEND`
    - Selects distributed queue adapter mode used by queue backend status/verify/smoke commands.
- `BOT_RABBITMQ_AMQP_URL`
    - RabbitMQ broker URL used by RabbitMQ queue backend adapter.
- `BOT_RABBITMQ_QUEUE`
    - RabbitMQ primary queue name.
- `BOT_RABBITMQ_DLQ`
    - RabbitMQ dead-letter queue name.
- `BOT_MAX_FORKS_PER_RUN`
    - Operational cap for `fork-repos` bulk processing.
- `BOT_GUI_ENABLED`
    - Feature toggle for optional GUI runtime path.
- `BOT_GUI_HOST`
    - Bind host for GUI mode.
- `BOT_GUI_PORT`
    - Bind port for GUI mode.
- `BOT_GUI_LOCALE`
    - Locale for GUI i18n catalog selection.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
