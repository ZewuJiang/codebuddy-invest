/**
 * markets-mock.js — 市场行情 Mock 数据 v4.0
 * 对齐 Skill §2: 美股(SPX/NDX/DJI+M7+VIX) + 亚太 + 大宗 + 加密 + GICS 11板块
 */
module.exports = {
  "usMarkets": [
    { "name": "标普500", "price": "5,254.35", "change": 0.86, "changeLabel": "连涨3日" },
    { "name": "纳斯达克", "price": "16,399.52", "change": 1.24, "changeLabel": "放量突破" },
    { "name": "道琼斯", "price": "39,807.37", "change": 0.32, "changeLabel": "温和上涨" },
    { "name": "VIX恐慌指数", "price": "13.01", "change": -5.2, "changeLabel": "低波动区" }
  ],
  "usInsight": "科技股领涨带动纳指创两周新高，AI板块延续强势，VIX降至13下方暗示短期波动率压缩，注意均值回归风险",
  "m7": [
    { "name": "苹果 AAPL", "price": "$192.53", "change": 0.65, "symbol": "AAPL" },
    { "name": "微软 MSFT", "price": "$428.72", "change": 1.12, "symbol": "MSFT" },
    { "name": "英伟达 NVDA", "price": "$878.36", "change": 4.20, "symbol": "NVDA" },
    { "name": "谷歌 GOOGL", "price": "$155.72", "change": 0.87, "symbol": "GOOGL" },
    { "name": "亚马逊 AMZN", "price": "$186.13", "change": 1.35, "symbol": "AMZN" },
    { "name": "Meta META", "price": "$503.28", "change": 2.18, "symbol": "META" },
    { "name": "特斯拉 TSLA", "price": "$175.22", "change": -1.45, "symbol": "TSLA" }
  ],
  "m7Insight": "M7分化加剧，NVDA独涨4.2%领跑受益AI资本开支超预期，META和AMZN跟涨，TSLA连跌三日拖累整体表现",
  "asiaMarkets": [
    { "name": "上证指数", "price": "3,041.17", "change": -0.27 },
    { "name": "深证成指", "price": "9,362.01", "change": -0.15 },
    { "name": "恒生指数", "price": "16,541.42", "change": 1.35 },
    { "name": "恒生科技", "price": "3,652.80", "change": 2.15 },
    { "name": "日经225", "price": "40,888.43", "change": 0.95 },
    { "name": "韩国KOSPI", "price": "2,745.82", "change": 0.42 }
  ],
  "asiaInsight": "港股领涨亚太，恒生科技受南向资金支撑涨2.15%，A股缩量调整缺乏主线，日经受日元走弱提振逼近41000",
  "commodities": [
    { "name": "黄金 XAU", "price": "$2,213.40", "change": 0.82 },
    { "name": "布伦特原油", "price": "$87.48", "change": -0.32 },
    { "name": "WTI原油", "price": "$83.12", "change": -0.45 },
    { "name": "美元指数 DXY", "price": "104.52", "change": -0.18 },
    { "name": "10Y美债", "price": "4.21%", "change": 0.03 },
    { "name": "离岸人民币 CNH", "price": "7.2650", "change": 0.05 }
  ],
  "commodityInsight": "黄金突破2210美元创历史新高，避险需求叠加央行购金支撑，原油小幅回落，美元走弱提振非美资产",
  "cryptos": [
    { "name": "比特币 BTC", "price": "$70,215", "change": 2.35 },
    { "name": "以太坊 ETH", "price": "$3,562", "change": 1.87 },
    { "name": "SOL", "price": "$185.40", "change": 3.12 }
  ],
  "cryptoInsight": "BTC站上7万美元关口，ETF持续净流入叠加减半预期升温，SOL领涨山寨币生态资金活跃",
  "gics": [
    { "name": "信息技术 XLK", "change": 1.82, "etf": "XLK" },
    { "name": "通信服务 XLC", "change": 1.45, "etf": "XLC" },
    { "name": "可选消费 XLY", "change": 0.92, "etf": "XLY" },
    { "name": "工业 XLI", "change": 0.67, "etf": "XLI" },
    { "name": "金融 XLF", "change": 0.55, "etf": "XLF" },
    { "name": "医疗保健 XLV", "change": 0.38, "etf": "XLV" },
    { "name": "原材料 XLB", "change": 0.25, "etf": "XLB" },
    { "name": "必需消费 XLP", "change": -0.12, "etf": "XLP" },
    { "name": "公用事业 XLU", "change": -0.35, "etf": "XLU" },
    { "name": "房地产 XLRE", "change": -0.58, "etf": "XLRE" },
    { "name": "能源 XLE", "change": -0.72, "etf": "XLE" }
  ],
  "gicsInsight": "板块轮动明显，科技/通信领涨反映AI主线延续，能源/房地产承压显示市场偏好成长股弃守价值股"
}
