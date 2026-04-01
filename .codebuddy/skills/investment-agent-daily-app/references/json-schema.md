# JSON Schema 完整字段规范（v1.0）

> **用途**：定义投研鸭小程序 4 个 JSON 文件的精确字段规范。每个字段都对应小程序前端组件的一个渲染点。
> **核心原则**：Schema 即契约。JSON 生成阶段必须逐字段对照本文件，不允许新增/缺失/改名字段。
> **字段类型约定**：`string` = 字符串，`number` = 数字（非字符串），`array` = 数组，`object` = 对象
> **必填标记**：⚠️ = 必填（不允许为空字符串/空数组/null）

---

## 一、briefing.json — 简报页

**对应页面**：`pages/briefing/briefing.wxml` + `briefing.js`
**涵盖模块**：核心事件、事件链、全球资产反应、三大判断、行动建议、情绪仪表盘、聪明钱速览、风险提示

```jsonc
{
  "date": "2026-04-01",                    // ⚠️ string — YYYY-MM-DD 格式

  "coreEvent": {                            // ⚠️ object — 核心事件
    "title": "string",                      // ⚠️ 30-80字，纯文本，禁止 markdown/emoji
    "chain": [                              // ⚠️ string[] — 传导链，3-6条
      "string — 每条是独立完整语句，禁止含 | 管道符"
    ]
  },

  "globalReaction": [                       // ⚠️ array — 全球资产反应，5-6项
    {
      "name": "string",                     // ⚠️ 资产名（标普500/纳斯达克/恒生科技/黄金/10Y美债/BTC）
      "value": "string",                    // ⚠️ 涨跌幅或绝对值（如 "+0.87%" 或 "4.23%"）
      "direction": "string"                 // ⚠️ 枚举：up / down / flat
    }
  ],

  "coreJudgments": [                        // ⚠️ array — 三大判断，精确3条
    {
      "title": "string",                    // ⚠️ 判断标题，10-30字
      "confidence": 85,                     // ⚠️ number — 置信度百分比，30-95
      "logic": "string"                     // ⚠️ 推理逻辑链，20-60字
    }
  ],

  "actions": {                              // ⚠️ object — 行动建议
    "today": [                              // ⚠️ array — 今日建议，1-3条
      {
        "type": "string",                   // ⚠️ 枚举：buy / sell / hold / bullish / bearish
        "content": "string"                 // ⚠️ 具体可执行建议，纯文本
      }
    ],
    "week": [                               // array — 本周建议，0-3条（可为空数组）
      {
        "type": "string",
        "content": "string"
      }
    ]
  },

  "sentimentScore": 62,                     // ⚠️ number — 0-100 情绪分数
  "sentimentLabel": "偏贪婪",                // ⚠️ string — 枚举：极度恐惧/偏恐惧/中性/偏贪婪/贪婪/极度贪婪
  "marketSummary": "string",                // ⚠️ 50-150字市场总结，纯文本，禁止 **加粗** markdown

  "smartMoney": [                           // ⚠️ array — 聪明钱速览，2-4条
    {
      "source": "string",                   // ⚠️ 机构名（如 "桥水基金"/"北向资金"）
      "action": "string",                   // ⚠️ 具体操作（如 "增持中国ETF约$2.3亿"）
      "signal": "string"                    // ⚠️ 枚举：bullish / bearish / neutral
    }
  ],

  "riskNote": "string",                     // ⚠️ 30-100字风险提示，纯文本，禁止表格语法
  "dataTime": "2026-04-01 09:00 BJT"        // ⚠️ string — 数据截止时间
}
```

**组件对齐清单**：

