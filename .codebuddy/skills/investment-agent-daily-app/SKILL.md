---
name: investment-agent-daily-app
description: 当用户提到「投资App」「小程序数据」「投研鸭数据」「app数据更新」「miniapp sync」或类似关键词时，自动执行投研鸭小程序数据生产全流程，输出4个原生结构化JSON并上传微信云数据库。
---

# 投研鸭小程序数据生产 — 标准工作流 v4.3

> **版本**: v4.3 (2026-04-05 17:37)
> **主控文档**：本文件为精炼主控，详细规则/知识库/模板/SOP通过引用按需加载。

### v4.3 Changelog（2026-04-05 17:37）
- **数据源升级：AkShare 替代 yfinance**：`refresh_verified_snapshot.py` 从 v2.2 升级至 v3.0。主数据源从 yfinance（已被 Yahoo 403 封禁）切换至 AkShare 新浪源，东方财富源作为 fallback。覆盖率从 0%（yfinance 全部失败）提升至 ~89%（41/46 标的成功）。
- **新增覆盖标的**：A股指数（上证/深证）和港股指数（恒生/恒生科技）从 v2.2 的 `None`（跳过）升级为 AkShare 自动补全。
- **防限流策略**：逐个调用 + 0.3秒 sleep 间隔，替代 yfinance 的批量下载模式。
- **双源降级路径**：新浪源失败 → 东方财富源自动重试 → 仍失败 → 跳过（保留 AI 估算值）。
- **AkShare 缺口（6个标的保留 AI 估算值）**：VIX / 美元指数DXY / 10Y美债 / 离岸人民币CNH / BTC / ETH。
- **`run_daily.sh` 升级至 v3.0**：说明文字从 yfinance 更新为 AkShare，失败提示更新。
- **同步更新**：`known-pitfalls.md` 升级至 v2.3（新增堵点#24）、`data-source-priority.md` 升级至 v1.6。

### v4.2 Changelog（2026-04-05 15:30）
- **`WATCHLIST_YF_MAP` 扩展至30只标的**：删除旧板块6只已下线标的（MRVL/MU/COST/NVO/LLY/JPM）；新增11只美股（AAPL/GOOGL/META/AMZN/ANET/PLTR/RBLX/TEM/NOW/KO/OXY/AXP）；新增港股4只（0700.HK/9988.HK/2513.HK/0100.HK）；新增A股5只（300308.SZ/688256.SZ/300750.SZ/002594.SZ/600519.SS）；`refresh_verified_snapshot.py` 升级至 v2.2。
- **港股/A股 sparkline 策略升级**：港股/A股标的全部加入 `WATCHLIST_YF_MAP`，yfinance 成功则写入真实历史数据，失败则失败安全机制自动跳过保留 AI 估算值。
- **A股 ticker 格式陷阱固化**：深交所 `.SZ` 直接用；上交所 `.SH` 必须转为 `.SS`（如茅台 `600519.SH` → `600519.SS`）；已在映射表中处理，并固化至 `known-pitfalls.md` 堵点#23。
- **SKILL.md 第2.3阶段规则更新**：`sparkline/chartData` 生成规则从「港股/A股由 AI 手动填」改为「所有映射表标的由脚本自动补，失败时 AI 再填」。
- **同步更新**：`known-pitfalls.md` 升级至 v2.2（新增堵点#23）。
- **watchlist 板块架构 v2.0 重构**：旧7板块（ai/semi/internet/energy/consumer/pharma/finance，17只标的）完全废弃。新5板块架构以大老板投资视角为核心：`ai_infra`（AI算力链10-12只）/ `ai_app`（AI应用4-6只）/ `cn_ai`（国产AI 5-7只，含未上市标的动态跟踪）/ `smart_money`（聪明钱精选5-6只，巴菲特+段永平非AI持仓）/ `hot_topic`（本期热点0-4只，事件驱动可变）。标的总数从17只扩展至约30只。
- **新增 `badges` 特殊标签系统**：`巴菲特第一重仓/巴菲特持有/段永平重仓/段永平持有/段永平大幅增持/段永平新建仓/大老板已汇报/未上市` 8种标签，前端金色/蓝色/橙色/灰色区分，与普通 tags 视觉独立。
- **新增未上市标的支持**：`listed: false` 标识，不显示价格/涨跌/sparkline/metrics，改为展示最新动态+竞争格局+融资估值。当前覆盖：字节跳动。
- **新增 `hot_topic` 动态板块**：事件驱动触发，过滤已有板块标的后取 top 2-4，无事件时整个板块隐藏。
- **RULE FIVE 更新**：从"7板块每个至少2只"改为"5板块前4个核心板块每个至少2只，hot_topic可为空"。
- **同步更新**：`stock-universe.md` v2.0 完全重写、`json-schema.md` §3 重构、`stock-card` 组件 v5.0、`watchlist.js` v5.0。

### v4.0 Changelog（2026-04-05 12:05）
- **架构升级：三档内容引擎** — 小程序"永远在线"，不允许出现空白页面。从"交易日才执行"升级为全年365天均可产出。
  - **Heavy 模式**（交易日盘后）：全量6批次采集 + 完整4个JSON，与v3.1相同
  - **Weekend 模式**（周末/节假日/休市日）：**新增** — 无行情时以深度洞察/周度总结/下周展望填充，保留上一交易日市场数据，内容侧重"思考"而非"报价"
  - **Live 模式**（交易日盘中多次更新）：**预留** — 增量更新变化部分（快讯/异动/实时价格），当前版本标记为 TODO
- **Weekend 模式产出规范**：详见下方「Weekend 模式内容规范」章节
- **`_meta.sourceType` 枚举扩展**：新增 `weekend_insight`（周末洞察模式）
- **`timeStatus.marketStatus` 枚举扩展**：新增 `美股休市`（已在 v3.0 添加）
- **删除** 第零阶段"周六～周日 → 不执行"硬性规则，改为按三档模式路由

### v3.1 Changelog（2026-04-05 11:48）
- **风险提示模块 bullet point 升级**：`riskNote` 散文字符串升级为 `riskPoints[]` 数组（2-4条独立风险点），前端用 `wx:for` 循环渲染，每条带红色圆点 `•` 前缀；保留旧版 `riskNote` 作为 fallback（前端优先读 `riskPoints`，缺失时按句号拆分兜底）。
- **图标规范更新**：简报页风险提示图标从 `⚠️` 更换为 `🛡️`（盾牌），与 🎯⚡🌡️🧠 实心彩色 emoji 风格统一，不与重点事件的 🚨 重复。
- **精确数值强制规则**：所有价格/涨跌幅字段禁止使用 `~`（约等于）、`≈`、`大约`、`左右` 等模糊前缀/后缀，必须来自行情源精确数值。典型事故：黄金 `~$4,677` → 修正为 `$4,675`。
- **致命错误清单新增第26条**（riskPoints）+ **第27条**（模糊数值）。
- **同步更新**：`json-schema.md` 升级至 v2.2（含 globalReaction value 精确数值规则）、`known-pitfalls.md` 升级至 v2.0（新增堵点#20）。

### v3.0 Changelog（2026-04-03 20:00）
- **架构升级：方案A — 双轨分工**：AI+搜索轨（主轨）负责所有字段生成；脚本补全轨只负责 `sparkline(7天)` + `chartData(30天)` 两个数组字段的真实历史序列补全。彻底消除脚本覆盖 AI 数据的风险根源。
- **`refresh_verified_snapshot.py` 升级至 v2.0（方案A）**：从 600+ 行缩减至 ~200 行；只用 yfinance 单一依赖（移除 AkShare / FRED / 新浪）；只读写 `markets.json` 和 `watchlist.json` 的 sparkline/chartData 字段；`briefing.json` 和 `radar.json` 完全不读取不修改；任何标的失败 → 跳过该标的，不阻断整体流程。
- **`run_daily.sh` 升级至 v2.0**：说明文字与方案A架构完全对齐；第1步说明从「API 数据校正」改为「sparkline/chartData 历史序列补全」；完成提示说明数据来源分工更精确。
- **新增 AI 直填规则：trafficLights / riskScore / riskLevel / riskAdvice**：这四个字段脚本不再负责，AI 在第二阶段 JSON 生成时按照本文档写死的公式直接计算填写，保证一致性。规则见下方「AI 直填公式」章节。
- **新增 AI 直填规则：GICS 11板块 / globalReaction / metrics**：同上，AI 从 Google Finance 采集后直接填写，脚本不再覆盖这些字段。
- **同步更新** `known-pitfalls.md` 至 v1.9、`data-collection-sop.md` 至 v1.5、`data-source-priority.md` 至 v1.5。

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

