/**
 * dynamic-mock.js — 动态 Mock 数据生成器
 * 基于日期种子的伪随机价格波动 + sparkline 走势数据
 * 同一天打开数据一致，不同天打开数据变化
 */

/**
 * 字符串哈希函数（用于生成种子）
 * @param {string} str
 * @returns {number}
 */
function hashCode(str) {
  var hash = 0
  for (var i = 0; i < str.length; i++) {
    var char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash // 转为32位整数
  }
  return Math.abs(hash)
}

/**
 * 基于种子的伪随机数生成器（0~1之间）
 * @param {number} seed
 * @returns {number}
 */
function seededRandom(seed) {
  var x = Math.sin(seed + 1) * 10000
  return x - Math.floor(x)
}

/**
 * 获取N天前的日期字符串 YYYY-MM-DD
 * @param {number} daysAgo
 * @returns {string}
 */
function getDateNDaysAgo(daysAgo) {
  var d = new Date()
  d.setDate(d.getDate() - daysAgo)
  var month = String(d.getMonth() + 1).padStart(2, '0')
  var day = String(d.getDate()).padStart(2, '0')
  return d.getFullYear() + '-' + month + '-' + day
}

/**
 * 获取今天的日期字符串
 * @returns {string}
 */
function getTodayStr() {
  return getDateNDaysAgo(0)
}

/**
 * 解析价格字符串为数字（去除$, ¥, ₩, HK$, 逗号等）
 * @param {string} priceStr
 * @returns {number}
 */
function parsePrice(priceStr) {
  if (typeof priceStr === 'number') return priceStr
  var cleaned = String(priceStr).replace(/[^0-9.\-]/g, '')
  return parseFloat(cleaned) || 0
}

/**
 * 格式化价格（保留原始前缀和千分位）
 * @param {number} num - 数字
 * @param {string} originalPriceStr - 原始价格字符串（用于推断前缀）
 * @returns {string}
 */
function formatPrice(num, originalPriceStr) {
  // 提取前缀
  var prefix = ''
  if (originalPriceStr) {
    var match = String(originalPriceStr).match(/^([^0-9.\-]*)/)
    if (match) prefix = match[1]
  }

  // 确定小数位
  var decimals = 2
  if (num >= 10000) decimals = 0
  else if (num >= 100) decimals = 2
  else decimals = 2

  // 千分位格式化
  var parts = num.toFixed(decimals).split('.')
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return prefix + parts.join('.')
}

/**
 * 为一个标的生成当日动态价格
 * @param {number} basePrice - 基准价格
 * @param {string} symbol - 标识符
 * @param {string} dateStr - 日期字符串
 * @param {number} volatility - 波动率（0~1），默认0.03（±3%）
 * @returns {number}
 */
function generatePrice(basePrice, symbol, dateStr, volatility) {
  volatility = volatility || 0.03
  var seed = hashCode(symbol + ':' + dateStr)
  var rand = seededRandom(seed)
  var fluctuation = (rand - 0.5) * 2 * volatility
  return basePrice * (1 + fluctuation)
}

/**
 * 生成涨跌幅（基于当日价格与前一日价格的差值）
 * @param {number} basePrice - 基准价格
 * @param {string} symbol - 标识符
 * @param {number} volatility - 波动率
 * @returns {number} 涨跌幅百分比（如 +2.35）
 */
function generateChange(basePrice, symbol, volatility) {
  var today = getTodayStr()
  var yesterday = getDateNDaysAgo(1)
  var todayPrice = generatePrice(basePrice, symbol, today, volatility)
  var yesterdayPrice = generatePrice(basePrice, symbol, yesterday, volatility)
  var change = ((todayPrice - yesterdayPrice) / yesterdayPrice) * 100
  return Math.round(change * 100) / 100
}

/**
 * 生成 sparkline 走势数据（7日）
 * @param {number} basePrice - 基准价格
 * @param {string} symbol - 标识符
 * @param {number} days - 天数，默认7
 * @param {number} volatility - 波动率
 * @returns {Array<number>}
 */
function generateSparkline(basePrice, symbol, days, volatility) {
  days = days || 7
  volatility = volatility || 0.03
  var points = []
  for (var i = days - 1; i >= 0; i--) {
    var dateStr = getDateNDaysAgo(i)
    points.push(generatePrice(basePrice, symbol, dateStr, volatility))
  }
  return points
}

