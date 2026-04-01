# 数据采集SOP — App版（v1.2）

> **用途**：投研鸭小程序数据生产第一阶段数据采集的完整操作规范。
> **核心原则**：数据完整性第一，精确到小数点后两位，严禁空位和模糊表述。
> **与原 Skill 的差异**：额外需要采集 sparkline（7天历史）、chartData（30天历史）、metrics 指标、个股分析文本。

---

## 一、采集批次总览

| 批次 | 内容 | 搜索次数 | 数据源 |
|------|------|---------|--------|
| 0 | 全球财经媒体头条扫描（参照`media-watchlist.md`一级必扫7家） | 2-3次 | web_search |
| 0a | 深度媒体补充扫描（参照`media-watchlist.md`二级强化11家） | 1-2次 | web_search |
| 0b | AI产业链重大动态专项扫描（参照`ai-supply-chain-universe.md`） | 1-2次 | web_search |
| 1a | **M7个股 — 精确数据 + 7天历史** | **7次web_fetch** | Google Finance |
| 1b | **美股指数+VIX — 精确数据 + 7天历史** | **3-4次web_fetch** | Google Finance |
| 1c | **GICS 11板块ETF — 涨跌幅** | **11次web_fetch** | Google Finance |
| 1d | **当日焦点个股 — 精确数据 + 7天历史** | **2-5次web_fetch** | Google Finance |
| 2 | 亚太/港股数据 + 北向资金 + 7天历史 | 2-3次 | 东方财富/同花顺/web_search |
| 3 | 大宗商品/汇率/加密/宏观 + 7天历史 | 2-3次 | web_search/金投网 |
| 4 | 基金&大资金动向（参照`fund-universe.md`三梯队） | 3-5次 | web_search + SEC EDGAR |
| **5** | **watchlist 标的详情采集（metrics/PE/市值/营收增速/毛利率/ROE）** | **15-20次web_fetch** | Google Finance / StockAnalysis |
| **6** | **本周事件日历 + 风险矩阵数据** | **1-2次** | web_search |

**周一额外批次**：
- 批次7: 上周市场周度数据（2-3次）
- 批次8: 本周关键事件日历（2-3次）
- 批次9: 周末重大新闻（2-3次）

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

> **App版额外要求**：从 Google Finance 页面同时提取 "近1月" 图表数据中的7个时间点作为 sparkline；30个时间点作为 chartData。若无法获取历史数据，使用当日价格 ± 模拟波动生成。

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
# 方式：yfinance.Ticker(ticker).info["trailingPE"]
# 失败时标注"—"，不阻断主流程

# 行情数据（前4项 metrics）来自主批次 yfinance/AkShare 历史序列，无需额外采集
# 综合评级（第6项 metrics）由 calc_star_rating(change, pct_30d) 规则函数自动生成

# 若需要补充个股分析文本（analysis/reason/risks/tags），仍可用 web_fetch：
web_fetch: https://www.google.com/finance/quote/{TICKER}:{EXCHANGE}
web_search: "{公司名} {TICKER} latest earnings analysis 2026"
```

> **v1.2 变更**：metrics 6项改为方案C（行情4项+PE+评级），不再需要爬取市值/营收增速/毛利率/ROE。
> 批次5 的工作量大幅降低，PE 通过 `fetch_pe_ttm()` 脚本自动批量获取。

---

## 三、数据源优先级表（v1.2）

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
| **个股 PE(TTM)** | **`yfinance.Ticker.info["trailingPE"]`** | "—"（不阻断） | — |
| **历史走势（sparkline）** | **yfinance/AkShare 真实历史序列** | **回采后重试** | **阻断发布（禁止估算）** |
| 基金&大资金 | SEC EDGAR | WhaleWisdom | web_search |

---

## 四、sparkline 数据采集规范（v1.2）

### 4.1 唯一合法方式（真实历史序列）

从 yfinance/AkShare 直接获取近 7-30 天的真实收盘价历史序列。

```python
# yfinance 批量获取（美股）
last, prev, last7, last30 = yf_daily(ticker, period="40d")

# AkShare 港股
last30 = ak.stock_hk_daily(symbol=symbol, adjust="")["close"].tail(30).tolist()

# AkShare A股
last30 = ak.stock_zh_a_daily(symbol=symbol, ...)["close"].tail(30).tolist()
```

### 4.2 禁止事项（v1.2强制）

- **禁止**基于当日价格 ± 随机波动估算
- **禁止**用线性插值/扩展生成 chartData
- 如果历史数据真的无法获取 → **回到采集批次重试；仍失败 → 阻断发布**

> v1.2 变更：完全移除估算降级路径，sparkline/chartData 只允许真实历史序列。

---

## 五、数据完整性验证门禁

### 验证清单（逐项打✅）

| # | 验证项 | 要求 | 缺失时操作 |
|---|--------|------|-----------|
| 1 | briefing: coreEvent | title + chain(3-6条) | 补充分析生成 |
| 2 | briefing: globalReaction | ≥5项，每项 name+value+direction | 补充数据 |
| 3 | briefing: coreJudgments | 精确3条，每条 title+confidence+logic | 补充分析 |
| 4 | briefing: actions.today | ≥1条 | 补充 |
| 5 | briefing: smartMoney | ≥2条 | 补充扫描 |
| 6 | markets: usMarkets | 4项+sparkline | 回到1b补采 |
| 7 | markets: m7 | 7项+sparkline | 回到1a补采 |
| 8 | markets: asiaMarkets | ≥4项+sparkline | 回到2补采 |
| 9 | markets: commodities | 6项+sparkline | 回到3补采 |
| 10 | markets: gics | 11项 | 回到1c补采 |
| 11 | watchlist: 每板块≥2只 | 7板块全覆盖 | 回到5补采 |
| 12 | watchlist: 每只标的metrics | 6项 | 补充搜索 |
| 13 | radar: trafficLights | 7项 | 补充数据 |
| 14 | radar: riskAlerts | ≥2条 | 补充分析 |
| 15 | radar: events | ≥3条 | 补充搜索 |
| 16 | radar: smartMoneyDetail | 3梯队 | 补充扫描 |
| **17** | **markets: 6个板块Insight** | **usInsight/m7Insight/asiaInsight/commodityInsight/cryptoInsight/gicsInsight，每个30-80字** | **基于已采集数据分析提炼** |

---

## 六、已知堵点与降级路径（v1.2）

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
| 上传失败 | → JSON 文件保留，可手动重传 |

---

## 七、板块 Insight 生成规范（v1.2.1 新增）

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

> v1.2.1 — 2026-04-02 00:21 | 新增第七章"板块 Insight 生成规范"：定义6个板块级Insight字段的生成规范、内容要点和示例；数据完整性门禁新增第17项Insight验证。
> v1.2 — 2026-04-01 | 批次5采集方案升级为方案C（yfinance PE + 规则化评级），完全移除 Google Finance 财报爬取和 sparkline 估算降级；数据源优先级表补充 CNH 专用通道；降级路径强制阻断禁止估算。
> v1.1 — 2026-04-01 | 老板直推级数据治理升级：市场交易数据与新闻源强隔离；sparkline/chartData 只允许真实历史序列；缺失处理改为回采或阻断发布；允许 metrics 改为可验证行情/财务指标组合。
> v1.0 — 2026-04-01 | 初始版本。基于原 Skill `data-collection-sop.md` v17.8 扩展：新增批次5（watchlist标的详情采集）和批次6（事件日历+风险矩阵）；新增sparkline采集规范（真实历史+降级估算）；新增metrics采集指南；数据完整性门禁扩展至16项。
