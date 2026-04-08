# JSON Schema 完整字段规范（v4.6）

> **用途**：定义投研鸭小程序 4 个 JSON 文件的精确字段规范。每个字段都对应小程序前端组件的一个渲染点。
> **核心原则**：Schema 即契约。JSON 生成阶段必须逐字段对照本文件，不允许新增/缺失/改名字段。
> **字段类型约定**：`string` = 字符串，`number` = 数字（非字符串），`array` = 数组，`object` = 对象
> **必填标记**：⚠️ = 必填（不允许为空字符串/空数组/null）；🔸 = 可选（省略时前端 `wx:if` 跳过，不渲染对应模块）
>
> **v4.6 变更**（2026-04-08）：topHoldings 从"2-4条"升级为"≥3条"硬约束（回归门禁 R1）；smartMoneyHoldings positions 从"推荐Top10"升级为"≥Top10"硬约束（回归门禁 R2）；新增 holdings-cache.json 引用规则

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
  "takeaway": "string",                     // 🔸 string — 30-80字，一句话宏观结论
  // 【定位】：发生了什么 + 为什么重要（非操作建议）。价投视角，有立场有条件。
  // 【标红】：3-5个【】关键词，前端 parseTakeaway() 渲染红色高亮
  // 【禁止】：操作指令（"建议维持仓位"等）→ 统一在 actionHints；标红≥6个失去重点
  // 正确："上周美股结束【5周连跌】首次反弹，但【油价$109】固化通胀预期——本周【CPI】是决定性变量"

  "coreEvent": {                            // ⚠️ object — 核心事件
    "title": "string",                      // ⚠️ 20-50字（精简优先），纯文本，禁止 markdown/emoji
    // 只抓 1-2 个核心矛盾，与 takeaway 形成「标题→结论」层次
    // 正确："美股反弹遇上油价暴涨——本周CPI将裁决反弹真伪"（26字，2矛盾）
    // ===== v1.7 升级：chain 从 string[] 改为 object[] =====
    // ===== v4.5 增强：新增 source_count 多源交叉验证标记 =====
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
        // ⚠️ 付费墙媒体（Bloomberg / FT / WSJ）及机构付费终端（Newsquawk / Refinitiv 等）：
        //   source 标注"Newsquawk（机构终端）"等，url 填官网首页或不填
        //   前端对无 url 的来源自动显示为灰色不可点文字（chain-link-no-url 样式）
        "url": "string",                    // 🔸 string — 完整 https 公开可访问链接（中国大陆可访问优先）；付费墙/机构终端内容可填官网首页或不填
        "source_count": 1                   // 🔸 number — v4.5 新增：该事件被多少个独立来源报道（默认1）
        // source_count 含义：1=单一来源 / 2-3=多源交叉初步确认 / 4+=广泛报道已确认事实
        // 用于 ClawHub Skill 展示证据强度：source_count≥3 显示 ◆(强) / 2 显示 ◇(中) / 1 显示 ○(弱)
        // 获取方式：在搜索事件时，统计不同媒体来源的报道数量
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
      // 【强制】：短句 + →（箭头）三段式：触发原因 → 传导路径 → 核心结论（每段≤15字，整条≤50字）
      // 正确："停火遭否认，IRGC升级威胁 → 每周冲突油价+$2~4（高盛）→ 油价中枢系统性上移"
      // 【禁止】：段落散文、分号长句、bullet点列举
      // 前端渲染：.logic-text 无图标前缀，文字直接顶格
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

  // ===== v5.0 重构：聪明钱建议模块（原决策建议）=====
  // 设计理念：大老板偏低频价值投资（巴菲特/段永平风格），不需要每天的买卖建议
  // 模块标题：⚡ 聪明钱建议
  // 布局顺序：actionHints（置顶）→ smartMoney（聪明钱动向）→ topHoldings（重点持仓）

  "actionHints": [                            // 🔸 array — 操作提示，0-2条（可选，无高置信机会时为空数组[]，前端不渲染此区域）
    {
      "type": "string",                       // ⚠️ 枚举（具体操作动词）：hold（持有）/ add（加仓）/ reduce（减仓）/ buy（买入）/ sell（卖出）/ watch（关注）/ hedge（对冲）/ stoploss（止损）
      // ⚠️ 禁止使用 bullish / bearish — 这是方向判断，不是具体操作指令
      "content": "string",                    // ⚠️ 具体可执行建议，含标的+条件+理由，纯文本
      // 正确示例："段永平4/4亲赴Westfield门店调研泡泡玛特，称right business——信号极强，值得纳入观察池深入研究"
      "reason": "string"                      // 🔸 string — ≤40字，说明建议理由/数据锚点
    }
  ],
  // ===== v5.0 actionHints 产出哲学 =====
  // 价投风格低频精而少。大多数日子为空 []，仅极高置信机会才填入。
  // 禁止凑数（"维持不变"/"持续关注"），type=buy/sell 仅极端场景使用。
  // 向后兼容：前端 JS 同时支持旧 actions.today/week 格式

  "sentimentScore": 62,                     // ⚠️ number — 0-100 情绪分数
  // 基于 VIX/Put-Call/信用利差等多维度独立综合打分，禁止机械对齐 CNN F&G（允许±15分偏差）
  "sentimentLabel": "偏贪婪",                // ⚠️ string — 枚举（强制映射）：
  //   0-20→极度恐惧 / 21-40→偏恐惧 / 41-60→中性 / 61-75→偏贪婪 / 76-90→贪婪 / 91-100→极度贪婪
  // 禁止非枚举值（如「偏悲观」「偏乐观」）
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

  "smartMoney": [                           // ⚠️ array — 聪明钱动向（边际动作），2-4条
    {
      "source": "string",                   // ⚠️ 机构名（如 "桥水基金"/"北向资金"）
      "action": "string",                   // ⚠️ 具体操作（如 "增持中国ETF约$2.3亿"）
      "signal": "string"                    // ⚠️ 枚举：bullish / bearish / neutral
    }
  ],

  // ===== v5.0 新增：重点持仓（聪明钱配置参考）=====
  "topHoldings": [                          // ⚠️ array — 聪明钱重点持仓快照，**≥3条**（v7.5 从"2-4条"升级为硬约束：伯克希尔+段永平+ARK旗舰缺一不可）
    {
      "name": "string",                     // ⚠️ 机构/KOL名称，简洁直接（如"伯克希尔"、"段永平"、"ARK旗舰"）
      // ⚠️ 禁止冗余后缀：不写"TOP5"/"已知持仓"等，名字本身就是最好的标签
      "holdings": "string"                  // ⚠️ 一行式持仓概要，格式：标的+占比 用 | 分隔，末尾可加补充说明
      // 正确示例："AAPL 28% | BAC 12% | AXP 10% | KO 9% | CVX 7% · 现金$3733亿"
      // 正确示例："AAPL | GOOG | PDD · 泡泡玛特观察中"
      // 正确示例："TSLA 12% | CRWV 8% | COIN 7% | ROKU 6% | PLTR 5%"
    }
  ],
  // ===== topHoldings 规则 =====
  // 低频更新：季度13F（2/5/8/11月中旬）刷新；中间只微调（如段永平确认建仓泡泡玛特）
  // 缓存引用：非13F窗口 → 引用 holdings-cache.json；13F窗口 → web_search 查证并更新缓存
  // 四条铁律（v5.0 致命级）：
  //   ①必须查证（web_search 权威源，禁止凭记忆） ②交叉一致（先写radar详版→提取briefing简版）
  //   ③严格降序（按权重排） ④宁缺毋错（港股不适用13F）

  "riskPoints": [                          // ⚠️ array — 风险提示 bullet point，2-3条，取代旧版 riskNote
    "string"                                // ⚠️ 每条15-50字，一个独立风险点，纯文本
    // 每条聚焦「风险 + 触发条件 + 影响方向」，**禁止操作建议**（统一在 actionHints）
    // 正确：["油价$109近红灯，若霍尔木兹持续受限布伦特可能突破$115", "CPI预期3.8%叠加汽油月涨36%"]
    // 禁止：["...建议维持6成仓位+能源对冲"]
  ],
  "riskNote": "string",                     // 🔸 旧版兼容字段——30-100字风险提示散文，纯文本。新版产出时仍保留此字段作为 fallback，但前端优先渲染 riskPoints 数组
  // ⚠️ v3.7：riskNote 同样禁止包含操作建议（与 riskPoints 保持一致），只描述风险本身
  "dataTime": "2026-04-01 09:00 BJT",       // ⚠️ string — 格式固定为 "YYYY-MM-DD HH:MM BJT"，四个JSON保持完全一致，与简报页顶部时间同步

  // ===== v1.4 新增：语音播报 =====
  "audioUrl": "cloud://cloud1-xxx/audio/briefing-2026-04-01.mp3",  // 🔸 string — 音频文件的云存储 fileID（cloud:// 格式）或 https URL，由 generate_audio.py + upload_to_cloud.py 自动生成和填充
  "audioFile": "briefing-2026-04-01.mp3",    // 🔸 string — 音频文件名（本地标记，上传后自动替换为 audioUrl）
  "voiceText": "string",                     // 🔸 string — 播报文稿原文（调试用，前端不直接使用）

  // ===== v1.3 新增：元数据 =====
  "_meta": {                                // 🔸 object — 元数据（可选，无则前端不显示来源标签）
    "sourceType": "heavy_analysis",         // 🔸 string — 枚举：heavy_analysis / refresh_update（v7.0新增）/ realtime_quote / breaking_news / weekend_insight（v4.0新增）
    "generatedAt": "2026-04-01T09:00:00+08:00",  // 🔸 string — ISO 8601 生成时间
    "skillVersion": "v4.0",                 // 🔸 string — 生产此数据的 Skill 版本号
    "refreshCount": 1                       // 🔸 number — Refresh 模式专用：当天第几次 Refresh（1/2/3...）。Heavy/Weekend 模式不填此字段。前端不渲染，仅用于调试追溯
  }
}
```

**组件对齐清单**：

| 小程序组件 | JSON 字段 | 数组长度要求 | 特殊规则 |
|---|---|---|---|
| 时间状态栏（v1.3） | `timeStatus` | — | 可选模块，前端也可自行计算时区 |
| 今日核心结论（v1.7）| `takeaway` | — | 可选；30-80字，有立场有行动方向 |
| 核心事件标题 | `coreEvent.title` | — | 纯文本，无 emoji，20-50字聚焦1-2个矛盾（v3.7精简） |
| 事件链卡片（v1.7） | `coreEvent.chain[]` | 3-6条 | **对象数组**：title（必填）+ brief（可选）+ source（可选）+ url（可选，有则可点击） |
| 全球资产 6 格卡片（v1.7） | `globalReaction[]` | 5-6项 | 固定6项；新增可选 `note` 字段（≤15字解读） |
| 核心判断×3 + 置信度条 | `coreJudgments[]` | 精确3条 | confidence 必须是 number |
| 判断扩展：决策者/参考源/概率/趋势（v1.3→v1.3.1） | `coreJudgments[].keyActor/references/probability/trend` | — | 全部可选；references 支持 string[] 旧格式和 object[] 新格式（含 name/summary/url） |
| ⚡ 聪明钱建议 — 操作提示（v5.0） | `actionHints[]` | 0-2条（可为空） | **v5.0 新增，替代旧 actions**；无高置信机会时为空数组，前端不渲染；向后兼容旧 actions 格式 |
| ⚡ 聪明钱建议 — 聪明钱动向（v5.0） | `smartMoney[]` | 2-4条 | signal 枚举严格；**v5.0 从子区域提升为聪明钱建议模块主体** |
| ⚡ 聪明钱建议 — 重点持仓（v5.0） | `topHoldings[]` | **≥3条**（v7.5硬约束） | **v5.0 新增**；一行式持仓概要，低频更新（季度13F）；v7.5 升级为必填≥3条（伯克希尔+段永平+ARK旗舰） |
| 情绪仪表盘圆环 | `sentimentScore` + `sentimentLabel` | — | score 是 number |
| 市场情绪 bullet list（v1.8） | `marketSummaryPoints[]` | 3-5条 | 每条15-40字独立观察点；旧版 `marketSummary` 字符串兼容（前端自动拆分） |
| 🛡️ 风险情绪 — 风险点（v5.0 标题精简+规则强化） | `riskPoints[]` + `riskNote`(兼容) | 2-3条 | **v5.0 禁止包含操作建议**；前端 🛡️ 图标 + bullet point 渲染 |
| 数据状态栏（v1.3） | `_meta` | — | 可选，控制底栏来源标签和版本号显示 |
| 语音播报（v1.4） | `audioUrl` / `audioFile` / `voiceText` | — | 可选；`audioUrl` 由脚本自动填充，前端时间状态栏显示🔊按钮 |

---

**简报页质量基线门禁（v4.1 固化 — 每次产出 briefing.json 必须逐项自查）**：

> **设计原则**：简报页是大老板每天第一眼看到的页面，takeaway+coreEvent+coreJudgments 构成核心决策信息。以下基线是 v4.1 确认的质量水平（以 2026-04-06 版为黄金样本），后续迭代只允许在此基础上提升，禁止退化。

| # | 质量维度 | 基线要求 | 自查方法 |
|---|---------|---------|---------|
| **B1** | **takeaway 有立场有标红** | 30-80字，含条件判断（"如果X则Y"），3-5个【】标红关键词；禁止操作建议 | 检查【】数量（3-5）、是否有"建议/仓位"违禁词 |
| **B2** | **coreEvent.title 精简聚焦** | 20-50字，只抓1-2个核心矛盾；与 takeaway 形成「标题→结论」层次 | 计字数、数信息点（≤2） |
| **B3** | **chain 来源链接完整** | 每条 chain：非付费墙 source 必须有 https url；3-6条 | 逐条检查 url 非空（付费墙除外） |
| **B4** | **coreJudgments 三段式** | 精确3条；logic 必须是「触发→传导→结论」箭头格式（≤50字）；每条有 references | 检查 → 符号、references 非空 |
| **B5** | **globalReaction 精确数值** | 5-6项；value 无 `~` `≈` 模糊前缀；direction 枚举合规 | 正则扫描模糊前缀 |
| **B6** | **actionHints 价投风格** | 0-2条（大多数日子为空数组）；type 使用操作动词（非 bullish/bearish）；不凑数 | 检查 type 枚举 + 有无"维持不变"废话 |
| **B7** | **riskPoints 去操作化** | 2-3条纯风险描述；禁止"建议/仓位/对冲"等操作词 | 正则扫描操作违禁词 |
| **B8** | **sentimentScore 独立判断** | 基于 VIX/Put-Call/信用利差综合打分；sentimentLabel 严格对应 score 区间 | 查表验证 score→label 映射 |
| **B9** | **smartMoney 有具体动作** | 2-4条；每条有具体数字/操作/信号；数字可追溯到搜索来源 | 逐条检查信息量 |
| **B10** | **topHoldings 数据查证** | 与 radar.smartMoneyHoldings 交叉一致；权重降序；数字来自 13F 查证 | briefing vs radar 比对 |
| **B11** | **marketSummaryPoints 不重复** | 3-5条 bullet；不重复 coreEvent/globalReaction 中的具体涨跌幅数字 | 检查与其他模块的数字重叠 |
| **B12** | **整体产出哲学** | 所有文字字段面向价投决策者（巴菲特/段永平风格），有立场有论据；无空洞废话；无 markdown 残留 | 自问："大老板读完能做判断吗？" |

> **门禁执行时机**：第2.5阶段 JSON 终审时，briefing.json 必须额外过一遍上述 B1-B12。任何一项不通过则退回修正。

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

  "gicsInsight": "板块轮动明显，科技/通信领涨反映AI主线延续，能源/房地产承压显示市场偏好成长股"  // ⚠️ string — GICS板块一句话洞察，30-80字。前端用 gicsInsightChain"轮动"节点渲染摘要，此字段为兜底
}
```

