# Architecture

**Statut de traduction :** ✅ Vue complétée en français.

**Statut de traduction :** ✅ Vue complétée en français.

## Vue d’ensemble

Le projet suit une évolution vers une architecture en couches :

- domaine / contrats,
- application / cas d'utilisation,
- adaptateurs (API, persistance),
- infrastructure (runtime, observabilité, sécurité).

## Principes

- séparation des responsabilités,
- idempotence des actions critiques,
- auditabilité via événements structurés,
- compatibilité CLI conservée pendant les refactors.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

