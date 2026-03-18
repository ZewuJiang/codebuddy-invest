---
name: investment-agent-daily
description: 当用户提到「投资Agent」「每日分析」「投资分析」「每日报告」「investment agent」「晨报」「morning report」或类似关键词时，自动执行投资Agent每日策略简报全流程。
---

# 投资Agent每日策略简报 — 标准工作流 v17.8

> **版本**: v17.8 (2026-03-13) | 新增RULE FIVE成稿终审铁律 + 数据缺失强制处理 + 三轮终审复核
> **主控文档**：本文件为精炼主控，详细规则/知识库/模板/SOP通过引用按需加载。

---

## 报告定位

> **读者**: $10B级个人投资者，集中持仓（约12个标的），低频交易，时间极宝贵
> **风格**: 段永平/巴菲特式价值投资 + 全球宏观视野
> **核心宗旨**: 对过去24小时二级市场的策略信息和动态保持敏锐捕捉。框架是骨架，灵活应变是灵魂。
> **目标**: 5分钟读完，回答三个核心问题：①过去24小时发生了什么？②这对我的持仓有影响吗？③我需要采取行动吗？
> **不是机构研究报告**，是大老板每天早上喝咖啡时的投资参谋简报。

---

## 五大铁律（最高优先级）

| 铁律 | 核心要求 | 详细规则 |
|------|---------|---------|
| **RULE ZERO** | 训练数据全面禁用。所有数据只能来自当期实时搜索。自查三问：①来自搜索？②时间戳≤24h？③可追溯？任一为否→重写 | → [core-rules.md](references/core-rules.md) |
| **RULE ONE** | 数据完整性铁律。表格严禁"—""-""N/A""~""约""小幅"。M7×7+GICS×11+指数×3+VIX+焦点≥2+亚太×4+大宗×6全部精确值 | → [core-rules.md](references/core-rules.md) |
| **RULE TWO** | 段落去重。同一事件只在最相关段落出现一次：§3写个股事件，§4写机构动向，不交叉重复 | → [core-rules.md](references/core-rules.md) |
| **RULE THREE** | AI产业链敏感度。大老板已汇报标的优先覆盖，AI全产业链24环主动扫描，中英文交叉验证 | → [core-rules.md](references/core-rules.md) |
| **RULE FOUR** | 基金&大资金覆盖完整性。三梯队26家（一级核心8家/二级追踪10家/三级雷达8家），策略师观点追踪 | → [core-rules.md](references/core-rules.md) |
| **RULE FIVE** | **成稿终审铁律（v17.8）**。数据缺失宁迟勿糊（至少3个数据源穷尽搜索）；成稿后逐表格逐单元格扫描（收盘价必须$XXX.XX/涨跌幅必须±X.XX%）；三轮终审复核（数据轮→逻辑轮→格式轮）全通过后一次性输出最终版。**严禁"收涨""上涨""+正"等模糊描述出现在数值列** | → [core-rules.md](references/core-rules.md) + [data-collection-sop.md](references/data-collection-sop.md) §七/§八 |

---

## 触发条件与报告日历

**触发关键词**：投资Agent / 每日分析 / 投资分析 / 每日报告 / investment agent / 晨报 / morning report

| 日期 | 报告类型 | 模板引用 |
|------|---------|---------|
| 周一 | 周一特殊模板（上周总结+本周展望+情景推演） | → [monday-special.md](templates/monday-special.md) |
| 周二～周五 | 标准每日简报 | → [daily-standard.md](templates/daily-standard.md) |
| 周六 | 每周复盘（周五收盘+一周回顾+持仓体检） | → [weekend-review.md](templates/weekend-review.md) |
| 周日 | **不出报告** | — |

**每天只出一份简报，不再区分晨报/晚报。**

---

## 五段式报告架构

```
§1 今日核心结论（GS/MBB风格bullet point + 三大判断 + 行动建议）
  ↓
§2 全球市场隔夜速览（分区域精简表 + 含月度上下文）
  ↓
§3 重点标的与行业分析（核心个股表格+GICS板块+重点标的展开）
  ↓
§4 基金&大资金动向（三梯队覆盖 + 策略师观点）
  ↓
§5 风险与机会雷达（红绿灯7-8项 + 阈值表 + 风险矩阵）
```

**详细格式规范和模块说明** → [report-format-guide.md](references/report-format-guide.md)

---

## 优先级声明

| 优先级 | 维度 | 说明 |
|--------|------|------|
| **P0** | 数据准确性与完整性 | RULE ZERO + RULE ONE |
| **P0** | AI产业链覆盖完整性 | RULE THREE |
| **P0** | 成稿终审质量 | RULE FIVE — 逐单元格扫描+三轮终审复核，一次性输出最终版 |
| **P1** | 新闻准确性与实时性 | 来源可查证、时间准确 |
| **P2** | 分析逻辑与判断质量 | 结论有据、操作可执行、段落无重复（RULE TWO） |
| **P3** | 格式与排版 | 渐进优化 |

---