/**
 * 生成动态的变化标签
 * @param {number} change - 涨跌幅
 * @returns {string}
 */
function generateChangeLabel(change) {
  if (change > 2) return '强势上涨'
  if (change > 1) return '放量上攻'
  if (change > 0.5) return '温和上涨'
  if (change > 0) return '小幅上扬'
  if (change > -0.5) return '窄幅震荡'
  if (change > -1) return '小幅回落'
  if (change > -2) return '承压下行'
  return '大幅调整'
}

/**
 * 动态生成市场行情数据
 * @returns {object} 与 markets-mock.js 同结构
 */
function generateMarketsData() {
  // 基准数据
  var baselines = {
    usMarkets: [
      { name: '标普500', basePrice: 5254.35, symbol: 'SPX', volatility: 0.025, note: '' },
      { name: '纳斯达克', basePrice: 16399.52, symbol: 'IXIC', volatility: 0.035 },
      { name: '道琼斯', basePrice: 39807.37, symbol: 'DJI', volatility: 0.02 },
      { name: 'VIX恐慌指数', basePrice: 13.01, symbol: 'VIX', volatility: 0.15 }
    ],
    m7: [
      { name: '苹果 AAPL', basePrice: 192.53, symbol: 'AAPL', volatility: 0.03, prefix: '$' },
      { name: '微软 MSFT', basePrice: 428.72, symbol: 'MSFT', volatility: 0.03, prefix: '$' },
      { name: '英伟达 NVDA', basePrice: 878.36, symbol: 'NVDA', volatility: 0.05, prefix: '$' },
      { name: '谷歌 GOOGL', basePrice: 155.72, symbol: 'GOOGL', volatility: 0.03, prefix: '$' },
      { name: '亚马逊 AMZN', basePrice: 186.13, symbol: 'AMZN', volatility: 0.035, prefix: '$' },
      { name: 'Meta META', basePrice: 503.28, symbol: 'META', volatility: 0.04, prefix: '$' },
      { name: '特斯拉 TSLA', basePrice: 175.22, symbol: 'TSLA', volatility: 0.06, prefix: '$' }
    ],
    asiaMarkets: [
      { name: '上证指数', basePrice: 3041.17, symbol: 'SSEC', volatility: 0.02 },
      { name: '深证成指', basePrice: 9362.01, symbol: 'SZSE', volatility: 0.025 },
      { name: '恒生指数', basePrice: 16541.42, symbol: 'HSI', volatility: 0.03 },
      { name: '恒生科技', basePrice: 3652.80, symbol: 'HSTECH', volatility: 0.04 },
      { name: '日经225', basePrice: 40888.43, symbol: 'N225', volatility: 0.025 },
      { name: '韩国KOSPI', basePrice: 2745.82, symbol: 'KOSPI', volatility: 0.02 }
    ],
    commodities: [
      { name: '黄金 XAU', basePrice: 2213.40, symbol: 'XAUUSD', volatility: 0.02, prefix: '$' },
      { name: '布伦特原油', basePrice: 87.48, symbol: 'BRENT', volatility: 0.04, prefix: '$' },
      { name: 'WTI原油', basePrice: 83.12, symbol: 'WTI', volatility: 0.04, prefix: '$' },
      { name: '美元指数 DXY', basePrice: 104.52, symbol: 'DXY', volatility: 0.01 },
      { name: '10Y美债', basePrice: 4.21, symbol: 'US10Y', volatility: 0.05 },
      { name: '离岸人民币 CNH', basePrice: 7.2650, symbol: 'CNH', volatility: 0.008 }
    ],
    cryptos: [
      { name: '比特币 BTC', basePrice: 70215, symbol: 'BTC', volatility: 0.06, prefix: '$' },
      { name: '以太坊 ETH', basePrice: 3562, symbol: 'ETH', volatility: 0.07, prefix: '$' },
      { name: 'SOL', basePrice: 185.40, symbol: 'SOL', volatility: 0.08, prefix: '$' }
    ]
  }

  // GICS 11板块基准
  var gicsBaselines = [
    { name: '信息技术 XLK', baseChange: 1.82, symbol: 'XLK', etf: 'XLK' },
    { name: '通信服务 XLC', baseChange: 1.45, symbol: 'XLC', etf: 'XLC' },
    { name: '可选消费 XLY', baseChange: 0.92, symbol: 'XLY', etf: 'XLY' },
    { name: '工业 XLI', baseChange: 0.67, symbol: 'XLI', etf: 'XLI' },
    { name: '金融 XLF', baseChange: 0.55, symbol: 'XLF', etf: 'XLF' },
    { name: '医疗保健 XLV', baseChange: 0.38, symbol: 'XLV', etf: 'XLV' },
    { name: '原材料 XLB', baseChange: 0.25, symbol: 'XLB', etf: 'XLB' },
    { name: '必需消费 XLP', baseChange: -0.12, symbol: 'XLP', etf: 'XLP' },
    { name: '公用事业 XLU', baseChange: -0.35, symbol: 'XLU', etf: 'XLU' },
    { name: '房地产 XLRE', baseChange: -0.58, symbol: 'XLRE', etf: 'XLRE' },
    { name: '能源 XLE', baseChange: -0.72, symbol: 'XLE', etf: 'XLE' }
  ]

  var today = getTodayStr()
  var result = {}

  // 动态生成note内容
  var usNotes = [
    '科技股领涨，AI板块表现强势',
    '美联储会议纪要释放鸽派信号',
    '非农数据超预期，市场情绪分化',
    '财报季表现良好，大盘稳步攀升',
    '芯片股带动纳指走高，资金回流',
    '降息预期升温，风险偏好改善'
  ]
  var noteSeed = hashCode('note:' + today)
  var noteIndex = Math.floor(seededRandom(noteSeed) * usNotes.length)

  Object.keys(baselines).forEach(function(category) {
    result[category] = baselines[category].map(function(item, idx) {
      var price = generatePrice(item.basePrice, item.symbol, today, item.volatility)
      var change = generateChange(item.basePrice, item.symbol, item.volatility)
      var sparkline = generateSparkline(item.basePrice, item.symbol, 7, item.volatility)
      var prefix = item.prefix || ''
      var priceStr

      // 特殊处理百分比类数据
      if (item.symbol === 'US10Y') {
        priceStr = price.toFixed(2) + '%'
      } else {
        priceStr = prefix + formatPriceNum(price, item.basePrice)
      }

      var entry = {
        name: item.name,
        price: priceStr,
        change: change,
        changeLabel: generateChangeLabel(change),
        sparkline: sparkline
      }

      // M7加上symbol
      if (category === 'm7') {
        entry.symbol = item.symbol
      }

      // 仅为美股第一条加note
      if (category === 'usMarkets' && idx === 0) {
        entry.note = usNotes[noteIndex]
      }

      return entry
    })
  })

  // GICS板块涨跌幅动态生成
  result.gics = gicsBaselines.map(function(item) {
    var gicsSeed = hashCode('gics:' + item.symbol + ':' + today)
    var gicsRand = (seededRandom(gicsSeed) - 0.5) * 4
    var change = Math.round((item.baseChange + gicsRand) * 100) / 100
    return {
      name: item.name,
      change: change,
      etf: item.etf
    }
  }).sort(function(a, b) { return b.change - a.change })

  return result
}

