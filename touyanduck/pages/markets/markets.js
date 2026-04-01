// pages/markets/markets.js
// 市场页 v4.0 — 新增M7巨头Tab + GICS板块热力图

var api = require('../../services/api')
var colorUtil = require('../../utils/color')

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
    animateReady: false,
    dataTime: '',
    swiperHeight: '1200rpx'
  },

  // 各Tab内容项数量（数据加载后更新）
  _tabCounts: [0, 0, 0, 0, 0],
  _hasGics: false,

  onLoad: function() {
    this.fetchData()
  },

  onShow: function() {
    var nav = getApp().globalData.navigateTo
    if (nav.marketsTab !== null && nav.marketsTab !== undefined) {
      var targetTab = nav.marketsTab
      nav.marketsTab = null
      if (targetTab !== this.data.activeTab) {
        this.setData({ activeTab: targetTab })
        this._updateSwiperHeight(targetTab)
      }
    }
  },

  /**
   * 根据当前Tab的内容数量动态计算Swiper高度
   * @param {number} tabIndex - Tab索引
   */
  _updateSwiperHeight: function(tabIndex) {
    var count = this._tabCounts[tabIndex] || 3
    // 每个列表项约100rpx + 卡片上下padding和margin约80rpx + 底部留白40rpx
    var baseHeight = count * 100 + 80 + 40

    // 美股Tab额外加上comment(80rpx)和GICS板块区(gics项数*50+标题+padding)
    if (tabIndex === 0) {
      baseHeight += 100 // comment区
      if (this._hasGics) {
        baseHeight += this.data.gics.length * 50 + 120 // GICS区域
      }
    }

    // M7巨头Tab额外加上头部
    if (tabIndex === 1) {
      baseHeight += 100
    }

    // 最小高度保障
    var height = Math.max(baseHeight, 500)
    this.setData({ swiperHeight: height + 'rpx' })
  },

  switchTab: function(e) {
    var index = e.currentTarget.dataset.index
    this.setData({ activeTab: index })
    this._updateSwiperHeight(index)
    wx.vibrateShort({ type: 'light' })
  },

  onSwiperChange: function(e) {
    var current = e.detail.current
    this.setData({ activeTab: current })
    this._updateSwiperHeight(current)
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
        item.colorClass = colorUtil.getChangeColorClass(item.change)
        item.changeText = (item.change > 0 ? '+' : '') + item.change + '%'
        item.isUp = item.change >= 0
        item.chartId = 'mc_' + item.name.replace(/[^a-zA-Z0-9]/g, '') + '_' + idx
        item.animDelay = idx * 60
        return item
      })
    }

    var gicsData = (data.gics || []).map(function(item) {
      var abs = Math.abs(item.change)
      var heatLevel = abs > 1.5 ? 'heat-3' : (abs > 0.8 ? 'heat-2' : (abs > 0.3 ? 'heat-1' : 'heat-0'))
      return {
        name: item.name,
        change: item.change,
        etf: item.etf,
        changeText: (item.change > 0 ? '+' : '') + item.change.toFixed(2) + '%',
        colorClass: colorUtil.getChangeColorClass(item.change),
        heatClass: item.change >= 0 ? 'heat-up-' + heatLevel : 'heat-down-' + heatLevel,
        isUp: item.change >= 0
      }
    })

    var now = new Date()
    var h = String(now.getHours()).padStart(2, '0')
    var m = String(now.getMinutes()).padStart(2, '0')
    var mon = String(now.getMonth() + 1).padStart(2, '0')
    var d = String(now.getDate()).padStart(2, '0')
    var dataTime = now.getFullYear() + '-' + mon + '-' + d + ' ' + h + ':' + m + ' BJT'

    that.setData({
      usMarkets: processItems(data.usMarkets),
      m7: processItems(data.m7),
      asiaMarkets: processItems(data.asiaMarkets),
      commodities: processItems(data.commodities),
      cryptos: processItems(data.cryptos),
      gics: gicsData,
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
    that._hasGics = gicsData.length > 0
    that._updateSwiperHeight(that.data.activeTab)

    setTimeout(function() {
      that.setData({ animateReady: true })
    }, 50)
  }
})
