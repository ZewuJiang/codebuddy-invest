---
name: investment-agent-daily-app
description: 当用户提到「投资App」「小程序数据」「投研鸭数据」「app数据更新」「miniapp sync」或类似关键词时，自动执行投研鸭小程序数据生产全流程，输出4个原生结构化JSON并上传微信云数据库。
---

# 投研鸭小程序数据生产 — 标准工作流 v10.3

> **版本**: v10.3 (2026-04-08 23:42) — 4/8 基准质量巩固：auto_compute v3.0 + validate v5.3 + 产出质量宪章
> **主控文档**：本文件为精炼主控（≤280行），详细规则通过引用按需加载。
> **核心改造**：①auto_compute.py v3.0（sparkline全自动对齐+price填充+方向修复）②validate.py v5.3（+V43 price占位符FATAL）③产出质量宪章（高盛级精选，非信息堆砌）

### 规范健康度快照

| 指标 | 值 | 上次更新 |
|------|------|---------|
| 致命错误条数 | 29 | 2026-04-06 |
| 已知堵点条数 | 43（活跃） | 2026-04-08 |
| trafficLights 阈值版本 | v4.8 | 2026-04-05 |
| 上次月度审计 | 未执行 | — |
| 连续零事故天数 | 0 | 2026-04-08 |
| 回归门禁条数 | 9 (R1-R9, 含3项FATAL) + V39/V43 FATAL | 2026-04-08 |
| 持仓缓存版本 | v1.1 (2025Q4 13F 已修正) | 2026-04-08 |
| **validate.py 版本** | **v5.3 (50项 含V39/V43 FATAL)** | **2026-04-08** |
| **auto_compute.py 版本** | **v3.0 (15类字段自动计算)** | **2026-04-08** |
| **checklist_generator.py** | **v1.0 (执行前自动清单)** | **2026-04-08** |
| **post_flight.py** | **v1.0 (执行后自动报告)** | **2026-04-08** |
| **schema-compact.json** | **v1.0 (AI紧凑Schema参照)** | **2026-04-08** |
| **质量基准** | **4/8 23:42 版 (49/49 PASS 零WARN)** | **2026-04-08** |

### v10.3 Changelog（2026-04-08 23:42）
- **🛡️ 4/8 基准质量巩固 — sparkline/price 全自动对齐 + 产出质量宪章**：
  - **auto_compute.py v2.0→v3.0**：新增 sparkline[-1]→price 自动对齐（markets+watchlist）+ sparkline 尾部方向 vs change 矛盾自动修复 + price="--" 从 sparkline[-1] 推导填充
  - **validate.py v5.1→v5.3**：新增 V43 [FATAL] price 禁止占位符（"--"/"N/A"/空值），校验项 49→50
  - **产出质量宪章**：高盛级智慧+$10级可读性，搜索广覆盖+产出精选，精简不凑数
  - **质量基线锚定**：4/8 23:42 版 50 项全 PASS 为不可降级基线
  - **known-pitfalls.md v4.2→v4.3**：新增堵点 #51(price占位符)/#52(sparkline偏离)/#53(信源链接空缺)

### v10.0 Changelog（2026-04-08 17:30）
- **🏗️ Harness v10.0 — 工具链全面升级（AI只做搜索+写分析，其余全自动）**：
  - **auto_compute.py v1.0→v2.0**：新增 metrics[2](7日涨跌)、metrics[3](30日涨跌)、metrics[5](综合评级) 从 sparkline/chartData 自动计算 + gics 按 change 降序排序 + dataTime 自动填充 + sourceType 废弃值修正 + refreshInterval 修正（共12类字段自动计算）
  - **validate.py v3.0→v4.0**：新增 V30-V34 内容质量检测层（Insight套话/riskAdvice模板/analysis深度/actionHints凑数/sourceType一致性）+ Insight 上限80→100字 + V7 精度修复 + riskAlerts 不再必填
  - **新增 checklist_generator.py v1.0**：执行前自动生成今天的精确清单（模式判定/采集批次/13F窗口/已知问题/数据新鲜度）
  - **新增 post_flight.py v1.0**：执行后自动生成交付确认+质量回归diff（AI不再手写模板）
  - **新增 schema-compact.json v1.0**：机器可读的紧凑 Schema（替代800行 json-schema.md 的执行阶段参照）
  - **golden-baseline.json v1.1→v1.2**：精简 sourceType 枚举（去掉 realtime_quote/breaking_news）+ riskAlerts 不再必填 + Insight 上限100 + 新增内容质量检测参数
  - **校验结果提升**：36项→41项，WARN 从 6→3

