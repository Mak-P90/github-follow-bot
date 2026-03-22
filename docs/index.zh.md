# GitHub Follower Bot 文档

该机器人文档（运维与技术）从 `main` 分支持续发布（不按 release/tag 做版本化）。

## 适用对象

- **运维人员**：安装、认证、运行与诊断。
- **维护者**：理解架构、运行时、持久化与安全。

## 快速入口

1. [安装](getting-started/installation.zh.md)
2. [认证](getting-started/authentication.zh.md)
3. [快速开始](getting-started/quickstart.zh.md)
4. [MkDocs + GitHub Pages 教程](getting-started/mkdocs-github-pages.zh.md)
5. [日常运维](user-guide/daily-operations.zh.md)
6. [GUI 运维](user-guide/gui.zh.md)
7. [故障排查](user-guide/troubleshooting.zh.md)
8. [技术架构](technical/architecture.zh.md)
9. [CLI 参考](reference/cli.zh.md)
10. [环境变量参考](reference/env-vars.zh.md)

## 文档策略

- 发布源：**`main`**。
- 不进行文档版本化（`mike`、tags、release trees：否）。
- 包含重要功能变更的 PR 必须在同一 PR 中更新文档。

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