## 七大铁律（最高优先级）

| 铁律 | 核心要求 |
|------|---------|
| **RULE ZERO** | 训练数据全面禁用。所有数据只能来自当期实时搜索。自查三问：①来自搜索？②时间戳≤24h？③可追溯？任一为否→重写 |
| **RULE ZERO-A** | **交易数据与新闻数据严格隔离（零容忍）**：<br>● **交易数据**（价格/涨跌幅/汇率/sparkline）→ **只允许**直接行情 API/数据源（Google Finance / yfinance / AkShare / OilPrice.com / FRED 等），**禁止**从任何新闻媒体页面（Bloomberg/Reuters/CNBC/财经媒体等）反向提取价格数字<br>● **新闻/观点/评论数据**（事件背景/分析/预测/聪明钱动向）→ 媒体网站（Bloomberg/Reuters/WSJ/华尔街见闻等）<br>● **违规判定**：如果一个价格数字的来源是新闻文章而非行情平台，该条数据视为**训练数据污染**，必须重新从行情源采集 |
| **RULE ONE** | JSON 完整性铁律。4个JSON中每个必填字段都必须有精确值，严禁空字符串/空数组/`null`/`"--"`/`"N/A"` |
| **RULE TWO** | 数据类型严格。`change` 必须是 `number` 类型（不是 string），`sparkline` 必须是 7 个 number 的数组，枚举值必须在允许范围内 |
| **RULE THREE** | Schema 对齐铁律。每个 JSON 的结构必须 100% 对齐 `references/json-schema.md` 中的定义，不允许新增/缺失/改名字段 |
| **RULE FOUR** | sparkline 必填。markets/watchlist 中每个标的必须有 7 天历史走势数据（sparkline 数组），watchlist 额外需要 30 天 chartData |
| **RULE FIVE** | 板块均衡。watchlist 的 5 个板块（ai_infra/ai_app/cn_ai/smart_money/hot_topic）中，前4个核心板块每个至少2只标的；hot_topic 为动态板块，无事件时可为空数组或整个板块省略 |
| **RULE SIX** | **新增标的行情数据零容忍捏造**。任何新加入 watchlist 的标的，`price`/`change`/`sparkline`/`chartData`/`metrics` 中的价格数据**必须全部来自 Google Finance web_fetch 或 yfinance 真实数据**。**绝对禁止**凭记忆/推测/估算填写任何价格数字。如果行情数据无法获取（如网络超时），该标的的 price 写"待采集"、change 写 0、sparkline/chartData 写空数组 `[]`，前端会自动隐藏图表区域。**宁可留空也不能编造**。<br>典型事故（2026-04-05）：新增10只标的全部凭空捏造价格，OXY 偏差16%、GOOGL 偏差46%、PLTR 偏差36%、ANET 偏差38%。 |

---

## 触发条件与三档内容引擎

**触发关键词**：投资App / 小程序数据 / 投研鸭数据 / app数据更新 / miniapp sync

> **核心原则**：小程序是"永远在线"的产品。用户任何时候打开都必须看到有价值的内容，绝不允许空白页面。

### 三档模式路由表

| 时机 | 模式 | 采集量 | 内容侧重 | `_meta.sourceType` |
|------|------|--------|---------|-------------------|
| 周一（盘后） | **Heavy + 周一特别版** | 全量6批次+Batch A | 行情+分析+上周总结+本周展望 | `heavy_analysis` |
| 周二～周五（盘后） | **Heavy** | 全量6批次+Batch A | 行情+分析+建议 | `heavy_analysis` |
| 周二～周五（盘前/盘中） | **Live**（TODO v5.0） | 增量（变化部分） | 快讯+异动+更新价格 | `realtime_quote` |
| **周末/节假日/休市日** | **Weekend** | 媒体深度扫描 | 周度总结+深度洞察+下周展望 | `weekend_insight` |

### 模式判定逻辑

```
用户触发
  → Step 1: 今天是周几？
    → 周六/周日 → Weekend 模式
    → 周一~周五 → Step 2: 是否为美股休市日？（Good Friday / MLK Day 等）
      → 休市日 → Weekend 模式
      → 非休市日 → Heavy 模式（若用户指定"更新一下"则Heavy，未来支持Live增量）
```

### Weekend 模式内容规范（v4.0 新增）

> **设计哲学**：没有行情不意味着没有价值。周末是"思考日"——比交易日更适合深度分析、复盘和前瞻。
> **内容品质标准**：与交易日 Heavy 模式相同的高盛/摩根斯坦利级严谨度。每句话都有信息量，每个判断都有论据。

#### Weekend 模式数据采集（精简版）

| 批次 | 内容 | 搜索次数 |
|------|------|---------|
| W0 | 全球财经媒体周末深度报道扫描 | 3-5次 web_search |
| W1 | 地缘政治/宏观政策最新进展 | 2-3次 web_search |
| W2 | 下周关键事件日历+风险前瞻 | 2次 web_search |
| W3 | 机构/策略师最新观点汇总 | 2-3次 web_search |
| WA | CNN Fear&Greed / Polymarket 最新数据 | 1-2次 web_fetch（可选，非阻断） |

#### Weekend 模式 JSON 产出规则

**共同规则**：
- `date` 字段写**周末当天日期**（如 "2026-04-05"）
- `dataTime` 写 `"2026-04-05 周末更新 BJT"`，明确标注非交易日
- `_meta.sourceType` = `"weekend_insight"`
- `timeStatus.marketStatus` = `"美股休市"`

**briefing.json（周末版）**：

| 字段 | Weekend 模式内容 | 与Heavy模式的差异 |
|------|----------------|-----------------|
| `takeaway` | 周末核心结论：本周最重要的启示 + 下周最需关注的变量 | 视角从"今日"切换为"本周→下周" |
| `coreEvent.title` | 本周最重要事件回顾标题 | 回顾性标题，非实时新闻 |
| `coreEvent.chain[]` | 3-5条：本周重点事件链 + 周末新进展（若有） | 可包含周末媒体深度报道的新洞察 |
| `globalReaction[]` | **保留上一交易日收盘数据不变** + note 改为"本周累计表现"视角 | note 从"当日解读"改为"本周回顾" |
| `coreJudgments[]` | 3条判断改为：①本周复盘判断 ②下周核心预判 ③中期趋势判断 | 从"日度"切换为"周度+前瞻"视角 |
| `actions.today[]` | 改为"下周操作建议"（1-3条） | label 含义从"今日"变为"下周" |
| `actions.week[]` | 改为"月度/中期布局建议"（0-2条） | 拉长时间维度 |
| `sentimentScore/Label` | 综合本周情绪+周末舆论最新方向 | 可微调（不超过±5分） |
| `marketSummaryPoints[]` | 3-5条本周市场复盘要点 | 从"日度观察"改为"周度复盘" |
| `smartMoney[]` | 本周最重要的机构动向汇总 | 同Heavy |
| `riskPoints[]` | 下周核心风险点 | 前瞻性，非回顾 |

**markets.json（周末版）**：

| 字段 | Weekend 模式规则 |
|------|-----------------|
| 所有 `price` / `change` / `sparkline` | **保留上一交易日数据不变**（不清零，不伪造） |
| 6个 Insight 字段 | **更新为"本周表现回顾+下周展望"视角** |

