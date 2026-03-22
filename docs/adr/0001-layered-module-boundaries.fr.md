# ADR-0001 : Introduire des frontières en couches pour réduire le couplage de `bot.py`

**Statut de traduction :** ✅ Vue complétée en français.

## Statut
Accepted

## Contexte
L’évaluation enterprise identifie un fort couplage dans `bot.py` (configuration + I/O + règles + CLI). Pour réduire le risque de régression, un premier découpage en couches est défini sans casser le contrat CLI existant.

## Décision
Introduction d’un squelette de modules en couches :

- `core/domain/contracts.py` : contrats de domaine (`RunExecutor`) pour les cas d’usage.
- `core/application/use_cases.py` : cas d’usage `execute_run`.
- `adapters/` et `infra/` : paquets de base pour migrer les adaptateurs API/persistance et l’infrastructure dans les itérations suivantes.

La commande `run` n’invoque plus directement `FollowBackService.run()` et passe désormais par le cas d’usage `execute_run(...)` pour formaliser la frontière application/domaine.

## Conséquences
- Bénéfice immédiat : point unique d’orchestration de `run` dans la couche application.
- Compatibilité : la CLI actuelle est conservée (`python bot.py run|stats|doctor|worker|export-*`).
- Étape suivante : migration progressive du client GitHub, du stockage et de l’observabilité vers `adapters/*` et `infra/*`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

