// app.js — 投研鸭小程序入口文件 v6.0（自建服务器 HTTP API）

var formatUtil = require('./utils/format')

App({
  onLaunch: function() {
    console.log('投研鸭启动啦 🦆 v6.0')
    
    this.globalData.currentDate = formatUtil.formatDateCN()
    this.globalData.currentDateISO = formatUtil.formatDateISO()

    // ===== v6.0 HTTP API 模式（已弃用微信云开发）=====
    this.globalData.cloudReady = false
    console.log('🌐 数据源：自建 HTTP API ->', this.globalData.apiBaseUrl)
  },

  globalData: {
    appName: '投研鸭',
    version: '6.0.0',
    currentDate: '',
    currentDateISO: '',

    // ===== HTTP API 配置（v6.0 自建服务器）=====
    useCloud: false,                                           // 已弃用云开发
    apiBaseUrl: 'https://miniapp.touyanduck.com/api',         // 自建服务器数据接口
    cloudReady: false,                                        // 保留字段，兼容旧逻辑

    preferences: {
      isFirstLaunch: true
    },
    // 页面间导航参数
    navigateTo: {
      // 市场页：跳转到指定Tab（0美股/1M7/2亚太/3大宗/4加密）
      marketsTab: null,
      // 标的页：跳转到指定板块
      watchlistSector: null
    }
  }
})
