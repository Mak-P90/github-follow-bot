# Observability

> Status: ✅ Completed in British English.

## Logging

- Structured JSON logging for runtime operations.
- Critical events include `event` and `run_id`.
- `trace_id` is used when cross-flow correlation is available.

## Operational visibility

- `doctor` reports configuration, auth status, and key runtime controls.
- Export commands provide auditable artefacts.
- Queue and security events are exposed for troubleshooting and hardening.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

