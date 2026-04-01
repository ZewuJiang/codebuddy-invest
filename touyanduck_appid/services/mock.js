/**
 * mock.js — Mock 数据管理器
 * v3.0 — 使用动态 Mock 生成器，每日数据自动变化
 */

var dynamicMock = require('../utils/dynamic-mock')

// 缓存（同一次会话内不重复生成）
var _cache = {}

/**
 * 获取简报数据
 * @param {string} date
 * @returns {Promise<object>}
 */
function getBriefing(date) {
  return new Promise(function(resolve) {
    var delay = 300 + Math.random() * 300
    setTimeout(function() {
      if (!_cache.briefing) {
        _cache.briefing = dynamicMock.generateBriefingData()
      }
      resolve({
        success: true,
        data: JSON.parse(JSON.stringify(_cache.briefing))
      })
    }, delay)
  })
}

/**
 * 获取市场行情数据
 * @param {string} category
 * @returns {Promise<object>}
 */
function getMarkets(category) {
  return new Promise(function(resolve) {
    var delay = 200 + Math.random() * 300
    setTimeout(function() {
      if (!_cache.markets) {
        _cache.markets = dynamicMock.generateMarketsData()
      }
      resolve({
        success: true,
        data: JSON.parse(JSON.stringify(_cache.markets))
      })
    }, delay)
  })
}

/**
 * 获取标的列表数据
 * @param {string} sectorId
 * @returns {Promise<object>}
 */
function getWatchlist(sectorId) {
  return new Promise(function(resolve) {
    var delay = 200 + Math.random() * 300
    setTimeout(function() {
      if (!_cache.watchlist) {
        _cache.watchlist = dynamicMock.generateWatchlistData()
      }
      resolve({
        success: true,
        data: JSON.parse(JSON.stringify(_cache.watchlist))
      })
    }, delay)
  })
}

/**
 * 获取雷达数据
 * @returns {Promise<object>}
 */
function getRadar() {
  return new Promise(function(resolve) {
    var delay = 200 + Math.random() * 300
    setTimeout(function() {
      if (!_cache.radar) {
        _cache.radar = dynamicMock.generateRadarData()
      }
      resolve({
        success: true,
        data: JSON.parse(JSON.stringify(_cache.radar))
      })
    }, delay)
  })
}

/**
 * 清除缓存（下拉刷新时可选调用，强制重新生成）
 */
function clearCache() {
  _cache = {}
}

module.exports = {
  getBriefing: getBriefing,
  getMarkets: getMarkets,
  getWatchlist: getWatchlist,
  getRadar: getRadar,
  clearCache: clearCache
}
