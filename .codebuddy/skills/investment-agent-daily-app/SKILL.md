---
name: investment-agent-daily-app
description: 当用户提到「投资App」「小程序数据」「投研鸭数据」「app数据更新」「miniapp sync」或类似关键词时，自动执行投研鸭小程序数据生产全流程，输出4个原生结构化JSON并上传微信云数据库。
---

# 投研鸭小程序数据生产 — 标准工作流 v8.2

> **版本**: v8.2 (2026-04-08 13:15) — FATAL/WARN 双级校验 + R9 自动比对
> **主控文档**：本文件为精炼主控（≤300行），详细规则通过引用按需加载。
> **核心改造**：validate.py v2.0 自动化校验（35+项 + FATAL/WARN 双级），AI 终审只需关注文本质量。

### 规范健康度快照

| 指标 | 值 | 上次更新 |
|------|------|---------|
| 致命错误条数 | 29 | 2026-04-06 |
| 已知堵点条数 | 40 | 2026-04-08 |
| trafficLights 阈值版本 | v4.8 | 2026-04-05 |
| 上次月度审计 | 未执行 | — |
| 连续零事故天数 | 0 | 2026-04-08 |
| 回归门禁条数 | 9 (R1-R9, 含3项FATAL) | 2026-04-08 |
| 持仓缓存版本 | v1.0 (2025Q4 13F) | 2026-04-08 |
| **validate.py 版本** | **v2.0 (35+项 FATAL/WARN双级门禁)** | **2026-04-08** |

### v8.2 Changelog（2026-04-08 13:15）
- **validate.py v1.1→v2.0**：FATAL/WARN 双级机制——R2(positions≥Top10)/R3(禁止"待更新")/R9(新增,holdings-cache一致性) 为 FATAL 级，`--skip-warn` 无法绕过
- **新增 R9 校验**：自动比对 radar.smartMoneyHoldings 与 holdings-cache.json，确保机构数/positions数/weight值完全一致
- **run_daily.sh v4.0→v5.0**：`--skip-validate` 废弃→`--skip-warn`（向后兼容自动映射），FATAL 级退出码=3 单独处理
- **known-pitfalls.md v3.5→v3.6**：新增堵点 #42(Heavy不引用cache)/#43(skip-validate万能逃生口)，堵点总数41→43
- **radar.json 修复**：从 holdings-cache.json 精确复制3家×Top10完整持仓，修复"待更新"+缺失ARK问题

### v8.1 Changelog（2026-04-08 11:30）
- **validate.py v1.0→v1.1**：新增 V27(Insight长度30-80字) + V28(metrics精确6项) + V29(logic箭头→三段式)，总项数 30+→35+
- **run_daily.sh v3.0→v4.0**：版本号+头部注释更新，精简架构说明
- **known-pitfalls.md v3.4→v3.5**：全文精简（去除冗余描述，从 ~170行→~110行），保留核心信息
- **json-schema.md 精简**：压缩重复注释（takeaway/title/logic/sentiment/actionHints/riskPoints/Insight），减少认知负荷
- **SKILL.md 数据修正**：堵点条数 40→41 对齐实际

### v8.0 Changelog（2026-04-08 10:30）
- **🏗️ Harness Engineering 架构升级（系统性治理规范膨胀）**：
  - **新增 `validate.py` v1.0**（30+项自动化校验）：结构校验+枚举校验+数组长度+数值一致性+riskScore公式+trafficLights阈值+文本质量+回归门禁R1-R8，全部由脚本机械执行，**AI终审从53+项降为仅文本质量审读**
  - **新增 `golden-baseline.json` v1.0**：结构化基线定义文件，所有门禁参数/枚举值/公式常量的机器可读单一信息源
  - **新增 `formulas.md` v1.0**：红绿灯阈值+riskScore公式+综合评级+sentimentScore映射的唯一权威源，消除SKILL.md/json-schema.md重复定义
  - **新增 `templates.md` v1.0**：交付模板集合（搜索日志/确认信息/diff/复盘模板）外迁集中管理
  - **新增 `CHANGELOG.md`**：完整版本历史归档，SKILL.md只保留最近2版
  - **SKILL.md 瘦身**：从 972 行→≤300行，认知负荷降 70%
  - **run_daily.sh v3.0→v4.0**：新增第0.5步 validate.py 自动化校验，不通过禁止上传

### v7.5 Changelog（2026-04-08 09:28）
- 质量守护体系三层防护：R1-R8回归门禁+holdings-cache.json+diff输出
- 详见 [CHANGELOG.md](CHANGELOG.md)

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

## 八大铁律

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
| **RULE SEVEN** | 聪明钱搜索广覆盖+产出精选（Heavy≥10+1次 / Refresh≥2+4次） |

---

## 触发条件与四档内容引擎

**触发关键词**：投资App / 小程序数据 / 投研鸭数据 / app数据更新 / miniapp sync

| 时机 | 模式 | `_meta.sourceType` | 详细规范 |
|------|------|--------------------|---------|
| 周一~周五（当天首次） | **Heavy** | `heavy_analysis` | 本文件全流程 |
| 工作日后续每4小时 | **Refresh** | `refresh_update` | → [refresh-mode.md](references/refresh-mode.md) |
| 周末/休市日 | **Weekend** | `weekend_insight` | → [weekend-mode.md](references/weekend-mode.md) |

### 模式判定逻辑

