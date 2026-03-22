# 运行时流程

## `run` 高层流程

1. 读取配置并初始化认证。
2. 创建并持久化 `run_id`。
3. 拉取 followers / 发现候选。
4. 根据策略入队 `follow_jobs`。
5. 执行 follow 并记录结果。
6. 输出摘要（JSON）与关键指标。

## `worker` 流程

- 按 `run_id` 读取 `pending` jobs。
- 按重试预算处理失败。
- 超出预算进入 `dead_letter` 并产生可审计事件。

## 故障保护

- 支持 `BOT_DRY_RUN`。
- 对 429/5xx 具备阈值与窗口控制。
- 可选择退化到 followers 流程（fallback）。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

