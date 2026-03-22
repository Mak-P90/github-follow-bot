# 快速开始

## 1) 准备环境

- Python 3.10+
- 已创建 `.env`（可由 `.env.example` 复制）
- 已配置认证变量（见 `getting-started/authentication.zh.md`）

## 2) 运行健康检查

```bash
python bot.py doctor
```

若输出中 `github_app_configured=true` 或 PAT 校验通过，即可继续。

## 3) 干跑（推荐）

```env
BOT_DRY_RUN=true
```

执行：

```bash
python bot.py run
```

期望：返回 JSON 摘要（`run_id`、`followers_fetched`、`followers_followed`）。

## 4) 正式运行

将 `BOT_DRY_RUN` 设为 `false`（或移除），然后再次执行：

```bash
python bot.py run
```

## 5) 查看状态

```bash
python bot.py stats
python bot.py queue-stats
```

## 6) 导出审计与运维工件

```bash
python bot.py export-audit --output artifacts/commands/audit.json
python bot.py export-release-manifest --output artifacts/commands/release-manifest.json
```

## 7) 最小故障排查路径

1. `doctor`
2. `run`（先 dry-run）
3. `queue-stats`
4. `export-audit`

## Full quickstart coverage (end-to-end operational flow)

After the first `run`, use this complete lifecycle to operate without gaps:

### 1) Initial health verification (`doctor`)

```bash
python bot.py doctor
```

Recommended minimum `.env` contract:

```env
GITHUB_USER=your_user
BOT_AUTH_MODE=pat
PERSONAL_GITHUB_TOKEN=ghp_replace_me
BOT_DRY_RUN=true
```

> If you use GitHub App or installation token, set explicit auth mode (`BOT_AUTH_MODE`) as documented in `getting-started/authentication.zh.md`.

### 2) First safe execution (dry-run)

```bash
python bot.py run
python bot.py stats
python bot.py queue-stats
```

### 3) Real execution (after dry-run validation)

```bash
# in .env: BOT_DRY_RUN=false (or remove the variable)
python bot.py run
python bot.py stats
python bot.py queue-stats
```

### 4) Queue lifecycle with `run_id` (worker/resume/abort)

Get `run_id` from `run` JSON output or from `stats`.

```bash
# process jobs for an existing run
python bot.py worker --run-id <id>

# safely continue a previous run
python bot.py resume --run-id <id>

# abort an active run with persisted reason
python bot.py abort --run-id <id> --reason operator_abort
```

### 5) Minimum operational evidence (audit + release)

```bash
python bot.py export-audit --output artifacts/commands/audit.json
python bot.py export-release-manifest --output artifacts/commands/release-manifest.json
python bot.py verify-release-manifest --manifest artifacts/commands/release-manifest.json --require-signature --max-age-seconds 3600
python bot.py export-sbom --output artifacts/commands/sbom.json
```

### 6) Recommended enterprise gate before merge/release

```bash
./scripts/enterprise_verify.sh
```

### 7) Optional extra operational sanity (recommended)

```bash
python bot.py metrics
python bot.py check-file-hardening
```

### 7.5) Extended runtime sanity (recommended for distributed operation)

```bash
python bot.py control-plane-status
python bot.py scheduler --max-ticks 1 --interval-seconds 60
python bot.py queue-backend-status
python bot.py queue-backend-verify
python bot.py queue-backend-smoke
python bot.py otel-runtime-status
```

### 8) Advanced commands coverage (out of quickstart scope)

Quickstart covers the minimum operational lifecycle. For advanced capabilities, see:

- `getting-started/authentication.zh.md` (auth modes)
- `user-guide/daily-operations.zh.md` (day-2 operations)
- `reference/cli.zh.md` (full command catalog: scheduler, control-plane, GUI, enterprise profiles, etc.)

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
