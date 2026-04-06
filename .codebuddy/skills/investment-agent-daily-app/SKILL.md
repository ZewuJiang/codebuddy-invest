---
name: investment-agent-daily-app
description: 当用户提到「投资App」「小程序数据」「投研鸭数据」「app数据更新」「miniapp sync」或类似关键词时，自动执行投研鸭小程序数据生产全流程，输出4个原生结构化JSON并上传微信云数据库。
---

# 投研鸭小程序数据生产 — 标准工作流 v6.1

> **版本**: v6.1 (2026-04-06 19:20)
> **主控文档**：本文件为精炼主控，详细规则/知识库/模板/SOP通过引用按需加载。

### 规范健康度快照

| 指标 | 值 | 上次更新 |
|------|------|---------|
| 致命错误条数 | 29 | 2026-04-06 |
| 已知堵点条数 | 32 | 2026-04-06 |
| trafficLights 阈值版本 | v4.8 | 2026-04-05 |
| 上次月度审计 | 未执行 | — |
| 连续零事故天数 | 0（首日） | 2026-04-06 |

### v6.1 Changelog（2026-04-06 19:20）
- **播报文本生成器全面重构（v1.0→v3.0）**：
  - `generate_audio.py` v1.0→v3.0：从单文件单段式播报升级为跨4个JSON的八段式精选播报
  - 播报结构：§0开场→§1核心判断→§2驱动事件→§3市场全景→§4重点标的→§5聪明钱→§6风险与日历→§7深度判断→§8结尾
  - 设计原则对标高盛晨会/伯克希尔致股东信：结论先行、增量信息优先、绝不重复、精选而非凑数
  - 口播化增强：`$320万`→`320万美元`、日期`3/30`→`3月30日`、`→`→`进而`、`Model S/X`→`Model S和X`、`30+`→`30以上`、`10Y美债`→`十年期美债`、去除股票代码括号`(CRWV)`、`+`连接→`、`、指数名与价格间加"报"字分隔
  - 标的筛选逻辑：|涨跌幅|≥2.5%或有badges，去重后按绝对值排序取前5
  - 段落去重优化：合并原大盘速览+市场概览为「市场全景」（跳过美股Insight避免重复）、风险日历不重复事件链内容
  - 预估播报时长约5-6分钟（1700-1900字），覆盖整个小程序全部页面
  - **已固化为工作流**：第三阶段上传后自动执行 generate_audio.py → upload_to_cloud.py 两步式
  - MINIMAX_API_KEY 环境变量配置说明已补充到第3.5阶段

### v6.0 Changelog（2026-04-06 17:59）
- **新增语音播报功能（MiniMax TTS）**：
  - 新建 `generate_audio.py` v1.0：从 briefing.json 提取重点内容（takeaway+事件+行动建议+情绪+风险），调用 MiniMax T2A v2 API（speech-2.8-hd）生成 mp3 音频
  - `upload_to_cloud.py` v1.1→v1.2：新增 `upload_audio_to_cloud()` 两步式上传音频到微信云存储 + `get_audio_temp_url()` 获取临时下载链接 + 主流程自动检测音频文件并上传
  - briefing.json schema 新增 `audioUrl`/`audioFile`/`voiceText` 三个可选字段（json-schema.md v4.3）
  - 小程序前端 briefing.js v7.1→v7.2 / briefing.wxml v7.0→v7.1 / briefing.wxss v7.0→v7.1：时间状态栏嵌入🔊播放按钮，支持 cloud:// fileID 自动转临时链接播放，含 loading 动画和播放/停止状态管理
  - 环境变量新增 `MINIMAX_API_KEY`
  - 每日执行流程新增步骤：生成播报文稿→调用TTS→上传音频→写入audioUrl

### v5.9 Changelog（2026-04-06 15:30）
- **小程序前端 + Skill 联动工程优化（P0 零风险清理）**：
  - 删除已废弃云函数目录 `cloudfunctions/refreshRealtimeData/`（3文件437行，Fear&Greed+Polymarket 云函数已停用）
  - api.js v6.1→v7.0：删除 `getRealtimeData()` 函数体（52行）+ `cache_realtime` + v6.1 变更注释
  - radar.js v6.3→v7.0：移除 realtime 并发调用 + 双层合并逻辑（predictions 现由 radar.json 日报层单源提供）
  - color.js：删除 `getDeltaStatusInfo` / `getHeatLabel` / `getFearGreedInfo` 三个废弃函数（48行）+ 清理导出
  - docs 脱敏：云数据接入指南明文 AppSecret/AppID/CloudEnvId 替换为占位符；更新已废弃的 extract_data.py 引用
  - SKILL.md 优先级声明修正：「7个板块」→「5个板块（前4核心板块各≥2标的）」

### v5.7 Changelog（2026-04-06 14:07）
- **简报页+标的页质量基线门禁固化 + 执行质量加固 + 全面冗余清理**：
  - json-schema.md v4.1 新增「简报页质量基线门禁 B1-B12」+ v4.2 新增「标的页质量基线门禁 W1-W9」
  - 第2.5阶段终审新增第13项+第14项（briefing 过 B1-B12 + watchlist 过 W1-W9）
  - 枚举修复：json-schema.md §5.3 sectors[].id 修正为新5板块
  - 黄金样本固化：2026-04-06 版 briefing.json 存为 `references/briefing-golden-sample.json`
  - 执行质量五项加固：搜索执行日志/Top10快速终审/执行复盘/月度审计/规范健康度快照

### v5.6 及更早版本（详见 git 历史）

> v5.1 持仓数据铁律 → v5.0 简报页架构优化 → v4.8 聪明钱搜索深度 → v4.6 Batch 4 分层修复 → v4.5 雷达页升级 → v4.4 雷达页重构 → v4.3 AkShare 替代 yfinance → v4.2 watchlist 5板块 → v4.0 三档引擎 → v3.x 数据治理 → v2.x 架构演进 → v1.0 初始版本

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
| **观点中的数字** | smartMoneyDetail[].action 中的任何具体金额/占比 | 当期 web_search 返回结果（RULE ZERO-B） |

