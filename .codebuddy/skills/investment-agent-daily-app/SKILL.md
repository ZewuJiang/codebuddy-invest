---
name: investment-agent-daily-app
description: 当用户提到「投资App」「小程序数据」「投研鸭数据」「app数据更新」「miniapp sync」或类似关键词时，自动执行投研鸭小程序数据生产全流程，输出4个原生结构化JSON并上传微信云数据库。
---

# 投研鸭小程序数据生产 — 标准工作流 v1.3.2

> **版本**: v1.3.2 (2026-04-02 00:21)
> **主控文档**：本文件为精炼主控，详细规则/知识库/模板/SOP通过引用按需加载。

---

## 定位与使命

> **读者**: 投研鸭微信小程序（机器消费）
> **产出物**: 4个原生结构化 JSON 文件（briefing / markets / watchlist / radar）
> **核心宗旨**: 为小程序提供 100% 完整、精确、结构化的数据，让每个组件都能"满血渲染"
> **与 `investment-agent-daily` 的关系**: 完全独立的数据采集 + 完全不同的产出格式。`daily` 输出给人读的 MD/PDF，本 Skill 输出给机器读的 JSON。

---

## 核心差异（vs investment-agent-daily）

| 维度 | `investment-agent-daily` | **本 Skill (`daily-app`)** |
|------|--------------------------|------------------------------|
| **产出物** | MD + PDF 文件 | **4 个 JSON 文件** |
| **读者** | 大老板（人读） | **小程序（机器读）** |
| **格式要求** | GS/MBB 投行风格 markdown | **精确 JSON Schema，枚举值受控** |
| **额外数据** | 无 | **sparkline(7天)、chartData(30天)、metrics(6项)、analysis、板块summary** |
| **终审** | 三轮终审（数据/逻辑/格式） | **JSON Schema 校验 + 空值扫描 + 枚举值校验** |
| **上传** | 无（输出文件即可） | **upload_to_cloud.py 推送云数据库** |

---

## 六大铁律（最高优先级）

| 铁律 | 核心要求 |
|------|---------|
| **RULE ZERO** | 训练数据全面禁用。所有数据只能来自当期实时搜索。自查三问：①来自搜索？②时间戳≤24h？③可追溯？任一为否→重写 |
| **RULE ONE** | JSON 完整性铁律。4个JSON中每个必填字段都必须有精确值，严禁空字符串/空数组/`null`/`"--"`/`"N/A"` |
| **RULE TWO** | 数据类型严格。`change` 必须是 `number` 类型（不是 string），`sparkline` 必须是 7 个 number 的数组，枚举值必须在允许范围内 |
| **RULE THREE** | Schema 对齐铁律。每个 JSON 的结构必须 100% 对齐 `references/json-schema.md` 中的定义，不允许新增/缺失/改名字段 |
| **RULE FOUR** | sparkline 必填。markets/watchlist 中每个标的必须有 7 天历史走势数据（sparkline 数组），watchlist 额外需要 30 天 chartData |
| **RULE FIVE** | 板块均衡。watchlist 的 7 个板块每个至少 2 只标的，不允许出现空板块 |

---

## 触发条件与报告日历

**触发关键词**：投资App / 小程序数据 / 投研鸭数据 / app数据更新 / miniapp sync

| 日期 | 执行 | 模板引用 |
|------|------|---------|
| 周一 | 执行（含上周总结数据） | → [monday-special.json](templates/monday-special.json) |
| 周二～周五 | 执行 | → [daily-standard.json](templates/daily-standard.json) |
| 周六～周日 | **不执行** | — |

---

## 产出物定义

| 文件 | 对应小程序页面 | 数据来源 | Schema 定义 |
|------|--------------|---------|------------|
| `briefing.json` | 简报页 | §1核心结论 + §2摘要 + §4摘要 | → [json-schema.md §1](references/json-schema.md) |
| `markets.json` | 市场页 | §2全球市场 + GICS板块 | → [json-schema.md §2](references/json-schema.md) |
| `watchlist.json` | 标的页 | §3重点标的 + 行业分析 | → [json-schema.md §3](references/json-schema.md) |
| `radar.json` | 雷达页 | §5风险雷达 + §4基金详情 | → [json-schema.md §4](references/json-schema.md) |

