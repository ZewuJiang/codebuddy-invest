// pages/radar/radar.js
// 雷达页 v5.0 — 对齐Skill §5 + §4 + v1.3前端体验升级

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

    api.getRadar().then(function(res) {
      if (res.success && res.data) {
        that._applyData(res.data, !isSilent)
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

  _applyData: function(data, withAnimation) {
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

    // v1.3 Fear & Greed 映射
    var fearGreed = data.fearGreed || null
    var fgInfo = null
    var fgPrevDiff = 0
    var fgWeekDiff = 0
    if (fearGreed) {
      fgInfo = colorUtil.getFearGreedInfo(fearGreed.value, fearGreed.label)
      fgPrevDiff = fearGreed.value - (fearGreed.previousClose || fearGreed.value)
      fgWeekDiff = fearGreed.value - (fearGreed.oneWeekAgo || fearGreed.value)
    }

    // v1.3 预测市场映射
    var predictions = (data.predictions || []).map(function(item) {
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

    // v1.3 数据新鲜度
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
      dataTime: data.dataTime || '',
      dataFreshness: dataFreshness || '',
      dataMeta: data._meta || null,
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
