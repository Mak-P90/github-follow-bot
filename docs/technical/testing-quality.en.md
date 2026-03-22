# Testing and Quality

> Status: ✅ Completed in British English.

## Recommended minimum validation

```bash
python -m py_compile bot.py check_all_followers.py
pytest -q
python bot.py doctor
mkdocs build --strict
```

## Pre-merge criteria

- The commands above should pass.
- If there is pre-existing repository debt, document precise evidence and scope.
- Any functional change in CLI/auth/env/persistence/queue/observability must include documentation updates in the same PR.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

