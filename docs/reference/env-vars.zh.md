# 环境变量参考

## 核心变量

- `GITHUB_USER`
- `BOT_AUTH_MODE` (`pat` | `github_app_installation_token` | `github_app`)
- `PERSONAL_GITHUB_TOKEN`（PAT 模式）
- `GITHUB_APP_INSTALLATION_TOKEN`（installation token 模式）

## GitHub App 变量

- `GITHUB_APP_ID`
- `GITHUB_APP_INSTALLATION_ID`
- `GITHUB_APP_PRIVATE_KEY`
- `GITHUB_APP_PRIVATE_KEY_FILE`
- `GITHUB_APP_PRIVATE_KEY_COMMAND`
- `BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS`
- `BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS`
- `BOT_REQUIRE_GITHUB_APP_AUTH`

## 运行与安全变量

- `BOT_DRY_RUN`
- `BOT_MAX_FOLLOWS_PER_RUN`
- `BOT_MAX_API_CALLS_PER_RUN`
- `BOT_DISCOVERY_MODE`
- `BOT_MAX_CANDIDATES_PER_RUN`
- `BOT_MAX_EXPAND_SEEDS_PER_RUN`
- `BOT_EXPAND_HTTP_ERROR_THRESHOLD`
- `BOT_EXPAND_HTTP_ERROR_WINDOW`
- `BOT_EXPAND_FALLBACK_TO_FOLLOWERS`
- `BOT_FOLLOW_JOB_MAX_ATTEMPTS`
- `BOT_VERIFY_FOLLOW_AFTER_PUT`
- `BOT_FOLLOW_VERIFY_MAX_RETRIES`
- `BOT_FOLLOW_VERIFY_RETRY_DELAY_SECONDS`
- `BOT_POLICY_REQUIRE_CONSENT`
- `BOT_POLICY_DENYLIST`
- `BOT_POLICY_RETENTION_DAYS`

## 持久化与可观测性

- `BOT_DB_PATH`
- `BOT_POSTGRES_DSN`
- `BOT_DUAL_WRITE_DRY_RUN`
- `BOT_CLEANUP_LEGACY_FILES`
- `BOT_OTEL_ENABLED`
- `OTEL_SERVICE_NAME`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `APP_ENV`
- `RELEASE_MANIFEST_SIGNING_KEY`
- `RELEASE_MANIFEST_REQUIRE_SIGNATURE`
- `RELEASE_MANIFEST_MAX_AGE_SECONDS`
- `BOT_COSIGN_ENABLED`
- `COSIGN_KEY_REF`

## 规则

- 密钥来源（`inline/file/command`）必须且只能配置一个。
- 使用 `BOT_REQUIRE_GITHUB_APP_AUTH=true` 时，必须启用 `github_app` 模式。
- 建议在生产环境启用 `BOT_MAX_FOLLOWS_PER_RUN` 与队列重试预算。

## Runtime 额外覆盖变量

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
