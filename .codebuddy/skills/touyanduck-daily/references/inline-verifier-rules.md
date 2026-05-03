# Generator-Verifier 内联自校验规则（v1.0）

> **用途**：Phase 2 每生成一个 JSON 后立即执行的内联校验清单。从 validate.py v5.7 的 17 项 FATAL + 关键 WARN 中提取"可在写入时即时检测"的子集。
> **设计原则**：Generator-Verifier 是**前置过滤**，validate.py 仍是**终极门禁**。两层防护，不是替代关系。
> **核心价值**：在 Phase 2 就拦截明显错误，避免进入 Phase 3 run_daily.sh 后触发 FATAL 导致整体重来。
> **加载时机**：L3 批次（Phase 2 前加载）

---

## 一、内联性分类总表（17 项 FATAL）

| Code | 校验项 | 可内联? | 理由 |
|------|--------|---------|------|
| **V6** | sparkline[-1] vs price ≤5% | ✅ 可内联 | 只需同一对象的 sparkline 和 price |
| **V24** | Markdown 残留（`**`） | ✅ 可内联 | 只需当前 JSON 文本正则扫描 |
| **V39** | 13F 持仓合规（无期权/权重≤105%） | ✅ 可内联 | 只需 radar.smartMoneyHoldings |
| **V40** | metrics 无空值 | ✅ 可内联 | 只需 watchlist.metrics[].value |
| **V41** | globalReaction value ≤15字符/无括号 | ✅ 可内联 | 只需 briefing.globalReaction |
| **V42** | generatedAt 非空 ISO 8601 | ✅ 可内联 | 只需 _meta.generatedAt |
| **V43** | price 非占位符 | ✅ 可内联 | 只需检查 price 是否在黑名单 |
| **V44** | sparkline 禁止任何零值 | ✅ 可内联 | 只需遍历 sparkline 数组 |
| **V45** | price vs sparkline[-1] 数量级 <30% | ✅ 可内联 | 只需同一对象的 price 和 sparkline[-1] |
| **V46** | chartData 禁止任何零值 | ✅ 可内联 | 只需遍历 chartData 数组 |
| **V38** | sparkline 趋势 vs change 方向一致 | ✅ 可内联 | 只需同一对象的 sparkline[-1,-2] 和 change |
| **R1** | topHoldings ≥ 3 条 | ✅ 可内联 | 只需 briefing.topHoldings 长度 |
| **R2** | 每家 positions ≥ Top10 | ✅ 可内联 | 只需 radar.smartMoneyHoldings |
| **R3** | 无"待更新"占位符 | ✅ 可内联 | 只需当前 JSON 字符串搜索 |
| **R9** | 与 holdings-cache.json 一致 | ❌ 不可内联 | 需读取外部 `references/holdings-cache.json` 文件 |
| **V35** | audioUrl 非空 | ⏸️ 暂停 | 语音播报已暂停，V35 降为 WARN，跳过不影响上传 |
| **V_TL** | 红绿灯 value↔status 阈值一致 | ❌ 不可内联 | 需 `golden-baseline.json` 阈值配置 + auto_compute 执行后 |

**统计**：14 项可内联 / 2 项不可内联 / 1 项暂停

---

## 二、briefing.json 内联校验清单（Phase 2A 写完后立即检）

### FATAL 级（必须全部通过，不通过则立即修复重写）

| # | Code | 规则 | 检测方法 |
|---|------|------|----------|
| B1 | **V24** | 全文无 `**` markdown 加粗残留 | 正则 `\*\*` 扫描 briefing.json 全文，命中即 FAIL |
| B2 | **V41** | globalReaction 每项 value ≤15字符且无括号 | 遍历 `globalReaction[]`，检查每项 `value`：`len(value) ≤ 15` 且不含 `()/（）` |
| B3 | **V42** | `_meta.generatedAt` 非空且含 "T" | 检查 `_meta.generatedAt` 不为空且包含字符 "T"（ISO 8601 格式标志） |
| B4 | **R1** | `topHoldings` ≥ 3 条 | `len(topHoldings) >= 3` |
| B5 | **V43** | 无占位符出现 | 全文搜索 `"--"` / `"N/A"` / `"TBD"` / `"待更新"` 作为 value |

### WARN 级（建议修复，不阻断）

