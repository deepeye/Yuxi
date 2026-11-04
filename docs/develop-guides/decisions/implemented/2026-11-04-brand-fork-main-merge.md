# 品牌分支合并上游结构重组

状态：implemented
类型：architecture
Owner：docs/develop-guides/decisions/implemented/2026-10-11-web-display-brand.md

## 问题

品牌分支 `feat/fix-brand` 基于旧目录结构：前端在 `web/`，后端包在 `backend/package/yuxi/`，品牌由 `organization` 与 `branding` 两个字段表达，并删除了仓库内大量上游 GitHub 链接。`origin/main` 已把前端迁到 `frontend/`、后端包迁到 `backend/yuxi/`，并在 `2026-10-16-product-branding-config.md` 中把品牌收敛为单一 `branding.name`。直接合并会产生 modify/delete 冲突，且两套品牌模型无法同时成立，必须明确保留哪些品牌事实。

## 决策

- 采用上游的目录结构和单一品牌模型：`branding.name` 是唯一产品名，合并后取 `睿狐`；`footer.copyright` 同为 `睿狐`。
- `Smartfox` 只保留为知识库类型 `milvus` 的前端展示名，见 `2026-10-12-kb-type-brand-label.md`。
- 分支原有的去品牌化意图继续有效：标签页标题跟随运行时 `branding.name`，默认回退 `睿狐`；登录页、侧栏、会话导航的品牌回退字面量同步为 `睿狐`；已删除的 GitHub Star 卡片、文档中心入口、GitHub 入口和首页仓库链接不因上游重写而恢复。
- 合并冲突集中的 22 个 Markdown 用户文档（即本次合并 `docs/**/*.md` 的未合并路径，不含决策记录、changelog 与 postmortem）继续去品牌化：上游源码链接改为代码路径，仓库克隆与 upstream 地址改为去品牌化占位符（`https://example.com/your-fork/Yuxi.git` 或 `https://<your-fork-host>/<your-org>/Yuxi.git`），站内文档改为相对链接。上游新增、且不在分支原改动范围的文档保持上游内容。
- 上游已提供等价能力的改动以合入上游为准：OCR 工具开关修复已在 `backend/yuxi/modules/agents/runtime/middlewares/model_input.py` 中实现；上游移除了自定义 `tool.uv.index` 并把 `backend/uv.lock` 全部指向官方 PyPI，因此分支的清华源改阿里云索引不再适用，锁文件采用上游版本；`docker/api.Dockerfile` 的 Debian 源仍按分支意图改为阿里云镜像。

### 实现方案

前端品牌投影位于 `frontend/src/modules/settings/model/info.js` 的 `setInfoConfig`：写入 `document.title = "${branding.name} - Knowledge Management"`，名称缺失时回退 `睿狐`。`frontend/src/app/layouts/AppLayout.vue`、`frontend/src/modules/session/ui/SessionNavigation.vue`、`frontend/src/pages/LoginView.vue` 从同一 Store 读取 `branding.name`，回退字面量为 `睿狐`。站点信息模板 `backend/yuxi/modules/system/static/info.template.yaml` 拥有默认品牌值，`backend/test/unit/routers/test_system_router.py` 断言模板中的产品名。

文档站配置保留 `/Yuxi/` 基路径，但移除上游 `sitemap.hostname`（原值不适用于本仓库，且非法值会使构建失败）、GitHub social link、edit link 和上游 og 图片。`frontend/public/favicon.svg` 为红色 72×32 资产，由 `frontend/index.html`、`branding.logo` 消费。

## 替代方案

- **rebase 分支并逐条重放品牌提交**：同步产生同样的 modify/delete 冲突，还会重写已推送历史，未减少人工判断。
- **保留旧 `web/`、`backend/package/` 结构**：无法合入上游后续修复，分叉持续扩大。
- **恢复 `organization` 字段以保留 `睿狐`/`Smartfox` 双名**：推翻 `2026-10-16-product-branding-config.md` 的单一来源收敛，重新引入两份名称事实。
- **把 `branding.name` 设为 `Smartfox`**：会使侧栏、登录页、首页和标签页出现英文产品名，与分支已确定的中文默认品牌 `睿狐` 不一致；`Smartfox` 继续只作为类型展示名。

## 后果

- 侧栏、登录页、首页与标签页统一显示 `睿狐`；知识库 `milvus` 类型仍显示 `Smartfox`。
- 自定义品牌 YAML 必须使用上游的单 `branding` 结构；旧 `organization` 配置不再生效。
- 分支先前未触及的上游文档和新文档仍可能包含上游 GitHub 链接；本记录不把它们纳入去品牌化范围，后续如需统一处理应另立变更。
- `packages/yuxi-cli` 已由上游改写为 npm 包，原 `pyproject.toml` 的 `project.urls` 移除不再适用；npm `package.json` 中的 `repository`/`bugs` 字段保持上游值。
- 文档站不再生成 sitemap.xml。

## 验证

- Passed：`python3 scripts/ci/verify_engineering_contracts.py`（357 decisions / 10 workflows / 4 agents files / 522 docs / 42 routers / 325 frontend sources）。
- Passed：`python3 -m unittest scripts.ci.test_verify_engineering_contracts`（56 tests OK）。
- Passed：`cd frontend && pnpm run lint:check`。
- Passed：`cd frontend && pnpm run test:unit`（1015 passed，0 failed）。
- Passed：`cd frontend && pnpm run build`；构建产物 `dist/index.html` 标题为 `睿狐 - Knowledge Management`。
- Passed：`cd docs && pnpm run build`（无 dead link）。
- Passed：`git diff --cached --check` 干净；`info.template.yaml` 经 YAML 解析确认 `branding.name=睿狐`、footer 版权为睿狐；改动过的 Python 文件 `py_compile` 通过。
- Passed：`backend/uv.lock` 与 `origin/main` 完全一致，202 个 registry 条目均指向官方 PyPI，`tuna.tsinghua` 出现 0 次。
- 未验证：未运行 `backend/test/unit`。本机 `backend/.venv` 缺少 fastapi/pytest，正在运行的 API 容器创建于合并前、仍挂载已删除的 `backend/package`，无法代表合并后的代码；上游已为 `model_input.py` 提供覆盖 OCR 开关同类行为的测试，合并直接采用上游实现与测试。
- 未验证：未做真实浏览器页面验证（未重新构建并启动前端容器）。

旧能力不存在：`organization` 品牌字段、独立头像、Star 卡片、文档中心/GitHub 菜单入口和首页仓库链接均不存在。

重新引入条件：任何恢复第二个品牌名称字段、重新引入上游仓库推广入口，或扩大/缩小文档去品牌化范围的决定，必须引用本记录说明部署方影响。
