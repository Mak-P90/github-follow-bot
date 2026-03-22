# PR 贡献计划（文档体系）

## 目标

确保未来 PR 在改动 CLI、认证、环境变量、持久化、队列、可观测性或安全时，同步更新文档，避免“代码升级、文档滞后”。

## 适用范围

当 PR 触及以下任一领域时：

- 命令新增/删除/重命名；
- 环境变量契约变更（新增、废弃、语义变化）；
- 认证流程（PAT、Installation Token、GitHub App）；
- 数据持久化（schema、导出、迁移、双写）；
- 队列与 worker 行为；
- 可观测性（日志、指标、trace）；
- 安全与发布完整性（manifest、签名、zero-trust）。

## PR 模板建议（可复制到 `.github/pull_request_template.md`）

```md
## Summary

- [ ] 功能变更已描述
- [ ] 风险与回滚方案已描述

## Docs Checklist (required)

- [ ] README.md
- [ ] docs/reference/cli.zh.md
- [ ] docs/reference/env-vars.zh.md
- [ ] docs/getting-started/\*（如受影响）
- [ ] docs/user-guide/\*（如受影响）
- [ ] docs/technical/\*（如受影响）
- [ ] .env.example（如适用）

## Validation

- [ ] python -m py_compile bot.py check_all_followers.py
- [ ] pytest -q
- [ ] python bot.py doctor
- [ ] mkdocs build --strict
```

## Reviewer 检查要点

1. **CLI 对齐**：文档列出的命令是否可执行，参数是否一致。
2. **env vars 对齐**：变量名、默认值、强制条件是否与代码一致。
3. **模式对齐**：认证模式非法组合是否写清。
4. **运维可执行性**：新 operator 是否可按文档完成部署/排障。
5. **风险信息可见性**：是否写明 fail-closed、dead-letter、retry budget 等关键行为。

## 建议工作流

1. 开发功能。
2. 同步更新相关文档页。
3. 本地执行 `mkdocs build --strict`。
4. 提交 PR，并在描述中粘贴文档变更摘要。
5. Reviewer 合并前完成 docs checklist 打勾。

## 最低门槛（建议 CI 强制）

- PR 上必须通过 docs build。
- 若代码改动涉及上述高风险区域，PR 需包含 docs diff（可在 CI 中检测路径）。
- 若缺少 docs 变更，应在 PR 中明确说明“为何无需更新文档”。

## 示例：路径映射建议

- 认证改动 → `docs/getting-started/authentication.zh.md` + `docs/reference/env-vars.zh.md`
- 新增导出命令 → `docs/reference/cli.zh.md` + `docs/user-guide/exports.zh.md`
- 队列状态语义变化 → `docs/user-guide/daily-operations.zh.md` + `docs/technical/runtime-flow.zh.md`
- 安全 gate 调整 → `docs/technical/security-model.zh.md` + `README.md`

## 完成定义（DoD）

一个“可合并”的功能 PR 至少满足：

- 代码与文档同时更新；
- docs build 通过；
- reviewer 能基于文档独立复现关键操作路径；
- 不存在已知“命令/变量”文档与代码不一致。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
