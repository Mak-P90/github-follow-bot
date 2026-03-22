# Flux d’exécution (runtime)

**Statut de traduction :** ✅ Vue complétée en français.

**Statut de traduction :** ✅ Vue complétée en français.

## Séquence typique

1. Charger la configuration et valider l’auth.
2. Lancer `doctor` si nécessaire.
3. Exécuter `run` (ou `worker` en mode file).
4. Persister événements/actions.
5. Exporter les artefacts d’audit/observabilité.

## Garanties attendues

- Idempotence des actions de follow.
- Limites opérationnelles actives (`max_follows_per_run`, budgets API).
- Journalisation structurée et corrélée par `run_id`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

