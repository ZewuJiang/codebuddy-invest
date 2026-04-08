# Refresh 模式内容规范（v1.0）

> **用途**：工作日每4小时增量刷新执行时的完整内容规范。从 SKILL.md 外迁以减少 Heavy 模式执行时的认知负荷。
> **触发条件**：工作日（周一～周五）且当天 miniapp_sync/ 目录下已有4个 JSON 文件（即当天 Heavy 已执行过）
> **典型执行时间**：北京时间 10:00 / 14:00 / 18:00 / 22:00（06:00 走 Heavy，后续走 Refresh）

---

## 设计哲学

> **大老板每次打开小程序，行情数据都是新鲜的，深度分析保持一天一次的权威质量。**
>
> Refresh 模式的核心思路是「**更新行情、保留分析**」——与 Weekend 模式的「保留行情、更新分析」恰好互补。
> Heavy 版是当天的"定海神针"，Refresh 只在此基准上刷新时效性最强的数据层，绝不降低分析内容的质量和深度。

**三条红线（不可逾越）**：
1. **数据铁律不降级**：RULE ZERO / ZERO-A / ZERO-B 在 Refresh 模式下同样有效，行情数据必须来自实时行情源，禁止凭记忆
2. **保留字段零篡改**：Refresh 不得修改任何保留字段，即使 AI 认为"可以写得更好"——保留字段的质量由 Heavy 模式终审保障
3. **结构完整性不破坏**：Refresh 产出的 JSON 必须 100% 对齐 json-schema.md，不新增、不缺失、不改名字段

**第四条红线（2026-04-07 新增，血泪教训）**：
4. **事件状态时效性强制校验**：R0 阶段必须执行"事件状态比对"——将当前时间与 Heavy 版 coreEvent/riskPoints 中的时效性文字对比，若发现过期描述（如"今夜到期"已到期、"待定"事件已发生），**必须强制更新 briefing.json 的以下字段**：
   - `takeaway`（从🔒升级为⚠️条件更新）
   - `coreEvent.title`（从🔒升级为⚠️条件更新）
   - `coreEvent.chain[]`（末尾追加"已发生"事件节点）
   - `riskPoints[]`（从🔒升级为⚠️条件更新）
   - `riskNote`（从🔒升级为⚠️条件更新）
   - `marketSummaryPoints[]`（从🔒升级为⚠️条件更新）
   - `actionHints[]`（从🔒升级为⚠️条件更新）

   **触发条件（满足任意一条即触发）**：
   - coreEvent/riskPoints 中含有时效性词汇（"今夜""今日""即将""最后通牒到期""待定""可能发生"），且事件时间已过
   - R0 搜索发现事件已以某种方式落地（无论升级/降级/取消），与 Heavy 版预期不符
   - riskScore 在本次 Refresh 中发生了 ≥20 分的变化（如从80→100），说明局势有重大变化，文案必须同步

---

## 模式判定逻辑

```
定时任务触发（工作日）
  → Step 1: 当天 miniapp_sync/ 目录下是否已有 4 个 JSON 文件？
    → 否 → Heavy 模式（当天首次执行，全量采集+生成）
    → 是 → Step 2: 读取基准 JSON 的 _meta.sourceType
      → "heavy_analysis" 或 "refresh_update" → Refresh 模式
      → "weekend_insight" → Heavy 模式（周一首次应覆盖周末版）
```

**降级安全网**：
- 如果 Refresh 模式启动后发现基准 JSON 不完整（缺少文件或核心字段为空），自动降级为 Heavy 模式
- 如果 Refresh 采集过程中发现重大突发事件（如战争升级、央行紧急降息），不自动升级——用户手动触发 Heavy 即可

---

## 数据采集（精简版 — R0~R3）

> **核心原则**：只采集时效性强的行情+突发事件数据，聪明钱/深度分析/事件日历等低频内容完全跳过。

| 批次 | 内容 | 搜索次数 | 数据源 |
|------|------|---------|--------|
| **R0** | 快扫头条：是否有重大突发事件？ | 1-2次 web_search | 一级必扫媒体（Bloomberg/Reuters/WSJ 标题扫描） |
| **R1** | 美股行情刷新：三大指数 + VIX + M7（价格/涨跌幅） | 3-4次 web_fetch | Google Finance |
| **R2** | 亚太/大宗/汇率/加密行情刷新 | 1-2次 web_search | 东方财富/OilPrice.com/web_search |
| **R3** | 异动信号检查：有无新的 alerts 需要替换？ | 0-1次 web_search | 基于 R0 判断是否需要 |

