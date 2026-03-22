# 故障排查

## 401 / 认证错误

- 检查 `BOT_AUTH_MODE`。
- 校验所选模式的最小变量是否齐全。
- 对于 `github_app`，确认 key 来源只有 **一个**。
- 执行 `python bot.py doctor`，检查 `auth_mode`、`github_app_configured`。

## 速率限制（Rate limit）

- 检查 `check_all_followers.py` 与相关指标。
- 降低运行频率。
- 使用 `BOT_MAX_FOLLOWS_PER_RUN` 做运维限额。

## 配置不完整

常见错误：
- 缺少 `GITHUB_USER`。
- 当前模式缺少 token/凭据。
- `GITHUB_APP_PRIVATE_KEY_FILE` 指向不存在路径。

## GitHub App key 问题

- `GITHUB_APP_PRIVATE_KEY_FILE`：检查文件存在性与权限。
- `GITHUB_APP_PRIVATE_KEY_COMMAND`：检查输出非空与超时配置。
- 不要同时混用 inline/file/command。

## Dry-run

若存在运维不确定性，可使用：

```env
BOT_DRY_RUN=true
```

这样可以在不执行真实 follow 的情况下验证流程。

## Windows 环境常见错误

- venv 激活失败（execution policy）：
  - 请在允许本地脚本执行的策略下运行 PowerShell。
- 路径含空格：
  - 需要时请为文件路径加引号。

## 路径 / 权限错误

- DB 不可写：检查 `BOT_DB_PATH` 对应目录/文件权限。
- Secret 挂载不可用：在 `doctor` 中确认实际生效路径。

## 日志解读

- bot 输出结构化 JSON 日志。
- 通过 `run_id` 与 `trace_id` 做关联分析。
- 认证或队列失败时重点检查安全事件。

## expand 熔断（`expand_circuit_breaker_open`）

若在窗口（`BOT_EXPAND_HTTP_ERROR_WINDOW`）内，429/5xx 重复超阈值（`BOT_EXPAND_HTTP_ERROR_THRESHOLD`）：

- bot 会中止当前运行的 expand；
- 记录 `security_event=expand_circuit_breaker_open`；
- 输出包含 `seed_login`、`phase`、`page`、`status_code` 的结构化日志；
- 若 `BOT_EXPAND_FALLBACK_TO_FOLLOWERS=true`，可回退到 followers 路径。

运维步骤：
1. 执行 `python bot.py export-audit --output artifacts/commands/audit.json`，筛选 `security_events`。
2. 调整节奏/cron 与预算（`BOT_MAX_API_CALLS_PER_RUN`、`BOT_MAX_EXPAND_SEEDS_PER_RUN`）。
3. 评估是否临时开启 followers fallback。

## expand 游标不一致

若 `expand_seed_index` 越界，或 `expand_seed_page` 非法（0/负数/非数值），运行时会回退到安全状态（索引 0 / 页面 1）并继续执行，不触发致命异常。

`follow_jobs` 通过（`run_id`, `github_login`）保持唯一性，即便游标损坏，同一 run 也不会产生重复任务。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

