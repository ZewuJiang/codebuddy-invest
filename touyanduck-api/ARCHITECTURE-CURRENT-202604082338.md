# 🦆 投研鸭项目架构全景（当前真实状态）

> 版本: v1.0 | 日期: 2026-04-08 23:38 | 状态: 调试优化阶段，尚未进入完全生产环境

---

## 一、项目定位

投研鸭是一个**二级市场每日策略简报系统**，为特定用户（大老板）提供每日全球市场洞察。

当前由 **三个独立子系统** 构成，各自独立触发、独立运行、互不耦合：

| 子系统 | 定位 | 消费者 | 运行状态 |
|--------|------|--------|----------|
| **App Skill** (`touyanduck-daily`) | 数据生产引擎 | 微信小程序 + 公开 API | 手动触发，调试中 |
| **微信小程序** (`touyanduck_appid`) | 终端展示层 | 大老板（手机端） | 开发者工具预览，未提审 |
| **公开 API** (`touyanduck-api/github-pages`) | 数据分发层 | ClawHub Skill / 公网 | 已上线，稳定运行 |

> **重要说明**：`investment-agent-daily`（MD/PDF 人读报告）是另一个独立 Skill，与本项目无关联、不联动、不共享流程。两者数据同源但各自独立执行。`touyanduck-daily` 是小程序数据生产的唯一入口。

---

## 二、数据流全景（当前实际运行链路）

```
┌─────────────────────────────────────────────────────────────┐
│                    数据生产（App Skill v10.0）                │
│                                                             │
│  AI 实时搜索采集（Google Finance / AkShare / SEC / 新闻等）   │
│         ↓                                                   │
│  结构化 JSON 生成（AI 填写原始值，对照 Schema）                │
│         ↓                                                   │
│  auto_compute.py v2.0（12类公式字段自动计算）                 │
│         ↓                                                   │
│  validate.py v5.1（49项 FATAL/WARN 校验）                    │
│         ↓                                                   │
│  refresh_verified_snapshot.py（sparkline/chartData 补全）     │
│         ↓                                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  miniapp_sync/（4个 JSON 暂存区，~86KB 合计）        │    │
│  │  briefing.json / markets.json / watchlist.json       │    │
│  │  / radar.json                                        │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
    ┌──────────────┐ ┌───────────┐ ┌──────────────┐
    │ upload_to_   │ │ sync_to_  │ │ generate_    │
    │ cloud.py     │ │ edgeone.sh│ │ audio.py     │
    │              │ │           │ │              │
    │ 微信云数据库  │ │ GitHub    │ │ TTS 语音     │
    │ 4个集合      │ │ Pages     │ │ MiniMax API  │
    └──────┬───────┘ └─────┬─────┘ └──────┬───────┘
           ↓               ↓              ↓
    ┌──────────────┐ ┌───────────┐ ┌──────────────┐
    │  微信小程序   │ │ api.      │ │ 微信云存储    │
    │  4 Tab 页面  │ │ touyanduck│ │ .mp3 文件    │
    │              │ │ .com      │ │              │
    └──────────────┘ └─────┬─────┘ └──────────────┘
                           ↓
                    ┌──────────────┐
                    │ ClawHub Skill│
                    │ 大老板的 AI   │
                    │ 助手可 curl   │
                    └──────────────┘
```

**关键说明**：
- 三路分发完全独立，任一路失败不影响其他路
- EdgeOne Pages（`public/` + KV）已**关闭**（`EDGEONE_ENABLED=0`），等域名备案
- 语音播报为可选步骤（第3.5阶段），非核心链路

---

## 三、子系统 A — App Skill 数据生产引擎

**位置**：`.codebuddy/skills/touyanduck-daily/`
**版本**：v10.0（2026-04-08）
**触发方式**：手动对话触发（关键词：投资App / 小程序数据 / 投研鸭数据 / app数据更新）

### 3.1 执行流水线（7阶段）

