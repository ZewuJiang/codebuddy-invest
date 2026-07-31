# 数据采集SOP（v19.4）

> **用途**：投资Agent每日策略简报第一阶段数据采集的完整操作规范。
> **核心原则**：数据完整性第一，精确到小数点后两位，严禁空位和模糊表述。**宁可多花10分钟搜索精确值，也绝不用模糊文字凑数。**
> **v19.4 跨期事件去重**：新增§九前一期日报预读流程，强制采集前预读前一期日报§1§3以支撑跨期事件去重判断。
> **v19.3 文档治理同步**：标题版本已与最近维护记录对齐，避免出现正文已更新但文档头仍停留旧版本的情况。

---

## 一、采集批次总览

| 批次 | 内容 | 搜索次数 | 数据源 |
|------|------|---------|--------|
| 0 | 全球财经媒体头条扫描（参照`media-watchlist.md`一级必扫7家） | 2-3次 | web_search |
| 0a | 深度媒体补充扫描（参照`media-watchlist.md`二级强化11家） | 1-2次 | web_search |
| 0b | AI产业链重大动态专项扫描（参照`ai-supply-chain-universe.md`） | 1-2次 | web_search |
| 1a | **M7个股精确数据（Google Finance批量）** | **7次web_fetch** | Google Finance |
| 1b | **美股指数+VIX精确数据** | **3-4次web_fetch** | Google Finance |
| 1c | **GICS 11板块ETF精确数据** | **11次web_fetch** | Google Finance |
| 1d | **当日焦点个股精确数据** | **2-5次web_fetch** | Google Finance |
| 2 | 亚太/港股数据 + 北向资金 | 2-3次 | 东方财富/同花顺/web_search |
| 3 | 大宗商品/汇率/加密/宏观 | 2-3次 | web_search/金投网 |
| 4 | 基金&大资金动向（参照`fund-universe.md`三梯队） | 3-5次 | web_search + SEC EDGAR |

**周一额外批次**：
- 批次5: 上周市场周度数据（2-3次）**⚠️ 含GICS ETF周涨跌%**：需分别获取11个ETF的上周五精确收盘价（GF fetch或历史K线），计算一周涨跌幅，用于周一特殊模板"周涨跌%"列；可利用GF页面"Compare to"区域一站获取多个ETF数据
- 批次6: 本周关键事件日历（2-3次）
- 批次7: 周末重大新闻（2-3次）

---

## 二、Google Finance批量采集模板（批次1a/1b/1c/1d）

```
# M7（批次1a）— 必须7个全部获取
web_fetch: https://www.google.com/finance/quote/NVDA:NASDAQ
web_fetch: https://www.google.com/finance/quote/AAPL:NASDAQ
web_fetch: https://www.google.com/finance/quote/MSFT:NASDAQ
web_fetch: https://www.google.com/finance/quote/GOOGL:NASDAQ
web_fetch: https://www.google.com/finance/quote/META:NASDAQ
web_fetch: https://www.google.com/finance/quote/AMZN:NASDAQ
web_fetch: https://www.google.com/finance/quote/TSLA:NASDAQ

# 指数+VIX（批次1b）— 必须4个全部获取
web_fetch: https://www.google.com/finance/quote/.INX:INDEXSP   (S&P 500)
web_fetch: https://www.google.com/finance/quote/.IXIC:INDEXNASDAQ (纳斯达克)
web_fetch: https://www.google.com/finance/quote/.DJI:INDEXDJX  (道琼斯)
web_fetch: https://www.google.com/finance/quote/VIX:INDEXCBOE   (VIX恐慌指数)
# ⚠️ VIX必须从Google Finance直接获取前收+现价，严禁从CBOE盘中数据反推！
# 教训(2026-03-18)：CBOE页面显示的%变化可能是盘中参考值，反推前收将导致致命错误

# GICS 11板块ETF（批次1c）— 必须11个全部获取
web_fetch: https://www.google.com/finance/quote/XLE:NYSEARCA   (能源)
web_fetch: https://www.google.com/finance/quote/XLK:NYSEARCA   (信息技术)
web_fetch: https://www.google.com/finance/quote/XLF:NYSEARCA   (金融)
web_fetch: https://www.google.com/finance/quote/XLV:NYSEARCA   (医疗保健)
web_fetch: https://www.google.com/finance/quote/XLY:NYSEARCA   (非必需消费)
web_fetch: https://www.google.com/finance/quote/XLC:NYSEARCA   (通信服务)
web_fetch: https://www.google.com/finance/quote/XLI:NYSEARCA   (工业)
web_fetch: https://www.google.com/finance/quote/XLB:NYSEARCA   (材料)
web_fetch: https://www.google.com/finance/quote/XLP:NYSEARCA   (必需消费)
web_fetch: https://www.google.com/finance/quote/XLU:NYSEARCA   (公用事业)
web_fetch: https://www.google.com/finance/quote/XLRE:NYSEARCA  (房地产)
```