## 工作流（4个阶段）

### 第零阶段：交易日检测 + 时间记录

```bash
date "+%A %Y-%m-%d %H:%M:%S"
REPORT_START_TIME=$(date "+%H%M")
```

根据星期几选择对应模板（周六→复盘 / 周日→不出 / 周一→特殊 / 周二~周五→标准）。

### 第一阶段：实时数据采集

**详细的采集批次SOP、Google Finance批量采集模板、数据源优先级表** → [data-collection-sop.md](references/data-collection-sop.md)

**采集批次概要**：

| 批次 | 内容 | 知识库引用 |
|------|------|-----------|
| 0 | 全球财经媒体头条扫描（一级必扫7家） | → [media-watchlist.md](references/media-watchlist.md) |
| 0a | 深度媒体补充扫描（二级强化11家） | → [media-watchlist.md](references/media-watchlist.md) |
| 0b | AI产业链重大动态专项扫描 | → [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md) |
| 1a-1d | M7/指数/GICS/焦点个股（Google Finance批量） | → [data-collection-sop.md](references/data-collection-sop.md) |
| 2 | 亚太/港股+北向资金 | 东方财富/同花顺 |
| 3 | 大宗/汇率/加密/宏观 | web_search/金投网 |
| 4 | 基金&大资金动向（三梯队系统化扫描） | → [fund-universe.md](references/fund-universe.md) |

### 第1.5阶段：数据完整性验证门禁（强制）

> 不通过则禁止进入撰写阶段。详见 → [data-collection-sop.md](references/data-collection-sop.md)

**必填数据清单**：
- 三大指数（SPX/NDX/DJI）+ M7全部7只 + VIX + 焦点个股≥2只
- GICS 11板块ETF + 大宗/汇率/加密6项 + 亚太4大指数
- 每项必须精确值+涨跌幅（公式计算），全部✅才可进入撰写

### 第二阶段：撰写报告

基于采集数据撰写五段式简报（§1-§5），控制在**200-300行**。

**详细格式规范** → [report-format-guide.md](references/report-format-guide.md)

### 第2.5阶段：成稿终审（v17.8强制 — RULE FIVE）

> **此阶段为强制性门禁，不通过则禁止输出报告。**

1. **逐单元格数据扫描**：对§2/§3所有表格逐行检查，收盘价列必须`$XXX.XX`，涨跌幅列必须`±X.XX%`，发现任何非精确数值→立即搜索补全
2. **三轮终审复核**：
   - ①数据轮：零空位+零模糊+数值格式正确
   - ②逻辑轮：§1引用数据与§2-§5一致，涨跌方向无矛盾
   - ③格式轮：禁用词扫描+行数检查+markdown语法
3. **一次性输出最终版**：三轮全通过后才允许输出

**详细扫描SOP** → [data-collection-sop.md](references/data-collection-sop.md) §七/§八

**终审清单（20项）** → [core-rules.md](references/core-rules.md)

### 第三阶段：MD转PDF

```bash
cd /Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows
python3 md_to_pdf.py "{MD文件路径}" "{PDF输出路径}"
```

**PDF标准**: 单页长图 / STHeiti字体 / 280mm宽 / 严禁flag emoji / 两轮渲染法

### 第四阶段：完成交付

1. 输出文件路径和大小确认。
2. **产出大老板消息文本**：从§1核心结论的引用块中提取内容，按固定格式在聊天窗口输出一段可直接复制发送的纯文本消息。详细格式见 → [report-format-guide.md § 九](references/report-format-guide.md)

---

## 核心规则速查（25条）

> **完整规则详见** → [core-rules.md](references/core-rules.md)

| 类别 | 条数 | 涵盖内容 |
|------|------|---------|
| 数据规则 | 8条 | RULE ZERO + 实时性 + 交叉验证 + 政策校验 + 涨跌幅计算 + 完整性扫描 + 零空位 + GF SOP |
| 内容规则 | 5条 | 有事才说 + 建议可执行 + 结论先行 + 200-300行 + 段落去重 |
| AI产业链覆盖 | 2条 | 深度扫描 + 供应链知识库联动 |
| 基金&大资金覆盖 | 2条 | 基金知识库联动 + 策略师观点追踪 |
| 媒体追踪覆盖 | 2条 | 媒体知识库联动 + 终审媒体交叉校验 |
| **成稿终审铁律** | **3条** | **逐单元格数据扫描 + 数据缺失宁迟勿糊 + 三轮终审复核（v17.8）** |
| 流程规则 | 3条 | 交易日检测 + PDF双输出 + 文件命名 |

---

## 致命错误清单（18条 — 零容忍）

