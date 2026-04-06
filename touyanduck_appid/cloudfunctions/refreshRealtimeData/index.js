/**
 * ⚠️ 已废弃（2026-04-06）
 * 原因：Fear & Greed 数据已从产品中移除，predictions 通过 radar.json 日报层覆盖。
 * 前端已移除 getRealtimeData() 调用，此云函数不再被触发。
 * 保留代码仅供参考，建议后续清理时删除此云函数及对应的定时触发器。
 *
 * 云函数 refreshRealtimeData v2.0（已废弃）
 * 用途：定时拉取实时数据，写入云数据库 realtime 集合
 *
 * v2.0 新增：
 *   - 在原有 CNN Fear & Greed 基础上，新增 Polymarket 预测市场数据抓取
 *   - realtime 文档新增 predictions[] 字段
 *   - 两个数据源独立抓取、独立降级，互不阻断
 *
 * 触发方式：
 *   1. 定时触发（每2小时，config.json 配置）
 *   2. 小程序端主动调用
 *
 * 数据写入结构（realtime 集合，文档 _id = "feargreed_YYYY-MM-DD"）：
 *   {
 *     _id: "feargreed_2026-04-02",
 *     date: "2026-04-02",
 *     fearGreed: { value, label, previousClose, oneWeekAgo, oneMonthAgo, updatedAt },
 *     predictions: [
 *       { title, source, probability, trend, change24h }
 *     ],
 *     _meta: {
 *       sourceType: "realtime_quote",
 *       source: "CNN Fear&Greed + Polymarket",
 *       updatedAt: "...",
 *       triggeredBy: "timer"
 *     }
 *   }
 */

var cloud = require('wx-server-sdk')

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

// ═══════════════════════════════════════════
// 通用工具函数
// ═══════════════════════════════════════════

/**
 * 获取北京时间的 YYYY-MM-DD 字符串
 */
function getBJTDateISO() {
  var now = new Date()
  var bjtMs = now.getTime() + (now.getTimezoneOffset() + 8 * 60) * 60000
  var d = new Date(bjtMs)
  var month = String(d.getMonth() + 1).padStart(2, '0')
  var day = String(d.getDate()).padStart(2, '0')
  return d.getFullYear() + '-' + month + '-' + day
}

// ═══════════════════════════════════════════
// 数据源 1：CNN Fear & Greed（原有逻辑，未改动）
// ═══════════════════════════════════════════

var CNN_HOSTNAME = 'production.dataviz.cnn.io'
var CNN_PATH = '/index/fearandgreed/graphdata'
var CNN_REFERER = 'https://edition.cnn.com'
var REQUEST_TIMEOUT_MS = 18000

function normalizeLabel(rating) {
  if (!rating) return 'Neutral'
  var map = {
    'extreme fear': 'Extreme Fear',
    'fear': 'Fear',
    'neutral': 'Neutral',
    'greed': 'Greed',
    'extreme greed': 'Extreme Greed'
  }
  return map[String(rating).toLowerCase()] || rating
}

function fetchCNNFearGreed() {
  return new Promise(function(resolve) {
    var https = require('https')
    var options = {
      hostname: CNN_HOSTNAME,
      path: CNN_PATH,
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; TouyanDuck/1.0)',
        'Accept': 'application/json',
        'Referer': CNN_REFERER
      },
      timeout: REQUEST_TIMEOUT_MS
    }

    var req = https.request(options, function(res) {
      var rawData = ''
      res.setEncoding('utf8')

      res.on('data', function(chunk) {
        rawData += chunk
      })

      res.on('end', function() {
        if (res.statusCode !== 200) {
          console.warn('[CNN] 状态码异常:', res.statusCode)
          resolve(null)
          return
        }

        try {
          var parsed = JSON.parse(rawData)
          var fg = parsed.fear_and_greed
          var hist = parsed.fear_and_greed_historical && parsed.fear_and_greed_historical.data

          if (!fg || fg.score === undefined || fg.score === null) {
            console.warn('[CNN] 返回结构异常')
            resolve(null)
            return
          }

          var value = Math.round(Number(fg.score))
          var prevClose   = null
          var oneWeekAgo  = null
          var oneMonthAgo = null

          if (Array.isArray(hist) && hist.length > 0) {
            var len = hist.length
            if (len >= 2)  prevClose   = Math.round(Number(hist[len - 2].y))
            if (len >= 6)  oneWeekAgo  = Math.round(Number(hist[len - 6].y))
            if (len >= 23) oneMonthAgo = Math.round(Number(hist[len - 23].y))
          }

          resolve({
            value:         value,
            label:         normalizeLabel(fg.rating),
            previousClose: prevClose,
            oneWeekAgo:    oneWeekAgo,
            oneMonthAgo:   oneMonthAgo,
            updatedAt:     new Date().toISOString()
          })

        } catch (e) {
          console.error('[CNN] JSON 解析失败:', e.message)
          resolve(null)
        }
      })
    })

    req.on('timeout', function() {
      console.warn('[CNN] 请求超时')
      req.destroy()
      resolve(null)
    })

    req.on('error', function(e) {
      console.error('[CNN] 请求失败:', e.message)
      resolve(null)
    })

    req.end()
  })
}

