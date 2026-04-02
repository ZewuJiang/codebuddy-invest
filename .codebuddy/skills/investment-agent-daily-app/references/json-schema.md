# JSON Schema 完整字段规范（v1.9）

> **用途**：定义投研鸭小程序 4 个 JSON 文件的精确字段规范。每个字段都对应小程序前端组件的一个渲染点。
> **核心原则**：Schema 即契约。JSON 生成阶段必须逐字段对照本文件，不允许新增/缺失/改名字段。
> **字段类型约定**：`string` = 字符串，`number` = 数字（非字符串），`array` = 数组，`object` = 对象
> **必填标记**：⚠️ = 必填（不允许为空字符串/空数组/null）；🔸 = 可选（省略时前端 `wx:if` 跳过，不渲染对应模块）

---

## 一、briefing.json — 简报页

**对应页面**：`pages/briefing/briefing.wxml` + `briefing.js`
**涵盖模块**：时间状态栏（v1.3）、今日结论TAKEAWAY（v1.7）、今日重点事件（chain对象化 v1.7）、全球资产反应（note v1.7）、三大判断（含扩展字段v1.3）、行动建议（reason v1.7）、情绪仪表盘、聪明钱速览、风险提示、元数据（v1.3）

```jsonc
{
  "date": "2026-04-01",                    // ⚠️ string — YYYY-MM-DD 格式

  // ===== v1.3 新增：时间状态栏 =====
  "timeStatus": {                           // 🔸 object — 时间状态栏（可选，无则前端不渲染该模块）
    "bjt": "22:30",                         // 🔸 string — 北京时间 HH:MM（前端也可自行计算，此字段为快照参考）
    "est": "10:30",                         // 🔸 string — 美东时间 HH:MM
    // ⚠️ 注意：此字段由前端 format.js getMultiTimezone() 实时计算，JSON中的值仅为快照参考
    // ⚠️ 时区换算规则（手算验证用）：
    //   夏令时 EDT（3月第2个周日 ~ 11月第1个周日）：纽约 = 北京时间 - 12小时
    //   冬令时 EST（其余时段）                   ：纽约 = 北京时间 - 13小时
    //   示例：北京 20:06 → 纽约夏令时 08:06 EDT ✅（错误写法：20:06-8=12:06 ❌，勿用UTC直接换算）
    "marketStatus": "美股交易中",            // 🔸 string — 枚举：美股交易中 / 美股已收盘 / 盘前交易 / 盘后交易
    // ⚠️ 时区判断规则（北京时间 BJT = UTC+8，美东夏令时 EDT = UTC-4，冬令时 EST = UTC-5）：
    // BJT 21:30 ~ 次日04:00 → 美股交易中（EDT 9:30~16:00）
    // BJT 04:00 ~ 06:00    → 盘后交易（EDT 16:00~18:00）
    // BJT 13:30 ~ 21:30    → 盘前交易（EDT 22:00~9:30 次日）
    // 其余时段             → 美股已收盘
    // 数据标注规则：globalReaction 中美股数据若非收盘值，必须在 dataTime 中注明「盘前」或「盘后」
    "refreshInterval": "每日更新"            // 🔸 string — 数据刷新频率说明
  },

  // ===== v1.7 新增：今日核心结论 TAKEAWAY =====
  "takeaway": "string",                     // 🔸 string — 30-80字，一句话宏观结论。要求：有立场、有行动方向、有条件（"如果X则Y"）；禁止：空洞废话、重复coreEvent原文。
  // 正确示例："停火预期彻底破裂叠加关税一周年情绪共振，今日以防御为主——能源小仓对冲、科技不追跌、等待VIX回落至22以下再重新入场。"
  // 错误示例（禁止）："今日市场受多重因素影响，投资者需保持谨慎。"（无立场、无行动方向）

  "coreEvent": {                            // ⚠️ object — 核心事件
    "title": "string",                      // ⚠️ 30-80字，纯文本，禁止 markdown/emoji
    // ===== v1.7 升级：chain 从 string[] 改为 object[] =====
    "chain": [                              // ⚠️ array — 今日重点事件链，3-6条
      {
        "title": "string",                  // ⚠️ string — ≤20字结论式标题（核心观点/判断，而非事实描述）
        // 正确示例："停战信号发出即被否认，战争溢价回归" / "WTI油价暴涨6%，通胀担忧重燃"
        // 错误示例（禁止）："特朗普宣布停火" / "油价上涨"（事实描述，非结论）
        "brief": "string",                  // 🔸 string — 15-40字背景/机制说明，回答"为什么/怎么影响市场"
        // 正确示例："霍尔木兹封锁风险溢价重定价，通胀预期抬头，联储降息空间进一步收窄"
        "source": "string",                 // 🔸 string — 来源媒体名（如 Reuters / Bloomberg / AP News），有则显示，无则不渲染
        // ⚠️ 来源与链接必须一一对应，严禁跨媒体伪造链接：
        // 正确：source="Reuters" + url="https://reuters.com/..."（路透的文章配路透链接）
        // 错误（禁止）：source="Bloomberg" + url="https://yahoo.com/..."（彭博内容配雅虎链接）
        // ⚠️ 付费墙媒体（Bloomberg / FT / WSJ）无公开链接时：只填 source，不填 url
        // 前端对无 url 的来源自动显示为灰色不可点文字（chain-link-no-url 样式）
        "url": "string"                     // 🔸 string — 完整 https 公开可访问链接（中国大陆可访问优先）；付费墙内容不填此字段
      }
    ]
  },

  "globalReaction": [                       // ⚠️ array — 全球资产反应，5-6项
    {
      "name": "string",                     // ⚠️ 资产名（标普500/纳斯达克/恒生科技/黄金/10Y美债/BTC）
      "value": "string",                    // ⚠️ 涨跌幅或绝对值（如 "+0.87%" 或 "4.23%"）
      "direction": "string",                // ⚠️ 枚举：up / down / flat
      "note": "string"                      // 🔸 string — ≤15字，极简解读（说明为什么涨跌），有则显示灰色小字
      // 正确示例："停战预期打压" / "科技股被点名承压" / "通胀预期推升收益率"
    }
  ],

  "coreJudgments": [                        // ⚠️ array — 三大判断，精确3条
    {
      "title": "string",                    // ⚠️ 判断标题，10-30字
      "confidence": 85,                     // ⚠️ number — 置信度百分比，30-95
      "logic": "string",                    // ⚠️ 推理逻辑链，20-60字
      // ===== v1.9 升级：logic 字段格式规范 =====
      // 【强制格式】：短句 + 箭头符号（→）串联，三段式结构：触发原因 → 传导路径 → 核心结论
      // 正确示例："停火信号遭否认，IRGC升级威胁美科技设施 → 每多一周冲突油价+$2~4（高盛模型）→ 霍尔木兹持续封锁，油价中枢系统性上移"
      // 正确示例："关税一年，供应链脱钩成本固化于企业利润表 → 能源冲击叠加通胀粘性 → 高利率周期延长，贸易回旋空间大幅收窄"
      // 错误示例（禁止）："停火信号发出即被否认，IRGC升级威胁美国科技设施，谈判进程从乐观转入拉锯阶段；高盛模型显示每增加一周冲突布伦特将额外上涨2-4美元，霍尔木兹封锁持续则油价中枢将上移"（段落散文，逻辑链隐藏在长句中，大老板扫读成本高）
      // 【禁止】：段落式散文、分号连接的长句、bullet点列举（前端不渲染bullet，直接显示原文）
      // 【字数要求】：每段短句 ≤15字，整条 logic 含箭头符号控制在 50字以内
      // 【前端渲染说明】：logic 字段对应 briefing.wxml 的 .logic-text，无图标前缀，文字直接顶格；箭头（→）自带方向感，无需额外修饰符号
      // ===== v1.3 新增：判断扩展字段（全部可选） =====
      "keyActor": "Jensen Huang / Satya Nadella",  // 🔸 string — 关键决策者姓名（可选）
      "references": [                         // 🔸 array — 参考信息源，1-3个（可选）
        // ⚡ 支持两种格式（向后兼容）：
        // 旧格式 string："Bloomberg" → 前端降级为仅显示名称，不可展开
        // 新格式 object（推荐）：
        {
          "name": "Bloomberg",                // 🔸 string — 来源名称
          "summary": "分析师认为AI资本开支将继续超预期增长",  // 🔸 string — 信息摘要，20-60字
          "url": "https://bloomberg.com/..."   // 🔸 string — 来源链接（可选，无则不显示链接图标）
        }
      ],
      "probability": "高可能性",             // 🔸 string — 枚举：高可能性 / 中可能性 / 低可能性（可选）
      "trend": "上升"                        // 🔸 string — 枚举：上升 / 下降 / 稳定（可选）
    }
  ],

  "actions": {                              // ⚠️ object — 行动建议
    "today": [                              // ⚠️ array — 今日建议，1-3条
      {
        "type": "string",                   // ⚠️ 枚举（具体操作动词）：hold（持有）/ add（加仓）/ reduce（减仓）/ buy（买入）/ sell（卖出）/ watch（关注）/ hedge（对冲）/ stoploss（止损）
        // ⚠️ 禁止使用 bullish / bearish — 这是方向判断，不是具体操作指令
        // 正确示例："hold"（持有现有科技仓位）/ "hedge"（布局能源对冲）/ "watch"（关注黄金4600买点）
        // 错误示例（禁止）："bullish"（看涨）/ "bearish"（看跌）— 语义模糊，无法指导操作
        "content": "string",                // ⚠️ 具体可执行建议，含标的+条件+幅度，纯文本
        // 正确示例："持有现有科技仓位无需操作，等VIX回落至22以下、伊朗谈判信号明朗后再择机增配NVDA/AVGO"
        // 正确示例："能源板块（XLE）可小仓布局作地缘对冲，油价站稳105美元上方则动能延续"
        "reason": "string"                  // 🔸 string — ≤40字，说明建议理由/数据锚点，有则显示灰色小字
        // 正确示例："地缘恐慌性下跌中加仓风险过高，VIX已急升至27上方，底部尚未确认"
      }
    ],
    "week": [                               // array — 本周建议，0-3条（可为空数组）
      {
        "type": "string",                   // 同今日 type 枚举规则
        "content": "string",
        "reason": "string"                  // 🔸 同今日建议
      }
    ]
  },

  "sentimentScore": 62,                     // ⚠️ number — 0-100 情绪分数
  "sentimentLabel": "偏贪婪",                // ⚠️ string — 枚举：极度恐惧/偏恐惧/中性/偏贪婪/贪婪/极度贪婪
  "marketSummaryPoints": [                  // ⚠️ array — 市场情绪 bullet point，3-5条，取代旧版 marketSummary 字符串
    "string"                                // ⚠️ 每条15-40字，独立一个观察点，条条有信息量
    // 写作规则：
    // - 第1条：亚太/美股盘面概述（已收盘的行情）
    // - 第2条：主要驱动力/事件共振说明
    // - 第3条：异常背离或关键信号（如黄金vs油价背离）
    // - 第4条（可选）：核心变量/下一催化剂
    // 禁止：重复 coreEvent/globalReaction 中已有的具体涨跌幅数字
    // 禁止：一段话大段文字（用 bullet 而非散文）
    // 旧版兼容：若 marketSummaryPoints 缺失，前端自动用 marketSummary 字符串按句号/分号拆分兜底
  ],

  "smartMoney": [                           // ⚠️ array — 聪明钱速览，2-4条
    {
      "source": "string",                   // ⚠️ 机构名（如 "桥水基金"/"北向资金"）
      "action": "string",                   // ⚠️ 具体操作（如 "增持中国ETF约$2.3亿"）
      "signal": "string"                    // ⚠️ 枚举：bullish / bearish / neutral
    }
  ],

  "riskNote": "string",                     // ⚠️ 30-100字风险提示，纯文本，禁止表格语法
  "dataTime": "2026-04-01 09:00 BJT",       // ⚠️ string — 数据截止时间

  // ===== v1.3 新增：元数据 =====
  "_meta": {                                // 🔸 object — 元数据（可选，无则前端不显示来源标签）
    "sourceType": "heavy_analysis",         // 🔸 string — 枚举：heavy_analysis / realtime_quote / breaking_news
    "generatedAt": "2026-04-01T09:00:00+08:00",  // 🔸 string — ISO 8601 生成时间
    "skillVersion": "v1.7"                  // 🔸 string — 生产此数据的 Skill 版本号
  }
}
```