**自查三问（每个数字都必须过关）**：
1. ❓ 这个数字来自**本次执行的哪次搜索**？→ 答不上来 = 凭记忆编造 → **必须重新搜索**
2. ❓ 搜索结果中**原文怎么写的**？→ 对不上 = 数字被篡改 → **必须修正**
3. ❓ 数据的**时间戳**是否在合理范围内？→ 过期 = 旧数据 → **必须更新**

**违规后果**：任何凭记忆输出的数字，一旦被发现与真实值有偏差，等同于**数据造假**——对投资决策的危害远大于留空。**宁缺毋错，宁空不编。**

**典型事故复盘**：
- 离岸人民币（2026-04-06）：AI 记忆 7.28（2022-2023年），实际 6.88——差 5.8%，连锁 5 个字段全错
- 持仓权重（2026-04-06）：伯克希尔 AAPL 记忆 28%，实际 22.6%——差 5.4 个百分点
- 新增标的价格（2026-04-05）：10 只标的全部凭空捏造，最大偏差 46%

---

## 八大铁律（最高优先级）

| 铁律 | 核心要求 |
|------|---------|
| **RULE ZERO** | **全局数据查证铁律（v5.3 升级）**。详见上方「全局基础铁律」完整说明。核心：所有数字必须来自当期实时搜索，**禁止凭 AI 训练数据的模糊记忆直接输出任何数字**。自查三问：①来自本次哪次搜索？②原文怎么写的？③时间戳合理？任一为否→重写 |
| **RULE ZERO-A** | **交易数据与新闻数据严格隔离（零容忍）**：<br>● **交易数据**（价格/涨跌幅/汇率/sparkline）→ **只允许**直接行情 API/数据源（Google Finance / AkShare / OilPrice.com / FRED 等），**禁止**从任何新闻媒体页面（Bloomberg/Reuters/CNBC/财经媒体等）反向提取价格数字<br>● **新闻/观点/评论数据**（事件背景/分析/预测/聪明钱动向）→ 媒体网站（Bloomberg/Reuters/WSJ/华尔街见闻等）<br>● **违规判定**：如果一个价格数字的来源是新闻文章而非行情平台，该条数据视为**训练数据污染**，必须重新从行情源采集 |
| **RULE ZERO-B** | **观点数据来源追溯铁律（v4.7 — 零容忍）**：<br>● **适用范围**：`smartMoneyDetail[].funds[].action` / `smartMoney[].action` / `alerts[].text` / 所有包含具体数字的观点文本字段<br>● **核心规则**：每个具体数字必须可追溯到**本次执行**的 web_search/web_fetch 返回结果。知识库仅作为「搜什么的雷达清单」，**绝对禁止**从知识库复制任何数值直接写入 JSON<br>● **自查三问**：①来自哪次搜索？②原文怎么写？③时间戳7天内？任一答不上→删除或重新搜索<br>● 详见 known-pitfalls.md 堵点#28 |
| **RULE ONE** | JSON 完整性铁律。4个JSON中每个必填字段都必须有精确值，严禁空字符串/空数组/`null`/`"--"`/`"N/A"` |
| **RULE TWO** | 数据类型严格。`change` 必须是 `number` 类型（不是 string），`sparkline` 必须是 7 个 number 的数组，枚举值必须在允许范围内 |
| **RULE THREE** | Schema 对齐铁律。每个 JSON 的结构必须 100% 对齐 `references/json-schema.md` 中的定义，不允许新增/缺失/改名字段 |
| **RULE FOUR** | sparkline 必填。markets/watchlist 中每个标的必须有 7 天历史走势数据（sparkline 数组），watchlist 额外需要 30 天 chartData |
| **RULE FIVE** | 板块均衡。watchlist 的 5 个板块（ai_infra/ai_app/cn_ai/smart_money/hot_topic）中，前4个核心板块每个至少2只标的；hot_topic 为动态板块，无事件时可为空数组或整个板块省略 |
| **RULE SIX** | **新增标的行情数据零容忍捏造**。任何新加入 watchlist 的标的，`price`/`change`/`sparkline`/`chartData`/`metrics` 中的价格数据**必须全部来自 Google Finance web_fetch 或 AkShare 真实数据**。**绝对禁止**凭记忆/推测/估算填写。数据无法获取时：price 写"待采集"、change 写 0、sparkline/chartData 写 `[]`。**宁可留空也不能编造**。 |
| **RULE SEVEN** | **聪明钱搜索广覆盖+产出精选铁律（v4.8）**：<br>● **搜索范围必须广**：每次执行必须走完5层搜索流程（广播→一级核心定向→ARK web_fetch→策略师→知识库联动），最低搜索次数：Heavy≥10次web_search+1次web_fetch；Weekend≥8次+1次；13F模式≥14次+1次<br>● **产出精选不凑数**：smartMoneyDetail 不设最低条数，只选真正有料的。**宁少而精，不多而杂**<br>● **深挖强制**：web_fetch≥2次（ARK 1次+高价值来源≥1次）<br>● **精选标准**：有具体动作/数字 > 有明确方向判断 > 时效性近。泛泛空话淘汰<br>● 详细搜索流程 → [fund-universe.md §七](references/fund-universe.md) |

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

### Weekend 模式内容规范（v4.0 新增 — 详细规范已外迁）

> **详细规范** → [weekend-mode.md](references/weekend-mode.md)（含采集批次、4个JSON产出规则、工作流、关键约束）
>
> **一句话概要**：周末/休市日读取上一交易日4个JSON文件作为基准，保留行情数据不变，更新分析/洞察/展望字段为"本周回顾+下周前瞻"视角。`_meta.sourceType` = `"weekend_insight"`。
>
> **关键约束**：不伪造行情、不降低品质、必须读取上一交易日JSON作为基准。

---

## 产出物定义

| 文件 | 对应小程序页面 | 数据来源 | Schema 定义 |
|------|--------------|---------|------------|
| `briefing.json` | 简报页 | §1核心结论 + §2摘要 + §4摘要 | → [json-schema.md §1](references/json-schema.md) |
| `markets.json` | 市场页 | §2全球市场 + GICS板块 | → [json-schema.md §2](references/json-schema.md) |
| `watchlist.json` | 标的页 | §3重点标的 + 行业分析 | → [json-schema.md §3](references/json-schema.md) |
| `radar.json` | 雷达页 | §5风险雷达 + §4基金详情 | → [json-schema.md §4](references/json-schema.md) |

---

## 工作流（7个阶段）

