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
 * @param {string} type - 具体操作类型
 * @returns {object} { label: 中文名, tagClass: 标签样式class }
 */
function getActionInfo(type) {
  var map = {
    // 具体操作类型（推荐使用）
    hold:     { label: '持有', tagClass: 'tag-yellow' },
    add:      { label: '加仓', tagClass: 'tag-red' },
    reduce:   { label: '减仓', tagClass: 'tag-green' },
    buy:      { label: '买入', tagClass: 'tag-red' },
    sell:     { label: '卖出', tagClass: 'tag-green' },
    watch:    { label: '关注', tagClass: 'tag-blue' },
    stoploss: { label: '止损', tagClass: 'tag-gray' },
    hedge:    { label: '对冲', tagClass: 'tag-orange' },
    // @deprecated 兼容旧格式（Skill 已禁止产出 bullish/bearish，仅保留防止旧数据崩溃）
    bullish:  { label: '看涨', tagClass: 'tag-orange' },
    bearish:  { label: '看跌', tagClass: 'tag-blue' }
  }
  return map[type] || { label: '持有', tagClass: 'tag-yellow' }
}

/**
 * 趋势方向映射
 * @param {string} trend - 'up' | 'down' | 'hold'
 * @returns {object} { label: 中文名, tagClass: 标签样式class }
 */
function getTrendInfo(trend) {
  var map = {
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
  var map = {
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
  var map = {
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
  var map = {
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
  var map = {
    green: 'light-green',
    yellow: 'light-yellow',
    red: 'light-red'
  }
  return map[status] || 'light-yellow'
}

/**
 * 预测市场趋势标签映射
 * @param {string} trend - 'up' | 'down' | 'stable' | 'hold'（hold 为 stable 的别名，统一兼容）
 * @returns {object} { arrow, colorClass }
 */
function getPredictionTrendInfo(trend) {
  var map = {
    up:     { arrow: '↑', colorClass: 'pm-trend-up' },
    down:   { arrow: '↓', colorClass: 'pm-trend-down' },
    stable: { arrow: '→', colorClass: 'pm-trend-stable' },
    hold:   { arrow: '→', colorClass: 'pm-trend-stable' }
  }
  return map[trend] || { arrow: '→', colorClass: 'pm-trend-stable' }
}

/**
 * 判断扩展字段：概率标签映射
 * @param {string} probability - '高可能性' | '中可能性' | '低可能性'
 * @returns {object} { tagClass }
 */
function getProbabilityInfo(probability) {
  var map = {
    '高可能性': { tagClass: 'jx-prob-high' },
    '中可能性': { tagClass: 'jx-prob-medium' },
    '低可能性': { tagClass: 'jx-prob-low' }
  }
  return map[probability] || { tagClass: 'jx-prob-medium' }
}

/**
 * 判断扩展字段：趋势方向映射
 * @param {string} trend - '上升' | '下降' | '稳定'
 * @returns {object} { arrow, tagClass }
 */
function getJudgmentTrendInfo(trend) {
  var map = {
    '上升': { arrow: '↑', tagClass: 'jx-trend-up' },
    '下降': { arrow: '↓', tagClass: 'jx-trend-down' },
    '稳定': { arrow: '→', tagClass: 'jx-trend-stable' }
  }
  return map[trend] || { arrow: '→', tagClass: 'jx-trend-stable' }
}

module.exports = {
  getChangeColorClass,
  getActionInfo,
  getTrendInfo,
  getRiskInfo,
  getImpactInfo,
  getAlertInfo,
  getLightClass,
  getPredictionTrendInfo,
  getProbabilityInfo,
  getJudgmentTrendInfo
}
