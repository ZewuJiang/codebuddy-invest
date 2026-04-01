/**
 * watchlist-mock.js — 标的/自选 Mock 数据 v4.0
 * 对齐 Skill §3: M7+AI产业链24环+一级关注标的
 * 7个板块，20-25只核心标的
 */
module.exports = {
  "sectors": [
    { "id": "ai", "name": "AI算力", "trend": "up", "summary": "AI算力需求持续爆发，英伟达数据中心收入超预期，产业链上游确定性最高。关注GPU、HBM内存、光模块三条子赛道。" },
    { "id": "semi", "name": "半导体", "trend": "up", "summary": "全球半导体周期触底回升，存储芯片价格连涨，HBM供不应求。设备股受益于扩产周期。" },
    { "id": "internet", "name": "互联网平台", "trend": "up", "summary": "中国互联网平台估值修复行情延续，回购力度加大，AI+应用落地成为新增长极。" },
    { "id": "energy", "name": "新能源", "trend": "down", "summary": "锂电产能过剩压制估值，光伏组件价格战持续，短期承压但长期逻辑不变。" },
    { "id": "consumer", "name": "消费", "trend": "hold", "summary": "消费复苏节奏偏慢，白酒分化加剧，关注出海品牌和性价比消费新趋势。" },
    { "id": "pharma", "name": "医药", "trend": "hold", "summary": "GLP-1减肥药赛道持续火热，创新药出海加速，CXO板块底部企稳迹象。" },
    { "id": "finance", "name": "金融", "trend": "hold", "summary": "美联储降息预期利好银行股，伯克希尔现金储备创新高，保险板块防御属性凸显。" }
  ],
  "stocks": {
    "ai": [
      {
        "name": "英伟达", "symbol": "NVDA", "change": 4.2, "price": "$878.36",
        "tags": ["AI芯片龙头", "GTC大会催化"],
        "reason": "Blackwell架构发布超预期，数据中心营收占比超80%，AI推理需求打开增量空间。",
        "analysis": "英伟达是全球AI算力领域的绝对龙头。Blackwell B200芯片性能较上代提升5-30倍，已获得微软、亚马逊、谷歌等头部客户大规模订单。数据中心收入已占总营收80%+，AI推理需求正在从训练延伸至推理端，为增长打开新空间。\n\n风险方面：估值偏高（PE超70x），竞争加剧（AMD MI300X、谷歌TPU v5、自研芯片趋势），出口管制可能影响中国市场收入。",
        "metrics": [
          { "label": "PE(TTM)", "value": "72.5x" },
          { "label": "市值", "value": "$2.3T" },
          { "label": "营收增速", "value": "+265%" },
          { "label": "毛利率", "value": "76.0%" },
          { "label": "ROE", "value": "91.5%" },
          { "label": "评级", "value": "⭐⭐⭐⭐⭐" }
        ],
        "risks": ["估值偏高，PE超70x", "AMD MI300X竞争加剧", "美国对华出口管制风险"]
      },
      {
        "name": "博通", "symbol": "AVGO", "change": 1.8, "price": "$1,342.50",
        "tags": ["定制芯片", "AI网络"],
        "reason": "ASIC定制芯片业务快速增长，为谷歌、Meta定制AI芯片，网络设备受益数据中心建设。",
        "analysis": "博通在AI定制芯片（ASIC）市场占据领先地位，为谷歌、Meta等巨头提供定制AI芯片方案。网络设备业务受益于AI数据中心的大规模建设。收购VMware后软件业务占比提升，利润率结构优化。",
        "metrics": [
          { "label": "PE(TTM)", "value": "35.2x" },
          { "label": "市值", "value": "$620B" },
          { "label": "营收增速", "value": "+34%" },
          { "label": "毛利率", "value": "74.2%" },
          { "label": "ROE", "value": "28.3%" },
          { "label": "评级", "value": "⭐⭐⭐⭐" }
        ],
        "risks": ["VMware整合风险", "客户集中度高"]
      },
      {
        "name": "台积电", "symbol": "TSM", "change": 2.3, "price": "$152.68",
        "tags": ["晶圆代工龙头", "先进制程"],
        "reason": "3nm/2nm先进制程产能满载，AI芯片需求带动CoWoS封装产能紧缺。",
        "analysis": "台积电是全球最大晶圆代工厂，先进制程(7nm以下)市占率超90%。AI芯片爆发带动CoWoS先进封装需求激增，产能供不应求至2025年底。3nm量产顺利，2nm预计2025年下半年投产。海外建厂(美国/日本/德国)降低地缘风险。",
        "metrics": [
          { "label": "PE(TTM)", "value": "26.8x" },
          { "label": "市值", "value": "$780B" },
          { "label": "营收增速", "value": "+26%" },
          { "label": "毛利率", "value": "54.2%" },
          { "label": "ROE", "value": "29.8%" },
          { "label": "评级", "value": "⭐⭐⭐⭐⭐" }
        ],
        "risks": ["地缘政治（台海局势）", "海外建厂成本高"]
      },
      {
        "name": "微软", "symbol": "MSFT", "change": 1.12, "price": "$428.72",
        "tags": ["AI应用龙头", "Copilot"],
        "reason": "Azure+AI增长强劲，Copilot商业化加速，AI应用层最大受益者。",
        "analysis": "微软是AI应用层的最大赢家。Azure云+AI营收增速超30%，Copilot已在Office/GitHub/安全等产品线全面铺开。与OpenAI深度绑定，占据AI平台层核心位置。企业级AI需求持续增长，订单能见度高。",
        "metrics": [
          { "label": "PE(TTM)", "value": "36.5x" },
          { "label": "市值", "value": "$3.2T" },
          { "label": "营收增速", "value": "+18%" },
          { "label": "毛利率", "value": "69.8%" },
          { "label": "ROE", "value": "39.2%" },
          { "label": "评级", "value": "⭐⭐⭐⭐⭐" }
        ],
        "risks": ["估值偏高", "Copilot变现不及预期", "反垄断风险"]
      }
    ],
    "semi": [
      {
        "name": "SK海力士", "symbol": "000660.KS", "change": 2.1, "price": "₩178,500",
        "tags": ["HBM内存", "存储龙头"],
        "reason": "HBM3e产能被英伟达包圆，存储价格Q2有望继续上涨20%+。",
        "analysis": "SK海力士在HBM市场份额超50%，是英伟达AI GPU的核心供应商。HBM3e良率持续提升，全部产能已被锁定。DRAM和NAND价格周期性回升，业绩拐点确认。",
        "metrics": [
          { "label": "PE(TTM)", "value": "18.3x" },
          { "label": "HBM份额", "value": "53%" },
          { "label": "营收增速", "value": "+88%" },
          { "label": "毛利率", "value": "42.5%" },
          { "label": "ROE", "value": "22.1%" },
          { "label": "评级", "value": "⭐⭐⭐⭐⭐" }
        ],
        "risks": ["存储芯片价格回升可持续性待观察", "三星HBM良率追赶"]
      },
      {
        "name": "ASML", "symbol": "ASML", "change": 1.5, "price": "$1,012.30",
        "tags": ["光刻机垄断", "EUV"],
        "reason": "EUV光刻机独家垄断，先进制程扩产不可能绕过ASML。",
        "analysis": "ASML是全球唯一EUV光刻机供应商，垄断地位无可撼动。台积电、三星、英特尔扩产先进制程都必须采购ASML设备。High-NA EUV已交付首台设备，下一代技术继续领先。订单积压超€380亿，能见度极高。",
        "metrics": [
          { "label": "PE(TTM)", "value": "42.8x" },
          { "label": "市值", "value": "$400B" },
          { "label": "积压订单", "value": "€380B" },
          { "label": "毛利率", "value": "51.3%" },
          { "label": "ROE", "value": "58.2%" },
          { "label": "评级", "value": "⭐⭐⭐⭐⭐" }
        ],
        "risks": ["地缘政治出口限制", "半导体周期波动"]
      },
      {
        "name": "AMD", "symbol": "AMD", "change": 0.8, "price": "$178.65",
        "tags": ["AI芯片挑战者", "MI300X"],
        "reason": "MI300X抢夺AI推理市场份额，数据中心GPU业务快速增长。",
        "analysis": "AMD凭借MI300X在AI GPU市场占据第二把交椅。数据中心GPU营收$35亿+，同比增长>6倍。MI400路线图清晰，CPU方面EPYC继续蚕食英特尔份额。性价比优势在推理场景中凸显。",
        "metrics": [
          { "label": "PE(TTM)", "value": "48.5x" },
          { "label": "市值", "value": "$290B" },
          { "label": "AI GPU营收", "value": "$3.5B" },
          { "label": "毛利率", "value": "52.1%" },
          { "label": "ROE", "value": "4.2%" },
          { "label": "评级", "value": "⭐⭐⭐⭐" }
        ],
        "risks": ["CUDA生态壁垒难突破", "与英伟达差距仍大"]
      }
    ],
    "internet": [
      {
        "name": "腾讯", "symbol": "0700.HK", "change": 1.85, "price": "HK$368.20",
        "tags": ["中国互联网龙头", "AI+游戏"],
        "reason": "混元大模型+微信生态AI化，游戏版号恢复常态化，回购力度创历史新高。",
        "analysis": "腾讯是中国互联网最核心资产。混元大模型已在微信/企微/腾讯云等多场景落地，AI赋能效果初显。游戏业务恢复增长，视频号商业化加速。每年回购超HK$1000亿，股东回报大幅提升。",
        "metrics": [
          { "label": "PE(TTM)", "value": "22.5x" },
          { "label": "市值", "value": "HK$3.5T" },
          { "label": "营收增速", "value": "+10%" },
          { "label": "毛利率", "value": "52.8%" },
          { "label": "ROE", "value": "22.6%" },
          { "label": "评级", "value": "⭐⭐⭐⭐⭐" }
        ],
        "risks": ["监管政策不确定性", "游戏出海竞争加剧"]
      },
      {
        "name": "拼多多", "symbol": "PDD", "change": 3.2, "price": "$142.56",
        "tags": ["Temu出海", "高增长"],
        "reason": "Temu全球扩张势如破竹，国内主站利润丰厚，增速远超同行。",
        "analysis": "拼多多通过Temu在海外跨境电商市场快速扩张，已进入50+国家/地区。国内主站高利润率支撑海外投资，全站推广(FSS)模式降低商家门槛。净利润率超20%，增长与盈利兼具。",
        "metrics": [
          { "label": "PE(TTM)", "value": "12.8x" },
          { "label": "市值", "value": "$195B" },
          { "label": "营收增速", "value": "+86%" },
          { "label": "毛利率", "value": "63.5%" },
          { "label": "ROE", "value": "45.8%" },
          { "label": "评级", "value": "⭐⭐⭐⭐⭐" }
        ],
        "risks": ["海外合规与关税风险", "Temu亏损持续性", "竞争对手(SHEIN/TikTok Shop)"]
      },
      {
        "name": "美团", "symbol": "3690.HK", "change": 2.45, "price": "HK$128.50",
        "tags": ["本地生活", "AI降本"],
        "reason": "本地生活龙头地位稳固，AI提效降本成效显著，新业务亏损收窄。",
        "analysis": "美团在本地生活（外卖+到店）领域市占率超65%。AI大模型应用于配送调度、客服等场景，单均成本持续下降。新业务（美团优选、买菜）亏损大幅收窄，整体盈利能力改善。",
        "metrics": [
          { "label": "PE(TTM)", "value": "28.3x" },
          { "label": "市值", "value": "HK$790B" },
          { "label": "营收增速", "value": "+22%" },
          { "label": "毛利率", "value": "38.2%" },
          { "label": "ROE", "value": "12.5%" },
          { "label": "评级", "value": "⭐⭐⭐⭐" }
        ],
        "risks": ["抖音本地生活竞争", "海外业务仍在投入期"]
      }
    ],
    "energy": [
      {
        "name": "宁德时代", "symbol": "300750.SZ", "change": -1.2, "price": "¥195.80",
        "tags": ["锂电龙头", "海外扩张"],
        "reason": "短期产能过剩压制毛利率，但海外建厂和神行超充电池打开新增长曲线。",
        "analysis": "宁德时代是全球动力电池市场份额第一（36.8%），技术领先优势明显。神行超充电池实现量产，固态电池研发进展领先。海外建厂拓展全球市场。但行业产能过剩导致价格竞争激烈。",
        "metrics": [
          { "label": "PE(TTM)", "value": "22.1x" },
          { "label": "全球份额", "value": "36.8%" },
          { "label": "营收增速", "value": "+22%" },
          { "label": "毛利率", "value": "22.9%" },
          { "label": "ROE", "value": "21.3%" },
          { "label": "评级", "value": "⭐⭐⭐" }
        ],
        "risks": ["锂电行业产能过剩", "欧美贸易壁垒", "固态电池路线切换风险"]
      },
      {
        "name": "比亚迪", "symbol": "002594.SZ", "change": 0.85, "price": "¥235.60",
        "tags": ["新能源车龙头", "出海加速"],
        "reason": "新能源车销量全球第一，智能化加速追赶，海外市场快速放量。",
        "analysis": "比亚迪2024年新能源车销量超300万辆，全球第一。垂直一体化（电池+芯片+整车）成本优势显著。海外建厂（匈牙利、泰国、巴西）推进中。智能驾驶方面投入加大，天神之眼系统快速迭代。",
        "metrics": [
          { "label": "PE(TTM)", "value": "25.6x" },
          { "label": "市值", "value": "¥6850亿" },
          { "label": "营收增速", "value": "+42%" },
          { "label": "毛利率", "value": "21.5%" },
          { "label": "ROE", "value": "18.7%" },
          { "label": "评级", "value": "⭐⭐⭐⭐" }
        ],
        "risks": ["海外贸易壁垒加高", "智驾技术差距", "价格战侵蚀利润"]
      }
    ],
    "consumer": [
      {
        "name": "泡泡玛特", "symbol": "9992.HK", "change": 3.5, "price": "HK$72.60",
        "tags": ["潮玩IP", "出海典范"],
        "reason": "海外收入占比超40%，东南亚和欧洲市场快速增长，IP矩阵持续扩充。",
        "analysis": "泡泡玛特是中国潮玩行业龙头，IP运营能力强大。海外业务高速增长，东南亚、欧洲、北美多点开花。线上线下渠道协同，机器人商店扩张顺利。",
        "metrics": [
          { "label": "PE(TTM)", "value": "45.8x" },
          { "label": "海外营收占比", "value": "42%" },
          { "label": "营收增速", "value": "+63%" },
          { "label": "毛利率", "value": "61.3%" },
          { "label": "ROE", "value": "35.2%" },
          { "label": "评级", "value": "⭐⭐⭐⭐" }
        ],
        "risks": ["IP热度具有周期性", "估值偏高", "海外汇率风险"]
      },
      {
        "name": "Costco", "symbol": "COST", "change": 0.45, "price": "$735.20",
        "tags": ["会员制零售", "防御型"],
        "reason": "会员续费率97.5%，同店销售稳健增长，通胀环境下性价比消费受益。",
        "analysis": "Costco是全球会员制仓储零售龙头。会员续费率高达97.5%，会员费收入构成核心利润来源。在通胀环境下，消费者追求性价比，Costco受益明显。",
        "metrics": [
          { "label": "PE(TTM)", "value": "52.3x" },
          { "label": "会员续费率", "value": "97.5%" },
          { "label": "营收增速", "value": "+8%" },
          { "label": "毛利率", "value": "12.8%" },
          { "label": "ROE", "value": "28.5%" },
          { "label": "评级", "value": "⭐⭐⭐⭐" }
        ],
        "risks": ["估值偏高", "中国市场扩张不及预期"]
      }
    ],
    "pharma": [
      {
        "name": "诺和诺德", "symbol": "NVO", "change": 1.6, "price": "$132.45",
        "tags": ["GLP-1龙头", "减肥药"],
        "reason": "Ozempic和Wegovy持续放量，全球减肥药市场2030年达1500亿美元。",
        "analysis": "诺和诺德是GLP-1类药物的全球领导者。减肥适应症全球渗透率极低（<5%），长期增长空间巨大。CagriSema下一代产品有望巩固领先地位。",
        "metrics": [
          { "label": "PE(TTM)", "value": "48.2x" },
          { "label": "市值", "value": "$570B" },
          { "label": "营收增速", "value": "+36%" },
          { "label": "毛利率", "value": "85.2%" },
          { "label": "ROE", "value": "88.7%" },
          { "label": "评级", "value": "⭐⭐⭐⭐⭐" }
        ],
        "risks": ["礼来竞品竞争加剧", "产能扩张不及需求", "定价与医保政策风险"]
      },
      {
        "name": "礼来", "symbol": "LLY", "change": 0.92, "price": "$782.30",
        "tags": ["GLP-1挑战者", "Mounjaro"],
        "reason": "Mounjaro/Zepbound双引擎驱动，减肥药市场双寡头格局确立。",
        "analysis": "礼来凭借Mounjaro(降糖)和Zepbound(减肥)迅速崛起为GLP-1赛道第二极。Zepbound减肥效果优于竞品，供应逐步放量。阿尔茨海默药Donanemab获批增添新增长点。",
        "metrics": [
          { "label": "PE(TTM)", "value": "62.5x" },
          { "label": "市值", "value": "$740B" },
          { "label": "营收增速", "value": "+28%" },
          { "label": "毛利率", "value": "80.5%" },
          { "label": "ROE", "value": "62.3%" },
          { "label": "评级", "value": "⭐⭐⭐⭐" }
        ],
        "risks": ["估值极高", "产能瓶颈", "GLP-1副作用担忧"]
      }
    ],
    "finance": [
      {
        "name": "伯克希尔", "symbol": "BRK.B", "change": 0.35, "price": "$418.52",
        "tags": ["巴菲特", "价值投资旗舰"],
        "reason": "现金储备超$1800亿创新高，等待大象级并购机会，保险浮存金贡献稳定收益。",
        "analysis": "伯克希尔是全球最大多元化控股公司。保险（GEICO）、铁路（BNSF）、能源等核心业务稳健。现金储备创历史新高，巴菲特在高利率环境下获取可观利息收入，同时等待大型并购机会。",
        "metrics": [
          { "label": "PE(TTM)", "value": "9.8x" },
          { "label": "市值", "value": "$905B" },
          { "label": "现金储备", "value": "$189B" },
          { "label": "营收增速", "value": "+21%" },
          { "label": "ROE", "value": "15.8%" },
          { "label": "评级", "value": "⭐⭐⭐⭐⭐" }
        ],
        "risks": ["巴菲特年龄与继任风险", "苹果持仓集中度"]
      },
      {
        "name": "摩根大通", "symbol": "JPM", "change": 0.68, "price": "$198.45",
        "tags": ["美国银行龙头", "降息受益"],
        "reason": "降息周期利好银行股，净息差企稳，投行业务回暖。",
        "analysis": "摩根大通是美国最大银行，业务全面（零售/投行/资管/交易）。在降息预期下，信贷需求有望回升。投行业务受益于IPO和M&A活动回暖。资本实力雄厚，持续高分红+回购。",
        "metrics": [
          { "label": "PE(TTM)", "value": "12.2x" },
          { "label": "市值", "value": "$570B" },
          { "label": "净息差", "value": "2.72%" },
          { "label": "ROE", "value": "17.2%" },
          { "label": "CET1比率", "value": "15.0%" },
          { "label": "评级", "value": "⭐⭐⭐⭐" }
        ],
        "risks": ["经济衰退信贷损失", "商业地产风险敞口"]
      }
    ]
  }
}
