# 数据源优先级表（v1.2）

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
| **CNH（离岸人民币）历史序列** | **`ak.forex_hist_em("USDCNH")` 东方财富** | `CNY=X` yfinance（在岸替代，须标注"非离岸"） | 阻断发布 |
| **CNH（离岸人民币）实时价** | **新浪 `fx_susdcnh` hq接口** | `CNY=X` yfinance（在岸替代） | — |
| HY信用利差 | web_search "US high yield spread" | FRED `BAMLH0A0HYM2` | — |
| **北向资金** | **已永久停止实时披露（2024-08-19起）** | **改用「外资动向」代理（见下方说明）** | — |
| 日经225（历史序列） | yfinance `^N225` + 量级校验 | `ak.futures_foreign_hist("N225")` AkShare | 阻断发布 |
| KOSPI（历史序列） | yfinance `^KS11` + 量级校验（约1500-4500） | — | 标注"数据待核实" |
| 全球头条扫描 | Bloomberg + Reuters + WSJ | CNBC + MarketWatch | FT + Barron's |
| 财经新闻(中) | 华尔街见闻/第一财经/智通财经/格隆汇 | 金十数据/证券时报/财新 | 36Kr/晚点 |
| AI/科技动态 | The Information + TechCrunch | 36Kr + 晚点 | Semafor |
| 聪明钱/13F | SEC EDGAR | WhaleWisdom/HedgeFollow | web_search |
| 个股 metrics（方案C）| yfinance Ticker.info["trailingPE"]（PE） | StockAnalysis.com | "—"（不阻断） |
| 历史走势（sparkline） | yfinance/AkShare 真实历史序列 | 回采后重试 | 阻断发布（禁止估算） |

---

## 二、北向资金永久缺口说明

> **重要**：自 **2024年8月19日** 起，沪深交易所正式调整沪深港通信息披露机制，停止实时公布北向资金净买额，仅公布沪深港通交易总额（无方向）。此为**永久性政策调整**，不可逆，与 AkShare 接口状态无关。
>
> **正式替代方案**：使用「外资动向」代理指标，以港股（恒生指数 + 恒生科技指数）均涨跌幅判断外资偏好，由脚本 `calc_foreign_capital_proxy()` 函数自动计算：
> - 港股均涨 ≥ +1.5%  → 绿（外资回流信号）
> - 港股均涨 0~+1.5%  → 黄（外资情绪中性）
> - 港股均跌 < 0%     → 红（外资谨慎/流出信号）

---

## 三、降级路径

| 堵点 | 降级路径 |
|------|---------|
| Google Finance 403/超时 | → web_search → 东方财富/StockAnalysis |
| MarketWatch 401/反爬 | → web_search → 中文金融网站 |
| **sparkline 历史数据无法获取** | → **回到对应数据源重试；仍失败 → 阻断发布（禁止估算）** |
| chartData 30天无法获取 | → 回采对应数据源，不允许估算扩展 |
| **AkShare CNH 失败** | → **阻断发布，不允许硬编码估算** |
| metrics 数据缺失（PE） | → 标注"—"，不阻断主流程（PE 为辅助指标） |
| 大宗期货 Google 不支持 | → OilPrice.com → 金投网 |
| CoinGecko 异常 | → Google Finance `BTC-USD` |
| 港股数据获取困难 | → 东方财富/同花顺 → 智通财经 |
| 13F 数据过季 | → WhaleWisdom → web_search |
| DXY 直接获取困难 | → Trading Economics → 金投网 → Finlore.io → 前日值+估算 |
| 某标的全部数据失败 | → 替换为同板块备选标的（参见 stock-universe.md） |
| **日经225 yfinance 量级校验失败** | → **ak.futures_foreign_hist("N225") AkShare 备用通道** |
| **KOSPI 量级校验失败（>4500 或 <1500）** | → **标注"数据待核实"，不阻断整体流程** |
| 上传失败 | → JSON 文件保留，下次可手动重传 |

---

> v1.2 — 2026-04-01 | 六项数据质量深度治理：①CNH 改用真实离岸源 `ak.forex_hist_em`；②移除 CNY=X 批量下载，避免在岸/离岸混用；③北向资金永久缺口说明+外资动向替代方案；④日经/KOSPI 量级校验机制；⑤禁止 sparkline/CNH 估算降级；⑥个股 metrics 改为方案C（PE+规则化评级）。
> v1.1 — 2026-04-01 | 老板直推级数据治理升级：只允许直接行情源进入交易字段；禁止新闻页回填价格；禁止 sparkline/chartData 估算；允许 metrics 改为可验证指标集合。
> v1.0 — 2026-04-01 | 初始版本。基于原 Skill data-collection-sop.md 数据源优先级表 + App 版额外需求（sparkline/metrics/chartData）扩展。
