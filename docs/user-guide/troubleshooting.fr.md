# Dépannage

**Statut de traduction :** ✅ Vue complétée en français.

## 401 / erreur d’auth

- Vérifier `BOT_AUTH_MODE`.
- Valider les variables minimales du mode choisi.
- Pour `github_app`, confirmer **une seule** source de clé.
- Exécuter `python bot.py doctor` et vérifier `auth_mode`, `github_app_configured`.

## Limite de taux

- Vérifier `check_all_followers.py` et les métriques.
- Réduire la fréquence d’exécution.
- Appliquer `BOT_MAX_FOLLOWS_PER_RUN` pour le contrôle opérationnel.

## Configuration incomplète

Erreurs fréquentes :
- `GITHUB_USER` manquant.
- Token/identifiants du mode actif manquants.
- `GITHUB_APP_PRIVATE_KEY_FILE` pointe vers un chemin inexistant.

## Problèmes de clé GitHub App

- `GITHUB_APP_PRIVATE_KEY_FILE` : vérifier existence/permissions.
- `GITHUB_APP_PRIVATE_KEY_COMMAND` : vérifier une sortie non vide et le timeout.
- Ne pas combiner inline/file/command simultanément.

## Dry-run

En cas de doute opérationnel, utiliser :
```env
BOT_DRY_RUN=true
```

Cela valide le flux sans follow réel.

## Erreurs d’environnement Windows

- Activation venv échouée (execution policy) :
  - lancer PowerShell avec une politique adaptée aux scripts locaux.
- Chemins avec espaces :
  - utiliser des guillemets autour des chemins.

## Erreurs de chemin/permissions

- DB non inscriptible : vérifier permissions du dossier/fichier `BOT_DB_PATH`.
- Secret mount indisponible : vérifier le chemin effectif via `doctor`.

## Logs et interprétation

- Le bot émet des logs JSON structurés.
- Corréler avec `run_id` et `trace_id`.
- Vérifier les événements de sécurité lors d’échecs auth/queue.

## Disjoncteur d'expansion (`expand_circuit_breaker_open`)

Si des 429/5xx se répètent au-delà du seuil (`BOT_EXPAND_HTTP_ERROR_THRESHOLD`) dans la fenêtre (`BOT_EXPAND_HTTP_ERROR_WINDOW`) :

- le bot interrompt l’expand du run courant ;
- enregistre `security_event=expand_circuit_breaker_open` ;
- émet un log structuré avec `seed_login`, `phase`, `page`, `status_code` ;
- optionnel : fallback vers `followers` si `BOT_EXPAND_FALLBACK_TO_FOLLOWERS=true`.

Étapes opérationnelles :
1. Vérifier `python bot.py export-audit --output artifacts/commands/audit.json` puis filtrer `security_events`.
2. Ajuster le rythme/cron et les budgets (`BOT_MAX_API_CALLS_PER_RUN`, `BOT_MAX_EXPAND_SEEDS_PER_RUN`).
3. Confirmer si un fallback temporaire vers followers est pertinent.

## Curseur expand incohérent

Si `expand_seed_index` est hors plage ou `expand_seed_page` est invalide (0/négatif/non numérique), le runtime revient à un état sûr (index 0 / page 1) et continue sans exception fatale.

La file `follow_jobs` conserve l’unicité (`run_id`, `github_login`), évitant les doublons sur un même run même avec curseur corrompu.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