| 小程序组件 | JSON 字段 | 数组长度要求 | 特殊规则 |
|---|---|---|---|
| 核心事件标题 | `coreEvent.title` | — | 纯文本，无 emoji |
| 事件链 dot→arrow | `coreEvent.chain[]` | 3-6条 | 每条独立语句，禁止 `\|` |
| 全球资产 6 格卡片 | `globalReaction[]` | 5-6项 | 固定6项：标普/纳指/恒科/黄金/10Y美债/BTC |
| 核心判断×3 + 置信度条 | `coreJudgments[]` | 精确3条 | confidence 必须是 number |
| 行动建议 tag+content | `actions.today/week` | today 1-3, week 0-3 | type 枚举严格 |
| 情绪仪表盘圆环 | `sentimentScore` + `sentimentLabel` | — | score 是 number |
| 市场总结文本 | `marketSummary` | — | 纯文本 |
| 聪明钱卡片 | `smartMoney[]` | 2-4条 | signal 枚举严格 |
| 风险提示底部 | `riskNote` | — | 纯文本 |

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
      "sparkline": [5180, 5195, 5220, 5210, 5235, 5248, 5254], // ⚠️ number[] — 7天
      "note": "科技股领涨，AI板块表现强势"   // string — 仅第1条(标普500)有note，其余无此字段
    }
  ],
  // usMarkets 精确4项顺序：标普500(+note) / 纳斯达克 / 道琼斯 / VIX
  // changeLabel 对应：大盘指数 / 科技指数 / 蓝筹指数 / 恐慌指标

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

  "asiaMarkets": [                          // ⚠️ array — 4-6项
    {
      "name": "上证指数",                    // ⚠️ string
      "price": "3,041.17",                  // ⚠️ string
      "change": 0.24,                       // ⚠️ number
      "sparkline": [3020, 3025, 3030, 3028, 3035, 3040, 3041] // ⚠️ number[]
    }
  ],
  // asiaMarkets 推荐6项：上证/深证/恒生指数/恒生科技/日经225/KOSPI

  "commodities": [                          // ⚠️ array — 精确6项
    {
      "name": "黄金 XAU",                   // ⚠️ string
      "price": "$2,213.40",                 // ⚠️ string
      "change": 1.09,                       // ⚠️ number
      "sparkline": [2190, 2195, 2200, 2205, 2210, 2215, 2213] // ⚠️ number[]
    }
  ],
  // commodities 精确6项：黄金/布伦特原油/WTI原油/美元指数DXY/10Y美债/离岸人民币CNH

  "cryptos": [                              // ⚠️ array — 1-3项
    {
      "name": "比特币 BTC",                  // ⚠️ string
      "price": "$70,215",                   // ⚠️ string
      "change": 1.95,                       // ⚠️ number
      "sparkline": [68000, 68500, 69000, 69200, 70000, 70100, 70215] // ⚠️ number[]
    }
  ],
  // cryptos 推荐：BTC / ETH(可选) / SOL(可选)

  "gics": [                                 // ⚠️ array — 精确11项，按涨跌幅降序
    {
      "name": "信息技术 XLK",                // ⚠️ string — 格式："中文名 ETF代码"
      "change": 1.82,                       // ⚠️ number
      "etf": "XLK"                          // ⚠️ string
    }
  ]
  // gics 精确11项：XLK/XLC/XLY/XLI/XLF/XLV/XLB/XLP/XLU/XLRE/XLE
}
```

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

**metrics 6项标准**：

| # | label | 数据来源 | 格式示例 |
|---|-------|---------|---------|
| 1 | PE(TTM) | Google Finance / StockAnalysis | "72.5x" |
| 2 | 市值 | Google Finance | "$2.3T" / "HK$3.5T" / "¥6850亿" |
| 3 | 营收增速 | 最近季度/年度同比 | "+265%" |
| 4 | 毛利率 | 最近季度 | "76.0%" |
| 5 | ROE | TTM | "91.5%" |
| 6 | 评级 | 综合评价 | "⭐⭐⭐⭐⭐" (1-5星) |

---

## 四、radar.json — 雷达页

**对应页面**：`pages/radar/radar.wxml` + `radar.js`
**涵盖模块**：红绿灯信号、风险评分、监控阈值、风险预警、事件日历、异动监测、聪明钱三梯队

```jsonc
{
  "date": "2026-04-01",                    // ⚠️ string

  "trafficLights": [                        // ⚠️ array — 精确7项
    {
      "name": "VIX波动率",                   // ⚠️ string
      "value": "13.0",                      // ⚠️ string — 精确数值
      "status": "green",                    // ⚠️ string — 枚举：green / yellow / red
      "threshold": "<18绿 / 18-25黄 / >25红" // ⚠️ string — 阈值说明
    }
  ],
  // trafficLights 精确7项顺序：
  // VIX波动率 / 10Y美债收益率 / 布伦特原油 / 美元指数DXY / HY信用利差 / 北向资金 / 离岸人民币CNH

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

  "dataTime": "2026-04-01 09:00 BJT"       // ⚠️ string
}
```

**红绿灯阈值标准**：

| # | 指标 | 🟢 green | 🟡 yellow | 🔴 red |
|---|------|----------|-----------|--------|
| 1 | VIX | <18 | 18-25 | >25 |
| 2 | 10Y美债 | <4.0% | 4.0-4.5% | >4.5% |
| 3 | 布伦特原油 | <$90 | $90-110 | >$110 |
| 4 | DXY | <102 | 102-107 | >107 |
| 5 | HY信用利差 | <4% | 4-5% | >5% |
| 6 | 北向资金 | 净流入 | 小幅流出 | 大幅流出(>100亿) |
| 7 | 离岸人民币CNH | <7.15 | 7.15-7.30 | >7.30 |

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

---

> v1.1 — 2026-04-01 | 老板直推级数据治理升级：交易数据字段强制直连行情源；`dataTime` 要显式写清分市场时点；watchlist `metrics` 改为6项可验证指标集合；删除 sparkline 估算逻辑。\n> v1.0 — 2026-04-01 | 初始版本。基于小程序 `touyanduck_appid` 的4个页面 + 5个组件逐行审查，精确定义每个字段类型、必填性、枚举范围和数组长度要求。
