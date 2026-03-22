# Opérations quotidiennes

**Statut de traduction :** ✅ Vue complétée en français.

## Principales commandes opérationnelles

- `python bot.py run`  
  Exécute un run complet.

- `python bot.py worker --run-id <id> [--max-jobs <n>]`  
  Traite la file de jobs pour un run.

- `python bot.py stats`  
  Résumé de l'état persistant + dernier run.

- `python bot.py queue-stats [--run-id <id>]`  
  État de la file (`pending`, `done`, `failed`, `dead_letter`).

- `python bot.py doctor`  
  Diagnostic configuration/auth/DB/hardening.

## Opération étendue (control plane, scheduler, backend de file)

- `python bot.py control-plane-status`  
  Snapshot du control plane sans démarrer le serveur HTTP.

- `python bot.py serve-control-plane --host 127.0.0.1 --port 8080`  
  Démarre l'endpoint HTTP minimal du control plane pour l'exploitation supervisée.

- `python bot.py scheduler --interval-seconds 60 --max-ticks 1 --lock-key default --lock-ttl-seconds 300`  
  Lance la boucle scheduler avec verrou pour éviter les déclenchements concurrents.

- `python bot.py queue-backend-status` / `python bot.py queue-backend-verify` / `python bot.py queue-backend-smoke`  
  Vérifie readiness backend, contrat runtime/topologie et smoke test.

- `python bot.py otel-runtime-status`  
  Valide la readiness de traçabilité runtime et la corrélation `trace_id`.

## Quand utiliser chaque commande

- Nouveau déploiement ou changement de secrets : `doctor`.
- Exécution standard : `run`.
- Exploitation orientée file : `worker` + `queue-stats`.
- Exploitation contrôlée/distribuée : `scheduler` + `queue-backend-*` + `control-plane-status`.
- Revue générale : `stats`.

## Signaux attendus

- `run` renvoie un JSON avec `run_id`, `followers_fetched`, `followers_followed`.
- `doctor` renvoie l'état auth, l'intégrité DB et les flags opérationnels.
- `queue-stats` expose retries épuisés et comportement dead-letter.
- `otel-runtime-status` confirme la posture de traçage runtime pour les environnements OTel.

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