| 阶段 | 名称 | 执行者 | 核心产出 | 耗时估算 |
|------|------|--------|----------|----------|
| **第0阶段** | 日期检测 + 模式路由 | AI | Standard（工作日）/ Weekend（周末） | 10秒 |
| **第1阶段** | 实时数据采集 | AI 搜索 | 46+次 web_search/web_fetch | 8-12分钟 |
| **第1.5阶段** | 数据完整性门禁 | AI 自检 | 三大指数+M7+VIX / GICS 11 / 亚太 / 大宗 / watchlist | 30秒 |
| **第2阶段** | JSON 生成 | AI 写入 | 4个 JSON 文件 → miniapp_sync/ | 5-8分钟 |
| **第3阶段** | 一键执行 | `run_daily.sh` | 校验→计算→补全→上传→同步 | 2-3分钟 |
| **第3.5阶段** | 语音播报（可选） | AI + TTS | 播报文稿 → MiniMax TTS → .mp3 | 2-3分钟 |
| **第4-5阶段** | 交付确认 + 复盘 | AI | 搜索日志 + 质量 diff + 堵点记录 | 1分钟 |

**总耗时**：约 20-25 分钟（Standard 全量模式）

### 3.2 `run_daily.sh` 一键执行链路

```bash
bash run_daily.sh 2026-04-08 [--skip-warn]
```

```
第0步   JSON 语法校验（4个文件）              → 失败则中断
  ↓
第0.3步 auto_compute.py v2.0（12类公式）      → 失败则警告但继续
  ↓
第0.5步 validate.py v5.1（49项校验）          → FATAL 中断 / WARN 可 --skip-warn
  ↓
第1步   sparkline 补全（AkShare 真实数据）     → 失败则跳过（AI 估算值兜底）
  ↓
第2步   upload_to_cloud.py                    → 上传微信云数据库（硬依赖）
  ↓
第3步   sync_to_edgeone.sh v5.0              → GitHub Pages 同步（软依赖）
         ├── 0.5步 render_briefing.py（JSON→Markdown）
         ├── 1步   复制到 api/latest/
         ├── 2步   生成 meta.json
         ├── 3步   EdgeOne public/ ← 已跳过（EDGEONE_ENABLED=0）
         ├── 3.5步 同步到 github-pages/（最新覆盖）
         ├── 3.7步 归档 archive/{date}/（summary.json + index.json）
         ├── 4步   EdgeOne KV ← 已跳过（EDGEONE_ENABLED=0）
         └── 5步   git push github-pages/ → GitHub Pages
```

### 3.3 工具链（14个脚本）

| 脚本 | 版本 | 功能 | 依赖级别 |
|------|------|------|----------|
| `run_daily.sh` | v6.0 | 一键串联主控 | 入口 |
| `auto_compute.py` | v2.0 | 12类公式字段自动计算 | 硬依赖 |
| `validate.py` | v5.1 | 49项 FATAL/WARN 校验 | 硬依赖 |
| `refresh_verified_snapshot.py` | v3.0 | sparkline/chartData 7天+30天补全 | 软依赖 |
| `upload_to_cloud.py` | v1.1 | 上传微信云数据库 + 回读校验 | 硬依赖 |
| `sync_to_edgeone.sh` | v5.0 | 公开 API 同步（GitHub Pages 为主） | 软依赖 |
| `render_briefing.py` | — | JSON → Markdown 渲染 | 被 sync 调用 |
| `generate_summary.py` | v1.0 | 生成精简归档 summary.json | 被 sync 调用 |
| `generate_meta.py` | — | 生成 meta.json | 被 sync 调用 |
| `generate_audio.py` | — | TTS 语音生成 + 上传 | 第3.5阶段可选 |
| `checklist_generator.py` | v1.0 | 执行前自动清单 | 可选 |
| `post_flight.py` | v1.0 | 执行后自动报告 | 可选 |
| `sync_to_edgeone_kv.py` | — | EdgeOne KV 推送 | **已停用** |

### 3.4 参考规范文件（15个）

| 文件 | 核心用途 |
|------|----------|
| `json-schema.md` (60KB) | 4个 JSON 完整 Schema + 门禁规则 |
| `schema-compact.json` (7KB) | AI 执行阶段紧凑参照 |
| `formulas.md` | 所有公式唯一权威源 |
| `golden-baseline.json` | validate.py 参数源 |
| `data-collection-sop.md` (24KB) | 采集批次 SOP |
| `stock-universe.md` | 5板块标的池 |
| `fund-universe.md` (29KB) | 三梯队26家基金 |
| `media-watchlist.md` | 三级媒体清单 |
| `ai-supply-chain-universe.md` | AI产业链24环 |
| `data-source-priority.md` | 数据源优先级 + 降级策略 |
| `known-pitfalls.md` | 50条已知堵点（活跃） |
| `weekend-mode.md` | Weekend 模式规范 |
| `holdings-cache.json` | 持仓缓存（3家×Top10，13F 来源） |
| `briefing-golden-sample.json` | 黄金样本 |
| `templates.md` | 交付模板集合 |