// ═══════════════════════════════════════════
// 数据源 2：Polymarket 预测市场（v2.0 新增）
// ═══════════════════════════════════════════

/**
 * 搜索关键词列表
 * 这些是我们关心的投资相关预测话题
 * 你可以根据需要增减关键词
 */
var POLYMARKET_KEYWORDS = [
  'fed rate',
  'recession',
  'tariff',
  'interest rate cut'
]

/**
 * 从 Polymarket Gamma API 搜索指定关键词的预测市场
 *
 * API 说明：
 *   Gamma API 是 Polymarket 的公开数据接口，不需要注册或 API Key
 *   GET https://gamma-api.polymarket.com/markets?closed=false&limit=3&query=关键词
 *   返回数组，每项含 question / outcomePrices / volume24hr 等字段
 *
 * @param {string} keyword - 搜索关键词
 * @returns {Promise<array>} 匹配的市场数据，失败返回空数组
 */
function searchPolymarket(keyword) {
  return new Promise(function(resolve) {
    var https = require('https')

    // 对关键词做 URL 编码（处理空格等特殊字符）
    var encodedQuery = encodeURIComponent(keyword)
    var path = '/markets?closed=false&active=true&limit=3&ascending=false&order=volume24hr&query=' + encodedQuery

    var options = {
      hostname: 'gamma-api.polymarket.com',
      path: path,
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; TouyanDuck/1.0)',
        'Accept': 'application/json'
      },
      timeout: 15000
    }

    var req = https.request(options, function(res) {
      var rawData = ''
      res.setEncoding('utf8')

      res.on('data', function(chunk) {
        rawData += chunk
      })

      res.on('end', function() {
        if (res.statusCode !== 200) {
          console.warn('[Polymarket] 搜索"' + keyword + '"状态码异常:', res.statusCode)
          resolve([])
          return
        }

        try {
          var markets = JSON.parse(rawData)
          if (!Array.isArray(markets)) {
            console.warn('[Polymarket] 搜索"' + keyword + '"返回非数组')
            resolve([])
            return
          }
          resolve(markets)
        } catch (e) {
          console.error('[Polymarket] 搜索"' + keyword + '"JSON解析失败:', e.message)
          resolve([])
        }
      })
    })

    req.on('timeout', function() {
      console.warn('[Polymarket] 搜索"' + keyword + '"超时')
      req.destroy()
      resolve([])
    })

    req.on('error', function(e) {
      console.error('[Polymarket] 搜索"' + keyword + '"请求失败:', e.message)
      resolve([])
    })

    req.end()
  })
}

/**
 * 从 Polymarket API 返回的单个市场数据中，提取概率
 *
 * outcomePrices 字段是一个 JSON 字符串，格式为 "[\"0.72\",\"0.28\"]"
 * 第一个数字就是 "Yes" 的概率（0-1 之间的小数）
 *
 * @param {object} market - Polymarket 单条市场数据
 * @returns {number|null} 概率百分比（0-100），解析失败返回 null
 */
function extractProbability(market) {
  try {
    if (!market.outcomePrices) return null
    var prices = JSON.parse(market.outcomePrices)
    if (Array.isArray(prices) && prices.length >= 1) {
      var prob = Math.round(Number(prices[0]) * 100)
      if (prob >= 0 && prob <= 100) return prob
    }
    return null
  } catch (e) {
    return null
  }
}

/**
 * 汇总所有关键词的搜索结果，去重并映射为 predictions schema
 *
 * 去重规则：同一个 conditionId 只保留第一个
 * 最终只取前 4 条（schema 规定 2-4 条）
 *
 * @returns {Promise<array>} predictions 数组，格式对齐 json-schema.md
 */
