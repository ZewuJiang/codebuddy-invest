# 数据源优先级表（v1.6）

> **用途**：投研鸭小程序数据采集的数据源优先级和降级路径快速参考表。
> **v1.6 核心升级（AkShare 替代 yfinance）**：sparkline/chartData 数据源从 yfinance（Yahoo 403 封禁）切换至 AkShare 新浪源（主）+ 东方财富源（fallback）。新增 A股指数和港股指数覆盖。

---

## ⚠️ 双轨体系总则（最高优先级）

```
交易数据轨（价格/涨跌/汇率/历史序列）
  → 只允许：直接行情平台 API/数据接口
  → 禁止：任何新闻媒体网站、财经资讯文章

观点数据轨（事件/分析/预测/评论/聪明钱动向）
  → 优先：权威财经媒体
  → 禁止：用媒体文章里的价格数字回填「交易数据轨」字段
```

**跨轨污染 = 致命错误#22，触发阻断发布**

---

## 零-A、web_search 结果可信域名白名单

> ⚠️ **核心问题**：`web_search` 的 snippet 摘要里经常含有价格数字，但 snippet 的来源可能是新闻媒体（违规）也可能是行情平台（合法）。AI 必须核实来源域名后再决定是否可用。

### 可信行情域名（价格数字可参考，但仍需 web_fetch 到页面核实）

| 域名 | 数据类型 | 可信度 |
|------|---------|--------|
| `google.com/finance` | 美股/ETF/加密 | ✅ 直接行情，最高可信 |
| `fred.stlouisfed.org` | 美债/宏观数据 | ✅ 美联储官方，最高可信 |
| `finance.yahoo.com` | 美股/ETF | ✅ 行情平台，可信 |
| `oilprice.com` | 原油/大宗 | ✅ 行情平台，可信 |
| `investing.com` | 综合行情 | ✅ 行情平台，可信 |
| `tradingeconomics.com` | 宏观/指数 | ✅ 行情平台，可信 |
| `coinmarketcap.com` / `coingecko.com` | 加密货币 | ✅ 行情平台，可信 |
| `eastmoney.com` (东方财富) | A股/港股 | ✅ 行情平台，可信 |
| `finance.sina.com.cn` | A股/外汇 | ✅ 行情接口，可信 |

### 禁止将价格数字用于交易字段的域名（只能用于观点轨）

| 域名 | 说明 |
|------|------|
| `bloomberg.com` / `reuters.com` | 新闻媒体 |
| `cnbc.com` / `marketwatch.com` | 新闻媒体 |
| `wsj.com` / `ft.com` | 新闻媒体 |
| `wallstreetcn.com` (华尔街见闻) | 新闻媒体 |
| `jin10.com` (金十数据) | 新闻转播 |
| `163.com` / `sina.com.cn` (新闻频道) | 新闻聚合 |
| 任何包含 `/news/` `/article/` `/story/` 路径的 URL | 新闻文章页面 |

### web_search 价格数字使用规则

```
web_search 返回了含价格数字的 snippet
  ↓
1. 检查来源域名是否在「可信行情域名」列表
   → 在列表 → 仍需 web_fetch 到实际行情页核实（不能只用 snippet）
   → 不在列表 / 是新闻域名 → 禁止使用，切换到行情源重新采集

2. 即使域名可信，价格数字也必须通过 web_fetch 到实际行情页面确认
   snippet 可能是缓存/过时数据，最终以 web_fetch 页面内容为准
```

---

## 一、交易数据轨 — 数据源优先级

> 所有 `price`、`change`、`sparkline`、`chartData`、`汇率` 字段必须来自本轨数据源。

