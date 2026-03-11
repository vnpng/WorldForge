# 文件说明 (供 AI 助手参考)
本文件是 WorldForge 项目的【全局技术白皮书与架构底座】（活文档）。
在任何新需求开发前，请务必仔细阅读本文件的架构设计、表结构与 UI 规范。绝对禁止在更新中破坏现有的双核机制、UI 视觉隔离体系与状态持久化逻辑。

# WorldForge 全局技术白皮书 (当前版本: V14.0.0)

## 一、 项目基础信息
* **项目名称**: WorldForge
* **当前版本**: V14.0.0 (UI Overhaul & Asset System)
* **项目定位**: 基于 FastAPI + SQLite 的模块化文字冒险游戏引擎与聊天终端。
* **核心技术栈**:
    * **前端**: Vue 3 (Composition API) + Vite + Tailwind CSS + Marked.js + Sortable.js
    * **后端**: Python 3.x + FastAPI + Pydantic + PyJWT
    * **数据库**: SQLite 3 (`worldforge.db`)，使用原生 `sqlite3` 库。

---

## 二、 目录结构规范
```
/
├── main.py              # 后端 FastAPI 入口，API 路由、JWT 鉴权、静态资源挂载
├── database.py          # 数据库初始化、表结构升级、连接管理
├── data/
│   └── worldforge.db    # 持久化数据库文件
├── frontend/            # Vite 前端项目根目录
│   ├── index.html
│   ├── vite.config.js
│   ├── src/
│   │   ├── main.js      # Vue 应用入口
│   │   ├── App.vue      # 根组件
│   │   ├── style.css    # 全局样式（含 Markdown 渲染、气泡 UI、CoT 折叠）
│   │   ├── constants/
│   │   │   ├── default_prompts.js   # 内置 System Prompt 种子数据
│   │   │   └── random_libs.js       # 多主题开局随机词库
│   │   └── components/  # 各视图组件
└── docs/                # 技术文档与行为规范
```

---

## 三、 数据存储层 (SQLite 表结构定义)
系统已彻底实现多用户数据隔离。所有业务表均含 `user_id` 外键。

1. **`Users` 表 (账号体系)**
   * 字段: `id` (TEXT PK), `username` (TEXT UNIQUE), `password_hash` (TEXT), `role` (superadmin/user), `created_at` (INT)。

2. **`InviteCodes` 表 (闭门注册)**
   * 字段: `code` (TEXT PK), `created_by` (TEXT FK), `is_used` (INT), `created_at` (INT)。

3. **`Sessions` 表 (会话与存档)**
   * 字段: `id` (TEXT PK), `user_id` (TEXT FK), `type` (TEXT), `title` (TEXT), `messages` (TEXT), `updatedAt` (INTEGER)。

4. **`SystemPrompts` 表 (引擎预设)**
   * 字段: `id` (TEXT PK), `user_id` (TEXT FK/system), `name` (TEXT), `content` (TEXT), `is_public` (INT), `sort_index` (INT)。
   * 说明: `user_id = 'system'` 且 `is_public = 1` 的预设为系统级公共资源，对所有登录用户可见，仅 superadmin 可修改。

5. **`Profiles` 表 (API 节点配置)**
   * 字段: `id` (TEXT PK), `user_id` (TEXT FK), `name` (TEXT), `baseUrl` (TEXT), `apiKey` (TEXT), `model` (TEXT), `memoryLength` (INT), `stmLength` (INT), `tempRpg` (REAL), `tempChat` (REAL)。
   * 前端 API 节点管理已实现三项能力，打通后端时需配套对应接口：① 多节点切换（下拉选择，选中即生效）；② 批量快速添加（支持粘贴多行，格式为 `Name,URL,Key,Model`，一次性创建多个节点）；③ 全量导出/导入 JSON（用于备份与迁移用户的节点配置）。

6. **`Worlds` 表 (世界资产) [V14 NEW]**
   * 字段: `id` (TEXT PK), `user_id` (TEXT FK), `name` (TEXT, 必填), `intro` (TEXT, 必填), `desc` (TEXT), `conflict` (TEXT), `society` (TEXT), `history` (TEXT), `geography` (TEXT), `magic_system` (TEXT), `rules` (TEXT), `extra_rules` (TEXT), `sort_index` (INT), `created_at` (INT)。
   * 必填项: `name`, `intro`。
   * 表单折叠规则: `name / intro / desc / conflict` 默认展开；`society / history / geography / magic_system / rules / extra_rules` 默认折叠在"展开更多详细设定"面板中，若任意一项有数据则自动展开。

7. **`Characters` 表 (角色资产) [V14 NEW]**
   * 字段: `id` (TEXT PK), `user_id` (TEXT FK), `name` (TEXT, 必填), `gender` (TEXT, 必填), `age` (TEXT, 必填), `race` (TEXT), `identity` (TEXT, 必填), `appearance` (TEXT), `personality` (TEXT), `item` (TEXT), `style` (TEXT), `custom` (TEXT), `sort_index` (INT), `created_at` (INT)。
   * 必填项: `name`, `gender`, `age`, `identity`。
   * 表单折叠规则: `name / gender / age / race / identity` 默认展开；其余字段默认折叠。

---

## 四、 核心架构与底层协议 (Protocols)

### 1. 双核驱动与 UI 视觉隔离机制 (极度重要，禁止破坏)
系统在创建会话时进行严格的逻辑与视觉分流：

* **RPG 模式 (Game Core)**:
    * **逻辑**: 组合 `[选中的世界资产] + [选中的角色资产] + [选中的引擎预设]` 生成完整 System Prompt，经后端 AI Proxy 路由发送。
    * **视觉**: 对话区背景为深黑辐射渐变。用户气泡为深紫色 (`#7D39EB`)，AI 气泡无背景色透明呈现，营造沉浸感。

