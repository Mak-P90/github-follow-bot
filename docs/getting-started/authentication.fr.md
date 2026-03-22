# Authentification

**Statut de traduction :** ✅ Vue complétée en français.

Le runtime supporte trois modes réels (`BOT_AUTH_MODE`) :

1. `pat`
2. `github_app_installation_token`
3. `github_app`

Si `BOT_AUTH_MODE` n’est pas défini, le runtime reste en `pat` et **ne promeut pas automatiquement** `GITHUB_APP_INSTALLATION_TOKEN`. Pour utiliser un installation token, définissez explicitement `BOT_AUTH_MODE=github_app_installation_token`.

## 1) PAT (simple)

Variables minimales :

- `GITHUB_USER`
- `PERSONAL_GITHUB_TOKEN`

Recommandation :

- principe du moindre privilège,
- ne pas réutiliser un PAT avec des permissions inutiles.

Note opérationnelle follow-back :

- pour `PUT /user/following/{username}`, un PAT classique doit inclure `user:follow` ; sans ce scope, GitHub peut renvoyer `404` même si le profil existe.
- lorsque ce `404` survient, le bot ajoute maintenant un diagnostic dans `follow_failed.reason` (mode auth, scopes observés et utilisateur authentifié) pour distinguer un problème de permissions d’une absence réelle du profil.

## 2) Installation token préémis

Variables minimales :

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app_installation_token`
- `GITHUB_APP_INSTALLATION_TOKEN`

## 3) GitHub App runtime (`github_app`)

Variables minimales :

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app`
- `GITHUB_APP_ID`
- `GITHUB_APP_INSTALLATION_ID`
- **exactement une** source de clé privée :
  - `GITHUB_APP_PRIVATE_KEY`
  - `GITHUB_APP_PRIVATE_KEY_FILE`
  - `GITHUB_APP_PRIVATE_KEY_COMMAND`

Variables de support :

- `BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS`
- `BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS`

## Combinaisons invalides

- Plusieurs sources de clé en même temps.
- `BOT_AUTH_MODE=github_app_installation_token` sans `GITHUB_APP_INSTALLATION_TOKEN`.
- `BOT_AUTH_MODE=github_app` sans `GITHUB_APP_ID`/`GITHUB_APP_INSTALLATION_ID`.
- `BOT_REQUIRE_GITHUB_APP_AUTH=true` avec un mode différent de `github_app`.

## Exemple de démarrage sécurisé

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

