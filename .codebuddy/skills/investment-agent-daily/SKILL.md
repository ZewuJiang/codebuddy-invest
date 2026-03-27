---
name: investment-agent-daily
description: 当用户提到「投资Agent」「每日分析」「投资分析」「每日报告」「investment agent」「晨报」「morning report」或类似关键词时，自动执行投资Agent每日策略简报全流程。
---

# 投资Agent每日策略简报 — 标准工作流 v18.5

> **版本**: v18.5 (2026-03-27) | **迁移兼容性修复**：增加通用路径注释+系统依赖说明+README.md，不改变任何现有逻辑
> **主控文档**：本文件为精炼主控，详细规则/知识库/模板/SOP通过引用按需加载。

---

## 报告定位

> **读者**: $10B级个人投资者，集中持仓（约12个标的），低频交易，时间极宝贵
> **风格**: 段永平/巴菲特式价值投资 + 全球宏观视野
> **核心宗旨**: 对过去24小时二级市场的策略信息和动态保持敏锐捕捉。框架是骨架，灵活应变是灵魂。
> **目标**: 5分钟读完，回答三个核心问题：①过去24小时发生了什么？②这对我的持仓有影响吗？③我需要采取行动吗？
> **不是机构研究报告**，是大老板每天早上喝咖啡时的投资参谋简报。

---

## 六大铁律（最高优先级）

| 铁律 | 核心要求 | 详细规则 |
|------|---------|---------|
| **RULE ZERO** | 训练数据全面禁用。所有数据只能来自当期实时搜索。自查三问：①来自搜索？②时间戳≤24h？③可追溯？任一为否→重写 | → [core-rules.md](references/core-rules.md) |
| **RULE ONE** | 数据完整性铁律。表格严禁"—""-""N/A""~""约""小幅"。M7×7+GICS×11+指数×3+VIX+焦点≥2+亚太×4+大宗×6全部精确值 | → [core-rules.md](references/core-rules.md) |
| **RULE TWO** | 段落去重。同一事件只在最相关段落出现一次：§3写个股事件，§4写机构动向，不交叉重复 | → [core-rules.md](references/core-rules.md) |
| **RULE THREE** | AI产业链敏感度。大老板已汇报标的优先覆盖，AI全产业链24环主动扫描，中英文交叉验证 | → [core-rules.md](references/core-rules.md) |
| **RULE FOUR** | 基金&大资金覆盖完整性。三梯队26家（一级核心8家/二级追踪10家/三级雷达8家），策略师观点追踪 | → [core-rules.md](references/core-rules.md) |
| **RULE FIVE** | **成稿终审铁律（v17.8）**。数据缺失宁迟勿糊（至少3个数据源穷尽搜索）；成稿后逐表格逐单元格扫描（收盘价必须$XXX.XX/涨跌幅必须±X.XX%）；三轮终审复核（数据轮→逻辑轮→格式轮）全通过后一次性输出最终版。**严禁"收涨""上涨""+正"等模糊描述出现在数值列** | → [core-rules.md](references/core-rules.md) + [data-collection-sop.md](references/data-collection-sop.md) §七/§八 |
| **RULE SIX** | **自主进化铁律（v18.0）**。每次日报交付后强制执行反思引擎（六维反思），进化提案必须通过质量铁栅栏三项检验（准确性/完整性/实时性不降级），三级分级执行（🟢低风险自动/🟡中风险默认生效/🔴高风险需确认），所有变更精确Diff记录可回滚。**质量只升不降，宁可不进化也不退化** | → [evolution-rules.md](references/evolution-rules.md) + [evolution-log.md](references/evolution-log.md) |

---

## 触发条件与报告日历

**触发关键词**：投资Agent / 每日分析 / 投资分析 / 每日报告 / investment agent / 晨报 / morning report

| 日期 | 报告类型 | 模板引用 |
|------|---------|---------|
| 周一 | 周一特殊模板（上周总结+本周展望+情景推演） | → [monday-special.md](templates/monday-special.md) |
| 周二～周五 | 标准每日简报 | → [daily-standard.md](templates/daily-standard.md) |
| 周六～周日 | **不出报告** | — |

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
| **P3** | 自主进化引擎 | RULE SIX — 每次日报后强制反思，质量只升不降。不影响日报本身产出质量 |

---

## 工作流（5个阶段）

