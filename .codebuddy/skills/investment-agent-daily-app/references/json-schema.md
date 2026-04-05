# JSON Schema 完整字段规范（v3.2）

> **用途**：定义投研鸭小程序 4 个 JSON 文件的精确字段规范。每个字段都对应小程序前端组件的一个渲染点。
> **核心原则**：Schema 即契约。JSON 生成阶段必须逐字段对照本文件，不允许新增/缺失/改名字段。
> **字段类型约定**：`string` = 字符串，`number` = 数字（非字符串），`array` = 数组，`object` = 对象
> **必填标记**：⚠️ = 必填（不允许为空字符串/空数组/null）；🔸 = 可选（省略时前端 `wx:if` 跳过，不渲染对应模块）

---

## 一、briefing.json — 简报页

**对应页面**：`pages/briefing/briefing.wxml` + `briefing.js`
**涵盖模块**：时间状态栏（v1.3）、今日结论TAKEAWAY（v1.7）、今日重点事件（chain对象化 v1.7）、全球资产反应（note v1.7）、三大判断（含扩展字段v1.3）、行动建议（reason v1.7）、情绪仪表盘、聪明钱速览、风险提示（v3.1 bullet point升级，🛡️图标）、元数据（v1.3）

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
    "marketStatus": "美股交易中",            // 🔸 string — 枚举：美股交易中 / 美股已收盘 / 盘前交易 / 盘后交易 / 美股休市
    // ⚠️ 时区判断规则（北京时间 BJT = UTC+8，美东夏令时 EDT = UTC-4，冬令时 EST = UTC-5）：
    // BJT 21:30 ~ 次日04:00 → 美股交易中（EDT 9:30~16:00）
    // BJT 04:00 ~ 06:00    → 盘后交易（EDT 16:00~18:00）
    // BJT 13:30 ~ 21:30    → 盘前交易（EDT 22:00~9:30 次日）
    // 其余时段             → 美股已收盘
    // 美国公共假日（如耶稣受难日、感恩节、国庆日、圣诞节等）→ 美股休市
    // 数据标注规则：globalReaction 中美股数据若非收盘值，必须在 dataTime 中注明「盘前」或「盘后」；休市日不需标注
    "refreshInterval": "每日更新"            // 🔸 string — 数据刷新频率说明
  },

  // ===== v1.7 新增：今日核心结论 TAKEAWAY =====
  "takeaway": "string",                     // 🔸 string — 30-80字，一句话宏观结论。要求：有立场、有行动方向、有条件（"如果X则Y"）；禁止：空洞废话、重复coreEvent原文。
  // ===== v1.9 新增：关键词标红机制 =====
  // 【强制】：takeaway 中的核心关键词必须用中文方括号【】包裹，前端 parseTakeaway() 正则 /【([^】]+)】/g 会将【】内的文字渲染为红色高亮（.takeaway-highlight { color: #e74c3c; font-weight: 700 }）
  // 标红原则：每句 takeaway 标红 3~5 个关键词，选择最核心的「行动指令」和「关键条件/数据」
  // 正确示例："停火预期彻底破裂叠加关税一周年情绪共振，今日【以防御为主】——【能源小仓对冲】、科技不追跌、等待【VIX回落至22以下】再重新入场。"
  // 错误示例（禁止）："停火预期彻底破裂叠加关税一周年情绪共振，今日以防御为主——能源小仓对冲、科技不追跌、等待VIX回落至22以下再重新入场。"（无【】标注，前端全部显示为普通黑色文字，关键信息淹没）
  // 错误示例（禁止）："【停火预期彻底破裂】叠加【关税一周年】【情绪共振】，【今日】【以防御为主】——..."（标红过多≥6个，失去重点，等于没有重点）

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
      "value": "string",                    // ⚠️ 涨跌幅或绝对值（如 "+0.87%" 或 "$4,675"）
      // ⚠️ 【精确数值强制规则】：禁止使用 `~`（约等于）、`≈`、`大约`、`左右` 等模糊前缀/后缀
      // 所有价格/涨跌幅必须来自行情源的精确数值，前端底部显示「更新时间」，用户预期数字与该时间点一致
      // 正确示例："$4,675" / "+7.78%" / "4.32%"
      // 错误示例（禁止）："~$4,677"（波浪号=约等于，不精确）/ "约$4,700"（中文模糊词）/ "$4,600+"（加号模糊）
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
  // ⚠️ sentimentLabel 与 sentimentScore 的对应关系（强制）：
  //   0-20  → 极度恐惧
  //   21-40 → 偏恐惧
  //   41-60 → 中性
  //   61-75 → 偏贪婪
  //   76-90 → 贪婪
  //   91-100→ 极度贪婪
  // ⚠️ 禁止使用非枚举值（如「偏悲观」「偏乐观」「恐慌」等），必须严格使用上述6个中文标签
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

  "riskPoints": [                          // ⚠️ array — 风险提示 bullet point，2-4条，取代旧版 riskNote 字符串
    "string"                                // ⚠️ 每条15-50字，一个独立风险点或行动建议，纯文本
    // 写作规则：
    // - 每条只说一个风险点，聚焦「是什么风险 + 触发条件 + 影响方向」
    // - 最后一条可以是行动建议（如"建议今日不操作，下周一等价格发现后再行动"）
    // - 禁止：一整段散文（前端无法分条渲染）、markdown 语法、emoji
    // 正确示例：["NFP实际数字在低流动性环境发布，若再次大幅偏离预期，外汇和商品市场将剧烈震荡", "油价固化通胀预期——布伦特若持续站稳110美元，美联储被迫维持高利率", "建议今日不操作，下周一等价格发现后再行动"]
    // 错误示例（禁止）：["今日最大尾部风险：NFP实际数字在低流动性环境发布，若再次意外大幅偏离预期（参考2月-92K远低预期），将引发外汇和商品市场剧烈震荡。中期最大风险仍是油价固化通胀预期——布伦特若持续站稳110美元...建议今日不操作"]（一整段散文塞进单个数组元素，等于没拆分）
    // 旧版兼容：若 riskPoints 缺失，前端自动用 riskNote 字符串按句号拆分兜底
  ],
  "riskNote": "string",                     // 🔸 旧版兼容字段——30-100字风险提示散文，纯文本。新版产出时仍保留此字段作为 fallback，但前端优先渲染 riskPoints 数组
  "dataTime": "2026-04-01 09:00 BJT",       // ⚠️ string — 格式固定为 "YYYY-MM-DD HH:MM BJT"，四个JSON保持完全一致，与简报页顶部时间同步

  // ===== v1.3 新增：元数据 =====
  "_meta": {                                // 🔸 object — 元数据（可选，无则前端不显示来源标签）
    "sourceType": "heavy_analysis",         // 🔸 string — 枚举：heavy_analysis / realtime_quote / breaking_news / weekend_insight（v4.0新增）
    "generatedAt": "2026-04-01T09:00:00+08:00",  // 🔸 string — ISO 8601 生成时间
    "skillVersion": "v4.0"                  // 🔸 string — 生产此数据的 Skill 版本号
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
| 风险提示底部（v3.1 bullet升级） | `riskPoints[]` + `riskNote`(兼容) | 2-4条 | 前端 🛡️ 图标 + bullet point 渲染；旧版 riskNote 字符串兜底按句号拆分 |
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

**板块 insightChain 规范（v2.4 新增）**：

> 每个 Insight 字段对应一个 `insightChain` 数组，用于前端渲染竖版因果链卡片（3节点）。

| 字段 | 类型 | 必填 | 结构 |
|------|------|------|------|
| `usInsightChain` | array | ⚠️ | 3条，每条 `{ icon: string, label: string, text: string }` |
| `m7InsightChain` | array | ⚠️ | 3条，每条同上 |
| `asiaInsightChain` | array | ⚠️ | 3条，每条同上 |
| `commodityInsightChain` | array | ⚠️ | 3条，每条同上 |
| `cryptoInsightChain` | array | ⚠️ | 3条，每条同上 |
| `gicsInsightChain` | array | ⚠️ | 3条，每条同上 |

**insightChain 节点字段规范**：

| 子字段 | 说明 | 示例 |
|--------|------|------|
| `icon` | 1个 emoji，代表该节点性质 | `"⚡"` `"📉"` `"🔄"` |
| `label` | ≤4字，节点逻辑标签（触发/反应/轮动/背景/领涨/领跌/压力/结论/信号/展望/主驱动/异动） | `"触发"` `"反应"` |
| `text` | 15-35字，完整短句，禁止用 `·` 分隔多个要点 | `"WTI油价暴涨14%，霍尔木兹封锁溢价固化"` |

**⚠️ 数字一致性强制规则（v2.4 新增）**：
- `insightChain[].text` 中出现的任何数字（价格/涨跌幅/百分比）必须与对应板块 `price`/`change` 字段完全一致
- 不允许出现方向矛盾（change 为负但文字说"上涨"）
- 不允许出现数值差异（change=-2.73 但文字说"跌5%"）
- 正确做法：先填完 `price`/`change`，再根据这些值写 `insightChain[].text`
- **数字来源**：insightChain 文字中的数字直接引用已采集的 `change` 字段值，不允许重新从媒体文章中"记忆"价格数字

**sparkline 生成规则**：
- 7 个数据点代表近 7 个交易日收盘价（真实历史序列）
- 数据来源：`yfinance.download(period="10d")["Close"]` 取最近7个交易日 / AkShare 历史接口
- **禁止估算/插值/模拟波动生成**（v1.2起强制阻断），sparkline 缺失时回采重试，仍失败则阻断发布

---

## 三、watchlist.json — 标的页（v2.0 重构）

**对应页面**：`pages/watchlist/watchlist.wxml` + `stock-card.wxml`
**涵盖模块**：板块 Tab + 板块概述 + 股票卡片（含聪明钱标签）+ 展开详情 + 未上市标的动态卡
**设计立意**：以大老板投资视角为核心（AI全产业链 + 聪明钱跟踪），板块和标的灵活可变。

```jsonc
{
  "date": "2026-04-01",                    // ⚠️ string

  "sectors": [                              // ⚠️ array — 4-5个板块（hot_topic无事件时不包含）
    {
      "id": "ai_infra",                     // ⚠️ string — 枚举：ai_infra / ai_app / cn_ai / smart_money / hot_topic
      "name": "AI算力链",                    // ⚠️ string — 显示名称
      "trend": "up",                        // ⚠️ string — 枚举：up / down / hold
      "summary": "string"                   // ⚠️ 板块概述，2-3句话，纯文本，含关键数据+判断
    }
  ],
  // sectors 排序固定：ai_infra → ai_app → cn_ai → smart_money → hot_topic（如有）
  // hot_topic 为动态板块：有事件时包含，无事件时从 sectors 数组中省略（前端 wx:for 自动适配）
  // 每个板块的 summary 要求：含具体数据（涨跌幅/价格）+ 核心驱动力判断 + 后续关注点
  //   正确示例："NVDA收于$177(+5.6%)领涨，Blackwell出货加速叠加微软Azure资本开支上调，产业链修复确认但高波动未消。"
  //   错误示例："AI板块整体表现不错，多只标的上涨。"（空洞无信息量）

  "stocks": {                               // ⚠️ object — 按板块 ID 分组
    "ai_infra": [                           // ⚠️ array — 10-12只
      {
        "name": "英伟达",                    // ⚠️ string — 中文名
        "symbol": "NVDA",                   // ⚠️ string — 股票代码
        "change": 5.59,                     // ⚠️ number — 涨跌幅百分比（正数=涨，负数=跌）
        "price": "$174.40",                 // ⚠️ string — 当前价格（含货币符号）
        "listed": true,                     // ⚠️ boolean — 是否已上市（默认true，未上市标的为false）
        "tags": ["AI芯片龙头", "Blackwell出货"], // ⚠️ string[] — 2个标签，4-8字
        "badges": ["段永平大幅增持"],         // 🔸 string[] — 特殊标签（可选，0-2个）
        // badges 枚举：巴菲特第一重仓 / 巴菲特持有 / 段永平重仓 / 段永平持有 / 段永平大幅增持 / 段永平新建仓 / 段永平关注 / 未上市
        // 「段永平关注」（v2.1新增）：段永平公开看好/实地调研但尚未在13F中确认建仓（如泡泡玛特），区别于「段永平持有」
        // 前端渲染：badges 用独立样式（金色/蓝色小标签），区别于普通 tags（黄色）
        "reason": "string",                 // ⚠️ 一句话核心逻辑（20-60字），要求有结论+论据
        //   正确示例："AI数据中心资本开支持续超预期，Blackwell供不应求，产业链地位不可替代"
        //   错误示例："英伟达是一家很好的AI公司"（空洞无论据）
        "analysis": "string",              // ⚠️ AI分析摘要（2-3段，100-300字，纯文本，\n\n分段）
        "metrics": [                        // ⚠️ array — 精确6项指标（方案C），已上市标的必填
          { "label": "最新价", "value": "$174.40" },
          { "label": "单日涨跌", "value": "+5.59%" },
          { "label": "7日涨跌", "value": "-0.71%" },
          { "label": "30日涨跌", "value": "-7.22%" },
          { "label": "PE(TTM)", "value": "36.2x" },
          { "label": "综合评级", "value": "⭐⭐⭐⭐" }
        ],
        "risks": [                          // ⚠️ string[] — 2-3条风险，每条一句话
          "AMD MI300X竞争加剧，定制ASIC分流算力需求",
          "出口管制政策不确定性影响中国市场收入"
        ],
        "sparkline": [168, 170, 172, 171, 173, 175, 174],  // ⚠️ number[] — 7天真实收盘价
        "chartData": [165, 166, 168, ...]   // ⚠️ number[] — 30天真实收盘价（展开详情大图用）
      },
      // === 未上市标的示例（字节跳动）===
      {
        "name": "字节跳动",
        "symbol": "ByteDance",              // 未上市：填公司英文名
        "change": 0,                        // 未上市：固定填0
        "price": "未上市",                   // 未上市：固定填"未上市"
        "listed": false,                    // ⚠️ 未上市标识
        "tags": ["豆包日活破亿", "AI视频生成"],
        "badges": ["未上市"],
        "reason": "豆包+即梦+Coze构成日活最大的AI应用矩阵，Coze Agent平台开发者生态快速扩张",
        "analysis": "字节跳动旗下AI产品矩阵全面开花...\n\n最新动态：...",  // 改为"动态+竞争格局+估值"
        "metrics": [],                      // 未上市：空数组
        "risks": ["未上市，无公开财务数据", "监管与上市时间表不确定"],
        "sparkline": [],                    // 未上市：空数组
        "chartData": []                     // 未上市：空数组
      }
    ],
    "ai_app": [...],                        // ⚠️ 4-6只
    "cn_ai": [...],                         // ⚠️ 5-7只（含未上市标的）
    "smart_money": [...],                   // ⚠️ 5-6只
    "hot_topic": [...]                      // 🔸 0-4只（无事件时该key可省略或空数组）
  },

  "dataTime": "2026-04-04 22:00 BJT"  // ⚠️ string — 格式固定为 "YYYY-MM-DD HH:MM BJT"，四个JSON保持完全一致
}
```

**板块架构规则（v2.0）**（详见 [stock-universe.md](stock-universe.md)）：

| 板块 ID | 名称 | 定位 | 标的数 | 稳定性 |
|---------|------|------|--------|--------|
| `ai_infra` | AI算力链 | 美股AI全产业链（芯片→制造→云→终端→基建） | 10-12只 | 基本稳定 |
| `ai_app` | AI应用 | 5个独立AI应用方向 | 4-6只 | 较稳定 |
| `cn_ai` | 国产AI | 中国AI核心（港股+A股+未上市动态） | 5-7只 | 灵活调整 |
| `smart_money` | 聪明钱 | 巴菲特+段永平非AI核心持仓 | 5-6只 | 季度更新 |
| `hot_topic` | 本期热点 | 事件驱动（每期可变，可为空） | 0-4只 | 每期可变 |

**`badges` 特殊标签系统（v2.0新增）**：

| badge 值 | 含义 | 前端样式 |
|----------|------|---------|
| `巴菲特第一重仓` | BRK持仓占比最高 | 金色标签 |
| `巴菲特持有` | BRK持仓 | 金色标签 |
| `段永平重仓` | 段永平核心持仓 | 蓝色标签 |
| `段永平持有` | 段永平持有 | 蓝色标签 |
| `段永平大幅增持` | 近一季度增持超100% | 蓝色标签 |
| `段永平新建仓` | 近一季度首次买入 | 蓝色标签 |
| `段永平关注` | 公开看好/调研但未确认建仓 | 蓝色标签（浅色） |
| `未上市` | 无二级市场数据 | 灰色标签 |

**未上市标的字段规则**：

| 字段 | 已上市标的 | 未上市标的 |
|------|-----------|-----------|
| `listed` | `true`（可省略） | `false`（必填） |
| `price` | `"$174.40"`（真实价格） | `"未上市"`（固定值） |
| `change` | 真实涨跌幅 number | `0`（固定值） |
| `metrics` | 6项完整指标 | `[]`（空数组） |
| `sparkline` | 7天真实数据 | `[]`（空数组） |
| `chartData` | 30天真实数据 | `[]`（空数组） |
| `analysis` | 公司分析+业务亮点+风险 | **最新动态+竞争格局+估值/融资** |
| `tags` | 行业地位+催化剂 | 产品动态+赛道定位 |
| `badges` | 聪明钱/已汇报标签 | 必含 `["未上市"]` |

**metrics 6项标准（方案C — 延续）**：

| # | label | 数据来源 | 格式示例 | 类型约束 | 说明 |
|---|-------|---------|---------|---------|------|
| 1 | 最新价 | yfinance/AkShare 实时价 | `"$174.40"` | **string**（含货币符号） | 自动计算 |
| 2 | 单日涨跌 | 当日 close vs prev close | `"+5.59%"` | **string**（含正负号和%） | 自动计算 |
| 3 | 7日涨跌 | last7[0] → last7[-1] | `"-0.71%"` | **string**（含正负号和%） | 自动计算 |
| 4 | 30日涨跌 | last30[0] → last30[-1] | `"-7.22%"` | **string**（含正负号和%） | 自动计算 |
| 5 | PE(TTM) | `yfinance Ticker.info["trailingPE"]` | `"53.4x"`（无数据则`"—"`） | **string** | 辅助指标，缺失不阻断 |
| 6 | 综合评级 | `calc_star_rating()` 规则函数 | `"⭐⭐⭐⭐"` | **string** | 规则化自动计算 |

> **⚠️ 格式强制规范**：metrics 第1项必须含货币符号（`"$"` 或 `"HK$"` 或 `"¥"`）；第2-4项必须含正负号和 `%` 后缀；全部6项的 `value` 字段必须为 **string 类型**。

> **评级规则**（`calc_star_rating(change, pct_30d)`）：
> - ⭐⭐⭐⭐⭐：30日涨超+15% 且 单日为正
> - ⭐⭐⭐⭐  ：30日涨+5%~+15%，或单日涨超+3%
> - ⭐⭐⭐    ：30日在-5%~+5%（震荡整理）
> - ⭐⭐      ：30日跌-5%~-15%
> - ⭐        ：30日跌超-15%（深度回调）

---

## 四、radar.json — 雷达页

**对应页面**：`pages/radar/radar.wxml` + `radar.js`
**版本**：v3.3（2026-04-05，对应前端 radar.js v6.3 / radar.wxml v6.3）
**涵盖模块（v6.3 新6模块）**：
1. **聪明钱动向**（三梯队扁平化，按 T1>T2>策略师 排序，全部直接展示，不折叠）
2. **聪明钱持仓** ⭐v6.3新增（巴菲特BRK + 段永平H&H 的13F头部持仓及占比，默认折叠，点击展开）
3. **风险判断**（一句话风险结论 + 7项红绿灯指标明细）
4. **本周前瞻**（events + riskAlerts 前端自动融合为时间线）
5. **市场在赌什么**（predictions，默认折叠，只显示当周强相关条目）
6. **异动信号**（alerts，无数据时模块整体隐藏）

**废弃模块（v6.0）**：
- 综合风险评分圆圈：字段 `riskScore`/`riskLevel` 保留（供 riskAdvice 内容参考），但不再单独渲染为圆形卡片
- 关键监控阈值表：字段 `monitorTable[]` 向后兼容保留，但**前端不再渲染**，产出时可省略或继续填写

```jsonc
{
  "date": "2026-04-01",                    // ⚠️ string

  // ===== Fear & Greed 情绪指数 =====
  "fearGreed": {                            // 🔸 object — 安全信号模块上半部分；无则情绪条不渲染
    "value": 42,                            // 🔸 number — 0-100 当前值
    "label": "Fear",                        // 🔸 string — 枚举：Extreme Fear / Fear / Neutral / Greed / Extreme Greed
    "previousClose": 38,                    // 🔸 number — 昨日收盘值
    "oneWeekAgo": 55,                       // 🔸 number — 一周前值
    "oneMonthAgo": 61                       // 🔸 number — 一月前值
  },

  // ===== 预测市场 =====
  // v4.4 筛选规则：① 与本周 events[] 直接相关 ② change24h 绝对值 > 5（快速变化中） ③ 极端概率（>65% 或 <20%）
  // 淘汰：长期宏观预测（无本周关联）/ change24h ≈ 0 的（市场无新信息）/ 成交量极小的小众事件
  // 数量：精选 2-3 条，宁少勿滥
  "predictions": [                          // 🔸 array — 2-4条（可选，无则前端不渲染该模块）
    {
      "title": "美联储6月降息?",             // 🔸 string — 预测问题（简洁，15字以内）
      "source": "Polymarket",               // 🔸 string — 枚举：Polymarket / Kalshi / CME FedWatch
      "probability": 72,                    // 🔸 number — 概率百分比 0-100
      "trend": "up",                        // 🔸 string — 枚举：up / down / stable
      "change24h": 5                        // 🔸 number — 24小时概率变化（正数上升，负数下降）
    }
  ],

  // ===== 7项红绿灯（安全信号摘要区数据源）=====
  "trafficLights": [                        // ⚠️ array — 精确7项，顺序固定
    {
      "name": "VIX波动率",                   // ⚠️ string
      "value": "13.0",                      // ⚠️ string — 精确数值，禁止模糊前缀（~/$约/+等）
      "status": "green",                    // ⚠️ string — 枚举：green / yellow / red
      "threshold": "<18绿 / 18-25黄 / >25红" // ⚠️ string — 阈值说明（复制 SKILL.md 第2.3阶段计算表）
    }
  ],
  // trafficLights 精确7项顺序（不可改变）：
  // VIX波动率 / 10Y美债收益率 / 布伦特原油 / 美元指数DXY / HY信用利差 / 黄金XAU / 离岸人民币CNH

  // ===== 综合风险评分（安全信号建议的数据支撑）=====
  "riskScore": 38,                          // ⚠️ number — 0-100，按 SKILL.md 公式计算
  "riskLevel": "medium",                    // ⚠️ string — 枚举：low / medium / high
  // ⚠️ riskAdvice v4.4 升级规范（详见 SKILL.md §2.3）：
  //   必须：①点名 1-2 项最危险指标说清楚危险在哪 ②结合 fearGreed.value 说情绪方向 ③给出具体仓位建议
  //   禁止：套模板（"当前风险评分X（Y）"开头）、模糊建议（"保持谨慎"）
  //   正确示例："布伦特原油$109（近红区间）叠加外资偏谨慎，情绪恐惧区（F&G 42），建议维持6成仓位，能源对冲维持至原油回落$100。"
  "riskAdvice": "string",                   // ⚠️ 动态一句话建议，不超过2句，每句有信息量

  // ===== 关键监控阈值（向后兼容，前端 v6.0 不再渲染）=====
  // ⚠️ v4.4 废弃渲染：前端已移除该模块，但字段向后兼容保留
  // 建议：将核心阈值触发条件内化到 riskAlerts[] 中
  "monitorTable": [                         // 🔸 array — 可选，前端不渲染（v4.4 废弃渲染）
    {
      "condition": "VIX突破25",              // 🔸 string
      "action": "将股票仓位降至5成以下"       // 🔸 string
    }
  ],

  // ===== 风险预警（本周前瞻时间线的附注部分）=====
  // 注意：前端将 events[] + riskAlerts[] 融合为「本周前瞻」时间线
  //   - events[]：有具体日期，作为时间轴锚点
  //   - riskAlerts[]：标注"持续"，附带概率和应对建议作为风险附注
  "riskAlerts": [],                          // ⚠️ array — v4.8起废弃渲染，填空数组[]。风险信息通过riskAdvice和alerts覆盖，不再在本周前瞻中重复展示

  // ===== 关键事件日历（本周前瞻时间线的主体）=====
  "events": [                               // ⚠️ array — 3-5条本周事件
    {
      "date": "周三",                        // ⚠️ string — "周一"/"周四"/"04/03"等
      "title": "FOMC 3月会议纪要发布，聚焦通胀措辞和降息路径讨论",  // ⚠️ string — 事件标题，20-40字，需说明为什么重要
      "impact": "high",                     // ⚠️ string — 枚举：high / medium / low
      "source": "Federal Reserve",          // 🔸 string — 数据来源名称（v3.0 新增，前端可点击跳转）
      "url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"  // 🔸 string — 来源链接（v3.0 新增）
    }
  ],

  // ===== 异动监测（无数据时整个模块隐藏）=====
  "alerts": [                               // ⚠️ array — 0-4条异动；空数组时前端模块不显示
    {
      "level": "danger",                    // ⚠️ string — 枚举：danger / warning / info
      "text": "string",                     // ⚠️ 异动描述，含具体数据和数字，禁止模糊表述
      "time": "23:30",                      // ⚠️ string — HH:MM 格式
      "source": "AP News",                  // 🔸 string — 消息来源名称（v3.0 新增）
      "url": "https://..."                  // 🔸 string — 来源链接（v3.0 新增）
    }
  ],

  // ===== 聪明钱三梯队（前端自动扁平化展示）=====
  // v4.4 内容质量要求（详见 SKILL.md §2.3 radar.json 产出质量规范）：
  //   ① T1旗舰：配置方向判断 + 具体信号，禁止"维持中性"等无信息表达
  //   ② T2成长：对当前市场环境的判断 + 操作建议
  //   ③ 策略师：具体看好/看空的板块或标的，禁止"关注市场变化"空话
  // ⚠️ 前端自动将三梯队扁平化为 T1>T2>策略师 排序的列表，全部直接展示不折叠
  "smartMoneyDetail": [                     // ⚠️ array — 3个梯队，顺序固定
    {
      "tier": "T1旗舰",                     // ⚠️ string — 枚举：T1旗舰 / T2成长 / 策略师观点
      "funds": [                            // ⚠️ array — 每梯队2-3条
        {
          "name": "桥水基金",                // ⚠️ string — 机构名
          "action": "全天候组合本周增配黄金ETF（GLD）约$4.2亿，Dalio表态「滞胀交易远未结束」",  // ⚠️ string — 具体动向，含数字+操作+理由
          "signal": "bearish",              // ⚠️ string — 枚举：bullish / bearish / neutral
          "source": "Bloomberg",            // 🔸 string — 信息来源名称（v3.0 新增，前端可点击跳转）
          "url": "https://...",             // 🔸 string — 来源链接（v3.0 新增）
          "freshness": "本周"               // 🔸 string — 枚举：本周 / 上周 / 本月（v3.2 新增，策略师观点时效标注）
          // freshness 使用规则（详见 fund-universe.md §5.4 策略师观点时效规则）：
          // - T1旗舰 / T2成长 梯队：通常不需要填（机构动向本身有时效性）
          // - 策略师观点梯队：当观点不是本周发布时，必须填写
          //   "本周" = 7天以内发布（默认，可省略）
          //   "上周" = 8-14天前发布（action 字段前还需加 [MM/DD] 日期前缀）
          //   "本月" = 15-30天前发布（仅在无更新观点时作为兜底使用）
          // - 前端可据此字段显示灰色时效标签（如"上周观点"），帮助读者判断信息新鲜度
          // - 超过 30 天的观点禁止填入（过期信息无参考价值）
        }
      ]
    }
  ],

  // ===== 聪明钱持仓快照（v6.3/v3.3 新增）=====
  // 展示巴菲特（BRK 13F）和段永平（H&H 13F）的头部持仓及占比
  // 数据来源：SEC 13F 季度披露（有延迟，需标注数据截止时间）
  // 前端交互：默认折叠，用户点击展开查看
  // 更新频率：每季度 13F 披露后更新（2/5/8/11月中旬），平时保持不变
  "smartMoneyHoldings": [                   // 🔸 array — 2-N 个投资人/机构持仓快照（可选，无则前端不渲染该模块）
    {
      "manager": "巴菲特 · 伯克希尔",       // ⚠️ string — 投资人/机构名称
      "fund": "Berkshire Hathaway",         // 🔸 string — 基金/公司英文名
      "aum": "$294.3B",                    // 🔸 string — 总持仓市值（13F披露口径）
      "asOf": "2025Q4 · 2月披露",           // ⚠️ string — 数据截止时间+披露时间（让读者知道数据有延迟）
      "positions": [                        // ⚠️ array — 头部持仓，推荐Top10（按占比降序）。默认折叠展示，不占空间
        {
          "name": "苹果",                   // ⚠️ string — 中文名
          "symbol": "AAPL",                // ⚠️ string — 股票代码
          "weight": "21.8%",               // ⚠️ string — 持仓占比（含%号）
          "change": "减持"                  // 🔸 string — 本季变动（加仓/减持/新建仓/持仓不变/清仓），无变动时可省略
        }
      ],
      "footnote": "持仓数36只，Top10占81.3%，Turnover 5.26%（极低换手），现金储备$3,700亿+"  // 🔸 string — 补充说明，一句话
    }
  ],

  "dataTime": "2026-04-01 09:00 BJT",       // ⚠️ string

  "_meta": {                                // 🔸 object — 元数据（可选）
    "sourceType": "heavy_analysis",         // 🔸 string — 枚举：heavy_analysis / realtime_quote / breaking_news / weekend_insight
    "generatedAt": "2026-04-01T09:00:00+08:00",  // 🔸 string — ISO 8601
    "skillVersion": "v4.4"                  // 🔸 string — Skill 版本号
  }
}
```

**红绿灯阈值标准（v1.2 — 不变）**：

| # | 指标 | 🟢 green | 🟡 yellow | 🔴 red | 判断方式 |
|---|------|----------|-----------|--------|---------|
| 1 | VIX波动率 | <18 | [18, 25] | >25 | `auto_traffic_status()` 程序化 |
| 2 | 10Y美债收益率 | <4.0% | [4.0%, 4.5%] | >4.5% | `auto_traffic_status()` 程序化 |
| 3 | 布伦特原油 | <$90 | [$90, $110] | >$110 | `auto_traffic_status()` 程序化 |
| 4 | 美元指数DXY | <102 | [102, 107] | >107 | `auto_traffic_status()` 程序化 |
| 5 | HY信用利差 | <4% | [4%, 5%] | >5% | `auto_traffic_status()` 程序化 |
| 6 | **黄金XAU** | **<$2,200** | **[$2,200, $3,500]** | **>$3,500** | **避险情绪纯粹指标（v4.6替代外资动向）** |
| 7 | 离岸人民币CNH | <7.15 | [7.15, 7.30] | >7.30 | `auto_traffic_status()` 程序化 |

> **riskScore 动态计算（v1.2）**：`calc_risk_score(traffic_lights)` = 30 + Σ(灯色权重)，上限100
> - green=0分，yellow=10分，red=20分
> - 等级：<45=low / 45-64=medium / ≥65=high

**前端展示逻辑说明（v6.1 供 AI 理解）**：

| 字段 | 前端处理方式 | AI 注意事项 |
|------|------------|------------|
| `trafficLights[7]` | 自动统计 green/yellow/red 数量，以彩色徽标形式展示；点击展开7项明细 | 顺序和数量必须精确（⚠️ 不可改变） |
| `smartMoneyDetail[3梯队]` | 自动展开为扁平列表，T1>T2>策略师排序，**全部直接展示不折叠**；每条显示来源链接可点击跳转 | 三梯队结构不变；`source`/`url` 可选，有则前端展示蓝色可点击来源标签 |
| `events[] + riskAlerts[]` | 自动融合为时间线：events 带具体日期，riskAlerts 标注"持续"并附风险附注；**每条显示📎来源链接可点击** | 两个字段独立填写；`source`/`url` 可选，有则前端显示蓝色可点击来源 |
| `predictions[]` | 默认折叠，标题行显示钩子文字（如"美联储6月降息 28% ↓"） | 筛选规则见 SKILL.md §2.3 |
| `alerts[]` | 空数组时整个模块不显示；**每条显示来源链接** | 无异动时可填 `[]`；`source`/`url` 可选 |
| `monitorTable[]` | **v4.4 废弃渲染，前端不显示** | 可省略或继续填写（向后兼容） |
| `riskScore` / 圆圈 | **v4.4 废弃圆圈渲染**，数值仍用于内部计算 riskAdvice | 仍需按公式计算填写 |

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
| `actions.today[].type` / `actions.week[].type` | `hold`, `add`, `reduce`, `buy`, `sell`, `watch`, `hedge`, `stoploss`（**禁止 `bullish` / `bearish`**） |
| `smartMoney[].signal` | `bullish`, `bearish`, `neutral` |
| `sentimentLabel` | `极度恐惧`, `偏恐惧`, `中性`, `偏贪婪`, `贪婪`, `极度贪婪`（**禁止**「偏悲观」「偏乐观」等非标准值；score→label映射见§1注释） |
| `sectors[].id` | `ai`, `semi`, `internet`, `energy`, `consumer`, `pharma`, `finance` |
| `sectors[].trend` | `up`, `down`, `hold` |
| `trafficLights[].status` | `green`, `yellow`, `red` |
| `riskLevel` | `low`, `medium`, `high` |
| `riskAlerts[].level` | `high`, `medium`, `low` |
| `events[].impact` | `high`, `medium`, `low` |
| `alerts[].level` | `danger`, `warning`, `info` |
| `smartMoneyDetail[].tier` | `T1旗舰`, `T2成长`, `策略师观点` |
| `smartMoneyDetail[].funds[].signal` | `bullish`, `bearish`, `neutral` |
| `smartMoneyDetail[].funds[].freshness`（v3.2） | `本周`, `上周`, `本月` |
| `usMarkets[].changeLabel` | `大盘指数`, `科技指数`, `蓝筹指数`, `恐慌指标` |
| `timeStatus.marketStatus`（v1.3→v2.3） | `美股交易中`, `美股已收盘`, `盘前交易`, `盘后交易`, `美股休市`（v2.3新增，用于美国公共假日如耶稣受难日/感恩节/圣诞节等） |
| ~~`keyDeltas[].status`~~（**已废弃 v2.0，禁止使用**） | ~~`升级`, `新增`, `活跃`, `降温`, `稳定`~~ — `keyDeltas[]` 整个模块已于 v2.0 从简报页删除，脚本/AI 均不应生成此字段 |
| `coreJudgments[].probability`（v1.3） | `高可能性`, `中可能性`, `低可能性` |
| `coreJudgments[].trend`（v1.3） | `上升`, `下降`, `稳定` |
| `fearGreed.label`（v1.3） | `Extreme Fear`, `Fear`, `Neutral`, `Greed`, `Extreme Greed` |
| `predictions[].trend`（v1.3） | `up`, `down`, `stable` |
| `predictions[].source`（v1.3） | `Polymarket`, `Kalshi`, `CME FedWatch` |
| `_meta.sourceType`（v1.3, v4.0扩展） | `heavy_analysis`, `realtime_quote`, `breaking_news`, `weekend_insight` |

---

> v3.3 — 2026-04-05 22:59 | **聪明钱动向取消折叠**：①前端去掉"展开/收起"按钮，聪明钱动向全部直接展示不折叠；②清理 `smartMoneyShowAll`/`smartMoneyTotal` 数据字段和 `toggleSmartMoneyAll` 方法；③对应前端 radar.js/wxml/wxss 同步精简；④Skill 规范同步更新描述。
> v3.2 — 2026-04-05 20:01 | **策略师观点时效标注**：①`smartMoneyDetail[].funds[]` 新增 🔸 可选 `freshness` 字段（枚举：本周/上周/本月），用于标注策略师观点的发布时效；②前端可据此显示灰色时效标签帮助读者判断新鲜度；③枚举值清单同步新增 `freshness`；④超过30天的观点禁止填入。
> v3.1 — 2026-04-05 19:14 | **雷达页来源链接+数据质量升级**：①`events[]` 新增 `source`/`url` 🔸可选字段（前端 v6.1 支持点击跳转 webview）；②`riskAlerts[]` 新增 `source`/`url`；③`alerts[]` 新增 `source`/`url`；④`smartMoneyDetail[].funds[]` 新增 `source`/`url`（每条机构动向可附来源链接）；⑤`events[].title` 内容规范升级（20-40字，需说明为什么重要，而非纯事件名称）；⑥`riskAdvice` 示例更新为动态内容规范（点名最危险指标+具体仓位建议）；⑦`smartMoneyDetail[].funds[].action` 示例更新为含具体数字的高质量内容。
> v3.0 — 2026-04-05 18:35 | **雷达页5模块重构**：①前端 radar.wxml v6.0 重构为5模块；②废弃渲染：综合风险评分圆圈、关键监控阈值表；③`smartMoneyDetail[]` 新增内容质量规范；④`predictions[]` 新增筛选规则；⑤`riskAdvice` 动态内容规范；⑥`events[] + riskAlerts[]` 融合展示说明；⑦`alerts[]` 可为空数组。
> v2.3 — 2026-04-05 | **枚举健壮性升级**：①`marketStatus` 新增 `美股休市` 枚举值；②`sentimentLabel` 新增 score→label 对应关系注释；③枚举总表升级。
> v2.2 — 2026-04-05 | **风险提示模块 bullet point 升级**：①`riskNote` 升级为 `riskPoints[]` 数组；②保留旧版兼容；③图标从 ⚠️ 更换为 🛡️。
> v2.1 — 2026-04-03 20:28 | 全面审查修复（13处）。
> v2.0 — 2026-04-03 | 见 SKILL.md v3.0 Changelog。
> v1.6 — 2026-04-02 20:18 | KEY DELTA 前端重构。
> v1.5 — 2026-04-02 20:02 | 数据时效性与格式规范修复。
> v1.4 — 2026-04-02 18:24 | 字段内容边界规范升级。
> v1.3.2 — 2026-04-02 00:21 | markets.json 新增6个板块级 Insight 字段。
> v1.3.1 — 2026-04-02 00:00 | UI精修三项。
> v1.3 — 2026-04-01 22:58 | 前端体验升级（timeStatus/keyDeltas/fearGreed/predictions/_meta）。
> v1.2 — 2026-04-01 | 六项数据质量深度治理。
> v1.1 — 2026-04-01 | 老板直推级数据治理升级。
> v1.0 — 2026-04-01 | 初始版本。
