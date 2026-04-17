// pages/markets/markets.js
// 市场页 v4.4 — 5Tab摘要条 + GICS热力图 + 圆点Tab + M7精简

var api = require('../../services/api')
var colorUtil = require('../../utils/color')

/**
 * 解析 insight 文本，提取数字/百分比/关键标的作为高亮片段
 * 匹配规则：$价格、±百分比、涨/跌/暴涨/暴跌、连续2-5位大写英文标的代码（通用匹配）
 * v4.5: 改为通用大写字母匹配，不再硬编码标的列表
 */
function parseInsightSegments(text) {
  if (!text) return []
  // 需排除的常见英文缩写（非标的代码）
  var excludeWords = { 'AI': 1, 'US': 1, 'EU': 1, 'UK': 1, 'GDP': 1, 'CPI': 1, 'PPI': 1, 'PMI': 1, 'PCE': 1, 'FOMC': 1, 'FED': 1, 'IPO': 1, 'CEO': 1, 'CFO': 1, 'CTO': 1, 'THE': 1, 'AND': 1, 'FOR': 1, 'TAB': 1 }
  // 匹配：$数字、±数字%、涨跌关键词+数字、Fear&Greed、中文方括号、2-5位大写英文
  var re = /(\$[\d,.]+[KMB]?|[+-]?\d+\.?\d*%|暴[涨跌]\d*\.?\d*%?|[涨跌]\d+\.?\d*%|Fear\s*&\s*Greed|【[^】]+】|[A-Z][A-Z0-9]{1,4})/g
  var segments = []
  var lastIndex = 0
  var match
  while ((match = re.exec(text)) !== null) {
    var matched = match[0]
    // 过滤纯大写英文中的常见非标的缩写
    var isTickerLike = /^[A-Z][A-Z0-9]{1,4}$/.test(matched)
    if (isTickerLike && excludeWords[matched]) {
      continue
    }
    if (match.index > lastIndex) {
      segments.push({ text: text.substring(lastIndex, match.index), highlight: false })
    }
    segments.push({ text: matched, highlight: true })
    lastIndex = re.lastIndex
  }
  if (lastIndex < text.length) {
    segments.push({ text: text.substring(lastIndex), highlight: false })
  }
  return segments
}

