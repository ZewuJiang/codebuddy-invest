# 数据采集SOP（v17.8）

> **用途**：投资Agent每日策略简报第一阶段数据采集的完整操作规范。
> **核心原则**：数据完整性第一，精确到小数点后两位，严禁空位和模糊表述。**宁可多花10分钟搜索精确值，也绝不用模糊文字凑数。**

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
- 批次5: 上周市场周度数据（2-3次）
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
| 加密 | Google Finance `BTC-USD` | CoinGecko | — |
| 黄金/白银 | web_search + 金投网 | OilPrice.com | — |
| WTI原油 | web_fetch OilPrice.com | 金投网 | web_search |
| **布伦特原油（主指标）** | **web_fetch OilPrice.com** | **金投网** | **web_search** |
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
| 大宗期货Google不支持 | → OilPrice.com → 金投网 |
| CoinGecko异常 | → Google Finance `BTC-USD` |
| 港股数据获取困难 | → 东方财富/同花顺 → 智通财经 |
| 13F数据过季/缺失 | → WhaleWisdom → web_search |
| Yahoo Finance被屏蔽 | → Google Finance → StockAnalysis |
| **DXY直接获取困难** | → web_search "DXY dollar index close {date}" Trading Economics snippet → 金投网 DXY → Macrotrends.net DXY daily chart → Finlore.io → 使用前日值+趋势估算（**必须标注"估算"**） |
| PDF flag emoji乱码 | → 用文字替代（"A股"代替"🇨🇳 A股"） |
| PDF中文乱码 | → 检查font-family，STHeiti必须排首位 |

---

## 六、数据准确性防坑指南

| 陷阱 | 规避方法 |
|------|---------|
| **年份混淆** | 搜索结果确认年份为当前年（2026） |
| **盘中vs收盘** | 美股4AM(BJT)后用收盘数据，之前标注"盘中" |
| **涨跌幅符号** | 必须公式计算`(现价-前收)/前收*100%` |
| **夏令时错位** | 美国3月第二周日起夏令时 |
| **VIX方向误读** | VIX上涨=恐慌上升=🔴 |
| **空占位符遗留** | 撰写前执行完整性验证门禁 |
| **模糊表述替代精确值** | 全部使用精确值 |
| **Google Finance涨跌幅绝对值** | 通过前收和现价自行计算确认正负 |

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

> v17.8 — 2026-03-13 | 新增§七数据缺失强制处理流程 + §八成稿逐单元格扫描SOP（RULE FIVE配套），强化"宁迟勿糊"原则
> v18.3 — 2026-03-27 | 数据源优先级表新增"布伦特原油（主指标）"行，明确原油采集以布伦特为主、WTI为辅
