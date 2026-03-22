# 运维 GUI（NiceGUI）

GUI 是 CLI 之上的**可选**运维界面。

## 安全启动

```bash
BOT_GUI_ENABLED=true BOT_GUI_HOST=127.0.0.1 BOT_GUI_PORT=8081 python bot.py gui
```

- 默认仅本地绑定：`127.0.0.1`。
- 若未安装 `nicegui`，命令将以受控方式失败并返回退出码 `2`。

## 变量

- `BOT_GUI_ENABLED`（默认：`false`）
- `BOT_GUI_HOST`（默认：`127.0.0.1`）
- `BOT_GUI_PORT`（默认：`8081`）
- `BOT_GUI_LOCALE`（默认：`en`，回退：`en`）

## MVP 范围

- Dashboard
- Runs（start/resume/abort）
- Diagnostics（`doctor`）
- Queue/Metrics
- Exports（`export-audit`）

## 集成契约

GUI 通过 `control_plane` 适配器进行委托，不包含业务逻辑，也不直接调用 GitHub API。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

