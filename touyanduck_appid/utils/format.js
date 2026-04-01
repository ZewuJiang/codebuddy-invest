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
  const d = date || new Date()
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

/**
 * 获取 YYYY-MM-DD 格式日期
 * @param {Date} date - 日期对象
 * @returns {string} 如 "2026-03-31"
 */
function formatDateISO(date) {
  const d = date || new Date()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${month}-${day}`
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
  const parts = Number(num).toFixed(decimals).split('.')
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
  const prefix = showPlus && change > 0 ? '+' : ''
  return `${prefix}${Number(change).toFixed(2)}%`
}

/**
 * 格式化涨跌幅（简化版，不补零）
 * @param {number} change - 涨跌幅值
 * @returns {string} 如 "+4.2%"
 */
function formatChangeSimple(change) {
  if (change === null || change === undefined || isNaN(change)) return '--'
  const prefix = change > 0 ? '+' : ''
  return `${prefix}${change}%`
}

/**
 * 获取星期几的中文名
 * @param {Date} date - 日期对象
 * @returns {string} 如 "周一"
 */
function getWeekDayCN(date) {
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return days[(date || new Date()).getDay()]
}

/**
 * 时间戳转 HH:MM 格式
 * @param {string|number} time - 时间字符串或时间戳
 * @returns {string} 如 "23:30"
 */
function formatTime(time) {
  if (typeof time === 'string' && time.includes(':')) return time
  const d = new Date(time)
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}

module.exports = {
  formatDateCN,
  formatDateISO,
  formatNumber,
  formatChange,
  formatChangeSimple,
  getWeekDayCN,
  formatTime
}