### 第零阶段：交易日检测 + 时间记录 + 待固化提案检查

```bash
date "+%A %Y-%m-%d %H:%M:%S"
REPORT_START_TIME=$(date "+%H%M")
```

根据星期几选择对应模板（周六～周日→不出 / 周一→特殊 / 周二~周五→标准）。

**新增（v18.0）**：检查 `evolution-log.md` 中是否有状态为"🔄 默认生效中"的中风险提案。若有且用户未反对，在本次执行开始前自动固化到对应文件，并更新日志状态为"✅ 已固化"。

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

**终审清单（22项）** → [core-rules.md](references/core-rules.md)

### 第三阶段：MD转PDF

```bash
# 默认路径（当前部署环境）：
cd /Users/zewujiang/Desktop/AICo/codebuddy-invest/.codebuddy/skills/investment-agent-daily/scripts
python3 md_to_pdf.py "{MD文件路径}" "{PDF输出路径}"

# 通用路径（适配其他环境）：
# cd {SKILL_ROOT}/scripts
# python3 md_to_pdf.py "{MD文件路径}" "{PDF输出路径}"
# 其中 {SKILL_ROOT} = 本 Skill 所在的根目录（包含 SKILL.md 的目录）
```

**PDF转换铁律**（原 `investment-report-pdf.mdc`，已合并至此）：

| 项目 | 要求 |
|------|------|
| **转换脚本** | 本 Skill 自带 `scripts/md_to_pdf.py`（v13.0），**禁止**使用 pandoc / weasyprint 单独 / 手动拼接HTML+CSS |
| **PDF标准** | 单页长图、无分页 / STHeiti字体优先（严禁PingFang SC排首位）/ 280mm宽 / MBB咨询风格 / 表格深色表头+斑马纹 |
| **渲染方法** | 两轮渲染法v2（probe测高度→精确高度重渲染），严禁pypdf裁剪mediabox |
| **验证检查** | ① `file xxx.pdf` 显示 "1 pages" ② 文件大小 2-5MB ③ Mac预览无乱码 |
| **依赖安装** | `pip3 install -r scripts/requirements.txt`（markdown / weasyprint / pdfplumber） |

### 第四阶段：完成交付

1. 输出文件路径和大小确认。
2. **产出大老板消息文本**：从§1核心结论的引用块中提取内容，按固定格式在聊天窗口输出一段可直接复制发送的纯文本消息。详细格式见 → [report-format-guide.md § 九](references/report-format-guide.md)

### 第五阶段：自主反思引擎（v18.0新增 — RULE SIX）

> **此阶段为强制执行阶段，每次日报交付后自动触发。** 详细规则见 → [evolution-rules.md](references/evolution-rules.md)

**执行流程**：

1. **六维反思**（≤2分钟）：按数据源效率/新闻源发现/分析框架/覆盖盲区/流程效率/格式呈现逐一快速检查
2. **判断是否有进化提案**：大多数时候结论是"本次无优化提案"，这完全正常
3. **有提案时**：通过质量铁栅栏三项检验（准确性/完整性/实时性不降级）→ 分级（🟢/🟡/🔴）→ 执行或报告
4. **输出反思总结**：在聊天窗口输出反思结果（无论是否有提案）
5. **记录到进化日志**：写入 `evolution-log.md` + 更新统计仪表盘

**进化提案在日报中的呈现**：

在大老板消息文本输出**之后**，以独立区块呈现进化提案（详细格式见 → [report-format-guide.md § 十](references/report-format-guide.md)）。

**质量铁栅栏（三项强制检验）**：

| # | 检验 | 不通过 = 直接拒绝 |
|---|------|------------------|
| 1 | 准确性不降级 | 任何可能降低数据准确性的变更 → 拒绝 |
| 2 | 完整性不降级 | 任何可能缩小覆盖范围的变更 → 拒绝 |
| 3 | 实时性不降级 | 任何可能增加信息延迟的变更 → 拒绝 |

**三级分级执行**：

| 级别 | 执行方式 | 说明 |
|------|---------|------|
| 🟢 低风险 | 自动执行 + 日报末尾通知 | 纯增量（新增数据源/堵点/URL模板等） |
| 🟡 中风险 | 日报末尾报告，默认生效 | 修改优先级/升级媒体级别/新增固定模块等 |
| 🔴 高风险 | 日报末尾报告，需用户确认 | 触及核心规则/致命错误清单/架构等 |

