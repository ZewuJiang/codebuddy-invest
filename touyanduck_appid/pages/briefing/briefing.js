// pages/briefing/briefing.js
// 简报页 v4.0 — 对齐Skill §1+§2摘要+§4摘要

var api = require('../../services/api')
var formatUtil = require('../../utils/format')
var colorUtil = require('../../utils/color')
var animate = require('../../utils/animate')

Page({
  data: {
    loading: true,
    currentDate: '',
    // §1 核心事件
    coreEvent: null,
    // §1 全球资产反应
    globalReaction: [],
    // §1 三大核心判断
    coreJudgments: [],
    // §1 行动建议
    todayActions: [],
    weekActions: [],
    // §2 市场情绪
    sentimentScore: 0,
    displaySentiment: 0,
    sentimentLabel: '',
    marketSummary: '',
    // §4 聪明钱速览
    smartMoney: [],
    // 风险提示
    riskNote: '',
    // 数据截止时间
    dataTime: '',
    // 数据源模式
    isCloud: false,
    // 动画控制
    animateReady: false
  },

  _animTimer: null,

  onLoad: function() {
    this.setData({
      currentDate: formatUtil.formatDateCN(),
      isCloud: api.isCloudMode()
    })

    // 缓存优先秒开：先读缓存渲染，再后台静默刷新
    var cached = api.getCache('briefing')
    if (cached && cached.success && cached.data) {
      this._applyData(cached.data, false)
      // 后台静默刷新（不显示loading）
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
    var dateISO = formatUtil.formatDateISO()

    if (!isRefresh && !isSilent) {
      that.setData({ loading: true, animateReady: false })
    }

    api.getBriefing(dateISO).then(function(res) {
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
      console.error('[Briefing] 数据加载失败:', err)
      if (!isSilent) {
        that.setData({ loading: false })
      }
      if (isRefresh) {
        wx.stopPullDownRefresh()
        wx.showToast({ title: '更新失败', icon: 'none', duration: 1500 })
      }
    })
  },

  _applyData: function(d, withAnimation) {
    var that = this

    var mapAction = function(item) {
      var info = colorUtil.getActionInfo(item.type)
      return {
        type: item.type,
        content: item.content,
        label: info.label,
        tagClass: info.tagClass
      }
    }
    var todayActions = (d.actions && d.actions.today || []).map(mapAction)
    var weekActions = (d.actions && d.actions.week || []).map(mapAction)

    that.setData({
      coreEvent: d.coreEvent || null,
      globalReaction: d.globalReaction || [],
      coreJudgments: d.coreJudgments || [],
      todayActions: todayActions,
      weekActions: weekActions,
      sentimentScore: d.sentimentScore || 50,
      displaySentiment: withAnimation ? 0 : (d.sentimentScore || 50),
      sentimentLabel: d.sentimentLabel || '',
      marketSummary: d.marketSummary || '',
      smartMoney: d.smartMoney || [],
      riskNote: d.riskNote || '',
      dataTime: d.dataTime || '',
      loading: false
    })

    setTimeout(function() {
      that.setData({ animateReady: true })
    }, 50)

    if (withAnimation) {
      if (that._animTimer) clearInterval(that._animTimer)
      that._animTimer = animate.animateInteger({
        from: 0,
        to: d.sentimentScore || 50,
        duration: 1000,
        onUpdate: function(val) {
          that.setData({ displaySentiment: val })
        }
      })
    }
  },

  // 全球资产反应点击 → 跳转市场页（美股Tab）
  onReactionTap: function() {
    getApp().globalData.navigateTo.marketsTab = 0
    wx.switchTab({ url: '/pages/markets/markets' })
  },

  // 聪明钱速览点击 → 跳转雷达页
  onSmartMoneyTap: function() {
    wx.switchTab({ url: '/pages/radar/radar' })
  }
})
