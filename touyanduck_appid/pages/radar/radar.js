// pages/radar/radar.js
// 雷达页 v7.0 — 聪明钱最优先：动向#1 + 持仓#2 + 风险判断#3
// v7.0 变更：
//   - 移除已废弃的 realtime 层（getRealtimeData / 双层合并逻辑）
//   - predictions 现在完全由 radar.json 日报层提供，无需实时层合并

var api = require('../../services/api')
var colorUtil = require('../../utils/color')
var formatUtil = require('../../utils/format')

Page({
  data: {
    loading: true,

    // ── 聪明钱动向（#1）──
    smartMoneyFlat: [],

    // ── 聪明钱持仓（#2，默认折叠）──
    holdings: [],

    // ── 风险判断模块（#3）──
    trafficLights: [],
    riskAdvice: '',

    // ── 本周前瞻（#4）──
    weekAhead: [],

    // ── 市场在赌什么（#5，默认折叠）──
    predictions: [],
    predictionHook: '',

    // ── 异动信号（#6）──
    alerts: [],

    dataTime: '',
    dataFreshness: '',
    dataMeta: null,
    isCloud: false,
    animateReady: false
  },

  onLoad: function() {
    this.setData({ isCloud: api.isCloudMode() })
    var cached = api.getCache('radar')
    if (cached && cached.success && cached.data) {
      this._applyData(cached.data, false)
      this.fetchData(false, true)
    } else {
      this.fetchData()
    }
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

    api.getRadar().then(function(radarRes) {
      if (radarRes.success && radarRes.data) {
        that._applyData(radarRes.data, !isSilent)
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

    // ── predictions 直接从 radar.json 读取 ──
    var rawPredictions = data.predictions || []

    // ── _meta ──
    var mergedMeta = Object.assign({}, data._meta || {})
    if (!mergedMeta.sourceType) {
      mergedMeta.sourceType = 'heavy_analysis'
    }

    // ── 1. 红绿灯（直接传给 traffic-light 组件）──

    // ── 2. 聪明钱扁平化（含 source/url）──
    var tierOrder = { 'T1旗舰': 0, 'T2成长': 1, '策略师观点': 2 }
    var smartMoneyFlat = []
    ;(data.smartMoneyDetail || []).forEach(function(tier) {
      var order = tierOrder[tier.tier] !== undefined ? tierOrder[tier.tier] : 9
      ;(tier.funds || []).forEach(function(fund) {
        smartMoneyFlat.push({
          name: fund.name,
          action: fund.action,
          signal: fund.signal,
          tierOrder: order,
          tierLabel: tier.tier,
          source: fund.source || '',
          url: fund.url || ''
        })
      })
    })
    smartMoneyFlat.sort(function(a, b) { return a.tierOrder - b.tierOrder })

    // ── 3. 前瞻时间线合并（events + riskAlerts，含 source/url）──
    var weekAhead = []
    ;(data.events || []).forEach(function(e) {
      var impactInfo = colorUtil.getImpactInfo(e.impact)
      weekAhead.push({
        date: e.date,
        title: e.title,
        impact: e.impact,
        impactLabel: impactInfo.label,
        impactTagClass: impactInfo.tagClass,
        isRiskAlert: false,
        probability: '',
        response: '',
        levelClass: '',
        source: e.source || '',
        url: e.url || ''
      })
    })
    ;(data.riskAlerts || []).forEach(function(ra) {
      var impactInfo = colorUtil.getImpactInfo(ra.level === 'high' ? 'high' : 'medium')
      weekAhead.push({
        date: '持续',
        title: ra.title,
        impact: ra.level,
        impactLabel: impactInfo.label,
        impactTagClass: impactInfo.tagClass,
        isRiskAlert: true,
        probability: ra.probability,
        response: ra.response,
        levelClass: ra.level === 'high' ? 'wa-risk-high' : 'wa-risk-medium',
        source: ra.source || '',
        url: ra.url || ''
      })
    })

    // ── 4. 预测市场处理 + 生成标题钩子 ──
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
    var predictionHook = ''
    if (predictions.length > 0) {
      var p0 = predictions[0]
      var arrow = p0.trend === 'up' ? '↑' : (p0.trend === 'down' ? '↓' : '—')
      predictionHook = p0.title.replace(/\?$/, '').replace(/？$/, '') + ' ' + p0.probability + '% ' + arrow
    }

    // ── 5. 异动信号处理（含 source/url）──
    var alerts = (data.alerts || []).map(function(item) {
      var alertInfo = colorUtil.getAlertInfo(item.level)
      return Object.assign({}, item, {
        icon: alertInfo.icon,
        bgClass: alertInfo.bgClass,
        source: item.source || '',
        url: item.url || ''
      })
    })

    // ── 6. 聪明钱持仓处理（v6.3 新增）──
    var holdings = (data.smartMoneyHoldings || []).map(function(h) {
      return {
        manager: h.manager || '',
        fund: h.fund || '',
        aum: h.aum || '',
        asOf: h.asOf || '',
        positions: (h.positions || []).map(function(pos, idx) {
          return {
            rank: idx + 1,
            name: pos.name || '',
            symbol: pos.symbol || '',
            weight: pos.weight || '',
            change: pos.change || ''
          }
        }),
        footnote: h.footnote || '',
        expanded: false
      }
    })

    // ── 数据新鲜度 ──
    var dataFreshness = formatUtil.getRelativeTime(
      data._meta && data._meta.generatedAt ? data._meta.generatedAt : data.dataTime
    )

    that.setData({
      // 聪明钱动向
      smartMoneyFlat: smartMoneyFlat,

      // 聪明钱持仓
      holdings: holdings,

      // 风险判断
      trafficLights: data.trafficLights || [],
      riskAdvice: data.riskAdvice || '',

      weekAhead: weekAhead,

      predictions: predictions,
      predictionHook: predictionHook,

      alerts: alerts,

      dataTime: (data.dataTime || '').split('/')[0].trim(),
      dataFreshness: dataFreshness || '',
      dataMeta: mergedMeta,
      loading: false
    })

    setTimeout(function() {
      that.setData({ animateReady: true })
    }, 50)
  },

  // ── 聪明钱持仓折叠展开 ──
  toggleHoldings: function(e) {
    var idx = e.currentTarget.dataset.index
    var key = 'holdings[' + idx + '].expanded'
    var obj = {}
    obj[key] = !this.data.holdings[idx].expanded
    this.setData(obj)
  },

  // ── 来源链接点击 → webview 打开 ──
  onSourceTap: function(e) {
    var url = e.currentTarget.dataset.url
    var name = e.currentTarget.dataset.source || '原文'
    if (!url) return
    if (!/^https?:\/\//i.test(url)) {
      wx.showToast({ title: '链接格式不支持', icon: 'none', duration: 2000 })
      return
    }
    wx.navigateTo({
      url: '/pages/webview/webview?url=' + encodeURIComponent(url) + '&title=' + encodeURIComponent(name),
      fail: function() {
        wx.showToast({ title: '无法打开链接，请稍后重试', icon: 'none', duration: 2500 })
      }
    })
  }
})