**watchlist.json（周末版）**：

| 字段 | Weekend 模式规则 |
|------|-----------------|
| 所有 `price` / `change` / `sparkline` / `chartData` / `metrics` | **保留上一交易日数据不变** |
| `analysis` | **更新为周度深度分析**（比日度更有深度，含本周事件影响+估值回顾+下周催化剂） |
| `reason` | 更新为下周关注点 |
| `tags` | 可根据本周表现微调 |
| `sectors[].summary` | 更新为本周板块表现回顾 |

**radar.json（周末版）**：

| 字段 | Weekend 模式规则 |
|------|-----------------|
| `trafficLights[]` | **保留上一交易日数据不变** |
| `riskScore` / `riskLevel` / `riskAdvice` | **保留不变** |
| `events[]` | **重点更新 — 下周关键事件日历**（这是周末最有价值的内容） |
| `riskAlerts[]` | **更新为下周风险前瞻** |
| `alerts[]` | 本周异动回顾 / 周末重大进展 |
| `smartMoneyDetail[]` | 本周机构动向深度分析 |
| `predictions[]` / `fearGreed` | 更新最新数据（若Batch WA获取成功） |

#### Weekend 模式工作流

```
第零阶段：日期检测 → 路由到 Weekend 模式
  ↓
第一阶段：精简数据采集（W0~WA，共10-15次搜索，远少于Heavy的50+次）
  ↓
第二阶段：读取上一交易日JSON文件 → 保留行情数据 → 更新分析/洞察/展望字段
  ↓
第2.5阶段：JSON 终审（同Heavy标准，不降级）
  ↓
第三阶段：上传云数据库
  ↓
第四阶段：交付确认（标注 Weekend 模式）
```

**关键约束**：
- Weekend 模式**不伪造行情数据**。所有价格/涨跌幅保留上一交易日真实值，绝不估算。
- Weekend 模式**不降低内容品质**。分析深度应高于日度（有更多时间思考），文字精炼度标准不变。
- Weekend 模式必须**读取上一交易日的4个JSON文件**作为基准，在此基础上修改分析内容字段。
- `_meta.sourceType` = `"weekend_insight"` 让前端可识别周末模式，显示对应标签。

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

### 第零阶段：日期检测 + 模式路由 + 环境准备

```bash
date "+%A %Y-%m-%d %H:%M:%S"
```

- **周六～周日 / 美股休市日** → **Weekend 模式**（见上方「Weekend 模式内容规范」）
  - 读取上一交易日 4 个 JSON 文件作为基准
  - 精简采集（W0~WA）→ 更新分析/洞察字段 → 保留行情数据 → 上传
- **周一** → **Heavy 模式** + 使用 monday-special.json 模板（含上周回顾数据）
- **周二～周五** → **Heavy 模式** + 使用 daily-standard.json 模板
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
| **A** | **情绪与预测数据采集（CNN Fear&Greed / Polymarket / CME FedWatch）** | → [data-collection-sop.md 第八章](references/data-collection-sop.md)（可选批次，失败不阻断） |

**⚠️ 与原 Skill 的关键差异**：
- 每个标的必须额外采集 **7 天历史价格**（用于 sparkline）
- watchlist 标的必须额外采集 **30 天历史价格**（用于 chartData）
- 每个 watchlist 标的必须采集 **6 项 metrics 指标**（最新价/单日涨跌/7日涨跌/30日涨跌/PE(TTM)/综合评级——方案C）
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
| 5 | **watchlist 5个板块（前4个核心板块×每板块≥2标的）** | 价格+涨跌+tags+badges+reason+analysis+metrics+risks（未上市标的免metrics/sparkline/chartData） | 回到批次5补采 |
| 6 | **radar 7项红绿灯** | 精确值+status | 回到批次3补采 |
| 7 | **coreEvent + coreJudgments×3 + actions + riskPoints** | 完整文本；riskPoints 2-4条 | 补充分析 |
| 8 | **globalReaction 6项** | name+value+direction | 补充 |
| 9 | **smartMoney 2-4条** | source+action+signal | 补充 |
| 10 | **events 3-5条 + riskAlerts 2-3条** | 完整字段 | 补充 |

**⭐ 可选字段建议检查（非阻断——缺失时前端对应模块不渲染，不影响发布）**：

| # | 验证项 | 要求 | 未填时操作 |
|---|--------|------|-----------|
| 18 | briefing: timeStatus（建议） | bjt+est+marketStatus(枚举值见 json-schema.md)+refreshInterval | 根据执行时间推算填写，或省略（前端可自行计算） |
| 19 | briefing: keyDeltas（建议） | 3-5条，每条 title(20-40字)+status(枚举)+heat(1-5整数)+brief(10-25字极简) | 在 JSON 生成阶段基于当日全部采集数据提炼；跳过则前端不渲染该模块 |
| 20 | radar: fearGreed（建议） | value(0-100整数)+label(枚举)+previousClose+oneWeekAgo+oneMonthAgo | 参照 Batch A 子批次 A1 采集结果填入；获取失败则完全省略该字段（不填 null） |
| 21 | radar: predictions（建议） | 2-4条，每条 title+source(枚举)+probability(0-100整数)+trend(枚举)+change24h | 参照 Batch A 子批次 A2/A3/A4 采集结果汇总；所有子批次均失败时填 [] |
| 22 | 所有4个JSON: _meta（建议） | sourceType+generatedAt(ISO8601格式)+skillVersion | sourceType 按模式填写（Heavy→`heavy_analysis` / Weekend→`weekend_insight`）；generatedAt 为执行时间（+08:00）；skillVersion 为 "v4.0" |

### 第二阶段：结构化 JSON 生成（核心阶段）

基于采集数据，严格按照 `references/json-schema.md` 的 Schema 定义生成 4 个 JSON 文件。

**生成规则**：
1. **先加载 Schema** — 必须重新读取 `json-schema.md`，逐字段对照生成
2. **枚举值受控** — direction 只能是 `up/down/flat`，signal 只能是 `bullish/bearish/neutral`，等等
3. **数据类型严格** — `change` 必须是 `number`（如 `1.42`），不是 string（如 `"+1.42%"`）
4. **纯文本** — 所有文本字段禁止包含 markdown 语法（`**加粗**`、`|表格|`、`- 列表`等）；analysis 字段允许 `\n` 分段
5. **sparkline/chartData 生成** — **方案A 双轨分工**：所有 WATCHLIST_YF_MAP 中已注册的标的（美股+港股+A股）的 sparkline(7天)/chartData(30天) 均由第三阶段脚本自动补全，AI 在此阶段**无需手动生成**；脚本失败（yfinance 超时/数据不足）时会自动跳过该标的，此时 AI 再从东方财富/同花顺采集历史价格填入。**严禁估算、插值或模拟波动生成 sparkline**（违反 RULE FOUR）。
   **A股 yfinance ticker 格式注意**：深交所用 `.SZ`（如 `300750.SZ`）；上交所必须用 `.SS`（如 `600519.SS`），**不是 `.SH`**，映射表已处理此转换。

**输出路径**：
```
{project_root}/workflows/investment_agent_data/miniapp_sync/
├── briefing.json
├── markets.json
├── watchlist.json
└── radar.json
```
> 实际路径：`/Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows/investment_agent_data/miniapp_sync/`

### 第2.3阶段：AI 直填公式（方案A 新增 — 必须严格执行）

> **背景**：方案A 下脚本不再负责 trafficLights / riskScore / riskLevel / riskAdvice / metrics 综合评级等字段。
> AI 在第二阶段 JSON 生成时，必须按照以下写死的公式和规则直接计算填写，保证一致性和可重现性。

---

#### 红绿灯 trafficLights 7项计算规则

