# Модель безопасности

## Аутентификация

Поддерживаемые режимы:

- ПАТ
- Премитированный токен установки
- Среда выполнения приложения GitHub

Ключевые правила:

- В режиме`github_app`: `GITHUB_APP_ID` + `GITHUB_APP_INSTALLATION_ID`+ ровно один источник ключа.
- `BOT_REQUIRE_GITHUB_APP_AUTH=true`принудительно закрытый режим среды выполнения приложения GitHub.

## Секреты

- Не вводите учетные данные жестко.
- Эксклюзивное использование переменных среды.
- Написание секретов в логировании.

## Освободите целостность

- Манифест артефакта с дайджестом.
- Проверка манифеста с дополнительной подписью и TTL.
- Профиль нулевого доверия/совместного подписания для усиления защиты.

## Прослеживаемость

- Критические события с`event`и корреляция по`run_id`.
- `trace_id`для перекрестной корреляции, когда это применимо.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