### 第零阶段：日期检测 + 模式路由 + 环境准备

```bash
date "+%A %Y-%m-%d %H:%M:%S"
```

#### 月度规范审计（v5.7 新增 — 每月1日自动触发）

> **触发条件**：当执行日期为**每月1日**时，在模式路由之前自动执行以下审计。非1日则跳过。

| # | 审计项 | 具体检查内容 | 输出 |
|---|--------|------------|------|
| 1 | **trafficLights 阈值审计** | 7项指标的阈值是否仍合理？（如黄金从 $2200-$3500 是否需要上调；离岸人民币从 7.15-7.30 是否需要下调） | 列出需要调整的指标 + 建议新阈值 |
| 2 | **堵点清单审计** | known-pitfalls.md 中已标记「永久性」「已修复」的条目是否可以归档？近30天有没有新堵点未记录？ | 建议归档的堵点编号 + 新增遗漏 |
| 3 | **数据源健康度** | 近30天哪些数据源出过故障/限流？（Google Finance 403 频率？AkShare 限流频率？Polymarket 可用性？）是否需要调整优先级？ | 数据源健康度报告 |
| 4 | **枚举值审计** | sentimentLabel / marketStatus / predictions.source 等枚举是否覆盖了所有出现过的场景？有没有新场景需要新增枚举？ | 建议新增的枚举值 |

**审计结果输出**：在交付确认中新增一段 `📋 本月规范审计：完成/发现{N}项需更新`，并立即执行更新。
**审计后更新**：修改顶部「规范健康度快照」的「上次月度审计」行。

- **周六～周日 / 美股休市日** → **Weekend 模式**（详见 [weekend-mode.md](references/weekend-mode.md)）
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
| **A** | **情绪与预测数据采集（Polymarket / CME FedWatch）** | → [data-collection-sop.md 第八章](references/data-collection-sop.md)（可选批次，失败不阻断） |

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
| 7 | **coreEvent + coreJudgments×3 + actionHints(可选) + riskPoints** | 完整文本；riskPoints 2-3条（禁止含操作建议）；actionHints 无高置信机会时为空数组[] | 补充分析 |
| 8 | **globalReaction 6项** | name+value+direction | 补充 |
| 9 | **smartMoney 2-4条** | source+action+signal | 补充 |
| 10 | **events 3-4条（精选高决策价值事件，日期必须搜索核实）+ riskAlerts 填[]** | events完整字段；riskAlerts空数组 | 补充events / riskAlerts保持[] |

**⭐ 可选字段建议检查（非阻断——缺失时前端对应模块不渲染，不影响发布）**：

| # | 验证项 | 要求 | 未填时操作 |
|---|--------|------|-----------|
| O1 | briefing: timeStatus（建议） | bjt+est+marketStatus(枚举值见 json-schema.md)+refreshInterval | 根据执行时间推算填写，或省略（前端可自行计算） |

| O2 | radar: predictions（建议） | 2-4条，每条 title+source(枚举)+probability(0-100整数)+trend(枚举)+change24h | 参照 Batch A 子批次 A2/A3/A4 采集结果汇总；所有子批次均失败时填 [] |
| O3 | 所有4个JSON: _meta（建议） | sourceType+generatedAt(ISO8601格式)+skillVersion | sourceType 按模式填写（Heavy→`heavy_analysis` / Weekend→`weekend_insight`）；generatedAt 为执行时间（+08:00）；skillVersion 为当前 SKILL.md 顶部版本号 |

### 第二阶段：结构化 JSON 生成（核心阶段）

基于采集数据，严格按照 `references/json-schema.md` 的 Schema 定义生成 4 个 JSON 文件。

**生成规则**：
1. **先加载 Schema** — 必须重新读取 `json-schema.md`，逐字段对照生成
2. **枚举值受控** — direction 只能是 `up/down/flat`，signal 只能是 `bullish/bearish/neutral`，等等
3. **数据类型严格** — `change` 必须是 `number`（如 `1.42`），不是 string（如 `"+1.42%"`）
4. **纯文本** — 所有文本字段禁止包含 markdown 语法（`**加粗**`、`|表格|`、`- 列表`等）；analysis 字段允许 `\n` 分段
5. **sparkline/chartData 生成** — **方案A 双轨分工**：所有 WATCHLIST_AK_MAP 中已注册的标的（美股+港股+A股）的 sparkline(7天)/chartData(30天) 均由第三阶段脚本自动补全（AkShare 新浪源+东方财富 fallback），AI 在此阶段**无需手动生成**；脚本失败时会自动跳过该标的，保留 AI 估算值。**严禁估算、插值或模拟波动生成 sparkline**（违反 RULE FOUR）。
   **A股 ticker 后缀格式**：深交所用 `.SZ`（如 `300750.SZ`）；上交所用 `.SH`（如 `600519.SH`、`688256.SH`）。脚本映射：深交所 `sz+代码`，上交所 `sh+代码`。

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
| 黄金XAU | web_search / OilPrice.com | < $2,200 | $2,200 ~ $3,500 | > $3,500 | `<$2200绿 / $2200-3500黄 / >$3500红` |
| 离岸人民币CNH | web_search / AkShare | < 7.15 | 7.15 ~ 7.30 | > 7.30 | `<7.15绿 / 7.15-7.30黄 / >7.30红` |

> ⚠️ AI 填写 trafficLights 时，`value` 字段写采集到的实际数值（字符串格式），`status` 字段严格按上表阈值判断，`threshold` 字段复制上表「threshold 文字」列的内容。

#### trafficLights 动态迭代机制（v4.8 新增）

> **核心原则**：安全信号必须跟着市场走，不能一成不变。7项指标应始终是**当下最关键的风险信号**——顶级机构（高盛/大摩/桥水/伯克希尔）当前最关注什么，我们就展示什么。
>
> **选择标准**：每项指标必须满足以下至少2条——①顶级机构（GS/MS/桥水/伯克希尔/Druckenmiller）正在重点关注或交易；②当前处于黄灯/红灯区间（绿灯且长期稳定的指标优先级降低）；③与本周核心风险事件直接相关（如伊朗战争→油价，CPI发布→10Y美债）

