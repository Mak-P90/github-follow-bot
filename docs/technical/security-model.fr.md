# Modèle de sécurité

**Statut de traduction :** ✅ Vue complétée en français.

**Statut de traduction :** ✅ Vue complétée en français.

## Contrôles de base

- Pas de secrets en dur.
- Redaction des secrets dans les logs.
- Variables d’environnement comme contrat de configuration.
- Validation fail-fast des prérequis d’authentification.

## Authentification

- PAT, jeton d'installation, ou GitHub App (`BOT_AUTH_MODE`).
- En mode GitHub App : exactement une source de clé privée (inline/file/command).
- Possibilité de mode fail-closed via `BOT_REQUIRE_GITHUB_APP_AUTH`.

## Intégrité de release

- Manifeste d’artefacts + vérification.
- Profil zero-trust/cosign pour le durcissement.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

