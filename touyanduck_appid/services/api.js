/**
 * api.js — 统一数据服务层 v6.0
 * 只允许两类数据进入页面：
 *   1. 云数据库真实数据
 *   2. 上一次成功拉取后的本地缓存
 *
 * 严禁在云数据失败时自动降级到 Mock / 伪随机 / 估算数据。
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
 * 清除数据缓存（下拉刷新时调用，强制重新获取数据）
 */
function clearCache() {
  storage.remove('cache_briefing')
  storage.remove('cache_markets')
  storage.remove('cache_watchlist')
  storage.remove('cache_radar')
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