**板块 Insight 规范（决策信号式写法）**：

> 大老板是低频价值投资者。Insight 必须回答"对价投意味着什么"——非盘面复述。30-80字，含关键数字+信号判断。

| 维度 | 错误（新闻摘要）❌ | 正确（决策信号）✅ |
|------|------------------------|------------------------|
| usInsight | "三大指数周涨3-4%，科技股领涨" | "SPX反弹至5570但VIX仍在23+，反弹结构脆弱——只有VIX回落至20以下才确认趋势反转" |
| m7Insight | "NVDA涨5%领涨，TSLA跌3%" | "NVDA Blackwell出货验证但PE仍50x，TSLA交付连续两季不及预期——分化加剧，个股选择比板块配置更关键" |
| commodityInsight | "油价涨至$109，黄金突破$4600" | "布伦特$109逼近红灯（>$110），若持续将固化通胀预期、收窄降息空间——直接影响全年权益估值中枢" |

---

**市场页质量基线门禁（v4.4 固化 — 每次产出 markets.json 必须逐项自查）**：

> **设计原则**：市场页是大老板最高频查看的页面（每天看多次），质量必须稳如磐石。以下基线是 v4.4 确认的质量水平，后续迭代只允许在此基础上提升，禁止退化。

| # | 质量维度 | 基线要求 | 自查方法 |
|---|---------|---------|---------|
| **Q1** | **数据完整性** | 5个Tab全部有数据：美股4项+M7精确7项+亚太4-6项+大宗精确6项+加密1-3项+GICS精确11项 | 逐Tab检查数组长度 |
| **Q2** | **6条 Insight 全部非空** | 每个Tab摘要条都有内容（30-80字），不允许任何一个 Insight 为空字符串 | 逐条检查长度 |
| **Q3** | **Insight 是决策信号而非新闻摘要** | 每条 Insight 必须回答"对价投决策者意味着什么"，含关键数字+信号判断+条件/阈值。禁止纯盘面复述（如"三大指数上涨"） | 自问：大老板读完这句话能做出判断吗？如果只是"知道发生了什么"而无法"判断该不该关注"，就是不合格 |
| **Q4** | **sparkline 与 price 一致** | 每个标的的 `sparkline[-1]` 与 `price` 数值偏差 ≤1% | 逐个标的比对（重点关注脚本补全后的数据） |
| **Q5** | **GICS 热力图有摘要** | `gicsSummarySegments` 非空——热力图顶部有一句话轮动摘要，不是光秃秃的条形图 | 检查 gicsInsightChain 或 gicsInsight 非空 |
| **Q6** | **数字全部实时查证** | 所有 price/change 来自行情源，非 AI 记忆（RULE ZERO）。特别关注：离岸人民币CNH、VIX、10Y美债——这三个容易凭记忆写错 | 自查三问（见全局基础铁律） |
| **Q7** | **枚举值合规** | changeLabel 只允许 `大盘指数/科技指数/蓝筹指数/恐慌指标`；GICS 精确11个ETF代码 | 逐项校验 |
| **Q8** | **前端渲染无异常** | M7 header 只有一行（`🏆 Magnificent Seven`，无副标题）；Tab indicator 为圆点；摘要条高亮正确 | 小程序模拟器视觉检查 |

