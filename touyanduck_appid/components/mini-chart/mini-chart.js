/**
 * mini-chart 组件 — 迷你走势折线图
 * 使用 Canvas 2D 绘制 sparkline 效果
 */
Component({
  properties: {
    // 走势数据数组，如 [5180, 5195, 5220, 5210, 5235, 5248, 5254]
    data: {
      type: Array,
      value: []
    },
    // 画布宽度（rpx）
    width: {
      type: Number,
      value: 160
    },
    // 画布高度（rpx）
    height: {
      type: Number,
      value: 50
    },
    // 是否为上涨（控制颜色）
    isUp: {
      type: Boolean,
      value: true
    },
    // 自定义线条颜色（优先级高于 isUp）
    color: {
      type: String,
      value: ''
    },
    // 线宽
    lineWidth: {
      type: Number,
      value: 2
    },
    // 是否填充渐变
    fill: {
      type: Boolean,
      value: true
    },
    // 唯一ID（同页面多个chart时区分）
    chartId: {
      type: String,
      value: ''
    }
  },

  data: {
    canvasId: '',
    pxWidth: 0,
    pxHeight: 0,
    noData: false
  },

  lifetimes: {
    attached: function() {
      // 生成唯一 canvasId
      var id = this.properties.chartId || ('mc_' + Math.random().toString(36).substr(2, 8))
      this.setData({ canvasId: id })
    },
    ready: function() {
      this.initCanvas()
    }
  },

  observers: {
    'data': function() {
      var d = this.properties.data
      var hasEnough = d && d.length >= 2
      this.setData({ noData: !hasEnough })
      if (this._canvasReady && hasEnough) {
        this.drawChart()
      }
    }
  },

  methods: {
    initCanvas: function() {
      var that = this
      // rpx 转 px
      var sysInfo = wx.getSystemInfoSync()
      var ratio = sysInfo.windowWidth / 750
      var dpr = sysInfo.pixelRatio || 2

      that._ratio = ratio
      that._dpr = dpr
      that.setData({
        pxWidth: Math.round(that.properties.width * ratio),
        pxHeight: Math.round(that.properties.height * ratio)
      })

      // 延迟获取 canvas 节点
      setTimeout(function() {
        that.createSelectorQuery().select('#' + that.data.canvasId)
          .fields({ node: true, size: true })
          .exec(function(res) {
            if (!res || !res[0] || !res[0].node) return

            var canvas = res[0].node
            var ctx = canvas.getContext('2d')
            
            // 设置 canvas 实际像素尺寸（高清）
            canvas.width = that.data.pxWidth * dpr
            canvas.height = that.data.pxHeight * dpr
            ctx.scale(dpr, dpr)

            that._canvas = canvas
            that._ctx = ctx
            that._canvasReady = true

            that.drawChart()
          })
      }, 100)
    },

    drawChart: function() {
      var ctx = this._ctx
      var data = this.properties.data
      if (!ctx || !data || data.length < 2) return

      var w = this.data.pxWidth
      var h = this.data.pxHeight
      var padding = 2 // 上下留白

      // 清空画布
      ctx.clearRect(0, 0, w, h)

      // 计算数据范围
      var min = data[0]
      var max = data[0]
      for (var i = 1; i < data.length; i++) {
        if (data[i] < min) min = data[i]
        if (data[i] > max) max = data[i]
      }
      
      // 避免 min === max（水平线）
      var range = max - min
      if (range === 0) range = 1

      // 确定颜色
      var lineColor = this.properties.color
      if (!lineColor) {
        lineColor = this.properties.isUp ? '#e74c3c' : '#27ae60'
      }

      // 计算点坐标
      var points = []
      var stepX = w / (data.length - 1)
      for (var j = 0; j < data.length; j++) {
        var x = j * stepX
        var y = padding + (1 - (data[j] - min) / range) * (h - 2 * padding)
        points.push({ x: x, y: y })
      }

      // 绘制渐变填充
      if (this.properties.fill) {
        ctx.beginPath()
        ctx.moveTo(points[0].x, points[0].y)
        
        for (var k = 1; k < points.length; k++) {
          ctx.lineTo(points[k].x, points[k].y)
        }
        
        // 闭合到底部
        ctx.lineTo(points[points.length - 1].x, h)
        ctx.lineTo(points[0].x, h)
        ctx.closePath()

        // 渐变填充
        var gradient = ctx.createLinearGradient(0, 0, 0, h)
        if (this.properties.isUp) {
          gradient.addColorStop(0, 'rgba(231, 76, 60, 0.15)')
          gradient.addColorStop(1, 'rgba(231, 76, 60, 0.01)')
        } else {
          gradient.addColorStop(0, 'rgba(39, 174, 96, 0.15)')
          gradient.addColorStop(1, 'rgba(39, 174, 96, 0.01)')
        }
        ctx.fillStyle = gradient
        ctx.fill()
      }

      // 绘制折线
      ctx.beginPath()
      ctx.moveTo(points[0].x, points[0].y)
      
      for (var m = 1; m < points.length; m++) {
        ctx.lineTo(points[m].x, points[m].y)
      }

      ctx.strokeStyle = lineColor
      ctx.lineWidth = this.properties.lineWidth
      ctx.lineJoin = 'round'
      ctx.lineCap = 'round'
      ctx.stroke()

      // 在最后一个点画一个小圆点
      var lastPoint = points[points.length - 1]
      ctx.beginPath()
      ctx.arc(lastPoint.x, lastPoint.y, 2.5, 0, Math.PI * 2)
      ctx.fillStyle = lineColor
      ctx.fill()
    }
  }
})
