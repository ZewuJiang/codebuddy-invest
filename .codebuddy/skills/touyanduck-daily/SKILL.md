---
name: touyanduck-daily
description: 当用户提到「投资App」「小程序数据」「投研鸭数据」「app数据更新」「miniapp sync」或类似关键词时，自动执行投研鸭小程序数据生产全流程，输出4个原生结构化JSON并上传微信云数据库。
---

# 投研鸭小程序数据生产 — 标准工作流 v13.1

> **版本**: v13.1 (2026-05-08) — 全链路稳定性修复（validate v6.2 + upload修复 + app-sync WARN策略）
> **主控文档**：本文件为精炼主控，详细规则通过引用按需加载（四批分层：L1/L2/L3/L4）。
> **完整版本历史** → [CHANGELOG.md](CHANGELOG.md)

### 规范健康度快照

| 指标 | 值 | 上次更新 |
|------|------|---------|
| 致命错误条数 | 29 | 2026-04-13 |
| 已知堵点条数 | 65（活跃），6条归档 | 2026-05-07 |
| trafficLights 阈值版本 | v4.8 | 2026-04-05 |
| 上次月度审计 | 未执行 | — |
| 连续零事故天数 | 0 | 2026-04-21 |
| 回归门禁条数 | 9 (R1-R9) + **20项FATAL** | 2026-05-08 |
| 持仓缓存版本 | v1.1 (2025Q4 13F 已修正) | 2026-04-08 |
| **validate.py 版本** | **v6.2 (57项 含V48+V49 FATAL，20 FATAL，V5升级FATAL+R7正则修复)** | **2026-05-08** |
| **auto_compute.py 版本** | **v3.1 (16类字段自动计算，含ARK asOf自动更新)** | **2026-04-23** |
| **run_daily.sh 版本** | **v6.5（Phase B1.5 新增第2.5步写入upload_hash）** | **2026-05-07** |
| **anchor_fetcher.py 版本** | **v1.1（CNH/DXY/VIX全备源补强，yfinance重试，fetched_at时效）** | **2026-05-07** |
| **radar.js asOf 处理** | **v7.1（括号清理正则加强，YYYY-MM-DD输出）** | **2026-04-21** |
| **data-collection-sop.md** | **v3.1 (含§0.4自媒体陷阱 +§0.10 JSON双引号)** | **2026-04-21** |
| **inline-verifier-rules.md** | **v1.3 (16项可内联FATAL前置校验/4项不可内联)** | **2026-05-08** |
| **known-pitfalls.md** | **v5.6 (65条活跃 + 6条归档)** | **2026-05-07** |
| **质量基准** | **4/9 22:27 版 (53/54 PASS, 0 FATAL)** | **2026-04-09** |

---

## 产出质量宪章（4/8 基准 — 不可降级）

> **一句话**：高盛级智慧，$10级个人投资者可读性。**搜索要广（不漏重要信息），产出要精（少而精的决策信号）**。

| 原则 | 要求 |
|------|------|
| **数据准确** | 每个数字可追溯到本次搜索，price/sparkline/change 三者自洽，搜索不到必须重试2-3次 |
| **内容严谨** | 结论+论据清晰对应，禁止模糊表述（"市场表现不一"等废话） |
| **精选不凑数** | 大老板看"决策信号"不看"信息堆砌"。5条精选 > 15条罗列 |
| **简单明了** | 每句话有信息增量，不冗余不啰嗦，观点+论据一句话说完 |
| **质量基线** | validate.py 57项校验, **0 FATAL**（20项FATAL全通过）方可上传。**目标：0 WARN**（WARN ≤1 可接受） |
| **重试机制** | 搜索失败 → 4级降级重试（Google Finance→StockAnalysis→web_search→东方财富）。多花几分钟没关系 |

---

## 定位与使命

