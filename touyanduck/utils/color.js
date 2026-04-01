/**
 * color.js — 颜色与标签工具函数
 * 统一管理涨跌颜色、行动标签、风险等级的判断逻辑
 */

/**
 * 根据涨跌幅返回颜色 class 名
 * @param {number} change - 涨跌幅
 * @returns {string} 'color-up' | 'color-down' | 'color-flat'
 */
function getChangeColorClass(change) {
  if (change > 0) return 'color-up'
  if (change < 0) return 'color-down'
  return 'color-flat'
}

/**
 * 行动建议类型映射
 * @param {string} type - 'buy' | 'sell' | 'hold' | 'bullish' | 'bearish'
 * @returns {object} { label: 中文名, tagClass: 标签样式class }
 */
function getActionInfo(type) {
  const map = {
    buy:     { label: '买入', tagClass: 'tag-red' },
    bullish: { label: '看涨', tagClass: 'tag-orange' },
    hold:    { label: '观望', tagClass: 'tag-yellow' },
    bearish: { label: '看跌', tagClass: 'tag-blue' },
    sell:    { label: '卖出', tagClass: 'tag-green' }
  }
  return map[type] || { label: '观望', tagClass: 'tag-yellow' }
}

/**
 * 趋势方向映射
 * @param {string} trend - 'up' | 'down' | 'hold'
 * @returns {object} { label: 中文名, tagClass: 标签样式class }
 */
function getTrendInfo(trend) {
  const map = {
    up:   { label: '看多', tagClass: 'tag-red' },
    down: { label: '看空', tagClass: 'tag-green' },
    hold: { label: '中性', tagClass: 'tag-yellow' }
  }
  return map[trend] || { label: '中性', tagClass: 'tag-yellow' }
}

/**
 * 风险等级映射
 * @param {string} level - 'low' | 'medium' | 'high'
 * @returns {object} { label: 中文名, className: CSS class }
 */
function getRiskInfo(level) {
  const map = {
    low:    { label: '低风险', className: 'risk-low' },
    medium: { label: '中风险', className: 'risk-medium' },
    high:   { label: '高风险', className: 'risk-high' }
  }
  return map[level] || { label: '未知', className: 'risk-medium' }
}

/**
 * 事件影响等级映射
 * @param {string} impact - 'high' | 'medium' | 'low'
 * @returns {object} { label: 中文名, tagClass: 标签样式class }
 */
function getImpactInfo(impact) {
  const map = {
    high:   { label: '高影响', tagClass: 'tag-red' },
    medium: { label: '中影响', tagClass: 'tag-yellow' },
    low:    { label: '低影响', tagClass: 'tag-gray' }
  }
  return map[impact] || { label: '低影响', tagClass: 'tag-gray' }
}

/**
 * 异动监测级别映射
 * @param {string} level - 'danger' | 'warning' | 'info'
 * @returns {object} { icon: emoji, bgClass: 背景class }
 */
function getAlertInfo(level) {
  const map = {
    danger:  { icon: '🔴', bgClass: 'alert-danger' },
    warning: { icon: '🟡', bgClass: 'alert-warning' },
    info:    { icon: '🟢', bgClass: 'alert-info' }
  }
  return map[level] || { icon: '⚪', bgClass: 'alert-info' }
}

/**
 * 红绿灯状态映射
 * @param {string} status - 'green' | 'yellow' | 'red'
 * @returns {string} CSS class 名
 */
function getLightClass(status) {
  const map = {
    green: 'light-green',
    yellow: 'light-yellow',
    red: 'light-red'
  }
  return map[status] || 'light-yellow'
}

module.exports = {
  getChangeColorClass,
  getActionInfo,
  getTrendInfo,
  getRiskInfo,
  getImpactInfo,
  getAlertInfo,
  getLightClass
}