| 数据类型 | 首选（必须先用） | 备选（首选失败时） | 第三选 | 失败处理 |
|---------|--------------|-----------------|--------|---------|
| 美股指数（SPX/IXIC/DJI） | `web_fetch` Google Finance `.INX/.IXIC/.DJI` | 东方财富/StockAnalysis (web_fetch) | MarketWatch (web_fetch) | 回采3次→阻断 |
| M7及美股个股 | `web_fetch` Google Finance `{TICKER}:NASDAQ/NYSE` | yfinance `download()` | StockAnalysis.com (web_fetch) | 回采→阻断 |
| VIX 恐慌指数 | `web_fetch` Google Finance `VIX:INDEXCBOE` | web_search（核实来源为 CBOE 官方）| 同花顺行情接口 | 回采→阻断 |
| GICS 11板块 ETF | `web_fetch` Google Finance `{XLE/XLK/...}:NYSEARCA` | yfinance `download()` | — | 回采→阻断 |
| 港股指数（恒生/恒科） | 东方财富行情接口 / 同花顺 | `web_fetch` Google Finance | 新浪财经行情接口 | 回采→阻断 |
| A股指数（上证/深证） | 东方财富行情接口 / AkShare `stock_zh_a_daily` | 同花顺 | 新浪财经行情接口 | 回采→阻断 |
| 日经225 | yfinance `^N225`（+ 量级校验 18000-55000）| `ak.futures_foreign_hist("N225")` | — | 量级异常→切备选→阻断 |
| KOSPI | yfinance `^KS11`（+ 量级校验 1500-4500）| — | 标注"数据待核实" | 量级异常→标注不阻断 |
| **黄金 XAU 价格** | **`web_fetch` OilPrice.com 或 金投网行情页** | **web_search（指定 `site:gold.org OR site:investing.com` 等行情平台）** | **Kitco 行情接口** | **阻断** |
| 布伦特原油 | `web_fetch` OilPrice.com | 金投网行情页 | web_search（行情平台来源）| 阻断 |
| WTI原油 | `web_fetch` OilPrice.com | 金投网行情页 | web_search（行情平台来源）| 阻断 |
| DXY 美元指数 | web_search（指定 ICE/Investing.com 等行情来源）| Trading Economics | 金投网 | 前日值+标注→不阻断 |
| **10Y美债收益率** | **`web_fetch` FRED `https://fred.stlouisfed.org/series/DGS10`** | **web_search（指定 treasury.gov 或 FRED 来源）** | — | **阻断** |
| **CNH 离岸人民币（实时价）** | **新浪 fx_susdcnh hq 接口 / AkShare `forex_spot_quote`** | **东方财富外汇行情页 (web_fetch)** | — | **阻断（禁止用7.xx训练数据）** |
| **sparkline/chartData 港股/A股（脚本跳过）** | **脚本 v3.0 已覆盖港股/A股（AkShare 新浪源+东方财富 fallback）** | — | 失败时保留 AI 估算值 | — |
| BTC/ETH 加密货币 | `web_fetch` Google Finance `BTC-USD` / `ETH-USD` | CoinGecko API | web_search（指定 CoinMarketCap 来源）| 阻断 |
| 历史走势 sparkline（7天）| **脚本 v3.0 自动补全（AkShare 新浪源+东方财富 fallback）**；VIX/DXY/10Y/CNH/BTC/ETH 为 AkShare 缺口，保留 AI 估算值 | — | — | — |
| 历史走势 chartData（30天）| **脚本 v3.0 自动补全（AkShare 新浪源+东方财富 fallback）**；VIX/DXY/10Y/CNH/BTC/ETH 为 AkShare 缺口，保留 AI 估算值 | — | — | — |
| 个股 PE(TTM) | yfinance `Ticker.info["trailingPE"]` | StockAnalysis.com (web_fetch) | 标注"—"（不阻断）| — |

---

## 二、观点数据轨 — 数据源优先级

> `coreEvent`、`coreJudgments`、`smartMoney`、`actions.reason`、`analysis`、`risks` 等文本字段来自本轨。

| 数据类型 | 首选 | 备选 | 第三选 |
|---------|------|------|--------|
| 全球头条/宏观事件 | Bloomberg + Reuters + WSJ | CNBC + MarketWatch | FT + Barron's |
| 财经新闻（中文） | 华尔街见闻 / 第一财经 / 智通财经 / 格隆汇 | 金十数据 / 证券时报 / 财新 | 36Kr / 晚点 |
| AI/科技产业动态 | The Information + TechCrunch | 36Kr + 晚点 | Semafor |
| 聪明钱/机构动向（13F）| SEC EDGAR | WhaleWisdom / HedgeFollow | web_search |
| 个股深度分析 | web_search + Google Finance 新闻标签 | 华尔街见闻个股页 | 东方财富研报 |

