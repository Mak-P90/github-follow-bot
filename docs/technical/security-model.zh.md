# 安全模型

## 认证安全

- 严禁硬编码凭据。
- 所有认证均通过环境变量注入。
- GitHub App private key 来源遵循“仅允许一个”的严格契约。
- `BOT_REQUIRE_GITHUB_APP_AUTH=true` 会强制 GitHub App fail-closed 模式。

## 密钥与日志

- 日志中必须脱敏 token / private key。
- 运行命令源（如 `GITHUB_APP_PRIVATE_KEY_COMMAND`）应限制超时并避免隐式 shell。

## 运行安全

- 设置 `max_follows_per_run` 等预算控制自动化风险。
- 队列重试耗尽后必须进入 `dead_letter` 并记录安全事件。

## 发布完整性

- 产物清单（manifest）包含摘要信息（digest）。
- 支持带签名与 TTL 的清单校验。
- 提供 zero-trust/cosign 基线配置导出能力。

## 可追溯性

- 关键事件包含 `event` 并以 `run_id` 关联。
- 在适用场景下附带 `trace_id` 用于跨系统追踪。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

