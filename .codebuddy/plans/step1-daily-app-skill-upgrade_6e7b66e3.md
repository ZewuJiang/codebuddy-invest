---
name: step1-daily-app-skill-upgrade
overview: 升级 investment-agent-daily-app Skill 的 5 个文件，补齐 v1.3 新字段的采集 SOP、数据源定义和模板脚手架，确保下次运行时能自动产出完整的 keyDeltas / fearGreed / predictions / _meta / 6个Insight 字段。不触碰 investment-agent-daily Skill 的任何文件。
todos:
  - id: update-data-collection-sop
    content: 修改 data-collection-sop.md：新增 Batch A 情绪/预测数据采集章节（Fear&Greed/Polymarket/Kalshi/CME FedWatch），更新采集批次总览表，补充验证门禁第18-19项，版本升至 v1.3
    status: completed
  - id: update-data-source-priority
    content: 修改 data-source-priority.md：新增情绪/预测类数据源优先级表区段（CNN/Polymarket/Kalshi/CME FedWatch），补充降级路径（全部非阻断），版本升至 v1.3
    status: completed
  - id: upgrade-json-templates
    content: 升级 daily-standard.json 和 monday-special.json：补充 briefing 的 timeStatus/keyDeltas/_meta 占位、markets 的6个Insight占位、radar 的 fearGreed/predictions/_meta 占位，coreJudgments 示例补充可选扩展字段，版本升至 v1.3
    status: completed
  - id: update-skill-md
    content: 修改 SKILL.md：第1.5阶段门禁追加第18-21项可选字段建议检查条目，致命错误清单补充第16条，Changelog 记录本次全部5项变更，版本升至 v1.4
    status: completed
    dependencies:
      - update-data-collection-sop
      - update-data-source-priority
      - upgrade-json-templates
---

## 用户需求

**目标**：专项修缮 `investment-agent-daily-app` Skill，补齐所有因 v1.3 新字段（`keyDeltas`、`fearGreed`、`predictions`、`_meta`、6个板块Insight）引入后、SOP 和模板文件未同步更新而留下的"空白地带"，使 AI 每次执行该 Skill 时能通过规范化 SOP 引导，稳定、自动地产出所有新字段，而不依赖"运气"。

**明确禁止**：不触碰 `investment-agent-daily` Skill 的任何文件。

## 产品概述

投研鸭小程序数据生产 Skill（`investment-agent-daily-app`）当前 json-schema.md 已完整定义 v1.3 新字段，但数据采集 SOP、数据源优先级表、JSON 脚手架模板三个文件仍停留在 v1.0-v1.2.1，导致：

1. AI 采集时没有 Fear & Greed / Polymarket / CME FedWatch 等情绪数据的采集 SOP 引导
2. 数据源优先级表缺失情绪类数据源，降级路径不明确
3. 模板脚手架不含新字段，AI 依赖模板时容易漏填
4. SKILL.md 完整性门禁未对新可选字段进行"建议检查"约束

## 核心功能

- **补充情绪/预测数据采集批次**：在 `data-collection-sop.md` 新增 Batch A（情绪与预测数据），采集 CNN Fear & Greed、Polymarket、Kalshi、CME FedWatch 数据，并更新验证门禁
- **扩展数据源优先级表**：在 `data-source-priority.md` 新增情绪/预测类数据源优先级和降级路径
- **升级 JSON 模板脚手架**：将 `daily-standard.json` 和 `monday-special.json` 从 v1.0 升级至 v1.3，补充所有新字段占位（含注释说明枚举值和必填性）
- **补充 SKILL.md 完整性门禁**：在第1.5阶段验证清单新增可选字段建议检查条目
- **版本递增 + Changelog**：所有修改文件版本号递增，Changelog 精确记录

## 技术栈

纯文档修改任务，涉及：

- Markdown 文件（`.md`）：`data-collection-sop.md`、`data-source-priority.md`、`SKILL.md`
- JSON 文件（`.json`）：`daily-standard.json`、`monday-special.json`

## 实施方案

### 核心策略

所有修改严格控制在 `.codebuddy/skills/investment-agent-daily-app/` 目录内，采用**最小侵入原则**：在现有文件结构基础上追加/修改内容，不重构已有章节，完全向后兼容。

### 各文件修改要点

#### 1. `data-collection-sop.md` → 升级至 v1.3

**关键问题**：当前周一额外批次已命名为 `批次7/8/9`，新增情绪数据批次需避免命名冲突。方案：新增为 **Batch A（情绪与预测数据）**，区别于周一专用的批次 7/8/9，适用于所有工作日（周一～周五均执行）。

新增内容：

- 采集批次总览表新增 Batch A 行
- 第八章（新增）：Batch A 详细 SOP —— CNN Fear & Greed（`production.dataviz.cnn.com/index/fearandgreed/graphdata`）、Polymarket（`clob.polymarket.com/markets`）、Kalshi API、CME FedWatch 页面解析
- 数据完整性验证门禁新增第18项（fearGreed 建议检查）和第19项（predictions 建议检查），标注为"建议项"（⭐ 非阻断）区别于强制项（✅ 阻断）
- 版本升级至 v1.3，Changelog 追加

