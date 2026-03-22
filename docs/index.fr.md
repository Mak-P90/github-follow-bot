# Documentation GitHub Follower Bot

Documentation opérationnelle et technique du bot, publiée depuis `main` dans un flux vivant unique (sans versionnement par release/tag).

## À qui s'adresse cette documentation ?

- **Opérateurs** : installer, authentifier, exécuter et diagnostiquer.
- **Mainteneurs** : comprendre l'architecture, le runtime, la persistance et la sécurité.

## Parcours rapides

1. [Installation](getting-started/installation.fr.md)
2. [Authentification](getting-started/authentication.fr.md)
3. [Quickstart](getting-started/quickstart.fr.md)
4. [Tutoriel MkDocs + GitHub Pages](getting-started/mkdocs-github-pages.fr.md)
5. [Opérations quotidiennes](user-guide/daily-operations.fr.md)
6. [Opérations GUI](user-guide/gui.fr.md)
7. [Dépannage](user-guide/troubleshooting.fr.md)
8. [Architecture technique](technical/architecture.fr.md)
9. [Référence CLI](reference/cli.fr.md)
10. [Référence des variables d'environnement](reference/env-vars.fr.md)

## Politique documentaire

- Source de publication : **`main`**.
- Pas de versionnement documentaire (`mike`, tags, release trees : non).
- Toute PR avec changement fonctionnel significatif doit mettre à jour la documentation dans la même PR.

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
