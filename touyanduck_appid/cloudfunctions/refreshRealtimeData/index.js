/**
 * 云函数 refreshRealtimeData v1.0
 * 用途：拉取 CNN Fear & Greed 实时数据，写入云数据库 realtime 集合
 *
 * 触发方式：
 *   1. 定时触发（每天 08:00 BJT，在微信云开发控制台配置 cron: 0 0 8 * * * *）
 *   2. 小程序端主动调用（wx.cloud.callFunction({ name: 'refreshRealtimeData', data: { source: 'manual' } })）
 *
 * 数据写入结构（realtime 集合，文档 _id = "feargreed_YYYY-MM-DD"）：
 *   {
 *     _id: "feargreed_2026-04-02",
 *     date: "2026-04-02",
 *     fearGreed: {
 *       value: 35,
 *       label: "Fear",
 *       previousClose: 33,
 *       oneWeekAgo: 28,
 *       oneMonthAgo: 45,
 *       updatedAt: "2026-04-02T12:00:00.000Z"
 *     },
 *     _meta: {
 *       sourceType: "realtime_quote",
 *       source: "CNN Fear&Greed",
 *       updatedAt: "2026-04-02T12:00:00.000Z",
 *       triggeredBy: "timer"   // "timer" | "manual"
 *     }
 *   }
 */

var cloud = require('wx-server-sdk')

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })

// CNN Fear & Greed API 主机和路径（Node.js https 模块分开配置）
var CNN_HOSTNAME = 'production.dataviz.cnn.io'
var CNN_PATH = '/index/fearandgreed/graphdata'
var CNN_REFERER = 'https://edition.cnn.com'
var REQUEST_TIMEOUT_MS = 18000

/**
 * 获取北京时间的 YYYY-MM-DD 字符串
 * Node.js 云函数运行于 UTC，需手动偏移 +8 小时
 * @returns {string} 如 "2026-04-02"
 */
function getBJTDateISO() {
  var now = new Date()
  // UTC 毫秒 + 8小时偏移
  var bjtMs = now.getTime() + (now.getTimezoneOffset() + 8 * 60) * 60000
  var d = new Date(bjtMs)
  var month = String(d.getMonth() + 1).padStart(2, '0')
  var day = String(d.getDate()).padStart(2, '0')
  return d.getFullYear() + '-' + month + '-' + day
}

/**
 * 将 CNN fear_and_greed.rating 统一映射为标准英文标签
 * CNN API 返回值可能为小写或首字母大写，统一处理
 * @param {string} rating - CNN 原始 rating 字符串
 * @returns {string} 标准化标签
 */
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

/**
 * 从 CNN API 获取 Fear & Greed 数据（使用 Node.js 原生 https 模块）
 * @returns {Promise<object|null>} fearGreed 对象，失败或数据异常返回 null
 */
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

      // 设置编码，防止中文/特殊字符乱码
      res.setEncoding('utf8')

      res.on('data', function(chunk) {
        rawData += chunk
      })

      res.on('end', function() {
        // HTTP 状态码校验
        if (res.statusCode !== 200) {
          console.warn('[refreshRealtimeData] CNN API 返回异常状态码:', res.statusCode)
          resolve(null)
          return
        }

        try {
          var parsed = JSON.parse(rawData)
          var fg = parsed.fear_and_greed
          var hist = parsed.fear_and_greed_historical && parsed.fear_and_greed_historical.data

          // 核心字段校验
          if (!fg || fg.score === undefined || fg.score === null) {
            console.warn('[refreshRealtimeData] CNN API 返回结构异常，缺少 fear_and_greed.score')
            console.warn('[refreshRealtimeData] 原始响应片段:', JSON.stringify(parsed).slice(0, 300))
            resolve(null)
            return
          }

          var value = Math.round(Number(fg.score))

          // 从历史数据提取 previousClose / oneWeekAgo / oneMonthAgo
          // hist 数组每项为 { x: score, y: timestamp_ms }，按时间正序排列
          var prevClose   = null
          var oneWeekAgo  = null
          var oneMonthAgo = null

          if (Array.isArray(hist) && hist.length > 0) {
            var len = hist.length
            // hist[len-1] = 今天，hist[len-2] = 昨天（前收）
            if (len >= 2)  prevClose   = Math.round(Number(hist[len - 2].y))
            // 约 5 个交易日 ≈ 1 周，取 hist 倒数第 6 条（idx = len-6）
            if (len >= 6)  oneWeekAgo  = Math.round(Number(hist[len - 6].y))
            // 约 22 个交易日 ≈ 1 个月，取 hist 倒数第 23 条（idx = len-23）
            if (len >= 23) oneMonthAgo = Math.round(Number(hist[len - 23].y))
          }

          var result = {
            value:         value,
            label:         normalizeLabel(fg.rating),
            previousClose: prevClose,
            oneWeekAgo:    oneWeekAgo,
            oneMonthAgo:   oneMonthAgo,
            updatedAt:     new Date().toISOString()
          }

          console.log('[refreshRealtimeData] CNN 数据解析成功:', JSON.stringify(result))
          resolve(result)

        } catch (e) {
          console.error('[refreshRealtimeData] JSON 解析失败:', e.message)
          console.error('[refreshRealtimeData] 原始响应片段:', rawData.slice(0, 200))
          resolve(null)
        }
      })
    })

    // 请求超时处理
    req.on('timeout', function() {
      console.warn('[refreshRealtimeData] HTTPS 请求超时（' + REQUEST_TIMEOUT_MS + 'ms）')
      req.destroy()
      resolve(null)
    })

    // 网络错误处理
    req.on('error', function(e) {
      console.error('[refreshRealtimeData] HTTPS 请求失败:', e.message)
      resolve(null)
    })

    req.end()
  })
}