> ⚠️ **注意**：即使在观点数据轨的媒体文章中看到了价格数字，也**不允许**将其用于交易数据轨的字段，必须回到交易数据轨的数据源重新采集。

---

## 一-A、情绪与预测数据源优先级（Batch A 专用）

> **重要**：情绪与预测数据对应 `radar.fearGreed` 和 `radar.predictions[]` 字段，均为**可选字段（🔸）**。
> 所有情绪/预测数据源**失败均不阻断主流程**，获取失败时对应字段省略（不填 null）。

| 数据类型 | 首选 | 备选 | 第三选 | 失败处理 |
|----------|------|------|--------|---------|
| **CNN Fear & Greed Index** | `production.dataviz.cnn.com/index/fearandgreed/graphdata` (web_fetch, JSON接口) | web_search "CNN Fear Greed Index today" | — | **跳过，省略 fearGreed 字段** |
| **Polymarket 预测概率** | `clob.polymarket.com/markets?active=true&limit=20` (web_fetch) | web_search "Polymarket [主题] probability 2026" | — | **跳过该条目，predictions 可为空数组** |
| **Kalshi 预测概率** | `trading-api.kalshi.com/trade-api/v2/markets?limit=20&status=open` (web_fetch) | web_search "Kalshi prediction [主题]" | — | **跳过该条目** |
| **CME FedWatch 降息概率** | `cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html` (web_fetch) | web_search "CME FedWatch probability June 2026" | web_search "美联储降息概率 CME" | **跳过该条目** |

**CNN Fear & Greed 接口说明**：
- 接口直接返回 JSON，`fear_and_greed.score`（当前值）+ `fear_and_greed.rating`（等级标签）
- 历史对比数据在 `fear_and_greed_historical.data` 数组中，按时间倒序排列
- 昨日值：取 `data[0].y`；一周前：取 `data[4].y`；一月前：取 `data[19].y`（约）
- 无需 API Key，直接 web_fetch 即可访问

**Polymarket 接口说明**：
- 返回活跃市场列表，每个市场包含 `question`（标题）、`last_trade_price`（最近成交概率）、`volume_24h`（24h交易量）
- 优先选取 `volume_24h` 较高（关注度高）且与当日核心主题相关的问题
- `change24h` 需从 `last_trade_price` 与 `last_close_price` 差值推算，单位为百分比

**CME FedWatch 说明**：
- 降息概率 = P(25bp降息) + P(50bp降息)，不包含维持不变的概率
- 关注最近一次 FOMC 会议日期（通常是未来最近的会议）
- 若页面解析困难，web_search 通常能快速获取当日 FedWatch 最新数据

---

## 三、北向资金永久缺口说明

> **重要**：自 **2024年8月19日** 起，沪深交易所正式调整沪深港通信息披露机制，停止实时公布北向资金净买额，仅公布沪深港通交易总额（无方向）。此为**永久性政策调整**，不可逆，与 AkShare 接口状态无关。
>
> **正式替代方案**：使用「外资动向」代理指标，以港股（恒生指数 + 恒生科技指数）均涨跌幅判断外资偏好，由脚本 `calc_foreign_capital_proxy()` 函数自动计算：
> - 港股均涨 ≥ +1.5%  → 绿（外资回流信号）
> - 港股均涨 0~+1.5%  → 黄（外资情绪中性）
> - 港股均跌 < 0%     → 红（外资谨慎/流出信号）

---

## 四、降级路径

