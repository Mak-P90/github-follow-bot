# 可观测性

## 日志

- 主流程使用结构化 JSON 日志。
- 关键事件包含 `event`，运行上下文内带 `run_id`。
- 涉及认证/密钥错误时必须做敏感信息脱敏。

## 指标

- `python bot.py metrics` 输出 Prometheus 指标。
- 至少覆盖运行次数、follow 结果、队列状态与错误计数。

## 追踪

- 启用 `BOT_OTEL_ENABLED=true` 时输出 OTel 相关上下文。
- 在可用场景下传播 `trace_id` 以支持跨系统关联。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