---

## 产出质量宪章（4/8 基准 — 不可降级）

> **一句话**：高盛级智慧，$10级个人投资者可读性。**搜索要广（不漏重要信息），产出要精（少而精的决策信号）**。

| 原则 | 要求 |
|------|------|
| **数据准确** | 每个数字可追溯到本次搜索，price/sparkline/change 三者自洽 |
| **内容严谨** | 结论+论据清晰对应，禁止模糊表述（"市场表现不一"等废话） |
| **精选不凑数** | 大老板看"决策信号"不看"信息堆砌"。5条精选 > 15条罗列 |
| **简单明了** | 每句话有信息增量，不冗余不啰嗦，观点+论据一句话说完 |
| **质量基线** | validate.py 50项全PASS（0 FATAL + 0 WARN）方可上传 |

---

## 定位与使命

> **读者**: 投研鸭微信小程序（机器消费）
> **产出物**: 4个原生结构化 JSON（briefing / markets / watchlist / radar）
> **核心宗旨**: 100% 完整、精确、结构化数据，让每个组件"满血渲染"
> **与 `investment-agent-daily` 的关系**: 完全独立。`daily` 输出 MD/PDF 给人读，本 Skill 输出 JSON 给机器读。

---

## 全局基础铁律（最高优先级）

> **🚨 一句话**：**禁止 AI 凭训练数据中的模糊记忆直接输出任何数字。所有数字必须来自当期实时搜索/查证。**

**自查三问**：①来自本次哪次搜索？②原文怎么写？③时间戳合理？→ 任一答不上→重新搜索
**违规后果**：等同于**数据造假**。**宁缺毋错，宁空不编。**

## 九大铁律

| 铁律 | 核心要求 |
|------|---------|
| **RULE ZERO** | 所有数字必须来自当期实时搜索，禁止凭记忆 |
| **RULE ZERO-A** | 交易数据（价格/汇率）只允许来自行情平台，禁止从新闻提取 |
| **RULE ZERO-B** | 观点数据中每个数字必须追溯到本次搜索结果，知识库只是搜索雷达 |
| **RULE ONE** | JSON 完整性——每个必填字段都必须有精确值，严禁空值 |
| **RULE TWO** | 数据类型严格——`change`=number, `sparkline`=number[], 枚举值受控 |
| **RULE THREE** | Schema 对齐——100% 对齐 [json-schema.md](references/json-schema.md) |
| **RULE FOUR** | sparkline 必填——7天历史走势由脚本自动补全，禁止估算 |
| **RULE FIVE** | 板块均衡——4核心板块（ai_infra/ai_app/cn_ai/smart_money）各≥2标的 |
| **RULE SIX** | 新增标的行情零容忍捏造——无法获取时宁可留空 |
| **RULE SEVEN** | 聪明钱搜索广覆盖+产出精选（Standard≥10+1次 / Weekend≥8+1次） |
| **RULE EIGHT** | **聪明钱持仓以 SEC 13F 为唯一确切数据源**（详见下方说明） |

### RULE EIGHT 详细说明 — 聪明钱持仓 13F 唯一数据源铁律

> **背景事故**（2026-04-08）：AI 将段永平 sell put（卖出看跌期权收取权利金）操作误解为 buy put（持有看跌期权多头），编造了 "AAPL PUT 2.8% 新建仓" 和 META/AMZN/TSLA 等 13F 中不存在的标的。

**适用范围**：`radar.smartMoneyHoldings` + `briefing.topHoldings` + `holdings-cache.json` 中所有持仓数据

**铁律条文**：