| 堵点 | 降级路径 |
|------|---------|
| Google Finance 403/超时 | → web_search → 东方财富/StockAnalysis（**行情页，非新闻页**）|
| MarketWatch 401/反爬 | → web_search → 中文金融行情网站 |
| **sparkline/chartData 的降级路径** | **脚本 v3.0（AkShare 新浪源→东方财富 fallback）失败 → AI 估算值兜底（非阻断），建议网络恢复后手动补跑脚本** |
| metrics 数据缺失（PE） | → 标注"—"，不阻断主流程（PE 为辅助指标）|
| 大宗期货 Google 不支持 | → OilPrice.com → 金投网（**行情页**，非新闻）|
| CoinGecko 异常 | → Google Finance `BTC-USD` |
| 港股数据获取困难 | → 东方财富/同花顺 → 智通财经行情接口 |
| 13F 数据过季 | → WhaleWisdom → web_search |
| DXY 直接获取困难 | → Trading Economics → 金投网 → Finlore.io → 前日值+估算（标注"前日值"）|
| 某标的全部数据失败 | → 替换为同板块备选标的（参见 stock-universe.md）|
| **日经225 yfinance 量级校验失败** | → **ak.futures_foreign_hist("N225") AkShare 备用通道** |
| **KOSPI 量级校验失败（>4500 或 <1500）** | → **标注"数据待核实"，不阻断整体流程** |
| 上传失败 | → JSON 文件保留，下次可手动重传 |
| **CNN Fear&Greed 接口失败** | → **web_search 获取当日值 → 仍失败 → 省略 fearGreed 字段（不阻断）** |
| **Polymarket API 失败** | → **web_search 定向搜索 → 仍失败 → 省略该条目（predictions 可为空数组，不阻断）** |
| **Kalshi API 失败** | → **web_search → 仍失败 → 省略该条目（不阻断）** |
| **CME FedWatch 页面失败** | → **web_search "CME FedWatch probability" → 仍失败 → 省略该条目（不阻断）** |
| **交易数据来源为新闻媒体（任何情况）** | → **RULE ZERO-A 违规，阻断发布，回到对应行情源重新采集** |

---

> v1.6 — 2026-04-05 17:37 | **AkShare 替代 yfinance**：sparkline/chartData 数据源从 yfinance（Yahoo 403 封禁）切换至 AkShare 新浪源（主）+ 东方财富源（fallback）；新增 A股指数+港股指数覆盖；港股/A股 sparkline 从「AI 手动采集」升级为「脚本 v3.0 自动补全」；AkShare 缺口（VIX/DXY/10Y/CNH/BTC/ETH）保留 AI 估算值；降级路径表 sparkline 行更新。
> v1.5 — 2026-04-03 20:00 | **方案A 双轨分工**：sparkline/chartData 字段从「AI 必须采集」改为「脚本 v2.0 自动补全」；数据源表 sparkline 行更新为脚本自动处理；港股/A股标注为 AI 手动补采；降级路径表 sparkline 行更新为「脚本失败→AI 估算兜底（非阻断）」；版本号升至 v1.5。
> v1.4 — 2026-04-03 10:55 | **双轨数据源体系**：将数据源表重构为「交易数据轨」与「观点数据轨」双轨体系；交易数据轨明确禁止使用任何新闻媒体来源，并为黄金/美债/CNH等历史问题数据类型单独强化备注；新增「跨轨污染禁止」总则；降级路径新增「交易数据来源为新闻媒体」兜底规则（任何情况均阻断）。
> v1.3 — 2026-04-02 | 新增一-A章"情绪与预测数据源优先级"（Batch A 专用）：定义 CNN Fear&Greed / Polymarket / Kalshi / CME FedWatch 四类数据源的优先级、接口说明和字段映射说明；降级路径表新增 4 条情绪数据降级路径（全部非阻断型）。
> v1.2 — 2026-04-01 | 六项数据质量深度治理：①CNH 改用真实离岸源 `ak.forex_hist_em`；②移除 CNY=X 批量下载，避免在岸/离岸混用；③北向资金永久缺口说明+外资动向替代方案；④日经/KOSPI 量级校验机制；⑤禁止 sparkline/CNH 估算降级；⑥个股 metrics 改为方案C（PE+规则化评级）。
> v1.1 — 2026-04-01 | 老板直推级数据治理升级：只允许直接行情源进入交易字段；禁止新闻页回填价格；禁止 sparkline/chartData 估算；允许 metrics 改为可验证指标集合。
> v1.0 — 2026-04-01 | 初始版本。基于原 Skill data-collection-sop.md 数据源优先级表 + App 版额外需求（sparkline/metrics/chartData）扩展。
