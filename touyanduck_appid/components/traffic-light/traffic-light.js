/**
 * traffic-light 组件 — 红绿灯指示器
 * 用于雷达页展示各项风险指标的信号灯
 */

Component({
  properties: {
    // 指标列表 [{ name, value, status: 'green'|'yellow'|'red' }]
    lights: {
      type: Array,
      value: []
    }
  }
})
