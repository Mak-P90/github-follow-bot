# 翻译 Pull Request 规则

本节定义接受文档翻译变更的最低标准。

## 1. 范围与结构

- 保持与西班牙语基线文档相同的文件树。
- 每个页面使用语言后缀（`.en.md`、`.fr.md`、`.he.md`、`.ru.md`、`.zh.md`）。
- 翻译过程中不得删除原文中的技术章节。

## 2. 内容质量

- 保持技术语义、命令与配置示例不变。
- 不翻译变量名、CLI flags、表名或代码标识符。
- 保持代码块和 Markdown 格式完整。

## 3. 术语一致性

- 对复用术语使用项目既有术语表。
- 如引入新术语，需在同一 PR 中记录。
- 避免改变运维语境的直译。

## 4. 评审要求

- 在 PR 中列出按语言划分的受影响页面。
- 附上本地 MkDocs 构建成功证据。
- 至少请求一位具有相关模块技术背景的评审者。

## 5. PR 最低检查清单

- [ ] 已按正确后缀创建/更新翻译文件。
- [ ] 已验证 `mkdocs.yml` 中新语言导航。
- [ ] 已本地执行文档构建。
- [ ] 技术术语已审阅并保持一致。
- [ ] 已记录范围变更（如适用）。
- [ ] 若新增运维命令/flags/runbook，需在同一 PR 中更新所有可用语言版本。

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
