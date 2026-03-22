# Architecture

## Mapa real de módulos

- **Entrypoint**: `bot.py`
- **Domain contract**: `core/domain/contracts.py`
- **Application use-case**: `core/application/use_cases.py`
- **Adapters**: `adapters/*` (incluye `queue/rabbitmq_adapter.py`)
- **Infra policy**: `infra/policy/engine.py`

## Responsabilidades

- `bot.py`: parser CLI, carga config/env, composición de servicios, ejecución de comandos y exports.
- `core/domain`: contratos para desacoplar caso de uso.
- `core/application`: orquestación de caso de uso (`execute_run`).
- `adapters`: punto de integración para cola/transportes.
- `infra/policy`: reglas de consentimiento/denylist.

## Límites

- Flujo principal sigue centrado en `bot.py` (monolito en descomposición).
- Existe base de capas, pero no separación completa de todos los concerns.

Ver ADR: `docs/adr/0001-layered-module-boundaries.md`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