1. **唯一数据源**：SEC 13F-HR 季度披露文件。权威解析来源优先级：StockZoa > 13Radar > WhaleeWisdom > HedgeFollow。**禁止**从雪球评论/Twitter/微信群/新闻标题推断持仓。
2. **禁止衍生品**：13F 多头持仓表中**不包含**期权（PUT/CALL）多头。Sell PUT 产生义务而非持仓，不在 13F 中显示为 holding。symbol 字段禁止 PUT/CALL/OPTION/WARRANT 后缀。
3. **每个持仓可追溯**：每个 `{ name, symbol, weight, change }` 都必须能追溯到 13F 原始数据。`weight` 来自 13F 计算的组合占比，`change` 来自 Q-over-Q 比较。
4. **宁缺毋错**：查不到完整 13F 数据时，引用 `holdings-cache.json` 缓存值，不编造不推测。
5. **期权操作标注规则**：如段永平的 sell put 操作确需提及，只在 `footnote` 中以文字说明（如"另有 AAPL sell put 操作收取权利金，不计入持仓"），**绝不**作为 positions 数组中的一个条目。

**自动化校验**：`validate.py` V39 [FATAL] 自动检测 symbol/name 黑名单 + 权重合计异常。

---

## 触发条件与二档内容引擎

**触发关键词**：投资App / 小程序数据 / 投研鸭数据 / app数据更新 / miniapp sync

| 时机 | 模式 | `_meta.sourceType` | 详细规范 |
|------|------|--------------------|---------|
| 周一~周五（每次执行） | **Standard** | `heavy_analysis` | 本文件全流程 |
| 周末/休市日 | **Weekend** | `weekend_insight` | → [weekend-mode.md](references/weekend-mode.md) |

### 模式判定逻辑

```
今天周几？
  → 周六/周日/休市日 → Weekend
  → 周一~周五 → Standard（全量采集+分析+产出）
```

> **v9.0 简化说明**：不再有 Heavy/Refresh 区分。每次执行都是全量高质量产出，确保数据一致性。

---

## 产出物定义

| 文件 | 小程序页面 | Schema | 数据来源 |
|------|----------|--------|---------|
| `briefing.json` | 简报页 | → [json-schema.md §1](references/json-schema.md) | 核心结论+判断+建议+情绪+聪明钱 |
| `markets.json` | 市场页 | → [json-schema.md §2](references/json-schema.md) | 美股+M7+亚太+大宗+加密+GICS |
| `watchlist.json` | 标的页 | → [json-schema.md §3](references/json-schema.md) | 5板块标的+详情+metrics |
| `radar.json` | 雷达页 | → [json-schema.md §4](references/json-schema.md) | 安全信号+聪明钱+前瞻+预测 |

**输出路径**：`/Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows/investment_agent_data/miniapp_sync/`

---

## 工作流（7个阶段）

### 第零阶段：日期检测 + 模式路由 + 环境准备
- `date "+%A %Y-%m-%d %H:%M:%S"`
- 周一~周五 → Standard / 周末 → Weekend
- 每月1日执行月度规范审计 → [templates.md §六](references/templates.md)
- 确认输出目录存在

### 第一阶段：实时数据采集
**采集SOP** → [data-collection-sop.md](references/data-collection-sop.md)
批次概要：0(媒体扫描) → 1a-1d(美股行情) → 2(亚太) → 3(大宗/汇率/加密) → 4(基金动向) → 5(watchlist详情) → 6(事件日历) → A(情绪预测,可选)

### 第1.5阶段：数据完整性门禁（强制）
三大指数+M7+VIX / GICS 11板块 / 亚太4-6指数 / 大宗6项 / watchlist 5板块 / radar 7项红绿灯 / coreEvent+coreJudgments×3 / globalReaction 6项 / smartMoney 2-4条 / events 3-4条

### 第二阶段：结构化 JSON 生成（核心）
1. **先加载 Schema** → 必须重新读取 [json-schema.md](references/json-schema.md)，逐字段对照
2. **枚举值受控** → 完整枚举清单见 [json-schema.md §5.3](references/json-schema.md) 和 [golden-baseline.json](references/golden-baseline.json)
3. **数据类型严格** → `change`=number, `price`=string
4. **纯文本** → 禁止 markdown 语法
5. **sparkline/chartData** → 方案A 双轨分工，脚本第三阶段自动补全

### 第2.3阶段：AI 填写原始数值（公式由脚本自动计算）

> **v9.0 核心改造**：AI 只需填写以下原始数值，所有公式计算由 `auto_compute.py` 自动执行：

