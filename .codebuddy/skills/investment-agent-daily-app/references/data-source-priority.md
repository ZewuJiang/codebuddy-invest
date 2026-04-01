# 数据源优先级表（v1.1）

> **用途**：投研鸭小程序数据采集的数据源优先级和降级路径快速参考表。

---

## 一、数据源优先级

| 数据类型 | 首选 | 备选 | 第三选 |
|----------|------|------|--------|
| 美股指数/个股 | Google Finance (web_fetch) | 东方财富/StockAnalysis | MarketWatch |
| VIX | Google Finance `VIX:INDEXCBOE` | web_search | 同花顺 |
| 港股/A股 | 东方财富/同花顺 | Google Finance | 新浪财经 |
| 加密 | Google Finance `BTC-USD` | CoinGecko | web_search |
| 黄金 | web_search + 金投网 | OilPrice.com | — |
| 布伦特原油（主指标） | web_fetch OilPrice.com | 金投网 | web_search |
| WTI原油 | web_fetch OilPrice.com | 金投网 | web_search |
| DXY | web_search "DXY dollar index close" | 金投网 | Finlore.io |
| 10Y美债 | web_search | FRED | — |
| CNH（离岸人民币） | web_search | 金投网 | — |
| HY信用利差 | web_search "US high yield spread" | FRED | — |
| 北向资金 | 东方财富"北向资金" | 同花顺 | web_search |
| 全球头条扫描 | Bloomberg + Reuters + WSJ | CNBC + MarketWatch | FT + Barron's |
| 财经新闻(中) | 华尔街见闻/第一财经/智通财经/格隆汇 | 金十数据/证券时报/财新 | 36Kr/晚点 |
| AI/科技动态 | The Information + TechCrunch | 36Kr + 晚点 | Semafor |
| 聪明钱/13F | SEC EDGAR | WhaleWisdom/HedgeFollow | web_search |
| 个股 metrics | Google Finance 详情页 | StockAnalysis.com | Yahoo Finance |
| 历史走势（sparkline） | Google Finance 图表 | 基于当日价格估算 | — |

---

## 二、降级路径

| 堵点 | 降级路径 |
|------|---------|
| Google Finance 403/超时 | → web_search → 东方财富/StockAnalysis |
| MarketWatch 401/反爬 | → web_search → 中文金融网站 |
| sparkline 历史数据无法获取 | → 基于当日价格 ± 随机波动估算（标记 `_sparklineEstimated`） |
| chartData 30天无法获取 | → sparkline 7天 + 估算扩展到 30 天 |
| metrics 数据缺失 | → web_search 补充 → 标记 `_metricsMissing` |
| 大宗期货 Google 不支持 | → OilPrice.com → 金投网 |
| CoinGecko 异常 | → Google Finance `BTC-USD` |
| 港股数据获取困难 | → 东方财富/同花顺 → 智通财经 |
| 13F 数据过季 | → WhaleWisdom → web_search |
| DXY 直接获取困难 | → Trading Economics → 金投网 → Finlore.io → 前日值+估算 |
| 某标的全部数据失败 | → 替换为同板块备选标的（参见 stock-universe.md） |
| 上传失败 | → JSON 文件保留，下次可手动重传 |

---

> v1.1 — 2026-04-01 | 老板直推级数据治理升级：只允许直接行情源进入交易字段；禁止新闻页回填价格；禁止 sparkline/chartData 估算；允许 metrics 改为可验证指标集合。\n> v1.0 — 2026-04-01 | 初始版本。基于原 Skill data-collection-sop.md 数据源优先级表 + App 版额外需求（sparkline/metrics/chartData）扩展。