**搜索总量**：Refresh ≥ 2次 web_search + 4次 web_fetch（最低基线）
**对比**：Heavy ≥ 50次搜索 / Weekend ≥ 10-15次搜索 / **Refresh ≥ 6-8次搜索（含 web_fetch）**

### 各批次详细说明

#### R0 — 快扫头条（必执行）

```
web_search: "breaking news markets today YYYY-MM-DD"
web_search: "美股 最新消息 今日" （可选，亚洲时段补充）
```

**目的**：判断自上次执行以来是否发生重大突发事件。
**判断标准**：
- 有重大突发（战争升级/央行紧急行动/黑天鹅事件）→ 后续 R1/R2 正常执行 + 更新 alerts + 考虑更新 coreEvent.chain
- 无重大突发 → 后续 R1/R2 正常执行，alerts/coreEvent 保留基准版

**【新增 v1.2】事件状态时效性强制比对（R0 必做，不可跳过）**：
```
Step R0-B：读取基准 briefing.json 的以下字段：
  - coreEvent.title / coreEvent.chain[-1].title
  - riskPoints[]
  - actionHints[0].content

检查是否含有以下时效性词汇：
  "今夜" / "今日" / "即将" / "最后通牒到期" / "待定" / "可能发生" / "尚未" / 具体时间点（如"20:00"）

若包含 → 比对当前时间，判断该事件是否已发生或已过期
  → 已发生/已过期 → 标记为"需要更新"，在R3阶段执行相应字段的条件更新
  → 未发生 → 继续保留

同时检查 riskScore 变化幅度：
  若本次 Refresh 计算出的 riskScore 与基准 riskScore 差值 ≥20 → 标记"需要更新"
```

#### R1 — 美股行情刷新（必执行）

```
# 三大指数 + VIX
web_fetch: https://www.google.com/finance/quote/.INX:INDEXSP
web_fetch: https://www.google.com/finance/quote/.IXIC:INDEXNASDAQ
web_fetch: https://www.google.com/finance/quote/.DJI:INDEXDJX
web_fetch: https://www.google.com/finance/quote/VIX:INDEXCBOE

# M7（可用1次web_search批量获取，或逐个web_fetch）
# 如果时间紧张，优先采集指数+VIX，M7可用上次数据
```

**产出**：更新 markets.json 的 usMarkets/m7 的 price/change 字段
**注意**：
- 盘前时段（北京时间 18:00 = 美东 06:00）：标注 marketStatus = "盘前交易"，价格来自盘前数据
- 盘中时段（北京时间 22:00 = 美东 10:00）：标注 marketStatus = "美股交易中"，价格为实时盘中价
- 已收盘时段（北京时间 10:00/14:00）：价格与 Heavy 版一致，仅更新 dataTime

#### R2 — 亚太/大宗/加密行情刷新（必执行）

```
web_search: "亚太股市 今日行情 上证 恒生 日经"
web_search: "gold price brent oil DXY today"
```

**产出**：更新 markets.json 的 asiaMarkets/commodities 的 price/change 字段
**注意**：
- 亚太盘中（北京时间 10:00）：亚太行情为实时数据
- 亚太收盘后（北京时间 14:00+）：亚太行情为当日收盘数据，与 Heavy 可能不同（因 Heavy 在 06:00 采集时亚太尚未开盘）
- 大宗商品/加密货币全天交易，每次 Refresh 都应有最新数据

#### R3 — 异动信号检查 + 文案时效更新（条件执行）

**触发条件 A**：R0 发现重大突发事件时才执行异动信号更新
**产出 A**：更新 radar.json 的 alerts[] 数组

**触发条件 B（v1.2 新增）**：R0-B 标记了"需要更新"的字段
**产出 B**：更新 briefing.json 的以下条件字段（根据实际情况选择需要更新的）：
- `takeaway`：重写，反映事件最新状态（已发生/已解除/已升级）
- `coreEvent.title`：更新标题
- `coreEvent.chain[]`：末尾追加"【已发生/已解除】..."节点
- `riskPoints[]`：全部重写，去掉"今夜/即将"等时效词，改为事后陈述
- `riskNote`：同步更新
- `marketSummaryPoints[]`：同步更新
- `actionHints[]`：将"密切关注"类建议升级为"执行对冲/持有/减仓"类行动建议

