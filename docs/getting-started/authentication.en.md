# Authentication

> Status: ✅ Completed in British English.

Runtime supports three concrete modes (`BOT_AUTH_MODE`):

1. `pat`
2. `github_app_installation_token`
3. `github_app`

If `BOT_AUTH_MODE` is not defined, runtime stays on `pat` and does **not** automatically promote `GITHUB_APP_INSTALLATION_TOKEN`. To use an installation token, explicitly set `BOT_AUTH_MODE=github_app_installation_token`.

## 1) PAT (simple)

Minimum variables:

- `GITHUB_USER`
- `PERSONAL_GITHUB_TOKEN`

Recommendation:

- Apply least privilege.
- Do not reuse PATs with unnecessary permissions.

Follow-back operational note:

- For `PUT /user/following/{username}`, a classic PAT must include `user:follow`; without this scope GitHub may return `404` even when the profile exists.
- When this `404` occurs, the bot now adds diagnostics to `follow_failed.reason` (auth mode, observed scopes, and authenticated user) to distinguish permission issues from genuine missing profiles.

## 2) Pre-issued installation token

Minimum variables:

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app_installation_token`
- `GITHUB_APP_INSTALLATION_TOKEN`

## 3) GitHub App runtime (`github_app`)

Minimum variables:

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app`
- `GITHUB_APP_ID`
- `GITHUB_APP_INSTALLATION_ID`
- **exactly one** private key source:
    - `GITHUB_APP_PRIVATE_KEY`
    - `GITHUB_APP_PRIVATE_KEY_FILE`
    - `GITHUB_APP_PRIVATE_KEY_COMMAND`

Support variables:

- `BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS`
- `BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS`

## Invalid combinations

- Multiple key sources at the same time.
- `BOT_AUTH_MODE=github_app_installation_token` without `GITHUB_APP_INSTALLATION_TOKEN`.
- `BOT_AUTH_MODE=github_app` without required App identifiers.

## Operational checks

Run:

```bash
python bot.py doctor
```

Check at least:

- `auth_mode`
- `github_app_configured`
- effective key source visibility (`inline`, `file`, `command`, or `none`)

## Security notes

- Never hardcode credentials.
- Never print secrets in logs.
- Prefer rotatable key sources (`..._FILE` / `..._COMMAND`) for GitHub App mode.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