> **门禁执行时机**：第2.5阶段 JSON 终审时，markets.json 必须额外过一遍上述 Q1-Q8。任何一项不通过则退回修正。

---

**板块 insightChain 规范（v4.4 降级为可选）**：

> **v4.4 状态**：前端已不渲染因果链卡片。仅 `gicsInsightChain` 的"轮动"节点被前端提取为热力图一句话摘要。数据层保留完整结构供搜索覆盖，但非必填。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `usInsightChain` | array | 🔸 | 3条 `{ icon, label, text }`，前端不渲染 |
| `m7InsightChain` | array | 🔸 | 同上 |
| `asiaInsightChain` | array | 🔸 | 同上 |
| `commodityInsightChain` | array | 🔸 | 同上 |
| `cryptoInsightChain` | array | 🔸 | 同上 |
| `gicsInsightChain` | array | 🔸 | 3条同上。前端提取 label="轮动" 节点的 text 作为热力图摘要；缺失时降级到 `gicsInsight` |

**insightChain 节点字段**：`icon`(1个emoji) + `label`(≤4字) + `text`(15-35字完整短句)

**数字一致性规则**：insightChain[].text 中的数字必须与对应板块 `price`/`change` 一致，先填数据字段再写文字。

**sparkline 生成规则**：
- 7 个数据点代表近 7 个交易日收盘价（真实历史序列）
- 数据来源：AkShare 新浪源+东方财富 fallback（脚本第三阶段自动补全）
- **禁止估算/插值/模拟波动生成**（v1.2起强制阻断），sparkline 缺失时回采重试，仍失败则阻断发布
- **⚠️ v4.4 新增：sparkline 与 price 一致性校验**：`sparkline` 最后一个数据点必须与 `price` 字段的数值一致（允许千分位/货币符号格式差异，但数值偏差不超过 1%）。典型事故：AAPL price 显示 `$223.45`，但 sparkline 最后一个点是 `255.92`——差 14.5%，严重损伤数据可信度。自查：逐个标的比对 `sparkline[-1]` 与 `price` 数值，不一致则修正 sparkline 或 price

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
| 1 | 最新价 | AkShare/Google Finance 实时价 | `"$174.40"` | **string**（含货币符号） | 自动计算 |
| 2 | 单日涨跌 | 当日 close vs prev close | `"+5.59%"` | **string**（含正负号和%） | 自动计算 |
| 3 | 7日涨跌 | last7[0] → last7[-1] | `"-0.71%"` | **string**（含正负号和%） | 自动计算 |
| 4 | 30日涨跌 | last30[0] → last30[-1] | `"-7.22%"` | **string**（含正负号和%） | 自动计算 |
| 5 | PE(TTM) | `StockAnalysis / web_search` | `"53.4x"`（无数据则`"—"`） | **string** | 辅助指标，缺失不阻断 |
| 6 | 综合评级 | `calc_star_rating()` 规则函数 | `"⭐⭐⭐⭐"` | **string** | 规则化自动计算 |