```
# 仅当 R0 发现突发事件时执行 A
web_search: "{突发事件关键词} latest impact markets"

# 仅当 R0-B 标记需要更新时执行 B（无需额外搜索，基于已有的 R0+riskScore 数据重写文案）
```

**未触发时**：alerts[] 保留基准 JSON 的内容不变；上述文案字段保留不动

---

## 字段刷新范围边界表（核心——严格执行）

### briefing.json

| 字段 | Refresh 行为 | 说明 |
|------|-------------|------|
| `date` | 🔄 更新 | 写当天日期 |
| `dataTime` | 🔄 更新 | 写 Refresh 执行时间（如 "2026-04-07 10:00 BJT"） |
| `timeStatus` | 🔄 更新 | 重新计算 bjt/est/marketStatus；**`refreshInterval` 从 `"每日更新"` 改为 `"每4小时更新"`**（Refresh 模式标识） |
| `takeaway` | ⚠️ 条件更新 | **默认保留**；但触发第四条红线时必须更新（事件状态过期/riskScore变化≥20分） |
| `coreEvent.title` | ⚠️ 条件更新 | **默认保留**；触发第四条红线时必须更新标题反映事件最新状态 |
| `coreEvent.brief` | 🔒 保留 | 极简摘要不变 |
| `coreEvent.chain[]` | ⚠️ 条件更新 | **仅当 R0 发现重大突发事件或事件已落地时**，在 chain 末尾追加新事件（不删除原有事件）；无突发则保留 |
| `globalReaction[]` | 🔄 更新 | 刷新 value/direction（行情变了，资产反应自然要变）；note 保留 |
| `coreJudgments[]` | 🔒 保留 | 3条深度判断一天不变 |
| `actionHints[]` | ⚠️ 条件更新 | **默认保留**；触发第四条红线时（事件已落地/riskScore封顶）必须更新操作建议 |
| `sentimentScore` | ⚠️ 微调 | 允许基于最新行情微调 ±5 分，但不得大幅偏离 Heavy 版。**微调触发条件**：①VIX 变化 >3 点（每3点 ≈ ±2分）；②标普500 变化 >1.5%（每1.5% ≈ ±2分）；③出现重大突发事件（R0 判定有突发 → ±3-5分）。**无触发条件时保持原值不动** |
| `sentimentLabel` | ⚠️ 联动 | 若 sentimentScore 微调后跨越枚举阈值，则同步更新 |
| `riskNote` | ⚠️ 条件更新 | **默认保留**；触发第四条红线时必须更新反映最新风险状态 |
| `riskPoints[]` | ⚠️ 条件更新 | **默认保留**；触发第四条红线时（riskScore变化≥20或事件已落地）必须更新 |
| `marketSummaryPoints[]` | ⚠️ 条件更新 | **默认保留**；触发第四条红线时必须同步更新 |
| `smartMoney[]` | 🔒 保留 | 聪明钱建议一天不变 |
| `topHoldings[]` | 🔒 保留 | 持仓参考季度更新 |
| `voiceText` | 🔒 保留 | 语音文稿 Heavy 版 |
| `audioUrl` / `audioFile` | 🔒 保留 | 语音文件 Heavy 版 |
| `_meta` | 🔄 更新 | sourceType="refresh_update"，generatedAt=当前时间 |

### markets.json

| 字段 | Refresh 行为 | 说明 |
|------|-------------|------|
| `date` | 🔄 更新 | 当天日期 |
| `dataTime` | 🔄 更新 | Refresh 执行时间 |
| `usMarkets[].price/change` | 🔄 更新 | 美股行情刷新 |
| `usMarkets[].sparkline` | 🔒 保留 | 7天日线不变 |
| `m7[].price/change` | 🔄 更新 | M7 行情刷新 |
| `m7[].sparkline` | 🔒 保留 | 7天日线不变 |
| `asiaMarkets[].price/change` | 🔄 更新 | 亚太行情刷新 |
| `asiaMarkets[].sparkline` | 🔒 保留 | 7天日线不变 |
| `commodities[].price/change` | 🔄 更新 | 大宗/汇率/加密行情刷新 |
| `commodities[].sparkline` | 🔒 保留 | 7天日线不变 |
| `usInsight` ~ `gicsInsight` | 🔒 保留 | 6个 Insight 一天不变 |
| `gics[]` | 🔒 保留 | GICS 11板块一天不变（盘后才有意义） |
| `gicsSummary` | 🔒 保留 | 板块轮动摘要不变 |
| `_meta` | 🔄 更新 | sourceType="refresh_update"，generatedAt=当前时间，refreshCount=当天第N次 Refresh |