**固定3项（永久保留，任何市场环境下都是核心）**：
| 指标 | 理由 |
|------|------|
| VIX波动率 | 恐慌指标之王，所有机构的风控第一看板 |
| 10Y美债收益率 | 全球资产定价锚，影响所有估值 |
| 黄金XAU | 终极避险资产，桥水/Druckenmiller核心持仓 |

**动态4项（随市场环境调整）**：
| 当前环境 | 推荐指标 | 替换时机 |
|---------|---------|---------|
| 伊朗战争/能源危机 | **布伦特原油**（当前） | 战争结束+油价回落<$85 → 可替换 |
| 美元走弱周期 | **美元指数DXY**（当前） | DXY持续稳定在98-104区间 → 优先级降低 |
| 信用市场平稳 | HY信用利差（当前） | 若HY利差突破4%或流动性危机 → 权重升高 |
| 中国相关风险低 | 离岸人民币CNH（当前） | 若中美关税升级/人民币破7.3 → 权重升高 |

**备选指标池（当动态4项需要替换时选用）**：
| 指标 | 适用场景 | 阈值参考 |
|------|---------|---------|
| 铜价 | AI/基建周期+供应紧张（Druckenmiller做多） | <$4绿 / $4-5黄 / >$5红 |
| 2Y-10Y利差 | 衰退预警信号 | >0绿 / -0.5~0黄 / <-0.5红 |
| 美联储降息概率 | 货币政策转向期 | >60%绿 / 30-60%黄 / <30%红（市场预期vs实际） |
| BofA牛熊指标 | 情绪极端值 | 3-7绿 / 2-3或7-8黄 / <2或>8红 |
| 天然气 | 能源危机/冬季供暖季 | 参照当时价格水平设定 |

**迭代规则**：每次全量执行时（第一阶段数据采集结束后），AI 应评估当前7项是否仍是最优组合。若发现某项已长期绿灯且与当前核心风险无关，可在下次执行时提议替换（需在交付确认中说明替换理由）。

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

**riskAdvice 内容规范（v5.4 升级 — 去操作化+F&G弱化）**：
```
格式：必须动态生成，禁止模板化套话。
要求：
  ①点名最危险的 1-2 项红灯/黄灯指标（说清楚危在哪里）
  ②如果底层指标（VIX/Put-Call/信用利差等）释放明确信号可综合判断情绪方向，但禁止机械引用 F&G 单一指标值
  ③指向本周最关键的催化剂/时间节点（如"若周四CPI确认通胀二次抬头"），让大老板自行判断
  ④禁止包含操作建议（仓位/加仓/减仓/对冲等），与简报页 riskNote/riskPoints 去操作化原则一致
  ⑤不超过 2 句话，但每句有信息量

正确示例：
  "黄金$4,627亮红灯（避险情绪极端），布伦特$109逼近红灯区间——若周四CPI确认通胀二次抬头，当前反弹基础将被抽空。"

错误示例（禁止）：
  "布伦特$109叠加F&G仅19（极度恐惧），建议维持5成仓位+能源对冲，等CPI落地后再评估。"
  （原因：①机械引用F&G单一指标值 ②包含操作建议"维持5成仓位+能源对冲"应放在actionHints）
```

---

#### radar.json 产出质量规范（v4.4 新增）

**`smartMoneyDetail[]` 模块定位与内容质量要求**：

> **模块定位**：聪明钱**最新动作/重大观点**扫描。优先级：当天 > 最近几天 > 本周，**最多不超过7个自然日**。只选最新、最有信息量的动作或观点，不凑数。
> **与 `smartMoneyHoldings` 的分工**：`smartMoneyDetail` = 「最近在做什么」（高频、动态、每次执行刷新）；`smartMoneyHoldings` = 「手里拿着什么」（季度13F持仓结构，低频更新）。

| 要求 | 说明 |
|------|------|
| **必须有具体内容** | 每条机构动向必须包含：「做了什么」+「为什么」或「信号意义」，禁止泛泛的「维持中性」「谨慎操作」等无信息量表达 |
| **T1旗舰（桥水/伯克希尔/贝莱德等）** | 需体现配置方向判断（如"继续维持宏观与防御资产平衡配置"）+ 具体信号（如"不因单日反弹放松风控"） |
| **T2成长（ARK等）** | 需体现对当前市场环境的判断 + 操作建议（如"分批而非一次性押注"） |
| **策略师观点** | 需体现具体看好/看空的板块或标的（如"继续看好AI基础设施"），禁止只说"关注市场变化" |
| **时效性铁律** | 优先当天动态（如ARK当日交易）→ 其次最近2-3天（如本周发布的策略报告）→ 最远不超过7天。超过7天的动向 action 前必须加 `[MM/DD]` 日期前缀让读者知道这不是最新的；超过30天的动向禁止填入。**有新的写新的，没新的宁可少写也不凑旧的** |
| **策略师时效门槛（v4.6新增）** | 策略师观点必须在7天以内发布；超过7天的旧观点 action 字段前必须加 `[MM/DD]` 日期前缀；超过30天的观点禁止填入。无新观点时 funds[] 可只放1条+1条量化情绪指标替代（详见 `fund-universe.md` §5.4） |
| **禁止重复持仓信息（v4.8新增）** | `smartMoneyDetail` = 「最近在做什么」（动态/新动作/新观点），`smartMoneyHoldings` = 「手里拿着什么」（季度13F静态持仓）。**两个模块严格分工，禁止在 smartMoneyDetail 的 action 中重复 smartMoneyHoldings 已展示的持仓数据**（如「苹果50.3%+BRK.B 20.6%」）。大老板往下滑就能看到完整持仓，动向模块只写本周新增的信息量 |
| **精炼写法规范（v4.8新增）** | 每条 action **35-75字**，只回答「谁在做什么、方向是什么」。大老板扫一眼就能抓到重点，原因和背景让他自己判断。<br>**精炼三原则**：①只留最核心的1-2个信号点，砍掉次要细节；②数字只保留最震撼的（如$120万买入CRWV），小金额买卖省略；③背景解释/原因分析一律砍掉，只留结论和动作<br>**正确示例**（65字）：`"3月股票ETF流入骤降至$640亿（1-2月均超$1000亿），75%资金涌入固收，能源板块资金流入6年来首超科技。"`<br>**错误示例**（110字）：`"Q1 ETF资金流报告释放避险信号：3月股票ETF流入从1-2月的$1000亿+/月骤降至$640亿；固收基金占3月ETF总流入75%+，超50%进入超短期国债；能源板块资金流入首次超过科技板块（6年来仅第3次）；比特币ETP Q1净流出$64亿。"` |