/**
 * 格式化价格数字（保留合理的小数位和千分位）
 * @param {number} num
 * @param {number} basePrice - 用于判断格式
 * @returns {string}
 */
function formatPriceNum(num, basePrice) {
  var decimals = 2
  if (basePrice >= 10000) decimals = 0
  else if (basePrice >= 1000) decimals = 2
  else decimals = 2

  var parts = num.toFixed(decimals).split('.')
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return parts.join('.')
}

/**
 * 动态生成标的/自选数据
 * @returns {object} 与 watchlist-mock.js 同结构
 */
function generateWatchlistData() {
  // 原始watchlist数据作为基准
  var watchlistBase = require('../data/watchlist-mock')
  var result = JSON.parse(JSON.stringify(watchlistBase))
  var today = getTodayStr()

  // 动态更新每只股票的价格和涨跌幅
  Object.keys(result.stocks).forEach(function(sectorId) {
    result.stocks[sectorId].forEach(function(stock) {
      var basePrice = parsePrice(stock.price)
      if (basePrice > 0) {
        var newPrice = generatePrice(basePrice, stock.symbol, today, 0.04)
        var change = generateChange(basePrice, stock.symbol, 0.04)
        stock.price = formatPrice(newPrice, stock.price)
        stock.change = change
        stock.sparkline = generateSparkline(basePrice, stock.symbol, 7, 0.04)
        // 为详情页生成30日走势
        stock.chartData = generateSparkline(basePrice, stock.symbol, 30, 0.04)
      }
    })
  })

  return result
}

