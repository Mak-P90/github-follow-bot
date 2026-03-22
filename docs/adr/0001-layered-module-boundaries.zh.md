# ADR-0001：引入分层边界以降低 `bot.py` 耦合

## 状态
Accepted

## 背景
Enterprise 评估指出 `bot.py` 存在高耦合（配置 + IO + 规则 + CLI 混杂）。为降低回归风险，决定先引入分层切分，在不破坏现有 CLI 契约的前提下推进重构。

## 决策
引入分层模块骨架：

- `core/domain/contracts.py`：领域契约（`RunExecutor`）用于用例编排。
- `core/application/use_cases.py`：`execute_run` 用例。
- `adapters/` 与 `infra/`：基础包，后续迭代迁移 API/持久化适配器与基础设施。

`run` 命令不再直接调用 `FollowBackService.run()`，而是通过 `execute_run(...)` 进入应用层，从而明确应用/领域边界。

## 影响
- 立即收益：`run` 的编排入口在应用层统一。
- 兼容性：保持现有 CLI（`python bot.py run|stats|doctor|worker|export-*`）不变。
- 后续工作：逐步将 GitHub 客户端、存储与可观测性迁移到 `adapters/*` 与 `infra/*`。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