---

## 工作流（6个阶段）

### 第零阶段：交易日检测 + 环境准备

```bash
date "+%A %Y-%m-%d %H:%M:%S"
```

- 周六～周日 → 不执行
- 周一 → 使用 monday-special.json 模板（含上周回顾数据）
- 周二～周五 → 使用 daily-standard.json 模板
- 确认输出目录存在：`workflows/investment_agent_data/miniapp_sync/`

### 第一阶段：实时数据采集（独立完整采集）

**详细的采集批次SOP、数据源优先级表** → [data-collection-sop.md](references/data-collection-sop.md)

**采集批次概要**：

| 批次 | 内容 | 知识库引用 |
|------|------|-----------|
| 0 | 全球财经媒体头条扫描（一级必扫7家） | → [media-watchlist.md](references/media-watchlist.md) |
| 0a | 深度媒体补充扫描（二级强化11家） | → [media-watchlist.md](references/media-watchlist.md) |
| 0b | AI产业链重大动态专项扫描 | → [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md) |
| 1a | **M7个股（Google Finance）+ 7天历史走势** | → [data-collection-sop.md](references/data-collection-sop.md) |
| 1b | **美股指数+VIX + 7天历史走势** | |
| 1c | **GICS 11板块ETF + 涨跌幅** | |
| 1d | **焦点个股 + 7天历史走势** | |
| 2 | 亚太/港股+北向资金 + 7天历史走势 | |
| 3 | 大宗商品/汇率/加密 + 7天历史走势 | |
| 4 | 基金&大资金动向（三梯队） | → [fund-universe.md](references/fund-universe.md) |
| **5** | **watchlist 标的详情采集**（metrics/analysis/risks） | → [stock-universe.md](references/stock-universe.md) |
| **6** | **本周关键事件日历 + 风险矩阵** | |

**⚠️ 与原 Skill 的关键差异**：
- 每个标的必须额外采集 **7 天历史价格**（用于 sparkline）
- watchlist 标的必须额外采集 **30 天历史价格**（用于 chartData）
- 每个 watchlist 标的必须采集 **6 项 metrics 指标**（PE/市值/营收增速/毛利率/ROE/评级）
- 每个 watchlist 标的必须生成 **analysis 分析文本**（2-3段）
- 每个 watchlist 标的必须生成 **2-3 条 risks**
- 每个 watchlist 标的必须生成 **2 个 tags**
- 每个板块必须生成 **summary 概述**（2-3句话）

### 第1.5阶段：数据完整性门禁（强制 — 比原 Skill 更严格）

> 不通过则禁止进入 JSON 生成阶段。

**必填数据清单**：

| # | 验证项 | 要求 | 缺失时操作 |
|---|--------|------|-----------|
| 1 | 三大指数 + M7 + VIX | 精确收盘价+涨跌幅+7天sparkline | 回到对应批次补采 |
| 2 | GICS 11板块ETF | 涨跌幅 | 回到批次1c补采 |
| 3 | 亚太4-6指数 | 精确值+sparkline | 回到批次2补采 |
| 4 | 大宗/汇率/加密6项 | 精确值+sparkline | 回到批次3补采 |
| 5 | **watchlist 7个板块×每板块≥2标的** | 价格+涨跌+tags+reason+analysis+metrics+risks | 回到批次5补采 |
| 6 | **radar 7项红绿灯** | 精确值+status | 回到批次3补采 |
| 7 | **coreEvent + coreJudgments×3 + actions** | 完整文本 | 补充分析 |
| 8 | **globalReaction 6项** | name+value+direction | 补充 |
| 9 | **smartMoney 2-4条** | source+action+signal | 补充 |
| 10 | **events 3-5条 + riskAlerts 2-3条** | 完整字段 | 补充 |

### 第二阶段：结构化 JSON 生成（核心阶段）

