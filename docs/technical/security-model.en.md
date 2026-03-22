# Security Model

> Status: ✅ Completed in British English.

## Core controls

- Explicit authentication modes (`pat`, installation token, GitHub App).
- Strict GitHub App key-source contract (exactly one source).
- Secrets are provided via environment variables, never hardcoded.
- Runtime logging applies secret redaction.

## Runtime safety

- Idempotent follow behaviour.
- Operational limits (`BOT_MAX_FOLLOWS_PER_RUN`, queue retries).
- Dead-letter handling for exhausted retries.

## Integrity and hardening

- Audit exports for command/run traceability.
- Release manifest generation and verification.
- Zero-trust profile support (including cosign guidance).

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

