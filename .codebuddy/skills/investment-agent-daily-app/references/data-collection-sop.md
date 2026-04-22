# 数据采集SOP — App版（v3.1）

> **用途**：投研鸭小程序数据生产第一阶段数据采集的完整操作规范，含情绪与预测数据采集（Batch A）。
> **核心原则**：数据完整性第一，精确到小数点后两位，严禁空位和模糊表述。
> **与原 Skill 的差异**：额外需要采集 sparkline（7天历史）、chartData（30天历史）、metrics 指标、个股分析文本。
> **v3.1 变更（2026-04-21）**：新增§0.10 JSON 字符串双引号防治规则（2026-04-21 血泪教训）。
> **v3.0 变更（2026-04-20）**：①新增§0.8 并行采集分组规范（Phase 1 四组并行+同步屏障）②新增§0.9 Context 压缩——最小字段集提取规范（11个批次精确字段表）③各批次标注并行组归属。
> **v2.1 变更（2026-04-09）**：新增第0.5节"price与sparkline同源规则"和第0.6节"sparkline禁止零值填充规则"（Harness v10.4 教训）。
> **v2.0 变更**：删除第九章 Refresh 精简采集批次定义（v9.0 统一为 Standard 全量执行）。

---

## 零、数据分类隔离规则（v1.4 新增 — 最高优先级）

> ⚠️ **本章是所有采集批次的前置约束，任何批次的操作都不得违反本章规则。**

### 0.1 两类数据的定义与合法数据源

| 数据类型 | 定义 | 合法数据源（必须用） | 禁止来源 |
|---------|------|------------------|---------|
| **交易数据** | 价格、涨跌幅、汇率、sparkline历史序列、成交量、指数点位 | **直接行情平台**：Google Finance (web_fetch) / AkShare API / OilPrice.com / FRED / 东方财富行情接口 / 同花顺行情接口 / CoinGecko | 任何新闻网站、财经媒体文章（Bloomberg/Reuters/CNBC/华尔街见闻/金十数据等）|
| **观点/事件/评论数据** | 事件背景、市场分析、机构判断、聪明钱动向、预测性观点 | 媒体网站（Bloomberg/Reuters/WSJ/FT/CNBC/华尔街见闻/第一财经等）| 不限（媒体是这类数据的合法来源）|

### 0.2 交叉污染禁止清单（零容忍）

以下行为视同 **RULE ZERO-A 违规**，触发阻断：

| 违规行为 | 示例 | 处理 |
|---------|------|------|
| 从新闻文章中提取股价/涨跌幅 | 读 Reuters 新闻："标普500下跌1.02%" → 直接写入 markets.json | **阻断，回到 Google Finance 重采** |
| 从财经媒体标题推算价格 | 看到"黄金创新高"新闻 → 估算价格 | **阻断，回到行情源采集** |
| 用训练数据里的历史汇率填充 | CNH写7.24（2024年旧数据）| **阻断，必须从 AkShare/行情源获取当日值** |
| 对 sparkline 使用线性估算 | 只有当日价格，手动推算7天序列 | **阻断，回到 AkShare/行情源重采** |
| 用新闻转述价格补全缺失字段 | 某标的 Google Finance 超时，从 CNBC 新闻里读到价格 | **阻断，切换备选行情源（非新闻源）** |
| **⚠️ 直接使用 web_search snippet 里的价格数字** | `web_search "DXY close"` → snippet 里显示"103.45"（来源：某财经媒体）→ 直接写入 JSON | **阻断。snippet 本质是媒体文章摘要，同样禁止。必须 `web_fetch` 到实际行情页面核实** |
| **⚠️ insightChain 文字中的数字与 price/change 字段不一致** | `usMarkets[VIX].change = -2.73`，但 `usInsightChain[].text = "VIX急升至27.3"` — 方向矛盾 | **阻断，JSON 生成阶段必须用 price/change 字段的值反向校验 insightChain 文字中的数字** |

### 0.3 批次前置自查（每个批次执行前必查）

```
在执行任何采集批次前，先问自己：
① 我即将采集的是「交易数据」还是「观点/事件数据」？
② 如果是交易数据 → 我的数据源是直接行情平台吗？（Google Finance/AkShare/FRED等）
③ 如果不是直接行情平台 → 停止！切换到正确的数据源后再继续
④ 交易数据采集成功后，可追溯到具体的 web_fetch URL 或 API 调用吗？
   不能 → 视为训练数据污染，阻断发布
```

### 0.4 各类数据对应的合法获取方式速查

> **⚠️ v3.1 新增 — 自媒体标题陷阱（2026-04-20 试运行血泪教训）**
>
> **事故经过**：web_search 返回了大量 CSDN/搜狐/sohu 等自媒体文章，标题声称"GPT-6正式发布"。AI 未去 OpenAI 官网/Bloomberg/Reuters 交叉核实，直接将虚假信息写入 briefing.json 的 coreEvent、globalReaction、coreJudgments、marketSummaryPoints、voiceText 共 **10+ 处**，造成**重大信息失误**。
>
> **根因**：违反 RULE ZERO —— 数字（事件）未来自本次可追溯的权威搜索，却被当做事实写入。
>
> **防治铁律（强制执行）**：
> 1. **模型/产品发布类重大事件**（如"GPT-6发布"/"Claude X.X发布"/"新iPhone"等），必须到**官方源**核实：OpenAI.com / Anthropic.com / Apple.com / NVIDIA.com / Bloomberg / Reuters，不得仅凭中文自媒体标题采信
> 2. **公司财务数据**（如"Anthropic年化收入300亿"），必须有路透/彭博/公司官方公告，不得引用分析机构估算或自媒体报道作为确定事实
> 3. **核实方法**：web_search 后发现重大事件时，**必须追加一次 web_fetch 到原始权威来源页面**，确认页面内容与标题一致，且发布时间在当日前后24小时内
> 4. **无法核实时的处理**：宁可删除该条事件，不写"可能发布"类模糊表述，更不可作为已确认事实写入