**组件对齐清单**：

| 小程序组件 | JSON 字段 | 数组长度要求 | 特殊规则 |
|---|---|---|---|
| 时间状态栏（v1.3） | `timeStatus` | — | 可选模块，前端也可自行计算时区 |
| 今日核心结论（v1.7）| `takeaway` | — | 可选；30-80字，有立场有行动方向 |
| 核心事件标题 | `coreEvent.title` | — | 纯文本，无 emoji |
| 事件链卡片（v1.7） | `coreEvent.chain[]` | 3-6条 | **对象数组**：title（必填）+ brief（可选）+ source（可选）+ url（可选，有则可点击） |
| 全球资产 6 格卡片（v1.7） | `globalReaction[]` | 5-6项 | 固定6项；新增可选 `note` 字段（≤15字解读） |
| 核心判断×3 + 置信度条 | `coreJudgments[]` | 精确3条 | confidence 必须是 number |
| 判断扩展：决策者/参考源/概率/趋势（v1.3→v1.3.1） | `coreJudgments[].keyActor/references/probability/trend` | — | 全部可选；references 支持 string[] 旧格式和 object[] 新格式（含 name/summary/url） |
| 行动建议 tag+content（v1.8） | `actions.today/week` | today 1-3, week 0-3 | type 枚举：hold/add/reduce/buy/sell/watch/hedge/stoploss；**禁止 bullish/bearish**；新增可选 `reason` 字段（≤40字） |
| 情绪仪表盘圆环 | `sentimentScore` + `sentimentLabel` | — | score 是 number |
| 市场情绪 bullet list（v1.8） | `marketSummaryPoints[]` | 3-5条 | 每条15-40字独立观察点；旧版 `marketSummary` 字符串兼容（前端自动拆分） |
| 聪明钱卡片 | `smartMoney[]` | 2-4条 | signal 枚举严格 |
| 风险提示底部 | `riskNote` | — | 纯文本 |
| 数据状态栏（v1.3） | `_meta` | — | 可选，控制底栏来源标签和版本号显示 |