/**
 * 云函数入口
 * @param {object} event - 触发事件，可含 { source: 'manual' | 'timer' }
 * @param {object} context - 云函数上下文
 * @returns {Promise<object>} 执行结果
 */
exports.main = async function(event, context) {
  var today = getBJTDateISO()
  var docId = 'feargreed_' + today
  var triggeredBy = (event && event.source) ? event.source : 'timer'

  console.log('[refreshRealtimeData] 开始执行，日期:', today, '，触发来源:', triggeredBy)

  // ── 步骤1：拉取 CNN Fear & Greed 实时数据 ──
 
  var fearGreedData = null
  var maxRetries = 3
  for (var i = 1; i <= maxRetries; i++) {
    console.log('[refreshRealtimeData] 第 ' + i + ' 次尝试拉取 CNN 数据...')
    fearGreedData = await fetchCNNFearGreed()
    if (fearGreedData) {
      console.log('[refreshRealtimeData] 第 ' + i + ' 次尝试成功')
      break
    }
    if (i < maxRetries) {
      console.log('[refreshRealtimeData] 第 ' + i + ' 次失败，等待 2 秒后重试...')
      await new Promise(function(r) { setTimeout(r, 2000) })
    }
  }

  if (!fearGreedData) {
    console.warn('[refreshRealtimeData] CNN 数据获取失败，本次跳过写入（不阻断）')
    return {
      success: false,
      date: today,
      message: 'CNN Fear & Greed 数据获取失败，请检查网络或 API 端点',
      fearGreed: null
    }
  }

  // ── 步骤2：写入云数据库 realtime 集合（upsert）──
  // 使用 .doc(docId).set() 实现 upsert：文档存在则全量覆盖，不存在则新建
  var db = cloud.database()
  var doc = {
    date: today,
    fearGreed: fearGreedData,
    _meta: {
      sourceType: 'realtime_quote',
      source: 'CNN Fear&Greed',
      updatedAt: new Date().toISOString(),
      triggeredBy: triggeredBy
    }
  }

  try {
    var setRes = await db.collection('realtime').doc(docId).set({ data: doc })
    console.log('[refreshRealtimeData] 写入成功，docId:', docId, '，updated:', setRes.updated)
    return {
      success: true,
      date: today,
      docId: docId,
      fearGreed: fearGreedData
    }
  } catch (dbErr) {
    console.error('[refreshRealtimeData] 数据库写入失败:', dbErr.message || dbErr)
    return {
      success: false,
      date: today,
      message: '数据库写入失败: ' + (dbErr.message || String(dbErr)),
      fearGreed: fearGreedData
    }
  }
}
