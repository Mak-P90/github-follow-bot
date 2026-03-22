# ADR-0001: Introduce layered boundaries to reduce `bot.py` coupling

> Status: ✅ Completed in British English.

## Status

Accepted

## Context

The enterprise assessment identified high coupling in `bot.py` (configuration + IO + rules + CLI). To reduce regression risk, we introduce an initial layered split without breaking the existing CLI contract.

## Decision

A layered module skeleton is introduced:

- `core/domain/contracts.py`: domain contracts (`RunExecutor`) for use cases.
- `core/application/use_cases.py`: `execute_run` use case.
- `adapters/` and `infra/`: base packages to move API/persistence adapters and infrastructure in subsequent iterations.

The `run` command no longer calls `FollowBackService.run()` directly; it now goes through `execute_run(...)` to formalise the application/domain boundary.

## Consequences

- Immediate benefit: a single `run` orchestration point in the application layer.
- Compatibility: current CLI remains intact (`python bot.py run|stats|doctor|worker|export-*`).
- Next work: progressively move GitHub client, storage, and observability into `adapters/*` and `infra/*`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

