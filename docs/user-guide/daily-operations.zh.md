# 日常运维

## 核心运维命令

- `python bot.py run`  
  执行一次完整运行。

- `python bot.py worker --run-id <id> [--max-jobs <n>]`  
  处理指定 run 的队列任务。

- `python bot.py stats`  
  查看持久化状态摘要 + 最近一次 run。

- `python bot.py queue-stats [--run-id <id>]`  
  查看队列状态（`pending`、`done`、`failed`、`dead_letter`）。

- `python bot.py doctor`  
  输出 config/auth/DB/hardening 诊断。

## 扩展运维（control plane、scheduler、queue backend）

- `python bot.py control-plane-status`  
  不启动 HTTP 服务时输出 control plane 状态快照。

- `python bot.py serve-control-plane --host 127.0.0.1 --port 8080`  
  启动最小化 control plane HTTP endpoint，用于受控运维。

- `python bot.py scheduler --interval-seconds 60 --max-ticks 1 --lock-key default --lock-ttl-seconds 300`  
  运行带锁保护的 scheduler 循环，避免并发触发。

- `python bot.py queue-backend-status` / `python bot.py queue-backend-verify` / `python bot.py queue-backend-smoke`  
  检查队列后端 readiness、runtime/topology 契约与 smoke 路径。

- `python bot.py otel-runtime-status`  
  检查运行时 tracing readiness 与 `trace_id` 关联状态。

## 何时使用

- 新部署或 secrets 变更：`doctor`。
- 常规执行：`run`。
- 队列驱动运行：`worker` + `queue-stats`。
- 受控/分布式运行：`scheduler` + `queue-backend-*` + `control-plane-status`。
- 全局巡检：`stats`。

## 期望信号

- `run` 返回 JSON，含 `run_id`、`followers_fetched`、`followers_followed`。
- `doctor` 返回 auth 状态、DB 完整性与运维开关。
- `queue-stats` 可观测重试耗尽与 dead-letter 行为。
- `otel-runtime-status` 反馈 OTel 场景下 runtime tracing 的可用性。

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
