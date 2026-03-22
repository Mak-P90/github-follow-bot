# 导出

导出命令会生成 JSON 工件，用于审计、运维和加固。

## 审计与完整性

- `export-audit --output <file>`
- `export-sbom --output <file>`
- `export-release-manifest --output <file>`
- `verify-release-manifest --manifest <file> [--require-signature] [--max-age-seconds N]`

## 迁移 / 数据

- `export-postgres-migration-profile --output <file>`
- `export-postgres-cutover-profile --output <file>`
- `export-dual-write-consistency-report --output <file>`

## 可观测性与安全

- `export-otel-bootstrap --output <file>`
- `export-otel-operations-profile --output <file>`
- `export-queue-topology-profile --output <file>`
- `export-zero-trust-profile --output <file>`
- `export-release-integrity-profile --output <file>`

## 推荐运维流程

1. 执行 `doctor`。
2. 执行 `run` 或 `worker`。
3. 按审计/排障需求导出相应工件。
4. 将导出结果与对应 `run_id` 一并保存。

## 审计契约：`discovery_context`

`export-audit` 现在会在由 discovery 触发的动作中包含 `actions[].discovery_context`（序列化 JSON）。

expand 预期字段：`seed_login`、`seed_index`、`phase`、`page`、`discovery_mode`。
followers 预期字段：`discovery_mode`、`page`。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