**AI 需要填写的字段**：
- `trafficLights[].value` — 7项指标的实际数值（从行情源采集）
- `trafficLights[].threshold` — 阈值说明文字（复制 [formulas.md §一](references/formulas.md)）
- `sentimentScore` — 情绪分数（0-100，基于多维度独立打分）
- `watchlist.stocks[].price` / `change` — 标的价格和涨跌幅

**由 `auto_compute.py` 自动计算的字段**（AI 无需手动填写，脚本会覆盖）：
- `trafficLights[].status` — 按阈值自动判定 green/yellow/red
- `riskScore` — 30 + Σ(green=0, yellow=10, red=20)，封顶100
- `riskLevel` — 按 riskScore 阈值自动判定 low/medium/high
- `sentimentLabel` — 按 sentimentScore 查表自动映射
- `watchlist.stocks[].metrics[0].value` — 自动与 price 对齐
- `watchlist.stocks[].metrics[1].value` — 自动与 change 对齐（含正负号+%）
- `watchlist.stocks[].metrics[2].value` — **v10.0 新增**：7日涨跌（从 sparkline 自动计算）
- `watchlist.stocks[].metrics[3].value` — **v10.0 新增**：30日涨跌（从 chartData 自动计算）
- `watchlist.stocks[].metrics[5].value` — **v10.0 新增**：综合评级（按 calc_star_rating 自动计算）
- `markets.gics[]` — **v10.0 新增**：按 change 降序自动排序
- `4个JSON dataTime` — **v10.0 新增**：自动填充当前北京时间
- `4个JSON _meta.sourceType` — **v10.0 新增**：自动修正废弃值

**所有公式唯一权威源** → [formulas.md](references/formulas.md)

### 第2.5阶段：JSON 完整性终审
> **v9.0 改造**：结构/数据/一致性/公式校验全部由 `validate.py` + `auto_compute.py` 自动执行。AI 只需关注以下**人工审读项**：
>
> **AI 人工审读（脚本无法覆盖的文本质量）**：
> 1. analysis/reason/summary 文本是否有洞察（非空洞废话）
> 2. coreJudgments.logic 是否箭头三段式（→ 符号串联）
> 3. Insight 是否为决策信号式（非新闻摘要）
> 4. riskAdvice 是否动态生成（非模板套话）
> 5. 播报文稿是否 TTS 友好

#### 回归门禁 R1-R9（validate.py 自动执行）
门禁口诀：`3家·Top10·无待更新·ARK在·交叉一致·2条动向·段永平有权重·三梯队满·cache一致·无期权`
**FATAL 级（R2/R3/R9/V39）**：不可被 `--skip-warn` 绕过，必须修复

#### 持仓数据缓存引用规则
**缓存文件** → [holdings-cache.json](references/holdings-cache.json)
非13F窗口期直接引用缓存，禁止凭记忆修改。13F窗口期（2/5/8/11月中旬）搜索最新数据并更新缓存。

### 第三阶段：自动计算 + sparkline补全 + 自动化校验 + 上传（一键执行）

```bash
bash /Users/zewujiang/Desktop/AICo/codebuddy-invest/.codebuddy/skills/investment-agent-daily-app/scripts/run_daily.sh {YYYY-MM-DD}
```

> **run_daily.sh v6.0 执行流程**：
> 1. 第0步：JSON 语法校验（硬依赖）
> 2. **第0.3步：auto_compute.py 自动计算公式字段（riskScore/riskLevel/sentimentLabel/trafficLights.status/metrics联动）**
> 3. **第0.5步：validate.py v3.0 自动化校验（FATAL级不可绕过 / WARN级可 --skip-warn）**
> 4. 第1步：sparkline/chartData 补全（软依赖）
> 5. 第2步：上传云数据库
> 6. 第3步：同步公开API

### 第3.5阶段：语音播报生成（⚠️ 强制，不可跳过）
> **v10.0 强制化**：validate.py V35 会检查 audioUrl 非空，跳过本步骤将触发 WARN。
步骤A：AI 撰写播报文稿 → 写入 briefing.json 的 `voiceText`
步骤B：TTS 音频生成 + 上传
```bash
python3 scripts/generate_audio.py "{sync_dir}" "{YYYY-MM-DD}"
python3 scripts/upload_to_cloud.py "{sync_dir}" "{YYYY-MM-DD}"
```