---

## 二、markets.json — 市场页

**对应页面**：`pages/markets/markets.wxml` + `markets.js`
**涵盖模块**：5个Tab（美股/M7/亚太/大宗/加密）+ GICS热力图

```jsonc
{
  "date": "2026-04-01",                    // ⚠️ string

  "usMarkets": [                            // ⚠️ array — 精确4项
    {
      "name": "标普500",                    // ⚠️ string
      "price": "5,254.35",                  // ⚠️ string — 千分位格式
      "change": -0.39,                      // ⚠️ number — 涨跌幅百分比
      "changeLabel": "大盘指数",             // ⚠️ string — 枚举：大盘指数/科技指数/蓝筹指数/恐慌指标
      "sparkline": [5180, 5195, 5220, 5210, 5235, 5248, 5254] // ⚠️ number[] — 7天
    }
  ],
  // usMarkets 精确4项顺序：标普500 / 纳斯达克 / 道琼斯 / VIX
  // changeLabel 对应：大盘指数 / 科技指数 / 蓝筹指数 / 恐慌指标

  "usInsight": "科技股领涨带动纳指创两周新高，AI板块延续强势，但VIX降至13下方暗示短期波动率压缩",  // ⚠️ string — 美股板块一句话洞察，30-80字，纯文本

  "m7": [                                   // ⚠️ array — 精确7项
    {
      "name": "苹果 AAPL",                  // ⚠️ string — 格式："中文名 代码"
      "price": "$192.53",                   // ⚠️ string
      "change": 1.42,                       // ⚠️ number
      "symbol": "AAPL",                     // ⚠️ string
      "sparkline": [188, 190, 189, 191, 193, 192, 192] // ⚠️ number[] — 7天
    }
  ],
  // m7 精确7项顺序：AAPL / MSFT / NVDA / GOOGL / AMZN / META / TSLA

  "m7Insight": "M7分化加剧，NVDA独涨4.2%领跑受益AI资本开支超预期，TSLA连跌三日拖累整体",  // ⚠️ string — M7板块一句话洞察，30-80字，纯文本

  "asiaMarkets": [                          // ⚠️ array — 4-6项
    {
      "name": "上证指数",                    // ⚠️ string
      "price": "3,041.17",                  // ⚠️ string
      "change": 0.24,                       // ⚠️ number
      "sparkline": [3020, 3025, 3030, 3028, 3035, 3040, 3041] // ⚠️ number[]
    }
  ],
  // asiaMarkets 推荐6项：上证/深证/恒生指数/恒生科技/日经225/KOSPI

  "asiaInsight": "港股微涨结束3月惨淡表现，恒生科技受南向资金支撑领涨2.15%，日经受日元走弱提振",  // ⚠️ string — 亚太板块一句话洞察，30-80字，纯文本

  "commodities": [                          // ⚠️ array — 精确6项
    {
      "name": "黄金 XAU",                   // ⚠️ string
      "price": "$2,213.40",                 // ⚠️ string
      "change": 1.09,                       // ⚠️ number
      "sparkline": [2190, 2195, 2200, 2205, 2210, 2215, 2213] // ⚠️ number[]
    }
  ],
  // commodities 精确6项：黄金/布伦特原油/WTI原油/美元指数DXY/10Y美债/离岸人民币CNH

  "commodityInsight": "黄金突破2210美元创历史新高，避险需求叠加央行购金支撑，美元走弱助推大宗普涨",  // ⚠️ string — 大宗板块一句话洞察，30-80字，纯文本

  "cryptos": [                              // ⚠️ array — 1-3项
    {
      "name": "比特币 BTC",                  // ⚠️ string
      "price": "$70,215",                   // ⚠️ string
      "change": 1.95,                       // ⚠️ number
      "sparkline": [68000, 68500, 69000, 69200, 70000, 70100, 70215] // ⚠️ number[]
    }
  ],
  // cryptos 推荐：BTC / ETH(可选) / SOL(可选)

  "cryptoInsight": "BTC站上7万美元关口，ETF持续净流入叠加减半预期升温，SOL领涨山寨币",  // ⚠️ string — 加密板块一句话洞察，30-80字，纯文本

  "gics": [                                 // ⚠️ array — 精确11项，按涨跌幅降序
    {
      "name": "信息技术 XLK",                // ⚠️ string — 格式："中文名 ETF代码"
      "change": 1.82,                       // ⚠️ number
      "etf": "XLK"                          // ⚠️ string
    }
  ],
  // gics 精确11项：XLK/XLC/XLY/XLI/XLF/XLV/XLB/XLP/XLU/XLRE/XLE

  "gicsInsight": "板块轮动明显，科技/通信领涨反映AI主线延续，能源/房地产承压显示市场偏好成长股"  // ⚠️ string — GICS板块一句话洞察，30-80字，纯文本
}
```