```
今天周几？
  → 周六/周日/休市日 → Weekend
  → 周一~周五 → 当天 miniapp_sync/ 已有4个JSON？
    → 否 → Heavy（当天首次）
    → 是 → _meta.sourceType?
      → heavy_analysis/refresh_update → Refresh
      → weekend_insight → Heavy（覆盖周末版）
      → 不完整 → Heavy（降级安全网）
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

## 工作流（7个阶段）

### 第零阶段：日期检测 + 模式路由 + 环境准备
- `date "+%A %Y-%m-%d %H:%M:%S"`
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

### 第2.3阶段：AI 直填公式
**所有公式唯一权威源** → [formulas.md](references/formulas.md)
- 红绿灯 7项阈值判定 → `formulas.md §一`
- riskScore/riskLevel/riskAdvice → `formulas.md §二`
- metrics 综合评级 → `formulas.md §三`
- sentimentScore→sentimentLabel → `formulas.md §四`

### 第2.5阶段：JSON 完整性终审
> **v8.0 核心改造**：30+项结构/数据/一致性检查由 `validate.py` 脚本自动执行。AI 只需关注以下**人工审读项**：
>
> **AI 人工审读（validate.py 无法覆盖的文本质量）**：
> 1. analysis/reason/summary 文本是否有洞察（非空洞废话）
> 2. coreJudgments.logic 是否箭头三段式（→ 符号串联）
> 3. Insight 是否为决策信号式（非新闻摘要）
> 4. riskAdvice 是否动态生成（非模板套话）
> 5. 播报文稿是否 TTS 友好
>
> **Refresh 模式**：使用精简终审 → [refresh-mode.md §终审](references/refresh-mode.md)

#### 回归门禁 R1-R9（Heavy/Weekend 模式，validate.py 自动执行）
门禁口诀：`3家·Top10·无待更新·ARK在·交叉一致·2条动向·段永平有权重·三梯队满·cache一致`
**FATAL 级（R2/R3/R9）**：不可被 `--skip-warn` 绕过，必须修复

#### 持仓数据缓存引用规则
**缓存文件** → [holdings-cache.json](references/holdings-cache.json)
非13F窗口期直接引用缓存，禁止凭记忆修改。13F窗口期（2/5/8/11月中旬）搜索最新数据并更新缓存。

### 第三阶段：sparkline补全 + 自动化校验 + 上传（一键执行）

```bash
bash /Users/zewujiang/Desktop/AICo/codebuddy-invest/.codebuddy/skills/investment-agent-daily-app/scripts/run_daily.sh {YYYY-MM-DD}
```

> **run_daily.sh v5.0 执行流程**：
> 1. 第0步：JSON 语法校验（硬依赖）
> 2. **第0.5步：validate.py v2.0 自动化校验（FATAL级不可绕过 / WARN级可 --skip-warn）**
> 3. 第1步：sparkline/chartData 补全（软依赖）
> 4. 第2步：上传云数据库
> 5. 第3步：同步公开API

### 第3.5阶段：语音播报生成（Heavy 模式，Refresh 跳过）
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
3. 质量回归 diff（Heavy 强制） → `templates.md §三`
4. 同步公开 API → `sync_to_edgeone.sh`

### 第五阶段：执行复盘（30秒快检，强制）
**复盘模板** → [templates.md §四/§五](references/templates.md)
- Heavy：3项自问（新堵点/新场景/trafficLights组合）
- Refresh：2项精简（新堵点/数据一致性）

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
| **[formulas.md](references/formulas.md)** | 🆕 所有公式唯一权威源（红绿灯+riskScore+评级+sentiment映射） | 第2.3阶段 |
| **[golden-baseline.json](references/golden-baseline.json)** | 🆕 结构化基线定义（validate.py参数源+枚举值+公式常量） | validate.py 自动加载 |
| **[templates.md](references/templates.md)** | 🆕 交付模板集合（搜索日志+确认信息+diff+复盘模板） | 第四/五阶段 |
| [data-collection-sop.md](references/data-collection-sop.md) | 数据采集批次SOP | 采集阶段 |
| [stock-universe.md](references/stock-universe.md) | 5板块标的池+选股规则+metrics指南 | watchlist 生成 |
| [fund-universe.md](references/fund-universe.md) | 三梯队26家基金+策略师清单 | batch 4 扫描 |
| [media-watchlist.md](references/media-watchlist.md) | 三级媒体清单 | batch 0/0a 扫描 |
| [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md) | AI产业链24环标的库 | batch 0b 扫描 |
| [data-source-priority.md](references/data-source-priority.md) | 数据源优先级+降级路径 | 全流程 |
| [known-pitfalls.md](references/known-pitfalls.md) | 已知堵点40条+降级路径 | 全流程 |
| [refresh-mode.md](references/refresh-mode.md) | Refresh 模式完整规范 | 工作日增量刷新 |
| [weekend-mode.md](references/weekend-mode.md) | Weekend 模式完整规范 | 周末/休市日 |
| [holdings-cache.json](references/holdings-cache.json) | 持仓数据缓存（伯克希尔+段永平+ARK各Top10） | 非13F窗口期兜底 |
| [briefing-golden-sample.json](references/briefing-golden-sample.json) | 黄金样本（2026-04-06版） | 质量基线参考 |
| [CHANGELOG.md](CHANGELOG.md) | 完整版本历史归档 | 历史查阅 |

---

## 版本历史

> 详细 Changelog 见本文件顶部（最近2版）。完整历史见 [CHANGELOG.md](CHANGELOG.md)。
