# ADR-0001: Introducir límites por capas para reducir acoplamiento de `bot.py`

## Estado
Accepted

## Contexto
El assessment enterprise identifica acoplamiento alto en `bot.py` (configuración + IO + reglas + CLI). Para reducir riesgo de regresión se define un primer corte por capas sin romper contrato CLI existente.

## Decisión
Se introduce esqueleto de módulos por capas:

- `core/domain/contracts.py`: contratos de dominio (`RunExecutor`) para casos de uso.
- `core/application/use_cases.py`: caso de uso `execute_run`.
- `adapters/` y `infra/`: paquetes base para mover adaptadores de API/persistencia e infraestructura en iteraciones siguientes.

El comando `run` deja de invocar `FollowBackService.run()` de forma directa y pasa por el caso de uso `execute_run(...)` para formalizar frontera aplicación/dominio.

## Consecuencias
- Beneficio inmediato: punto único de orquestación de `run` en capa de aplicación.
- Compatibilidad: se mantiene el CLI actual (`python bot.py run|stats|doctor|worker|export-*`).
- Trabajo siguiente: mover progresivamente cliente GitHub, storage y observabilidad a `adapters/*` e `infra/*`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

