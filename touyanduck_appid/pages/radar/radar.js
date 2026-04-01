// pages/radar/radar.js
// 雷达页 v4.0 — 对齐Skill §5 + §4: 7项红绿灯+阈值表+风险提示+聪明钱

var api = require('../../services/api')
var colorUtil = require('../../utils/color')
var animate = require('../../utils/animate')

Page({
  data: {
    loading: true,
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
    isCloud: false,
    animateReady: false
  },

  _animTimer: null,

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

    that.setData({
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
      loading: false
    })

    setTimeout(function() {
      that.setData({ animateReady: true })
    }, 50)

    if (withAnimation) {
      if (that._animTimer) clearInterval(that._animTimer)
      that._animTimer = animate.animateInteger({
        from: 0,
        to: data.riskScore || 0,
        duration: 1000,
        onUpdate: function(val) {
          that.setData({ displayRiskScore: val })
        }
      })
    }
  }
})