---

## 三、数据源优先级表

> 📋 媒体追踪完整清单详见 `media-watchlist.md`

| 数据类型 | 首选 | 备选 | 第三选 |
|----------|------|------|--------|
| 美股指数/个股 | Google Finance (web_fetch) | 东方财富/StockAnalysis | MarketWatch |
| VIX | Google Finance `VIX:INDEXCBOE` | web_search | 同花顺 |
| 港股/A股 | 东方财富/同花顺 | Google Finance | 新浪财经 |
| 加密 | Google Finance `BTC-USD`（取"前收价"字段，标注"GF前收价UTC{日期}"）⚠️ | CoinGecko历史K线 | CoinMarketCap历史数据 |
| 黄金/白银 | web_search + 金投网 | OilPrice.com | — |
| **布伦特原油（主指标）** | **web_fetch OilPrice.com** | **金投网** | **web_search** |
| WTI原油（辅指标） | web_fetch OilPrice.com | 金投网 | web_search |
| DXY | web_search "DXY dollar index close {date}" Trading Economics | 金投网 DXY / Macrotrends.net | Finlore.io / 前日值+趋势估算（必须标注"估算"） |
| 10Y美债 | web_search | FRED | 每经 |
| **全球头条扫描** | **Bloomberg + Reuters + WSJ** | **CNBC + MarketWatch** | **FT + Barron's** |
| 财经新闻(中) | 华尔街见闻/第一财经/智通财经/格隆汇 | 金十数据/证券时报/财新 | 36Kr/晚点LatePost |
| 财经新闻(英) | Bloomberg/Reuters/WSJ/CNBC | FT/MarketWatch/Barron's | Nikkei Asia/Semafor |
| **AI/科技动态** | **The Information + TechCrunch** | **36Kr + 晚点LatePost** | **Semafor** |
| 聪明钱/13F | SEC EDGAR | WhaleWisdom/HedgeFollow | web_search |
| 基金策略师观点 | Bloomberg/CNBC/Reuters | 各基金官网/投资者信 | X(Twitter)/LinkedIn |
| 微信相关 | https://mp.weixin.qq.com/ | — | — |

---

## 四、第1.5阶段：数据完整性验证门禁（强制）

> **此阶段为强制性门禁，不通过则禁止进入第二阶段撰写。**

### 验证清单（每项必须打✅）

| # | 验证项 | 要求 | 缺失时操作 |
|---|--------|------|-----------|
| 1 | 三大指数收盘价+涨跌% | SPX/NDX/DJI各3个数值 | 回到批次1b补采 |
| 2 | M7全部7只收盘价+涨跌% | 14个数值（7×2） | 回到批次1a补采 |
| 3 | VIX精确值+涨跌% | 2个数值 | 回到批次1b补采 |
| 4 | GICS 11板块ETF收盘价+涨跌% | 22个数值（11×2） | 回到批次1c补采 |
| 5 | 焦点个股≥2只收盘价+涨跌% | ≥4个数值 | 回到批次1d补采 |
| 6 | 亚太4大指数最新价+涨跌% | 8个数值 | 回到批次2补采 |
| 7 | 大宗/汇率/加密6项 | 黄金/原油/BTC/DXY/10Y美债/CNH | 回到批次3补采 |
| 8 | 涨跌幅全部公式计算验证 | `(现价-前收)/前收*100%` | 重新计算 |

### 数据整理格式（内部工作表）

