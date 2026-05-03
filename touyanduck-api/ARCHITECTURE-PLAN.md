# 🦆 投研鸭公网端点架构升级方案

> 版本: v1.2 | 日期: 2026-04-08 | 状态: ✅ 阶段1+阶段2已实施（GitHub Pages 历史归档 + 自定义域名 api.touyanduck.com）

---

## 一、当前架构现状

### 1.1 数据流全景

```
数据生产层（touyanduck-daily Skill v7.5）
  │
  │ 产出 4 个 JSON（briefing/markets/watchlist/radar）
  ▼
miniapp_sync/                    ← 数据暂存区（~86KB）
  │
  ├──→ 微信云数据库              ← 小程序端（upload_to_cloud.py）
  │
  ├──→ api/latest/               ← 本地最新版本（sync_to_edgeone.sh 渲染+复制）
  │     │
  │     └──→ github-pages/       ← GitHub Pages 同步暂存区
  │           │
  │           └──→ git push      ← GitHub Pages 公网发布
  │                 │
  │                 └──→ https://api.touyanduck.com/
  │                       │
  │                       └──→ ClawHub Skill（大老板的 OpenClaw curl 读取）
  │
  └──→ briefing-*.mp3            ← 语音简报（上传微信云存储）
```

### 1.2 公网端点文件（GitHub Pages）

| 文件 | 大小 | 用途 |
|------|------|------|
| `briefing.md` | ~14KB | **AI 主入口** — OpenClaw curl 这个文件 |
| `briefing.json` | ~12KB | 核心简报 JSON（按需深挖） |
| `markets.json` | ~9KB | 市场详情 JSON |
| `watchlist.json` | ~38KB | 标的分析 JSON |
| `radar.json` | ~8KB | 风险雷达 JSON |
| `meta.json` | ~1KB | 元数据 |
| **合计** | **~82KB** | 每日覆盖写 |

### 1.3 核心问题

| 问题 | 影响 |
|------|------|
| **只有"今天"的快照** | 昨天的数据被覆盖，AI 无法纵向对比 |
| **无历史归档** | 大老板问"上周情况"，AI 答不上来 |
| **无知识库** | 聪明钱/机构历史信息无法积累 |
| **github-pages/ 不是独立 Git 仓库** | 需要确认发布流程（可能通过外部 `ZewuJiang/touyanduck-api` 仓库推送） |

---

## 二、推荐方案：GitHub Pages 静态扩展（近期实施）

### 2.1 目标目录结构

```
github-pages/（→ 发布到 GitHub Pages）
│
├── briefing.md                    ← 最新简报（AI 默认读这个，不变）
├── briefing.json                  ← 最新 JSON（不变）
├── markets.json                   ← 不变
├── watchlist.json                 ← 不变
├── radar.json                     ← 不变
├── meta.json                      ← 不变
│
├── archive/                       ← 【新增】历史归档
│   ├── index.json                 ← 日期索引（AI 查"有哪些历史数据"用）
│   ├── 2026-04-07/
│   │   ├── briefing.md            ← 当天完整简报
│   │   └── summary.json           ← 当天摘要（精简版，~2KB）
│   ├── 2026-04-08/
│   │   ├── briefing.md
│   │   └── summary.json
│   └── ...
│
└── knowledge/                     ← 【新增】知识库（未来扩展）
    ├── index.json                 ← 知识库索引
    └── smart-money/               ← 聪明钱档案
        ├── berkshire.md           ← 伯克希尔历史持仓+变动
        ├── bridgewater.md         ← 桥水历史动态
        ├── ark-invest.md          ← ARK 历史操作
        └── duan-yongping.md       ← 段永平持仓追踪
```

### 2.2 关键设计决策

#### 决策1：归档粒度 — 每日一份 `briefing.md` + 精简 `summary.json`

**为什么不归档全部 5 个 JSON？**

| 方案 | 每日增量 | 30天累积 | 1年累积 | 仓库1GB上限 |
|------|---------|---------|--------|------------|
| 全量归档（5 JSON + MD） | ~82KB | ~2.5MB | ~21MB | 可撑 ~12年 |
| **精简归档（MD + summary.json）** | **~16KB** | **~480KB** | **~4MB** | **可撑 ~60年** |
| 仅 briefing.md | ~14KB | ~420KB | ~3.6MB | 可撑 ~70年 |

**推荐精简归档**。原因：
- `briefing.md` 已包含所有分析结论，AI 读 MD 就够用了
- `summary.json` 只存关键指标（情绪分/风险分/核心事件标题/涨跌幅），用于 AI 做跨天趋势对比
- 空间极省，完全不用担心 GitHub Pages 1GB 仓库限制
- 大老板的 AI 问"上周市场情绪变化"→ curl index.json 获取日期列表 → curl 各天 summary.json → 汇总趋势