**板块 Insight 规范（v1.3.2 新增）**：

| 字段 | 类型 | 必填 | 长度 | 内容要求 |
|------|------|------|------|---------|
| `usInsight` | string | ⚠️ | 30-80字 | 美股板块核心驱动力+关键数字+信号判断，禁止泛泛"市场上涨"，必须说清为什么涨、谁领涨、后续信号 |
| `m7Insight` | string | ⚠️ | 30-80字 | M7整体表现+分化情况+领涨/拖累个股+驱动因素 |
| `asiaInsight` | string | ⚠️ | 30-80字 | 亚太市场格局+港股/A股/日韩分化+核心驱动（政策/资金/外围） |
| `commodityInsight` | string | ⚠️ | 30-80字 | 大宗核心品种走势+美元/债券联动+地缘/宏观驱动 |
| `cryptoInsight` | string | ⚠️ | 30-80字 | BTC走势+ETF资金流向+链上信号/监管动态 |
| `gicsInsight` | string | ⚠️ | 30-80字 | 板块轮动方向+领涨/领跌板块+资金偏好风格 |

> **v1.3.2 变更**：原 `usMarkets[0].note` 字段已迁移为独立的 `usInsight` 字段，其他5个板块新增对应 Insight。所有 Insight 为必填（⚠️），格式为纯文本，禁止 markdown/emoji。前端向后兼容：有 `usInsight` 优先使用，否则降级到 `usMarkets[0].note`。

