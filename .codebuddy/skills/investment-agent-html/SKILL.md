---
name: investment-agent-html
description: 当用户提到「投资报告」「投资HTML」「投研鸭报告」「investment report」或类似关键词时，自动执行投研鸭数据生产全流程，输出4个原生结构化JSON并渲染为单个自包含HTML报告。
---

# 投研鸭 HTML 报告生成 — 标准工作流 v1.0

> **版本**: v1.0 (2026-04-07)
> **基于**: investment-agent-daily-app v7.1 裁剪（删除云数据库/Refresh模式/语音播报/硬编码路径）
> **主控文档**：本文件为精炼主控，详细规则/知识库/模板/SOP通过引用按需加载。

---

## 定位与使命

> **读者**: 大老板（人读，浏览器查看）
> **产出物**: 4个原生结构化 JSON 文件 + **1个自包含 HTML 报告**
> **核心宗旨**: 从全球市场实时数据出发，生成投行级品质的每日投资策略简报，双击浏览器打开即可查看
> **零依赖**: 无需微信云开发、无需 API Key、无需环境变量

---

## 全局基础铁律（最高优先级，凌驾于所有其他规则之上）

> **🚨 一句话**：**禁止 AI 凭训练数据中的模糊记忆直接输出任何数字。所有数字必须来自当期实时搜索/查证。**

本条铁律适用于本 Skill 产出的**全部内容**，包括但不限于：

| 数据类别 | 具体字段示例 | 必须查证的数据源 |
|----------|-------------|----------------|
| **行情价格** | price / value / sparkline / chartData | 英为财情 / 东方财富 / Google Finance / AkShare |
| **涨跌幅** | change / change24h | 同上（从行情源计算，禁止从新闻提取） |
| **汇率** | 离岸人民币CNH / 美元指数DXY | 英为财情 / 中国货币网 / 新浪外汇 |
| **持仓权重** | topHoldings / smartMoneyHoldings / positions[].weight | SEC 13F / 13Radar / Whalewisdom / StockAnalysis |
| **估值指标** | PE(TTM) / PB / 市值 / AUM | StockAnalysis / 东方财富 / web_search |
| **目标价/预测** | 分析师目标价 / predictions[].probability | 原始研报 / Polymarket / CME FedWatch |
| **资金流数据** | 机构买卖金额 / ETF 净流入 | Bloomberg / ETF.com / ARK 官网 |
| **宏观数据** | CPI / 利率 / 信用利差 | FRED / BLS / 行情终端 |

**自查三问（每个数字都必须过关）**：
1. ❓ 这个数字来自**本次执行的哪次搜索**？→ 答不上来 = 凭记忆编造 → **必须重新搜索**
2. ❓ 搜索结果中**原文怎么写的**？→ 对不上 = 数字被篡改 → **必须修正**
3. ❓ 数据的**时间戳**是否在合理范围内？→ 过期 = 旧数据 → **必须更新**

**违规后果**：任何凭记忆输出的数字，一旦被发现与真实值有偏差，等同于**数据造假**。**宁缺毋错，宁空不编。**

---

## 八大铁律（最高优先级）

| 铁律 | 核心要求 |
|------|---------|
| **RULE ZERO** | **全局数据查证铁律**。所有数字必须来自当期实时搜索，**禁止凭 AI 训练数据的模糊记忆直接输出任何数字**。 |
| **RULE ZERO-A** | **交易数据与新闻数据严格隔离**：交易数据只从行情平台取，禁止从新闻媒体反向提取价格。 |
| **RULE ZERO-B** | **观点数据来源追溯铁律**：smartMoneyDetail 中每个数字必须可追溯到本次 web_search/web_fetch。 |
| **RULE ONE** | JSON 完整性铁律。4个JSON中每个必填字段都必须有精确值，严禁空字符串/空数组/null。 |
| **RULE TWO** | 数据类型严格。change 必须是 number，sparkline 必须是 7 个 number 的数组，枚举值严格受控。 |
| **RULE THREE** | Schema 对齐铁律。每个 JSON 结构 100% 对齐 references/json-schema.md 定义。 |
| **RULE FOUR** | sparkline 必填。markets/watchlist 中每个标的必须有 7 天历史走势数据。 |
| **RULE FIVE** | 板块均衡。watchlist 的 4 个核心板块每个至少2只标的。 |
| **RULE SIX** | 新增标的数据零容忍捏造。无法获取时：price 写"待采集"、change 写 0、sparkline 写 []。 |
| **RULE SEVEN** | 聪明钱搜索广覆盖+产出精选。Heavy≥10次web_search+1次web_fetch；Weekend≥8次+1次。 |

---

## 触发条件与两档内容引擎

**触发关键词**：投资报告 / 投资HTML / 投研鸭报告 / investment report

### 两档模式路由表（简化版，删除 Refresh 和 Live）

| 时机 | 模式 | 采集量 | 内容侧重 | `_meta.sourceType` |
|------|------|--------|---------|-------------------|
| 周一 | **Heavy + 周一特别版** | 全量6批次+Batch A | 行情+分析+上周总结+本周展望 | `heavy_analysis` |
| 周二～周五 | **Heavy** | 全量6批次+Batch A | 行情+分析+建议 | `heavy_analysis` |
| **周末/节假日/休市日** | **Weekend** | 媒体深度扫描 | 周度总结+深度洞察+下周展望 | `weekend_insight` |