> **读者**: 投研鸭微信小程序（机器消费）
> **产出物**: 4个原生结构化 JSON（briefing / markets / watchlist / radar）
> **核心宗旨**: 100% 完整、精确、结构化数据，让每个组件"满血渲染"
> **与 `investment-agent-daily` 的关系**: 完全独立。`daily` 输出 MD/PDF 给人读，本 Skill（`touyanduck-daily`）输出 JSON 给机器读。

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
| **RULE ZERO-C** | **重大事件（模型发布/公司财务/政策）必须到官方源核实，不得仅凭中文自媒体标题采信**（2026-04-20 GPT-6虚假信息事故教训，血泪固化） |
| **RULE ONE** | JSON 完整性——每个必填字段都必须有精确值，严禁空值 |
| **RULE TWO** | 数据类型严格——`change`=number, `sparkline`=number[], 枚举值受控 |
| **RULE THREE** | Schema 对齐——100% 对齐 [json-schema.md](references/json-schema.md) |
| **RULE FOUR** | sparkline 必填——7天历史走势由脚本自动补全，禁止估算 |
| **RULE FIVE** | 板块均衡——4核心板块（ai_infra/ai_app/cn_ai/smart_money）各≥2标的；第5板块 hot_topic 可为空 |
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

## 工作流（v11.0 — 并行采集 + Context 压缩 + 内联自校验）

### Phase 0：日期检测 + 模式路由 + 环境准备 + L1 加载
- `date "+%A %Y-%m-%d %H:%M:%S"`
- 周一~周五 → Standard / 周末 → Weekend
- 每月1日执行月度规范审计 → [templates.md §六](references/templates.md)
- 确认输出目录存在
- **L1 加载**：读取 [schema-compact.json](references/schema-compact.json) + [formulas.md](references/formulas.md) + [golden-baseline.json](references/golden-baseline.json)

### Phase 1：实时数据采集（🆕 4 组并行 + 1 组串行 + Context 压缩）

**采集SOP** → [data-collection-sop.md](references/data-collection-sop.md)（v3.1 含 §0.8 并行分组 + §0.9 最小字段集 + §0.10 JSON双引号防治）

**L2 按组加载**：Phase 1 启动前，加载各并行组所需的知识库：
- P1 需要：[data-collection-sop.md](references/data-collection-sop.md) + [media-watchlist.md](references/media-watchlist.md) + [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md)
- P4 需要：[fund-universe.md](references/fund-universe.md) + [data-source-priority.md](references/data-source-priority.md)

**并行执行**（在同一 AI turn 中发出全部工具调用）：

```
├── [并行] P1: Batch 0+0a+0b — 媒体+AI产业链扫描（3-7次 web_search）
├── [并行] P2: Batch 1a-1d — 美股行情 web_fetch（22-27次）
├── [并行] P3: Batch 2+3 — 亚太+大宗/汇率/加密（4-6次）
└── [并行] P4: Batch 4 — 基金动向（8-12次 search + 1次 fetch）
    │
    ├──── 同步屏障 ────┤ （P1-P4 全部完成才可通过）
    │
    └── [串行] S1: Batch 5→6→A（依赖 P2 GICS 结果）
```

**🔴 Context 压缩铁律**：每次 web_fetch/web_search 返回后，**必须立即提取最小字段集，丢弃原始 HTML/snippet**。详见 [data-collection-sop.md §0.9](references/data-collection-sop.md)。

### Phase 1.5：数据完整性门禁（强制）
三大指数+M7+VIX / GICS 11板块 / 亚太4-6指数 / **大宗6项（🔴黄金/布伦特/WTI/DXY/10Y美债/CNH，缺一不可，V5 FATAL）** / watchlist 5板块 / radar 7项红绿灯 / coreEvent+coreJudgments×3 / globalReaction 6项 / smartMoney 2-4条 / events 3-4条

> ⚠️ **commodities 漏写是高频事故（5/8事故）**：`黄金XAU / 布伦特原油 / WTI原油 / 美元指数DXY / 10Y美债 / 离岸人民币CNH` 必须全部填写，缺任何一项将触发 V5 FATAL 阻断上传。

### Phase 1.8：L3 加载（Phase 2 前补读）
读取：[json-schema.md](references/json-schema.md) + [stock-universe.md](references/stock-universe.md) + [holdings-cache.json](references/holdings-cache.json) + [inline-verifier-rules.md](references/inline-verifier-rules.md)

