/**
 * format.js — 通用格式化工具函数
 * 日期、数字、百分比等格式化统一管理
 */

/**
 * 获取格式化的中文日期字符串
 * @param {Date} date - 日期对象，默认今天
 * @returns {string} 如 "2026年3月31日"
 */
function formatDateCN(date) {
  var d = date || new Date()
  return d.getFullYear() + '年' + (d.getMonth() + 1) + '月' + d.getDate() + '日'
}

/**
 * 获取 YYYY-MM-DD 格式日期
 * @param {Date} date - 日期对象
 * @returns {string} 如 "2026-03-31"
 */
function formatDateISO(date) {
  var d = date || new Date()
  var month = String(d.getMonth() + 1).padStart(2, '0')
  var day = String(d.getDate()).padStart(2, '0')
  return d.getFullYear() + '-' + month + '-' + day
}

/**
 * 格式化数字为千分位
 * @param {number|string} num - 数字
 * @param {number} decimals - 小数位数，默认2
 * @returns {string} 如 "5,254.35"
 */
function formatNumber(num, decimals) {
  if (num === null || num === undefined || isNaN(num)) return '--'
  decimals = decimals !== undefined ? decimals : 2
  var parts = Number(num).toFixed(decimals).split('.')
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return parts.join('.')
}

/**
 * 格式化涨跌幅百分比
 * @param {number} change - 涨跌幅值
 * @param {boolean} showPlus - 是否显示+号，默认true
 * @returns {string} 如 "+4.20%"
 */
function formatChange(change, showPlus) {
  if (change === null || change === undefined || isNaN(change)) return '--'
  showPlus = showPlus !== undefined ? showPlus : true
  var prefix = showPlus && change > 0 ? '+' : ''
  return prefix + Number(change).toFixed(2) + '%'
}

/**
 * 格式化涨跌幅（简化版，不补零）
 * @param {number} change - 涨跌幅值
 * @returns {string} 如 "+4.2%"
 */
function formatChangeSimple(change) {
  if (change === null || change === undefined || isNaN(change)) return '--'
  var prefix = change > 0 ? '+' : ''
  return prefix + change + '%'
}

/**
 * 获取星期几的中文名
 * @param {Date} date - 日期对象
 * @returns {string} 如 "周一"
 */
function getWeekDayCN(date) {
  var days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return days[(date || new Date()).getDay()]
}

/**
 * 时间戳转 HH:MM 格式
 * @param {string|number} time - 时间字符串或时间戳
 * @returns {string} 如 "23:30"
 */
function formatTime(time) {
  if (typeof time === 'string' && time.includes(':')) return time
  var d = new Date(time)
  var h = String(d.getHours()).padStart(2, '0')
  var m = String(d.getMinutes()).padStart(2, '0')
  return h + ':' + m
}

/**
 * 获取多时区时间信息
 * @returns {object} { bjt: "22:30", est: "10:30", bjtLabel: "Beijing", estLabel: "New York" }
 */
function getMultiTimezone() {
  var now = new Date()
  // 北京时间 UTC+8
  var bjtOffset = 8 * 60
  var bjtMs = now.getTime() + (now.getTimezoneOffset() + bjtOffset) * 60000
  var bjtDate = new Date(bjtMs)
  var bjt = String(bjtDate.getHours()).padStart(2, '0') + ':' + String(bjtDate.getMinutes()).padStart(2, '0')

  // 美东时间：判断夏令时（3月第二个周日～11月第一个周日）
  // estOffset 为负数（EDT=-240, EST=-300），与 bjtOffset 保持同一符号方向
  var estOffset = _isUSEasternDST(now) ? -4 * 60 : -5 * 60
  var estMs = now.getTime() + (now.getTimezoneOffset() + estOffset) * 60000
  var estDate = new Date(estMs)
  var est = String(estDate.getHours()).padStart(2, '0') + ':' + String(estDate.getMinutes()).padStart(2, '0')

  return {
    bjt: bjt,
    est: est,
    bjtLabel: 'Beijing',
    estLabel: 'New York',
    bjtWeekday: getWeekDayCN(bjtDate),
    estWeekday: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][estDate.getDay()]
  }
}