| 指标 | 采集来源 | 绿（green） | 黄（yellow） | 红（red） | threshold 文字 |
|------|---------|------------|-------------|----------|---------------|
| VIX波动率 | Google Finance `VIX:INDEXCBOE` | < 18 | 18 ~ 25 | > 25 | `<18绿 / 18-25黄 / >25红` |
| 10Y美债收益率 | FRED `DGS10` / web_search | < 4.0% | 4.0% ~ 4.5% | > 4.5% | `<4.0%绿 / 4.0-4.5%黄 / >4.5%红` |
| 布伦特原油 | OilPrice.com / web_search | < $90 | $90 ~ $110 | > $110 | `<$90绿 / $90-110黄 / >$110红` |
| 美元指数DXY | Investing.com / web_search | < 102 | 102 ~ 107 | > 107 | `<102绿 / 102-107黄 / >107红` |
| HY信用利差 | FRED `BAMLH0A0HYM2` / web_search | < 4% | 4% ~ 5% | > 5% | `<4%绿 / 4-5%黄 / >5%红` |
| 外资动向 | 港股（恒生+恒生科技）均涨跌幅代理 | 均涨 ≥ +1.5% | 均涨 0~+1.5% | 均跌 < 0% | `以港股（恒生+恒生科技）均涨跌幅为代理：≥+1.5%绿 / 0~+1.5%黄 / 跌红` |
| 离岸人民币CNH | web_search / AkShare | < 7.15 | 7.15 ~ 7.30 | > 7.30 | `<7.15绿 / 7.15-7.30黄 / >7.30红` |

> ⚠️ AI 填写 trafficLights 时，`value` 字段写采集到的实际数值（字符串格式），`status` 字段严格按上表阈值判断，`threshold` 字段复制上表「threshold 文字」列的内容。

---

#### riskScore / riskLevel / riskAdvice 计算公式

**riskScore 公式**：
```
基础分 = 30（代表市场正常背景噪音）
权重：green = 0分 / yellow = 10分 / red = 20分
riskScore = min(100, 30 + Σ各灯颜色权重)

示例：7绿 → 30+0=30分；3黄4绿 → 30+30=60分；7红 → 30+140→封顶100分
```

**riskLevel 规则**：
```
riskScore < 45  → "low"
riskScore < 65  → "medium"
riskScore ≥ 65  → "high"
```

**riskAdvice 模板**（动态生成，不硬编码具体指标描述）：
```
当前风险评分 {riskScore}（{riskLevel}）：
{N}项指标中 {G}绿 / {Y}黄 / {R}红，
具体仓位建议请参考当日简报研判。
```

---

#### metrics 综合评级（watchlist 标的）计算规则

基于 30日涨跌幅 + 单日涨跌幅，规则化计算，可重现：

```
pct_30d = (最新价 - 30日前收盘价) / 30日前收盘价 × 100

pct_30d ≥ 15% 且 单日涨跌 > 0  → ⭐⭐⭐⭐⭐
pct_30d ≥ 5%  或 单日涨跌 ≥ 3%  → ⭐⭐⭐⭐
pct_30d ≥ -5%（-5% ~ +5%）        → ⭐⭐⭐
pct_30d ≥ -15%（-15% ~ -5%）      → ⭐⭐
pct_30d < -15%                     → ⭐
```

> AI 按上述规则计算后填入 `metrics[5].value`（综合评级）。

---

### 第2.5阶段：JSON 完整性终审（强制）

> **此阶段为强制性门禁，不通过则禁止上传。**

**逐文件扫描**：

对 4 个 JSON 文件执行以下检查：

| # | 检查项 | 规则 |
|---|--------|------|
| 1 | **必填字段非空** | 所有 json-schema.md 中标记"必填"的字段不能是 `""`、`[]`、`null`、`"--"` |
| 2 | **枚举值校验** | `direction` ∈ {up, down, flat}，`signal` ∈ {bullish, bearish, neutral}，`trend` ∈ {up, down, hold}，`type` ∈ {hold, add, reduce, buy, sell, watch, hedge, stoploss}（**禁止 bullish/bearish**），`level` ∈ {high, medium, low}，`status` ∈ {green, yellow, red}，`sentimentLabel` ∈ {极度恐惧, 偏恐惧, 中性, 偏贪婪, 贪婪, 极度贪婪}（**禁止「偏悲观」「偏乐观」等非标准值**），`marketStatus` ∈ {美股交易中, 美股已收盘, 盘前交易, 盘后交易, 美股休市} |
| 3 | **数据类型校验** | `change` = number，`sentimentScore` = number，`riskScore` = number，`confidence` = number，`sparkline` = number[]，`chartData` = number[] |
| 4 | **数组长度校验** | `globalReaction` ≥ 5，`coreJudgments` = 3，`trafficLights` = 7，`sparkline` = 7，GICS = 11 |
| 5 | **板块均衡** | watchlist 每个板块至少 2 只标的 |
| 6 | **sparkline 有效性** | 每个 sparkline 数组必须是 7 个正数，不能全为 0 或相同值 |
| 7 | **JSON 语法** | 每个文件必须是合法 JSON（`run_daily.sh` 第0步自动校验）|
| **8** | **chain[].url 非空校验** | `coreEvent.chain[]` 每一条，若 `source` 为非付费墙媒体（非 Bloomberg/FT/WSJ），则 `url` 必须是有效 `https://` 链接，不得为 `""` 或 `null`；逐条检查，一条不过则退回补链接 |
| **9** | **coreJudgments[].references 非空校验** | 每一条 `coreJudgments` 必须存在 `references` 数组且至少有 1 条；每条 reference 必须含 `name`（非空）和 `summary`（非空）；违反则退回补写 |
| **10** | **riskPoints 数组校验** | `riskPoints` 必须是 2-4 条的 string 数组，每条 15-50 字独立风险点；禁止只有 `riskNote` 而缺少 `riskPoints`；禁止单条散文超 100 字（等于没拆分） |

### 第三阶段：sparkline补全 + 上传（一键自动执行）

> **⚠️ 此阶段 AI 必须直接执行命令，无需用户手动操作。**
> JSON 终审通过后，立即运行以下命令——它会自动完成：
> 1. JSON 语法预校验（硬依赖，失败则阻断）
> 2. sparkline/chartData 历史序列补全（**软依赖**，失败时警告+跳过，不阻断）
> 3. 上传到微信云数据库（无论步骤2是否成功，均执行）

**执行命令（AI 直接调用 execute_command）**：

```bash
bash /Users/zewujiang/Desktop/AICo/codebuddy-invest/.codebuddy/skills/investment-agent-daily-app/scripts/run_daily.sh {YYYY-MM-DD}
```

**【方案A 双轨分工】脚本只补全以下字段**（其他所有字段由 AI 在第二阶段直接生成，脚本不触碰）：

| 文件 | 字段 | 数据源 | 说明 |
|------|------|--------|------|
| markets.json | `usMarkets[*].sparkline` | AkShare 新浪源 | 7天收盘价序列 |
| markets.json | `m7[*].sparkline` | AkShare 新浪源 | 7天收盘价序列 |
| markets.json | `asiaMarkets[*].sparkline` | AkShare（新浪/东方财富） | 含上证/深证/恒生/恒生科技/日经 |
| markets.json | `commodities[黄金/原油].sparkline` | AkShare 新浪源 | DXY/10Y/CNH/BTC/ETH 为缺口跳过 |
| watchlist.json | `stocks[*][*].sparkline` | AkShare 新浪源 + 东方财富 fallback | 美股/港股/A股全覆盖 |
| watchlist.json | `stocks[*][*].chartData` | AkShare 新浪源 + 东方财富 fallback | 30天收盘价序列 |

**AI 在第二阶段直接填写（脚本不覆盖）**：