基于采集数据，严格按照 `references/json-schema.md` 的 Schema 定义生成 4 个 JSON 文件。

**生成规则**：
1. **先加载 Schema** — 必须重新读取 `json-schema.md`，逐字段对照生成
2. **枚举值受控** — direction 只能是 `up/down/flat`，signal 只能是 `bullish/bearish/neutral`，等等
3. **数据类型严格** — `change` 必须是 `number`（如 `1.42`），不是 string（如 `"+1.42%"`）
4. **纯文本** — 所有文本字段禁止包含 markdown 语法（`**加粗**`、`|表格|`、`- 列表`等）
5. **sparkline 生成** — 用采集到的 7 天历史价格填充，若某天缺失用线性插值

**输出路径**：
```
/Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows/investment_agent_data/miniapp_sync/
├── briefing.json
├── markets.json
├── watchlist.json
└── radar.json
```

### 第2.5阶段：JSON 完整性终审（强制）

> **此阶段为强制性门禁，不通过则禁止上传。**

**逐文件扫描**：

对 4 个 JSON 文件执行以下检查：

| # | 检查项 | 规则 |
|---|--------|------|
| 1 | **必填字段非空** | 所有 json-schema.md 中标记"必填"的字段不能是 `""`、`[]`、`null`、`"--"` |
| 2 | **枚举值校验** | `direction` ∈ {up, down, flat}，`signal` ∈ {bullish, bearish, neutral}，`trend` ∈ {up, down, hold}，`type` ∈ {buy, sell, hold, bullish, bearish}，`level` ∈ {high, medium, low}，`status` ∈ {green, yellow, red} |
| 3 | **数据类型校验** | `change` = number，`sentimentScore` = number，`riskScore` = number，`confidence` = number，`sparkline` = number[]，`chartData` = number[] |
| 4 | **数组长度校验** | `globalReaction` ≥ 5，`coreJudgments` = 3，`trafficLights` = 7，`sparkline` = 7，GICS = 11 |
| 5 | **板块均衡** | watchlist 每个板块至少 2 只标的 |
| 6 | **sparkline 有效性** | 每个 sparkline 数组必须是 7 个正数，不能全为 0 或相同值 |
| 7 | **JSON 语法** | 每个文件必须是合法 JSON（可通过 `python3 -m json.tool` 校验） |

### 第三阶段：上传到微信云数据库

```bash
cd /Users/zewujiang/Desktop/AICo/codebuddy-invest/.codebuddy/skills/investment-agent-daily-app/scripts
python3 upload_to_cloud.py "/Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows/investment_agent_data/miniapp_sync/" "{YYYY-MM-DD}"
```

**容错机制**：
- 上传失败 → 小程序自动降级使用本地缓存/Mock数据
- 部分上传失败 → 成功的数据生效，失败的保持旧数据
- 整阶段失败 → 打印警告，JSON 文件保留（下次可手动重传）

### 第四阶段：完成交付 + 输出确认

输出交付确认信息：

```
📱 投研鸭小程序数据更新完成 — {YYYY-MM-DD}

✅ briefing.json → 简报页（核心事件+判断+建议+情绪+聪明钱）
✅ markets.json  → 市场页（美股+M7+亚太+大宗+加密+GICS热力图）
✅ watchlist.json → 标的页（7板块×{N}只标的+详情+metrics）
✅ radar.json    → 雷达页（7项红绿灯+风险矩阵+事件日历+聪明钱详情）

☁️ 云数据库上传：{成功/失败数}
📊 数据完整度：{百分比}
```

---

## 优先级声明

| 优先级 | 维度 | 说明 |
|--------|------|------|
| **P0** | JSON Schema 100% 对齐 | 每个字段都必须存在且类型正确 |
| **P0** | 数据准确性 | RULE ZERO — 只用实时搜索数据 |
| **P0** | sparkline 完整性 | 每个标的必须有 7 天走势数据 |
| **P1** | 数据精确性 | 收盘价 $XXX.XX、涨跌幅 ±X.XX% |
| **P1** | 板块均衡 | 7 个板块每个至少 2 只标的 |
| **P2** | 分析质量 | analysis/reason/summary 内容有洞察 |
| **P3** | metrics 精确性 | PE/市值/营收增速等可用最新季度数据 |

