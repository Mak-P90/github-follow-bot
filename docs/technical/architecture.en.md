# Architecture

> Status: ✅ Completed in British English.

## Current direction

The project follows a layered architecture to reduce coupling and improve maintainability.

## Layers

- **Core/domain**: contracts and business invariants.
- **Application**: use-case orchestration (`execute_run`).
- **Adapters**: external service and persistence integrations.
- **Infrastructure**: runtime and operational tooling.

## Design goals

- Keep CLI contracts stable whilst refactoring internals.
- Isolate side effects (network/DB/IO) from business rules.
- Enable safer incremental migration from monolithic flows.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