### 3.5 质量保障体系

```
第1层：九大铁律（RULE ZERO ~ RULE EIGHT）
  → 所有数字必须来自实时搜索，禁止凭记忆
  → 聪明钱持仓以 SEC 13F 为唯一数据源

第2层：29条致命错误清单 + 50条活跃堵点

第3层：validate.py v5.1 自动化校验
  → 49项检测，FATAL 不可绕过 / WARN 可 --skip-warn
  → V39 聪明钱13F合规性 [FATAL]
  → V36 跨JSON交叉验证 / V37 数值合理性 / V38 趋势方向一致性

第4层：回归门禁 R1-R9（含3项 FATAL）

第5层：golden-baseline.json + briefing-golden-sample
```

### 3.6 产出物 — 4个 JSON

| 文件 | 大小 | 驱动页面 | 核心内容 |
|------|------|----------|----------|
| `briefing.json` | ~12KB | 简报 | takeaway / coreEvent / coreJudgments / actionHints / sentimentScore / smartMoney / topHoldings / voiceText |
| `markets.json` | ~9KB | 市场 | usMarkets / m7 / asia / commodities / crypto / gics(11板块) / sparkline(7天) |
| `watchlist.json` | ~38KB | 标的 | 5板块 × 5-7标的 / price / change / metrics(6项) / analysis / chartData(30天) |
| `radar.json` | ~8KB | 雷达 | trafficLights(7项) / riskScore / smartMoneyDetail / smartMoneyHoldings / events / predictions / anomalies |

---

## 四、子系统 B — 微信小程序

**位置**：`touyanduck_appid/`
**版本**：v5.0
**状态**：开发者工具预览中，**未提交微信审核**

### 4.1 页面架构（4 Tab + 1 WebView）

| Tab | 页面文件 | 数据源 | 核心功能 |
|-----|----------|--------|----------|
| 简报 | `pages/briefing/` | briefing.json | 核心结论 / 事件链 / 全球资产反应 / 核心判断 / 行动建议 / 情绪仪表盘 / 聪明钱速览 / 语音播报 |
| 市场 | `pages/markets/` | markets.json | 5子Tab(美股/M7/亚太/大宗/加密) / sparkline趋势图 / GICS热力图 |
| 标的 | `pages/watchlist/` | watchlist.json | 5板块分组 / 标的卡片(价格+6维metrics) / 30天走势图 |
| 雷达 | `pages/radar/` | radar.json | 7项红绿灯 / 风险评分 / 聪明钱详情 / 事件日历 / 预测市场 / 异动信号 |
| — | `pages/webview/` | URL参数 | 内嵌浏览器（打开来源链接） |

### 4.2 技术栈

| 层级 | 选型 |
|------|------|
| 框架 | 微信小程序原生（ES5 语法） |
| 数据层 | `services/api.js` v7.0 — 统一数据服务 |
| 存储 | 微信云数据库（4个集合）+ 本地缓存（30分钟有效期） |
| 组件 | 5个：mini-chart / section-card / skeleton / stock-card / traffic-light |
| 工具库 | animate.js / color.js / format.js / storage.js |
| 云环境 | `cloud1-3g6wj06h84f38ea8` |

### 4.3 数据流（小程序内部）

```
用户打开 → app.js 初始化云开发
  → 各页面 onLoad → api.fetchData(collection, cacheKey)
     → ① 读本地缓存（秒开）→ 渲染
     → ② 后台查云数据库（按 date 匹配，fallback 取最新）
     → ③ 成功 → 更新缓存 + 重渲染
     → ④ 失败 → 保持缓存数据（严禁 Mock 降级）
```

### 4.4 当前已知问题

- 未提交微信审核（大老板只能通过开发者工具或体验版使用）
- 前端UI还有待打磨优化的地方
- 部分页面加载体验可进一步优化

---

