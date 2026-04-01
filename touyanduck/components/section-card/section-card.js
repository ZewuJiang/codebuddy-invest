/**
 * section-card 组件 — 通用可折叠卡片
 * 支持标题 + 折叠/展开 + slot 内容
 */

Component({
  properties: {
    // 卡片标题
    title: {
      type: String,
      value: ''
    },
    // 是否支持折叠
    collapsible: {
      type: Boolean,
      value: false
    },
    // 初始是否展开
    expanded: {
      type: Boolean,
      value: true
    },
    // 额外的 class（如 risk-card）
    extraClass: {
      type: String,
      value: ''
    },
    // 左边框颜色（可选覆盖）
    borderColor: {
      type: String,
      value: ''
    }
  },

  data: {
    isExpanded: true
  },

  lifetimes: {
    attached: function() {
      this.setData({
        isExpanded: this.data.expanded
      })
    }
  },

  methods: {
    toggleExpand: function() {
      if (!this.data.collapsible) return
      this.setData({
        isExpanded: !this.data.isExpanded
      })
    }
  }
})