### Phase 2：结构化 JSON 生成 + 🆕 Generator-Verifier 内联自校验

**生成顺序**（4 个 JSON 有强交叉依赖，必须串行）：

| 步骤 | 生成 | 内联校验 | 校验规则来源 |
|------|------|---------|------------|
| **2A** | briefing.json | 写完后立即执行 B1-B13 校验 | [inline-verifier-rules.md §二](references/inline-verifier-rules.md) |
| **2B** | markets.json | 写完后立即执行 M1-M11 校验 | [inline-verifier-rules.md §三](references/inline-verifier-rules.md) |
| **2C** | watchlist.json | 写完后立即执行 W1-W12 校验 | [inline-verifier-rules.md §四](references/inline-verifier-rules.md) |
| **2D** | radar.json | 写完后立即执行 D1-D10 校验 | [inline-verifier-rules.md §五](references/inline-verifier-rules.md) |
| **2E** | — | 跨 JSON 一致性终检 X1-X6 | [inline-verifier-rules.md §六](references/inline-verifier-rules.md) |

**Generator-Verifier 循环规则**：FATAL 项不通过 → 定位修复 → 重新校验（最多 2 次重试，共 3 轮）→ 仍 FAIL 则记录继续（Phase 3 validate.py 终裁）。

**生成规则不变**：
1. **逐字段对照 Schema** → [json-schema.md](references/json-schema.md)
2. **枚举值受控** → [golden-baseline.json](references/golden-baseline.json)
3. **数据类型严格** → `change`=number, `price`=string
4. **纯文本** → 禁止 markdown 语法
5. **sparkline/chartData** → 方案A 双轨分工，脚本第三阶段自动补全

### Phase 2.3：AI 填写原始数值（公式由脚本自动计算）

> AI 只需填写原始数值，所有 15 类公式计算由 `auto_compute.py` 自动执行。详见 [inline-verifier-rules.md §九](references/inline-verifier-rules.md)。

**AI 需要填写的字段**：
- `trafficLights[].value` — 7项指标的实际数值（从行情源采集）
- `trafficLights[].threshold` — 阈值说明文字（复制 [formulas.md §一](references/formulas.md)）
- `sentimentScore` — 情绪分数（0-100，基于多维度独立打分）
- `watchlist.stocks[].price` / `change` — 标的价格和涨跌幅

**所有公式唯一权威源** → [formulas.md](references/formulas.md)

### Phase 2.5：JSON 完整性终审（人工审读项）
> AI 人工审读（脚本无法覆盖的文本质量）：
> 1. analysis/reason/summary 文本是否有洞察（非空洞废话）
> 2. coreJudgments.logic 是否箭头三段式（→ 符号串联）
> 3. Insight 是否为决策信号式（非新闻摘要）
> 4. riskAdvice 是否动态生成（非模板套话）

#### 回归门禁 R1-R9（validate.py 自动执行）
门禁口诀：`3家·Top10·无待更新·ARK在·交叉一致·2条动向·段永平有权重·三梯队满·cache一致·无期权`
**FATAL 级（R2/R3/R9/V39）**：不可被 `--skip-warn` 绕过，必须修复

#### 持仓数据缓存引用规则
**缓存文件** → [holdings-cache.json](references/holdings-cache.json)
非13F窗口期直接引用缓存，禁止凭记忆修改。13F窗口期（2/5/8/11月中旬）搜索最新数据并更新缓存。

### Phase 3：自动计算 + sparkline补全 + 自动化校验 + 上传（一键执行）