## 五、子系统 C — 公开 API（GitHub Pages）

**位置**：`touyanduck-api/github-pages/`（独立 git 仓库，推送到 `ZewuJiang/touyanduck-api`）
**域名**：`https://api.touyanduck.com`（CNAME → `zewujiang.github.io`）
**状态**：已上线，稳定运行

### 5.1 端点清单（均为 HTTPS GET，纯静态文件）

| 端点 | 大小 | 用途 |
|------|------|------|
| `/briefing.md` | ~14KB | AI 主入口（ClawHub Skill 默认 curl 这个） |
| `/briefing.json` | ~6KB | 简报 JSON |
| `/markets.json` | ~7KB | 市场详情 |
| `/watchlist.json` | ~72KB | 标的分析 |
| `/radar.json` | ~10KB | 风险雷达 |
| `/meta.json` | ~1KB | 元数据 |
| `/archive/index.json` | ~0.1KB | 历史日期索引 |
| `/archive/{date}/summary.json` | ~2KB | 某天精简摘要 |
| `/archive/{date}/briefing.md` | ~14KB | 某天完整简报 |

### 5.2 历史归档

- 当前已有 **2天** 数据（2026-04-07、2026-04-08）
- 每天增量 ~16KB（briefing.md + summary.json）
- 空间可撑 ~60年（远低于 GitHub Pages 1GB 上限）
- 归档由 `sync_to_edgeone.sh` 第3.7步自动完成

### 5.3 ClawHub Skill