**`predictions[]` 筛选与内容规范（v4.8 升级）**：

> **模块定位**：市场预测 = 当下最关键的2-3个概率事件。每一条都应该让大老板看到后立即知道「市场最担心/最期待什么」。

| 规则 | 说明 |
|------|------|
| **核心原则** | **每条预测必须与当前市场最大矛盾直接挂钩**，灵活应对而非僵化。不同市场环境选不同预测，没有固定模板 |
| **筛选标准（按优先级）** | ①与本周 `events[]` 直接相关的预测（最高优先，如本周有CPI → 选通胀/降息相关）；②与当前最大风险源直接相关（如伊朗战争 → 油价/停火概率）；③`change24h` 绝对值 > 5 的（市场判断在快速变化）；④`probability` > 65% 或 < 20% 的极端共识 |
| **淘汰标准** | ①与本周/当前核心矛盾无关的长期预测（如「2026年底衰退概率」）；②`change24h` ≈ 0 的（市场无新信息）；③成交量极小的小众事件 |
| **来源枚举** | `source` 仅允许：`Polymarket` / `Kalshi` / `CME FedWatch` |
| **数量控制** | 精选 2-3 条，宁少而精。1条极高价值 > 3条平庸 |

**不同市场环境的选择参考（灵活应对，非固定模板）**：

| 市场环境 | 推荐选取方向 | 示例 |
|---------|------------|------|
| 地缘冲突（当前） | 战争走向+能源价格+央行政策应对 | 伊朗停火/油价突破/降息概率 |
| 衰退担忧 | 经济衰退概率+降息次数+就业恶化 | 年内衰退概率/降息3次+概率/失业率破4% |
| AI泡沫/科技调整 | 科技股回调幅度+AI监管+巨头财报 | NVDA年底超$200/AI监管法案通过 |
| 大选年 | 选举赔率+政策变化+市场影响 | 特朗普胜选概率/关税政策延续 |
| 货币政策转向 | 加息/降息路径+通胀走向 | 首次降息时间/核心CPI破3% |

**`events[]` 本周前瞻规范（v4.8 重构）**：

> **模块定位**：本周前瞻 = 纯时间轴确定性事件，只展示「哪天发生什么」。少而精，大老板扫一眼就知道本周哪几天要注意。

| 要求 | 说明 |
|------|------|
| **只选高决策价值事件** | 只保留对投资决策有直接影响的事件（CPI/FOMC/NFP/GDP等），砍掉二级指标（如密歇根消费者信心、耐用品订单等——除非出现极端值） |
| **日期必须搜索核实** | 每次生成 events 时，必须 web_search 核实具体日期（如「CPI April 2026 release date」），**禁止凭记忆填日期**。典型事故（2026-04-05）：FOMC纪要写周二（实际周四）、CPI写周四（实际周五）、PPI写周五（实际周三），3/5日期错误 |
| **3-5条为宜** | 一般每周3-4条高影响事件即可，最多5条。不够就不凑 |
| **title要说清为什么重要** | 不是纯事件名称，而是「事件+为什么本周要关注」，如「3月CPI发布——本周最重要数据，油价+34%后通胀能否确认二次上行」 |

**`riskAlerts[]` 状态（v4.8 废弃渲染）**：

> ⚠️ `riskAlerts[]` **不再在本周前瞻中渲染**——风险预警信息已通过 `riskAdvice`（安全信号模块顶部的一句话建议）和 `alerts[]`（异动信号）充分覆盖，再在前瞻中重复展示「持续」类风险会导致信息过载。
> 为保持 Schema 向后兼容，JSON 中 `riskAlerts` 填空数组 `[]`，前端自动隐藏该模块。

**`alerts[]` 异动信号精选规范（v4.8 新增）**：

> **模块定位**：最近24-48小时内的突发/重大事件快讯，按紧急程度分红（danger）/黄（warning）/绿（info）三级。

| 要求 | 说明 |
|------|------|
| **只选影响投资决策的事件** | 大老板看到后会想「这对我的仓位有什么影响」的才选。纯新闻不选 |
| **2-3条为宜** | 宁少而精。当天只有1件大事就只写1条 |
| **禁止信息重叠** | 同一事件链（如伊朗战争的多个子事件）合并为1条，不要拆成3条占满屏幕 |
| **禁止子数据拆条** | 同一数据发布（如NFP）的多个维度（总量/工资/ADP）合并为1条，不把子项单独拆出来 |
| **精炼写法** | 每条1-2句话，只说「发生了什么+关键数字」，不加分析和建议（建议在riskAdvice中统一给） |

**`monitorTable[]` 状态（v4.4 废弃渲染）**：
> ⚠️ `monitorTable[]` 字段**不再渲染**（前端已移除该模块）。
> 为保持 Schema 向后兼容，JSON 中可继续生成 `monitorTable[]`，但前端不显示。

---

#### metrics 综合评级（watchlist 标的）计算规则

> 详细的评级规则定义 → 参见 [stock-universe.md §四](references/stock-universe.md) 和 [json-schema.md §三](references/json-schema.md)。

**快速参考**（基于 30日涨跌幅 + 单日涨跌幅）：
- ⭐⭐⭐⭐⭐：30日涨超+15% 且单日为正
- ⭐⭐⭐⭐：30日涨+5%~+15%，或单日涨超+3%
- ⭐⭐⭐：30日在-5%~+5%
- ⭐⭐：30日跌-5%~-15%
- ⭐：30日跌超-15%

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
| **11** | **smartMoneyDetail 逐条来源追溯（RULE ZERO-B）** | 逐条检查 `smartMoneyDetail[].funds[].action`：每个具体数字（$金额/百分比/目标价/持仓占比）是否可追溯到本次执行的 web_search/web_fetch 结果URL？不能追溯→该条必须删除或重新搜索核实后填入。**终审自查口诀：「每个数字都要有搜索来源，说不出来源就删掉」** |
| **12** | **markets.json 质量基线门禁（v4.4 固化）** | 逐项过 json-schema.md「市场页质量基线门禁 Q1-Q8」：①5Tab数据完整性（数组长度）；②6条Insight全部非空且为决策信号式（非新闻摘要）；③sparkline[-1]与price偏差≤1%；④GICS摘要非空；⑤数字全部实时查证（特别关注CNH/VIX/10Y）；⑥枚举值合规；⑦M7 header为 `🏆 Magnificent Seven`（无副标题）。**任一项不通过则退回修正** |

