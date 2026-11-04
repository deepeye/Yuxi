# 知识库类型 milvus 的展示品牌名

状态：implemented
类型：feature
Owner：frontend/src/modules/knowledge/model/kb_utils.js

## 问题

知识库类型 `milvus` 在前端展示层显示为 `Yuxi`（源码项目名），与站点品牌体系（`睿狐` / `Smartfox`，见 `2026-10-11-web-display-brand.md`）不一致：新建知识库弹出层、知识库列表筛选 Tab 与类型标签、知识图谱区都把源码项目名当作类型展示名暴露给用户。

## 决策

`frontend/src/modules/knowledge/model/kb_utils.js` 的 `getKbTypeLabel` 将 `milvus` 映射为 `Smartfox`。该函数是 `milvus` 类型展示名的唯一前端 Owner，新建流程（`KnowledgeBaseCreateFlowModal.vue`）、列表（`KnowledgeCatalog.vue`）、图谱区（`KnowledgeGraphSection.vue`）共用同一映射，全部展示面一致变化，不出现混品牌。品牌名本身统一为 `睿狐`，见 `2026-10-11-web-display-brand.md`；`Smartfox` 只作为该类型的展示名。

后端 `backend/yuxi/modules/knowledge/implementations/milvus.py` 的类属性 `name = "Milvus"` 保持不变：它是 `get_available_types()` 经 API 返回的技术语义名称，仅在前端映射缺失时作为回退。展示品牌与后端技术身份分离，避免数据层携带营销品牌。

### 实现方案

`frontend/src/modules/knowledge/model/kb_utils.js` 的 `getKbTypeLabel` 是 `milvus` 类型展示名的唯一映射点，新建流程 `KnowledgeBaseCreateFlowModal.vue`（类型卡片与步骤标题）、列表页 `KnowledgeCatalog.vue`（筛选下拉与卡片标签）、图谱区 `KnowledgeGraphSection.vue`（类型标签）都经它取值，替换该映射即覆盖全部展示面。测试 `frontend/test/unit/knowledge_base_create_flow.test.js` 的标签映射断言同步更新为 `Smartfox`，保证旧值会使测试失败。

## 替代方案

保留 `Yuxi`：维持源码项目名曝光，与站点品牌继续不一致。采用后端 `name = "Milvus"`：暴露向量引擎名，用户不感知且同样不是品牌。只改弹出层、在组件内单独覆写：产生两个展示 Owner，列表页与弹出层品牌漂移。

## 后果

所有 `milvus` 类型知识库的展示名统一为 `Smartfox`；图标（`DatabaseZap`）、颜色（`blue`）、读写能力不变。后端 API 返回的 `name = "Milvus"` 与前端展示名不同是接受的设计，未来若引入原生 Milvus 连接器作为独立 `kb_type`，需要为新类型重新决定展示名。

## 验证

- Passed：`docker compose exec -T frontend pnpm run test:unit`（更新 `frontend/test/unit/knowledge_base_create_flow.test.js` 中 milvus 标签映射断言为 `Smartfox`）。
- Passed：`docker compose exec -T frontend pnpm run lint:check`。
- 未验证：未做真实浏览器页面验证（纯字符串映射，未触发行为关键升级条件）。
