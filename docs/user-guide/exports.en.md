# Exports

> Status: ✅ Completed in British English.

Exports produce JSON artefacts for audit, operations, and hardening.

## Audit and integrity

- `export-audit --output <file>`
- `export-sbom --output <file>`
- `export-release-manifest --output <file>`
- `verify-release-manifest --manifest <file> [--require-signature] [--max-age-seconds N]`

## Migration / data

- `export-postgres-migration-profile --output <file>`
- `export-postgres-cutover-profile --output <file>`
- `export-dual-write-consistency-report --output <file>`

## Observability and security

- `export-otel-bootstrap --output <file>`
- `export-otel-operations-profile --output <file>`
- `export-queue-topology-profile --output <file>`
- `export-zero-trust-profile --output <file>`
- `export-release-integrity-profile --output <file>`

## Recommended operational flow

1. Run `doctor`.
2. Run `run` or `worker`.
3. Export required artefacts for audit or troubleshooting.
4. Store results with the associated `run_id`.

## Audit contract: `discovery_context`

`export-audit` now includes `actions[].discovery_context` (serialised JSON) when an action originates from discovery.

Expected fields in expand mode: `seed_login`, `seed_index`, `phase`, `page`, `discovery_mode`.
Expected fields in followers mode: `discovery_mode`, `page`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