#### Top 10 快速终审 Checklist（v5.7 新增 — 每次执行必须逐项过一遍）

> **目的**：从29条致命错误+12项终审门禁中提取历史最高频出错 Top 10，认知负荷降80%。先过 Top 10，再查完整门禁。

| # | 检查项 | 快速验证方法 | 对应致命错误 |
|---|--------|------------|------------|
| 1 | **price/change 来源追溯** | 每个价格能说出 web_fetch URL 吗？ | 致命 #22/#31 |
| 2 | **sparkline[-1] vs price 一致** | 偏差 < 1%？逐标的扫描 | 高频 #33 |
| 3 | **smartMoneyDetail 数字追溯** | 每个数字有搜索来源？说不出→删掉 | 致命 #28 |
| 4 | **topHoldings 权重查证** | 来自 13Radar / Whalewisdom？briefing vs radar 一致？ | 致命 #27 |
| 5 | **takeaway 有 3-5 个【】标红** | 数一数？不足3个或超5个→调整 | 高频 #16 |
| 6 | **riskPoints 不含操作建议** | 含"建议/仓位/对冲"→重写为纯风险描述 | 高频 #25 |
| 7 | **chain[].url 非空** | 非付费墙的 source 都有 https 链接？ | 高频 #17 |
| 8 | **coreJudgments.logic 箭头式** | 有 → 符号？每段 ≤15 字？整条 ≤50 字？ | 高频 #15 |
| 9 | **枚举值合规** | direction/signal/type/label/marketStatus 全在合法范围？ | 高频 #5/#13/#21 |
| 10 | **briefing vs radar 持仓一致** | 先写 radar 再提取 briefing？标的/排序/权重完全对应？ | 高频 #28 |

**执行方式**：终审时先用 Top 10 做 1 分钟快扫（逐行打 ✅/❌），再执行上方完整 12 项门禁。Top 10 中任一项 ❌ 则立即修正后重新扫描。

#### 额外质量门禁（v5.7 新增 — 基于 json-schema.md 的逐项自查）

| **13** | **briefing.json 质量基线门禁（v5.7 固化）** | 逐项过 json-schema.md「简报页质量基线门禁 B1-B12」——takeaway标红3-5个/title 20-50字聚焦1-2矛盾/chain url完整/logic箭头三段式/globalReaction无模糊前缀/actionHints不凑数/riskPoints去操作化/sentimentScore独立判断/smartMoney有信息量/topHoldings交叉一致/marketSummaryPoints不重复/整体价投风格。**任一项不通过则退回修正** |
| **14** | **watchlist.json 质量基线门禁（v5.7 固化）** | 逐项过 json-schema.md「标的页质量基线门禁 W1-W9」——W1板块完整性（4核心板块各≥2标的）/W2字段完整（name~chartData全非空）/W3 analysis 2-3段有洞察/W4 reason有结论+论据/W5 tags精准4-8字/W6 metrics一致（price⟷metrics[0]、change⟷metrics[1]、评级按公式）/W7 summary有具体数据/W8 sparkline[-1]与price偏差≤1%/W9 risks独立具体。**任一项不通过则退回修正** |

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
| AkShare 限速 / 超时（第1步） | 重试1次；仍失败 → **警告+跳过**，继续上传 | sparkline/chartData 为 AI 估算值；其他字段 AI 直接保障，不受影响 |
| 上传失败（第2步） | **阻断**，JSON 文件保留在本地，可手动重传 | — |

### 第3.5阶段：语音播报生成（v6.2 — 上传成功后自动执行）

> **⚠️ 此阶段在第三阶段上传成功后自动执行，无需用户手动操作。**
> 前提：4个 JSON 文件已上传成功。

**环境变量（已持久化到 ~/.zshrc，无需每次设置）**：
```bash
export MINIMAX_API_KEY="sk-api-xxx"
# 获取地址：https://platform.minimaxi.com/user-center/basic-information/interface-key
# ⚠️ API Key 有有效期，过期后需重新生成
```

#### 步骤 A：AI 撰写播报文稿（核心步骤）

> **关键改进**：播报文稿由 AI 基于当天 4 个 JSON 的实际数据**撰写**，而非代码拼接。
> 写完后 AI 自行**通读审校**一遍，确保逻辑通顺、数据准确、表述自然，然后写入 `briefing.json` 的 `voiceText` 字段。

**撰写规范**：

| 要求 | 说明 |
|------|------|
| **风格** | 对标高盛晨会口播稿/伯克希尔致股东信口吻——专业、从容、有判断力。不是念数据，是讲故事 |
| **受众** | 大老板一个人听的私人简报，语气可以稍微亲切但保持专业感，像首席策略师一对一汇报 |
| **结构** | §0开场→§1核心判断→§2驱动事件→§3市场全景→§4重点标的→§5聪明钱→§6风险与日历→§7深度判断→§8结尾 |
| **时长** | 1500-2000字，约5-7分钟 |
| **衔接** | 段落之间要有自然的逻辑衔接，不能像数据库读条目。如"说完大盘，看看个股层面"、"接下来关注聪明钱最近在做什么" |
| **口播化** | 所有内容必须TTS友好：金额用中文（109美元）、日期用中文（3月30日）、避免括号/代码/特殊符号、英文缩写首次出现时加中文注解 |
| **精选原则** | 搜索范围大不漏，产出精选不凑数。大老板听的是"少而精的决策信号"，不是信息堆砌 |

**数据来源映射**（同 generate_audio.py v3.0 八段结构）：