---

## 致命错误清单（15条 — 零容忍）

| # | 错误类型 | 说明 |
|---|----------|------|
| 1 | JSON Schema 不匹配 | 字段名错误/缺失/多余 |
| 2 | 训练数据污染 | 数据不来自实时搜索 |
| 3 | 必填字段为空 | `""`、`[]`、`null`、`"--"` |
| 4 | 数据类型错误 | `change` 是 string 而非 number |
| 5 | 枚举值越界 | direction 写了 "rising" 而非 "up" |
| 6 | sparkline 缺失 | markets/watchlist 标的没有 sparkline |
| 7 | sparkline 无效 | 全为 0 或数组长度 ≠ 7 |
| 8 | 空板块 | watchlist 某个板块 stocks 为空数组 |
| 9 | 红绿灯不足7项 | trafficLights 数组长度 < 7 |
| 10 | GICS 不足11项 | gics 数组长度 < 11 |
| 11 | globalReaction 不足5项 | 核心资产反应不完整 |
| 12 | coreJudgments ≠ 3条 | 必须精确3条判断 |
| 13 | markdown 残留 | JSON 文本字段含 `**`、`|`、`>`、`- ` 等 md 语法 |
| 14 | JSON 语法错误 | 无法被 `json.loads()` 解析 |
| 15 | 价格数据错误 | 收盘价/涨跌幅与实际不符 |

---

## 知识库引用索引

| 文件 | 内容 | 用途 |
|------|------|------|
| [json-schema.md](references/json-schema.md) | **4个JSON的完整字段规范（核心文件）** | JSON 生成阶段 |
| [data-collection-sop.md](references/data-collection-sop.md) | 数据采集批次SOP + Google Finance模板 + 数据源优先级 | 采集阶段 |
| [stock-universe.md](references/stock-universe.md) | **7板块标的池 + 板块分类规则 + metrics采集指南** | watchlist 生成 |
| [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md) | AI产业链24环标的知识库 | batch 0b扫描 |
| [fund-universe.md](references/fund-universe.md) | 三梯队26家基金+策略师追踪清单 | batch 4扫描 |
| [media-watchlist.md](references/media-watchlist.md) | 三级媒体清单+扫描SOP | batch 0/0a扫描 |
| [data-source-priority.md](references/data-source-priority.md) | 数据源优先级表 + 降级路径 | 全流程 |
| [known-pitfalls.md](references/known-pitfalls.md) | App专属已知堵点与降级路径 | 全流程 |

---

## JSON 输出路径

```
# 默认输出路径：
/Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows/investment_agent_data/miniapp_sync/

# 4个JSON文件：
briefing.json / markets.json / watchlist.json / radar.json
```

---

## 端到端零堵点执行

用户触发后应尽量自动完成数据更新，但**准确性高于连续性**：
- 直接行情源异常 → 只切换到同类直接行情源 / API，不允许退化到新闻页
- sparkline / chartData 缺失 → 回到采集阶段补采，禁止估算生成
- 某标的关键行情无法获取 → 允许替换为同板块备选标的，但必须重新核验全量字段
- 上传失败 → JSON 文件保留，下次可重传
- 任何环节如触发核心行情缺失，**必须阻断发布**，而不是带病上线

---

## 版本Changelog