* **聊天模式 (Chat Core)**:
    * **逻辑**: 使用通用助手 Prompt，经后端 AI Proxy 路由发送。
    * **视觉**: 对话区背景纯深色。用户气泡为荧光绿渐变 (`#BFF729`)，文字为深色。AI 气泡无背景色透明呈现。

### 2. AI 调用架构 (Backend Proxy 模式，禁止绕过)
**已确定采用方案 B：后端 Proxy 模式。禁止在前端直接调用任何 AI API。**

* **调用链**: 前端 → `POST /api/chat` → 后端取出 `apiKey` → 请求 AI 服务商 → 流式转发响应 → 前端渲染。
* **理由**: 所有中间层能力（rate limiting、上下文压缩、Lorebook 注入、Function Calling、行为埋点）均挂载在后端 `/api/chat` 路由上，前端只负责发送消息和渲染结果。
* **流式输出**: 后端使用 FastAPI `StreamingResponse` 转发 AI 的 SSE 流，前端用 `fetch` ReadableStream 接收，实现打字机效果。

### 3. 多用户数据隔离机制 (Security Protocol)
* **鉴权层**: 后端基于 JWT 算法，所有业务接口强制依赖 `get_current_user` 中间件。
* **物理隔离**: 所有 CRUD 操作通过 SQL `WHERE user_id = ?` 进行绝对阻断，防止横向越权。
* **权限分级**: `superadmin` 可管理系统级公共资源；普通 `user` 只能操作自己的数据。

### 4. 三大核心资产体系 (V14 NEW)
WorldForge 的开局由三种资产组合驱动，均支持独立创建、编辑、删除和拖拽排序：

* **引擎 (Engine)**: 对应 `SystemPrompts` 表。控制 AI 的行为规则与叙事风格。`isPublic` 开关仅 superadmin 可见。
* **世界 (World)**: 对应 `Worlds` 表。定义故事发生的背景框架。
* **角色 (Character)**: 对应 `Characters` 表。定义玩家扮演的角色信息。

RPG 开局时，用户从三个列表中各选一项，后端将三者内容合并拼装为完整的 System Prompt。

### 5. 思维链 (CoT) 强力阻断机制
* AI 引擎被强制要求使用 `<cot>...</cot>` 标签进行剧情推演。
* 前端使用正则将其替换为 `<details class="cot-box">`。
* 顶层绑定 `:class="{'hide-cot': !showCoT}"`，利用 CSS 的 `.hide-cot details.cot-box { display: none !important; }` 彻底隐藏推演过程。

### 6. 拖拽排序规范
* 引擎、世界、角色三个列表均支持拖拽排序，统一使用 **Sortable.js**（CDN 引入），禁止改用原生 HTML5 拖拽事件。
* 拖拽完成后调用对应的排序持久化接口，将新的 `sort_index` 写入数据库。
* CSS 中已定义 `.sortable-chosen`、`.sortable-ghost`、`.sortable-drag` 三套样式，禁止删除。

---

## 五、 版本更新日志 (Changelog)

### [V14.0.0] UI Overhaul & Asset System (重大重构) [CURRENT]
* **前端重构**: 单文件 HTML 迁移至 Vite + Vue 3 工程化项目，CSS/JS/模板彻底分离。
* **视觉升级**: 全新设计语言，主色调调整为紫色 (`#7D39EB`) + 荧光绿 (`#BFF729`) 双品牌色体系；引入侧边导航栏与多视图路由架构。
* **资产体系建立**: 新增世界 (`Worlds`) 与角色 (`Characters`) 两张核心资产表，字段经完整规划，与前端表单字段严格对应。
* **AI 调用架构确立**: 正式确定采用后端 Proxy 模式，新增 `/api/chat` 路由，支持流式输出转发。
* **注册流程完善**: 前端新增独立注册页面，支持邀请码注册流程。

### [V13.6.1] Security Hardening & Productivity Boost
* **核心重构与安全修复**: 彻底修复了因前端状态残留和后端硬编码 ID 导致的多租户配置覆盖灾难（IDOR 越权漏洞），引入动态 ID 生成与后端归属权校验。
* **引擎库生产力升级**: 数据库 SystemPrompts 表新增 `sort_index` 字段，前端引入 Sortable.js 实现拖拽排序与云端持久化；新增 .txt 文件一键导入为预设引擎功能。
* **健壮性优化**: 修复 Token 统计失效、CoT 文案退化、流式输出切换失效及 API 节点选中状态刷新重置等多个交互级 Bug。

### [V13.6.0] Multi-User Isolation & Auth (多用户隔离与鉴权)
* **安全升级**: 引入 JWT 身份鉴权机制，新增基于邀请码的闭门注册流程。
* **底层重构**: 数据库全量增加 `user_id` 外键与严格查询过滤，实现私人会话、API 节点与个人预设的绝对数据隔离。
* **依赖重构**: 移除已停更的 passlib，全量改用原生 bcrypt 进行密码哈希与校验。

### [V13.5.1] UI Refactoring & Logic Decoupling (前端解耦与UI重构)
* **种子数据独立化**: 新增 `default_prompts.js` 和 `random_libs.js`（5 大主题联动词库）。
* **无限世界表单重构**: 为 `rpgForm` 每个输入项增加独立状态锁 (`rpgLocks`)；引入"内容随机库"双轨联动机制。

### [V13.5] Backend Migration (重大重构)
* **重构**: 引入 Python FastAPI 后端，接管静态文件。
* **重构**: 引入 SQLite 数据库，彻底移除浏览器 `localStorage` 依赖。
* **新增**: RESTful API 体系 (`/api/sessions`, `/api/prompts`, `/api/profiles`)。