#### 决策2：`summary.json` 结构设计

```json
{
  "date": "2026-04-08",
  "updatedAt": "2026-04-08T06:15:07+08:00",
  "sentiment": {
    "score": 38,
    "label": "恐慌偏多"
  },
  "risk": {
    "score": 72,
    "level": "高"
  },
  "trafficLights": {
    "red": 2,
    "yellow": 3,
    "green": 2
  },
  "coreEvent": "特朗普关税最后通牒倒计时",
  "usMarkets": {
    "sp500": { "price": 5062.25, "change": -0.23 },
    "nasdaq": { "price": 15587.79, "change": -0.35 },
    "vix": { "price": 25.78, "change": 6.24 }
  },
  "topMovers": [
    { "name": "AVGO", "change": 3.14, "reason": "与Google/Anthropic签署AI芯片扩大协议" },
    { "name": "AAPL", "change": -2.07, "reason": "折叠屏受挫" }
  ],
  "smartMoneySummary": "桥水增持黄金ETF，伯克希尔未有新动作，ARK买入PLTR",
  "actionSummary": "防御为主，等待VIX回落",
  "briefingUrl": "archive/2026-04-08/briefing.md"
}
```

**特点**：
- 控制在 ~2KB 以内
- AI 读 index.json + 多天 summary.json 就能做趋势分析，不需要下载完整 briefing
- 完整 briefing.md 仍然可按需 curl

#### 决策3：`archive/index.json` 结构

```json
{
  "latest": "2026-04-08",
  "count": 15,
  "dates": [
    "2026-04-08",
    "2026-04-07",
    "2026-04-04",
    "2026-04-03"
  ],
  "updatedAt": "2026-04-08T06:15:07+08:00"
}
```

简单的日期数组，AI 一 curl 就知道有哪些历史数据。

#### 决策4：knowledge/ 知识库暂不急

- 当前 `radar.json` 中的 `smartMoneyDetail` 和 `smartMoneyHoldings` 每天都有聪明钱数据
- 通过历史归档，AI 就能回溯"桥水上个月在做什么"
- 独立的 knowledge/ 知识库（机构深度档案）作为**阶段2**按需建设
- 现阶段优先做好历史归档

### 2.3 SKILL.md 升级设计

ClawHub Skill 需要告诉 AI 新增了哪些端点：

```markdown
## 使用方式

### 获取最新简报（默认）
curl -s "https://api.touyanduck.com/briefing.md"

### 查看历史归档索引
curl -s "https://api.touyanduck.com/archive/index.json"

### 获取某天的摘要（用于跨天对比）
curl -s "https://api.touyanduck.com/archive/2026-04-07/summary.json"

### 获取某天的完整简报
curl -s "https://api.touyanduck.com/archive/2026-04-07/briefing.md"
```

**AI 使用策略**（写入 SKILL.md 指引 AI 行为）：

| 用户问题 | AI 动作 |
|---------|---------|
| "今天市场怎么样" | curl `briefing.md`（默认行为，不变） |
| "这周市场情绪变化" | curl `archive/index.json` → 获取本周日期 → curl 各天 `summary.json` → 比较 sentimentScore 趋势 |
| "上周五聪明钱在干嘛" | curl `archive/index.json` → 找到上周五日期 → curl `archive/{date}/briefing.md` → 提取聪明钱段落 |
| "VIX 最近一周走势" | curl 最近5天 `summary.json` → 提取 VIX 数据 → 画趋势 |

### 2.4 需要改动的文件清单

| 文件 | 改动内容 | 优先级 |
|------|---------|--------|
| `scripts/sync_to_edgeone.sh` | 新增归档逻辑：每次同步时自动生成 `archive/{date}/` | P0 |
| 新增 `scripts/generate_summary.py` | 从 4 个 JSON 提取关键指标生成 `summary.json` | P0 |
| `scripts/sync_to_edgeone.sh` | 同步时自动更新 `archive/index.json` | P0 |
| `touyanduck-briefing/SKILL.md` | 新增历史查询端点说明 + AI 使用策略 | P1 |
| `INSTALL-GUIDE.md` | 更新技术架构图 | P2 |
| `index.html` | 新增历史归档端点展示 | P2 |

### 2.5 实施步骤

```
步骤1：创建 generate_summary.py
        从 4 个 JSON 提取关键指标 → 输出 summary.json（~2KB）

步骤2：改造 sync_to_edgeone.sh v3.0 → v4.0
        在现有"复制到 api/latest/"之后，新增：
        ① mkdir -p archive/{date}/
        ② cp briefing.md → archive/{date}/briefing.md
        ③ 运行 generate_summary.py → archive/{date}/summary.json
        ④ 更新 archive/index.json（追加今天的日期）

步骤3：更新 ClawHub SKILL.md v1.0.2 → v1.1.0
        新增历史查询端点 + AI 使用策略

步骤4：补录历史数据（可选）
        如果之前的 JSON 还保存在 miniapp_sync/，可回溯生成
```