**文件**：`touyanduck-api/touyanduck-briefing/SKILL.md` v1.2.0
**平台**：[clawhub.ai/zewujiang/touyanduck-briefing](https://clawhub.ai/zewujiang/touyanduck-briefing)
**功能**：大老板的 AI 助手说"今天市场怎么样" → curl briefing.md → 解读回答

---

## 六、已暂停 / 待启用的组件

| 组件 | 位置 | 状态 | 恢复条件 |
|------|------|------|----------|
| **EdgeOne Pages 静态文件** | `touyanduck-api/public/` | 已停用 | 域名备案完成 → `EDGEONE_ENABLED=1` |
| **EdgeOne KV 动态 API** | `touyanduck-api/edge-functions/api/` (8个) | 已停用 | 同上 |
| **EdgeOne KV 同步脚本** | `scripts/sync_to_edgeone_kv.py` | 已停用 | 同上 |
| **knowledge/ 知识库** | 规划中 | 未建设 | 有需求时启动 |

> EdgeOne 全部代码已就绪（8个 Edge Functions + KV fallback），备案完成后改一行开关即可启用。
> GitHub Pages 当前完全能满足需求，无需急于切换。

---

## 七、目录结构总览

```
codebuddy-invest/
│
├── .codebuddy/skills/touyanduck-daily/   ← App Skill 数据生产引擎
│   ├── SKILL.md                    ← 主控文档 v10.0（~276行）
│   ├── README.md                   ← 快速入门
│   ├── CHANGELOG.md                ← 完整版本历史
│   ├── scripts/                    ← 14个工具脚本
│   │   ├── run_daily.sh            ← 一键执行入口
│   │   ├── auto_compute.py         ← 公式自动计算
│   │   ├── validate.py             ← 自动化校验（69KB）
│   │   ├── upload_to_cloud.py      ← 微信云上传
│   │   ├── sync_to_edgeone.sh      ← 公开API同步（含 EDGEONE_ENABLED 开关）
│   │   ├── refresh_verified_snapshot.py  ← sparkline 补全
│   │   ├── render_briefing.py      ← JSON→MD 渲染
│   │   ├── generate_summary.py     ← 归档摘要生成
│   │   ├── generate_meta.py        ← 元数据生成
│   │   ├── generate_audio.py       ← TTS 语音
│   │   ├── checklist_generator.py  ← 执行前清单
│   │   ├── post_flight.py          ← 执行后报告
│   │   └── sync_to_edgeone_kv.py   ← EdgeOne KV（已停用）
│   └── references/                 ← 15个规范文件
│       ├── json-schema.md          ← 完整 Schema（60KB）
│       ├── data-collection-sop.md  ← 采集 SOP（24KB）
│       ├── known-pitfalls.md       ← 已知堵点
│       └── ...（12个其他规范文件）
│
├── touyanduck_appid/               ← 微信小程序
│   ├── app.js / app.json           ← 入口 + 配置
│   ├── pages/                      ← 5个页面（每页4文件）
│   │   ├── briefing/               ← 简报页
│   │   ├── markets/                ← 市场页
│   │   ├── watchlist/              ← 标的页
│   │   ├── radar/                  ← 雷达页
│   │   └── webview/                ← 内嵌浏览器
│   ├── components/                 ← 5个自定义组件
│   ├── services/api.js             ← 统一数据服务层 v7.0
│   └── utils/                      ← 4个工具库
│
├── touyanduck-api/                 ← 公开 API
│   ├── github-pages/               ← GitHub Pages（独立 git 仓库）
│   │   ├── CNAME                   ← api.touyanduck.com
│   │   ├── briefing.md / *.json    ← 最新数据
│   │   └── archive/                ← 历史归档（2天）
│   ├── touyanduck-briefing/        ← ClawHub Skill 源文件
│   │   └── SKILL.md                ← v1.2.0
│   ├── edge-functions/             ← EdgeOne（已停用，代码保留）
│   ├── public/                     ← EdgeOne 静态（已停用）
│   ├── ARCHITECTURE-PLAN.md        ← 架构演进规划 v1.2
│   └── DEPLOY-GUIDE.md             ← 部署指南
│
└── workflows/investment_agent_data/
    └── miniapp_sync/               ← 数据暂存区（4个 JSON + 语音）
        ├── briefing.json
        ├── markets.json
        ├── watchlist.json
        └── radar.json
```

---

## 八、当前运行模式（手动调试阶段）

```
人工对话触发 App Skill
  → AI 执行全流程（~20-25分钟）
  → run_daily.sh 一键校验+上传+同步
  → 微信开发者工具刷新验证
  → 发现问题 → 手动修复 → 重跑上传
```

**特点**：
- 每次都是完整的 Standard 模式全量执行
- 需要人工介入确认数据质量
- 发现问题后迭代修复 Skill 规范（known-pitfalls / validate.py / auto_compute.py）
- 属于 **"边跑边调"** 的工程优化阶段

---

## 九、版本演进关键里程碑

| 日期 | 版本 | 里程碑 |
|------|------|--------|
| ~4/5 | v1.0~v5.x | 基础架构：4JSON+4页面+语音播报+黄金样本 |
| 4/7 | v7.0~v7.5 | 公开API+GitHub Pages+回归门禁R1-R8 |
| 4/8 AM | v8.0~v8.2 | Harness Engineering：validate.py + FATAL/WARN 双级 |
| 4/8 PM | v9.0 | 架构重构：四档→二档引擎，新增 auto_compute.py |
| 4/8 PM | v10.0 | 工具链全面升级：AI只做搜索+写分析，其余全自动 |
| 4/8 晚 | — | 自定义域名 api.touyanduck.com + ClawHub Skill v1.2.0 |
| 4/8 晚 | — | 聪明钱13F铁律 + V39 FATAL + EdgeOne 开关化 |

> 注：v7.0 → v10.0 全部发生在 4/7~4/8 两天内，迭代密度极高。

---

## 十、待优化和讨论事项

以下是当前阶段可以讨论的方向（非优先级排序，仅列出）：

### 数据生产层
- 每次全量 Standard 执行 ~25分钟，是否需要更轻量的增量刷新机制
- AkShare 10个已知缺口标的的 sparkline 需要 AI 手动预填，能否自动化
- validate.py 已 49 项，部分 WARN 是否需要升级/降级
- 连续零事故天数尚未开始计数（v10.0 刚上线）

### 小程序展示层
- UI/UX 打磨（加载体验、空状态、错误提示）
- 是否准备提交微信审核
- 前端对数据异常的容错处理

### 公开 API 层
- 历史归档仅 2 天，需要持续积累
- EdgeOne 备案完成后的启用计划
- knowledge/ 知识库是否有近期需求

### 运维自动化
- 目前纯手动触发，是否考虑定时任务
- launchd 方案之前因超时（900s < 25分钟）失败，已调整到 1800s 但未验证
- 错误告警机制（数据异常时通知）

---

*本文档反映 2026-04-08 23:38 的项目真实状态，不包含规划中但未实施的功能。*