| 交易数据字段 | 合法获取方式 |
|------------|------------|
| 美股价格/涨跌幅 | `web_fetch: https://www.google.com/finance/quote/{TICKER}:{EXCHANGE}` |
| 美股 7 天 sparkline | AkShare 新浪源（脚本第三阶段自动补全） |
| 亚太指数 | 东方财富/同花顺行情接口，或 `web_fetch` Google Finance |
| 黄金/原油实时价格 | `web_fetch: https://oilprice.com/commodity-price-charts/` |
| 离岸人民币 CNH 汇率 | `ak.forex_hist_em("USDCNH")` 东方财富接口 |
| 10Y美债收益率 | `web_fetch: https://fred.stlouisfed.org/series/DGS10` 或 web_search |
| DXY 美元指数 | `web_search "DXY dollar index close YYYY-MM-DD"` → 核实来源为 ICE/Investing.com 等行情平台 |
| BTC/ETH 价格 | `web_fetch: https://www.google.com/finance/quote/BTC-USD` 或 CoinGecko API |
| VIX | `web_fetch: https://www.google.com/finance/quote/VIX:INDEXCBOE` |

### 0.5 price 与 sparkline 必须来自同一数据源（v2.1 新增 — FATAL 违规）

> ⚠️ **2026-04-09 事故教训**：AI 在填写 `price` 字段时使用了每手价格/旧数据源，导致：
> - 智谱AI price=HK$42.80（正确为 HK$929）差22倍
> - MiniMax price=HK$38.50（正确为 HK$999）差26倍
> - 博通 AVGO price=$179.83（正确为 $353.81）差2倍
> - 其余 10 个标的均有类似问题
>
> **触发原因**：price 和 sparkline 来自不同搜索结果，sparkline 是正确的行情价格，price 错误地使用了其他来源。

**强制规则**：
1. `price` 必须等于 `sparkline[-1]`（最后一个历史价格点），误差 ≤ 1%
2. 如果 `price` 和 `sparkline[-1]` 差距超过 5%，必须重新搜索确认，两者使用同一数据源
3. **禁止**：先搜到 price，再单独搜 sparkline 历史——两者应在同一个 `web_fetch` 请求中从同一数据源获取
4. validate.py V45 [FATAL] 会自动检测数量级差异（>50%），差异 1-50% 范围由 V6 [WARN] 处理

**港股特别注意**（两类常见错误）：
| 错误类型 | 示例 | 处理 |
|---------|------|------|
| 使用"每手价格"而非"每股价格" | 每手50股，误把每手价格HK$46视为每股价格 | Google Finance 显示的是每股价格，直接使用 |
| 使用旧来源/过期缓存价格 | 缺乏历史数据的标的用训练数据中的旧价格 | 必须实时 web_fetch 行情源 |

### 0.6 sparkline 禁止零值填充（v2.1 新增 — FATAL 违规）

> ⚠️ **2026-04-09 事故教训**：AI 对 VIX、日经225、KOSPI、黄金、DXY、10Y美债、CNH、BTC/ETH 等**没有7日历史数据**的标的，直接用 `0` 填充 sparkline，导致：
> - 前端图表渲染为从0跳到当前价的断崖曲线（视觉错误）
> - auto_compute.py 的 `compute_pct_change(sparkline[0]=0)` 返回 None → 7日涨跌空白
>
> **validate.py V44 [FATAL]** 会自动拦截 sparkline 中 >50% 为 0 的情况。

**强制规则**：
1. 任何标的的 sparkline **禁止** 使用 `0` 作为历史价格占位符
2. 获取不到历史数据时，必须：
   - 搜索 `stockanalysis.com`、`macrotrends.net`、`ycharts.com`、`chartexchange.com` 等历史价格数据库
   - 或通过 `web_search "{标的名} price history April 2026"` 获取7日历史
   - 或在同一行情源页面切换到 "5D" 视图获取5日历史（至少填充后5个点）
3. 实在获取不到历史数据 → 使用当前价作为所有7个点（平线），不要用 0
   - 例：`[97.47, 97.47, 97.47, 97.47, 97.47, 97.47, 97.47]` 胜过 `[0, 0, 0, 0, 0, 97.47, 97.47]`

---

## 〇.七、质量门禁与重试机制（v2.1 新增 — 数据准确性 > 执行速度）

> ⚠️ **核心原则**：宁可多搜几轮花多几分钟，也不能让错误数据发布到前端。

### 每个标的的数据采集必须通过以下 4 道门禁：

```
门禁1: price ≠ 0 且 ≠ "" 且 ≠ "--" → 否则阻断（V43 FATAL）
门禁2: sparkline 7个点全部 > 0 → 否则阻断（V44 FATAL）
门禁3: |price / sparkline[-1] - 1| < 30% → 否则阻断（V45 FATAL）
门禁4: sparkline[-1] vs price 偏差 < 5% → 否则阻断（V6 FATAL）
```

### 搜索失败时的重试 SOP：

```
第1次搜索: Google Finance (web_fetch)
  ↓ 如果失败或数据不完整
第2次搜索: StockAnalysis.com / ChartExchange.com (web_fetch)
  ↓ 如果仍然失败
第3次搜索: web_search "{标的名} stock price April 2026 history" → 核实来源
  ↓ 如果仍然失败
第4次搜索: 东方财富/同花顺/新浪财经 (中国标的) 或 macrotrends.net/ycharts.com (海外标的)
  ↓ 如果全部失败（极罕见）
降级处理: 使用当前价填充sparkline为平线，validate V47 会标记为 WARN 提醒
```

### 发布前必须运行 validate.py：

```bash
python3 validate.py <sync_dir> --mode standard

# 通过标准：
#   🔴 FATAL: 0（必须为0，否则阻断发布）
#   🟡 WARN: ≤3（超过3条建议修复后再发布）
```

### 当前 FATAL 级校验项清单（16项，全部不可绕过；V35 已暂停为 WARN）：

