# Règles de Pull Request de traduction

Cette section définit les critères minimums pour accepter des changements de traduction de documentation.

## 1. Portée et structure

- Conserver la même arborescence de fichiers que la base espagnole.
- Utiliser les suffixes de langue sur chaque page (`.en.md`, `.fr.md`, `.he.md`, `.ru.md`, `.zh.md`).
- Ne pas supprimer les sections techniques du document d’origine pendant la traduction.

## 2. Qualité du contenu

- Préserver le sens technique, les commandes et les exemples de configuration.
- Ne pas traduire les noms de variables, flags CLI, tables ou identifiants de code.
- Conserver les blocs de code et la mise en forme Markdown.

## 3. Cohérence terminologique

- Réutiliser le glossaire du projet pour les termes récurrents.
- Si un nouveau terme est introduit, le documenter dans la même PR.
- Éviter les traductions littérales qui changent le contexte opérationnel.

## 4. Exigences de revue

- Inclure dans la PR la liste des pages impactées par langue.
- Joindre la preuve d’un build MkDocs local réussi.
- Demander au moins une revue par une personne avec le contexte technique du module touché.

## 5. Checklist minimale de PR

- [ ] Fichiers traduits créés/mis à jour avec le suffixe correct.
- [ ] Navigation `mkdocs.yml` validée pour les nouvelles langues.
- [ ] Build de documentation exécuté localement.
- [ ] Terminologie technique revue et cohérente.
- [ ] Changements de périmètre documentés (si applicable).
- [ ] Si des commandes/flags/runbooks opérationnels sont ajoutés, toutes les variantes de langue disponibles sont mises à jour dans la même PR.

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
