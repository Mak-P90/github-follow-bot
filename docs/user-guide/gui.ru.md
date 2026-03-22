# Операционный GUI (NiceGUI)

GUI — это **опциональный** операционный слой поверх CLI.

## Безопасный запуск

```bash
BOT_GUI_ENABLED=true BOT_GUI_HOST=127.0.0.1 BOT_GUI_PORT=8081 python bot.py gui
```

- Локальная привязка по умолчанию: `127.0.0.1`.
- Если `nicegui` не установлена, команда завершается контролируемо с кодом `2`.

## Переменные

- `BOT_GUI_ENABLED` (по умолчанию: `false`)
- `BOT_GUI_HOST` (по умолчанию: `127.0.0.1`)
- `BOT_GUI_PORT` (по умолчанию: `8081`)
- `BOT_GUI_LOCALE` (по умолчанию: `en`, fallback: `en`)

## MVP-объём

- Dashboard
- Runs (start/resume/abort)
- Diagnostics (`doctor`)
- Queue/Metrics
- Exports (`export-audit`)

## Интеграционный контракт

GUI делегирует действия через адаптер `control_plane` и не содержит бизнес-логики или прямых вызовов GitHub API.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