### 模式判定逻辑

```
触发执行
  → 今天是周几？
    → 周六/周日 → Weekend 模式
    → 周一~周五 → 是否为美股休市日？
      → 休市日 → Weekend 模式
      → 周一 → Heavy 模式 + 周一特别版模板
      → 周二~周五 → Heavy 模式 + 标准日模板
```

### Weekend 模式

> **详细规范** → [weekend-mode.md](references/weekend-mode.md)
> **一句话概要**：周末/休市日读取上一交易日4个JSON文件作为基准，保留行情数据不变，更新分析/洞察/展望字段。

---

## 产出物定义

| 文件 | 对应 HTML Tab | 数据来源 | Schema 定义 |
|------|-------------|---------|------------|
| `briefing.json` | 简报 Tab | 核心结论+事件+判断+建议 | → [json-schema.md §1](references/json-schema.md) |
| `markets.json` | 市场 Tab | 全球市场+GICS板块 | → [json-schema.md §2](references/json-schema.md) |
| `watchlist.json` | 标的 Tab | 重点标的+行业分析 | → [json-schema.md §3](references/json-schema.md) |
| `radar.json` | 雷达 Tab | 风险雷达+基金详情 | → [json-schema.md §4](references/json-schema.md) |
| **`touyanduck-YYYY-MM-DD.html`** | **全部4个Tab** | **从上述4个JSON渲染** | — |

---

## 工作流（6个阶段）

### 第零阶段：日期检测 + 模式路由 + 环境准备

```bash
date "+%A %Y-%m-%d %H:%M:%S"
```

- **周六～周日 / 美股休市日** → **Weekend 模式**（详见 [weekend-mode.md](references/weekend-mode.md)）
- **周一** → **Heavy 模式** + 使用 monday-special.json 模板
- **周二～周五** → **Heavy 模式** + 使用 daily-standard.json 模板
- 确认输出目录存在：`{project_root}/workflows/investment_agent_data/miniapp_sync/`

### 第一阶段：实时数据采集（独立完整采集）

**详细的采集批次SOP、数据源优先级表** → [data-collection-sop.md](references/data-collection-sop.md)

**采集批次概要**（与 daily-app 完全一致）：

| 批次 | 内容 | 知识库引用 |
|------|------|-----------|
| 0 | 全球财经媒体头条扫描（一级必扫7家） | → [media-watchlist.md](references/media-watchlist.md) |
| 0a | 深度媒体补充扫描（二级强化11家） | → [media-watchlist.md](references/media-watchlist.md) |
| 0b | AI产业链重大动态专项扫描 | → [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md) |
| 1a-1d | M7个股+美股指数+VIX+GICS+焦点个股 | → [data-collection-sop.md](references/data-collection-sop.md) |
| 2 | 亚太/港股+北向资金 | |
| 3 | 大宗商品/汇率/加密 | |
| 4 | 基金&大资金动向（三梯队） | → [fund-universe.md](references/fund-universe.md) |
| 5 | watchlist 标的详情采集 | → [stock-universe.md](references/stock-universe.md) |
| 6 | 本周关键事件日历+风险矩阵 | |
| A | 情绪与预测数据（可选） | |

### 第1.5阶段：数据完整性门禁（与 daily-app 完全一致）

不通过则禁止进入 JSON 生成阶段。详见 daily-app SKILL.md 同名章节。

### 第二阶段：结构化 JSON 生成（核心阶段）

基于采集数据，严格按照 `references/json-schema.md` 的 Schema 定义生成 4 个 JSON 文件。

**生成规则**（与 daily-app 完全一致）：
1. **先加载 Schema** — 必须重新读取 json-schema.md
2. **枚举值受控** — direction/signal/type 等严格受控
3. **数据类型严格** — change 必须是 number
4. **纯文本** — 所有文本字段禁止 markdown 语法
5. **sparkline/chartData** — 由第三阶段脚本自动补全

**输出路径**：
```
{project_root}/workflows/investment_agent_data/miniapp_sync/
├── briefing.json
├── markets.json
├── watchlist.json
└── radar.json
```

### 第2.3阶段：AI 直填公式

红绿灯 trafficLights、riskScore / riskLevel / riskAdvice、metrics 综合评级等计算规则与 daily-app 完全一致。详见 json-schema.md 和 daily-app SKILL.md §2.3。

### 第2.5阶段：JSON 完整性终审（强制）

与 daily-app 完全一致的 14 项门禁 + Top 10 快速终审。不通过则禁止进入第三阶段。

### 第三阶段：sparkline补全 + HTML渲染（一键自动执行）

> **⚠️ 此阶段 AI 必须直接执行命令，无需用户手动操作。**

**执行命令（AI 直接调用 execute_command）**：

```bash
bash {project_root}/.codebuddy/skills/investment-agent-html/scripts/run_daily.sh {YYYY-MM-DD}
```

