# 架构

系统按职责拆分为几层：

- **CLI / Orchestration**：命令入口与运行流程编排。
- **Application**：用例（如 `execute_run`）。
- **Domain**：业务契约与核心规则。
- **Adapters/Infra**：GitHub API、数据库、日志、导出器等实现。

## 目标

- 降低 `bot.py` 的历史耦合。
- 在不破坏 CLI 兼容性的前提下渐进重构。
- 为持久化升级（SQLite → Postgres）与可观测性增强预留边界。

## 关键原则

1. 命令契约稳定优先。
2. 领域规则与 IO 分离。
3. 导出/审计能力是“一等公民”。
4. 所有关键路径都必须具备可诊断性（doctor、metrics、audit）。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