**sparkline 生成规则**：
- 7 个数据点代表近 7 个交易日价格
- 数据来源优先级：Google Finance 历史数据 > web_search 历史数据 > 基于当日价格 ± 估算
- 估算公式（降级用）：`[base * (1 + rand*0.01*i) for i in range(-6, 1)]`
- 估算时必须标记文件级 `_sparklineEstimated: true`

---

## 三、watchlist.json — 标的页

**对应页面**：`pages/watchlist/watchlist.wxml` + `stock-card.wxml`
**涵盖模块**：板块 Tab + 板块概述 + 股票卡片 + 展开详情

```jsonc
{
  "date": "2026-04-01",                    // ⚠️ string

  "sectors": [                              // ⚠️ array — 7个板块
    {
      "id": "ai",                           // ⚠️ string — 枚举：ai/semi/internet/energy/consumer/pharma/finance
      "name": "AI算力",                      // ⚠️ string
      "trend": "up",                        // ⚠️ string — 枚举：up / down / hold
      "summary": "string"                   // ⚠️ 板块概述，2-3句话，纯文本
    }
  ],

  "stocks": {                               // ⚠️ object — 按板块 ID 分组
    "ai": [                                 // ⚠️ array — 每板块至少2只
      {
        "name": "英伟达",                    // ⚠️ string — 中文名
        "symbol": "NVDA",                   // ⚠️ string — 股票代码
        "change": 4.2,                      // ⚠️ number — 涨跌幅百分比
        "price": "$878.36",                 // ⚠️ string — 当前价格
        "tags": ["AI芯片龙头", "GTC大会催化"], // ⚠️ string[] — 2个标签
        "reason": "string",                 // ⚠️ 一句话推荐逻辑（20-60字）
        "analysis": "string",              // ⚠️ AI分析摘要（2-3段，100-300字，纯文本，用\n分段）
        "metrics": [                        // ⚠️ array — 精确6项指标
          { "label": "PE(TTM)", "value": "72.5x" },
          { "label": "市值", "value": "$2.3T" },
          { "label": "营收增速", "value": "+265%" },
          { "label": "毛利率", "value": "76.0%" },
          { "label": "ROE", "value": "91.5%" },
          { "label": "评级", "value": "⭐⭐⭐⭐⭐" }
        ],
        "risks": [                          // ⚠️ string[] — 2-3条风险
          "估值偏高，PE超70x",
          "AMD MI300X竞争加剧"
        ],
        "sparkline": [850, 855, 860, 870, 868, 875, 878],  // ⚠️ number[] — 7天走势
        "chartData": [830, 835, 840, ...]   // ⚠️ number[] — 30天走势（展开详情用）
      }
    ],
    "semi": [...],                          // ⚠️ 至少2只
    "internet": [...],                      // ⚠️ 至少2只
    "energy": [...],                        // ⚠️ 至少2只
    "consumer": [...],                      // ⚠️ 至少2只
    "pharma": [...],                        // ⚠️ 至少2只
    "finance": [...]                        // ⚠️ 至少2只
  }
}
```

**板块分类规则**（详见 [stock-universe.md](stock-universe.md)）：

| 板块 ID | 名称 | 代表标的 | 最低数量 |
|---------|------|---------|---------|
| `ai` | AI算力 | NVDA/AVGO/TSM/MSFT | 3-4只 |
| `semi` | 半导体 | 000660.KS/ASML/AMD | 2-3只 |
| `internet` | 互联网平台 | 0700.HK/PDD/3690.HK | 2-3只 |
| `energy` | 新能源 | 300750.SZ/002594.SZ | 2只 |
| `consumer` | 消费 | 9992.HK/COST | 2只 |
| `pharma` | 医药 | NVO/LLY | 2只 |
| `finance` | 金融 | BRK.B/JPM | 2只 |

**metrics 6项标准（方案C — v1.2更新）**：

