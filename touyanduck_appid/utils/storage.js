/**
 * storage.js — 本地缓存封装
 * 统一管理 wx.setStorageSync / getStorageSync
 */

var CACHE_PREFIX = 'touyanduck_'

/**
 * 写入缓存
 * @param {string} key - 缓存键
 * @param {any} value - 缓存值
 * @param {number} expireMinutes - 过期时间（分钟），0表示不过期
 */
function set(key, value, expireMinutes) {
  var data = {
    value: value,
    timestamp: Date.now(),
    expire: expireMinutes ? expireMinutes * 60 * 1000 : 0
  }
  try {
    wx.setStorageSync(CACHE_PREFIX + key, JSON.stringify(data))
  } catch (e) {
    console.warn('[Storage] 写入失败:', key, e)
  }
}

/**
 * 读取缓存
 * @param {string} key - 缓存键
 * @param {any} defaultValue - 默认值（缓存不存在或过期时返回）
 * @returns {any}
 */
function get(key, defaultValue) {
  try {
    var raw = wx.getStorageSync(CACHE_PREFIX + key)
    if (!raw) return defaultValue !== undefined ? defaultValue : null
    
    var data = JSON.parse(raw)
    if (data.expire && (Date.now() - data.timestamp > data.expire)) {
      remove(key)
      return defaultValue !== undefined ? defaultValue : null
    }
    return data.value
  } catch (e) {
    console.warn('[Storage] 读取失败:', key, e)
    return defaultValue !== undefined ? defaultValue : null
  }
}

/**
 * 删除缓存
 * @param {string} key - 缓存键
 */
function remove(key) {
  try {
    wx.removeStorageSync(CACHE_PREFIX + key)
  } catch (e) {
    console.warn('[Storage] 删除失败:', key, e)
  }
}

/**
 * 清除所有投研鸭缓存
 */
function clearAll() {
  try {
    var res = wx.getStorageInfoSync()
    var keys = res.keys || []
    keys.forEach(function(k) {
      if (k.startsWith(CACHE_PREFIX)) {
        wx.removeStorageSync(k)
      }
    })
  } catch (e) {
    console.warn('[Storage] 清除失败:', e)
  }
}

module.exports = {
  set,
  get,
  remove,
  clearAll
}
