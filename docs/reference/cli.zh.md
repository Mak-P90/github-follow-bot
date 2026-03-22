# CLI 参考

## 基本语法

```bash
python bot.py <command> [options]
```

如果未指定命令，默认等同于 `python bot.py run`。

## 核心命令

- `python bot.py run` → 执行一次完整同步。
- `python bot.py stats` → 汇总持久化状态与最近运行信息。
- `python bot.py doctor` → 诊断配置、认证模式、数据库/运行时契约与 hardening 控制。
- `python bot.py metrics` → 以文本格式输出 Prometheus 指标。
- `python bot.py check-file-hardening` → 校验运行时文件权限/属主约束。

## 队列操作

- `python bot.py queue-stats [--run-id <id>]`
- `python bot.py worker --run-id <id> [--max-jobs <n>]`
- `python bot.py resume --run-id <id> [--max-jobs <n>]`
- `python bot.py abort --run-id <id> [--reason <text>]`

## 导出与发布完整性

- `python bot.py export-audit --output <file>`
- `python bot.py export-sbom --output <file>`
- `python bot.py export-release-manifest --output <file>`
- `python bot.py verify-release-manifest --manifest <file> [--require-signature] [--max-age-seconds N]`

## Enterprise 配置画像与 readiness

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

## 控制平面、调度器与分布式队列后端

### `control-plane-status`

- 命令：`python bot.py control-plane-status`
- 作用：不启动 HTTP 服务时输出控制平面的简要 readiness/status。

### `serve-control-plane`

- 命令：`python bot.py serve-control-plane [--host 127.0.0.1] [--port 8080]`
- 作用：启动最小化控制平面 HTTP 服务。

### `scheduler`

- 命令：`python bot.py scheduler [--interval-seconds 60] [--max-ticks 1] [--lock-key default] [--lock-ttl-seconds 300]`
- 作用：运行带锁保护的调度循环，避免并发触发。

### 队列后端校验命令

- `python bot.py queue-backend-status` → 报告后端 readiness。
- `python bot.py queue-backend-verify` → 校验队列拓扑/运行时契约。
- `python bot.py queue-backend-smoke` → 执行 enqueue/claim/update 的快速 smoke 测试。

### OTel 运行时检查

- `python bot.py otel-runtime-status` → 输出运行时 tracing 与 `trace_id` 关联状态。

## Fork 自动化与 GUI

- `python bot.py fork-repos --username <github_user> [--owned|--forked|--all] [--profile-readme] [--fork-source] [--follow-fork-owners]`
- `python bot.py gui`

## 运维建议

- 首次运行前以及调整认证/密钥后执行 `doctor`。
- 执行 enterprise readiness gate 之前先运行 `queue-backend-status` 与 `compliance-evidence-status`。
- 在 CI/hardening 中使用 `verify-release-manifest --require-signature --max-age-seconds <ttl>`。

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
