# Аутентификация

Среда выполнения поддерживает три реальных режима (`BOT_AUTH_MODE`):

1.`pat` 2.`github_app_installation_token` 3.`github_app`

И`BOT_AUTH_MODE`не определено, время выполнения остается на уровне`pat`и **не** автоматически продвигает`GITHUB_APP_INSTALLATION_TOKEN`. Чтобы использовать установочный токен, вы должны явно объявить`BOT_AUTH_MODE=github_app_installation_token`.

## 1) ПАТ (простой)

Минимум переменных:

- `GITHUB_USER`
- `PERSONAL_GITHUB_TOKEN`

Рекомендация:

- наименьшие привилегии,
- не используйте повторно PAT с ненужными разрешениями.

Ответная реакция Nota Operativa:

- для`PUT /user/following/{username}`классический PAT должен включать`user:follow`; без этой области GitHub может ответить`404`даже если профиль существует.
- когда это произойдет`404`, бот теперь добавляет диагностику в`follow_failed.reason`(режим аутентификации, наблюдаемые области и аутентифицированный пользователь), чтобы отличать разрешения от реального отсутствия профиля.

## 2) Премиум токена установки

Минимум переменных:

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app_installation_token`
- `GITHUB_APP_INSTALLATION_TOKEN`

## 3) Среда выполнения приложения GitHub (`github_app`)

Минимум переменных:

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app`
- `GITHUB_APP_ID`
- `GITHUB_APP_INSTALLATION_ID`
- **ровно один** источник закрытого ключа:
    - `GITHUB_APP_PRIVATE_KEY`
    - `GITHUB_APP_PRIVATE_KEY_FILE`
    - `GITHUB_APP_PRIVATE_KEY_COMMAND`

Поддержка переменных:

- `BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS`
- `BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS`

## Неверные комбинации

- Несколько ключевых источников одновременно.
- `BOT_AUTH_MODE=github_app_installation_token`грех`GITHUB_APP_INSTALLATION_TOKEN`.
- `BOT_AUTH_MODE=github_app`грех`GITHUB_APP_ID`/`GITHUB_APP_INSTALLATION_ID`.
- `BOT_REQUIRE_GITHUB_APP_AUTH=true`с другим способом`github_app`.

## Пример безопасного запуска

```env
GITHUB_USER=your_user
BOT_AUTH_MODE=pat
PERSONAL_GITHUB_TOKEN=ghp_replace_me
BOT_DRY_RUN=true
```

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