### watchlist.json

| 字段 | Refresh 行为 | 说明 |
|------|-------------|------|
| `date` | 🔄 更新 | 当天日期 |
| `dataTime` | 🔄 更新 | Refresh 执行时间 |
| `sectors[].stocks[].price/change` | 🔄 更新 | 标的行情刷新 |
| `sectors[].stocks[].metrics[0]`（最新价） | 🔄 联动更新 | 必须与 price 保持一致 |
| `sectors[].stocks[].metrics[1]`（单日涨跌） | 🔄 联动更新 | 必须与 change 保持一致（含正负号+%） |
| `sectors[].stocks[].metrics[2-5]` | 🔒 保留 | 7日/30日涨跌+PE+评级一天不变 |
| `sectors[].stocks[].sparkline` | 🔒 保留 | 7天日线不变 |
| `sectors[].stocks[].chartData` | 🔒 保留 | 30天日线不变 |
| `sectors[].stocks[].analysis` | 🔒 保留 | 分析文本不变 |
| `sectors[].stocks[].reason` | 🔒 保留 | 入选理由不变 |
| `sectors[].stocks[].risks[]` | 🔒 保留 | 风险提示不变 |
| `sectors[].stocks[].tags[]` | 🔒 保留 | 标签不变 |
| `sectors[].stocks[].badges[]` | 🔒 保留 | 徽章不变 |
| `sectors[].summary` | 🔒 保留 | 板块摘要不变 |
| `_meta` | 🔄 更新 | sourceType="refresh_update"，refreshCount=当天第N次 |

### radar.json

| 字段 | Refresh 行为 | 说明 |
|------|-------------|------|
| `date` | 🔄 更新 | 当天日期 |
| `dataTime` | 🔄 更新 | Refresh 执行时间 |
| `trafficLights[]` | 🔄 更新 | 7项指标的 value/status 重新采集+重算 |
| `riskScore` | 🔄 更新 | 基于新 trafficLights 按公式重算 |
| `riskLevel` | 🔄 更新 | 基于新 riskScore 按规则重算 |
| `riskAdvice` | 🔄 更新 | 基于新红绿灯状态重新生成（遵循去操作化规范） |
| `alerts[]` | ⚠️ 条件更新 | R0 发现重大突发 → 替换/新增；无突发 → 保留基准版 |
| `smartMoneyDetail[]` | 🔒 保留 | 聪明钱动向一天不变 |
| `smartMoneyHoldings[]` | 🔒 保留 | 持仓排行季度更新 |
| `events[]` | 🔒 保留 | 本周前瞻一周不变 |
| `riskAlerts[]` | 🔒 保留 | 保持空数组 [] |
| `predictions[]` | 🔒 保留 | 预测市场数据一天不变 |
| `_meta` | 🔄 更新 | sourceType="refresh_update"，refreshCount=当天第N次 |

---

## JSON 产出规则

### 共同规则

1. **读取基准 JSON**：必须读取当天 miniapp_sync/ 目录下已有的 4 个 JSON 文件作为基准
2. **`date` 字段**：写当天日期（如 "2026-04-07"），与基准 JSON 相同
3. **`dataTime` 字段**：写 Refresh 执行时间（如 "2026-04-07 14:00 BJT"），明确标注更新时间
4. **`_meta.sourceType`** = `"refresh_update"`
5. **`_meta.generatedAt`**：写当前执行时间的 ISO8601 格式（+08:00）
6. **`_meta.skillVersion`**：与当前 SKILL.md 版本号一致
7. **`_meta.refreshCount`**（v1.1 新增）：当天第几次 Refresh（如 1=10:00首次/2=14:00/3=18:00/4=22:00），便于调试追溯。判断方法：若基准 JSON `_meta.sourceType` = `"heavy_analysis"` → refreshCount=1；若 = `"refresh_update"` → refreshCount = 基准的 refreshCount + 1
8. **`timeStatus.refreshInterval`**（v1.1 新增）：Refresh 模式写 `"每4小时更新"`（Heavy 版写 `"每日更新"`），让用户知道数据是高频刷新的

### 产出流程