| # | label | 数据来源 | 格式示例 | 说明 |
|---|-------|---------|---------|------|
| 1 | 最新价 | yfinance/AkShare 实时价 | "$174.40" | 自动计算 |
| 2 | 单日涨跌 | 当日 close vs prev close | "+5.59%" | 自动计算 |
| 3 | 7日涨跌 | last7[0] → last7[-1] | "-0.71%" | 自动计算 |
| 4 | 30日涨跌 | last30[0] → last30[-1] | "-7.22%" | 自动计算 |
| 5 | PE(TTM) | `yfinance Ticker.info["trailingPE"]` | "53.4x"（无数据则"—"） | 辅助指标，缺失不阻断 |
| 6 | 综合评级 | `calc_star_rating()` 规则函数（基于30日涨跌） | "⭐⭐⭐⭐" | 规则化自动计算，可重现 |

> **评级规则**（`calc_star_rating(change, pct_30d)`）：
> - ⭐⭐⭐⭐⭐：30日涨超+15% 且 单日为正
> - ⭐⭐⭐⭐  ：30日涨+5%~+15%，或单日涨超+3%
> - ⭐⭐⭐    ：30日在-5%~+5%（震荡整理）
> - ⭐⭐      ：30日跌-5%~-15%
> - ⭐        ：30日跌超-15%（深度回调）

---

## 四、radar.json — 雷达页

**对应页面**：`pages/radar/radar.wxml` + `radar.js`
**涵盖模块**：市场情绪指数（v1.3）、预测市场（v1.3）、红绿灯信号、风险评分、监控阈值、风险预警、事件日历、异动监测、聪明钱三梯队、元数据（v1.3）

```jsonc
{
  "date": "2026-04-01",                    // ⚠️ string

  // ===== v1.3 新增：Fear & Greed 情绪指数 =====
  "fearGreed": {                            // 🔸 object — CNN Fear & Greed 指数（可选，无则前端不渲染该卡片）
    "value": 42,                            // 🔸 number — 0-100 当前值
    "label": "Fear",                        // 🔸 string — 枚举：Extreme Fear / Fear / Neutral / Greed / Extreme Greed
    "previousClose": 38,                    // 🔸 number — 昨日收盘值
    "oneWeekAgo": 55,                       // 🔸 number — 一周前值
    "oneMonthAgo": 61                       // 🔸 number — 一月前值
  },

  // ===== v1.3 新增：预测市场 =====
  "predictions": [                          // 🔸 array — 预测市场概率，2-4条（可选，无则前端不渲染该卡片）
    {
      "title": "美联储6月降息?",             // 🔸 string — 预测问题
      "source": "Polymarket",               // 🔸 string — 数据来源（Polymarket / Kalshi / CME FedWatch）
      "probability": 72,                    // 🔸 number — 概率百分比 0-100
      "trend": "up",                        // 🔸 string — 枚举：up / down / stable
      "change24h": 5                        // 🔸 number — 24小时概率变化（正数上升，负数下降）
    }
  ],

  "trafficLights": [                        // ⚠️ array — 精确7项
    {
      "name": "VIX波动率",                   // ⚠️ string
      "value": "13.0",                      // ⚠️ string — 精确数值
      "status": "green",                    // ⚠️ string — 枚举：green / yellow / red
      "threshold": "<18绿 / 18-25黄 / >25红" // ⚠️ string — 阈值说明
    }
  ],
  // trafficLights 精确7项顺序：
  // VIX波动率 / 10Y美债收益率 / 布伦特原油 / 美元指数DXY / HY信用利差 / 外资动向（v1.2替代北向资金）/ 离岸人民币CNH

  "riskScore": 38,                          // ⚠️ number — 0-100
  "riskLevel": "medium",                    // ⚠️ string — 枚举：low / medium / high
  "riskAdvice": "string",                   // ⚠️ 仓位建议文本

  "monitorTable": [                         // ⚠️ array — 5-6条触发条件
    {
      "condition": "VIX突破25",              // ⚠️ string — 触发条件
      "action": "将股票仓位降至5成以下"       // ⚠️ string — 应对动作
    }
  ],

  "riskAlerts": [                           // ⚠️ array — 2-3条风险预警
    {
      "title": "非农数据超预期风险",          // ⚠️ string
      "probability": "35%",                 // ⚠️ string
      "impact": "高",                        // ⚠️ string — 高/中/低
      "response": "string",                 // ⚠️ string — 应对建议
      "level": "high"                       // ⚠️ string — 枚举：high / medium / low
    }
  ],

  "events": [                               // ⚠️ array — 3-5条本周事件
    {
      "date": "周三",                        // ⚠️ string — 如 "周一"/"周三"/"04/03"
      "title": "美联储会议纪要",              // ⚠️ string
      "impact": "high"                      // ⚠️ string — 枚举：high / medium / low
    }
  ],

  "alerts": [                               // ⚠️ array — 2-4条异动监测
    {
      "level": "danger",                    // ⚠️ string — 枚举：danger / warning / info
      "text": "string",                     // ⚠️ 异动描述
      "time": "23:30"                       // ⚠️ string — HH:MM 格式
    }
  ],

  "smartMoneyDetail": [                     // ⚠️ array — 3个梯队
    {
      "tier": "T1旗舰",                     // ⚠️ string — 枚举：T1旗舰 / T2成长 / 策略师观点
      "funds": [                            // ⚠️ array — 每梯队2-3条
        {
          "name": "桥水基金",                // ⚠️ string
          "action": "增持中国ETF $2.3亿",    // ⚠️ string
          "signal": "bullish"               // ⚠️ string — 枚举：bullish / bearish / neutral
        }
      ]
    }
  ],

  "dataTime": "2026-04-01 09:00 BJT",       // ⚠️ string

  // ===== v1.3 新增：元数据 =====
  "_meta": {                                // 🔸 object — 元数据（可选）
    "sourceType": "heavy_analysis",         // 🔸 string — 枚举：heavy_analysis / realtime_quote / breaking_news
    "generatedAt": "2026-04-01T09:00:00+08:00",  // 🔸 string — ISO 8601 生成时间
    "skillVersion": "v1.3"                  // 🔸 string — Skill 版本号
  }
}
```

