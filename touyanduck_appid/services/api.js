/**
 * api.js — 统一数据服务层 v5.0
 * 支持两种数据源：
 *   1. Mock数据（默认）— 本地伪随机数据，用于开发和演示
 *   2. 云数据库（开通后切换）— 真实日报数据，从微信云数据库读取
 * 
 * 页面层代码零改动，数据源切换对上层完全透明。
 * 
 * v5.0 变更：
 *   - 新增云数据库直接读取模式（不需要云函数）
 *   - 自动降级：云数据库读取失败 → 自动回退到Mock数据
 *   - 保留本地缓存策略（秒开 + 后台静默刷新）
 */

var mock = require('./mock')
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

    // 先查指定日期的数据
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
          // 没有指定日期的数据，取最新一条
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
 * 通用数据获取函数（含自动降级逻辑）
 * 优先级：缓存 → 云数据库 → Mock数据
 * 
 * @param {string} collection - 集合名称
 * @param {string} cacheKey - 缓存键
 * @param {Function} mockFn - Mock数据获取函数
 * @param {*} mockArg - 传给 mockFn 的参数
 * @returns {Promise<object>}
 */
function fetchData(collection, cacheKey, mockFn, mockArg) {
  if (isCloudMode()) {
    // 云模式：从云数据库读取
    var app = getApp()
    var date = app.globalData.currentDateISO || new Date().toISOString().slice(0, 10)

    return queryCloud(collection, date).then(function(cloudRes) {
      if (cloudRes.success && cloudRes.data) {
        // 云数据读取成功，缓存并返回
        var result = { success: true, data: cloudRes.data }
        storage.set(cacheKey, result, CACHE_EXPIRE)
        return result
      } else {
        // 云数据读取失败，降级到Mock
        console.log('[API] 云数据不可用，降级到Mock:', collection)
        return mockFn(mockArg).then(function(mockRes) {
          if (mockRes.success) {
            storage.set(cacheKey, mockRes, CACHE_EXPIRE)
          }
          return mockRes
        })
      }
    })
  } else {
    // Mock模式
    return mockFn(mockArg).then(function(res) {
      if (res.success) {
        storage.set(cacheKey, res, CACHE_EXPIRE)
      }
      return res
    })
  }
}

/**
 * 获取每日简报数据
 * @param {string} date - 日期字符串（如 2026-03-31）
 * @returns {Promise<object>}
 */
function getBriefing(date) {
  return fetchData('briefing', 'cache_briefing', mock.getBriefing, date)
}

/**
 * 获取市场行情数据
 * @param {string} category - 市场分类
 * @returns {Promise<object>}
 */
function getMarkets(category) {
  return fetchData('markets', 'cache_markets', mock.getMarkets, category)
}

/**
 * 获取标的列表数据
 * @param {string} sectorId - 板块ID
 * @returns {Promise<object>}
 */
function getWatchlist(sectorId) {
  return fetchData('watchlist', 'cache_watchlist', mock.getWatchlist, sectorId)
}

/**
 * 获取雷达数据
 * @returns {Promise<object>}
 */
function getRadar() {
  return fetchData('radar', 'cache_radar', mock.getRadar, undefined)
}

/**
 * 读取本地缓存数据
 * @param {string} key - 缓存键（briefing/markets/watchlist/radar）
 * @returns {object|null} 缓存的数据，过期或不存在返回 null
 */
function getCache(key) {
  return storage.get('cache_' + key, null)
}

/**
 * 清除数据缓存（下拉刷新时调用，强制重新获取数据）
 */
function clearCache() {
  if (!isCloudMode()) {
    mock.clearCache()
  }
  // 同时清除本地持久缓存
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