function fetchPolymarketPredictions() {
  // 同时搜索所有关键词（并发请求，更快）
  var promises = POLYMARKET_KEYWORDS.map(function(kw) {
    return searchPolymarket(kw)
  })

  return Promise.all(promises).then(function(results) {
    // 把所有搜索结果合并成一个大数组
    var allMarkets = []
    results.forEach(function(markets) {
      allMarkets = allMarkets.concat(markets)
    })

    // 去重：同一个 conditionId 只保留第一个
    var seen = {}
    var unique = []
    allMarkets.forEach(function(m) {
      var id = m.conditionId || m.question
      if (!seen[id]) {
        seen[id] = true
        unique.push(m)
      }
    })

    // 按交易量排序（最热门的排前面）
    unique.sort(function(a, b) {
      return (Number(b.volume24hr) || 0) - (Number(a.volume24hr) || 0)
    })

    // 取前 4 条，映射为 predictions schema
    var predictions = []
    for (var i = 0; i < Math.min(unique.length, 4); i++) {
      var m = unique[i]
      var prob = extractProbability(m)
      if (prob === null) continue   // 跳过无法解析概率的条目

      predictions.push({
        title:     m.question || '未知问题',
        source:    'Polymarket',
        probability: prob,
        trend:     'stable',        // Gamma API 不直接提供趋势，默认 stable
        change24h: 0                // 同上，暂无 24h 变化数据
      })
    }

    console.log('[Polymarket] 获取到', predictions.length, '条预测数据')
    return predictions

  }).catch(function(err) {
    console.error('[Polymarket] 汇总失败:', err && err.message)
    return []   // 失败返回空数组，不阻断主流程
  })
}

// ═══════════════════════════════════════════
// 云函数入口
// ═══════════════════════════════════════════

exports.main = async function(event, context) {
  var today = getBJTDateISO()
  var docId = 'feargreed_' + today
  var triggeredBy = (event && event.source) ? event.source : 'timer'

  console.log('[refreshRealtimeData] v2.0 开始执行，日期:', today, '，触发来源:', triggeredBy)

  // ── 第1步：并发拉取两个数据源 ──
  // 两个请求同时发出，互不等待，谁先回来算谁的
  // 任何一个失败都不影响另一个

  var fearGreedData = null
  var predictionsData = []

  try {
    var results = await Promise.all([
      // 数据源1：CNN Fear & Greed（带重试）
      (async function() {
        for (var i = 1; i <= 3; i++) {
          console.log('[CNN] 第', i, '次尝试...')
          var data = await fetchCNNFearGreed()
          if (data) return data
          if (i < 3) await new Promise(function(r) { setTimeout(r, 2000) })
        }
        return null
      })(),

      // 数据源2：Polymarket 预测市场（无重试，失败静默返回空数组）
      fetchPolymarketPredictions()
    ])

    fearGreedData = results[0]
    predictionsData = results[1] || []
  } catch (err) {
    console.error('[refreshRealtimeData] 并发拉取异常:', err && err.message)
  }

  // 如果两个数据源全部失败，跳过写入
  if (!fearGreedData && predictionsData.length === 0) {
    console.warn('[refreshRealtimeData] 所有数据源均失败，本次跳过写入')
    return {
      success: false,
      date: today,
      message: '所有数据源均失败',
      fearGreed: null,
      predictions: []
    }
  }

  // ── 第2步：写入云数据库 ──
  var db = cloud.database()

  // 构建要写入的文档（只包含成功获取到的数据）
  var doc = {
    date: today,
    _meta: {
      sourceType: 'realtime_quote',
      source: 'CNN Fear&Greed + Polymarket',
      updatedAt: new Date().toISOString(),
      triggeredBy: triggeredBy
    }
  }

  // 有 Fear & Greed 数据才写入这个字段
  if (fearGreedData) {
    doc.fearGreed = fearGreedData
  }

  // 有预测市场数据才写入这个字段
  if (predictionsData.length > 0) {
    doc.predictions = predictionsData
  }

  try {
    var setRes = await db.collection('realtime').doc(docId).set({ data: doc })
    console.log('[refreshRealtimeData] 写入成功，docId:', docId)
    console.log('[refreshRealtimeData] fearGreed:', fearGreedData ? '有' : '无',
                '，predictions:', predictionsData.length, '条')
    return {
      success: true,
      date: today,
      docId: docId,
      fearGreed: fearGreedData,
      predictions: predictionsData
    }
  } catch (dbErr) {
    console.error('[refreshRealtimeData] 数据库写入失败:', dbErr.message || dbErr)
    return {
      success: false,
      date: today,
      message: '数据库写入失败: ' + (dbErr.message || String(dbErr)),
      fearGreed: fearGreedData,
      predictions: predictionsData
    }
  }
}