> **🚨 自我守卫约束（最高优先级）**
>
> **本 Phase 是整个 Skill 的终极交付物。没有执行 run_daily.sh = 任务完全失败。**
>
> 1. **禁止省略**：无论 Phase 1-2 消耗了多少 token，Phase 3 必须执行。如果感知到上下文接近上限，**立即跳过所有剩余 Phase 2 内联校验**，直接执行下方 bash 命令。
> 2. **一句 bash 即可**：Phase 3 只需要一次 Bash 工具调用，耗时 ~60 秒，token 消耗极低。
> 3. **绝不允许**输出"已生成 JSON，后续请手动执行 run_daily.sh"——这等同于任务失败。
> 4. **兜底保障**：即使 AI 被截断未执行本步骤，外层 `app-sync.sh` v2 会自动检测并强制调用。但 AI **仍应主动执行**以获得完整日志和错误反馈。
> 5. **执行时机**：Phase 2 的 4 个 JSON 全部写入完成后，**立即**执行（不要先做复盘/总结/其他步骤）。

```bash
bash /Users/zewujiang/Desktop/AICo/codebuddy-invest/.codebuddy/skills/touyanduck-daily/scripts/run_daily.sh {YYYY-MM-DD}
```

> **run_daily.sh v6.5 执行流程**：
> 0. **第-1步：日期子目录→根目录同步**（自动cp `miniapp_sync/YYYY-MM-DD/*.json` → `miniapp_sync/*.json`，确保工具链读到今日数据）
> -0.5. **涨跌方向快速目视摘要**（打印三大指数/M7/大宗的涨跌符号，1秒内目视发现全线方向异常）
> 1. 第0步：JSON 语法校验（硬依赖）
> 2. **第0.3步：auto_compute.py 自动计算公式字段**
> 3. **第0.4步：anchor_fetcher.py v1.1 真值锚点拉取**（FRED/yfinance/CoinGecko，覆盖6字段，供 V48 比对）
> 4. **第0.5步：validate.py v6.2 自动化校验（57项，20项FATAL不可绕过，含V5关键数组+V48/V49真值锚点+上传一致性门禁）**
> 5. 第1步：sparkline/chartData 补全（软依赖）
> 6. 第1.5步：强制刷新 `_meta.generatedAt` 为当前时间
> 7. 第2步：上传云数据库（**P0 — 唯一分发通道，小程序直接读取**）← 终点
> 8. **第2.5步：写入上传 Hash**（记录4文件 sha256，供 V49 检测"改了但未重新上传"堵点#65）

> ⚠️ **数据分发通道**：微信云数据库（第2步）= 唯一分发通道，小程序前端直接读取。

### Phase 4：完成交付 + 输出确认
**L4 加载**：[templates.md](references/templates.md) + [known-pitfalls.md](references/known-pitfalls.md)
1. 搜索执行日志 → `templates.md §一`
2. 交付确认信息 → `templates.md §二`
3. 质量回归 diff（强制） → `templates.md §三`

### Phase 5：执行复盘（30秒快检，强制）
**复盘模板** → [templates.md §四](references/templates.md)
3项自问：新堵点/新场景/trafficLights组合

---

## Context 压缩铁律（v11.0 新增）

> **一句话**：每次 web_fetch/web_search 返回后，**立即提取最小字段集，丢弃原始 HTML/snippet**。绝对禁止将原始页面内容保留在上下文中。

**详细字段定义** → [data-collection-sop.md §0.9](references/data-collection-sop.md)
**目标**：Phase 1 上下文从 ~76k 压缩至 ~35k，腾出 ~40k 余量给 Phase 2 JSON 生成。

---

## References 分层加载（v11.0 新增）

| 批次 | 时机 | 加载文件 | 理由 |
|------|------|---------|------|
| **L1** | Phase 0 | SKILL.md(自动) + schema-compact.json + formulas.md + golden-baseline.json | 核心铁律+公式+枚举 |
| **L2** | Phase 1 前 | data-collection-sop.md + data-source-priority.md + media-watchlist.md(P1) + fund-universe.md(P4) | 各并行组只读所需 |
| **L3** | Phase 2 前 | json-schema.md + stock-universe.md + holdings-cache.json + inline-verifier-rules.md | JSON 生成+自校验 |
| **L4** | Phase 4 | templates.md + known-pitfalls.md | 交付+复盘 |

> 按阶段需求加载，控制上下文负担。禁止 Phase 0 一次性加载全部 references。

---

