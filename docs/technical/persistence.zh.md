# 持久化

## 当前模型

- 运行状态、队列与审计数据存储在事务型数据库（默认 SQLite）。
- `follow_jobs` 维护状态：`pending`、`done`、`failed`、`dead_letter`。

## 设计约束

- follow 操作必须具备幂等性。
- 每次运行必须有 `run_id`，用于关联日志、导出与队列。
- 禁止使用 `followers.txt` 等文本文件作为主数据库。

## 迁移方向

- 提供 `export-postgres-migration-profile` 与 `export-postgres-cutover-profile`。
- 支持 dual-write 一致性报告（`export-dual-write-consistency-report`）。
- 持久化变更必须保证 `export-audit` 继续可用。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

