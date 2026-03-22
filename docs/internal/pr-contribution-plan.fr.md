# Plan de cotisation PR

**Statut de traduction :** ✅ Vue complétée en français.

## Objectif

Définir un flux de contribution prévisible, auditable et compatible avec les exigences enterprise du projet.

## Portée des PR

Toute PR qui touche au comportement fonctionnel (auth, CLI, persistance, queue, sécurité, observabilité) doit inclure :

- code,
- tests/contrôles,
- documentation alignée.

## Liste de contrôle RP

- [ ] Description claire du problème et de la solution.
- [ ] Impact explicite sur auth/CLI/env/DB/queue/security.
- [ ] Mise à jour de `README.md` si le contrat utilisateur change.
- [ ] Mise à jour des pages docs concernées.
- [ ] Validation locale des commandes de qualité.
- [ ] Evidence des résultats de test dans la PR.

## Validation minimale recommandée
```bash
python -m py_compile bot.py check_all_followers.py
pytest -q
python bot.py doctor
mkdocs build --strict
```

## Bonnes pratiques de review

1. Vérifier l’idempotence et la sécurité des actions de follow.
2. Vérifier la gestion correcte des secrets (pas de hardcode, pas de fuite en logs).
3. Vérifier la cohérence entre runtime et documentation.
4. Vérifier que les exports critiques restent fonctionnels.

## Critère de merge

- Les checks requis passent.
- Les changements sont documentés.
- Les écarts préexistants, s’il y en a, sont explicitement signalés.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

