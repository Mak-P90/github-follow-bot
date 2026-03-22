# GitHub Follower Bot Automated

Automatización de crecimiento de red en GitHub con enfoque en **operación segura**, **persistencia transaccional** y **auditabilidad**.

## Overview

Este subproyecto permite ejecutar ciclos operativos de forma controlada:

- Descubre candidatos desde GitHub API en modo followers (follow-back) y en modo expand (ampliación desde tu red de seguidos).
- Aplica follows de manera idempotente.
- Puede descubrir y forkear repositorios de una cuenta objetivo con filtros granulares.
- Registra ejecuciones, acciones y eventos en SQLite/PostgreSQL.
- Expone comandos de diagnóstico, métricas y exportación de evidencia.
- Mantiene una ruta de hardening enterprise incremental (release integrity, SBOM, observabilidad).

> El CLI es la interfaz principal. La GUI (NiceGUI) es opcional.

## Capacidades principales

- **Persistencia por motor**: SQLite (default) o PostgreSQL.
- **Follow-back automático**: procesa followers pendientes y evita duplicados.
- **Expansión de red**: modo `expand` para descubrir cuentas desde seguidos y sus conexiones.
- **Fork discovery**: capacidad `fork-repos` para forkear repositorios de un usuario con filtros (`--owned`, `--forked`, `--all`, `--profile-readme`).
- **Ejecución durable**: `run`, `worker`, `resume`, `abort`, `fork-repos`.
- **Auditoría**: historial por `run_id`, acciones y eventos de seguridad.
- **Cola operativa**: estados de job (`pending/done/failed/dead_letter`) y métricas de cola.
- **Hardening**:
    - sanitización de secretos en logs,
    - validaciones de doctor,
    - export/verify de release manifest,
    - export de SBOM y perfiles operativos.

## Requisitos

- Python 3.10+
- Dependencias de `requirements.txt`
- Variables mínimas:
    - `GITHUB_USER`
    - modo de autenticación válido (`pat`, `github_app_installation_token`, `github_app`)

## Inicio rápido

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py doctor
python bot.py run
```

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python .\bot.py doctor
python .\bot.py run
```

## Comandos más usados

```bash
# Follow-back / expansión
python bot.py run
python bot.py worker --run-id <id>
python bot.py resume --run-id <id>
python bot.py abort --run-id <id> --reason "operator_request"
# Diagnóstico y observabilidad
python bot.py doctor
python bot.py metrics
python bot.py queue-stats

# Fork de repositorios de un usuario objetivo
python bot.py fork-repos --username <user> --owned
python bot.py fork-repos --username <user> --all --fork-source --follow-fork-owners
```

## Documentación

- Sitio MkDocs: `docs/`
- Guía de inicio: `docs/getting-started/quickstart.md`
- Referencia CLI: `docs/reference/cli.md`
- Variables de entorno: `docs/reference/env-vars.md`
- Arquitectura: `docs/technical/architecture.md`

## Desarrollo y validación mínima

```bash
python -m py_compile bot.py check_all_followers.py
pytest -q
python bot.py doctor
```

## Nota de uso responsable
Automatizar acciones en GitHub puede activar límites, políticas anti-abuso o restricciones de cuenta.  
Usa límites operativos (`BOT_DRY_RUN`, máximos por corrida, budget de cola) y valida permisos/scopes antes de producción.