> **⚠️ 格式强制规范**：metrics 第1项必须含货币符号（`"$"` 或 `"HK$"` 或 `"¥"`）；第2-4项必须含正负号和 `%` 后缀；全部6项的 `value` 字段必须为 **string 类型**。

> **评级规则**（`calc_star_rating(change, pct_30d)`）：
> - ⭐⭐⭐⭐⭐：30日涨超+15% 且 单日为正
> - ⭐⭐⭐⭐  ：30日涨+5%~+15%，或单日涨超+3%
> - ⭐⭐⭐    ：30日在-5%~+5%（震荡整理）
> - ⭐⭐      ：30日跌-5%~-15%
> - ⭐        ：30日跌超-15%（深度回调）

---

**标的页质量基线门禁（v4.2 固化 — 每次产出 watchlist.json 必须逐项自查）**：

> **设计原则**：标的页是大老板定期精选观察池，质量必须稳如磐石。以下基线是 v4.2 确认的质量水平（以 2026-04-06 版为黄金样本），后续迭代只允许在此基础上提升，禁止退化。

| # | 质量维度 | 基线要求 | 自查方法 |
|---|---------|---------|---------|
| **W1** | **板块完整性** | 4个核心板块（ai_infra/ai_app/cn_ai/smart_money）每个 stocks 数组非空且≥2只标的；hot_topic 无事件时可省略或空数组 | 逐板块检查 stocks 数组长度 |
| **W2** | **每只标的字段完整** | 已上市标的必须含：name/symbol/change(number)/price/listed(true)/tags(2个)/reason/analysis/metrics(6项)/risks(2-3条)/sparkline(7)/chartData(30)，全部非空 | 逐标的扫描空值 |
| **W3** | **analysis 质量** | 2-3段（100-300字），含 ①当前业务亮点+关键数据 ②近期催化剂/事件 ③风险/估值判断。禁止泛泛空话 | 自问："大老板读完能判断该不该关注这只标的？" |
| **W4** | **reason 有论据** | 20-60字，必须含结论+论据，禁止"是一家好公司"式空洞表达 | 检查是否含具体数据/事件/逻辑 |
| **W5** | **tags 精准** | 每个标的2个 tag，每个4-8字。第一个=行业定位/核心能力，第二个=当期催化剂/最新动态（随行情更新） | 检查 tag 数量和时效性 |
| **W6** | **metrics 一致性** | metrics[0].value 与 price 一致；metrics[1].value 与 change 一致（含正负号+%）；综合评级按 calc_star_rating 公式计算 | 逐标的比对 price⟷metrics[0]、change⟷metrics[1] |
| **W7** | **sectors summary 有数据** | 每个板块 summary 含具体涨跌数字+核心驱动力+后续关注点（2-3句话），禁止"板块表现不错"式空话 | 检查 summary 是否含数字 |
| **W8** | **sparkline[-1] 与 price 偏差≤1%** | 与市场页 Q4 同一标准——sparkline 最后一个点与 price 数值偏差不超过 1% | 逐标的比对（重点关注脚本补全后数据） |
| **W9** | **risks 独立具体** | 每条风险15-50字，一条只讲一个风险点；禁止"市场风险"等泛泛表述 | 逐条检查独立性和具体性 |

