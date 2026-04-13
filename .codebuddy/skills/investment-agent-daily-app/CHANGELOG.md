# 投研鸭小程序数据生产 — 完整版本历史

> **用途**：归档 SKILL.md 的完整变更历史。SKILL.md 主控只保留最近版本的 Changelog，历史版本在此查阅。

---

## v10.6（2026-04-13 11:05）— Harness v10.6 FATAL 项全面升级

**原则**：目标每次全部通过，零 WARN。前端渲染安全与核心功能完整性纳入 FATAL 门禁。

**validate.py v5.5→v5.6**：
- V35  **WARN→FATAL**：audioUrl 为空 = 语音播报失效，不可绕过
- V38  **WARN→FATAL**：sparkline 趋势与 change 方向矛盾 = 数据错误
- V41  **WARN→FATAL**：globalReaction value 超长/含括号 = 前端布局溢出
- V42  **WARN→FATAL**：generatedAt 为空 = 前端时间显示异常
- V24  **WARN→FATAL**：Markdown 残留 = 前端乱码
- R1   **WARN→FATAL**：topHoldings < 3 = 聪明钱核心展示不完整
- V_TL **WARN→FATAL**：红绿灯 value↔status 不一致 = 前端颜色错误
- **FATAL 项**：10 → **17 个**
- **校验项**：54 项（不变）

**SKILL.md**：
- 第3.5阶段语音播报标注升级为 🔴 FATAL 级强制
- 质量宪章 WARN 上限从 ≤3 → 目标 0 WARN（≤1 可接受）

---

## v10.5（2026-04-09 22:19）— Harness v10.5 门槛全面收紧

**原则**：数据准确性 > 执行速度。宁可多搜几轮花多几分钟，也不能让错误数据发布。

**validate.py v5.4→v5.5**：
- V6  **WARN→FATAL** 升级：sparkline[-1] vs price 偏差容差从 1%→5%（FATAL 级，形成 V6/V45 双层防护）
- V40 **WARN→FATAL** 升级：metrics 空值 = 前端空白 = 阻断发布
- V44 **阈值收紧**：从 >50% 零值 → **任何零值（>=1个）即 FATAL**
- V45 **阈值收紧**：price vs sparkline[-1] 差距从 50%→**30%**
- 新增 **V46 [FATAL]** chartData 禁止零值（与 V44 平行，覆盖30日数据）
- 新增 **V47 [WARN]** sparkline 禁止全平线（拦截估算填充）
- **FATAL 项**：从 5 → **10 个**（V6/V39/V40/V43/V44/V45/V46/R2/R3/R9）
- **校验项**：52 → **54 项**

**data-collection-sop.md v2.0→v2.1**：
- 新增 §0.7 质量门禁与重试机制（4道门禁 + 4级搜索重试 SOP + 10项FATAL清单表格）

---

## v10.4（2026-04-09 21:53）— Harness v10.4 结构性数据防护

**根因**：2026-04-09 发现两类系统性结构错误：
1. AI 对新上市/无历史数据标的（VIX/日经/KOSPI/黄金/BTC/ETH/CNH/DXY等）直接用 `0` 填充 sparkline → 图表断崖+7日涨跌空白
2. AI 填写 price 时使用错误来源（智谱 HK$42.80 实为 HK$929，MiniMax HK$38.50 实为 HK$999，AVGO $179.83 实为 $353.81 等 13 个标的错误）— **价格与 sparkline 数量级不一致**

**修复**：
- **数据修复**：watchlist.json 修正 13 个标的 price + 全部 32 个标的补全 7日/30日涨跌；markets.json 修复 VIX/META/日经/KOSPI/黄金/布伦特/DXY/10Y美债/CNH/BTC/ETH 共 11 个 sparkline
- validate.py **v5.3→v5.4**：
  - 新增 V44 [FATAL] sparkline 禁止大量0值（>50%为0 → FATAL，拦截AI零值填充历史数据）
  - 新增 V45 [FATAL] price 与 sparkline[-1] 数量级一致性（差距>50% → FATAL，拦截数据来源不一致）
  - FATAL_CODES 新增 V44/V45
  - 校验项 50→52 项

**结构性教训**：
- 直接能取的数不应让 AI 计算（5D/1M 涨跌 Google Finance 直接有）
- sparkline 一律从历史行情搜索，禁止 AI 手写估算值
- price 与 sparkline 必须来自同一数据源

---

## v10.0（2026-04-08 17:30）— Harness v10.0 工具链全面升级
- **核心理念**：AI 只做搜索+写分析，其余全部由工具链接管
- auto_compute.py v1.0→v2.0：新增6类自动计算（metrics[2-5]+gics排序+dataTime+sourceType修正），总计12类
- validate.py v3.0→v4.0：新增 V30-V34 内容质量检测层 + Insight 上限扩展 + V7 修复 + riskAlerts 废弃
- 新增 checklist_generator.py v1.0：执行前自动清单
- 新增 post_flight.py v1.0：执行后自动报告
- 新增 schema-compact.json v1.0：AI 紧凑 Schema 参照
- golden-baseline.json v1.1→v1.2：sourceType 精简 + 内容质量参数 + Insight 上限100
- 校验结果：36项→41项，WARN 6→3

