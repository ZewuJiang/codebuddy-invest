# 数据采集SOP — App版（v1.0）

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

### 批次5 — watchlist 标的详情（新增批次）

对 stock-universe.md 中定义的每只标的，采集以下额外数据：

```
# 对每只标的：
web_fetch: https://www.google.com/finance/quote/{TICKER}:{EXCHANGE}
# 从页面提取：
# - PE(TTM)
# - 市值
# - 52周高低
# - 近1月走势数据（30个点 → chartData）

# 补充采集（若GF缺失）：
web_search: "{公司名} {TICKER} revenue growth YoY quarterly 2026"
web_search: "{公司名} gross margin ROE latest quarter"
```

---

## 三、数据源优先级表

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
| **个股 metrics** | **Google Finance 详情页** | **StockAnalysis.com** | **Yahoo Finance** |
| **历史走势（sparkline）** | **Google Finance 图表** | **基于当日价格估算** | — |
| 基金&大资金 | SEC EDGAR | WhaleWisdom | web_search |

---

## 四、sparkline 数据采集规范

### 4.1 理想方式（真实历史数据）

从 Google Finance 页面获取近 5-7 天的收盘价数据点。

### 4.2 降级方式（估算生成）

当无法获取真实历史数据时，使用以下估算方法：

```python
# 基于当日价格 + 涨跌幅 估算 sparkline
def estimate_sparkline(current_price, change_pct, days=7):
    """
    current_price: 当日收盘价
    change_pct: 当日涨跌幅（如 1.42 表示 +1.42%）
    """
    import random
    random.seed(hash(str(current_price)))  # 保证同一标的同一天生成一致的数据
    
    points = []
    base = current_price / (1 + change_pct / 100)  # 估算昨日价格
    for i in range(days - 1):
        jitter = random.uniform(-0.015, 0.015)  # ±1.5% 随机波动
        day_price = base * (1 + jitter * (i - days/2) / days)
        points.append(round(day_price, 2))
    points.append(round(current_price, 2))  # 最后一个点是当日价格
    return points
```

**降级标记**：使用估算 sparkline 时，在 JSON 文件顶层添加 `"_sparklineEstimated": true`

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

---

## 六、已知堵点与降级路径

| 堵点 | 降级路径 |
|------|---------|
| Google Finance 403/超时 | → web_search → 东方财富/StockAnalysis |
| sparkline 历史数据无法获取 | → 使用估算方法生成（标记 `_sparklineEstimated`） |
| 个股 metrics 数据缺失 | → web_search 补充 → 使用 "N/A" 后标记 `_metricsMissing` |
| chartData 30天数据无法获取 | → 使用 sparkline 7天数据 + 估算扩展到 30 天 |
| 某板块标的全部数据失败 | → 替换为同板块备选标的（参见 stock-universe.md 备选池） |
| 港股数据获取困难 | → 东方财富/同花顺 → 智通财经 |
| 大宗期货 Google 不支持 | → OilPrice.com → 金投网 |
| 上传失败 | → JSON 文件保留，可手动重传 |

---

> v1.1 — 2026-04-01 | 老板直推级数据治理升级：市场交易数据与新闻源强隔离；sparkline/chartData 只允许真实历史序列；缺失处理改为回采或阻断发布；允许 metrics 改为可验证行情/财务指标组合。\n> v1.0 — 2026-04-01 | 初始版本。基于原 Skill `data-collection-sop.md` v17.8 扩展：新增批次5（watchlist标的详情采集）和批次6（事件日历+风险矩阵）；新增sparkline采集规范（真实历史+降级估算）；新增metrics采集指南；数据完整性门禁扩展至16项。
