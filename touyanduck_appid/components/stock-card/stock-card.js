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
    classifiedBadges: [],
    coloredMetrics: [],
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
        changeText = (stock.change > 0 ? '+' : '') + Number(stock.change).toFixed(2) + '%'
        isUp = stock.change >= 0
      }

      // badges 三色分类
      var classifiedBadges = (stock.badges || []).map(function(b) {
        var cls = 'badge-default'
        if (b.indexOf('巴菲特') >= 0) cls = 'badge-buffett'
        else if (b.indexOf('段永平') >= 0) cls = 'badge-duan'
        else if (b === '未上市') cls = 'badge-unlisted'
        return { text: b, cls: cls }
      })

      // metrics 涨跌着色：含 + 的百分比绿色，含 - 的百分比红色，其余不变
      var coloredMetrics = (stock.metrics || []).map(function(m) {
        var val = (m.value || '') + ''
        var colorClass = ''
        if (/^\+.*%$/.test(val)) {
          colorClass = 'metric-up'
        } else if (/^-.*%$/.test(val)) {
          colorClass = 'metric-down'
        }
        return { label: m.label, value: m.value, colorClass: colorClass }
      })

      this.setData({
        changeColorClass: changeColorClass,
        changeText: changeText,
        isUp: isUp,
        isUnlisted: isUnlisted,
        classifiedBadges: classifiedBadges,
        coloredMetrics: coloredMetrics
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