**红绿灯阈值标准（v1.2）**：

| # | 指标 | 🟢 green | 🟡 yellow | 🔴 red | 判断方式 |
|---|------|----------|-----------|--------|---------|
| 1 | VIX波动率 | <18 | [18, 25] | >25 | `auto_traffic_status()` 程序化 |
| 2 | 10Y美债收益率 | <4.0% | [4.0%, 4.5%] | >4.5% | `auto_traffic_status()` 程序化 |
| 3 | 布伦特原油 | <$90 | [$90, $110] | >$110 | `auto_traffic_status()` 程序化 |
| 4 | 美元指数DXY | <102 | [102, 107] | >107 | `auto_traffic_status()` 程序化 |
| 5 | HY信用利差 | <4% | [4%, 5%] | >5% | `auto_traffic_status()` 程序化 |
| 6 | **外资动向** | **港股均涨≥+1.5%** | **港股均涨0~+1.5%** | **港股均跌** | **`calc_foreign_capital_proxy()` 代理计算**（注：北向净买额已于2024-08-19永久停止披露） |
| 7 | 离岸人民币CNH | <7.15 | [7.15, 7.30] | >7.30 | `auto_traffic_status()` 程序化 |

> **riskScore 动态计算（v1.2）**：`calc_risk_score(traffic_lights)` = 30 + Σ(灯色权重)，上限100
> - green=0分，yellow=10分，red=20分
> - 基础分30代表正常市场背景噪音
> - 等级：<45=low / 45-64=medium / ≥65=high

---

## 五、通用规则

### 5.1 纯文本规则

所有 JSON 中的 string 类型字段必须是**纯文本**，禁止包含：
- `**加粗**` markdown 语法
- `| 表格 |` 表格语法
- `> 引用` 引用语法
- `- 列表` 列表语法（analysis 字段中用 `\n` 分段代替）
- `🚨` 等 emoji（riskNote、coreEvent.title 等字段）

### 5.2 数值类型规则

| 字段 | 类型 | 正确示例 | 错误示例 |
|------|------|---------|---------|
| `change` | number | `1.42` | `"+1.42%"` |
| `sentimentScore` | number | `62` | `"62"` |
| `riskScore` | number | `38` | `"38"` |
| `confidence` | number | `85` | `"85%"` |
| `sparkline[i]` | number | `5254.35` | `"5,254.35"` |
| `price` | string | `"$878.36"` | `878.36` |

### 5.3 枚举值完整清单

| 字段路径 | 允许值 |
|----------|--------|
| `globalReaction[].direction` | `up`, `down`, `flat` |
| `actions.today[].type` / `actions.week[].type` | `buy`, `sell`, `hold`, `bullish`, `bearish` |
| `smartMoney[].signal` | `bullish`, `bearish`, `neutral` |
| `sentimentLabel` | `极度恐惧`, `偏恐惧`, `中性`, `偏贪婪`, `贪婪`, `极度贪婪` |
| `sectors[].id` | `ai`, `semi`, `internet`, `energy`, `consumer`, `pharma`, `finance` |
| `sectors[].trend` | `up`, `down`, `hold` |
| `trafficLights[].status` | `green`, `yellow`, `red` |
| `riskLevel` | `low`, `medium`, `high` |
| `riskAlerts[].level` | `high`, `medium`, `low` |
| `events[].impact` | `high`, `medium`, `low` |
| `alerts[].level` | `danger`, `warning`, `info` |
| `smartMoneyDetail[].tier` | `T1旗舰`, `T2成长`, `策略师观点` |
| `smartMoneyDetail[].funds[].signal` | `bullish`, `bearish`, `neutral` |
| `usMarkets[].changeLabel` | `大盘指数`, `科技指数`, `蓝筹指数`, `恐慌指标` |
| `timeStatus.marketStatus`（v1.3） | `美股交易中`, `美股已收盘`, `盘前交易`, `盘后交易` |
| `keyDeltas[].status`（v1.3） | `升级`, `新增`, `活跃`, `降温`, `稳定` |
| `coreJudgments[].probability`（v1.3） | `高可能性`, `中可能性`, `低可能性` |
| `coreJudgments[].trend`（v1.3） | `上升`, `下降`, `稳定` |
| `fearGreed.label`（v1.3） | `Extreme Fear`, `Fear`, `Neutral`, `Greed`, `Extreme Greed` |
| `predictions[].trend`（v1.3） | `up`, `down`, `stable` |
| `predictions[].source`（v1.3） | `Polymarket`, `Kalshi`, `CME FedWatch` |
| `_meta.sourceType`（v1.3） | `heavy_analysis`, `realtime_quote`, `breaking_news` |