### 第四阶段：完成交付 + 输出确认
**所有交付模板** → [templates.md](references/templates.md)
1. 搜索执行日志 → `templates.md §一`
2. 交付确认信息 → `templates.md §二`
3. 质量回归 diff（强制） → `templates.md §三`
4. 同步公开 API → `sync_to_edgeone.sh`

### 第五阶段：执行复盘（30秒快检，强制）
**复盘模板** → [templates.md §四](references/templates.md)
3项自问：新堵点/新场景/trafficLights组合

---

## 优先级声明

| 优先级 | 维度 |
|--------|------|
| **P0** | JSON Schema 100% 对齐 + 数据准确性(RULE ZERO) + sparkline 完整性 |
| **P1** | 数据精确性(±X.XX%) + 板块均衡(4核心板块各≥2) |
| **P2** | 分析质量(analysis/reason/summary 有洞察) |
| **P3** | metrics 精确性(PE/市值用最新季度数据) |

---

## 致命错误索引（29条 — 详情见 [known-pitfalls.md](references/known-pitfalls.md)）

| # | 类别 | 说明 |
|---|------|------|
| 1-7 | 结构错误 | Schema不匹配/训练数据污染/空字段/类型错误/枚举越界/sparkline缺失无效 |
| 8-12 | 数据错误 | 空板块/红绿灯不足7/GICS不足11/globalReaction不足5/coreJudgments≠3 |
| 13-16 | 格式错误 | markdown残留/JSON语法/价格错误/可选字段枚举越界 |
| 17-21 | 内容错误 | 字段边界越界/时效性错误/数字矛盾/logic散文/takeaway缺标红 |
| 22-29 | 铁律违规 | RULE ZERO-A违规/数字不一致/脚本覆盖/url漏填/riskPoints未升级/模糊前缀/ZERO-B违规/SEVEN搜索不足 |

---

## 引用文件索引

| 文件 | 内容 | 加载时机 |
|------|------|---------|
| **[json-schema.md](references/json-schema.md)** | 4个JSON完整字段规范+门禁B1-B12/W1-W9/Q1-Q8 | JSON 生成阶段（必读） |
| **[schema-compact.json](references/schema-compact.json)** | **v10.0 新增**：机器可读紧凑Schema（AI执行阶段直接参照） | JSON 生成阶段（推荐） |
| **[formulas.md](references/formulas.md)** | 所有公式唯一权威源（红绿灯+riskScore+评级+sentiment映射） | 第2.3阶段 |
| **[golden-baseline.json](references/golden-baseline.json)** | 结构化基线定义（validate.py参数源+枚举值+公式常量） | validate.py 自动加载 |
| **[templates.md](references/templates.md)** | 交付模板集合（搜索日志+确认信息+diff+复盘模板） | 第四/五阶段 |
| [data-collection-sop.md](references/data-collection-sop.md) | 数据采集批次SOP | 采集阶段 |
| [stock-universe.md](references/stock-universe.md) | 5板块标的池+选股规则+metrics指南 | watchlist 生成 |
| [fund-universe.md](references/fund-universe.md) | 三梯队26家基金+策略师清单 | batch 4 扫描 |
| [media-watchlist.md](references/media-watchlist.md) | 三级媒体清单 | batch 0/0a 扫描 |
| [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md) | AI产业链24环标的库 | batch 0b 扫描 |
| [data-source-priority.md](references/data-source-priority.md) | 数据源优先级+降级路径 | 全流程 |
| [known-pitfalls.md](references/known-pitfalls.md) | 已知堵点40条+降级路径 | 全流程 |
| [weekend-mode.md](references/weekend-mode.md) | Weekend 模式完整规范 | 周末/休市日 |
| [holdings-cache.json](references/holdings-cache.json) | 持仓数据缓存（伯克希尔+段永平+ARK各Top10） | 非13F窗口期兜底 |
| [briefing-golden-sample.json](references/briefing-golden-sample.json) | 黄金样本（2026-04-06版） | 质量基线参考 |
| [CHANGELOG.md](CHANGELOG.md) | 完整版本历史归档 | 历史查阅 |

---

## 版本历史

> 详细 Changelog 见本文件顶部。完整历史见 [CHANGELOG.md](CHANGELOG.md)。