> 注意：`{project_root}` 需替换为实际项目根目录。AI 执行时应动态获取。

脚本自动完成：
1. JSON 语法预校验（硬依赖，失败则阻断）
2. sparkline/chartData 历史序列补全（**软依赖**，失败时警告+跳过）
3. **渲染 HTML 报告**（4个JSON → 1个 touyanduck-YYYY-MM-DD.html）

### 第四阶段：完成交付 + 输出确认

#### 4.1 搜索执行日志（强制输出）

```
### 🔍 搜索执行日志
| # | 层次 | 搜索关键词/URL | 结果摘要 | 有效数据提取 |
|---|------|---------------|---------|------------|
| ... | ... | ... | ... | ... |
| **合计** | — | **web_search: {N}次 / web_fetch: {M}次** | — | **达标✅ / 不达标❌** |

达标基线：Heavy≥10+1 / Weekend≥8+1（RULE SEVEN）
```

#### 4.2 交付确认信息

```
📄 投研鸭 HTML 报告生成完成 — {YYYY-MM-DD}

✅ briefing.json → 简报 Tab
✅ markets.json  → 市场 Tab
✅ watchlist.json → 标的 Tab
✅ radar.json    → 雷达 Tab
✅ touyanduck-{YYYY-MM-DD}.html → 双击浏览器打开查看 🦆

📊 数据完整度：{百分比}
```

### 第五阶段：执行复盘（30秒快检，强制触发）

每次执行完毕后，AI 必须自问并输出以下三行：

```
### 🔄 执行复盘
1. 🆕 **本次有没有遇到新的堵点/数据源异常？**
   → {有/无}
2. 📋 **本次有没有发现规范覆盖不到的新场景？**
   → {有/无}
3. 🎯 **trafficLights 7项是否仍是最优组合？**
   → {是/否}
```

---

## 优先级声明

| 优先级 | 维度 | 说明 |
|--------|------|------|
| **P0** | JSON Schema 100% 对齐 | 每个字段都必须存在且类型正确 |
| **P0** | 数据准确性 | RULE ZERO — 只用实时搜索数据 |
| **P0** | sparkline 完整性 | 每个标的必须有 7 天走势数据 |
| **P1** | 数据精确性 | 收盘价 $XXX.XX、涨跌幅 ±X.XX% |
| **P1** | 板块均衡 | 4 个核心板块各≥2标的 |
| **P2** | 分析质量 | analysis/reason/summary 内容有洞察 |
| **P3** | metrics 精确性 | PE/市值/营收增速等可用最新季度数据 |

---

## 致命错误清单（29条 — 零容忍）

与 daily-app 完全一致。详见 [known-pitfalls.md](references/known-pitfalls.md)。

核心致命错误速查：

| # | 错误类型 |
|---|----------|
| 1 | JSON Schema 不匹配 |
| 2 | 训练数据污染 |
| 3 | 必填字段为空 |
| 4 | 数据类型错误 |
| 5 | 枚举值越界 |
| 6-7 | sparkline 缺失/无效 |
| 8 | 空板块 |
| 13 | markdown 残留 |
| 15 | 价格数据错误 |
| 22 | 交易数据来源错误（RULE ZERO-A） |
| 28 | smartMoneyDetail 知识库快照污染 |
| 29 | 聪明钱搜索覆盖不足 |

---

## 知识库引用

| 文件 | 内容 | 用途 |
|------|------|------|
| [json-schema.md](references/json-schema.md) | **4个JSON的完整字段规范（核心文件）** | JSON 生成阶段 |
| [data-collection-sop.md](references/data-collection-sop.md) | 数据采集批次SOP + 数据源优先级 | 采集阶段 |
| [stock-universe.md](references/stock-universe.md) | 5板块标的池 + metrics采集指南 | watchlist 生成 |
| [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md) | AI产业链24环标的知识库 | batch 0b扫描 |
| [fund-universe.md](references/fund-universe.md) | 三梯队26家基金+策略师追踪清单 | batch 4扫描 |
| [media-watchlist.md](references/media-watchlist.md) | 三级媒体清单+扫描SOP | batch 0/0a扫描 |
| [data-source-priority.md](references/data-source-priority.md) | 数据源优先级表 + 降级路径 | 全流程 |
| [known-pitfalls.md](references/known-pitfalls.md) | 已知堵点与降级路径 | 全流程 |
| [weekend-mode.md](references/weekend-mode.md) | Weekend 模式完整规范 | 周末/休市日执行 |
| [briefing-golden-sample.json](references/briefing-golden-sample.json) | 简报页黄金样本 | 质量基准参考 |

---

## JSON 输出路径

```
# 默认输出路径：
{project_root}/workflows/investment_agent_data/miniapp_sync/

# 4个JSON + 1个HTML：
briefing.json / markets.json / watchlist.json / radar.json / touyanduck-YYYY-MM-DD.html
```

---

## 版本历史

> v1.0 (2026-04-07) — 基于 investment-agent-daily-app v7.1 创建 HTML 版本。删除云数据库上传/Refresh模式/语音播报/硬编码路径。新增 render_html.py 渲染脚本和 report.html 模板。
