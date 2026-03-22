# GitHub Follower and Fork Bot Documentation

Operational and technical documentation for the bot, published from `main` in a single living workflow (no release/tag versioning).

## Who is this for?

- **Operators**: install, authenticate, run, and diagnose.
- **Maintainers**: understand architecture, runtime, persistence, and security.

## Quick paths

1. [Installation](getting-started/installation.en.md)
2. [Authentication](getting-started/authentication.en.md)
3. [Quickstart](getting-started/quickstart.en.md)
4. [MkDocs + GitHub Pages tutorial](getting-started/mkdocs-github-pages.en.md)
5. [Daily operations](user-guide/daily-operations.en.md)
6. [GUI operations](user-guide/gui.en.md)
7. [Troubleshooting](user-guide/troubleshooting.en.md)
8. [Technical architecture](technical/architecture.en.md)
9. [CLI reference](reference/cli.en.md)
10. [Environment variables reference](reference/env-vars.en.md)

## Documentation policy

- Publishing source: **`main`**.
- No docs versioning (`mike`, tags, release trees: no).
- PRs with relevant functional changes must update docs in the same PR.

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
