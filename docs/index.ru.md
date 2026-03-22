# Документация GitHub Follower Bot

Операционная и техническая документация бота, публикуемая из `main` как единый живой поток (без версионирования по release/tag).

## Для кого эта документация?

- **Операторы**: установка, аутентификация, запуск и диагностика.
- **Поддерживающие разработчики**: архитектура, runtime, хранилище и безопасность.

## Быстрые пути

1. [Установка](getting-started/installation.ru.md)
2. [Аутентификация](getting-started/authentication.ru.md)
3. [Quickstart](getting-started/quickstart.ru.md)
4. [Руководство MkDocs + GitHub Pages](getting-started/mkdocs-github-pages.ru.md)
5. [Ежедневные операции](user-guide/daily-operations.ru.md)
6. [Операции GUI](user-guide/gui.ru.md)
7. [Устранение неполадок](user-guide/troubleshooting.ru.md)
8. [Техническая архитектура](technical/architecture.ru.md)
9. [Справочник CLI](reference/cli.ru.md)
10. [Справочник переменных окружения](reference/env-vars.ru.md)

## Политика документации

- Источник публикации: **`main`**.
- Без версионирования документации (`mike`, теги, release trees: нет).
- PR с существенными функциональными изменениями должен обновлять документацию в том же PR.

## Sync status (2026-03-22)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-22**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `python bot.py control-plane-status`
- `python bot.py scheduler -h`
- `python bot.py queue-backend-status`
- `python bot.py queue-backend-verify`
- `python bot.py queue-backend-smoke`
- `python bot.py otel-runtime-status`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
