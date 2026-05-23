/**
 * api.js — 统一数据服务层 v8.0
 * 数据来源：自建服务器 HTTPS 静态 JSON（替代微信云开发）
 *
 * 优先级：HTTP 接口 → 本地缓存
 * 严禁在接口失败时自动降级到 Mock / 伪随机 / 估算数据。
 */

var storage = require('../utils/storage')

// 缓存有效期（分钟）
var CACHE_EXPIRE = 30

/**
 * 判断是否可以使用 HTTP API 模式
 * 只要 apiBaseUrl 配置了就返回 true
 */
function isCloudMode() {
  try {
    var app = getApp()
    return !!(app && app.globalData && app.globalData.apiBaseUrl)
  } catch (e) {
    return false
  }
}

/**
 * 通过 HTTPS 请求自建服务器获取 JSON 数据
 * @param {string} collection - briefing / markets / watchlist / radar
 * @returns {Promise<object>} - { success: true/false, data: {...} }
 */
function queryHttp(collection) {
  return new Promise(function(resolve) {
    var app = getApp()
    var baseUrl = app && app.globalData && app.globalData.apiBaseUrl

    if (!baseUrl) {
      console.warn('[API] apiBaseUrl 未配置')
      resolve({ success: false, data: null })
      return
    }

    wx.request({
      url: baseUrl + '/' + collection + '.json',
      method: 'GET',
      timeout: 10000,
      success: function(res) {
        if (res.statusCode === 200 && res.data && typeof res.data === 'object') {
          console.log('[API] HTTP 命中:', collection)
          resolve({ success: true, data: res.data })
        } else {
          console.warn('[API] HTTP 异常状态:', collection, res.statusCode)
          resolve({ success: false, data: null })
        }
      },
      fail: function(err) {
        console.warn('[API] HTTP 请求失败:', collection, err)
        resolve({ success: false, data: null })
      }
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
 * 优先级：HTTP 接口 → 已存在本地缓存
 * 不再提供任何 Mock 自动回退。
 *
 * @param {string} collection - 集合名称
 * @param {string} cacheKey - 缓存键
 * @returns {Promise<object>}
 */
function fetchData(collection, cacheKey) {
  var cached = storage.get(cacheKey, null)

  if (!isCloudMode()) {
    console.warn('[API] 当前未配置 apiBaseUrl，仅可使用已有本地缓存:', collection)
    return Promise.resolve(cached || { success: false, data: null, error: 'API_DISABLED' })
  }

  return queryHttp(collection).then(function(httpRes) {
    if (httpRes.success && httpRes.data) {
      var result = { success: true, data: httpRes.data }
      storage.set(cacheKey, result, CACHE_EXPIRE)
      return result
    }

    if (cached && cached.success && cached.data) {
      console.warn('[API] HTTP 接口暂不可用，回退到上一次本地缓存:', collection)
      return cached
    }

    console.warn('[API] HTTP 接口与本地缓存均不可用:', collection)
    return { success: false, data: null, error: 'API_UNAVAILABLE' }
  })
}

/**
 * 获取每日简报数据
 * @returns {Promise<object>}
 */
function getBriefing() {
  return fetchData('briefing', 'cache_briefing')
}

/**
 * 获取市场行情数据
 * @returns {Promise<object>}
 */
function getMarkets() {
  return fetchData('markets', 'cache_markets')
}

/**
 * 获取标的列表数据
 * @returns {Promise<object>}
 */
function getWatchlist() {
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
