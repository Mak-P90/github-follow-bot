# Operational GUI (NiceGUI)

The GUI is an **optional** operational surface on top of the CLI.

## Safe activation

```bash
BOT_GUI_ENABLED=true BOT_GUI_HOST=127.0.0.1 BOT_GUI_PORT=8081 python bot.py gui
```

- Local bind by default: `127.0.0.1`.
- If `nicegui` is missing, the command fails cleanly with exit code `2`.

## Variables

- `BOT_GUI_ENABLED` (default: `false`)
- `BOT_GUI_HOST` (default: `127.0.0.1`)
- `BOT_GUI_PORT` (default: `8081`)
- `BOT_GUI_LOCALE` (default: `en`, fallback: `en`)

## MVP scope

- Dashboard
- Runs (start/resume/abort)
- Diagnostics (`doctor`)
- Queue/Metrics
- Exports (`export-audit`)

## Integration contract

The GUI delegates through the `control_plane` adapter and does not execute business logic or direct GitHub API calls.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