| 段落 | 数据来源 |
|------|---------|
| §0 开场白 | 固定："投研鸭，X月X日，二级市场简报" |
| §1 核心判断 | `briefing.takeaway`（口播化处理后原样播出） |
| §2 驱动事件 | `briefing.coreEvent.chain`（每条 title+brief，最多5条） |
| §3 市场全景 | `markets.usMarkets` + `globalReaction` + 各市场Insight（合并去重） |
| §4 重点标的 | `watchlist.stocks`（\|change\|≥2.5%或有badges，每只一句催化） |
| §5 聪明钱信号 | `briefing.smartMoney`（3-4条） |
| §6 风险与日历 | `riskPoints` + `trafficLights`(红灯) + `events`（不重复事件链） |
| §7 深度判断 | `briefing.coreJudgments`（标题+置信度+逻辑链，压轴） |
| §8 结尾 | 固定："以上是今日简报，详细内容请查看投研鸭小程序" |

**审读自查清单（AI 写完后必须过一遍）**：

| # | 检查项 | 说明 |
|---|--------|------|
| 1 | **数据准确** | 播报中提到的每一个数字是否与 JSON 中的值一致？ |
| 2 | **逻辑通顺** | 段落之间因果关系是否清晰？听众能跟上思路吗？ |
| 3 | **无重复** | 同一信息是否在不同段落说了两遍？（如事件链和风险日历重复） |
| 4 | **TTS 友好** | 有没有 $符号、括号内代码(CRWV)、加号连接、10Y 等 TTS 会念乱的内容？ |
| 5 | **表述自然** | 朗读一遍，有没有机械感/拗口的地方？ |
| 6 | **时长合理** | 1500-2000字，约5-7分钟，不超过10分钟 |

**写入方式**：AI 将审读通过的播报文稿写入 `briefing.json` 的 `voiceText` 字段（replace_in_file 或 python 脚本写入）。

#### 步骤 B：TTS 音频生成 + 上传

```bash
# 步骤1：读取 voiceText 并调用 MiniMax TTS 生成 mp3（若 voiceText 已存在则直接使用，不再代码拼接）
python3 /Users/zewujiang/Desktop/AICo/codebuddy-invest/.codebuddy/skills/investment-agent-daily-app/scripts/generate_audio.py "/Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows/investment_agent_data/miniapp_sync/" "YYYY-MM-DD"

# 步骤2：重新上传（含音频文件 + 更新后的 briefing.json）
python3 /Users/zewujiang/Desktop/AICo/codebuddy-invest/.codebuddy/skills/investment-agent-daily-app/scripts/upload_to_cloud.py "/Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows/investment_agent_data/miniapp_sync/" "YYYY-MM-DD"
```

> **generate_audio.py 双模式**：
> - **模式A（推荐）**：检测到 briefing.json 中已有 voiceText（>200字）→ 直接读取，仅调用 TTS
> - **模式B（fallback）**：voiceText 为空 → 自动从4个JSON代码拼接播报文稿，再调用 TTS

### 第四阶段：完成交付 + 输出确认

#### 4.1 搜索执行日志（强制输出 — v5.7 新增）

> **目的**：让用户一眼核验搜索是否充分，AI 无法"声称搜了但没搜"。每次执行必须在交付确认前输出此表。

```
### 🔍 搜索执行日志
| # | 层次 | 搜索关键词/URL | 结果摘要 | 有效数据提取 |
|---|------|---------------|---------|------------|
| 1 | 广播层 | web_search "..." | X条有效 | ✅/❌ |
| 2 | T1定向 | web_search "..." | X条 | ✅/❌ |
| 3 | ARK深挖 | web_fetch cathiesark.com/... | X笔交易 | ✅/❌ |
| ... | ... | ... | ... | ... |
| **合计** | — | **web_search: {N}次 / web_fetch: {M}次** | — | **达标✅ / 不达标❌** |

达标基线：Heavy≥10+1 / Weekend≥8+1 / 13F≥14+1（RULE SEVEN）
```

**强制规则**：
- 每次 web_search / web_fetch 调用都必须记录在表中（不允许遗漏）
- 合计行的 web_search/web_fetch 次数必须与实际调用次数一致
- 不达标时禁止进入交付确认，必须补充搜索直到达标

#### 4.2 交付确认信息

输出交付确认信息：

```
📱 投研鸭小程序数据更新完成 — {YYYY-MM-DD}

✅ briefing.json → 简报页（核心事件+判断+建议+情绪+聪明钱）
✅ markets.json  → 市场页（美股+M7+亚太+大宗+加密+GICS热力图）
✅ watchlist.json → 标的页（5板块×{N}只标的+详情+metrics）
✅ radar.json    → 雷达页（安全信号+聪明钱+本周前瞻+预测市场+异动信号）

☁️ 云数据库上传：{成功/失败数}
📊 数据完整度：{百分比}
```

### 第五阶段：执行复盘（v5.7 新增 — 30秒快检，强制触发）

> **目的**：每次执行后强制触发「是否需要回写 Skill」判断，从"想起来才写"变成"每次都检查"。
> **耗时**：约30秒，三个问题自问自答后输出结论。

每次执行完毕后，AI 必须自问并输出以下三行：

```
### 🔄 执行复盘
1. 🆕 **本次有没有遇到新的堵点/数据源异常？**
   → {有/无} → {有：简述问题 + 已写入 known-pitfalls.md 堵点#XX / 无}
2. 📋 **本次有没有发现规范覆盖不到的新场景？**
   → {有/无} → {有：简述场景 + 已更新 SKILL.md/json-schema.md XX部分 / 无}
3. 🎯 **trafficLights 7项是否仍是最优组合？**
   → {是/否} → {否：提议将 XX 替换为 YY，理由：... / 是}
```

**规则**：
- **三项全为"无/是"时**：输出 `✅ 本次执行无新增问题，Skill 规范无需更新`
- **任一项有变更**：必须在本次会话中完成回写（不允许"下次再改"），回写后更新顶部「规范健康度快照」
- **此阶段为强制步骤**，不可跳过。即使赶时间，3行自问也只需30秒

---

## 优先级声明

| 优先级 | 维度 | 说明 |
|--------|------|------|
| **P0** | JSON Schema 100% 对齐 | 每个字段都必须存在且类型正确 |
| **P0** | 数据准确性 | RULE ZERO — 只用实时搜索数据 |
| **P0** | sparkline 完整性 | 每个标的必须有 7 天走势数据 |
| **P1** | 数据精确性 | 收盘价 $XXX.XX、涨跌幅 ±X.XX% |
| **P1** | 板块均衡 | 5 个板块（前4核心板块各≥2标的） |
| **P2** | 分析质量 | analysis/reason/summary 内容有洞察 |
| **P3** | metrics 精确性 | PE/市值/营收增速等可用最新季度数据 |