| # | Code | 规则 | 检测方法 |
|---|------|------|----------|
| B6 | V5 | `coreJudgments` 精确 3 条 | `len(coreJudgments) == 3` |
| B7 | V5 | `globalReaction` ≥ 5 项 | `len(globalReaction) >= 5` |
| B8 | V5 | `riskPoints` ≥ 2 条 | `len(riskPoints) >= 2` |
| B9 | V5 | `smartMoney` ≥ 2 条 | `len(smartMoney) >= 2` |
| B10 | V29 | `coreJudgments[].logic` 含 → 箭头 | 每条 logic 中存在 `→` 字符 |
| B11 | V20 | `takeaway` 含 3-5 个【】标红 | 正则 `【[^】]+】` 匹配数 ∈ [3, 5] |
| B12 | V3 | `sentimentScore` 是 number | `isinstance(sentimentScore, (int, float))` |
| B13 | R3 | 全文无 "待更新" | 字符串搜索 |

---

## 三、markets.json 内联校验清单（Phase 2B 写完后立即检）

### FATAL 级

| # | Code | 规则 | 检测方法 |
|---|------|------|----------|
| M1 | **V43** | 所有 price ≠ 占位符 | 遍历 usMarkets/m7/asiaMarkets/commodities/cryptos，每项 `price` ∉ `{"--", "N/A", "n/a", "—", "", "TBD", "待更新"}` |
| M2 | **V24** | 全文无 `**` markdown 残留 | 正则扫描 |
| M3 | **V44** | 所有 sparkline 无零值 | 遍历所有 section 每项 `sparkline[]`，不含 0 |
| M4 | **V45** | price vs sparkline[-1] 数量级 <30% | 每项 `|price_num / sparkline[-1] - 1| < 0.3` |
| M5 | **V6** | sparkline[-1] vs price ≤5% | 每项 `|sparkline[-1] - price_num| / price_num ≤ 0.05` |
| M6 | **V38** | sparkline 趋势 vs change 方向一致 | `sparkline[-1] > sparkline[-2]` 应与 `change > 0` 方向一致（容差 0.5%） |
| M7 | **V42** | `_meta.generatedAt` 非空 | 同 B3 |

### WARN 级

| # | Code | 规则 | 检测方法 |
|---|------|------|----------|
| M8 | V3 | 所有 `change` 是 number | `isinstance(change, (int, float))` |
| M9 | V5 | usMarkets=4项、m7=7项、gics=11项、asiaMarkets≥4、commodities=6 | 数组长度检查 |
| M10 | V27 | 6 个 Insight 长度 30-100 字 | `30 ≤ len(xxxInsight) ≤ 100` |
| M11 | V25 | 无模糊前缀（~≈约左右） | 价格字段搜索 |

---

## 四、watchlist.json 内联校验清单（Phase 2C 写完后立即检）

### FATAL 级

| # | Code | 规则 | 检测方法 |
|---|------|------|----------|
| W1 | **V43** | 已上市标的 price ≠ 占位符 | 遍历 `stocks` 各板块，`listed != false` 的标的 `price` ∉ 占位符集合 |
| W2 | **V40** | metrics 无空值 | 每只已上市标的每个 `metrics[].value` ≠ `""` 且 ≠ `null` |
| W3 | **V44** | sparkline 禁止零值 | 每只标的 `sparkline[]` 无 0 |
| W4 | **V46** | chartData 禁止零值 | 每只标的 `chartData[]` 无 0（数组非空时检查） |
| W5 | **V45** | price vs sparkline[-1] 数量级 <30% | 同 M4 逻辑 |
| W6 | **V6** | sparkline[-1] vs price ≤5% | 同 M5 逻辑 |
| W7 | **V38** | sparkline 趋势 vs change 方向一致 | 同 M6 逻辑 |
| W8 | **V24** | 全文无 `**` markdown 残留 | 正则扫描 |

### WARN 级

| # | Code | 规则 | 检测方法 |
|---|------|------|----------|
| W9 | V28 | 每只已上市标的 metrics 精确 6 项 | `len(metrics) == 6` |
| W10 | V26 | 4 核心板块各 ≥ 2 只标的 | `ai_infra/ai_app/cn_ai/smart_money` 各板块 `len(stocks) >= 2` |
| W11 | V3 | 所有 `change` 是 number | `isinstance(change, (int, float))` |
| W12 | V32 | analysis 深度 ≥ 80 字 | 已上市标的 `len(analysis) >= 80` |