| # | 错误类型 | 来源 |
|---|----------|------|
| 1 | 数据错误（价格/涨跌幅/时间） | v17.0 |
| 2 | 训练数据污染 | v17.0 |
| 3 | 逻辑矛盾 | v17.0 |
| 4 | 建议模糊（使用禁用词） | v17.0 |
| 5 | 风险隐瞒 | v17.0 |
| 6 | 政策错误 | v17.0 |
| 7 | 交易日错误 | v17.0 |
| 8 | 数据空位（"—""-""N/A"） | v17.3 |
| 9 | 模糊数据（"~""约""小幅"） | v17.3 |
| 10 | 跨段重复 | v17.3 |
| 11 | AI链重大遗漏 | v17.4 |
| 12 | 供应链盲区 | v17.5 |
| 13 | 一级基金动态遗漏 | v17.6 |
| 14 | 策略师观点盲区 | v17.6 |
| **15** | **数值列出现中文描述性文字（"收涨""+正""上涨"等）** | **v17.8** |
| **16** | **数据缺失未穷尽搜索链即用模糊文字代替** | **v17.8** |
| **17** | **未执行三轮终审复核即输出报告** | **v17.8** |
| **18** | **遗漏大老板消息文本输出（MD+PDF生成后未在聊天窗口输出可复制的纯文本消息）** | **v17.9** |

---

## 知识库引用索引

| 文件 | 内容 | 用途 |
|------|------|------|
| [core-rules.md](references/core-rules.md) | 24条核心规则完整版 + 致命错误清单 + 终审清单 + 禁用词表 | 规则参考 |
| [data-collection-sop.md](references/data-collection-sop.md) | 数据采集4批次详细SOP + Google Finance模板 + 数据源优先级 + 验证门禁 + 降级路径 | 采集阶段 |
| [report-format-guide.md](references/report-format-guide.md) | §1-§5详细格式说明 + 覆盖范围雷达 + PDF渲染铁律 + 市场时间矩阵 | 撰写阶段 |
| [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md) | AI产业链24环标的知识库（含NVDA 19家供应商+中国AI基建50+标的） | batch 0b扫描 |
| [fund-universe.md](references/fund-universe.md) | 三梯队26家基金+策略师追踪清单+25H1回报基线+batch 4扫描指南 | batch 4扫描 |
| [media-watchlist.md](references/media-watchlist.md) | 三级媒体清单（一级7家+二级11家+三级7类）+扫描SOP+交叉校验 | batch 0/0a扫描 |
| [known-pitfalls.md](references/known-pitfalls.md) | 已知堵点与降级路径（数据采集/准确性/完整性/PDF/AI链/基金覆盖） | 全流程 |

---

## 报告输出路径（OrbitOS）

```
/Users/zewujiang/Desktop/OrbitOS/20_日常监控/每日策略简报/
```

- 文件命名：`投资Agent-每日策略简报-{YYYYMMDD}.md/.pdf`
- 周六复盘：`投资Agent-每周复盘-{YYYYMMDD}.md/.pdf`
- 每天只出一份简报，文件名不含时间戳
- PDF转换脚本：`workflows/md_to_pdf.py`
- 中间数据文件：`workflows/investment_agent_data/`
- **禁止**输出到 `workflows/` 目录

---

## 端到端零堵点执行

用户触发后**不需要任何中间干预**即可收到完整报告：
- 数据源异常 → 自动切换备选源（详见 [known-pitfalls.md](references/known-pitfalls.md)）
- 搜索无结果 → 扩大搜索词+换源
- PDF生成失败 → 清理特殊字符重试
- 任何环节不停下等用户

---

## 版本Changelog

| 版本 | 日期 | 核心变更 |
|------|------|---------|
| **v17.8** | 2026-03-13 | **RULE FIVE成稿终审铁律**：新增3条规则（逐单元格扫描+数据缺失宁迟勿糊+三轮终审复核）；致命错误14→17条；终审清单17→20项；数据禁用表述新增4项（"收涨""+正""上涨""下跌"等）；工作流新增第2.5阶段成稿终审门禁；data-collection-sop新增§七数据缺失强制处理流程+§八逐单元格扫描SOP |
| **v17.7** | 2026-03-05 | 文件命名简化：去掉HHMM，改为`YYYYMMDD`；第四阶段新增大老板消息文本自动产出 |
| **v17.6.1** | 2026-03-03 | 媒体追踪体系化：新增media-watchlist.md + batch 0a + 媒体覆盖规则2条 |
| **v17.6** | 2026-03-03 | 基金&大资金深度覆盖：三梯队26家 + 段永平H&H + 策略师追踪 + RULE FOUR |
| **v17.5** | 2026-03-03 | AI产业链深度覆盖：24环供应链级 + ai-supply-chain-universe.md + RULE THREE深化 |
| **v17.4** | 2026-03-03 | AI产业链全覆盖：RULE THREE + 大老板标的优先覆盖 + batch 0b主动扫描 |
| **v17.3** | 2026-03-03 | 数据完整性铁律：RULE ONE + RULE TWO + 验证门禁 + GF批量采集SOP |
| **v17.2** | 2026-03-02 | §3增厚：核心个股表格+GICS板块。§1升级：GS/MBB风格bullet point |
| **v17.0** | 2026-03-02 | 框架全面重构：五段式轻量简报，取消晚报，15→24条核心规则 |
