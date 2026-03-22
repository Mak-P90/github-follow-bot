# MkDocs + GitHub Pages（从零到可发布）

本指南定义了一个可复现的最小流程，用于从当前仓库发布文档。

## 1) 安装文档依赖

建议在项目虚拟环境中执行：

```bash
python -m pip install --upgrade pip
pip install mkdocs mkdocs-material pymdown-extensions
```

## 2) 创建 `mkdocs.yml`

在仓库根目录创建 `mkdocs.yml`：

```yaml
site_name: GitHub Follower Bot Automated
site_description: Operational and technical documentation
site_url: https://<ORG_OR_USER>.github.io/<REPO>/
repo_url: https://github.com/<ORG_OR_USER>/<REPO>
repo_name: <ORG_OR_USER>/<REPO>

theme:
    name: material
    language: en

markdown_extensions:
    - admonition
    - tables
    - toc:
          permalink: true
    - pymdownx.superfences
    - pymdownx.details
    - pymdownx.tabbed:
          alternate_style: true

nav:
    - Home: index.md
    - Getting Started:
          - Installation: getting-started/installation.md
          - Authentication: getting-started/authentication.md
          - Quickstart: getting-started/quickstart.md
          - MkDocs & GitHub Pages: getting-started/mkdocs-github-pages.md
    - User Guide:
          - Daily Operations: user-guide/daily-operations.md
          - Exports: user-guide/exports.md
          - Troubleshooting: user-guide/troubleshooting.md
    - Technical:
          - Architecture: technical/architecture.md
          - Runtime Flow: technical/runtime-flow.md
          - Persistence: technical/persistence.md
          - Observability: technical/observability.md
          - Security Model: technical/security-model.md
          - Testing & Quality: technical/testing-quality.md
    - Reference:
          - CLI: reference/cli.md
          - Environment Variables: reference/env-vars.md
```

> 若后续提供多语言，可通过 `i18n` 插件扩展；当前先采用单站点模式。

## 3) 准备文档目录

确保以下结构存在（可按需增减）：

```text
docs/
  index.md
  getting-started/
  user-guide/
  technical/
  reference/
```

## 4) 本地预览与严格校验

```bash
mkdocs serve
mkdocs build --strict
```

要求：

- `serve` 能正常启动；
- `build --strict` 零错误。

## 5) 新建 GitHub Actions 工作流

创建 `.github/workflows/docs.yml`：

```yaml
name: docs

on:
    push:
        branches: ['main']
    pull_request:

permissions:
    contents: read
    pages: write
    id-token: write

jobs:
    build:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v4
            - uses: actions/setup-python@v5
              with:
                  python-version: '3.11'
            - name: Install docs deps
              run: |
                  python -m pip install --upgrade pip
                  pip install mkdocs mkdocs-material pymdown-extensions
            - name: Build docs
              run: mkdocs build --strict
            - name: Upload Pages artifact
              if: github.ref == 'refs/heads/main' && github.event_name == 'push'
              uses: actions/upload-pages-artifact@v3
              with:
                  path: site

    deploy:
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        needs: build
        runs-on: ubuntu-latest
        environment:
            name: github-pages
            url: ${{ steps.deployment.outputs.page_url }}
        steps:
            - name: Deploy to GitHub Pages
              id: deployment
              uses: actions/deploy-pages@v4
```

## 6) 仓库设置

在 GitHub 仓库中：

1. 进入 **Settings → Pages**。
2. Source 选择 **GitHub Actions**。
3. 合并到 `main` 后，等待工作流自动部署。

## 7) 文档维护建议

- 功能改动应同步更新文档；
- 文档发布唯一来源建议保持为 `main`；
- PR 建议通过 `mkdocs build --strict`。

## 8) 常见问题

### 404（Pages 根路径错误）

- 检查 `site_url` 是否与 `https://<ORG_OR_USER>.github.io/<REPO>/` 一致。
- 若使用自定义域名，补充配置 `CNAME` 与 DNS。

### 构建成功但样式丢失

- 多见于 `site_url` 与子路径不一致。
- 重新确认仓库名大小写与 URL 完全一致。

### 严格模式构建失败

- 检查失效链接、错误路径与未纳入 `nav` 的页面。
- 若为临时占位内容，先降级为可解析文本再提交。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
