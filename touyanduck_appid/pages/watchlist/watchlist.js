// pages/watchlist/watchlist.js
// 标的页 v5.0 — 5板块新架构（AI算力链/AI应用/国产AI/聪明钱/本期热点）

var api = require('../../services/api')
var colorUtil = require('../../utils/color')

Page({
  data: {
    loading: true,
    activeSector: 'ai_infra',
    sectors: [],
    currentSector: null,
    stocks: [],
    animateReady: false,
    isCloud: false,
    switching: false,
    dataTime: ''
  },

  _allStockData: {},

  onLoad: function() {
    this.setData({ isCloud: api.isCloudMode() })
    // 缓存优先秒开
    var cached = api.getCache('watchlist')
    if (cached && cached.success && cached.data) {
      this._applyData(cached.data)
      this.fetchData(false, true)
    } else {
      this.fetchData()
    }
  },

  onShow: function() {
    var nav = getApp().globalData.navigateTo
    if (nav.watchlistSector !== null && nav.watchlistSector !== undefined) {
      var targetSector = nav.watchlistSector
      nav.watchlistSector = null
      if (targetSector !== this.data.activeSector && this.data.sectors.length > 0) {
        this.setData({ activeSector: targetSector, animateReady: false })
        this.updateSectorData(targetSector)
        var that = this
        setTimeout(function() {
          that.setData({ animateReady: true })
        }, 50)
      }
    }
  },

  switchSector: function(e) {
    var id = e.currentTarget.dataset.id
    if (id === this.data.activeSector) return

    var that = this
    // 先淡出当前内容
    that.setData({ switching: true, animateReady: false })
    wx.vibrateShort({ type: 'light' })

    // 200ms后切换数据并淡入
    setTimeout(function() {
      that.setData({ activeSector: id })
      that.updateSectorData(id)
      that.setData({ switching: false })

      setTimeout(function() {
        that.setData({ animateReady: true })
      }, 50)
    }, 200)
  },

  updateSectorData: function(sectorId) {
    var sectorInfo = this.data.sectors.find(function(s) { return s.id === sectorId })
    
    var trendInfo = null
    if (sectorInfo) {
      trendInfo = colorUtil.getTrendInfo(sectorInfo.trend)
    }

    this.setData({
      currentSector: sectorInfo ? Object.assign({}, sectorInfo, {
        trendLabel: trendInfo ? trendInfo.label : '中性',
        trendTagClass: trendInfo ? trendInfo.tagClass : 'tag-yellow'
      }) : null,
      stocks: this._allStockData[sectorId] || []
    })
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

    api.getWatchlist().then(function(res) {
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
      console.error('[Watchlist] 数据加载失败:', err)
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
    that._allStockData = JSON.parse(JSON.stringify(data.stocks || {}))

    // 优先使用云数据中的 dataTime
    var dataTime = data.dataTime
    if (!dataTime) {
      var now = new Date()
      var h = String(now.getHours()).padStart(2, '0')
      var m = String(now.getMinutes()).padStart(2, '0')
      var mon = String(now.getMonth() + 1).padStart(2, '0')
      var d = String(now.getDate()).padStart(2, '0')
      dataTime = now.getFullYear() + '-' + mon + '-' + d + ' ' + h + ':' + m + ' BJT'
    }

    that.setData({
      sectors: data.sectors || [],
      dataTime: dataTime,
      loading: false
    })

    that.updateSectorData(that.data.activeSector)

    setTimeout(function() {
      that.setData({ animateReady: true })
    }, 50)
  }
})
