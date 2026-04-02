// pages/radar/radar.js
// 雷达页 v5.2 — 双层数据合并：AI日报层（radar集合）+ 实时层（realtime集合）
// v5.2 变更：
//   - predictions 也支持双层合并：实时层 Polymarket 优先，AI日报兜底
//   - _meta 合并逻辑扩展：fearGreed 或 predictions 任一来自实时层，即标记 realtime_quote
// v5.1 变更：
//   - fetchData() 改为 Promise.all 并发拉取 radar + realtime 两层数据
//   - _applyData() 新增第三参数 realtimeData，实时 fearGreed 优先，AI日报兜底
//   - onLoad 缓存预渲染路径仍走单层（保持快速秒开）

var api = require('../../services/api')
var colorUtil = require('../../utils/color')
var formatUtil = require('../../utils/format')
var animate = require('../../utils/animate')

Page({
  data: {
    loading: true,
    // v1.3 Fear & Greed
    fearGreed: null,
    displayFGValue: 0,
    fgInfo: null,
    fgPrevDiff: 0,
    fgWeekDiff: 0,
    // v1.3 预测市场
    predictions: [],
    // 红绿灯
    trafficLights: [],
    riskScore: 0,
    displayRiskScore: 0,
    riskLevel: 'low',
    riskLabel: '低风险',
    riskClassName: 'risk-low',
    riskAdvice: '',
    monitorTable: [],
    riskAlerts: [],
    events: [],
    alerts: [],
    smartMoneyDetail: [],
    dataTime: '',
    dataFreshness: '',
    dataMeta: null,
    isCloud: false,
    animateReady: false
  },

  _animTimer: null,
  _fgAnimTimer: null,

  onLoad: function() {
    this.setData({ isCloud: api.isCloudMode() })
    // 缓存优先秒开
    var cached = api.getCache('radar')
    if (cached && cached.success && cached.data) {
      this._applyData(cached.data, false)
      this.fetchData(false, true)
    } else {
      this.fetchData()
    }
  },

  onUnload: function() {
    if (this._animTimer) clearInterval(this._animTimer)
    if (this._fgAnimTimer) clearInterval(this._fgAnimTimer)
  },

  onPullDownRefresh: function() {
    api.clearCache()
    this.fetchData(true)
  },

  fetchData: function(isRefresh, isSilent) {
    var that = this
    if (!isRefresh && !isSilent) {
      that.setData({ loading: true, animateReady: false })
    }

    // 并发拉取：AI日报层 + 实时层
    // 实时层用独立 .catch() 包裹，失败静默返回 null，不阻断主流程
    Promise.all([
      api.getRadar(),
      api.getRealtimeData().catch(function(err) {
        console.log('[Radar] 实时层获取异常，静默降级:', err && err.message)
        return null
      })
    ]).then(function(results) {
      var radarRes     = results[0]
      var realtimeData = results[1]   // object | null（静默降级时为 null）

      if (radarRes.success && radarRes.data) {
        that._applyData(radarRes.data, !isSilent, realtimeData)
      } else if (!isSilent) {
        that.setData({ loading: false })
      }

      if (isRefresh) {
        wx.stopPullDownRefresh()
        wx.showToast({ title: '已更新至最新', icon: 'success', duration: 1500 })
      }
    }).catch(function(err) {
      console.error('[Radar] 数据加载失败:', err)
      if (!isSilent) {
        that.setData({ loading: false })
      }
      if (isRefresh) {
        wx.stopPullDownRefresh()
        wx.showToast({ title: '更新失败', icon: 'none' })
      }
    })
  },

  /**
   * 将数据映射到页面 state
   * @param {object} data          - AI日报层数据（来自 radar 集合）
   * @param {boolean} withAnimation - 是否执行数字滚动动画
   * @param {object|null} realtimeData - 实时层数据（来自 realtime 集合），可为 null
   *
   * 双层合并规则：
   *   fearGreed：realtimeData.fearGreed 优先 → data.fearGreed 兜底 → null
   *   dataMeta：AI日报 _meta 为基础，实时层存在时将 sourceType 覆盖为 'realtime_quote'
   *            并追加 realtimeUpdatedAt 字段，供状态栏显示「实时行情」标签
   */
  _applyData: function(data, withAnimation, realtimeData) {
    var that = this
    var riskInfo = colorUtil.getRiskInfo(data.riskLevel)

    var events = (data.events || []).map(function(item) {
      var impactInfo = colorUtil.getImpactInfo(item.impact)
      return Object.assign({}, item, {
        impactLabel: impactInfo.label,
        impactTagClass: impactInfo.tagClass
      })
    })

    var alerts = (data.alerts || []).map(function(item) {
      var alertInfo = colorUtil.getAlertInfo(item.level)
      return Object.assign({}, item, {
        icon: alertInfo.icon,
        bgClass: alertInfo.bgClass
      })
    })

    var riskAlerts = (data.riskAlerts || []).map(function(item) {
      return Object.assign({}, item, {
        levelClass: item.level === 'high' ? 'ra-high' : 'ra-medium'
      })
    })

    // ── 双层合并：实时层 fearGreed 优先，AI日报层兜底 ──
    // realtimeData 由 api.getRealtimeData() 提供，可能为 null（静默降级场景）
    var fearGreed = (realtimeData && realtimeData.fearGreed)
      ? realtimeData.fearGreed      // 实时层：来自云函数当日刷新（优先）
      : (data.fearGreed || null)    // 日报层：来自 AI 每日生成（降级兜底）

    // ── _meta 双层合并 ──
    // 以 AI 日报 _meta 为基础（保留 skillVersion / generatedAt 等字段）
    // 若实时层存在，将 sourceType 覆盖为 'realtime_quote'，并追加 realtimeUpdatedAt
    var mergedMeta = Object.assign({}, data._meta || {})
    if (realtimeData && (realtimeData.fearGreed || (realtimeData.predictions && realtimeData.predictions.length > 0))) {
      mergedMeta.sourceType = 'realtime_quote'
      mergedMeta.realtimeUpdatedAt = (realtimeData.fearGreed && realtimeData.fearGreed.updatedAt)
        || (realtimeData._meta && realtimeData._meta.updatedAt) || null
    }
    // 兜底：若 AI 日报无 sourceType，补默认值
    if (!mergedMeta.sourceType) {
      mergedMeta.sourceType = 'heavy_analysis'
    }

    // v1.3 Fear & Greed 映射（fearGreed 已指向合并后的值）
    var fgInfo = null
    var fgPrevDiff = 0
    var fgWeekDiff = 0
    if (fearGreed) {
      fgInfo = colorUtil.getFearGreedInfo(fearGreed.value, fearGreed.label)
      fgPrevDiff = fearGreed.value - (fearGreed.previousClose || fearGreed.value)
      fgWeekDiff = fearGreed.value - (fearGreed.oneWeekAgo || fearGreed.value)
    }

    // ── 双层合并：实时层 predictions 优先，AI日报层兜底 ──（v2.0 新增）
    var rawPredictions = (realtimeData && realtimeData.predictions && realtimeData.predictions.length > 0)
      ? realtimeData.predictions      // 实时层：来自云函数抓取的 Polymarket（优先）
      : (data.predictions || [])      // 日报层：来自 AI 每日生成（降级兜底）

    var predictions = rawPredictions.map(function(item) {
      var trendInfo = colorUtil.getPredictionTrendInfo(item.trend)
      return {
        title: item.title,
        source: item.source,
        probability: item.probability,
        trend: item.trend,
        trendArrow: trendInfo.arrow,
        trendClass: trendInfo.colorClass,
        change24h: item.change24h || 0,
        changeLabel: (item.change24h > 0 ? '+' : '') + (item.change24h || 0) + '%'
      }
    })

    // v1.3 数据新鲜度（以 AI 日报生成时间为基准）
    var dataFreshness = formatUtil.getRelativeTime(
      data._meta && data._meta.generatedAt ? data._meta.generatedAt : data.dataTime
    )

    that.setData({
      fearGreed: fearGreed,
      displayFGValue: withAnimation ? 0 : (fearGreed ? fearGreed.value : 0),
      fgInfo: fgInfo,
      fgPrevDiff: fgPrevDiff,
      fgWeekDiff: fgWeekDiff,
      predictions: predictions,
      trafficLights: data.trafficLights || [],
      riskScore: data.riskScore || 0,
      displayRiskScore: withAnimation ? 0 : (data.riskScore || 0),
      riskLevel: data.riskLevel || 'low',
      riskLabel: riskInfo.label,
      riskClassName: riskInfo.className,
      riskAdvice: data.riskAdvice || '',
      monitorTable: data.monitorTable || [],
      riskAlerts: riskAlerts,
      events: events,
      alerts: alerts,
      smartMoneyDetail: data.smartMoneyDetail || [],
      dataTime: (data.dataTime || '').split('/')[0].trim(),
      dataFreshness: dataFreshness || '',
      dataMeta: mergedMeta,
      loading: false
    })

    setTimeout(function() {
      that.setData({ animateReady: true })
    }, 50)

    if (withAnimation) {
      // 风险评分动画
      if (that._animTimer) clearInterval(that._animTimer)
      that._animTimer = animate.animateInteger({
        from: 0,
        to: data.riskScore || 0,
        duration: 1000,
        onUpdate: function(val) {
          that.setData({ displayRiskScore: val })
        }
      })
      // v1.3 Fear & Greed 数字跳动
      if (fearGreed) {
        if (that._fgAnimTimer) clearInterval(that._fgAnimTimer)
        that._fgAnimTimer = animate.animateInteger({
          from: 0,
          to: fearGreed.value,
          duration: 1000,
          onUpdate: function(val) {
            that.setData({ displayFGValue: val })
          }
        })
      }
    }
  }
})
