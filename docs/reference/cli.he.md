# מדריך CLI

## תחביר בסיסי

```bash
python bot.py <command> [options]
```

אם לא צוינה פקודה, ברירת המחדל היא `python bot.py run`.

## פקודות ליבה

- `python bot.py run` → מריץ מחזור סנכרון מלא.
- `python bot.py stats` → מציג סיכום מצב מתמשך והרצות אחרונות.
- `python bot.py doctor` → בדיקות תצורה, מצב אימות, חוזי DB/runtime ובקרות hardening.
- `python bot.py metrics` → פלט מדדי Prometheus ל-stdout.
- `python bot.py check-file-hardening` → בדיקת הרשאות/בעלות של קבצי runtime.

## פעולות תור

- `python bot.py queue-stats [--run-id <id>]`
- `python bot.py worker --run-id <id> [--max-jobs <n>]`
- `python bot.py resume --run-id <id> [--max-jobs <n>]`
- `python bot.py abort --run-id <id> [--reason <text>]`

## יצוא ודגמי release integrity

- `python bot.py export-audit --output <file>`
- `python bot.py export-sbom --output <file>`
- `python bot.py export-release-manifest --output <file>`
- `python bot.py verify-release-manifest --manifest <file> [--require-signature] [--max-age-seconds N]`

## פרופילי enterprise ו-readiness

- `python bot.py export-postgres-migration-profile --output <file>`
- `python bot.py export-postgres-cutover-profile --output <file>`
- `python bot.py export-dual-write-consistency-report --output <file>`
- `python bot.py export-otel-bootstrap --output <file>`
- `python bot.py export-otel-operations-profile --output <file>`
- `python bot.py export-queue-topology-profile --output <file>`
- `python bot.py export-zero-trust-profile --output <file>`
- `python bot.py export-release-integrity-profile --output <file>`
- `python bot.py export-governance-profile --output <file>`
- `python bot.py export-enterprise-readiness-report --output <file> [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py enterprise-readiness-gate [--evidence-dir artifacts/enterprise-evidence] [--allow-partial]`
- `python bot.py enterprise-backlog-status [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py enterprise-remaining-work [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py enterprise-handoff-report [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py compliance-evidence-status [--evidence-dir artifacts/enterprise-evidence]`

## Control plane, scheduler ו-backend תור מבוזר

### `control-plane-status`

- פקודה: `python bot.py control-plane-status`
- מטרה: מצב readiness קומפקטי של control plane ללא העלאת שרת HTTP.

### `serve-control-plane`

- פקודה: `python bot.py serve-control-plane [--host 127.0.0.1] [--port 8080]`
- מטרה: הפעלת שירות HTTP מינימלי של control plane.

### `scheduler`

- פקודה: `python bot.py scheduler [--interval-seconds 60] [--max-ticks 1] [--lock-key default] [--lock-ttl-seconds 300]`
- מטרה: הרצת לולאת scheduler עם נעילה למניעת ריצות מקבילות.

### בדיקות backend תור

- `python bot.py queue-backend-status` → מצב readiness של backend התור.
- `python bot.py queue-backend-verify` → אימות חוזה topology/runtime של backend התור.
- `python bot.py queue-backend-smoke` → smoke test למסלול enqueue/claim/update.

### בדיקת OTel runtime

- `python bot.py otel-runtime-status` → מצב tracing runtime וקורלציה של `trace_id`.

## אוטומציית forks ו-GUI

- `python bot.py fork-repos --username <github_user> [--owned|--forked|--all] [--profile-readme] [--fork-source] [--follow-fork-owners]`
- `python bot.py gui`

## הנחיות תפעוליות

- להריץ `doctor` לפני run ראשון ואחרי שינוי auth/secrets.
- לפני gate ברמת enterprise להריץ `queue-backend-status` ו-`compliance-evidence-status`.
- ב-CI/hardening להשתמש ב-`verify-release-manifest --require-signature --max-age-seconds <ttl>`.

## Sync status (2026-03-22)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-22**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `python bot.py control-plane-status`
- `python bot.py scheduler -h`
- `python bot.py serve-control-plane -h`
- `python bot.py queue-backend-status`
- `python bot.py queue-backend-verify`
- `python bot.py queue-backend-smoke`
- `python bot.py otel-runtime-status`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
