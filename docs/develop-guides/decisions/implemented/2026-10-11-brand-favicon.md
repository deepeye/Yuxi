# Web 默认 favicon 资产替换

状态：implemented
类型：feature
Owner：frontend/public/favicon.svg

## 问题

`frontend/public/favicon.svg` 是源码默认的方形黄色狐狸图标（128×128），部署方需要把它换成新的红色图形。该文件承担用户可见显示面：浏览器标签页图标（`frontend/index.html` 硬编码 `<link rel="icon" href="/favicon.svg">`）、登录页与首页头部 logo（经站点信息模板 `branding.logo` 指向 `/favicon.svg`）。

上游 `2026-10-16-product-branding-config.md` 移除了独立 `organization.avatar` 与侧边栏头像，本记录合并后只保留标签页、登录页和首页三个显示面。

## 决策

把 `frontend/public/favicon.svg` 逐字替换为新的 72×32 图形，不修改 SVG 内容、不修改任何引用方式。新图形是单条 `fill="#D94848"` 的 path，无 `viewBox`，仅声明 `width="72" height="32"`。

### 实现方案

`frontend/public/favicon.svg` 是这些显示面的唯一事实 Owner：`frontend/index.html` 按固定路径引用标签页图标，`backend/yuxi/modules/system/static/info.template.yaml` 的 `branding.logo` 默认值为 `/favicon.svg`。替换文件内容即同时改变这些显示面，无需改动任何代码、模板或样式。渲染由各消费点的 CSS 决定：`LoginView.vue` 的 `.brand-logo` 为 `height:32px; width:auto; object-fit:contain`，`HomeView.vue` 的 `.logo-img` 为 `height:2rem`（默认根字号下等同 32px）且宽度随固有比例，两者都按 72:32 原生比例完整渲染、无变形。

## 替代方案

- **给 SVG 补 `viewBox="0 0 72 32"`**：可让缩放行为更明确，但会偏离"逐字替换源文件"的目标，且实测缩放行为可接受（见验证），不需要这一步。
- **同时替换 `docs/public/favicon.svg`**：文档站另有一个为 16/20 像素专门简化并加了安全边的版本，且其 VitePress 配置使用带 `/Yuxi/` 前缀的独立路径，属于不同的显示 Owner，不在本次范围。
- **改为运行时配置驱动标签页图标**：与同日的 `2026-10-11-web-display-brand` 记录方向一致，但会新增配置表面与测试，超出本次"替换资产"的目标。
- **另存一份方形资产专供 24px 头像**：可避免裁切，但引入了源文件中不存在的第二个图形，属于新增维护表面；上游已移除独立头像，当前没有该显示面。

## 后果

- 浏览器标签页图标从方形黄色狐狸变为 2.25:1 的红色图形。SVG 无 `viewBox`，按 SVG 规范其 viewBox 默认为 `0 0 72 32`、`preserveAspectRatio` 默认为 `xMidYMid meet`：标签页 16×16 图标位实际渲染为居中的 16×7 红色横条，上下各留约 4.5px 空白，图形不再充满整个图标位。这是接受的取舍——原方形图标在该尺寸下的可辨认度优势不复存在，横条仍是可辨识的品牌色块。
- 登录页与首页头部 logo 会按原生比例渲染该图形，无变形、无裁切，外观符合预期。
- 原始实现中侧边栏 24×24 头像经 `object-fit: cover` 只显示图形中间一条；上游移除独立头像后该显示面不存在，当前无此裁切效果。
- 文档站 favicon 保持原样，与 Web 端不再一致。
- 标签页图标仍由 `frontend/index.html` 静态硬编码，不随运行时品牌配置更新；部署方无法通过站点信息配置替换它。

## 验证

- Passed：`diff /Users/felixwang/Desktop/favicon.svg frontend/public/favicon.svg` 无输出，`wc -c` 两侧同为 1684 字节，确认逐字复制。
- Passed：`git diff --check` 干净；文件以单个换行结尾。
- Passed：真实浏览器渲染（Chromium 经 `python3 -m http.server` 加载仓库内 `frontend/public/favicon.svg`）：在 16×16（标签页图标位）、32×32（logo 样式）、72×32（原生尺寸）、128×128 四档位下，图片 `naturalWidth/naturalHeight` 均为 72×32，`getBoundingClientRect` 与 CSS 尺寸一致。canvas 采样确认 32×32 与 128×128 档位为 meet 缩放——墨迹保持 72:32 比例、居中留白，无拉伸变形；16×16 档位墨迹为 16×7 居中横条（上 4 行、下 5 行空白），与后果一节描述一致。
- Passed：与 ImageMagick `meet`/`stretch` 基准图逐像素对照：Chromium 32×32 墨迹比例 ≈2.2:1（meet），与强制拉伸基准（充满全框、比例 1:1）明显不同，排除拉伸渲染。
- 截图（本地证据，`.playwright-mcp/` 被 Git 忽略、不入库）：`.playwright-mcp/page-2026-10-11T14-28-04-111Z.png`（五档位对照，16px 格内可见居中红条与上下留白）、`.playwright-mcp/avatar24.png`（24px 头像中间裁切效果）。截图为当时观察的留档；可复现方式是任一浏览器打开引用 `/favicon.svg` 的页面并按上述档位采样。
- 未验证：未运行 `docker compose exec frontend pnpm run build` 或启动真实前端服务截图；未运行 backend integration / E2E（本变更不触及后端链路）。

重新引入条件：任何新增第二个方形资产、或把标签页图标改为运行时配置驱动的变更，必须引用本记录并说明部署方影响。