---

## 五、radar.json 内联校验清单（Phase 2D 写完后立即检）

### FATAL 级

| # | Code | 规则 | 检测方法 |
|---|------|------|----------|
| D1 | **V39** | 持仓 13F 合规 | ①`positions[].symbol` 不含 PUT/CALL/OPTION/WARRANT（大写比对）②`positions[].name` 不含 看跌期权/看涨期权/认购/认沽/期权/权证/PUT/CALL ③每家机构 `Σweight ≤ 105%` |
| D2 | **R2** | 每家 positions ≥ Top10 | `len(positions) >= 10` |
| D3 | **R3** | 全文无 "待更新" | 字符串搜索 radar.json 序列化文本 |
| D4 | **V24** | 全文无 `**` markdown 残留 | 正则扫描 |
| D5 | **V42** | `_meta.generatedAt` 非空 | 同 B3 |

### WARN 级

| # | Code | 规则 | 检测方法 |
|---|------|------|----------|
| D6 | V5 | trafficLights = 7 项 | `len(trafficLights) == 7` |
| D7 | V5 | events ≥ 3 条 | `len(events) >= 3` |
| D8 | V5 | smartMoneyHoldings ≥ 2 家 | `len(smartMoneyHoldings) >= 2` |
| D9 | V3 | riskScore 是 number | `isinstance(riskScore, (int, float))` |
| D10 | R8 | smartMoneyDetail 三梯队均非空 | T1旗舰/T2成长/策略师观点 各 ≥ 1 条 |

---

## 六、跨 JSON 一致性终检（Phase 2E — 4 个 JSON 全部写完后执行）

| # | Code | 规则 | 检测方法 |
|---|------|------|----------|
| X1 | V36 | radar.trafficLights 数值 vs markets 对应价格一致 | 比对 6 个红绿灯（CNH/布伦特/VIX/10Y美债/黄金/DXY）的 value 与 markets 中对应 price，容差 3% |
| X2 | V36 | markets.m7 标的 vs watchlist 同标的价格一致 | 比对 M7 个股在 markets 和 watchlist 中的 price，容差 3% |
| X3 | — | 4 个 JSON 的 `date` 字段一致 | `briefing.date == markets.date == watchlist.date == radar.date` |
| X4 | V34 | 4 个 JSON 的 `_meta.sourceType` 一致 | 全部为 `heavy_analysis` 或全部为 `weekend_insight` |
| X5 | R5 | briefing.topHoldings 与 radar.smartMoneyHoldings 机构名对应 | topHoldings 中每个机构名在 smartMoneyHoldings 的 manager 中有对应 |
| X6 | R3 | 4 个 JSON 合并后无 "待更新" | `json.dumps(全部4个JSON)` 中不含 "待更新" |

---

## 七、自校验不通过时的修复 SOP

```
Generator-Verifier 循环 SOP：

第1次生成 → 内联校验
  ├── 全部通过 → 进入下一个 JSON
  └── 有 FAIL →
      ├── FATAL 级 FAIL → 必须修复
      │   ├── 定位 FAIL 项（报告具体 Code + 字段位置）
      │   ├── 修复对应字段
      │   └── 第2次校验
      │       ├── 通过 → 继续
      │       └── 仍有 FATAL →
      │           ├── 第3次修复+校验（最终机会）
      │           │   ├── 通过 → 继续
      │           │   └── 仍 FAIL → ⚠️ 报告失败项，继续后续 JSON 生成
      │           │       （Phase 3 validate.py 会做终裁）
      │           └── 不再重试，避免无限循环
      └── 仅 WARN 级 → 记录警告，不阻断，继续生成下一个 JSON

最大重试次数：每个 JSON 最多 2 次修复重试（共 3 次尝试）
超时保护：单个 JSON 的 Generator-Verifier 循环不超过 3 轮
```

---

## 八、不可内联检测项声明（3 项 — 必须等 Phase 3 脚本执行）

以下 FATAL 项**无法在 Phase 2 内联检测**，必须依赖 Phase 3 的工具链：

