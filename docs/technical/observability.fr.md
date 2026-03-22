# Observabilité

**Statut de traduction :** ✅ Vue complétée en français.

**Statut de traduction :** ✅ Vue complétée en français.

## Principes

- Logs JSON structurés pour les flux principaux.
- Événements critiques avec champ `event`.
- Corrélation opérationnelle via `run_id` et `trace_id`.

## Artefacts utiles

- `export-otel-bootstrap`
- `export-otel-operations-profile`
- `export-audit`

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

