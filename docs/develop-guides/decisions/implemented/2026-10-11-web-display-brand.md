# Web 显示层品牌与标签页标题

状态：implemented
类型：feature
Owner：frontend/src/modules/settings/model/info.js

## 问题

浏览器标签页标题由 `frontend/index.html` 硬编码，不随运行时品牌配置更新：部署方把站点信息改为自有品牌后，标签页仍长期显示源码默认品牌，与页面内品牌不一致。站点信息配置 `backend/yuxi/modules/system/static/info.template.yaml` 是运行时品牌的语义 Owner，但标签页是同一字符串的第二个独立 Owner，两者会各自漂移。

## 决策

标签页标题由运行时品牌配置驱动，静态 `frontend/index.html` 只保留与默认品牌一致的初始值；`branding.name` 是标题的品牌来源，缺少时回退到源码默认品牌 `睿狐`，后缀 `- Knowledge Management` 作为页面用途描述保留在代码中。品牌名统一为 `睿狐`；知识库类型 `milvus` 的展示名 `Smartfox` 是独立映射，见 `2026-10-12-kb-type-brand-label.md`。

本记录最初以旧 `organization.name` 作为标题来源。上游 `2026-10-16-product-branding-config.md` 把 `organization` 与 `branding` 收敛为单一 `branding.name` 后，标题来源随之改为 `branding.name`；两条记录的合并取舍见 `2026-11-04-brand-fork-main-merge.md`。

### 实现方案

`frontend/src/modules/settings/model/info.js` 的 `setInfoConfig` 是所有品牌配置写入的汇合点（初次加载、`HomeView` 重试、`AppLayout` 加载、`DebugComponent` 强制刷新都经它），在此写入 `document.title`；`typeof document !== 'undefined'` 守卫与同文件 `localStorage` 读取一致，使 SSR 单测无需 DOM。读取失败路径不调用 `setInfoConfig`，标签页保持 `frontend/index.html` 的静态默认值，因此失败时仍显示正确品牌。

`backend/yuxi/modules/system/static/info.template.yaml` 拥有站点信息默认值：`branding.name` 与 `footer.copyright` 同时使用 `睿狐`。`frontend/src/pages/LoginView.vue`、`frontend/src/app/layouts/AppLayout.vue` 与 `frontend/src/modules/session/ui/SessionNavigation.vue` 的品牌回退字面量属于同一显示面，同步更新。

## 替代方案

让 `index.html` 继续硬编码品牌并只在构建期替换，会保留两个品牌 Owner 与漂移可能；保留 `organization.name` 作为标题来源需要维持上游已移除的第二个品牌字段；新增 `branding.document_title` 配置字段会引入没有其他 consumer 的长期维护表面。

## 后果

部署方修改站点信息后，标签页与页面内品牌一致；品牌只来自 `branding.name` 一处，不会出现组织名与产品名分叉。聊天机器人人设、CLI 本地 UI、文档站、wire 契约与 GitHub 仓库地址不在本次范围。

## 验证

- Passed（原始实现）：`docker compose exec -T web pnpm run test:unit` 新增两例：配置写入标签页标题且产品名缺失时回退、读取失败不覆盖静态标题。
- Passed（合并后）：`frontend/test/unit/infoStore.test.js` 覆盖 `branding.name` 写入标题、缺少名称时回退 `睿狐`、读取失败不覆盖静态标题。
- Passed（原始与合并后）：`frontend/index.html` 静态标题为 `睿狐 - Knowledge Management`。
- 未验证：未做真实浏览器页面验证（标签页由静态标题切到运行时标题的过渡未截图）；未运行 backend integration / E2E。

旧能力不存在：`frontend/index.html` 与站点信息模板中面向用户可见的 `语析` 字符串已清除；标签页不再由静态文件独占品牌。

重新引入条件：任何让标签页品牌脱离 `branding.name` 或重新硬编码到 `frontend/index.html` 的变更，必须引用本记录、说明部署方影响，并给出兼容窗口或回退方案。