| Code | 原因 | 由谁执行 |
|------|------|----------|
| **R9** | 需读取外部 `references/holdings-cache.json` 进行逐字段比对 | validate.py |
| **V35** | `audioUrl` — 语音播报已暂停，V35 降为 WARN，跳过不影响上传 | validate.py（WARN级） |
| **V_TL** | 红绿灯 `value↔status` 的阈值判定由 `auto_compute.py` 按 `golden-baseline.json` 配置自动计算，validate 在其之后校验 | auto_compute.py + validate.py |

> ⚠️ **V_TL 特殊说明**：虽然 AI 在 Phase 2 填写了 `trafficLights[].value` 和 `threshold`，但 `status` 字段由 `auto_compute.py` 在 Phase 3 自动覆盖。因此 Phase 2 无需（也不应该）检测 value↔status 一致性——不一致是正常的（AI 填的 status 会被脚本覆盖）。

---

## 九、auto_compute.py 覆盖字段清单（AI 无需手动计算）

以下 15 类字段由 `auto_compute.py` 在 Phase 3 自动计算覆盖，**AI 在 Phase 2 不需要手算这些字段**（可填初始值，脚本会覆盖）：

| # | 字段 | 计算逻辑 |
|---|------|----------|
| 1 | `radar.trafficLights[].status` | 按 baseline 阈值判定 green/yellow/red |
| 2 | `radar.riskScore` | `30 + Σ(green=0, yellow=10, red=20)`，封顶100 |
| 3 | `radar.riskLevel` | ≤44→low, ≤64→medium, 其他→high |
| 4 | `briefing.sentimentLabel` | 按 sentimentScore 查表映射 |
| 5 | `watchlist.stocks[].metrics[0].value` | 对齐 price |
| 6 | `watchlist.stocks[].metrics[1].value` | 对齐 change（含正负号+%） |
| 7 | `watchlist.stocks[].metrics[2].value` | 从 sparkline 计算 7 日涨跌 |
| 8 | `watchlist.stocks[].metrics[3].value` | 从 chartData 计算 30 日涨跌 |
| 9 | `watchlist.stocks[].metrics[5].value` | 综合评级（星星） |
| 10 | `markets.gics[]` 排序 | 按 change 降序 |
| 11 | 4个 JSON 的 `dataTime` | 当前北京时间 |
| 12 | 4个 JSON 的 `_meta.sourceType` | 修正废弃值 |
| 13 | sparkline[-1] 对齐 price | 偏差>0.5%时修正 |
| 14 | sparkline 尾部方向修复 | change 与 sparkline 尾部方向矛盾时调整 spark[-2] |
| 15 | price="--" 填充 | 从 sparkline[-1] 推导 |

**额外操作**：`_meta.generatedAt` 强制更新、`coreJudgments.references` 字符串→数组修复、`refreshInterval` 旧值清理。

---

## 十、validate.py WARN 误报识别（v11.0 试运行发现）

> **背景**：run_daily.sh 的 SYNC_DIR 指向 `miniapp_sync/`（根目录），validate.py 在 Phase 3 第0.5步检测的是根目录文件，而 AI 在 Phase 2 写入的是 `miniapp_sync/YYYY-MM-DD/` 日期子目录文件。run_daily.sh 在 Phase 3 最后阶段才将日期子目录内容同步到根目录。

**误报判断规则**：

| 场景 | 判断方法 | 处理方式 |
|------|---------|---------|
| validate WARN 报告的文本内容（如 takeaway、analysis）与当日生成的 JSON 不一致 | 比对 WARN 报告中引用的具体字符串 vs 当日写入的内容 | 旧文件误报，`--skip-warn` 安全跳过 |
| validate WARN 报告的内容确实存在于当日 JSON | 当日内容确实有问题 | 必须修复后重新执行 |

**v11.0 试运行实测**：V20/V32 WARN 均为旧文件误报，新数据实际通过。**FATAL 0项确认**。

---

> v1.0 — 2026-04-20 | 初始版本。从 validate.py v5.6（17项FATAL）精确提取可内联检测的 14 项 + 关键 WARN，定义 4 个 JSON 各自的校验清单 + 跨 JSON 一致性终检 + 修复 SOP + 不可内联项声明 + auto_compute 覆盖字段清单。
> v1.1 — 2026-04-20 | 新增§十 validate.py WARN 误报识别规则（v11.0 试运行实测发现）。
