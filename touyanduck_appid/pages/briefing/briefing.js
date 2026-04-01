// pages/briefing/briefing.js
// 简报页 v5.0 — 对齐Skill §1+§2摘要+§4摘要 + v1.3前端体验升级

var api = require('../../services/api')
var formatUtil = require('../../utils/format')
var colorUtil = require('../../utils/color')
var animate = require('../../utils/animate')

Page({
  data: {
    loading: true,
    // v1.3 时间状态栏
    timeStatus: null,
    marketStatus: '',
    marketStatusOpen: false,
    // v1.3 KEY DELTA
    keyDeltas: [],
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
    dataFreshness: '',
    // v1.3 元数据
    dataMeta: null,
    // 数据源模式
    isCloud: false,
    // v1.3.1 参考源展开状态（key=判断index）
    expandedRefs: {},
    // 动画控制
    animateReady: false
  },

  _animTimer: null,

  onLoad: function() {
    this.setData({
      isCloud: api.isCloudMode()
    })
    this._updateTimeStatus()

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

  onShow: function() {
    this._updateTimeStatus()
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

    // v1.3 KEY DELTA 数据映射
    var keyDeltas = (d.keyDeltas || []).map(function(item) {
      var statusInfo = colorUtil.getDeltaStatusInfo(item.status)
      return {
        title: item.title || '',
        status: item.status || '活跃',
        statusTagClass: statusInfo.tagClass,
        heat: item.heat || 3,
        heatLabel: colorUtil.getHeatLabel(item.heat || 3),
        brief: item.brief || ''
      }
    })

    // v1.3 核心判断扩展字段映射
    var coreJudgments = (d.coreJudgments || []).map(function(item) {
      var result = {
        title: item.title,
        confidence: item.confidence,
        logic: item.logic
      }
      // 可选扩展字段
      if (item.keyActor) result.keyActor = item.keyActor
      if (item.references && item.references.length) {
        // v1.3.1 兼容新旧格式
        result.references = item.references.map(function(ref) {
          if (typeof ref === 'string') {
            return { name: ref, summary: '', url: '' }
          }
          return {
            name: ref.name || '',
            summary: ref.summary || '',
            url: ref.url || ''
          }
        })
        result.refCount = item.references.length
        // 收起态显示的来源名称列表
        result.refNames = result.references.map(function(r) { return r.name }).join(', ')
        // 是否有丰富内容（有 summary 才算可展开）
        result.hasRichRef = item.references.some(function(ref) {
          return typeof ref !== 'string' && ref.summary
        })
      }
      if (item.probability) {
        result.probability = item.probability
        result.probClass = colorUtil.getProbabilityInfo(item.probability).tagClass
      }
      if (item.trend) {
        var trendInfo = colorUtil.getJudgmentTrendInfo(item.trend)
        result.trend = item.trend
        result.trendArrow = trendInfo.arrow
        result.trendClass = trendInfo.tagClass
      }
      result.hasExtension = !!(item.keyActor || (item.references && item.references.length) || item.probability || item.trend)
      return result
    })

    // v1.3 数据新鲜度
    var dataFreshness = formatUtil.getRelativeTime(
      d._meta && d._meta.generatedAt ? d._meta.generatedAt : d.dataTime
    )

    that.setData({
      keyDeltas: keyDeltas,
      coreEvent: d.coreEvent || null,
      globalReaction: d.globalReaction || [],
      coreJudgments: coreJudgments,
      todayActions: todayActions,
      weekActions: weekActions,
      sentimentScore: d.sentimentScore || 50,
      displaySentiment: withAnimation ? 0 : (d.sentimentScore || 50),
      sentimentLabel: d.sentimentLabel || '',
      marketSummary: d.marketSummary || '',
      smartMoney: d.smartMoney || [],
      riskNote: d.riskNote || '',
      dataTime: d.dataTime || '',
      dataFreshness: dataFreshness || '',
      dataMeta: d._meta || null,
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

  // v1.3 更新时间状态栏
  _updateTimeStatus: function() {
    var tz = formatUtil.getMultiTimezone()
    var status = formatUtil.getMarketStatus()
    this.setData({
      timeStatus: tz,
      marketStatus: status,
      marketStatusOpen: status === '美股交易中'
    })
  },

  // 全球资产反应点击 → 跳转市场页（美股Tab）
  onReactionTap: function() {
    getApp().globalData.navigateTo.marketsTab = 0
    wx.switchTab({ url: '/pages/markets/markets' })
  },

  // v1.3.1 参考源展开/收起切换
  onRefToggle: function(e) {
    var jIdx = e.currentTarget.dataset.jIdx
    var key = 'expandedRefs.' + jIdx
    var current = this.data.expandedRefs[jIdx]
    this.setData({ [key]: !current })
  },

  // 聪明钱速览点击 → 跳转雷达页
  onSmartMoneyTap: function() {
    wx.switchTab({ url: '/pages/radar/radar' })
  }
})