```
1. 读取基准 JSON（4个文件）
2. 执行精简采集（R0~R3）
3. 将采集到的新数据覆盖到刷新字段
4. 保留字段从基准 JSON 原样拷贝（禁止任何修改）
5. 重算公式字段（trafficLights.status / riskScore / riskLevel / riskAdvice / sentimentScore微调）
6. 更新元数据字段（date / dataTime / _meta）
7. 输出4个完整 JSON 到 miniapp_sync/ 目录
```

### 行情数据时态标注规范

Refresh 在不同时段采集的行情数据时态不同，需要在 `dataTime` 和 `timeStatus.marketStatus` 中准确反映：

| 北京时间 | 美东时间(EDT) | marketStatus | 行情数据含义 |
|---------|-------------|-------------|------------|
| 10:00 | 22:00 | 美股已收盘 | 美股=昨日收盘（与Heavy一致）；亚太=当日盘中 |
| 14:00 | 02:00 | 美股已收盘 | 美股=昨日收盘；亚太=当日收盘/接近收盘 |
| 18:00 | 06:00 | 盘前交易 | 美股=盘前数据（futures/pre-market）；亚太=当日收盘 |
| 22:00 | 10:00 | 美股交易中 | 美股=实时盘中价；亚太=已收盘 |

**关键注意**：
- 当 marketStatus = "盘前交易" 时，美股 price 为盘前价格，与 Heavy 版（收盘价）可能有差异，这是正常的
- 当 marketStatus = "美股已收盘" 且在亚太交易时段，亚太行情可能与 Heavy 版不同（因为 Heavy 在 06:00 采集时亚太未开盘）
- 加密货币和大宗商品全天交易，每次都应有最新数据

---

## Refresh 精简终审门禁

> **核心原则**：只校验被更新的字段，保留字段已由 Heavy 终审保障，无需重复检查。

### 必检项（Refresh 终审 7 项）

| # | 检查项 | 规则 |
|---|--------|------|
| R1 | **price/change 来源追溯** | 每个被刷新的价格能追溯到本次 web_fetch/web_search URL |
| R2 | **数据类型校验** | 被刷新的 change 仍为 number；sparkline 未被意外覆盖 |
| R3 | **trafficLights 一致性** | 7项 value 与行情源一致，status 按阈值表机械判定 |
| R4 | **riskScore 公式校验** | 30 + Σ(green=0, yellow=10, red=20) 结果正确 |
| R5 | **枚举值合规** | direction/marketStatus/sourceType 等在合法范围 |
| R6 | **保留字段未被篡改** | 抽检 3-5 个保留字段（coreJudgments/analysis/smartMoneyDetail），确认与基准 JSON 完全一致 |
| R7 | **JSON 语法合法** | 4个文件均可被 `json.loads()` 正确解析 |
| R8 | **【v1.2 新增】文案时效性校验** | 检查 briefing.json 的 takeaway/riskPoints/riskNote 是否含有已过期的时效词汇（"今夜""即将""最后通牒到期"等）；若含有且对应事件已发生 → **必须打回重做，不允许带着过期文案通过终审** |

### 跳过项（Heavy 已保障）

以下门禁在 Refresh 模式下跳过，因为对应字段未被修改：

- Top 10 快速终审 #3（smartMoneyDetail 数字追溯）
- Top 10 快速终审 #4（topHoldings 权重查证）
- Top 10 快速终审 #5（takeaway 3-5个【】标红）
- Top 10 快速终审 #6（riskPoints 不含操作建议）
- Top 10 快速终审 #8（coreJudgments.logic 箭头式）
- Top 10 快速终审 #10（briefing vs radar 持仓一致）
- 门禁 #11（smartMoneyDetail 逐条来源追溯）
- 门禁 #13（briefing 质量基线 B1-B12）
- 门禁 #14（watchlist 质量基线 W1-W9）

---

## 工作流

```
第零阶段：日期检测 → 确认当天已有 JSON → 路由到 Refresh 模式
  → 读取基准 JSON（4个文件）
  ↓
第一阶段：精简数据采集（R0~R3，共5-6次搜索）
  ↓
第二阶段：在基准 JSON 上覆盖刷新字段 → 重算公式字段 → 更新元数据
  ↓
第2.5阶段：Refresh 精简终审（7项）
  ↓
第三阶段：sparkline补全 + 上传（与 Heavy 完全相同的脚本流程）
  ↓
跳过第3.5阶段（不生成语音播报）
  ↓
第四阶段：交付确认（标注 Refresh 模式 + 搜索执行日志）
  ↓
第五阶段：执行复盘（精简版，仅检查"有无新堵点"，跳过 trafficLights 组合评估）
```

