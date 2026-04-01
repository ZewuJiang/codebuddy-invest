/**
 * animate.js — 动画工具函数
 * 数字跳动、缓动函数等
 */

/**
 * easeOutCubic 缓动函数
 * @param {number} t - 进度（0~1）
 * @returns {number}
 */
function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3)
}

/**
 * easeOutExpo 缓动函数（更明显的减速效果）
 * @param {number} t - 进度（0~1）
 * @returns {number}
 */
function easeOutExpo(t) {
  return t === 1 ? 1 : 1 - Math.pow(2, -10 * t)
}

/**
 * 数字跳动动画
 * @param {object} options
 * @param {number} options.from - 起始值
 * @param {number} options.to - 目标值
 * @param {number} options.duration - 持续时间（ms），默认600
 * @param {number} options.decimals - 小数位数，默认1
 * @param {function} options.onUpdate - 每帧回调 (currentValue, formattedStr)
 * @param {function} options.onComplete - 完成回调
 * @returns {number} timer ID（可用于提前清除）
 */
function animateNumber(options) {
  var from = options.from || 0
  var to = options.to
  var duration = options.duration || 600
  var decimals = options.decimals !== undefined ? options.decimals : 1
  var onUpdate = options.onUpdate
  var onComplete = options.onComplete

  if (to === undefined || to === null || !onUpdate) return -1

  var startTime = Date.now()
  var timer = setInterval(function() {
    var elapsed = Date.now() - startTime
    var progress = Math.min(elapsed / duration, 1)
    var eased = easeOutCubic(progress)
    var current = from + (to - from) * eased

    // 格式化
    var formatted = current.toFixed(decimals)
    if (current > 0 && to > 0) formatted = '+' + formatted
    formatted = formatted + '%'

    onUpdate(current, formatted)

    if (progress >= 1) {
      clearInterval(timer)
      if (onComplete) onComplete(to)
    }
  }, 16) // ~60fps

  return timer
}

/**
 * 数字递增动画（整数版）
 * @param {object} options
 * @param {number} options.from
 * @param {number} options.to
 * @param {number} options.duration
 * @param {function} options.onUpdate - (currentInt)
 * @param {function} options.onComplete
 * @returns {number}
 */
function animateInteger(options) {
  var from = options.from || 0
  var to = options.to
  var duration = options.duration || 800
  var onUpdate = options.onUpdate
  var onComplete = options.onComplete

  if (to === undefined || !onUpdate) return -1

  var startTime = Date.now()
  var timer = setInterval(function() {
    var elapsed = Date.now() - startTime
    var progress = Math.min(elapsed / duration, 1)
    var eased = easeOutExpo(progress)
    var current = Math.round(from + (to - from) * eased)

    onUpdate(current)

    if (progress >= 1) {
      clearInterval(timer)
      if (onComplete) onComplete(to)
    }
  }, 16)

  return timer
}

/**
 * 生成依次延迟的动画 class 索引数组
 * @param {number} count - 项目数量
 * @param {number} baseDelay - 基础延迟（ms），默认50
 * @returns {Array<number>} 每项的延迟时间
 */
function staggerDelays(count, baseDelay) {
  baseDelay = baseDelay || 50
  var delays = []
  for (var i = 0; i < count; i++) {
    delays.push(i * baseDelay)
  }
  return delays
}

module.exports = {
  animateNumber: animateNumber,
  animateInteger: animateInteger,
  easeOutCubic: easeOutCubic,
  easeOutExpo: easeOutExpo,
  staggerDelays: staggerDelays
}
