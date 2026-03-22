# GitHub Follower and Fork Bot Documentation

Documentación operativa y técnica del bot, publicada desde `main` en un único flujo vivo (sin versionado por release/tag).

## ¿Para quién es?

- **Operadores**: instalar, autenticar, ejecutar y diagnosticar.
- **Maintainers**: entender arquitectura, runtime, persistencia y seguridad.

## Caminos rápidos

1. [Instalación](getting-started/installation.md)
2. [Autenticación](getting-started/authentication.md)
3. [Quickstart](getting-started/quickstart.md)
4. [Tutorial MkDocs + GitHub Pages](getting-started/mkdocs-github-pages.md)
5. [Operación diaria](user-guide/daily-operations.md)
6. [GUI operativa](user-guide/gui.md)
7. [Troubleshooting](user-guide/troubleshooting.md)
8. [Arquitectura técnica](technical/architecture.md)
9. [Referencia CLI](reference/cli.md)
10. [Referencia de variables](reference/env-vars.md)

## Política documental

- Fuente de publicación: **`main`**.
- Sin versionado de docs (`mike`, tags, release trees: no).
- PR con cambio funcional relevante => actualización de docs en el mismo PR.

## Sync status (2026-03-22)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-22**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `python bot.py control-plane-status`
- `python bot.py scheduler -h`
- `python bot.py queue-backend-status`
- `python bot.py queue-backend-verify`
- `python bot.py queue-backend-smoke`
- `python bot.py otel-runtime-status`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
