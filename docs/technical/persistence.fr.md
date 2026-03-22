# Persistance

**Statut de traduction :** ✅ Vue complétée en français.

**Statut de traduction :** ✅ Vue complétée en français.

## Principes

- La persistance opérationnelle doit être transactionnelle.
- Éviter les mécanismes legacy type fichiers TXT comme base principale.
- Préserver l’auditabilité des runs et actions.

## Points clés

- Suivi des runs via `run_id`.
- File `follow_jobs` avec états (`pending`, `done`, `failed`, `dead_letter`).
- Exports de migration/cutover pour trajectoire PostgreSQL.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

