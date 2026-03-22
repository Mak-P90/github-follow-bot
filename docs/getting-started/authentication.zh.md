# 认证

运行时支持三种真实模式（`BOT_AUTH_MODE`）：

1. `pat`
2. `github_app_installation_token`
3. `github_app`

如果未设置 `BOT_AUTH_MODE`，运行时将保持在 `pat`，并且**不会**自动提升为 `GITHUB_APP_INSTALLATION_TOKEN`。如需使用 installation token，必须显式声明 `BOT_AUTH_MODE=github_app_installation_token`。

## 1) PAT（最简单）

最小变量：

- `GITHUB_USER`
- `PERSONAL_GITHUB_TOKEN`

建议：

- 遵循最小权限原则；
- 不要复用包含多余权限的 PAT。

follow-back 运维说明：

- 对于 `PUT /user/following/{username}`，经典 PAT 需包含 `user:follow`；缺少该 scope 时，GitHub 即使目标存在也可能返回 `404`。
- 发生此类 `404` 时，bot 会在 `follow_failed.reason` 中补充诊断信息（认证模式、观察到的 scopes、当前认证用户），用于区分“权限不足”与“目标不存在”。

## 2) 预签发 installation token

最小变量：

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app_installation_token`
- `GITHUB_APP_INSTALLATION_TOKEN`

## 3) GitHub App 运行时（`github_app`）

最小变量：

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app`
- `GITHUB_APP_ID`
- `GITHUB_APP_INSTALLATION_ID`
- private key 来源必须且只能有 **一个**：
    - `GITHUB_APP_PRIVATE_KEY`
    - `GITHUB_APP_PRIVATE_KEY_FILE`
    - `GITHUB_APP_PRIVATE_KEY_COMMAND`

辅助变量：

- `BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS`
- `BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS`

## 非法组合

- 同时配置多个 key 来源。
- `BOT_AUTH_MODE=github_app_installation_token` 但缺少 `GITHUB_APP_INSTALLATION_TOKEN`。
- `BOT_AUTH_MODE=github_app` 但缺少 `GITHUB_APP_ID`/`GITHUB_APP_INSTALLATION_ID`。
- `BOT_REQUIRE_GITHUB_APP_AUTH=true` 且模式不是 `github_app`。

## 安全启动示例

```env
GITHUB_USER=<your_bot_user>
BOT_AUTH_MODE=github_app
GITHUB_APP_ID=123456
GITHUB_APP_INSTALLATION_ID=987654
GITHUB_APP_PRIVATE_KEY_FILE=/run/secrets/github_app_private_key.pem
BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS=5
BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS=120
```

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

