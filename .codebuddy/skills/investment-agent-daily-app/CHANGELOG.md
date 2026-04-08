# 投研鸭小程序数据生产 — 完整版本历史

> **用途**：归档 SKILL.md 的完整变更历史。SKILL.md 主控只保留最近2个版本的 Changelog，历史版本在此查阅。

---

## v7.5（2026-04-08 09:28）
- **🔴 质量守护体系三层防护（P0 — 根治质量退化）**：
  - 新增 R1-R8 黄金样本回归门禁
  - 新增 `holdings-cache.json` v1.0
  - 新增交付确认 diff 输出
  - known-pitfalls.md v3.2→v3.3：新增堵点 #37~#40
  - json-schema.md v4.5→v4.6：topHoldings/smartMoneyHoldings 硬约束强化

## v7.4（2026-04-07 21:42）
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