#### 2. `data-source-priority.md` → 升级至 v1.3

在现有优先级表末尾新增情绪/预测数据源区段：

| 数据类型 | 首选 | 备选 | 第三选 |
| --- | --- | --- | --- |
| CNN Fear & Greed Index | `production.dataviz.cnn.com` JSON endpoint (web_fetch) | web_search "CNN Fear Greed Index" | 跳过（不阻断） |
| Polymarket 预测概率 | `clob.polymarket.com/markets` API (web_fetch) | web_search "Polymarket [主题]" | 跳过（不阻断） |
| Kalshi 预测概率 | `kalshi.com/markets` API (web_fetch) | web_search | 跳过（不阻断） |
| CME FedWatch 降息概率 | `cmegroup.com/markets/interest-rates/cme-fedwatch-tool` | web_search "CME FedWatch probability" | 跳过（不阻断） |


降级路径补充：情绪数据全部为非阻断型（可选字段，获取失败则跳过，不影响主流程）。

版本升级至 v1.3，Changelog 追加。

#### 3. `daily-standard.json` → 升级至 v1.3

在现有 4 个 JSON 对象（briefing/markets/watchlist/radar）内补充缺失字段，使用**占位值 + 注释**标注枚举范围和必填性：

- `briefing`：补充 `timeStatus`（含 marketStatus 枚举注释）、`keyDeltas[]`（含示例结构和枚举注释）、`_meta`（含 sourceType 枚举注释）
- `markets`：补充 `usInsight`、`m7Insight`、`asiaInsight`、`commodityInsight`、`cryptoInsight`、`gicsInsight` 六个空字符串占位
- `radar`：补充 `fearGreed`（含字段说明注释）、`predictions[]`（含示例结构和枚举注释）、`_meta`
- `coreJudgments` 条目模板中补充 `keyActor`、`references`、`probability`、`trend` 可选字段示例
- 模板版本升级至 `v1.3`

#### 4. `monday-special.json` → 升级至 v1.3

与 `daily-standard.json` 保持结构完全一致，额外在 `_note` 字段中补充说明周一额外执行 Batch A（情绪数据采集）。版本升级至 `v1.3`。

#### 5. `SKILL.md` → 升级至 v1.4

在第1.5阶段"数据完整性门禁"验证清单末尾追加第18项（可选字段建议检查，⭐ 标记区别于 ✅ 强制项）：

```
| 18 | briefing: keyDeltas（建议） | 3-5条，每条 title+status+heat+brief | 可选但建议填充，跳过时前端该模块不渲染 |
| 19 | radar: fearGreed（建议） | value(0-100)+label+previousClose+oneWeekAgo | 参照 Batch A 采集结果填充 |
| 20 | radar: predictions（建议） | 2-4条，每条 title+source+probability+trend+change24h | 参照 Batch A 采集结果填充 |
| 21 | 所有JSON: _meta（建议） | sourceType+generatedAt+skillVersion | 固定值：heavy_analysis / 当前时间 / v1.4 |
```

版本号升级至 v1.4，Changelog 精确记录 5 项变更（含受影响文件列表）。

致命错误清单同步更新：补充第16条（keyDeltas.status 枚举值越界）。

## 实施注意事项

- **版本命名冲突规避**：`data-collection-sop.md` 中周一特殊批次已占用 7/8/9 数字编号，新增情绪批次命名为 **Batch A** 并在总览表标注"适用全工作日（周一～周五）"，与周一特殊批次 7/8/9（仅周一）形成明确区分
- **向后兼容保障**：模板新增字段均为可选（🔸），占位值为空字符串/空数组，旧数据可正常渲染
- **JSON 模板合法性**：JSON 文件中不允许真正的注释，改用 `_field_comment` 辅助字段或在模板顶部 `_comment` 对象中集中说明枚举值和规则
- **Changelog 格式统一**：所有修改文件的 Changelog 追加在文件末尾，格式 `> vX.X — YYYY-MM-DD | 变更说明`

## 目录结构

```
.codebuddy/skills/investment-agent-daily-app/
├── SKILL.md                              # [MODIFY] v1.3.2 → v1.4，补充门禁第18-21项 + 致命错误第16条
├── references/
│   ├── json-schema.md                    # [不动] 已完整（v1.3.2）
│   ├── data-collection-sop.md            # [MODIFY] v1.2.1 → v1.3，新增第八章 Batch A 情绪数据采集 SOP
│   ├── data-source-priority.md           # [MODIFY] v1.2 → v1.3，新增情绪/预测数据源优先级表区段
│   ├── known-pitfalls.md                 # [不动]
│   ├── stock-universe.md                 # [不动]
│   ├── ai-supply-chain-universe.md       # [不动]
│   ├── fund-universe.md                  # [不动]
│   └── media-watchlist.md                # [不动]
└── templates/
    ├── daily-standard.json               # [MODIFY] v1.0 → v1.3，补充全部 v1.3 新字段占位
    └── monday-special.json               # [MODIFY] v1.0 → v1.3，同上 + 补充周一 Batch A 说明
```