## v9.0（2026-04-08 17:00）— Harness v9.0 架构级重构
- **🏗️ 从"越做越厚"到"结构性简洁"**：
  - 删除 Refresh 模式：四档→二档引擎（Standard + Weekend），消除 413行 refresh-mode.md + 模式路由决策树 + 字段边界表
  - 新增 `auto_compute.py` v1.0：自动计算 riskScore/riskLevel/sentimentLabel/trafficLights.status/metrics联动，AI 不再手算公式
  - validate.py v2.0→v3.0：去掉 refresh 分支，heavy 映射 standard，统一校验
  - run_daily.sh v5.0→v6.0：新增第0.3步 auto_compute，模式检测简化
  - data-collection-sop.md v1.9→v2.0：删除第九章 Refresh 精简采集批次
  - known-pitfalls.md v3.6→v4.0：Refresh 堵点归档，活跃堵点 43→40
  - json-schema.md v4.6→v5.0：清理 refresh_update 枚举引用
  - templates.md v1.0→v1.1：删除 Refresh 复盘模板
  - golden-baseline.json v1.0→v1.1：sourceType 枚举清理
  - weekend-mode.md v4.0→v4.1：术语 Heavy→Standard
  - 规范总行数减少约 660行（-15%），AI 认知负荷显著降低

## v8.2（2026-04-08 13:15）
- validate.py v1.1→v2.0：FATAL/WARN 双级机制——R2/R3/R9 为 FATAL 级
- 新增 R9 校验：自动比对 radar.smartMoneyHoldings 与 holdings-cache.json
- run_daily.sh v4.0→v5.0：--skip-validate 废弃→--skip-warn
- known-pitfalls.md v3.5→v3.6：新增堵点 #42/#43

## v8.1（2026-04-08 11:30）
- validate.py v1.0→v1.1：新增 V27(Insight长度) + V28(metrics数量) + V29(logic箭头格式)
- run_daily.sh v3.0→v4.0：版本号更新
- known-pitfalls.md v3.4→v3.5：全文精简

## v8.0（2026-04-08 10:30）
- 🏗️ Harness Engineering 架构升级（系统性治理规范膨胀）
- 新增 validate.py v1.0（30+项自动化校验）
- 新增 golden-baseline.json v1.0
- 新增 formulas.md v1.0、templates.md v1.0、CHANGELOG.md
- SKILL.md 从 972行→≤300行瘦身

## v7.5（2026-04-08 09:28）
- 质量守护体系三层防护：R1-R8回归门禁+holdings-cache.json+diff输出
- known-pitfalls.md v3.2→v3.3：新增堵点 #37~#40
- json-schema.md v4.5→v4.6：topHoldings/smartMoneyHoldings 硬约束强化
- GitHub Pages 作为唯一公网端点

## v7.3（2026-04-07 20:40）
- 新增第4.3阶段：公开API同步

## v7.2（2026-04-07 18:30）
- 工程化改造（对标 Iran Briefing skill）
- sync_to_edgeone.sh v1.0→v3.0
- refreshInterval 统一修正
- json-schema.md v4.2→v4.5

## v7.1（2026-04-07 13:00）
- P0 残留 Bug 修复（3处）
- refresh-mode.md v1.0→v1.1
- data-collection-sop.md R1 批次明确化

## v7.0（2026-04-07 12:00）
- 新增 Refresh 模式（每4小时增量刷新）
- 三档升级为四档引擎
- 新建 refresh-mode.md v1.0
- known-pitfalls.md v3.0→v3.1

## v6.1（2026-04-06 19:20）
- 播报文本生成器全面重构 v1.0→v3.0

## v6.0（2026-04-06 17:59）
- 新增语音播报功能（MiniMax TTS）

## v5.9（2026-04-06 15:30）
- 小程序前端 + Skill 联动工程优化

## v5.7（2026-04-06 14:07）
- 简报页+标的页质量基线门禁固化
- 黄金样本固化
- 执行质量五项加固

## v5.6 及更早版本
v5.1 持仓数据铁律 → v5.0 简报页架构优化 → v4.8 聪明钱搜索深度 → v4.6 Batch 4 分层修复 → v4.5 雷达页升级 → v4.4 雷达页重构 → v4.3 AkShare 替代 yfinance → v4.2 watchlist 5板块 → v4.0 三档引擎 → v3.x 数据治理 → v2.x 架构演进 → v1.0 初始版本

详见 git log。
