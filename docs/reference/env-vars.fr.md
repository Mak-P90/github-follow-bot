# Référence des variables d’environnement

**Statut de traduction :** ✅ Vue complétée en français.

## Variables de base

- `GITHUB_USER`
- `BOT_AUTH_MODE`
- `PERSONAL_GITHUB_TOKEN`
- `BOT_DRY_RUN`
- `BOT_DB_PATH`

## Authentifier l'application GitHub

- `GITHUB_APP_ID`
- `GITHUB_APP_INSTALLATION_ID`
- `GITHUB_APP_PRIVATE_KEY`
- `GITHUB_APP_PRIVATE_KEY_FILE`
- `GITHUB_APP_PRIVATE_KEY_COMMAND`
- `BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS`
- `BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS`
- `BOT_REQUIRE_GITHUB_APP_AUTH`

## Contrôles opérationnels

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

## Observabilité / sécurité

- `BOT_OTEL_ENABLED`
- `OTEL_SERVICE_NAME`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `APP_ENV`
- `BOT_COSIGN_ENABLED`
- `COSIGN_KEY_REF`
- `RELEASE_MANIFEST_SIGNING_KEY`
- `RELEASE_MANIFEST_REQUIRE_SIGNATURE`
- `RELEASE_MANIFEST_MAX_AGE_SECONDS`
- options de redaction/trace selon la configuration runtime.

## Persistance / migration

- `BOT_POSTGRES_DSN`
- `BOT_DUAL_WRITE_DRY_RUN`
- `BOT_CLEANUP_LEGACY_FILES`
- `GITHUB_APP_INSTALLATION_TOKEN`

> Référence normative : aligner ces variables avec `.env.example` et le comportement effectif de `bot.py`.

## Variables supplémentaires couvertes au runtime

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