| 字段 | AI 填写规则 |
|------|------------|
| `price` / `change` | 从 Google Finance / OilPrice.com / FRED 等行情源直采（RULE ZERO-A） |
| `metrics` 6项 | 最新价+单日+7日+30日涨跌（来自行情数据）+ PE(TTM)（web_fetch）+ 综合评级（按**第2.3阶段「metrics 综合评级计算规则」**计算） |
| `trafficLights` 7项 | 按**第2.3阶段「红绿灯计算规则」**填写 status |
| `riskScore` / `riskLevel` | 按**第2.3阶段「riskScore 计算公式」**计算 |
| `riskAdvice` | 按**第2.3阶段「riskAdvice 模板」**生成 |
| `globalReaction` 6项 | 从行情数据直接生成 direction（up/down） |
| `gics` 11板块 | 从 Google Finance 采集 11 个 ETF 的涨跌幅 |
| 所有文字字段 | AI 分析撰写，脚本永远不触碰 |

**执行失败处理**：

| 情形 | 行为 | 对数据质量的影响 |
|------|------|----------------|
| JSON 语法错误（第0步） | **阻断**，AI 修复后重新运行 | — |
| yfinance 限速 / 超时（第1步） | 重试1次；仍失败 → **警告+跳过**，继续上传 | sparkline/chartData 为 AI 估算值；其他字段 AI 直接保障，不受影响 |
| 上传失败（第2步） | **阻断**，JSON 文件保留在本地，可手动重传 | — |

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

## 致命错误清单（27条 — 零容忍）

| # | 错误类型 | 说明 |
|---|----------|------|
| 1 | JSON Schema 不匹配 | 字段名错误/缺失/多余 |
| 2 | 训练数据污染 | 数据不来自实时搜索 |
| 3 | 必填字段为空 | `""`、`[]`、`null`、`"--"` |
| 4 | 数据类型错误 | `change` 是 string 而非 number |
| 5 | 枚举值越界 | direction 写了 "rising" 而非 "up" |
| 6 | sparkline 缺失 | markets/watchlist 标的没有 sparkline |
| 7 | sparkline 无效 | 全为 0 或数组长度 ≠ 7 |
| 8 | 空板块 | watchlist 的 4 个核心板块（ai_infra/ai_app/cn_ai/smart_money）中某个 stocks 为空数组 |
| 9 | 红绿灯不足7项 | trafficLights 数组长度 < 7 |
| 10 | GICS 不足11项 | gics 数组长度 < 11 |
| 11 | globalReaction 不足5项 | 核心资产反应不完整 |
| 12 | coreJudgments ≠ 3条 | 必须精确3条判断 |
| 13 | markdown 残留 | JSON 文本字段含 `**`、`\|`、`>`、`- ` 等 md 语法 |
| 14 | JSON 语法错误 | 无法被 `json.loads()` 解析 |
| 15 | 价格数据错误 | 收盘价/涨跌幅与实际不符 |
| 16 | 可选字段枚举值越界 | `keyDeltas[].status` 填了"上涨"而非枚举值（升级/新增/活跃/降温/稳定）——⚠️ keyDeltas 整体已废弃 v2.0，此规则仅在使用旧模板产出 keyDeltas 时适用；`fearGreed.label` 填了"恐惧"而非英文枚举（Extreme Fear/Fear/Neutral/Greed/Extreme Greed）；`predictions[].source` 填了非允许值（仅限 Polymarket/Kalshi/CME FedWatch）；`_meta.sourceType` 填了非枚举值 |
| 17 | 字段内容边界越界 | `keyDeltas[].brief` 写了 coreEvent/globalReaction 中已有的具体数字（如指数涨跌幅）；`coreEvent.chain` 重复了 brief 中已有的具体数字；`marketSummary` 汇总重复了 keyDeltas/coreEvent/globalReaction 中的具体数字 — 三处均有明确的「正确/错误示例」，详见 json-schema.md |
| 18 | 数据时效性错误 | ①`brief` 字段超过25字（应极简10-25字，非长句）；②生成时美股未收盘却在 globalReaction/coreEvent 中使用期货盘前数据并当作收盘数据呈现，未注明「盘前」；③`timeStatus.marketStatus` 填写错误（北京时间19:22=纽约盘前07:22，应填「盘前交易」而非「美股已收盘」）；④`dataTime` 未注明数据时态（盘前/盘中/盘后/收盘） |

| 19 | keyDeltas 热度评级虚高 | 所有 heat≥4 的条目必须符合「宏观/地缘突发冲击、市场结构性拐点、指数级行情驱动事件」定义；战略投资（规模<市值1%）、供应链合作、行业进展等「重要但不紧迫」事件必须降为 heat=3；若一天内 heat≥4 超过2条，必须重审全部 keyDeltas 评级 |

| 20 | coreJudgments.logic 使用段落散文 | `logic` 字段必须使用「短句+箭头（→）三段式」：`触发原因 → 传导路径 → 核心结论`，每段≤15字，整条≤50字；禁止：段落散文、分号连接长句、bullet点（`•`）列举；前端无 💡 图标前缀，文字直接顶格，箭头自带方向感，无需其他修饰符号 |

| 21 | takeaway 缺少【】关键词标红 | takeaway 文本中核心关键词必须用中文方括号【】包裹（3~5个），前端 `parseTakeaway()` 正则提取后渲染为红色高亮；无【】则全段黑色，关键行动指令被淹没；标红过多（≥6个）等于没有重点；选择标红的优先级：行动指令（以防御为主）> 关键条件/数据（VIX回落至20以下）> 事实描述 |

| 22 | **交易数据来源错误（从新闻媒体提取价格）** | **markets.json / watchlist.json 中任何价格、涨跌幅、汇率数字，若来源是新闻媒体文章（Bloomberg/Reuters/CNBC/财经媒体等文本），而非直接行情平台（Google Finance/yfinance/AkShare/OilPrice.com/FRED等），视为违规。<br>典型案例：CNH汇率写7.24（来自训练数据），实际应为6.88；黄金跌幅写-2.38%（来自新闻转述），实际为-0.26%。<br>自查：交易数据能追溯到 `web_fetch URL` 或 `yfinance/AkShare 接口调用` 吗？不能→阻断发布，重新从行情源采集** |

| 23 | **insightChain 数字与字段值不一致** | **`insightChain[].text` 中出现的数字（涨跌幅/价格/百分比）必须与同文件对应字段的 `price`/`change` 完全一致，不允许任何方向矛盾或数值差异。<br>正确做法：先确认 `price`/`change` 字段，再据此写 `text` 内容；禁止从媒体文章独立"记忆"这些数字。<br>同时禁用 web_search snippet 里的价格数字直接写入任何字段（snippet 来源可能是新闻媒体，需 web_fetch 到行情页核实）。** |

| 24 | **`refresh_verified_snapshot.py` 覆盖 AI 文字内容字段** | **【方案A v2.0 已从架构层面根本解决】脚本只允许写 sparkline / chartData 两个数组字段（~200行），其他所有字段脚本永远不读取、不修改。以下为历史审计参考（v2.5之前脚本曾覆盖）：<br>脚本绝对禁止覆盖的 AI 观点字段（已在 v2.5 脚本中彻底删除）：<br>· `alerts` / `riskAlerts` / `smartMoneyDetail` / `sectors`<br>· `coreEvent` / `coreJudgments` / `actions` / `smartMoney` / `riskNote` / `riskPoints` / `sentimentScore` / `sentimentLabel` / `marketSummary` / `takeaway` / `marketSummaryPoints` / `insightChain` / `insight`<br>如果未来修改脚本，检查原则：脚本里任何硬编码的中文分析文本都是危险信号，必须删除。** |

| 25 | **chain[].url 和 coreJudgments[].references 被漏填（可选字段偷懒空置）** | **这是导致简报功能性损坏的致命失误。「可选字段」≠「可以留空」，唯一合法的空置理由是付费墙媒体（Bloomberg/FT/WSJ）无公开链接。<br>强制终审门禁（第2.5阶段必查）：<br>① `coreEvent.chain[]` 每一条：source 填了非付费墙媒体 → url 必须有真实 https 链接，禁止 `""` 或 `null`<br>② `coreJudgments[]` 每一条：必须有 references 数组，每条含 name + summary + url（付费墙 url 可省略）<br>**终审自查口诀：「有 source 必有 url（付费墙除外），有判断必有 references」**<br>典型事故（2026-04-02）：AI 产出时将 chain 全部 4 条 url 留空（`""`），coreJudgments 全部 3 条无 references，导致简报链接全部点击无效，用户无法核实信息来源，严重损伤可信度。** |

