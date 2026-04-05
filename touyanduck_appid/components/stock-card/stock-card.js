/**
 * stock-card 组件 v5.0 — 支持 badges 特殊标签 + 未上市标的
 */
var colorUtil = require('../../utils/color')

Component({
  properties: {
    stock: {
      type: Object,
      value: {}
    },
    showDetail: {
      type: Boolean,
      value: true
    },
    animDelay: {
      type: Number,
      value: 0
    }
  },

  data: {
    changeColorClass: 'color-flat',
    changeText: '--',
    isUp: true,
    isUnlisted: false,
    badgeClass: 'badge-default',
    chartId: '',
    showCard: false,
    expanded: false
  },

  lifetimes: {
    attached: function() {
      var that = this
      var delay = that.properties.animDelay || 0
      var stock = that.properties.stock || {}
      var id = 'sc_' + (stock.symbol || '').replace(/[^a-zA-Z0-9]/g, '') + '_' + Math.random().toString(36).substr(2, 4)
      that.setData({ chartId: id })
      
      setTimeout(function() {
        that.setData({ showCard: true })
      }, delay + 50)
    }
  },

  observers: {
    'stock': function(stock) {
      if (!stock || !stock.symbol) return
      var isUnlisted = stock.listed === false
      var changeText = '--'
      var changeColorClass = 'color-flat'
      var isUp = true

      if (!isUnlisted) {
        changeColorClass = colorUtil.getChangeColorClass(stock.change)
        changeText = (stock.change > 0 ? '+' : '') + stock.change + '%'
        isUp = stock.change >= 0
      }

      this.setData({
        changeColorClass: changeColorClass,
        changeText: changeText,
        isUp: isUp,
        isUnlisted: isUnlisted
      })
    }
  },

  methods: {
    toggleExpand: function() {
      this.setData({ expanded: !this.data.expanded })
      wx.vibrateShort({ type: 'light' })
    }
  }
})