---

## 搜索执行日志（Refresh 版）

```
### 🔍 搜索执行日志（Refresh 模式）
| # | 批次 | 搜索关键词/URL | 结果摘要 | 有效数据提取 |
|---|------|---------------|---------|------------|
| 1 | R0 | web_search "..." | X条有效 | ✅/❌ |
| 2 | R1 | web_fetch google.com/finance/... | 价格/涨跌 | ✅/❌ |
| 3 | R2 | web_search "..." | X条 | ✅/❌ |
| ... | ... | ... | ... | ... |
| **合计** | — | **web_search: {N}次 / web_fetch: {M}次** | — | **达标✅ / 不达标❌** |

达标基线：Refresh ≥ 2次 web_search + 4次 web_fetch
```

---

## 交付确认（Refresh 版）

```
📱 投研鸭小程序数据刷新完成 — {YYYY-MM-DD HH:MM}（Refresh 模式）

🔄 刷新内容：
  ✅ 行情价格（美股+亚太+大宗+加密）
  ✅ 安全信号红绿灯（7项重算）
  ✅ 风险评分（riskScore/riskLevel/riskAdvice）
  ✅ 全球资产反应（direction 更新）
  {有突发事件时} ✅ 异动信号更新
  {无突发事件时} ➡️ 异动信号保留 Heavy 版

🔒 保留 Heavy 版（{Heavy执行时间}）：
  核心判断 / 深度分析 / 聪明钱 / 本周前瞻 / 语音播报

☁️ 云数据库上传：{成功/失败数}
📊 数据完整度：100%（基准 JSON + 增量刷新）
```

---

## 执行复盘（Refresh 精简版）

```
### 🔄 执行复盘（Refresh）
1. 🆕 **本次有没有遇到新的堵点/数据源异常？**
   → {有/无} → {有：简述 + 已写入 known-pitfalls.md / 无}
2. 📋 **行情数据是否与预期一致？**
   → {是/否} → {否：简述异常（如盘前价格波动大于预期）/ 是}
```

> 注意：Refresh 复盘省略 trafficLights 组合评估（一天一次由 Heavy 负责），仅关注数据采集层面的问题。

---

## 关键约束

1. Refresh 模式**必须读取当天 Heavy 版 JSON 作为基准**，不允许从零生成
2. Refresh 模式**不生成语音播报**——语音内容是深度分析，一天一次由 Heavy 负责
3. Refresh 模式**不执行聪明钱5层搜索**（RULE SEVEN 豁免）——聪明钱动向日内变化小，保留 Heavy 版
4. Refresh 模式**不更新 GICS 11板块数据**——板块ETF收盘后才有意义，日内刷新无价值
5. Refresh 模式**不更新 watchlist 的 metrics/analysis/tags 等深度字段**——标的分析一天不变
6. Refresh 模式的**行情数据铁律与 Heavy 完全相同**——RULE ZERO / ZERO-A / ZERO-B 不降级
7. 如果 Refresh 执行时发现基准 JSON 不存在或不完整——**自动降级为 Heavy 模式**，不允许 Refresh 失败退出
8. `_meta.sourceType` = `"refresh_update"`——让系统和日志可追溯执行模式

---

> v1.2 — 2026-04-07 | 【血泪教训】新增第四条红线：事件状态时效性强制校验。R0新增R0-B步骤（时效词检测+riskScore变化≥20触发），R3新增触发条件B（文案条件更新），终审新增R8门禁（过期文案不得通过终审）。字段边界表：takeaway/coreEvent.title/riskPoints/riskNote/marketSummaryPoints/actionHints从🔒保留升级为⚠️条件更新。背景：22:00 Refresh执行时riskScore从80→100（美以打击伊朗），但briefing文案仍写"今夜最后通牒到期"，大老板在小程序看到完全过期信息。
> v1.1 — 2026-04-07 | refreshInterval Refresh模式写"每4小时更新"；sentimentScore微调量化规则（VIX±3点/SPX±1.5%/突发事件）；_meta.refreshCount字段；R1批次M7默认策略明确化；briefing/markets/watchlist/radar四个JSON的_meta边界表同步补全refreshCount。
> v1.0 — 2026-04-07 | 初始版本，新增 Refresh 模式完整规范。
