# GUI opérationnelle (NiceGUI)

La GUI est une surface opérationnelle **optionnelle** au-dessus du CLI.

## Activation sûre

```bash
BOT_GUI_ENABLED=true BOT_GUI_HOST=127.0.0.1 BOT_GUI_PORT=8081 python bot.py gui
```

- Liaison locale par défaut : `127.0.0.1`.
- Si `nicegui` n'est pas installée, la commande échoue proprement avec le code `2`.

## Variables

- `BOT_GUI_ENABLED` (par défaut : `false`)
- `BOT_GUI_HOST` (par défaut : `127.0.0.1`)
- `BOT_GUI_PORT` (par défaut : `8081`)
- `BOT_GUI_LOCALE` (par défaut : `en`, fallback : `en`)

## Portée MVP

- Dashboard
- Runs (start/resume/abort)
- Diagnostics (`doctor`)
- Queue/Metrics
- Exports (`export-audit`)

## Contrat d'intégration

La GUI délègue via l'adapter `control_plane` et n'exécute ni logique métier ni appels directs à l'API GitHub.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

