/**
 * skeleton 组件 — 骨架屏加载占位
 * 页面数据加载前展示灰色闪烁占位块
 */

Component({
  properties: {
    // 骨架屏类型：briefing / markets / watchlist / radar
    type: {
      type: String,
      value: 'briefing'
    },
    // 是否显示骨架屏
    loading: {
      type: Boolean,
      value: true
    },
    // 行数（用于列表型骨架）
    rows: {
      type: Number,
      value: 4
    }
  },

  data: {
    rowArray: []
  },

  observers: {
    'rows': function(rows) {
      var arr = []
      for (var i = 0; i < rows; i++) {
        arr.push(i)
      }
      this.setData({ rowArray: arr })
    }
  },

  lifetimes: {
    attached: function() {
      var arr = []
      for (var i = 0; i < this.data.rows; i++) {
        arr.push(i)
      }
      this.setData({ rowArray: arr })
    }
  }
})
