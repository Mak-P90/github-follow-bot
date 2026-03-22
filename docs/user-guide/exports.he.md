# יצוא

הייצוא מייצר חפצי JSON לביקורת, תפעול והקשחה.

## ביקורת ויושרה

- `export-audit --output <file>`
- `export-sbom --output <file>`
- `export-release-manifest --output <file>`
- `verify-release-manifest --manifest <file> [--require-signature] [--max-age-seconds N]`

## הגירה / נתונים

- `export-postgres-migration-profile --output <file>`
- `export-postgres-cutover-profile --output <file>`
- `export-dual-write-consistency-report --output <file>`

## צפייה ואבטחה

- `export-otel-bootstrap --output <file>`
- `export-otel-operations-profile --output <file>`
- `export-queue-topology-profile --output <file>`
- `export-zero-trust-profile --output <file>`
- `export-release-integrity-profile --output <file>`

## שימוש תפעולי מומלץ

1. הפעל `doctor`.
2. הפעל את `run` או `worker`.
3. ייצא חפצים הדרושים לביקורת או לפתרון בעיות.
4. שמור תוצאות ליד `run_id` המשויך.

## חוזה ביקורת: discovery_context

`export-audit` כולל כעת `actions[].discovery_context` (JSON בסידרה) כאשר הפעולה מגיעה מגילוי.

שדות צפויים בהרחבה: `seed_login`, `seed_index`, `phase`, `page`, `discovery_mode`.
שדות צפויים בעוקבים: `discovery_mode`, `page`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