| 版本 | 日期 | 核心变更 |
|------|------|---------|
| **v1.3.2** | 2026-04-02 00:21 | 市场页板块 Insight 升级：①json-schema.md 新增 6 个板块级 Insight 字段（usInsight/m7Insight/asiaInsight/commodityInsight/cryptoInsight/gicsInsight），每个板块数据表格底部提供30-80字高质量一句话洞察，对齐日报"XX信号"风格；②原 usMarkets[0].note 迁移为独立 usInsight 字段，前端向后兼容；③markets.wxml 6个Tab/GICS均加入💡洞察卡片（复用 .market-comment 样式）；④markets.js _applyData 传递6个insight+向后兼容旧note；⑤markets-mock.js 补充6个高质量示例文本；⑥data-collection-sop.md 新增第七章"板块Insight生成规范"+门禁第17项验证。 |
| **v1.3.1** | 2026-04-02 00:00 | UI精修三项：①删除简报页顶部hero冗余渐变区域（导航栏已有标题+日期），页面更简洁；②修复判断扩展区 jx-divider 虚线样式（dashed→渐变淡化实线），视觉更优雅；③json-schema.md 中 references 从 string[] 升级为 object[]（含 name/summary/url），briefing 前端改为可点击展开的手风琴组件，展开后显示信息摘要和来源链接，向后兼容旧格式纯字符串数组。相关文件：briefing.js（删除 currentDate + 新增 expandedRefs/onRefToggle + references 兼容映射）、briefing.wxml（删除 hero + 重写 Reference 区域）、briefing.wxss（删除 hero 样式 + 修复虚线 + 新增展开面板样式）。 |
| **v1.3** | 2026-04-01 22:58 | 前端体验升级（阶段一）：①json-schema.md 升级至 v1.3 — briefing.json 新增 `timeStatus`（多时区+开市状态）、`keyDeltas[]`（增量信息 KEY DELTA，借鉴 Iran Briefing 设计）、`coreJudgments` 扩展 `keyActor/references/probability/trend` 四个可选字段；radar.json 新增 `fearGreed`（CNN Fear & Greed 情绪指数）、`predictions[]`（预测市场概率 Polymarket/Kalshi/CME FedWatch）；所有 JSON 新增 `_meta` 元数据对象；②小程序前端 v5.0 — 简报页新增时间状态栏（前端实时计算双时区+开市判断）、KEY DELTA 卡片（热度点+状态标签）、核心判断扩展行（决策者/参考源/概率/趋势标签）；雷达页新增 Fear & Greed 情绪卡片（渐变情绪条+数字跳动动画+三时段对比）、预测市场预览卡片（概率进度条+24h 趋势）；③简报页和雷达页数据底栏统一升级为双层状态栏（数据源+新鲜度+sourceType 标签+Skill 版本号）；④format.js 新增 `getMultiTimezone()`/`getMarketStatus()`/`getRelativeTime()`；⑤color.js 新增 `getDeltaStatusInfo()`/`getFearGreedInfo()`/`getPredictionTrendInfo()`/`getProbabilityInfo()`/`getJudgmentTrendInfo()`/`getHeatLabel()`。所有新字段均为可选（🔸标记），完全向后兼容旧数据。 |
| **v1.2** | 2026-04-01 | 数据质量六项深度治理：①CNH改用`ak.forex_hist_em("USDCNH")`真实离岸源，移除CNY=X混用；②日经/KOSPI新增`MARKET_SANITY_RANGE`量级校验+日经AkShare备用通道；③watchlist metrics升级为方案C（最新价/单日/7日/30日涨跌+PE(TTM)+`calc_star_rating()`规则化综合评级）；④北向资金红绿灯改为「外资动向」（港股均涨跌代理，`calc_foreign_capital_proxy()`），根因：2024-08-19交易所永久停止披露净买额；⑤阈值逻辑标准化为`TRAFFIC_LIGHT_RULES`常量+`auto_traffic_status()`程序化判断；⑥riskScore改为`calc_risk_score()`动态计算（权重公式：30+Σ灯色权重，上限100）；⑦upload_to_cloud.py新增`verify_upload()`上传后回读校验（7字段+数组长度+dataTime一致性）。 |
| **v1.0** | 2026-04-01 | 初始版本。从 `investment-agent-daily` v19.0 独立分支：①复用核心数据采集逻辑（6大铁律、数据源、采集批次）；②全新 JSON Schema 精确对齐小程序4页面（briefing/markets/watchlist/radar）；③新增 sparkline/chartData/metrics/analysis 等 MD 报告不需要但小程序需要的数据；④新增 stock-universe.md（7板块标的池）；⑤复用 upload_to_cloud.py |