| 26 | **riskNote 风险提示为散文段落（未使用 riskPoints 数组）** | **v3.1 起 `riskNote` 已升级为 `riskPoints[]` 数组（2-4条 bullet point）。AI 产出时必须同时输出 `riskPoints`（主）和 `riskNote`（兼容），前端优先渲染 `riskPoints` 数组。<br>禁止：只输出 `riskNote` 而不输出 `riskPoints`；把一整段散文塞进 `riskPoints` 单个元素（等于没拆分）。<br>每条 riskPoints 只说一个风险点（15-50字），最后一条可以是行动建议。<br>前端图标为 🛡️（盾牌），与 🎯⚡🌡️🧠 风格统一，禁止使用 ⚠️（字符感）或 🚨（与重点事件重复）。** |

| 27 | **价格/涨跌幅使用模糊前缀（`~` / `≈` / `约` / `左右`）** | **所有 JSON 中的价格、涨跌幅、汇率数字必须是行情源的精确数值，禁止使用 `~`（波浪号/约等于）、`≈`、`大约`、`左右`、`+` 后缀等任何模糊修饰。<br>根本原因：前端底部显示「更新时间」，用户预期数字与该时间点精确对应；`~$4,677` 这种写法暗示数据不可靠，损伤专业性。<br>适用范围：`globalReaction[].value`、`markets 所有 price 字段`、`watchlist 所有 price 字段`、`trafficLights[].value`、`metrics[].value`。<br>正确示例：`"$4,675"` / `"+7.78%"` / `"4.32%"`<br>错误示例（禁止）：`"~$4,677"` / `"约$4,700"` / `"$4,600+"`<br>典型事故（2026-04-03）：黄金 globalReaction value 写了 `~$4,677`，前端直接渲染出波浪号，大老板质疑数据精度。** |

---

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
{project_root}/workflows/investment_agent_data/miniapp_sync/

