# Security Model

## Autenticación

Modos soportados:
- PAT
- Installation token preemitido
- GitHub App runtime

Reglas clave:
- En modo `github_app`: `GITHUB_APP_ID` + `GITHUB_APP_INSTALLATION_ID` + exactamente una fuente de key.
- `BOT_REQUIRE_GITHUB_APP_AUTH=true` fuerza modo fail-closed de GitHub App runtime.

## Secretos

- No hardcodear credenciales.
- Uso exclusivo de variables de entorno.
- Redacción de secretos en logging.

## Integridad de release

- Manifiesto de artefactos con digest.
- Verificación de manifiesto con firma opcional y TTL.
- Perfil zero-trust/cosign para endurecimiento.

## Trazabilidad

- Eventos críticos con `event` y correlación por `run_id`.
- `trace_id` para correlación transversal cuando aplica.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