---

## 核心规则速查（28条）

> **完整规则详见** → [core-rules.md](references/core-rules.md)

| 类别 | 条数 | 涵盖内容 |
|------|------|---------|
| 数据规则 | 8条 | RULE ZERO + 实时性 + 交叉验证 + 政策校验 + 涨跌幅计算 + 完整性扫描 + 零空位 + GF SOP |
| 内容规则 | 5条 | 有事才说 + 建议可执行 + 结论先行 + 200-300行 + 段落去重 |
| AI产业链覆盖 | 2条 | 深度扫描 + 供应链知识库联动 |
| 基金&大资金覆盖 | 2条 | 基金知识库联动 + 策略师观点追踪 |
| 媒体追踪覆盖 | 2条 | 媒体知识库联动 + 终审媒体交叉校验 |
| **成稿终审铁律** | **3条** | **逐单元格数据扫描 + 数据缺失宁迟勿糊 + 三轮终审复核（v17.8）** |
| 流程规则 | 4条 | 交易日检测 + PDF双输出 + 文件命名 + 大老板消息文本（v17.9） |
| **自主进化规则** | **2条** | **反思引擎强制执行 + 质量铁栅栏（v18.0）** |

---

## 致命错误清单（21条 — 零容忍）

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
| **19** | **高风险进化变更未经用户确认即执行** | **v18.0** |
| **20** | **进化变更未通过质量铁栅栏即执行（绕过准确性/完整性/实时性三项检验）** | **v18.0** |
| **21** | **进化变更无精确Diff记录（导致无法回滚）** | **v18.0** |

---

## 知识库引用索引

| 文件 | 内容 | 用途 |
|------|------|------|
| [core-rules.md](references/core-rules.md) | 28条核心规则完整版 + 致命错误清单 + 终审清单 + 禁用词表 | 规则参考 |
| [data-collection-sop.md](references/data-collection-sop.md) | 数据采集4批次详细SOP + Google Finance模板 + 数据源优先级 + 验证门禁 + 降级路径 | 采集阶段 |
| [report-format-guide.md](references/report-format-guide.md) | §1-§5详细格式说明 + 覆盖范围雷达 + PDF渲染铁律 + 市场时间矩阵 + 进化提案格式 | 撰写阶段 |
| [ai-supply-chain-universe.md](references/ai-supply-chain-universe.md) | AI产业链24环标的知识库（含NVDA 19家供应商+中国AI基建50+标的） | batch 0b扫描 |
| [fund-universe.md](references/fund-universe.md) | 三梯队26家基金+策略师追踪清单+25H1回报基线+batch 4扫描指南 | batch 4扫描 |
| [media-watchlist.md](references/media-watchlist.md) | 三级媒体清单（一级7家+二级11家+三级7类）+扫描SOP+交叉校验 | batch 0/0a扫描 |
| [known-pitfalls.md](references/known-pitfalls.md) | 已知堵点与降级路径（数据采集/准确性/完整性/PDF/AI链/基金覆盖/进化机制） | 全流程 |
| **[evolution-rules.md](references/evolution-rules.md)** | **进化机制核心规则：质量铁栅栏+三级分级+六维反思+回滚机制+致命错误** | **第五阶段** |
| **[evolution-log.md](references/evolution-log.md)** | **进化日志：统计仪表盘+变更记录+精确Diff+审计轨迹** | **第五阶段** |

---

## 报告输出路径（OrbitOS）

```
# 默认输出路径（当前部署环境）：
/Users/zewujiang/Desktop/OrbitOS/20_日常监控/每日策略简报/

# 通用配置（适配其他环境）：
# 将上方路径替换为你的报告输出目录即可，例如：
# /path/to/your/reports/每日策略简报/
```