> **门禁执行时机**：第2.5阶段 JSON 终审时，watchlist.json 必须额外过一遍上述 W1-W9。任何一项不通过则退回修正。

---

## 四、radar.json — 雷达页

**对应页面**：`pages/radar/radar.wxml` + `radar.js`
**版本**：v3.3（2026-04-05，对应前端 radar.js v7.0 / radar.wxml v7.0）
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
  // ⚠️ riskAdvice v5.4 升级规范（详见 SKILL.md §2.3）：
  //   必须：①点名 1-2 项最危险指标说清楚危险在哪 ②底层指标释放明确信号时可综合判断情绪方向，禁止机械引用 F&G 单一指标值 ③指向本周最关键催化剂/时间节点
  //   禁止：套模板（"当前风险评分X（Y）"开头）、模糊建议（"保持谨慎"）、操作建议（仓位/加仓/减仓/对冲等——统一在 actionHints 中覆盖）
  //   正确示例："黄金$4,627亮红灯（避险情绪极端），布伦特$109逼近红灯区间——若周四CPI确认通胀二次抬头，当前反弹基础将被抽空。"
  //   错误示例（禁止）："布伦特$109叠加F&G仅19，建议维持5成仓位+能源对冲。"（机械引用F&G+含操作建议）
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
  "smartMoneyHoldings": [                   // ⚠️ array — ≥2个投资人/机构持仓快照（v7.5 从可选升级为必填：伯克希尔+段永平必须存在，ARK旗舰强烈推荐）
    {
      "manager": "巴菲特 · 伯克希尔",       // ⚠️ string — 投资人/机构名称
      "fund": "Berkshire Hathaway",         // 🔸 string — 基金/公司英文名
      "aum": "$294.3B",                    // 🔸 string — 总持仓市值（13F披露口径）
      "asOf": "2025Q4 · 2月披露",           // ⚠️ string — 数据截止时间+披露时间（让读者知道数据有延迟）
      "positions": [                        // ⚠️ array — 头部持仓，**≥Top10**（v7.5 从"推荐Top10"升级为硬约束，按占比降序）。默认折叠展示，不占空间
      // ⚠️ v7.5 缓存引用规则：非13F窗口期直接引用 holdings-cache.json 的 positions 数组，禁止凭记忆修改权重
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
    "sourceType": "heavy_analysis",         // 🔸 string — 枚举：heavy_analysis / refresh_update（v7.0新增）/ realtime_quote / breaking_news / weekend_insight
    "generatedAt": "2026-04-01T09:00:00+08:00",  // 🔸 string — ISO 8601
    "skillVersion": "v4.4"                  // 🔸 string — Skill 版本号
  }
}
```

**红绿灯阈值标准与 riskScore 计算**：

> **唯一权威源** → [formulas.md](formulas.md)（红绿灯7项阈值表+riskScore公式+riskLevel分级）
> **机器可执行版本** → [golden-baseline.json](golden-baseline.json) 的 `trafficLightThresholds` + `riskScoreFormula`
>
> **快速参考**：green=0分/yellow=10分/red=20分，基础分30，封顶100。<45=low / 45-64=medium / ≥65=high。

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

### 5.0 全局数据查证铁律（最高优先级）

> **🚨 禁止 AI 凭训练数据中的模糊记忆直接输出任何数字。所有 4 个 JSON 中出现的每一个数字，都必须来自当期实时搜索/查证。**

本规则适用于全部 JSON 字段中的所有数值类数据，包括但不限于：价格（price）、涨跌幅（change）、汇率、持仓权重（weight）、估值指标（PE）、AUM、目标价、预测概率、资金流金额、宏观数据（CPI/利率/信用利差）等。

**自查三问**：①这个数字来自本次执行的哪次搜索？②搜索结果原文怎么写的？③时间戳是否在合理范围内？——任一答不上来→该数字必须重新搜索核实。

**宁缺毋错**：查不到确切数据时标注"待更新"或省略，绝不编造数字。

详见 SKILL.md「全局基础铁律」完整说明。

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
| `actionHints[].type` | `hold`, `add`, `reduce`, `buy`, `sell`, `watch`, `hedge`, `stoploss`（**禁止 `bullish` / `bearish`**） |
| `smartMoney[].signal` | `bullish`, `bearish`, `neutral` |
| `sentimentLabel` | `极度恐惧`, `偏恐惧`, `中性`, `偏贪婪`, `贪婪`, `极度贪婪`（score→label映射见§1注释） |
| `sectors[].id` | `ai_infra`, `ai_app`, `cn_ai`, `smart_money`, `hot_topic` |
| `sectors[].trend` | `up`, `down`, `hold` |
| `trafficLights[].status` | `green`, `yellow`, `red` |
| `riskLevel` | `low`, `medium`, `high` |
| `riskAlerts[].level` | `high`, `medium`, `low` |
| `events[].impact` | `high`, `medium`, `low` |
| `alerts[].level` | `danger`, `warning`, `info` |
| `smartMoneyDetail[].tier` | `T1旗舰`, `T2成长`, `策略师观点` |
| `smartMoneyDetail[].funds[].signal` | `bullish`, `bearish`, `neutral` |
| `smartMoneyDetail[].funds[].freshness` | `本周`, `上周`, `本月` |
| `usMarkets[].changeLabel` | `大盘指数`, `科技指数`, `蓝筹指数`, `恐慌指标` |
| `timeStatus.marketStatus` | `美股交易中`, `美股已收盘`, `盘前交易`, `盘后交易`, `美股休市` |
| `coreJudgments[].probability` | `高可能性`, `中可能性`, `低可能性` |
| `coreJudgments[].trend` | `上升`, `下降`, `稳定` |
| `predictions[].trend` | `up`, `down`, `stable` |
| `predictions[].source` | `Polymarket`, `Kalshi`, `CME FedWatch` |
| `_meta.sourceType` | `heavy_analysis`, `refresh_update`, `realtime_quote`, `breaking_news`, `weekend_insight` |

---

> v4.6 — 2026-04-08 | **持仓字段硬约束升级（回归门禁 R1-R8 配套）**：①`topHoldings` 从"🔸可选2-4条"升级为"⚠️必填≥3条"（伯克希尔+段永平+ARK旗舰缺一不可）；②`smartMoneyHoldings` 从"🔸可选"升级为"⚠️必填"（伯克希尔+段永平必须存在）；③`positions` 从"推荐Top10"升级为"≥Top10硬约束"；④新增 `holdings-cache.json` 引用规则（非13F窗口期直接引用缓存，禁止凭记忆修改权重）
> v4.5 — 2026-04-07 | `coreEvent.chain[]` 新增 `source_count` 可选字段（多源交叉验证标记）：①`refreshInterval` 新增 Refresh 模式说明（"每4小时更新"）；②`_meta` 新增 `refreshCount` 可选字段（当天第几次 Refresh，调试追溯用）；③版本号 v4.2→v4.4 对齐 Refresh 模式变更。
> v4.3 — 2026-04-06 17:59 | **新增语音播报字段**：briefing.json 新增 `audioUrl`/`audioFile`/`voiceText` 三个可选字段，支持前端时间状态栏🔊播放按钮。由 `generate_audio.py`（MiniMax TTS）+ `upload_to_cloud.py` v1.2 自动生成和上传。
> v4.2 — 2026-04-06 14:06 | **标的页质量基线门禁固化+枚举修复**：①新增「标的页质量基线门禁 W1-W9」——9项覆盖板块完整性/字段完整性/analysis质量/reason论据/tags精准/metrics一致性/summary有数据/sparkline-price一致/risks独立具体；②§5.3 `sectors[].id` 枚举从旧7板块修正为新5板块；③新增「简报页质量基线门禁 B1-B12」（v4.1已固化）。
> v4.1 — 2026-04-06 14:05 | **简报页质量基线门禁 B1-B12 固化**：12项逐条自查清单覆盖 takeaway~整体价投风格；以 2026-04-06 版 briefing.json 为黄金样本基准。
> v4.0 — 2026-04-06 13:59 | **市场页 v4.4 优化 + 质量基线门禁固化**：Insight 升级为决策信号式；sparkline-price 一致性校验；新增 Q1-Q8 市场页门禁。
> v3.9 及更早 | 详见 git 历史。