---

## 致命错误清单（29条 — 零容忍，详细事故复盘见 known-pitfalls.md）

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
| 16 | 可选字段枚举值越界 | `predictions[].source` 填了非允许值（仅限 Polymarket/Kalshi/CME FedWatch）；`_meta.sourceType` 填了非枚举值 |
| 17 | 字段内容边界越界 | `coreEvent.chain` 重复了 brief 中已有的具体数字；`marketSummaryPoints` 汇总重复了 coreEvent/globalReaction 中的具体数字 — 详见 json-schema.md |
| 18 | 数据时效性错误 | ①`brief` 字段超过25字（应极简10-25字，非长句）；②生成时美股未收盘却在 globalReaction/coreEvent 中使用期货盘前数据并当作收盘数据呈现，未注明「盘前」；③`timeStatus.marketStatus` 填写错误（北京时间19:22=纽约盘前07:22，应填「盘前交易」而非「美股已收盘」）；④`dataTime` 未注明数据时态（盘前/盘中/盘后/收盘） |
| 19 | insightChain 数字与字段值方向矛盾 | insightChain/insight 文字中的涨跌方向或数字与 price/change 字段值矛盾（如 change=-2.73 但文字写"上涨"），JSON 生成阶段必须用字段值反向校验文字 |
| 20 | coreJudgments.logic 使用段落散文 | `logic` 字段必须使用「短句+箭头（→）三段式」：`触发原因 → 传导路径 → 核心结论`，每段≤15字，整条≤50字；禁止：段落散文、分号连接长句、bullet点（`•`）列举；前端无 💡 图标前缀，文字直接顶格，箭头自带方向感，无需其他修饰符号 |

| 21 | takeaway 缺少【】关键词标红 | takeaway 文本中核心关键词必须用中文方括号【】包裹（3~5个），前端 `parseTakeaway()` 正则提取后渲染为红色高亮；无【】则全段黑色，关键行动指令被淹没；标红过多（≥6个）等于没有重点；选择标红的优先级：行动指令（以防御为主）> 关键条件/数据（VIX回落至20以下）> 事实描述 |

| 22 | **交易数据来源错误（RULE ZERO-A 违规）** | 价格/涨跌幅/汇率只允许来自直接行情平台（Google Finance/AkShare/FRED等），禁止从新闻媒体提取。自查：能追溯到 web_fetch URL 吗？→ 详见 known-pitfalls.md 堵点#22 |
| 23 | **insightChain 数字与字段值不一致** | insightChain 文字中的数字必须与对应 price/change 完全一致，禁止方向矛盾。先确认字段值再写文字 → 详见 known-pitfalls.md 堵点#23 |
| 24 | **脚本覆盖 AI 字段（方案A 已解决）** | 脚本只写 sparkline/chartData 两个数组字段，其他所有字段永不触碰。未来修改脚本时：硬编码中文文本=危险信号 → 详见 known-pitfalls.md 堵点#24 |
| 25 | **chain[].url / references 被漏填** | 非付费墙 source 必须有 https url；每条 coreJudgments 必须有 references。口诀：「有 source 必有 url，有判断必有 references」→ 详见 known-pitfalls.md 堵点#25 |
| 26 | **riskNote 未升级为 riskPoints 数组** | 必须同时输出 riskPoints（主）+ riskNote（兼容），每条只说一个风险点（15-50字），前端 🛡️ 图标 → 详见 known-pitfalls.md 堵点#26 |
| 27 | **价格使用模糊前缀（~/$约/左右）** | 所有 JSON 价格/涨跌幅必须是行情源精确数值，禁止 `~` `≈` `约` `左右` 等模糊修饰 → 详见 known-pitfalls.md 堵点#27 |
| 28 | **smartMoneyDetail 知识库快照污染（RULE ZERO-B）** | action 中每个数字必须追溯到本次 web_search/web_fetch 结果，知识库只是搜索雷达不是数据源。口诀：「说不出来源就删掉」→ 详见 known-pitfalls.md 堵点#28 |
| 29 | **聪明钱搜索覆盖不足（RULE SEVEN）** | 5层搜索必须完整执行（Heavy≥10+1/Weekend≥8+1/13F≥14+1），不看产出条数只看搜索是否充分 → 详见 known-pitfalls.md 堵点#29 |

---

| 文件 | 内容 | 用途 |
|------|------|------|
| [json-schema.md](references/json-schema.md) | **4个JSON的完整字段规范（核心文件）** | JSON 生成阶段 |
| [data-collection-sop.md](references/data-collection-sop.md) | 数据采集批次SOP + Google Finance模板 + 数据源优先级 | 采集阶段 |
| [stock-universe.md](references/stock-universe.md) | **5板块标的池 + 板块分类规则 + metrics采集指南** | watchlist 生成 |
| [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md) | AI产业链24环标的知识库 | batch 0b扫描 |
| [fund-universe.md](references/fund-universe.md) | 三梯队26家基金+策略师追踪清单 | batch 4扫描 |
| [media-watchlist.md](references/media-watchlist.md) | 三级媒体清单+扫描SOP | batch 0/0a扫描 |
| [data-source-priority.md](references/data-source-priority.md) | 数据源优先级表 + 降级路径 | 全流程 |
| [known-pitfalls.md](references/known-pitfalls.md) | App专属已知堵点与降级路径 | 全流程 |
| [weekend-mode.md](references/weekend-mode.md) | Weekend 模式完整规范（采集+产出+工作流） | 周末/休市日执行 |

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

> 详细降级路径表 → [data-source-priority.md §四](references/data-source-priority.md) | 完整堵点清单 → [known-pitfalls.md](references/known-pitfalls.md)

**核心原则**：准确性高于连续性。
- 直接行情源异常 → 只切换到**同类直接行情源**，禁止退化到新闻页
- sparkline/chartData 缺失 → 回采重试，禁止估算生成
- 某标的关键行情无法获取 → 允许替换同板块备选标的，但必须重新核验全量字段
- 任何环节如触发核心行情缺失，**必须阻断发布**，而不是带病上线

---

## 版本历史

> 详细 Changelog 见本文件顶部。完整变更记录见 git log。
