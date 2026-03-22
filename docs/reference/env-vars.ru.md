# Справочник по переменным среды

Каноническая таблица переменных, обнаруженных во время выполнения (`bot.py`).

| Variable                                     | Requerida   | Aplica a                        | Default               | Ejemplo                 | Impacto/Notas                                                                                                                    |
| -------------------------------------------- | ----------- | ------------------------------- | --------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `GITHUB_USER`                                | Sí          | todos                           | -                     | `octocat`               | Usuario objetivo del bot.                                                                                                        |
| `BOT_AUTH_MODE`                              | No          | auth                            | inferido              | `github_app`            | Válidos: `pat`, `github_app_installation_token`, `github_app`.                                                                   |
| `PERSONAL_GITHUB_TOKEN`                      | Condicional | `pat`                           | -                     | `ghp_xxx`               | No exponer en logs/repositorio.                                                                                                  |
| `GITHUB_APP_INSTALLATION_TOKEN`              | Condicional | `github_app_installation_token` | -                     | `ghs_xxx`               | Token preemitido.                                                                                                                |
| `GITHUB_APP_ID`                              | Condicional | `github_app`                    | -                     | `12345`                 | Requerido en modo app runtime.                                                                                                   |
| `GITHUB_APP_INSTALLATION_ID`                 | Condicional | `github_app`                    | -                     | `67890`                 | Requerido en modo app runtime.                                                                                                   |
| `GITHUB_APP_PRIVATE_KEY`                     | Condicional | `github_app`                    | -                     | PEM inline              | Elegir solo una fuente de key.                                                                                                   |
| `GITHUB_APP_PRIVATE_KEY_FILE`                | Condicional | `github_app`                    | -                     | `/run/secrets/key.pem`  | Acepta lista `,` o `:`; usa primer archivo existente.                                                                            |
| `GITHUB_APP_PRIVATE_KEY_COMMAND`             | Condicional | `github_app`                    | -                     | `python -c ...`         | Ejecutado con argv y timeout.                                                                                                    |
| `BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS` | No          | `github_app` + command          | `10`                  | `10`                    | Debe ser >=1.                                                                                                                    |
| `BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS`  | No          | `github_app`                    | `60`                  | `60`                    | Debe ser >=0.                                                                                                                    |
| `BOT_VERIFY_FOLLOW_AFTER_PUT`                | No          | follow runtime                  | `true`                | `false`                 | Verifica `PUT /user/following/{login}` con `GET /user/following/{login}` para evitar falsos positivos.                           |
| `BOT_FOLLOW_VERIFY_MAX_RETRIES`              | No          | follow runtime                  | `2`                   | `3`                     | Reintentos de verificación post-follow. Debe ser >=1.                                                                            |
| `BOT_FOLLOW_VERIFY_RETRY_DELAY_SECONDS`      | No          | follow runtime                  | `1.0`                 | `0.5`                   | Espera entre probes de verificación. Debe ser >=0.                                                                               |
| `BOT_REQUIRE_GITHUB_APP_AUTH`                | No          | auth policy                     | `false`               | `true`                  | Fail-closed: bloquea modos no `github_app`.                                                                                      |
| `BOT_DB_PATH`                                | No          | runtime                         | `bot_state.db`        | `bot_state.db`          | Ruta de SQLite.                                                                                                                  |
| `BOT_DRY_RUN`                                | No          | runtime                         | `false`               | `true`                  | Recomendado en primer run.                                                                                                       |
| `BOT_MAX_FOLLOWS_PER_RUN`                    | No          | runtime                         | sin límite            | `50`                    | Debe ser >=1 si se define.                                                                                                       |
| `BOT_MAX_CANDIDATES_PER_RUN`                 | No          | expand runtime                  | sin límite            | `500`                   | Corta descubrimiento expand al alcanzar candidatos encolados por corrida. Debe ser >=1.                                          |
| `BOT_MAX_API_CALLS_PER_RUN`                  | No          | expand runtime                  | sin límite            | `200`                   | Presupuesto total de llamadas de discovery (`fetch_my_following`, `fetch_user_followers`, `fetch_user_following`). Debe ser >=1. |
| `BOT_MAX_EXPAND_SEEDS_PER_RUN`               | No          | expand runtime                  | sin límite            | `20`                    | Máximo de semillas procesadas por corrida en modo `expand`. Debe ser >=1.                                                        |
| `BOT_DISCOVERY_MODE`                         | No          | runtime                         | `followers`           | `expand`                | Válidos: `followers`, `expand`. `expand` usa seeds de `following` y cursor persistido en `settings`.                             |
| `BOT_EXPAND_HTTP_ERROR_WINDOW`               | No          | expand resilience               | `20`                  | `20`                    | Ventana deslizante de errores HTTP para circuit breaker de discovery. Debe ser >=1.                                              |
| `BOT_EXPAND_HTTP_ERROR_THRESHOLD`            | No          | expand resilience               | `5`                   | `3`                     | Umbral por tipo HTTP (429 y 5xx) para abrir breaker y degradar expand. Debe ser >=1.                                             |
| `BOT_EXPAND_FALLBACK_TO_FOLLOWERS`           | No          | expand resilience               | `false`               | `true`                  | Si el breaker abre, permite fallback a `followers` en la misma corrida.                                                          |
| `BOT_FOLLOW_JOB_MAX_ATTEMPTS`                | No          | queue                           | `3`                   | `3`                     | Debe ser >=1.                                                                                                                    |
| `BOT_CLEANUP_LEGACY_FILES`                   | No          | migración                       | `true`                | `true`                  | Archiva archivos TXT migrados a `*.migrated`.                                                                                    |
| `BOT_POLICY_REQUIRE_CONSENT`                 | No          | policy                          | `false`               | `true`                  | Bloquea follow sin consentimiento.                                                                                               |
| `BOT_POLICY_DENYLIST`                        | No          | policy                          | vacío                 | `user1,user2`           | Denylist por login.                                                                                                              |
| `BOT_POLICY_RETENTION_DAYS`                  | No          | policy                          | `365`                 | `90`                    | Ventana de retención declarada.                                                                                                  |
| `RELEASE_MANIFEST_SIGNING_KEY`               | No          | release integrity               | -                     | `change-me`             | Firma HMAC manifiesto.                                                                                                           |
| `RELEASE_MANIFEST_REQUIRE_SIGNATURE`         | No          | release integrity               | `false`               | `true`                  | Exige firma al verificar.                                                                                                        |
| `RELEASE_MANIFEST_MAX_AGE_SECONDS`           | No          | release integrity               | sin TTL               | `300`                   | Debe ser >=1 si se define.                                                                                                       |
| `BOT_OTEL_ENABLED`                           | No          | observabilidad                  | `false`               | `true`                  | Habilita tracing runtime.                                                                                                        |
| `OTEL_SERVICE_NAME`                          | No          | observabilidad                  | `github_follower_bot` | `github_follower_bot`   | Nombre de servicio OTel.                                                                                                         |
| `OTEL_EXPORTER_OTLP_ENDPOINT`                | No          | observabilidad                  | -                     | `http://localhost:4318` | Endpoint OTLP.                                                                                                                   |
| `APP_ENV`                                    | No          | observabilidad export           | `local`               | `prod`                  | Etiqueta de entorno en `export-otel-bootstrap`.                                                                                  |
| `BOT_COSIGN_ENABLED`                         | No          | zero-trust                      | `false`               | `true`                  | Señal de enforcement cosign.                                                                                                     |
| `COSIGN_KEY_REF`                             | No          | zero-trust                      | -                     | `cosign.pub`            | Referencia de llave cosign.                                                                                                      |
| `BOT_DUAL_WRITE_DRY_RUN`                     | No          | migración                       | `false`               | `true`                  | Señal de modo sombra dual-write.                                                                                                 |
| `BOT_POSTGRES_DSN`                           | No          | migración                       | -                     | `postgresql://...`      | Habilita reportes con contexto Postgres.                                                                                         |

## `BOT_DISCOVERY_MODE`

Определяет источник кандидатов на`python bot.py run`.

- `followers`(по умолчанию): выполнять подписку, используя своих прямых подписчиков.
- `expand`: активируйте обнаружение с помощью семян для своих подписчиков (`/users/{self.user}/following`) и проходит две подфазы по затравке (`followers`й`following`) с постоянным курсором`settings`.

### Операционные примечания`expand`

- Постоянный курсор:`expand_seed_index`, `expand_seed_login`, `expand_seed_phase`, `expand_seed_page`.
- Дедупликация: избегать`self`, пользователи уже подписались, а пользователи с успешными подписками зарегистрировались (`follow_actions.success=1`), чтобы избежать автоматического повтора.
- Выполнение: не изменяет работника или очередь; повторное использование`follow_jobs` + `process_follow_queue`.
- Ограничение: уважение`BOT_MAX_FOLLOWS_PER_RUN`.

## Дополнительные переменные, покрытые в runtime

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