---

## 三、未来演进路线（文档记录，暂不实施）

### 阶段2：自定义域名绑定 ✅ 已完成（2026-04-08）

| 项目 | 内容 |
|------|------|
| 操作 | `api.touyanduck.com` CNAME 到 `zewujiang.github.io`，GitHub Pages Custom Domain + Enforce HTTPS |
| 工作量 | DNS 配置 30 分钟 + SKILL.md URL 替换 |
| 需要备案 | **不需要**（GitHub Pages 服务器在海外） |
| 好处 | ① 更专业的 URL ② ClawHub 安全评分可能提升 ③ 以后换托管平台不需要改 SKILL.md |
| 版本影响 | ClawHub Skill v1.2.0（大老板需重装一次） |

### 阶段3：Cloudflare Workers 动态 API（数据量大了之后）

**触发条件**：当以下任一条件满足时考虑迁移：
- GitHub Pages 仓库超过 500MB
- 大老板频繁需要"最近30天聪明钱趋势汇总"等聚合查询
- 需要参数化查询（`?since=2026-03-01&fund=bridgewater`）

**架构预览**：
```
Cloudflare Pages（静态文件）     Cloudflare Workers（动态 API）
├── briefing.md                  ├── /api/briefing
├── archive/...                  ├── /api/archive?date=...
└── knowledge/...                ├── /api/smart-money?fund=...&since=...
                                 ├── /api/search?q=NVDA
                                 └── /api/trend?metric=sentiment&days=30

数据存储：Cloudflare D1（SQLite）/ KV
```

**优缺点**：
| 维度 | 优点 | 缺点 |
|------|------|------|
| 功能 | 参数化查询、聚合分析、全文搜索 | 需要维护 Workers 代码 |
| 成本 | 免费额度 10万次/天 | Cloudflare 账号 |
| 性能 | 全球 CDN + Edge 计算 | D1 SQLite 有容量限制 |
| 迁移 | 自定义域名无缝切换 | 数据同步逻辑需改写 |

**对标**：Iran Briefing Skill（`skill.capduck.com`）就是这种架构，有 7 个参数化端点。

### 阶段4：knowledge/ 知识库建设（按需）

**潜在内容**：
| 知识库 | 内容 | 数据来源 |
|--------|------|---------|
| `smart-money/berkshire.md` | 伯克希尔历史持仓、13F 变动记录 | SEC EDGAR 13F |
| `smart-money/bridgewater.md` | 桥水历史操作、宏观策略转向 | SEC 13F + 新闻 |
| `smart-money/ark-invest.md` | ARK 每日买卖记录 | ARK 官方日报 |
| `smart-money/duan-yongping.md` | 段永平持仓追踪 | 雪球 + SEC 13F |
| `sectors/ai-chips.md` | AI 算力链历史分析 | 累积每日简报 |
| `events/tariff-timeline.md` | 关税事件时间线 | 累积核心事件链 |

**建设方式**：每次 touyanduck-daily 产出时，自动追加当天的聪明钱数据到对应机构的 .md 文件。

---

## 四、方案对比总览

| 维度 | 阶段1（推荐，现在做） | 阶段2 | 阶段3 | 阶段4 |
|------|----------------------|-------|-------|-------|
| **核心改动** | 历史归档 + summary.json | 绑定域名 | 迁移 Cloudflare | 知识库 |
| **工作量** | 2-3 小时 | 30 分钟 | 1-2 天 | 持续积累 |
| **成本** | 零 | 零（域名已有） | 零（免费额度） | 零 |
| **大老板体验** | 可问历史+趋势 | URL 更专业 | 参数化查询 | 深度研究 |
| **需要重装 Skill** | 是（v1.1.0） | 是（v1.2.0） | 是 | 否 |
| **风险** | 极低 | 极低 | 中（需学 Workers） | 低 |

---

## 五、关于 GitHub Pages 发布仓库

**发现的问题**：本地 `github-pages/` 目录没有 `.git`，说明它不是独立 Git 仓库。

**需要确认**：`github.com/ZewuJiang/touyanduck-api` 这个外部仓库是如何与本地 `github-pages/` 同步的？

**可能的情况**：
1. 手动 cd 到外部仓库目录，复制文件后 git push
2. 通过 SKILL.md 4.3 阶段描述的 cd + git push 流程

**建议**：在实施阶段1之前，先确认发布流程，确保归档文件能正确推送到 GitHub Pages。

---

⚠️ 本文档为架构规划文档，实施前需确认发布流程。