/**
 * 动态生成简报数据 v4.0
 * 对齐 Skill §1+§2摘要+§4摘要
 * @returns {object} 与 briefing-mock.js 同结构
 */
function generateBriefingData() {
  var briefingBase = require('../data/briefing-mock')
  var result = JSON.parse(JSON.stringify(briefingBase))
  var today = getTodayStr()

  // 情绪分数每日波动（40~80之间）
  var seed = hashCode('sentiment:' + today)
  var rand = seededRandom(seed)
  result.sentimentScore = Math.round(40 + rand * 40)
  if (result.sentimentScore < 35) result.sentimentLabel = '极度恐惧'
  else if (result.sentimentScore < 45) result.sentimentLabel = '偏恐惧'
  else if (result.sentimentScore < 55) result.sentimentLabel = '中性'
  else if (result.sentimentScore < 65) result.sentimentLabel = '偏贪婪'
  else if (result.sentimentScore < 75) result.sentimentLabel = '贪婪'
  else result.sentimentLabel = '极度贪婪'

  // 核心事件标题每日轮换
  var allEvents = [
    {
      title: '英伟达GTC大会发布Blackwell Ultra架构，AI算力竞赛进入新阶段',
      chain: [
        'NVIDIA发布Blackwell Ultra GPU + Vera Rubin路线图',
        '训练成本预计下降40%，推理效率提升3倍',
        '微软/Meta/谷歌抢先锁定2026年产能',
        'AI算力资本开支预期上修，供应链全线受益'
      ]
    },
    {
      title: '美联储3月议息会议按兵不动，点阵图暗示年内两次降息',
      chain: [
        'Fed维持利率5.25-5.50%不变',
        '点阵图中位数显示年内降息50bp',
        '鲍威尔称"对通胀回落更有信心"',
        '市场定价6月首次降息概率升至72%'
      ]
    },
    {
      title: '苹果发布AI战略重大更新，Apple Intelligence全面接入GPT-5',
      chain: [
        '苹果宣布与OpenAI深化合作，Siri接入GPT-5',
        '自研端侧大模型性能超预期',
        'iPhone AI功能推动换机潮预期',
        '苹果供应链（立讯/歌尔）跟涨'
      ]
    },
    {
      title: '中国央行意外降准50bp，释放流动性约1.2万亿',
      chain: [
        '央行宣布全面降准0.5个百分点',
        '释放长期资金约1.2万亿人民币',
        'A股大幅高开，港股同步上涨，外资动向转暖',
        '房地产/基建板块领涨'
      ]
    },
    {
      title: 'Meta发布Llama 4开源模型，性能对标GPT-4o，AI开源生态加速',
      chain: [
        'Llama 4在多项benchmark超越GPT-4o',
        '开源社区极度活跃，下游应用快速跟进',
        '对闭源模型商业化形成挤压',
        'AI应用层公司受益，算力需求进一步增长'
      ]
    }
  ]
  var eventSeed = hashCode('event:' + today)
  var eventIdx = Math.floor(seededRandom(eventSeed) * allEvents.length)
  result.coreEvent = allEvents[eventIdx]

  // 全球资产反应动态生成
  var assets = ['标普500', '纳斯达克', '恒生科技', '黄金', '10Y美债', 'BTC']
  result.globalReaction = assets.map(function(name, i) {
    var assetSeed = hashCode('asset:' + name + ':' + today)
    var assetRand = (seededRandom(assetSeed) - 0.5) * 6 // ±3%
    var direction = assetRand > 0.3 ? 'up' : (assetRand < -0.3 ? 'down' : 'flat')
    var prefix = assetRand >= 0 ? '+' : ''
    var value = name === '10Y美债'
      ? (3.8 + seededRandom(assetSeed + 1) * 0.8).toFixed(2) + '%'
      : prefix + assetRand.toFixed(2) + '%'
    return { name: name, value: value, direction: direction }
  })

  // 三大判断置信度每日微调
  result.coreJudgments.forEach(function(j, i) {
    var jSeed = hashCode('judgment:' + i + ':' + today)
    var jitter = Math.round((seededRandom(jSeed) - 0.5) * 20)
    j.confidence = Math.max(30, Math.min(95, j.confidence + jitter))
  })

  // 聪明钱数据动态
  var allSmartMoney = [
    { source: '桥水基金', action: '增持中国ETF约$2.3亿', signal: 'bullish' },
    { source: '木头姐ARK', action: '继续减持TSLA，加仓COIN和PLTR', signal: 'neutral' },
    { source: '港股成交代理', action: '港股均涨+1.8%，外资动向代理指标为绿灯信号（北向净买额已于2024-08-19停止披露）', signal: 'bullish' },
    { source: '巴菲特伯克希尔', action: '继续增持西方石油，现金储备创新高', signal: 'neutral' },
    { source: '高瓴资本', action: '加仓PDD和BYD，减持JD', signal: 'bullish' },
    { source: '索罗斯基金', action: '建仓AI半导体ETF，加仓NVDA看涨期权', signal: 'bullish' },
    { source: '南向资金', action: '净流入HK$45亿，重点买入腾讯/美团', signal: 'bullish' },
    { source: '贝莱德', action: '上调AI主题配置权重至15%', signal: 'bullish' }
  ]
  var smSeed = hashCode('smartmoney:' + today)
  var smShuffled = allSmartMoney.slice()
  for (var i = smShuffled.length - 1; i > 0; i--) {
    var j = Math.floor(seededRandom(smSeed + i) * (i + 1))
    var temp = smShuffled[i]
    smShuffled[i] = smShuffled[j]
    smShuffled[j] = temp
  }
  result.smartMoney = smShuffled.slice(0, 3)

  // 市场总结每日轮换
  var summaries = [
    '全球风险偏好回升，科技股领涨，VIX回落至低位，但需警惕非农数据扰动',
    'AI叙事持续强化，算力链领涨全球，但估值已进入高位区间需注意回调风险',
    '降息预期升温叠加财报季利好，多头氛围浓厚，关注美债利率走向',
    '地缘风险溢价推升商品，避险资产走强，股市进入高波动窗口期',
    '中美关系缓和信号推动中概股反弹，港股恒生科技领涨亚太市场'
  ]
  var sumSeed = hashCode('summary:' + today)
  result.marketSummary = summaries[Math.floor(seededRandom(sumSeed) * summaries.length)]

  // 数据截止时间
  var now = new Date()
  var hour = String(now.getHours()).padStart(2, '0')
  var minute = String(now.getMinutes()).padStart(2, '0')
  var month = String(now.getMonth() + 1).padStart(2, '0')
  var day = String(now.getDate()).padStart(2, '0')
  result.dataTime = now.getFullYear() + '-' + month + '-' + day + ' ' + hour + ':' + minute + ' BJT'

  return result
}