/**
 * 判断美东夏令时（3月第二个周日 02:00 ～ 11月第一个周日 02:00）
 * @param {Date} d - UTC 时间
 * @returns {boolean}
 */
function _isUSEasternDST(d) {
  var year = d.getUTCFullYear()
  // 3月第二个周日
  var mar1 = new Date(Date.UTC(year, 2, 1))
  var marSun2 = new Date(Date.UTC(year, 2, 8 + (7 - mar1.getUTCDay()) % 7, 7, 0)) // UTC 07:00 = ET 02:00
  // 11月第一个周日
  var nov1 = new Date(Date.UTC(year, 10, 1))
  var novSun1 = new Date(Date.UTC(year, 10, 1 + (7 - nov1.getUTCDay()) % 7, 6, 0)) // UTC 06:00 = ET 02:00 (EDT→EST)
  return d >= marSun2 && d < novSun1
}

/**
 * 获取美股开市状态
 * @returns {string} 枚举：美股交易中 / 美股已收盘 / 盘前交易 / 盘后交易
 */
function getMarketStatus() {
  var now = new Date()
  var isDST = _isUSEasternDST(now)
  var estOffset = isDST ? -4 : -5
  var estMs = now.getTime() + (now.getTimezoneOffset() + estOffset * 60) * 60000
  var estDate = new Date(estMs)
  var day = estDate.getDay()
  var h = estDate.getHours()
  var m = estDate.getMinutes()
  var minutes = h * 60 + m

  // 周末
  if (day === 0 || day === 6) return '美股已收盘'

  // 盘前 04:00-09:30 ET
  if (minutes >= 240 && minutes < 570) return '盘前交易'
  // 正式交易 09:30-16:00 ET
  if (minutes >= 570 && minutes < 960) return '美股交易中'
  // 盘后 16:00-20:00 ET
  if (minutes >= 960 && minutes < 1200) return '盘后交易'

  return '美股已收盘'
}

/**
 * 计算相对时间文本
 * @param {string} dateStr - 日期字符串（ISO 8601 或 "YYYY-MM-DD HH:MM BJT" 格式）
 * @returns {string} 如 "3分钟前"、"2小时前"、"昨天 09:00"
 */
function getRelativeTime(dateStr) {
  if (!dateStr) return ''
  var parts = null  // 提升到顶部，避免非BJT分支时引用未定义变量
  var target
  if (dateStr.includes('T')) {
    target = new Date(dateStr)
  } else if (dateStr.includes('BJT')) {
    // "2026-04-01 09:00 BJT" → 解析为北京时间
    parts = dateStr.replace(' BJT', '').split(' ')
    var dateParts = parts[0].split('-')
    var timeParts = (parts[1] || '00:00').split(':')
    target = new Date(dateParts[0], dateParts[1] - 1, dateParts[2], timeParts[0], timeParts[1] || 0)
  } else {
    target = new Date(dateStr)
  }

  if (isNaN(target.getTime())) return dateStr

  var diff = Date.now() - target.getTime()
  if (diff < 0) return '刚刚'

  var minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return minutes + '分钟前'

  var hours = Math.floor(minutes / 60)
  if (hours < 24) return hours + '小时前'

  var days = Math.floor(hours / 24)
  if (days === 1) return '昨天 ' + formatTime(target)
  if (days < 7) return days + '天前'

  // parts 仅在 BJT 分支中有值；其他格式直接截取前10位
  return parts ? parts[0] : dateStr.slice(0, 10)
}

module.exports = {
  formatDateCN,
  formatDateISO,
  formatNumber,
  formatChange,
  formatChangeSimple,
  getWeekDayCN,
  formatTime,
  getMultiTimezone,
  getMarketStatus,
  getRelativeTime
}