- 文件命名：`投资Agent-每日策略简报-{YYYYMMDD}.md/.pdf`
- 每天只出一份简报，文件名不含时间戳
- PDF转换脚本：`scripts/md_to_pdf.py`（本Skill自包含，详见第三阶段）
- 中间数据文件：`workflows/investment_agent_data/`（可选，非必需目录）
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
| **v18.5** | 2026-03-27 | **迁移兼容性修复**（纯增量，不改变任何现有逻辑）：①第三阶段脚本路径增加通用路径注释（原绝对路径保留）；②输出路径区增加通用配置说明（原OrbitOS路径保留）；③requirements.txt补充weasyprint系统级依赖说明（macOS/Ubuntu）；④notes/目录添加.gitkeep；⑤新增README.md安装指南 |
| **v18.4** | 2026-03-27 | **Skill自包含优化**：①将 `workflows/md_to_pdf.py` v13.0 移入 `scripts/md_to_pdf.py`，第三阶段路径更新；②新增 `scripts/requirements.txt`（3个pip依赖）；③合并 `investment-report-pdf.mdc` 核心规则到第三阶段（PDF转换铁律表）；④删除外部冗余文件（`workflows/md_to_pdf.py` + `chart_generator.py` + `mbb_report_engine.py` + 整个 `valueinvest/` 目录）；⑤删除 `investment-report-pdf.mdc` workspace rule |
| **v18.3** | 2026-03-27 | **原油指标规范固化**：①report-format-guide.md §二新增原油指标规范（布伦特Brent为全球定价基准主指标，WTI为辅）；②红绿灯标准新增布伦特原油阈值行（<$90安全/$90-110警惕/>$110危险）；③data-collection-sop.md数据源优先级表新增"布伦特原油（主指标）"行；④全文叙事/标题/事件链/结论/红绿灯/监控阈值统一以布伦特为锚 |
| **v18.2** | 2026-03-26 | **维护升级**：①DXY降级路径固化到data-collection-sop.md §三+§五（连续4次实战遇阻→正式SOP化）；②media-watchlist.md新增§七新数据源验证管道（5个待验证源）；③删除周六复盘模板+日历更新（周六～周日均不出报告）；④删除scripts/md_to_pdf.py旧副本；⑤删除notes/notes.md冗余文件；⑥known-pitfalls新增周一特殊模板额外批次遗漏提醒；⑦evolution-log #20260326-01状态→已固化 |
| **v18.0** | 2026-03-18 | **RULE SIX自主进化铁律**：新增第五阶段「自主反思引擎」；新增evolution-rules.md（质量铁栅栏三项检验+三级分级🟢🟡🔴+六维反思+精确Diff回滚+默认生效机制）；新增evolution-log.md（统计仪表盘+审计轨迹）；六大铁律（+RULE SIX）；致命错误18→21条（+3条进化专用）；核心规则26→28条（+2条进化规则）；第零阶段新增待固化提案检查；report-format-guide新增§十进化提案格式；known-pitfalls新增进化机制陷阱 |
| **v17.9** | 2026-03-18 | 新增第28条流程规则（大老板消息文本必须输出），致命错误17→18条。VIX数据采集教训固化到data-collection-sop |
| **v17.8** | 2026-03-13 | **RULE FIVE成稿终审铁律**：新增3条规则（逐单元格扫描+数据缺失宁迟勿糊+三轮终审复核）；致命错误14→17条；终审清单17→20项；数据禁用表述新增4项（"收涨""+正""上涨""下跌"等）；工作流新增第2.5阶段成稿终审门禁；data-collection-sop新增§七数据缺失强制处理流程+§八逐单元格扫描SOP |
| **v17.7** | 2026-03-05 | 文件命名简化：去掉HHMM，改为`YYYYMMDD`；第四阶段新增大老板消息文本自动产出 |
| **v17.6.1** | 2026-03-03 | 媒体追踪体系化：新增media-watchlist.md + batch 0a + 媒体覆盖规则2条 |
| **v17.6** | 2026-03-03 | 基金&大资金深度覆盖：三梯队26家 + 段永平H&H + 策略师追踪 + RULE FOUR |
| **v17.5** | 2026-03-03 | AI产业链深度覆盖：24环供应链级 + ai-supply-chain-universe.md + RULE THREE深化 |
| **v17.4** | 2026-03-03 | AI产业链全覆盖：RULE THREE + 大老板标的优先覆盖 + batch 0b主动扫描 |
| **v17.3** | 2026-03-03 | 数据完整性铁律：RULE ONE + RULE TWO + 验证门禁 + GF批量采集SOP |
| **v17.2** | 2026-03-02 | §3增厚：核心个股表格+GICS板块。§1升级：GS/MBB风格bullet point |
| **v17.0** | 2026-03-02 | 框架全面重构：五段式轻量简报，取消晚报，15→24条核心规则 |