# 4个JSON文件：
briefing.json / markets.json / watchlist.json / radar.json
```

> 实际路径：`/Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows/investment_agent_data/miniapp_sync/`

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
| **v4.3** | 2026-04-05 17:37 | **数据源升级：AkShare 替代 yfinance**：①`refresh_verified_snapshot.py` 从 v2.2 升级至 v3.0，主数据源从 yfinance（Yahoo 403 封禁）切换至 AkShare 新浪源 + 东方财富源 fallback；②覆盖率从 0% 提升至 ~89%（41/46 标的）；③新增 A股指数（上证/深证）+ 港股指数（恒生/恒生科技）自动补全；④防限流：逐个调用+0.3s sleep；⑤AkShare 缺口：VIX/DXY/10Y/CNH/BTC/ETH 保留 AI 估算值；⑥`run_daily.sh` 升级至 v3.0；⑦`known-pitfalls.md` v2.3 新增堵点#24；⑧`data-source-priority.md` 升级至 v1.6。 |
| **v4.2** | 2026-04-05 15:30 | **WATCHLIST_YF_MAP 扩展至30只标的**：①删除旧板块6只已下线标的（MRVL/MU/COST/NVO/LLY/JPM）；②新增11只美股（AAPL/GOOGL/META/AMZN/ANET/PLTR/RBLX/TEM/NOW/KO/OXY/AXP）；③新增港股4只（0700.HK/9988.HK/2513.HK/0100.HK）；④新增A股5只（300308.SZ/688256.SZ/300750.SZ/002594.SZ/600519.SS）；⑤`refresh_verified_snapshot.py` 升级至 v2.2；⑥固化 A股 ticker 格式陷阱（上交所 `.SH` → `.SS`）至 `known-pitfalls.md` 堵点#23；⑦SKILL.md 第2.3阶段第5条更新——港股/A股 sparkline 从「AI 手动填」改为「脚本自动补，失败时 AI 再填」。 |
| **v4.1** | 2026-04-05 13:10 | **watchlist 板块架构 v2.0 重构**：旧7板块（ai/semi/internet/energy/consumer/pharma/finance，17只标的）完全废弃，新5板块架构（`ai_infra`/`ai_app`/`cn_ai`/`smart_money`/`hot_topic`），标的总数从17只扩展至约30只；新增 `badges` 特殊标签系统；新增未上市标的支持（`listed: false`）；新增 `hot_topic` 动态板块；RULE FIVE 更新。 |
| **v4.0** | 2026-04-05 12:05 | **三档内容引擎 — 小程序"永远在线"**：①从"交易日才执行"升级为365天均可产出，新增 Heavy（交易日盘后全量）/ Weekend（周末深度洞察）/ Live（盘中增量，TODO v5.0）三档模式路由；②Weekend 模式规范：无行情时保留上一交易日市场数据不伪造，内容切换为周度总结+深度分析+下周展望+事件日历前瞻，采集精简为W0~WA五批次（10-15次搜索 vs Heavy的50+次），`_meta.sourceType` 新增 `weekend_insight` 枚举；③第零阶段从"周末不执行"改为三档模式智能路由；④内容品质标准不因模式降级——周末深度分析应比日度更有洞察（有更多时间思考），文字精炼度和信息密度标准不变。 |
| **v3.1** | 2026-04-05 11:48 | **风险提示 bullet point 升级 + 精确数值强制规则**：①`riskNote` 散文升级为 `riskPoints[]` 数组（2-4条），前端 `wx:for` 循环+红色圆点渲染；保留旧版 `riskNote` 字段兜底（前端按句号自动拆分）；②图标从 ⚠️ 更换为 🛡️（盾牌），与全页 emoji 风格统一，不与重点事件 🚨 重复；③所有价格/涨跌幅字段禁止 `~` / `≈` / `大约` 等模糊前缀（典型事故：黄金 `~$4,677` → `$4,675`）；④致命错误清单新增第26条（riskPoints）+第27条（模糊数值）；⑤`json-schema.md` 升级至 v2.2、`known-pitfalls.md` 升级至 v2.0（新增堵点#20）。 |
| **v3.0** | 2026-04-03 20:00 | **方案A — 双轨分工架构**：①`refresh_verified_snapshot.py` 重写为 v2.0 → v2.1（批量下载优化） — 从 600+行缩减至 ~200行，只用 yfinance 单一依赖（移除 AkShare/FRED/新浪），只写 sparkline(7天)/chartData(30天) 两个数组字段，briefing.json/radar.json 完全不读取不修改；②`run_daily.sh` 升级至 v2.0 — 说明文字与方案A对齐；③SKILL.md 新增「第2.3阶段：AI直填公式」——trafficLights 7项阈值表、riskScore/riskLevel/riskAdvice 计算公式、metrics 综合评级规则全部写死，AI 第二阶段直接按公式填写；④消除了历史上所有脚本覆盖AI数据的风险根源（v1.3曾删三块硬编码、v2.5删sectors等），从架构层面彻底解决。 |
| **v2.7** | 2026-04-03 19:10 | **API 校正改为软依赖（方案 Alpha）**：①`run_daily.sh` 升级至 v1.2 — 第1步（API校正）失败时改为「警告+跳过+继续上传」，不再 `exit 1` 阻断全流程；第0步（JSON语法校验）和第2步（上传）仍为硬依赖；脚本末尾完成提示根据校正是否成功输出不同数据来源声明；②`SKILL.md` 第三阶段重写为分层依赖设计（第0/2步硬依赖 + 第1步软依赖），补充「执行失败处理」四情形对照表及「软依赖设计理由」；③`known-pitfalls.md` 升级至 v1.8 — 新增堵点#18（API 软依赖运行机制说明）。**设计根因**：yfinance/AkShare 偶发限速不应让小程序当天无数据；AI+搜索对 price/change 已独立保障精度；sparkline/chartData 是 API 唯一不可替代的增值价值，失败时降级为 AI 估算兜底，远优于全流程阻断。 |
| **v2.6** | 2026-04-03 18:37 | **封堵「可选字段偷懒空置」漏洞（来源：2026-04-02 产出事故）**：①`SKILL.md` 致命错误清单新增第25条（chain[].url 和 coreJudgments[].references 漏填，含事故复盘和强制自查口诀「有 source 必有 url（付费墙除外），有判断必有 references」）；②第2.5阶段终审清单新增第8项（chain[].url 非空逐条校验）和第9项（coreJudgments[].references 非空校验），从流程层面强制拦截；③`known-pitfalls.md` 升级至 v1.7 — 新增堵点#17（chain[].url/references 漏填）；**根本原因**：原终审清单只检查 length/type/enum，未检查可选字段是否真实填写，导致带病上线。 |
| **v2.5** | 2026-04-03 17:18 | **校正脚本彻底清除硬编码观点数据（v1.3）**：①`refresh_verified_snapshot.py` 升级至 v1.3 — 删除 `update_radar()` 中 `alerts`（含4月1日旧数字NVDA 174.40/上证3948/布伦特103.31）/ `riskAlerts`（固定概率30%/25%/20%）/ `smartMoneyDetail`（含伯克希尔479.20旧股价）三块硬编码，这三个字段完全由 AI 每日填写，脚本永远不触碰；②删除 `update_watchlist()` 中 `sectors` 七板块硬编码（含旧日期旧股价文字），板块观点完全由 AI 负责；③`riskAdvice` 改为基于当日灯色统计动态生成模板句（"X绿/Y黄/Z红"），不再描述具体指标状态，消除文字与实际灯色矛盾风险；④`SKILL.md` 致命错误清单第24条补充 `alerts` / `riskAlerts` / `smartMoneyDetail` / `sectors` 到禁止覆盖清单；⑤脚本 docstring 明确"观点数据轨"与"交易数据轨"双轨边界。 |
| **v2.4** | 2026-04-03 10:55 | **交易数据/新闻数据严格隔离**：①新增 RULE ZERO-A — 交易数据（价格/涨跌幅/汇率/sparkline）只允许直接行情API，禁止从新闻媒体文章反向提取；②致命错误清单新增第22条（交易数据来源错误），含典型案例（CNH汇率7.24→实际6.88；黄金跌幅-2.38%→实际-0.26%）；③`data-collection-sop.md` 升级至 v1.4 — 新增第零章「数据分类隔离规则」和批次前置校验清单；④`data-source-priority.md` 升级至 v1.4 — 重写为交易数据轨/观点数据轨双轨体系，明确交叉污染禁止清单。 |
| **v2.3** | 2026-04-03 10:29 | **takeaway 关键词标红机制固化**：①`takeaway` 字段中核心关键词必须用中文方括号【】包裹（3~5个），前端 `parseTakeaway()` 正则 `/【([^】]+)】/g` 提取后渲染为红色高亮（`.takeaway-highlight { color: #e74c3c; font-weight: 700 }`）；无【】则全段纯黑，关键行动指令被淹没；②`json-schema.md` 升级至 v2.0 — takeaway 字段注释新增标红机制说明、标红原则（3~5个，优先行动指令和关键条件/数据）、正/错误示例（含过多标红的反例）；③`known-pitfalls.md` 升级至 v1.6 — 新增堵点#16（takeaway缺少标红，含根本原因+强制规则+双向错误示例）；④`SKILL.md` 致命错误清单新增第21条（takeaway标红缺失零容忍）。 |
| **v2.2** | 2026-04-02 23:01 | **核心判断呈现质量升级**：①`coreJudgments.logic` 字段强制「短句+箭头（→）三段式」格式（触发原因→传导路径→核心结论），禁止段落散文/分号长句/bullet列举；每段≤15字，整条≤50字；②前端 `briefing.wxml` 移除 💡 灯泡图标（`logic-icon`），logic 文字直接顶格，`briefing.wxss` 同步删除 `.logic-icon` 样式；③`json-schema.md` 升级至 v1.9 — logic 字段注释新增强制格式、正/错误示例、字数要求、前端渲染说明；④`known-pitfalls.md` 升级至 v1.5 — 新增堵点#15（核心判断散文式呈现，含正/错误示例+前端渲染说明）；⑤`SKILL.md` 致命错误清单新增第20条（logic段落散文零容忍）。 |
| **v2.1** | 2026-04-02 22:41 | **小程序呈现质量全面升级**：①`actions.type` 枚举从方向判断（bullish/bearish）改为具体操作动词（hold/add/reduce/watch/hedge/stoploss），前端 color.js 同步扩展标签映射；②`marketSummary` 字符串升级为 `marketSummaryPoints` 数组（3-5条 bullet），对齐重点事件阅读风格，前端兼容旧格式自动拆分；③新增来源链接规范——严禁跨媒体伪造链接，Bloomberg/FT/WSJ 等付费墙媒体无公开链接时只填 source 不填 url，前端自动显示灰色不可点样式（chain-link-no-url）；④json-schema.md v1.8、known-pitfalls.md v1.4 同步升级。 |
| **v2.0** | 2026-04-02 21:21 | **删除** `keyDeltas[]` 字段（整个 KEY DELTA 模块已从简报页移除）；**新增** `takeaway`；**升级** `coreEvent.chain[]` 对象化；**升级** `globalReaction[]` 新增 note；**升级** `actions` 新增 reason；**修改** 标签名 |
| **v1.9** | 2026-04-02 20:49 | **热度三档标准全链路系统内化**：①`color.js` `getHeatLabel()` 从旧5档逻辑（加速中/活跃/关注/降温/平淡）重写为新三档逻辑（加速/活跃/关注），与 `briefing.js` 前端渲染完全对齐，并补充详细注释说明三档规则；②`json-schema.md` 升级至 v1.6 — `heat` 字段注释新增「前端颜色对应」规范表（加速→#c0392b血红/.kd-dot.hot；活跃→#f1c40f黄色/.kd-dot.active；关注→#555深灰/默认），含 WXML 渲染代码片段，让新开发前端页面时无需反向查 wxss；③`known-pitfalls.md` 升级至 v1.3 — 新增堵点#12「keyDeltas热度评级虚高」，明确三档判断边界、错误类型（战略投资、供应链合作≠加速），以及「一天内heat≥4超2条必须重审」自查规则；④`SKILL.md` 致命错误清单新增第19条（热度评级虚高零容忍）。 |
| **v1.8** | 2026-04-02 20:41 | **热度三档评级标准固化**：①`json-schema.md` `keyDeltas[].heat` 字段注释新增三档评级判断规则 — 加速（heat≥4）对应宏观/地缘突发冲击、市场结构性拐点、指数级行情驱动事件；活跃（heat=3）对应重要但不紧迫的行业进展、企业战略投资（规模<市值1%）；关注（heat≤2）对应背景信息、趋势性缓慢演变；附正/错误示例防止评级虚高；②`briefing.json` 数据层将"NVIDIA $20亿投资Marvell"从 heat:4 降为 heat:3（属战略生态布局，非突发市场冲击，前端由3点加速→2点活跃）。 |
| **v1.7** | 2026-04-02 20:06 | 修复前端纽约时间计算Bug（根本原因修复）：`format.js` `getMultiTimezone()` 中 `estOffset` 符号方向错误——`estOffset` 为负数（EDT=-240），旧代码用 `- estOffset` 变成 `+240`（UTC+4），导致纽约时间错8小时（实际显示16:06而非08:06）；修复为与 `bjt` 同一模式的 `+ estOffset`（UTC-4），计算结果正确；同步在 json-schema.md 中新增时区换算快速验证规则（夏令时：纽约=北京-12h；冬令时：北京-13h）防止人工填写时再犯。 |
| **v1.6** | 2026-04-02 20:02 | 数据时效性与格式规范修复（源自实测反馈）：①致命错误清单新增第18条（数据时效性错误）— `brief` 字段超过25字、使用盘前期货数据未注明时态、`timeStatus.marketStatus` 填写与实际时间不符、`dataTime` 未标注盘前/盘中/盘后/收盘；②json-schema.md 升级至 v1.5 — `brief` 字长由30-80字收紧为10-25字极简风格（大老板阅读习惯，类似图片中伊朗简报样式），附正确示例；③`timeStatus.marketStatus` 增加完整时区判断规则注释（BJT与EDT/EST对照表），防止时区计算错误导致开市状态标注错误；④`dataTime` 格式规范新增时态标注要求，美股非收盘数据必须注明「盘前」或「盘后」。 |
| **v1.5** | 2026-04-02 18:24 | 字段内容边界规范治本升级（防信息冗余）：①json-schema.md 升级至 v1.4 — `keyDeltas[].brief` 重定义为专写「为何重要/影响方向/市场逻辑」，禁止重复 coreEvent/globalReaction 中具体数字；`coreEvent.chain[]` 重定义为因果逻辑推演，禁止重复 brief 中具体数字；`marketSummary` 重定义为情绪结构判断+核心风险/下一变量，禁止汇总重复各区块具体数字；三处均附正确/错误示例；marketSummary 字长限制收紧为50-120字；②致命错误清单新增第17条（字段内容边界越界）。目标：面向10亿+个人投资者大老板，消除简报首页 keyDeltas/coreEvent/marketSummary 之间同一数字重复出现4次的信息冗余，每个区块各司其职、互不重叠。 |
| **v1.4** | 2026-04-02 12:34 | Skill 数据采集端全面对齐 v1.3 新字段，补齐 SOP 与模板空白地带：①`data-collection-sop.md` 升级至 v1.3 — 新增第八章"Batch A 情绪与预测数据采集SOP"（四子批次：CNN Fear&Greed API / Polymarket CLOB API / Kalshi API / CME FedWatch 页面；含字段映射、失败处理、汇总规则）；采集批次总览表新增 Batch A 行（适用全工作日，可选非阻断）；验证门禁扩展第18-22项可选字段建议检查（⭐ 非阻断）；明确 keyDeltas 为 JSON 生成阶段 AI 提炼，非行情直采；②`data-source-priority.md` 升级至 v1.3 — 新增"一-A章"情绪与预测数据源优先级（CNN F&G / Polymarket / Kalshi / CME FedWatch 四类数据源定义、接口说明、字段映射注释）；降级路径表新增 4 条情绪数据降级路径（全部非阻断型）；③`daily-standard.json` 模板升级至 v1.3 — 补充 briefing 的 timeStatus/keyDeltas/_meta 完整占位示例；markets 的6个板块Insight空字符串占位；radar 的 fearGreed/predictions/_meta 完整占位示例；coreJudgments 三条示例均补充 keyActor/references/probability/trend 可选扩展字段；_field_notes 字段集中声明所有枚举值供 AI 参考；④`monday-special.json` 模板升级至 v1.3 — 与 daily-standard 结构完全对齐，_note 补充周一额外执行 Batch A 说明；⑤`SKILL.md` 致命错误清单新增第16条（可选字段枚举值越界）；第一阶段采集批次概要表新增 Batch A 行；第1.5阶段门禁扩展第18-22项可选字段建议检查。 |
| **v1.3.2** | 2026-04-02 00:21 | 市场页板块 Insight 升级：①json-schema.md 新增 6 个板块级 Insight 字段（usInsight/m7Insight/asiaInsight/commodityInsight/cryptoInsight/gicsInsight），每个板块数据表格底部提供30-80字高质量一句话洞察，对齐日报"XX信号"风格；②原 usMarkets[0].note 迁移为独立 usInsight 字段，前端向后兼容；③markets.wxml 6个Tab/GICS均加入💡洞察卡片（复用 .market-comment 样式）；④markets.js _applyData 传递6个insight+向后兼容旧note；⑤markets-mock.js 补充6个高质量示例文本；⑥data-collection-sop.md 新增第七章"板块Insight生成规范"+门禁第17项验证。 |
| **v1.3.1** | 2026-04-02 00:00 | UI精修三项：①删除简报页顶部hero冗余渐变区域（导航栏已有标题+日期），页面更简洁；②修复判断扩展区 jx-divider 虚线样式（dashed→渐变淡化实线），视觉更优雅；③json-schema.md 中 references 从 string[] 升级为 object[]（含 name/summary/url），briefing 前端改为可点击展开的手风琴组件，展开后显示信息摘要和来源链接，向后兼容旧格式纯字符串数组。相关文件：briefing.js（删除 currentDate + 新增 expandedRefs/onRefToggle + references 兼容映射）、briefing.wxml（删除 hero + 重写 Reference 区域）、briefing.wxss（删除 hero 样式 + 修复虚线 + 新增展开面板样式）。 |
| **v1.3** | 2026-04-01 22:58 | 前端体验升级（阶段一）：①json-schema.md 升级至 v1.3 — briefing.json 新增 `timeStatus`（多时区+开市状态）、`keyDeltas[]`（增量信息 KEY DELTA，借鉴 Iran Briefing 设计）、`coreJudgments` 扩展 `keyActor/references/probability/trend` 四个可选字段；radar.json 新增 `fearGreed`（CNN Fear & Greed 情绪指数）、`predictions[]`（预测市场概率 Polymarket/Kalshi/CME FedWatch）；所有 JSON 新增 `_meta` 元数据对象；②小程序前端 v5.0 — 简报页新增时间状态栏（前端实时计算双时区+开市判断）、KEY DELTA 卡片（热度点+状态标签）、核心判断扩展行（决策者/参考源/概率/趋势标签）；雷达页新增 Fear & Greed 情绪卡片（渐变情绪条+数字跳动动画+三时段对比）、预测市场预览卡片（概率进度条+24h 趋势）；③简报页和雷达页数据底栏统一升级为双层状态栏（数据源+新鲜度+sourceType 标签+Skill 版本号）；④format.js 新增 `getMultiTimezone()`/`getMarketStatus()`/`getRelativeTime()`；⑤color.js 新增 `getDeltaStatusInfo()`/`getFearGreedInfo()`/`getPredictionTrendInfo()`/`getProbabilityInfo()`/`getJudgmentTrendInfo()`/`getHeatLabel()`。所有新字段均为可选（🔸标记），完全向后兼容旧数据。 |
| **v1.2** | 2026-04-01 | 数据质量六项深度治理：①CNH改用`ak.forex_hist_em("USDCNH")`真实离岸源，移除CNY=X混用；②日经/KOSPI新增`MARKET_SANITY_RANGE`量级校验+日经AkShare备用通道；③watchlist metrics升级为方案C（最新价/单日/7日/30日涨跌+PE(TTM)+`calc_star_rating()`规则化综合评级）；④北向资金红绿灯改为「外资动向」（港股均涨跌代理，`calc_foreign_capital_proxy()`），根因：2024-08-19交易所永久停止披露净买额；⑤阈值逻辑标准化为`TRAFFIC_LIGHT_RULES`常量+`auto_traffic_status()`程序化判断；⑥riskScore改为`calc_risk_score()`动态计算（权重公式：30+Σ灯色权重，上限100）；⑦upload_to_cloud.py新增`verify_upload()`上传后回读校验（7字段+数组长度+dataTime一致性）。 |
| **v1.0** | 2026-04-01 | 初始版本。从 `investment-agent-daily` v19.0 独立分支：①复用核心数据采集逻辑（6大铁律、数据源、采集批次）；②全新 JSON Schema 精确对齐小程序4页面（briefing/markets/watchlist/radar）；③新增 sparkline/chartData/metrics/analysis 等 MD 报告不需要但小程序需要的数据；④新增 stock-universe.md（7板块标的池）；⑤复用 upload_to_cloud.py |