```
=== 数据完整性验证 ===
□ SPX: $_____ / ____% ✅/❌
□ NDX: $_____ / ____% ✅/❌
□ DJI: $_____ / ____% ✅/❌
□ NVDA: $_____ / ____% ✅/❌
□ AAPL: $_____ / ____% ✅/❌
□ MSFT: $_____ / ____% ✅/❌
□ GOOGL: $_____ / ____% ✅/❌
□ META: $_____ / ____% ✅/❌
□ AMZN: $_____ / ____% ✅/❌
□ TSLA: $_____ / ____% ✅/❌
□ VIX: _____ / ____% ✅/❌
□ XLE/XLK/XLF/XLV/XLY/XLC/XLI/XLB/XLP/XLU/XLRE: 全部✅/缺___
□ 焦点个股: [___] $___/___% [___] $___/___%
□ 恒生/恒科/上证/日经: 全部✅/缺___
□ 黄金/原油/BTC/DXY/10Y美债/CNH: 全部✅/缺___
→ 全部✅ → 进入第二阶段撰写
→ 任何❌ → 回到对应批次补采
```

---

## 五、已知堵点与降级路径

| 堵点 | 降级路径 |
|------|---------|
| Google Finance 403/超时 | → web_search → 东方财富/StockAnalysis |
| MarketWatch 401/反爬 | → web_search → 中文金融网站 |
| 大宗期货Google不支持 | → OilPrice.com → 金投网 → Investrade.com Market Review（一站获取指数+大宗+债券+外汇精确收盘，investrade.com/market-review/） |
| CoinGecko异常 | → Google Finance `BTC-USD` |
| 港股数据获取困难 | → 东方财富/同花顺 → 智通财经 |
| 13F数据过季/缺失 | → WhaleWisdom → web_search |
| Yahoo Finance被屏蔽 | → Google Finance → StockAnalysis |
| **DXY直接获取困难** | → web_search "DXY dollar index close {date}" Trading Economics snippet → 金投网 DXY → Macrotrends.net DXY daily chart → Finlore.io → 使用前日值+趋势估算（**必须标注"估算"**） |
| **布伦特历史K线5日内精确值** | → oilcrudeprice.com → **centralcharts.com/en/6567-brent-crude-oil/quotes**（提供完整OHLCV历史K线，已验证2026年数据质量高） → 金投网 |
| **亚太指数实时（日经/KOSPI/恒生/上证/深成/恒生科技）** | → **curl CNBC quote API**（`symbols=.HSI\|.N225\|.KS11\|.SSEC\|.SZI\|.HSTECH`，一站批量返回last/前收/涨跌幅/时间戳，20260721实战验证：一次获取恒生/日经/KOSPI/上证/深成/恒生科技6大指数，前收与前一日收盘完全自洽，是dhan 403时首选降级源） → **Google Finance 任一指数页面底部"相关指数"区**（一站显示日经/KOSPI/恒生/上证实时报价，dhan 403时的有效降级，20260720实战验证：NI225页面底部同时给出KOSPI 6,594.12/恒生24,562.24/上证3,825.24） → **dhan.co/indices/asian-indices/**（一站获取日经/KOSPI/恒生实时精确报价，约15分钟延迟，已验证2026年数据质量高，但间歇性403） → stockq.org → 各交易所官网 |
| **财报密集日/季报季批次0/4补充** | → **cannontrading.com/tools/daily-updates/**（Cannon Trading盘前简报，一站覆盖机构目标价/JOLTS等宏观/大宗/债券/外汇/技术水平/风险提示，URL格式：briefing-{mmdd}{yyyy}-readers-web.html，已连续2次财报日验证高效：4/16银行财报日/6/3 AVGO+CRWD财报日）|
| **内置web_fetch/web_search全不可用** | → **curl调用CNBC quote API**（`quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols=A\|B\|C&output=json`，支持`\|`批量、返回last/previous_day_closing/change_pct/时间戳）**+ Google News RSS**（`news.google.com/rss/search?q=`，一站获取多主题头条）。已于7/16财报日验证高效（前收与前一期收盘完全自洽）。**⚠️ 必须加浏览器 User-Agent 头**（`curl -H "User-Agent: Mozilla/5.0 ..."`），否则 Akamai edge 返回 `Access Denied`（20260727 周一实战验证：无 UA 返回 403 拦截，加 UA 后一次批量获取亚太6大指数+布伦特/WTI/黄金/DXY/US10Y/CNH/BTC 全部成功）|
| PDF flag emoji乱码 | → 用文字替代（"A股"代替"🇨🇳 A股"） |
| PDF中文乱码 | → 检查font-family，STHeiti必须排首位 |

---

## 六、数据准确性防坑指南

| 陷阱 | 规避方法 |
|------|---------|
| **年份混淆** | 搜索结果确认年份为当前年（2026） |
| **盘中vs收盘** | 美股4AM(TPE)后用收盘数据，之前标注"盘中" |
| **涨跌幅符号** | 必须公式计算`(现价-前收)/前收*100%` |
| **夏令时错位** | 美国3月第二周日起夏令时 |
| **VIX方向误读** | VIX上涨=恐慌上升=🔴 |
| **空占位符遗留** | 撰写前执行完整性验证门禁 |
| **模糊表述替代精确值** | 全部使用精确值 |
| **Google Finance涨跌幅绝对值** | 通过前收和现价自行计算确认正负 |
| **CNBC API VIX字段UNCH/prev=last异常** | CNBC quote API 对 `.VIX` 盘后可能返回 `change_pct=UNCH` 且 `previous_day_closing=last`（前收=现价），此为盘后快照特性。**VIX涨跌幅必须用前一期收盘手动公式复算 `(现价-前期收盘)/前期收盘×100%`，禁止直接采用API的UNCH/change_pct**（20260722实战：VIX从18.65→17.05实为-8.58%，API却返回UNCH，个股/其他指数无此问题） |

---

## 七、数据缺失强制处理流程（v17.8新增 — RULE FIVE配套）

> **核心原则**：任何标的的精确数据，宁可多花时间搜索多个来源，也**绝不用模糊文字代替**（如"收涨""上涨""+正"等）。

### 数据缺失时的强制搜索链

当某标的在首选数据源获取失败时，**必须按以下顺序逐一尝试**，至少尝试3个以上数据源：

```
Google Finance (web_fetch)
  → Yahoo Finance (web_search "TICKER Yahoo Finance close")
    → 新浪财经/东方财富 (web_search 中文搜索)
      → StockAnalysis.com (web_fetch)
        → MarketWatch (web_search)
          → web_search 多关键词组合（"TICKER March XX 2026 close exact price"）
```

### 穷尽搜索后仍无法获得精确值的处理

| 情况 | 处理方式 | 禁止的做法 |
|------|---------|-----------|
| 搜索6个源后仍无精确值 | **删除该行**（宁可少一行也不凑数） | ❌ 写"收涨""上涨""正""约$XX" |
| 仅获得收盘价无涨跌幅 | 通过web_search获取前收盘价，**手动公式计算** `(现-前)/前×100%` | ❌ 写"小幅上涨""略跌" |
| 仅获得涨跌幅无收盘价 | 继续搜索收盘价，两个值必须成对出现 | ❌ 只填一个值另一个空着 |
| 数据源间数值冲突 | 以Google Finance为准；若GF无数据，取出现频次最高的值 | ❌ 取平均值或写区间 |

### 真实案例（v17.8触发事件）

```
❌ 错误做法（v17.7出现的实际错误）：
| PLTR | 收涨 | +正 | 逆势上涨，国防AI概念受益 |

✅ 正确做法：
| PLTR | $153.50 | +1.25% | 逆势上涨，国防AI概念受益 |

处理方式：通过Google Finance获取精确收盘价$153.50和前收$151.60，
手动计算涨跌幅 ($153.50-$151.60)/$151.60×100% = +1.25%
```

---

## 八、成稿逐单元格扫描SOP（v17.8新增 — RULE FIVE配套）

> **时机**：报告写完后、输出最终版前的强制检查步骤。

### 扫描规则

对报告中每个数据表格，逐行逐单元格检查：

| 列名 | 允许的格式 | 禁止的内容 |
|------|-----------|-----------|
| 收盘价/最新价 | `$XXX.XX` 或 `XXX.XX`（非美元资产） | 任何中文描述（"收涨""跌""持平"等） |
| 涨跌幅/日涨跌% | `+X.XX%` 或 `-X.XX%` | 任何中文描述（"+正""-负""上涨""下跌""约"等） |
| 当前值（红绿灯） | 精确数值（如"4.23%""$95.33""99.30"） | 模糊表述（如"~24-26（估算）"） |
| 关键信号 | 中文简述≤15字 | ✅ 允许描述性文字 |

### 扫描方法

```
对§2/§3中所有表格：
  对每一行：
    检查"收盘价"列 → 是否$XXX.XX格式？
      → 否 → 立即搜索补全 → 不允许输出
    检查"涨跌幅"列 → 是否±X.XX%格式？
      → 否 → 立即搜索补全 → 不允许输出
对§5红绿灯表格：
  检查"当前值"列 → 是否精确数值？
    → 否 → 立即搜索补全 → 不允许输出
全部通过 → 允许进入三轮终审复核
```

---

## 九、前一期日报预读流程（v19.4新增 — RULE SEVEN配套）

> **核心原则**：同一事件在连续两期日报中**必须差异化处理**。为实现跨期去重，采集前必须先读取前一期日报，识别已详细展开的事件。

### 预读时机

- **位置**：第一阶段数据采集的**最前置步骤**（在batch 0之前执行）
- **强制性**：必须执行，跳过则违反致命错误#23

### 预读操作步骤

```
1. 确定前一期日报路径：
   - 标准日期：前一个交易日（如今天周三→读周二报告；今天周一→读上周五报告）
   - 路径格式：{报告输出目录}/投资Agent-每日策略简报-{YYYYMMDD}.md

2. 读取前一期日报§1和§3：
   - 定位§1"今日核心结论"的引用块（> 部分）
   - 定位§3"重点标的与行业分析"的展开卡片部分
   
3. 提取"已展开事件清单"：
   - 从§1事件链中提取核心事件
   - 从§3展开卡片中提取已详细分析的标的事件
   - 记录格式：[标的/事件] + [首次报道日期]

4. 如果前一期日报文件不存在：
   - 标注"前一期日报不存在，跳过预读"
   - 继续正常采集（不阻塞流程）
```

### 已展开事件清单示例

```
=== 前一期已展开事件清单（{YYYY-MM-DD}日报）===
□ AMD Q1'26财报超预期（首次报道：5/6日报）
□ 美联储维持利率不变+鹰派声明（首次报道：5/6日报）
□ NVDA公布$25B回购计划（首次报道：5/6日报）
→ 以上事件在本期§1/§3中禁止完整复述，仅引用价格数据+侧重市场定价反应
```

### 撰写阶段的去重判断

| 事件状态 | 本期§1处理方式 | 本期§3处理方式 |
|----------|--------------|--------------|
| 前一期已完整展开 | 禁止作为事件链核心重新展开；如涉及价格，一句话带过市场反应 | 数据表中正常填入当日收盘价/涨跌幅；展开卡片侧重"市场定价反应vs预期差" |
| 前一期仅在数据表中出现（未展开） | 可以完整展开（不算重复） | 可以完整展开 |
| 本期有实质性新增信息 | 仅展开新增部分，明确标注"延续性" | 仅展开新增部分 |

---

> v19.4 — 2026-05-07 | 新增§九前一期日报预读流程（RULE SEVEN配套），强制采集前预读前一期日报§1§3，提取已展开事件清单用于跨期去重判断
> v19.3 — 2026-04-01 | 文档治理同步：标题版本与最近维护记录正式对齐，避免版本头滞后造成误判
> v19.2 — 2026-04-01 | 一致性修正：将数据源优先级表中的原油顺序调整为"布伦特主指标在前、WTI辅指标在后"，与格式指南和模板保持一致
> v18.3 — 2026-03-27 | 数据源优先级表新增"布伦特原油（主指标）"行，明确原油采集以布伦特为主、WTI为辅
> v17.8 — 2026-03-13 | 新增§七数据缺失强制处理流程 + §八成稿逐单元格扫描SOP（RULE FIVE配套），强化"宁迟勿糊"原则
