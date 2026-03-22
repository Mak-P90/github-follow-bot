# GUI operativa (NiceGUI)

La GUI es una superficie operativa **opcional** sobre el CLI.

## Activación segura

```bash
BOT_GUI_ENABLED=true BOT_GUI_HOST=127.0.0.1 BOT_GUI_PORT=8081 python bot.py gui
```

- Bind local por defecto: `127.0.0.1`.
- Si `nicegui` no está instalada, el comando falla de forma controlada con exit code `2`.

## Variables

- `BOT_GUI_ENABLED` (default: `false`)
- `BOT_GUI_HOST` (default: `127.0.0.1`)
- `BOT_GUI_PORT` (default: `8081`)
- `BOT_GUI_LOCALE` (default: `en`, fallback a `en`)

## Alcance MVP

- Dashboard
- Runs (start/resume/abort)
- Diagnostics (`doctor`)
- Queue/Metrics
- Exports (`export-audit`)

## Contrato de integración

La GUI delega al adapter `control_plane` y no ejecuta lógica de negocio ni llamadas directas a GitHub.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