## Generator-Verifier 内联自校验（v11.0 新增）

> **定位**：Phase 2 前置过滤，validate.py 仍是终极门禁。两层防护，不是替代。
> **完整规则** → [inline-verifier-rules.md](references/inline-verifier-rules.md)

**16/20 项 FATAL 可在 Phase 2 内联检测**（写完即检，避免 Phase 3 整体重来）：
V5, V6, V24, V36, V38, V39, V40, V41, V42, V43, V44, V45, V46, R1, R2, R3

**4 项 FATAL 不可内联**（必须等 Phase 3 脚本执行）：
R9（需 holdings-cache.json）、V_TL（需 auto_compute 执行后）、V48（需 anchor_fetcher.py 生成 anchors.json）、V49（需上传后写入 .last_upload_hash.json）

---

## 每日操作 Checklist

> 完整 Checklist（J1-J10 / P1-P5 / V1-V4）→ [daily-checklist.md](references/daily-checklist.md)

**执行命令**：
```bash
bash /Users/zewujiang/Desktop/AICo/codebuddy-invest/.codebuddy/skills/touyanduck-daily/scripts/run_daily.sh YYYY-MM-DD
```

**Phase 3 核心预期**：P1 子目录同步 ✅ → P2 JSON语法 ✅ → P3 validate FATAL:0 ✅ → P4 上传 4/0 ✅

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

## 引用文件索引（分层加载）

| 文件 | 内容 | 加载批次 |
|------|------|---------|
| **[schema-compact.json](references/schema-compact.json)** | 机器可读紧凑Schema | **L1** Phase 0 |
| **[formulas.md](references/formulas.md)** | 所有公式唯一权威源 | **L1** Phase 0 |
| **[golden-baseline.json](references/golden-baseline.json)** | 结构化基线定义（validate.py参数源） | **L1** Phase 0 |
| [data-collection-sop.md](references/data-collection-sop.md) | 数据采集SOP v3.1（含并行分组+最小字段集+JSON双引号防治） | **L2** Phase 1 前 |
| [data-source-priority.md](references/data-source-priority.md) | 数据源优先级+降级路径 | **L2** Phase 1 前 |
| [media-watchlist.md](references/media-watchlist.md) | 三级媒体清单（P1组用） | **L2** Phase 1 前(P1) |
| [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md) | AI产业链24环标的库（P1组用） | **L2** Phase 1 前(P1) |
| [fund-universe.md](references/fund-universe.md) | 三梯队26家基金+策略师清单（P4组用） | **L2** Phase 1 前(P4) |
| **[json-schema.md](references/json-schema.md)** | 4个JSON完整字段规范+门禁 | **L3** Phase 2 前 |
| [stock-universe.md](references/stock-universe.md) | 5板块标的池+选股规则 | **L3** Phase 2 前 |
| [holdings-cache.json](references/holdings-cache.json) | 持仓数据缓存（伯克希尔+段永平+ARK各Top10） | **L3** Phase 2 前 |
| **[inline-verifier-rules.md](references/inline-verifier-rules.md)** | Generator-Verifier 内联自校验规则（v1.3 — 16项FATAL可内联/4项不可内联） | **L3** Phase 2 前 |
| [templates.md](references/templates.md) | 交付模板集合 | **L4** Phase 4 |
| [known-pitfalls.md](references/known-pitfalls.md) | 已知堵点65条活跃+6条归档（v5.6） | **L4** Phase 4/5 |
| [daily-checklist.md](references/daily-checklist.md) | 完整每日操作Checklist（J1-J10/P1-P5/V1-V4/故障排查） | **L4** Phase 2后 |
| [weekend-mode.md](references/weekend-mode.md) | Weekend 模式完整规范 | 周末触发时 |
| [briefing-golden-sample.json](references/briefing-golden-sample.json) | 黄金样本（2026-04-06版） | 质量基线参考 |
| [CHANGELOG.md](CHANGELOG.md) | 完整版本历史归档 | 历史查阅 |

---

## 版本历史

> 完整历史见 [CHANGELOG.md](CHANGELOG.md)。
