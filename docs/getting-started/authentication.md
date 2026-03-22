# Authentication

El runtime soporta tres modos reales (`BOT_AUTH_MODE`):

1. `pat`
2. `github_app_installation_token`
3. `github_app`

Si `BOT_AUTH_MODE` no se define, el runtime queda en `pat` y **no** promociona automáticamente `GITHUB_APP_INSTALLATION_TOKEN`. Para usar installation token debes declarar explícitamente `BOT_AUTH_MODE=github_app_installation_token`.

## 1) PAT (simple)

Variables mínimas:

- `GITHUB_USER`
- `PERSONAL_GITHUB_TOKEN`

Recomendación:

- mínimo privilegio,
- no reutilizar PAT con permisos innecesarios.

Nota operativa follow-back:

- para `PUT /user/following/{username}` el PAT clásico debe incluir `user:follow`; sin ese scope GitHub puede responder `404` aunque el perfil exista.
- cuando ocurre ese `404`, el bot ahora agrega diagnóstico en `follow_failed.reason` (modo de auth, scopes observados y usuario autenticado) para diferenciar permisos de inexistencia real del perfil.

## 2) Installation token preemitido

Variables mínimas:

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app_installation_token`
- `GITHUB_APP_INSTALLATION_TOKEN`

## 3) GitHub App runtime (`github_app`)

Variables mínimas:

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app`
- `GITHUB_APP_ID`
- `GITHUB_APP_INSTALLATION_ID`
- **exactamente una** fuente de private key:
    - `GITHUB_APP_PRIVATE_KEY`
    - `GITHUB_APP_PRIVATE_KEY_FILE`
    - `GITHUB_APP_PRIVATE_KEY_COMMAND`

Variables de soporte:

- `BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS`
- `BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS`

## Combinaciones inválidas

- Múltiples fuentes de key al mismo tiempo.
- `BOT_AUTH_MODE=github_app_installation_token` sin `GITHUB_APP_INSTALLATION_TOKEN`.
- `BOT_AUTH_MODE=github_app` sin `GITHUB_APP_ID`/`GITHUB_APP_INSTALLATION_ID`.
- `BOT_REQUIRE_GITHUB_APP_AUTH=true` con modo distinto de `github_app`.

## Ejemplo seguro de inicio

```env
GITHUB_USER=your_user
BOT_AUTH_MODE=pat
PERSONAL_GITHUB_TOKEN=ghp_replace_me
BOT_DRY_RUN=true
```

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