/**
 * 动态生成雷达数据
 * @returns {object} 与 radar-mock.js 同结构
 */
function generateRadarData() {
  var radarBase = require('../data/radar-mock')
  var result = JSON.parse(JSON.stringify(radarBase))
  var today = getTodayStr()

  // 风险分数每日波动（20~65之间）
  var seed = hashCode('risk:' + today)
  var rand = seededRandom(seed)
  result.riskScore = Math.round(20 + rand * 45)
  
  if (result.riskScore < 30) {
    result.riskLevel = 'low'
    result.riskAdvice = '当前市场处于低风险区间，可适当提高仓位至7-8成，把握上涨机会。'
  } else if (result.riskScore < 50) {
    result.riskLevel = 'medium'
    result.riskAdvice = '当前市场处于中等风险区间，建议维持6成仓位，保留现金应对潜在波动。'
  } else {
    result.riskLevel = 'high'
    result.riskAdvice = '当前市场风险偏高，建议降低仓位至4成以下，注意止损纪律，等待市场企稳信号。'
  }

  // VIX动态 (<18绿 / 18-25黄 / >25红)
  var vixSeed = hashCode('vix:' + today)
  var vixVal = 11 + seededRandom(vixSeed) * 18
  result.trafficLights[0].value = vixVal.toFixed(1)
  result.trafficLights[0].status = vixVal < 18 ? 'green' : (vixVal < 25 ? 'yellow' : 'red')

  // 10Y美债动态 (<4.0%绿 / 4.0-4.5%黄 / >4.5%红)
  var bondSeed = hashCode('bond:' + today)
  var bondVal = 3.8 + seededRandom(bondSeed) * 1.0
  result.trafficLights[1].value = bondVal.toFixed(2) + '%'
  result.trafficLights[1].status = bondVal < 4.0 ? 'green' : (bondVal < 4.5 ? 'yellow' : 'red')

  // 布伦特原油动态 (<80绿 / 80-95黄 / >95红)
  var oilSeed = hashCode('oil:' + today)
  var oilVal = 75 + seededRandom(oilSeed) * 25
  result.trafficLights[2].value = '$' + oilVal.toFixed(2)
  result.trafficLights[2].status = oilVal < 80 ? 'green' : (oilVal < 95 ? 'yellow' : 'red')

  // DXY动态 (<102绿 / 102-107黄 / >107红)
  var dxySeed = hashCode('dxy:' + today)
  var dxyVal = 100 + seededRandom(dxySeed) * 10
  result.trafficLights[3].value = dxyVal.toFixed(1)
  result.trafficLights[3].status = dxyVal < 102 ? 'green' : (dxyVal < 107 ? 'yellow' : 'red')

  // HY信用利差动态 (<4%绿 / 4-5%黄 / >5%红)
  var hySeed = hashCode('hy:' + today)
  var hyVal = 3.0 + seededRandom(hySeed) * 2.5
  result.trafficLights[4].value = hyVal.toFixed(2) + '%'
  result.trafficLights[4].status = hyVal < 4.0 ? 'green' : (hyVal < 5.0 ? 'yellow' : 'red')

  // 外资动向动态（港股均涨跌幅代理，北向净买额已于2024-08-19停止披露）
  var fxSeed = hashCode('foreigncap:' + today)
  var fxVal = (seededRandom(fxSeed) - 0.3) * 5 // 模拟港股均涨跌幅 ±2.5%
  var fxStr = '港股均' + (fxVal >= 0 ? '涨+' : '跌') + fxVal.toFixed(2) + '%'
  result.trafficLights[5].name = '外资动向'
  result.trafficLights[5].value = fxStr
  result.trafficLights[5].threshold = '港股均涨≥+1.5%绿 / 0~+1.5%黄 / 跌红'
  result.trafficLights[5].status = fxVal >= 1.5 ? 'green' : (fxVal >= 0 ? 'yellow' : 'red')

  // CNH动态 (<7.15绿 / 7.15-7.30黄 / >7.30红)
  var cnhSeed = hashCode('cnh:' + today)
  var cnhVal = 7.10 + seededRandom(cnhSeed) * 0.30
  result.trafficLights[6].value = cnhVal.toFixed(4)
  result.trafficLights[6].status = cnhVal < 7.15 ? 'green' : (cnhVal < 7.30 ? 'yellow' : 'red')

  // 数据截止时间
  var now = new Date()
  var hour = String(now.getHours()).padStart(2, '0')
  var minute = String(now.getMinutes()).padStart(2, '0')
  var month = String(now.getMonth() + 1).padStart(2, '0')
  var day = String(now.getDate()).padStart(2, '0')
  result.dataTime = now.getFullYear() + '-' + month + '-' + day + ' ' + hour + ':' + minute + ' BJT'

  return result
}

module.exports = {
  generateMarketsData: generateMarketsData,
  generateWatchlistData: generateWatchlistData,
  generateBriefingData: generateBriefingData,
  generateRadarData: generateRadarData,
  generateSparkline: generateSparkline,
  generatePrice: generatePrice,
  generateChange: generateChange,
  parsePrice: parsePrice,
  formatPrice: formatPrice,
  hashCode: hashCode,
  seededRandom: seededRandom
}