| 校验项 | 规则 | 阈值 |
|--------|------|------|
| V6 | sparkline[-1] vs price 偏差 | ≤5% |
| V24 | Markdown 残留 | 零容忍 |
| V38 | sparkline趋势 vs change 方向矛盾 | 零容忍 |
| V39 | 13F 持仓合规（无期权/伪造） | 零容忍 |
| V40 | metrics 无空值 | 零容忍 |
| V41 | globalReaction value 超长/含括号 | 零容忍 |
| V42 | generatedAt 为空 | 零容忍 |
| V43 | price 非占位符 | 零容忍 |
| V44 | sparkline 无零值 | 零容忍 |
| V45 | price vs sparkline 数量级 | ≤30% |
| V46 | chartData 无零值 | 零容忍 |
| V_TL | 红绿灯 value↔status 不一致 | 零容忍 |
| R1 | topHoldings < 3 | 零容忍 |
| R2 | smartMoneyHoldings ≥ Top10 | 零容忍 |
| R3 | 无"待更新"占位符 | 零容忍 |
| R9 | 持仓与cache一致 | 零容忍 |

---

## 零.十、JSON 字符串双引号防治（v3.1 新增 — 2026-04-21 血泪教训）

> ⚠️ **血泪教训**：2026-04-21 发现 `briefing.json` 和 `radar.json` 含未转义 ASCII 双引号（`"right business"` / `"保险公司正式开张"`），导致 JSON 语法错误，第0步校验本应拦截但因 #64 路径 Bug 读的是旧文件而漏过，最终前端无法加载数据。

### 铁律

| 场景 | 禁止 | 正确写法 |
|------|------|---------|
| 字符串内含英文引号 | `"称"right business""` | `"称\"right business\""` |
| 字符串内含品名/术语 | `"称"保险公司正式开张""` | `"称\"保险公司正式开张\""` 或 `"称'保险公司正式开张'"` |
| 字符串内引用说法 | `"他说"市场已见顶""` | `"他说\"市场已见顶\""` 或改用中文书名号《》 |

### Phase 2 写 JSON 前自查

```
每次在 JSON 字符串值里出现英文双引号时，自问：
① 这个 " 是字段值的结束符吗？→ 合法
② 这个 " 是我想表达引号标记吗？→ 必须改为 \" 或 '' 或 ""
③ 生成完整 JSON 后，用 python3 -m json.tool 脑内模拟校验一遍
```

### inline-verifier-rules 连动

Phase 2 Generator-Verifier 内联校验新增 **JQ1 [FATAL]**：每个 JSON 生成后用 `python3 -m json.tool` 验证语法，失败则立即定位并修复未转义双引号，**不得上报 Phase 3 才发现**。

---

## 一、采集批次总览

