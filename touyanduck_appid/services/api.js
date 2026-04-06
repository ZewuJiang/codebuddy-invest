/**
 * api.js — 统一数据服务层 v6.1
 * 只允许两类数据进入页面：
 *   1. 云数据库真实数据
 *   2. 上一次成功拉取后的本地缓存
 *
 * 严禁在云数据失败时自动降级到 Mock / 伪随机 / 估算数据。
 *
 * v6.1 变更：
 *   - 新增 getRealtimeData()：查询 realtime 集合最新 fearGreed 实时数据（5分钟缓存）
 *   - clearCache() 追加清除 cache_realtime
 *   - module.exports 追加 getRealtimeData
 */

var storage = require('../utils/storage')

// 缓存有效期（分钟）
var CACHE_EXPIRE = 30

/**
 * 判断是否使用云数据库
 * 从 app.globalData 中读取配置，确保和 app.js 中的设置一致
 */
function isCloudMode() {
  try {
    var app = getApp()
    return app && app.globalData && app.globalData.useCloud && app.globalData.cloudReady
  } catch (e) {
    return false
  }
}

/**
 * 从云数据库查询数据
 * @param {string} collection - 集合名称（briefing/markets/watchlist/radar）
 * @param {string} date - 日期字符串（如 2026-03-31）
 * @returns {Promise<object>} - { success: true/false, data: {...} }
 */
function queryCloud(collection, date) {
  return new Promise(function(resolve) {
    if (!wx.cloud) {
      console.warn('[API] wx.cloud 不可用')
      resolve({ success: false, data: null })
      return
    }

    var db = wx.cloud.database()

    db.collection(collection)
      .where({ date: date })
      .orderBy('_updateTime', 'desc')
      .limit(1)
      .get()
      .then(function(res) {
        if (res.data && res.data.length > 0) {
          console.log('[API] 云数据库命中:', collection, date)
          resolve({ success: true, data: res.data[0] })
        } else {
          console.log('[API] 指定日期无数据，取最新:', collection)
          return db.collection(collection)
            .orderBy('date', 'desc')
            .limit(1)
            .get()
            .then(function(latestRes) {
              if (latestRes.data && latestRes.data.length > 0) {
                resolve({ success: true, data: latestRes.data[0] })
              } else {
                console.log('[API] 云数据库无任何数据:', collection)
                resolve({ success: false, data: null })
              }
            })
        }
      })
      .catch(function(err) {
        console.warn('[API] 云数据库查询失败:', collection, err)
        resolve({ success: false, data: null })
      })
  })
}

/**
 * 读取本地缓存数据
 * @param {string} key - 缓存键（briefing/markets/watchlist/radar）
 * @returns {object|null}
 */
function getCache(key) {
  return storage.get('cache_' + key, null)
}

/**
 * 通用数据获取函数
 * 优先级：云数据库 → 已存在本地缓存
 * 不再提供任何 Mock 自动回退。
 *
 * @param {string} collection - 集合名称
 * @param {string} cacheKey - 缓存键
 * @returns {Promise<object>}
 */
function fetchData(collection, cacheKey) {
  var cached = storage.get(cacheKey, null)

  if (!isCloudMode()) {
    console.warn('[API] 当前未启用云数据模式，仅可使用已有本地缓存:', collection)
    return Promise.resolve(cached || { success: false, data: null, error: 'CLOUD_DISABLED' })
  }

  var app = getApp()
  var date = app.globalData.currentDateISO || new Date().toISOString().slice(0, 10)

  return queryCloud(collection, date).then(function(cloudRes) {
    if (cloudRes.success && cloudRes.data) {
      var result = { success: true, data: cloudRes.data }
      storage.set(cacheKey, result, CACHE_EXPIRE)
      return result
    }

    if (cached && cached.success && cached.data) {
      console.warn('[API] 云数据暂不可用，回退到上一次本地缓存:', collection)
      return cached
    }

    console.warn('[API] 云数据与本地缓存均不可用:', collection)
    return { success: false, data: null, error: 'CLOUD_UNAVAILABLE' }
  })
}

/**
 * 获取每日简报数据
 * @param {string} date - 日期字符串（如 2026-03-31）
 * @returns {Promise<object>}
 */
function getBriefing(date) {
  return fetchData('briefing', 'cache_briefing')
}

/**
 * 获取市场行情数据
 * @param {string} category - 市场分类
 * @returns {Promise<object>}
 */
function getMarkets(category) {
  return fetchData('markets', 'cache_markets')
}

/**
 * 获取标的列表数据
 * @param {string} sectorId - 板块ID
 * @returns {Promise<object>}
 */
function getWatchlist(sectorId) {
  return fetchData('watchlist', 'cache_watchlist')
}

/**
 * 获取雷达数据
 * @returns {Promise<object>}
 */
function getRadar() {
  return fetchData('radar', 'cache_radar')
}

/**
 * 获取实时数据（由云函数 refreshRealtimeData 写入的 realtime 集合）
 *
 * 查询逻辑：
 *   1. 根据当前北京日期构造 docId = "feargreed_YYYY-MM-DD"
 *   2. 命中云数据库则写入 5 分钟本地缓存并返回
 *   3. 未命中则返回本地缓存（若有）
 *   4. 任何异常均静默返回 null，不阻断主流程
 *
 * 缓存时间：5 分钟（相比日报层 30 分钟更激进刷新）
 *
 * @returns {Promise<object|null>} realtime 文档数据，云函数未运行/失败时返回 null
 */
function getRealtimeData() {
  var REALTIME_CACHE_EXPIRE = 5
  var cacheKey = 'cache_realtime'
  var cached = storage.get(cacheKey, null)

  // 非云模式：直接返回本地缓存（可能为 null）
  if (!isCloudMode()) {
    return Promise.resolve(cached ? cached.data : null)
  }

  if (!wx.cloud) {
    return Promise.resolve(cached ? cached.data : null)
  }

  var db = wx.cloud.database()
  var app = getApp()
  var date = app.globalData.currentDateISO || new Date().toISOString().slice(0, 10)
  var docId = 'feargreed_' + date

  return db.collection('realtime')
    .doc(docId)
    .get()
    .then(function(res) {
      if (res.data) {
        console.log('[API] 实时数据命中，F&G value:', res.data.fearGreed && res.data.fearGreed.value)
        var result = { success: true, data: res.data }
        storage.set(cacheKey, result, REALTIME_CACHE_EXPIRE)
        return res.data
      }
      // docId 不存在但请求成功（res.data 为 null）
      console.log('[API] 实时数据暂无（云函数今日尚未执行或 docId 不存在）:', docId)
      return cached ? cached.data : null
    })
    .catch(function(err) {
      // 静默降级：文档不存在时云数据库会抛 errCode: -1，此处统一不打印 warn
      console.log('[API] 实时数据不可用，静默降级:', err && err.errMsg)
      return cached ? cached.data : null
    })
}

/**
 * 清除数据缓存（下拉刷新时调用，强制重新获取数据）
 */
function clearCache() {
  storage.remove('cache_briefing')
  storage.remove('cache_markets')
  storage.remove('cache_watchlist')
  storage.remove('cache_radar')
  storage.remove('cache_realtime')
}

module.exports = {
  getBriefing: getBriefing,
  getMarkets: getMarkets,
  getWatchlist: getWatchlist,
  getRadar: getRadar,
  getCache: getCache,
  clearCache: clearCache,
  isCloudMode: isCloudMode
}
