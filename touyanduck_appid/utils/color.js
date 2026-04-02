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
  const map = {
    // 具体操作类型（推荐使用）
    hold:     { label: '持有', tagClass: 'tag-yellow' },
    add:      { label: '加仓', tagClass: 'tag-red' },
    reduce:   { label: '减仓', tagClass: 'tag-green' },
    buy:      { label: '买入', tagClass: 'tag-red' },
    sell:     { label: '卖出', tagClass: 'tag-green' },
    watch:    { label: '关注', tagClass: 'tag-blue' },
    stoploss: { label: '止损', tagClass: 'tag-gray' },
    hedge:    { label: '对冲', tagClass: 'tag-orange' },
    // 兼容旧格式
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

/**
 * KEY DELTA 状态标签映射
 * @param {string} status - '升级' | '新增' | '活跃' | '降温' | '稳定'
 * @returns {object} { label, tagClass, heatLabel }
 */
function getDeltaStatusInfo(status) {
  var map = {
    '升级':  { label: '升级', tagClass: 'kd-tag-upgrade' },
    '新增':  { label: '新增', tagClass: 'kd-tag-new' },
    '活跃':  { label: '活跃', tagClass: 'kd-tag-active' },
    '降温':  { label: '降温', tagClass: 'kd-tag-cool' },
    '稳定':  { label: '稳定', tagClass: 'kd-tag-stable' }
  }
  return map[status] || { label: status || '活跃', tagClass: 'kd-tag-active' }
}

/**
 * 根据热度值返回文字标签（三档制）
 * @param {number} heat - 1-5（JSON原始值）
 * @returns {string} "加速" | "活跃" | "关注"
 *
 * 三档映射规则（与 briefing.js 及前端 dot 渲染完全一致）：
 *   heat ≥ 4 → ●●● 加速（宏观/地缘突发冲击、市场结构性拐点）
 *   heat = 3 → ●●○ 活跃（重要但不紧迫的行业进展、企业战略投资）
 *   heat ≤ 2 → ●○○ 关注（背景信息、趋势性缓慢演变）
 *
 * ⚠️ 注意：旧的5档逻辑（加速中/活跃/关注/降温/平淡）已废弃。
 *   JSON 数据层仍存储 1-5 整数，前端/工具函数统一按三档归一显示。
 */
function getHeatLabel(heat) {
  if (heat >= 4) return '加速'
  if (heat >= 3) return '活跃'
  return '关注'
}

/**
 * Fear & Greed 指数信息映射
 * @param {number} value - 0-100
 * @param {string} label - 英文标签
 * @returns {object} { cnLabel, colorClass, emoji }
 */
function getFearGreedInfo(value, label) {
  if (value <= 25) return { cnLabel: '极度恐惧', colorClass: 'fg-extreme-fear', emoji: '😱' }
  if (value <= 40) return { cnLabel: '恐惧', colorClass: 'fg-fear', emoji: '😰' }
  if (value <= 60) return { cnLabel: '中性', colorClass: 'fg-neutral', emoji: '😐' }
  if (value <= 75) return { cnLabel: '贪婪', colorClass: 'fg-greed', emoji: '😊' }
  return { cnLabel: '极度贪婪', colorClass: 'fg-extreme-greed', emoji: '🤑' }
}

/**
 * 预测市场趋势标签映射
 * @param {string} trend - 'up' | 'down' | 'stable'
 * @returns {object} { arrow, colorClass }
 */
function getPredictionTrendInfo(trend) {
  var map = {
    up:     { arrow: '↑', colorClass: 'pm-trend-up' },
    down:   { arrow: '↓', colorClass: 'pm-trend-down' },
    stable: { arrow: '→', colorClass: 'pm-trend-stable' }
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
  getDeltaStatusInfo,
  getHeatLabel,
  getFearGreedInfo,
  getPredictionTrendInfo,
  getProbabilityInfo,
  getJudgmentTrendInfo
}