> **v3.0 新增**：「并行组」列标注每个批次的并行分组归属，详见 [§0.8 并行采集分组规范](#〇八并行采集分组规范v30-新增phase-1-四组并行同步屏障)。

| 批次 | 内容 | 搜索次数 | 数据源 | 适用日 | **并行组** |
|------|------|---------|--------|--------|-----------|
| 0 | 全球财经媒体头条扫描（参照`media-watchlist.md`一级必扫7家） | 2-3次 | web_search | 周一～周五 | **P1** |
| 0a | 深度媒体补充扫描（参照`media-watchlist.md`二级强化11家） | 1-2次 | web_search | 周一～周五 | **P1** |
| 0b | AI产业链重大动态专项扫描（参照`ai-supply-chain-universe.md`） | 1-2次 | web_search | 周一～周五 | **P1** |
| 1a | **M7个股 — 精确数据 + 7天历史** | **7次web_fetch** | Google Finance | 周一～周五 | **P2** |
| 1b | **美股指数+VIX — 精确数据 + 7天历史** | **3-4次web_fetch** | Google Finance | 周一～周五 | **P2** |
| 1c | **GICS 11板块ETF — 涨跌幅** | **11次web_fetch** | Google Finance | 周一～周五 | **P2** |
| 1d | **当日焦点个股 — 精确数据 + 7天历史** | **2-5次web_fetch** | Google Finance | 周一～周五 | **P2** |
| 2 | 亚太/港股数据 + 北向资金 + 7天历史 | 2-3次 | 东方财富/同花顺/web_search | 周一～周五 | **P3** |
| 3 | 大宗商品/汇率/加密/宏观 + 7天历史 | 2-3次 | web_search/金投网 | 周一～周五 | **P3** |
| 4 | 基金&大资金动向（参照`fund-universe.md`三梯队） | 8-12次+1次web_fetch | web_search + web_fetch + SEC EDGAR | 周一～周五 | **P4** |
| **5** | **watchlist 标的详情采集（metrics/PE/市值/营收增速/毛利率/ROE）** | **15-20次web_fetch** | Google Finance / StockAnalysis | 周一～周五 | **S1** |
| **6** | **本周事件日历 + 风险矩阵数据** | **1-2次** | web_search | 周一～周五 | **S1** |
| **A** | **情绪与预测数据采集（Polymarket / CME FedWatch）** | **1-3次web_fetch** | 详见第八章 | **周一～周五（可选批次，失败不阻断）** | **S1** |

**周一额外批次**：
- 批次7: 上周市场周度数据（2-3次）
- 批次8: 本周关键事件日历（2-3次）
- 批次9: 周末重大新闻（2-3次）

> ⚠️ **Batch A 与周一批次 7/8/9 的区别**：
> - 批次 7/8/9 仅在**周一**执行，内容是"上周回顾/本周日历/周末新闻"（行情补充类）
> - **Batch A** 在**周一～周五均执行**，内容是"情绪指数与预测市场概率"（情绪类），为可选批次，失败时不阻断主流程

---

## 二、Google Finance批量采集模板

### 批次1a — M7（7只，必须全部获取）

```
web_fetch: https://www.google.com/finance/quote/NVDA:NASDAQ
web_fetch: https://www.google.com/finance/quote/AAPL:NASDAQ
web_fetch: https://www.google.com/finance/quote/MSFT:NASDAQ
web_fetch: https://www.google.com/finance/quote/GOOGL:NASDAQ
web_fetch: https://www.google.com/finance/quote/META:NASDAQ
web_fetch: https://www.google.com/finance/quote/AMZN:NASDAQ
web_fetch: https://www.google.com/finance/quote/TSLA:NASDAQ
```

> **App版额外要求**：从 Google Finance 页面同时提取 "近1月" 图表数据中的7个时间点作为 sparkline；30个时间点作为 chartData。若无法获取历史数据，**回到批次重试；仍失败 → 阻断发布（禁止估算）**。

### 批次1b — 指数+VIX（4项）

```
web_fetch: https://www.google.com/finance/quote/.INX:INDEXSP
web_fetch: https://www.google.com/finance/quote/.IXIC:INDEXNASDAQ
web_fetch: https://www.google.com/finance/quote/.DJI:INDEXDJX
web_fetch: https://www.google.com/finance/quote/VIX:INDEXCBOE
```

### 批次1c — GICS 11板块ETF

```
web_fetch: https://www.google.com/finance/quote/XLE:NYSEARCA
web_fetch: https://www.google.com/finance/quote/XLK:NYSEARCA
web_fetch: https://www.google.com/finance/quote/XLF:NYSEARCA
web_fetch: https://www.google.com/finance/quote/XLV:NYSEARCA
web_fetch: https://www.google.com/finance/quote/XLY:NYSEARCA
web_fetch: https://www.google.com/finance/quote/XLC:NYSEARCA
web_fetch: https://www.google.com/finance/quote/XLI:NYSEARCA
web_fetch: https://www.google.com/finance/quote/XLB:NYSEARCA
web_fetch: https://www.google.com/finance/quote/XLP:NYSEARCA
web_fetch: https://www.google.com/finance/quote/XLU:NYSEARCA
web_fetch: https://www.google.com/finance/quote/XLRE:NYSEARCA
```

### 批次5 — watchlist 标的详情（v1.2：方案C）

对 stock-universe.md 中定义的每只标的，采集以下数据：

```
# 对每只美股/港股标的获取 PE(TTM)：
# 方式：AkShare / StockAnalysis.com（yfinance 已被 Yahoo 403 封禁）
# 失败时标注"—"，不阻断主流程

# 行情数据（前4项 metrics）来自主批次 AkShare 历史序列，无需额外采集
# 综合评级（第6项 metrics）由 calc_star_rating(change, pct_30d) 规则函数自动生成

# 若需要补充个股分析文本（analysis/reason/risks/tags），仍可用 web_fetch：
web_fetch: https://www.google.com/finance/quote/{TICKER}:{EXCHANGE}
web_search: "{公司名} {TICKER} latest earnings analysis 2026"
```

> **v1.2 变更**：metrics 6项改为方案C（行情4项+PE+评级），不再需要爬取市值/营收增速/毛利率/ROE。
> 批次5 的工作量大幅降低，PE 通过 `fetch_pe_ttm()` 脚本自动批量获取。

---

## 三、数据源优先级表（v1.3）

| 数据类型 | 首选 | 备选 | 第三选 |
|----------|------|------|--------|
| 美股指数/个股 | Google Finance (web_fetch) | 东方财富/StockAnalysis | MarketWatch |
| VIX | Google Finance `VIX:INDEXCBOE` | web_search | 同花顺 |
| 港股/A股 | 东方财富/同花顺 | Google Finance | 新浪财经 |
| 加密 | Google Finance `BTC-USD` | CoinGecko | web_search |
| 黄金/白银 | web_search + 金投网 | OilPrice.com | — |
| 布伦特原油（主指标） | web_fetch OilPrice.com | 金投网 | web_search |
| DXY | web_search "DXY dollar index close" | 金投网 | Finlore.io |
| 10Y美债 | web_search | FRED | — |
| **CNH（离岸人民币）历史序列** | **`ak.forex_hist_em("USDCNH")` AkShare** | **阻断发布** | — |
| **个股 PE(TTM)** | **StockAnalysis.com / web_search** | "—"（不阻断） | — |
| **历史走势（sparkline）** | **AkShare 新浪源+东方财富 fallback 真实历史序列** | **回采后重试** | **阻断发布（禁止估算）** |
| 基金&大资金 | SEC EDGAR | WhaleWisdom | web_search |
| **ARK 每日交易（v1.6新增）** | **`web_fetch: cathiesark.com/ark-funds-combined/trades`** | **web_search "ARK daily trade"** | — |
| **段永平/H&H 持仓（v1.6新增）** | **SEC EDGAR 13F (H&H International)** | **HedgeFollow/WhaleWisdom** | **雪球(@大道无形我有型)** |

---

## 四、sparkline 数据采集规范（方案A v1.5）

### 4.1 双轨分工说明（方案A）

| 字段 | 谁负责 | 方式 |
|------|--------|------|
| `sparkline`（7天历史序列） | **脚本** `refresh_verified_snapshot.py v3.0` | AkShare 新浪源+东方财富 fallback 批量下载，在第三阶段自动补全 |
| `chartData`（30天历史序列） | **脚本** `refresh_verified_snapshot.py v3.0` | AkShare 新浪源+东方财富 fallback 批量下载，在第三阶段自动补全 |
| `price` / `change` | **AI** 从 Google Finance 等行情源直采 | RULE ZERO-A 保障 |

**AI 在第一阶段不需要采集 sparkline/chartData 的历史序列**。第一阶段只需采集当日价格和涨跌幅（用于 price/change 字段）；sparkline/chartData 由脚本在第三阶段自动从 AkShare 补全。

> ⚠️ **AkShare 缺口标的**：VIX/DXY/10Y美债/CNH/BTC/ETH 的 sparkline/chartData，AkShare 缺口无法覆盖，脚本会跳过这些标的，保留 AI 估算值。

### 4.2 港股/A股 sparkline 采集方式

```
# 港股历史收盘价（东方财富/同花顺行情页）
web_fetch: https://quote.eastmoney.com/hk/03690.html
# 或: AkShare 接口（AI 不能直接调用，但可在行情页面读取图表数据）

# A股历史收盘价（东方财富行情页）
web_fetch: https://quote.eastmoney.com/sz300750.html
```

取近7天收盘价构成 sparkline 数组，近30天收盘价构成 chartData 数组。

### 4.3 禁止事项（方案A 不变）

- **禁止**基于当日价格 ± 随机波动估算
- **禁止**用线性插值/扩展生成 chartData
- **美股 sparkline/chartData 不需要 AI 手动采集**——脚本 v3.0（AkShare）自动处理

> v1.5 变更：方案A 下美股/主要指数的 sparkline 完全由脚本负责，AI 采集工作量大幅降低。v3.0 后港股/A股也由脚本覆盖（AkShare 新浪源+东方财富 fallback），仅 VIX/DXY/10Y/CNH/BTC/ETH 为 AkShare 缺口，需 AI 估算值兜底。

---

## 五、数据完整性验证门禁

### 验证清单（逐项打✅）

| # | 验证项 | 要求 | 缺失时操作 |
|---|--------|------|-----------|
| 1 | briefing: coreEvent | title + chain(3-6条) | 补充分析生成 |
| 2 | briefing: globalReaction | ≥5项，每项 name+value+direction | 补充数据 |
| 3 | briefing: coreJudgments | 精确3条，每条 title+confidence+logic | 补充分析 |
| 4 | briefing: actionHints | 0-2条（可为空数组），价投风格低频精而少 | 补充（无高置信机会时为空） |
| 5 | briefing: smartMoney | ≥2条 | 补充扫描 |
| 6 | markets: usMarkets | 4项+sparkline | 回到1b补采 |
| 7 | markets: m7 | 7项+sparkline | 回到1a补采 |
| 8 | markets: asiaMarkets | ≥4项+sparkline | 回到2补采 |
| 9 | markets: commodities | 6项+sparkline | 回到3补采 |
| 10 | markets: gics | 11项 | 回到1c补采 |
| 11 | watchlist: 4个核心板块每板块≥2只 | ai_infra/ai_app/cn_ai/smart_money 全覆盖，hot_topic可为空 | 回到5补采 |
| 12 | watchlist: 每只标的metrics | 6项 | 补充搜索 |
| 13 | radar: trafficLights | 7项 | 补充数据 |
| 14 | radar: riskAlerts | 填空数组 `[]`（v4.8 废弃渲染） | 固定填 [] |
| 15 | radar: events | ≥3条 | 补充搜索 |
| 16 | radar: smartMoneyDetail | 3梯队 | 补充扫描 |
| **17** | **markets: 6个板块Insight** | **usInsight/m7Insight/asiaInsight/commodityInsight/cryptoInsight/gicsInsight，每个30-80字** | **基于已采集数据分析提炼** |
| **18** | **markets: 6个板块 insightChain（⚠️ v4.4 起前端不渲染，建议跳过）** | **usInsightChain/m7InsightChain/asiaInsightChain/commodityInsightChain/cryptoInsightChain/gicsInsightChain，每个数组3条，每条包含 icon/label/text。v4.4 起前端不渲染因果链卡片（仅 gicsInsightChain 的"轮动"节点被提取为热力图摘要），可省略** | **可选——省略不影响发布** |
| **19** | **⭐ 数字一致性交叉校验（强制）** | **insightChain/insight 文字中出现的任何价格、涨跌幅、数字，必须与 markets.json 对应字段的 price/change 值一致，禁止矛盾（如 change=-2.73 但文字写"上涨"）** | **JSON 生成阶段逐一核对，不一致→修改文字使其对齐字段值** |

**⭐ 可选字段建议检查（非阻断，未填充时前端对应模块不渲染）**：

| # | 验证项 | 要求 | 未填时操作 |
|---|--------|------|-----------|
| O1 | briefing: timeStatus（建议） | bjt+est+marketStatus(枚举)+refreshInterval | 根据当前时间推算填入，或省略（前端自行计算时区） |
| O2 | radar: predictions（建议） | 2-4条，每条 title+source(枚举)+probability(0-100)+trend(枚举)+change24h | 参照 Batch A 采集的 Polymarket/Kalshi/CME FedWatch 数据；获取失败则省略该字段 |
| O3 | 所有JSON: _meta（建议） | sourceType+generatedAt(ISO8601)+skillVersion | sourceType 按模式填写（Standard→`heavy_analysis` / Weekend→`weekend_insight`）；generatedAt 为执行时间（+08:00）；skillVersion 为当前 SKILL.md 顶部版本号 |

---

## 六、已知堵点与降级路径（v1.3）

| 堵点 | 降级路径 |
|------|---------|
| Google Finance 403/超时 | → web_search → 东方财富/StockAnalysis |
| **sparkline 历史数据无法获取** | → **回采后重试；仍失败 → 阻断发布（禁止估算）** |
| **个股 PE 数据缺失** | → **标注"—"，不阻断（PE 为辅助指标）** |
| chartData 30天数据无法获取 | → 回到对应数据源重采，**禁止估算扩展** |
| 某板块标的全部数据失败 | → 替换为同板块备选标的（参见 stock-universe.md 备选池） |
| 港股数据获取困难 | → 东方财富/同花顺 → 智通财经 |
| 大宗期货 Google 不支持 | → OilPrice.com → 金投网 |
| **CNH 历史序列失败** | → **阻断发布，禁止退化到估算** |
| **Polymarket API 503/超时** | → **web_search 定向搜索 → 仍失败 → 跳过该 predictions 条目，不阻断主流程** |
| **Kalshi API 访问受限** | → **web_search 备选 → 仍失败 → 跳过该 predictions 条目，不阻断主流程** |
| **CME FedWatch 页面加载失败** | → **web_search "CME FedWatch 降息概率" → 仍失败 → 跳过该 predictions 条目，不阻断主流程** |
| 上传失败 | → JSON 文件保留，可手动重传 |

---

## 七、板块 Insight 生成规范（v1.3 新增）

> **生成时机**：在第二阶段"结构化 JSON 生成"时，基于已采集的数据自动提炼每个板块的 Insight。
> **生成方式**：AI 分析当日采集数据，提炼核心驱动力+关键数字+信号判断。

### 7.1 通用规范

| 维度 | 要求 |
|------|------|
| **长度** | 30-80字，一句话到两句话 |
| **内容** | 板块核心驱动力 + 关键数字 + 信号判断 |
| **风格** | 对齐日报中的"XX信号"段落，精准简洁 |
| **格式** | 纯文本，禁止 markdown/emoji |
| **质量** | 不能只说"市场上涨"，必须说清为什么涨、谁领涨、后续怎么看 |

### 7.2 各板块 Insight 要点

| 板块 | 字段 | 内容要点 |
|------|------|---------|
| 美股 | `usInsight` | 主线（科技/价值）、领涨指数、VIX信号、核心催化 |
| M7 | `m7Insight` | 分化情况、领涨/拖累个股、AI资本开支/业绩催化 |
| 亚太 | `asiaInsight` | 港股/A股/日韩格局、资金面（南向/北向）、政策驱动 |
| 大宗 | `commodityInsight` | 黄金/原油核心驱动、美元/债券联动、地缘因素 |
| 加密 | `cryptoInsight` | BTC走势/ETF资金流/链上信号/监管动态 |
| GICS | `gicsInsight` | 板块轮动方向、资金偏好风格（成长vs价值） |

### 7.3 示例

```
usInsight: "科技股领涨带动纳指创两周新高，AI板块延续强势，VIX降至13下方暗示短期波动率压缩，注意均值回归风险"
m7Insight: "M7分化加剧，NVDA独涨4.2%领跑受益AI资本开支超预期，TSLA连跌三日拖累整体表现"
asiaInsight: "港股微涨结束3月惨淡表现，恒生科技受南向资金支撑领涨2.15%，日经受日元走弱提振"
```

---

## 八、Batch A — 情绪与预测数据采集 SOP（v1.7 更新）

> **定位**：Batch A 是独立于行情采集批次之外的**情绪类可选批次**，适用于所有工作日（周一～周五均执行）。
> **执行时机**：在批次 6（事件日历）完成后、进入第二阶段 JSON 生成之前执行。
> **非阻断原则**：Batch A 的所有数据源均为可选。任何子批次获取失败时，记录失败原因后**跳过**，不影响主流程。

### ~~8.1 子批次 A1 — CNN Fear & Greed Index（已废弃 2026-04-06）~~

> Fear & Greed 数据已从产品中移除（太散户化，对价投决策价值有限）。fearGreed 字段不再产出。

---

### 8.2 子批次 A2 — Polymarket 预测概率

**产出字段**：`radar.predictions[]`（source = "Polymarket" 的条目）

**数据源（优先级顺序）**：

```
# 首选：Polymarket CLOB API（搜索关键问题）
web_fetch: https://clob.polymarket.com/markets?active=true&limit=20

# 筛选策略：从返回的市场列表中，选取与以下主题相关的问题：
# - 美联储利率/降息决策
# - 中东地缘政治（停火/和谈）
# - 宏观经济走向（衰退/软着陆）
# - 重大政治事件（选举/峰会结果）

# 备选：web_search 定向搜索
web_search: "Polymarket Fed rate cut probability 2026"
web_search: "Polymarket [当日热点主题] probability"
```

**筛选规则（从 API 结果中提取 2-4 条）**：
1. 概率在 10%-90% 之间（两极端的问题信息量低）
2. 与当前市场主要叙事相关（AI/宏观/地缘/政策）
3. 优先选择与当日 coreEvent 主题相关的预测问题

**字段映射**：
```jsonc
{
  "title": "美联储6月降息?",        // 问题标题（中文，20字以内）
  "source": "Polymarket",
  "probability": 72,                // 整数，0-100
  "trend": "up",                   // up/down/stable（与前日相比）
  "change24h": 5                   // 24小时概率变化（正数=上升，负数=下降）
}
```

**失败处理**：API 503/超时 → web_search 获取最新数据 → 仍失败 → **跳过该条目**（predictions 可为空数组 `[]`）

---

### 8.3 子批次 A3 — Kalshi 预测概率

**产出字段**：`radar.predictions[]`（source = "Kalshi" 的条目）

**数据源**：

```
# Kalshi API（需注意可能有访问限制）
web_fetch: https://trading-api.kalshi.com/trade-api/v2/markets?limit=20&status=open

# 备选：web_search
web_search: "Kalshi prediction market probability 2026"
```

**筛选规则**：同 Polymarket，选取与宏观/政策/AI主题相关的2条以内。

**失败处理**：与 Polymarket 相同，失败则跳过，不阻断。

---

### 8.4 子批次 A4 — CME FedWatch 降息概率

**产出字段**：`radar.predictions[]`（source = "CME FedWatch" 的条目）

**数据源（优先级顺序）**：

```
# 首选：CME FedWatch 工具页面
web_fetch: https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html

# 备选：web_search
web_search: "CME FedWatch Fed funds rate probability June 2026"
web_search: "美联储6月降息概率 CME FedWatch"
```

**需要采集的数据**：
- 下次（最近）FOMC 会议的降息概率（25bp or 50bp）
- 该概率相比昨日的变化（+N% 或 -N%）
- 会议日期（如 "6月会议"）

**字段映射示例**：
```jsonc
{
  "title": "美联储6月降息?",
  "source": "CME FedWatch",
  "probability": 28,               // 降息概率百分比（取降息总概率，即 25bp + 50bp 之和）
  "trend": "down",
  "change24h": -4
}
```

**失败处理**：页面加载失败 → web_search → 仍失败 → **跳过该条目**

---

### 8.5 Batch A 执行流程与汇总

**执行顺序**：A2（Polymarket）→ A3（Kalshi）→ A4（CME FedWatch）

**汇总规则**：
- A2/A3/A4 各自成功的条目 → 汇入 `radar.predictions[]`
- 最终 `predictions` 数组 2-4 条为宜；所有子批次均失败时 → `predictions` 填为 `[]`（空数组允许）

**Batch A 完成确认清单**：

| # | 检查项 | 状态记录 |
|---|--------|---------|
| A2 | Polymarket 预测概率获取 | 成功-[N条]/失败-[原因] |
| A3 | Kalshi 预测概率获取 | 成功-[N条]/失败-[原因] |
| A4 | CME FedWatch 降息概率获取 | 成功/失败-[原因] |

---

---

## 〇.八、并行采集分组规范（v3.0 新增 — Phase 1 四组并行+同步屏障）

> **核心原则**：按 **context-centric decomposition** 划分——每组的上下文需求独立，无数据依赖，可安全并行。
> **目标**：Phase 1 采集时间减少 60-70%（从串行 ~50次 web_fetch/search 改为 4 组并发）。

### 并行分组定义

| 组号 | 批次 | 内容 | 搜索次数 | 上下文依赖 | 可并行原因 |
|------|------|------|---------|-----------|-----------|
| **P1** | 0 + 0a + 0b | 媒体头条 + AI产业链扫描 | 3-7次 web_search | media-watchlist.md + ai-supply-chain-universe.md | 纯搜索，不依赖行情数据 |
| **P2** | 1a + 1b + 1c + 1d | 美股行情 + 指数 + GICS + 焦点 | 22-27次 web_fetch | Google Finance URL模板 | 纯行情抓取，不依赖其他组 |
| **P3** | 2 + 3 | 亚太 + 大宗/汇率/加密 | 4-6次 web_search/fetch | 行情源URL | 独立市场，不依赖P1/P2 |
| **P4** | 4 | 基金&大资金动向 | 8-12次 search + 1次 fetch | fund-universe.md | 独立知识域，不依赖行情组 |
| **S1** | 5 + 6 + A | watchlist详情 + 事件 + 情绪 | 17-25次 | 依赖 P2(GICS结果) | 需 P1-P4 全部完成后串行 |

### 执行时序

```
Phase 1 启动
├── [同时发出] P1 (3-7次 web_search)
├── [同时发出] P2 (22-27次 web_fetch)
├── [同时发出] P3 (4-6次 web_search/fetch)
└── [同时发出] P4 (8-12次 web_search + 1次 web_fetch)
    │
    ├──── 同步屏障 ────┤
    │  （P1-P4 全部完成才可通过）
    │
    └── [串行] S1: Batch 5 → Batch 6 → Batch A
        │
        └── Phase 1.5 完整性门禁
```

### 并行实现方式（CodeBuddy 工具调用）

在同一个 AI turn 中，发出 P1-P4 四组的全部工具调用（web_fetch / web_search），CodeBuddy 会自动并行执行同一 turn 内的多个工具调用。

**P1 工具调用示例**（3-5 次 web_search 同时发出）：
```
web_search: "global financial news headlines today April 2026"
web_search: "AI产业链 重大动态 today"
web_search: "tech earnings AI capex latest"
```

**P2 工具调用示例**（22+ 次 web_fetch 同时发出）：
```
web_fetch: https://www.google.com/finance/quote/NVDA:NASDAQ
web_fetch: https://www.google.com/finance/quote/AAPL:NASDAQ
... (M7 全部 7 只 + 指数 4 项 + GICS 11 项)
```

**P3 工具调用示例**（4-6 次）：
```
web_search: "亚太市场 恒生 上证 日经 today"
web_search: "gold oil DXY 10Y yield BTC ETH price today"
```

**P4 工具调用示例**（8-12 次）：
```
web_search: "Berkshire Hathaway Buffett latest"
web_search: "段永平 雪球 大道无形我有型"
web_fetch: https://cathiesark.com/ark-funds-combined/trades
... (按 fund-universe.md 五层搜索)
```

### 同步屏障规则

1. **P1-P4 全部完成后**，对所有工具调用结果执行"Context 压缩"（§0.9），提取最小字段集
2. **压缩后**进入 S1 串行组：Batch 5（watchlist 详情，需参考 P2 的 GICS 结果选热点标的）→ Batch 6（事件日历）→ Batch A（情绪预测）
3. **S1 完成后**进入 Phase 1.5 完整性门禁

### 失败处理

| 场景 | 处理 |
|------|------|
| P1 某次搜索超时 | P1 内重试 1 次；仍失败 → 跳过该搜索，不阻断其他组 |
| P2 某只标的 web_fetch 403 | 按 data-source-priority.md 降级到备选源重试；仍失败 → 标注该标的"数据缺失"，不阻断 |
| P3 全部失败 | 亚太+大宗为核心数据，重试 2 次；仍全失败 → 阻断（Phase 1.5 门禁会拦截） |
| P4 全部失败 | 基金动向不阻断主流程，标注"聪明钱数据不完整"，Phase 1.5 门禁会降级处理 |
| S1 Batch 5 依赖 P2 数据但 P2 不完整 | 用已有行情数据继续，缺失标的从备选池替补 |

---

## 〇.九、Context 压缩——最小字段集提取规范（v3.0 新增 — 铁律）

> **核心铁律**：每次 `web_fetch` / `web_search` 返回结果后，**必须立即提取下方定义的最小字段集，然后丢弃原始 HTML/snippet**。
> **目标**：Phase 1 上下文从约 76k token 压缩至约 35k token，腾出 40k+ 余量给 Phase 2 JSON 生成。
> **原则**：压缩的是"HTML噪音"，不是"有用信息"。最小字段集必须覆盖 JSON 生成所需的全部原始数据。

### 9.1 交易数据批次（P2 行情 / P3 亚太+大宗）

**每次 web_fetch Google Finance 页面后，立即提取以下字段，丢弃原始 HTML：**

| 字段 | 类型 | 示例 | 用途 |
|------|------|------|------|
| `name` | string | "英伟达" | markets/watchlist 的 name |
| `symbol` | string | "NVDA" | 标的标识 |
| `price` | string | "$134.50" | price 字段（含货币符号） |
| `change` | number | -2.37 | change 字段（纯数字，负号表跌） |
| `5D_close` | number[7] | [136.2, 135.8, 137.1, 135.5, 136.0, 134.9, 134.5] | AI 初始 sparkline（脚本第三阶段会用 AkShare 覆盖美股） |

**提取格式示例**（一只标的约 80 token，对比原始 HTML ~3000 token）：
```
NVDA 英伟达 | $134.50 | -2.37% | 5D:[136.2,135.8,137.1,135.5,136.0,134.9,134.5]
```

**GICS 11板块（Batch 1c）只需 3 个字段：**

| 字段 | 类型 | 示例 |
|------|------|------|
| `etf` | string | "XLK" |
| `name` | string | "信息技术" |
| `change` | number | 1.82 |

### 9.2 媒体/新闻批次（P1 媒体扫描）

**每次 web_search 返回后，每条结果只保留：**

| 字段 | 类型 | 最大长度 | 用途 |
|------|------|---------|------|
| `title` | string | 60字 | coreEvent.chain[].title |
| `source` | string | 20字 | source 字段 |
| `url` | string | — | url 字段（付费墙除外） |
| `date` | string | 10字 | 时效性判断 |
| `summary` | string | **≤80字** | chain[].brief + 事件分析素材 |

**提取格式示例**（一条新闻约 60 token，对比原始 snippet ~500 token）：
```
[Reuters 2026-04-20] 美联储会议纪要显示官员对降息节奏存分歧 | 多数官员支持维持利率不变至通胀进一步回落，但少数派认为就业数据恶化可能需要预防性降息 | https://reuters.com/...
```

### 9.3 基金动向批次（P4）

**每条基金/策略师动态只保留：**

| 字段 | 类型 | 最大长度 | 用途 |
|------|------|---------|------|
| `fund_name` | string | 30字 | smartMoneyDetail 的 name |
| `person` | string | 15字 | 关联人物 |
| `action` | string | **≤100字** | funds[].action 字段 |
| `signal` | string | 枚举 | bullish/bearish/neutral |
| `source` | string | 20字 | source |
| `url` | string | — | url |
| `date` | string | 10字 | 时效性 |

### 9.4 watchlist 详情批次（S1 Batch 5）

**每只标的只保留：**

| 字段 | 类型 | 最大长度 | 用途 |
|------|------|---------|------|
| `symbol` | string | — | 标的标识 |
| `PE_TTM` | string | 10字 | metrics[4] |
| `analysis_summary` | string | **≤150字** | analysis 字段素材 |
| `risks_summary` | string | **≤80字** | risks 信息 |

### 9.5 事件日历批次（S1 Batch 6）

| 字段 | 类型 | 最大长度 | 用途 |
|------|------|---------|------|
| `date` | string | 10字 | events[].date |
| `title` | string | 30字 | events[].title |
| `impact` | string | 枚举 | high/medium/low |
| `source` | string | 20字 | source |
| `url` | string | — | url |

### 9.6 情绪预测批次（S1 Batch A）

| 字段 | 类型 | 用途 |
|------|------|------|
| `title` | string | predictions[].title |
| `source` | string(枚举) | Polymarket/Kalshi/CME FedWatch |
| `probability` | number | 0-100 整数 |
| `trend` | string(枚举) | up/down/stable |
| `change24h` | number | ±N |

### 9.7 绝对禁止事项

1. **绝对禁止**在工具调用返回后保留原始 HTML 页面内容在上下文中
2. **绝对禁止**保留 web_search 的完整 snippet 文本（只保留提取后的结构化字段）
3. **绝对禁止**将一次 web_fetch 的完整响应跨批次携带（每次提取后立即丢弃）
4. **绝对禁止**在 summary/action 字段中超过规定最大长度（超长 = 上下文浪费）
5. **允许**在同一 turn 内的并行工具调用结果中保留结构化提取字段（这是正常的数据积累）

### 9.8 Context 预算分配

| 阶段 | 预算 | 来源 |
|------|------|------|
| Phase 0 | ~5k | SKILL.md(自动) + L1 refs |
| Phase 1 (压缩后) | ~35k | P1-P4+S1 全部采集结果的提取字段 |
| Phase 1.5 门禁 | ~2k | 门禁检查清单 |
| Phase 1.8 L3 加载 | ~70k | json-schema.md(60k) + stock-universe(15k) + holdings-cache(5k) + inline-verifier(8k) |
| Phase 2 JSON生成 | ~40k+ | 4个JSON的写入空间 |
| **总计** | ~152k | 在 200k context 窗口内 |

> ⚠️ **若不做 Context 压缩**：Phase 1 原始 HTML 约 76k + Phase 2 需要 ~110k = 186k，已接近 200k 极限，留给 JSON 生成的余量极少。压缩后 Phase 1 降至 ~35k，腾出 ~40k 关键余量。

---

> v3.0 — 2026-04-20 | **v11.0 架构升级**：新增§0.8 并行采集分组规范（P1-P4 四组并行+S1串行+同步屏障+失败处理）+ §0.9 Context 压缩最小字段集提取规范（11个批次精确字段表+绝对禁止事项+Context预算分配）。
> v2.1 — 2026-04-09 | 新增§0.5 price与sparkline同源规则 + §0.6 sparkline禁止零值填充规则 + §0.7 质量门禁与重试机制。
> v2.0 及更早版本 | 详见 git log 或 CHANGELOG.md。