Page({
  data: {
    loading: true,
    activeTab: 0,
    tabs: [
      { key: 'us', label: '美股' },
      { key: 'm7', label: 'M7巨头' },
      { key: 'asia', label: '亚太' },
      { key: 'commodity', label: '大宗' },
      { key: 'crypto', label: '加密' }
    ],
    usMarkets: [],
    m7: [],
    asiaMarkets: [],
    commodities: [],
    cryptos: [],
    gics: [],
    usInsight: '',
    m7Insight: '',
    asiaInsight: '',
    commodityInsight: '',
    cryptoInsight: '',
    gicsInsight: '',
    usSummarySegments: [],
    m7SummarySegments: [],
    asiaSummarySegments: [],
    commoditySummarySegments: [],
    cryptoSummarySegments: [],
    gicsSummarySegments: [],
    animateReady: false,
    isCloud: false,
    dataTime: '',
    swiperHeights: ['1600px', '1000px', '900px', '900px', '700px']
  },

  // 各Tab内容项数量（数据加载后更新）
  _tabCounts: [0, 0, 0, 0, 0],
  _hasGics: false,

  onLoad: function() {
    this.setData({ isCloud: api.isCloudMode() })
    // 缓存优先秒开：先读缓存渲染，再后台静默刷新
    var cached = api.getCache('markets')
    if (cached && cached.success && cached.data) {
      this._applyData(cached.data)
      this.fetchData(false, true)
    } else {
      this.fetchData()
    }
  },

  onShow: function() {
    var nav = getApp().globalData.navigateTo
    if (nav.marketsTab !== null && nav.marketsTab !== undefined) {
      var targetTab = nav.marketsTab
      nav.marketsTab = null
      if (targetTab !== this.data.activeTab) {
        this.setData({ activeTab: targetTab })
        this._measureTabHeight(targetTab, 0)
      }
    }
  },

  /**
   * 用 SelectorQuery 量取指定 Tab 的真实内容高度，赋给 swiperHeights[tabIndex]
   * @param {number} tabIndex
   * @param {number} [retryCount] 重试次数，最多3次（等待渲染完成）
   */
  _measureTabHeight: function(tabIndex, retryCount) {
    var that = this
    var retry = retryCount || 0
    var selector = '.tab-wrap-' + tabIndex

    wx.createSelectorQuery().select(selector).boundingClientRect(function(rect) {
      if (rect && rect.height > 100) {
        // 量到真实高度，加 40px 底部留白，转为 rpx（1px ≈ 2rpx，但直接用 px 赋值更准）
        var h = Math.ceil(rect.height) + 40
        var heights = that.data.swiperHeights.slice()
        heights[tabIndex] = h + 'px'
        that.setData({ swiperHeights: heights })
      } else if (retry < 4) {
        // 渲染尚未完成，延迟后重试
        setTimeout(function() {
          that._measureTabHeight(tabIndex, retry + 1)
        }, 120)
      }
    }).exec()
  },

  /**
   * 数据渲染完成后，批量量取所有 5 个 Tab 的高度
   */
  _measureAllTabs: function() {
    var that = this
    for (var i = 0; i < 5; i++) {
      ;(function(idx) {
        setTimeout(function() {
          that._measureTabHeight(idx, 0)
        }, idx * 80)
      })(i)
    }
  },

  switchTab: function(e) {
    var index = e.currentTarget.dataset.index
    this.setData({ activeTab: index })
    // 切换时重新量取该 Tab（可能首次尚未量到）
    this._measureTabHeight(index, 0)
    wx.vibrateShort({ type: 'light' })
  },

  onSwiperChange: function(e) {
    var current = e.detail.current
    this.setData({ activeTab: current })
    this._measureTabHeight(current, 0)
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

    api.getMarkets().then(function(res) {
      if (res.success && res.data) {
        that._applyData(res.data)
      } else if (!isSilent) {
        that.setData({ loading: false })
      }

      if (isRefresh) {
        wx.stopPullDownRefresh()
        wx.showToast({ title: '已更新至最新', icon: 'success', duration: 1500 })
      }
    }).catch(function(err) {
      console.error('[Markets] 数据加载失败:', err)
      if (!isSilent) {
        that.setData({ loading: false })
      }
      if (isRefresh) {
        wx.stopPullDownRefresh()
        wx.showToast({ title: '更新失败', icon: 'none' })
      }
    })
  },

  _applyData: function(data) {
    var that = this
    var processItems = function(items) {
      return (items || []).map(function(item, idx) {
        var c = (typeof item.change === 'number' && !isNaN(item.change)) ? item.change : 0
        item.change = c
        item.colorClass = colorUtil.getChangeColorClass(c)
        item.changeText = (c > 0 ? '+' : '') + c.toFixed(2) + '%'
        item.isUp = c >= 0
        item.chartId = 'mc_' + item.name.replace(/[^a-zA-Z0-9]/g, '') + '_' + idx
        item.animDelay = idx * 60
        return item
      })
    }

    var gicsData = (data.gics || []).map(function(item) {
      var gc = (typeof item.change === 'number' && !isNaN(item.change)) ? item.change : 0
      var abs = Math.abs(gc)
      var barWidth = Math.min(abs * 25, 100)
      var heatLevel = abs > 1.5 ? 'heat-3' : (abs > 0.8 ? 'heat-2' : (abs > 0.3 ? 'heat-1' : 'heat-0'))
      return {
        name: item.name,
        change: gc,
        etf: item.etf,
        changeText: (gc > 0 ? '+' : '') + gc.toFixed(2) + '%',
        colorClass: colorUtil.getChangeColorClass(gc),
        heatClass: gc >= 0 ? 'heat-up-' + heatLevel : 'heat-down-' + heatLevel,
        isUp: gc >= 0,
        barWidth: barWidth
      }
    })

    // 优先使用云数据中的 dataTime，没有则自动生成
    var dataTime = data.dataTime
    if (!dataTime) {
      var now = new Date()
      var h = String(now.getHours()).padStart(2, '0')
      var m = String(now.getMinutes()).padStart(2, '0')
      var mon = String(now.getMonth() + 1).padStart(2, '0')
      var d = String(now.getDate()).padStart(2, '0')
      dataTime = now.getFullYear() + '-' + mon + '-' + d + ' ' + h + ':' + m + ' BJT'
    }

    // 板块 Insight：优先使用独立 *Insight 字段，美股向后兼容旧 usMarkets[0].note
    var usInsight = data.usInsight || (data.usMarkets && data.usMarkets[0] && data.usMarkets[0].note) || ''
    var m7Insight = data.m7Insight || ''
    var asiaInsight = data.asiaInsight || ''
    var commodityInsight = data.commodityInsight || ''
    var cryptoInsight = data.cryptoInsight || ''
    var gicsInsight = data.gicsInsight || ''

    // GICS 摘要：优先从因果链提取"轮动"节点，降级到 gicsInsight
    var gicsInsightChain = data.gicsInsightChain || []
    var gicsSummaryText = ''
    if (gicsInsightChain.length) {
      var rotationNode = gicsInsightChain.filter(function(n) {
        return n.label === '轮动' || n.label === '趋势' || n.label === '逻辑'
      })[0]
      gicsSummaryText = rotationNode ? rotationNode.text : gicsInsightChain[gicsInsightChain.length - 1].text
    }
    if (!gicsSummaryText) gicsSummaryText = gicsInsight

    that.setData({
      usMarkets: processItems(data.usMarkets),
      m7: processItems(data.m7),
      asiaMarkets: processItems(data.asiaMarkets),
      commodities: processItems(data.commodities),
      cryptos: processItems(data.cryptos),
      gics: gicsData,
      usInsight: usInsight,
      m7Insight: m7Insight,
      asiaInsight: asiaInsight,
      commodityInsight: commodityInsight,
      cryptoInsight: cryptoInsight,
      gicsInsight: gicsInsight,
      usSummarySegments: parseInsightSegments(usInsight),
      m7SummarySegments: parseInsightSegments(m7Insight),
      asiaSummarySegments: parseInsightSegments(asiaInsight),
      commoditySummarySegments: parseInsightSegments(commodityInsight),
      cryptoSummarySegments: parseInsightSegments(cryptoInsight),
      gicsSummarySegments: parseInsightSegments(gicsSummaryText),
      dataTime: dataTime,
      loading: false
    })

    that._tabCounts = [
      (data.usMarkets || []).length,
      (data.m7 || []).length,
      (data.asiaMarkets || []).length,
      (data.commodities || []).length,
      (data.cryptos || []).length
    ]

    // 数据渲染完成后，立即量取高度（不等动画）
    setTimeout(function() {
      that._measureAllTabs()
      that.setData({ animateReady: true })
      // 动画完成后再量一次精确高度
      setTimeout(function() {
        that._measureAllTabs()
      }, 500)
    }, 50)
  }
})