---

> v1.6 — 2026-04-02 20:18 | KEY DELTA 前端重构 + title 字数收紧：①`keyDeltas[].title` 字数限制由20-40字收紧为**≤15字**（单行显示不折行），附正确示例（"伊朗打击升级，停火破裂"/"WTI油价盘前暴涨6%"）和错误示例（超15字长标题）；②简报页 KEY DELTA 区块从 section-card 组件改为自定义 inline 结构，标题"增量信息 KEY DELTA"改为22rpx浅灰小标签（#bbb），视觉层级与"今日核心事件"标签对齐，重点突出下方 point 内容。
> v1.5 — 2026-04-02 20:02 | 数据时效性与格式规范修复：①`keyDeltas[].brief` 字长由30-80字收紧为**10-25字极简风格**（面向大老板阅读习惯，参照伊朗简报卡片样式），附正确示例（"供应链重构代价被重新定价，风险偏好承压"）和错误示例（超25字长句）；②`timeStatus.marketStatus` 新增完整时区判断规则注释（BJT与EDT/EST对照，防止时区计算错误）；③`dataTime` 新增时态标注规范，美股非收盘数据必须注明「盘前」或「盘后」，globalReaction中美股数据若非收盘值须在coreEvent.title中明确标注数据时态。
> v1.4 — 2026-04-02 18:24 | 字段内容边界规范升级（防冗余治本）：①`keyDeltas[].brief` 重定义为专写「为何重要/影响方向/市场逻辑」，禁止重复 coreEvent.title 或 chain 已有的具体数字；②`coreEvent.chain[]` 重定义为因果逻辑推演，禁止重复 brief 中已出现的具体数字（改为描述传导机制和影响边界）；③`marketSummary` 重定义为情绪结构判断+核心风险/下一变量，禁止汇总重复 keyDeltas/coreEvent/globalReaction 中的具体数字；三处均附正确/错误示例。字长限制：marketSummary 由50-150字收紧为50-120字。
> v1.3.2 — 2026-04-02 00:21 | markets.json 新增6个板块级 Insight 字段（usInsight/m7Insight/asiaInsight/commodityInsight/cryptoInsight/gicsInsight），每个板块数据表格底部提供30-80字高质量一句话洞察，对齐日报中的"XX信号"段落风格；原 usMarkets[0].note 迁移为独立 usInsight 字段，前端向后兼容；所有 Insight 为必填纯文本。
> v1.3.1 — 2026-04-02 00:00 | UI精修三项：①删除简报页顶部hero冗余渐变区域（导航栏已有标题），日期信息保留在底部数据状态栏；②修复判断扩展区 jx-divider 虚线样式（dashed→渐变淡化实线）；③references 从 string[] 升级为 object[]（含 name/summary/url），前端改为可点击展开的手风琴组件，支持下拉查看信息摘要和来源链接，向后兼容旧格式纯字符串数组。
> v1.3 — 2026-04-01 22:58 | 前端体验升级：①briefing.json 新增 `timeStatus` 时间状态栏（多时区+开市状态）；②新增 `keyDeltas[]` 增量信息 KEY DELTA 模块（借鉴 Iran Briefing 设计）；③`coreJudgments` 扩展 `keyActor/references/probability/trend` 四个可选字段；④radar.json 新增 `fearGreed` CNN Fear & Greed 情绪指数卡片；⑤新增 `predictions[]` 预测市场概率模块（Polymarket/Kalshi/CME FedWatch）；⑥所有 JSON 新增 `_meta` 元数据对象（sourceType/generatedAt/skillVersion）；⑦新增 🔸 可选标记，所有新字段均向后兼容。
> v1.2 — 2026-04-01 | 六项数据质量深度治理：①watchlist metrics 升级为方案C（4项行情+PE(TTM)+规则化综合评级）；②trafficLights第6项由「北向资金」改为「外资动向」（港股代理，2024-08-19起北向净买额永久停止披露）；③riskScore 改为 `calc_risk_score()` 动态计算，权重公式标准化；④阈值标准表新增「判断方式」列，明确全部由 `auto_traffic_status()` 程序化执行。
> v1.1 — 2026-04-01 | 老板直推级数据治理升级：交易数据字段强制直连行情源；`dataTime` 要显式写清分市场时点；watchlist `metrics` 改为6项可验证指标集合；删除 sparkline 估算逻辑。
> v1.0 — 2026-04-01 | 初始版本。基于小程序 `touyanduck_appid` 的4个页面 + 5个组件逐行审查，精确定义每个字段类型、必填性、枚举范围和数组长度要求。
