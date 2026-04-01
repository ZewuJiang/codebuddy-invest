// app.js — 投研鸭小程序入口文件 v5.0（支持云开发）

var formatUtil = require('./utils/format')

App({
  onLaunch: function() {
    console.log('投研鸭启动啦 🦆 v5.0')
    
    this.globalData.currentDate = formatUtil.formatDateCN()
    this.globalData.currentDateISO = formatUtil.formatDateISO()

    // ===== 微信云开发初始化 =====
    // 如果你已开通云开发并配置了环境ID，将下面的 'your-cloud-env-id' 
    // 替换为你的真实环境ID，并将 useCloud 改为 true
    if (this.globalData.useCloud && wx.cloud) {
      wx.cloud.init({
        env: this.globalData.cloudEnvId,
        traceUser: true
      })
      this.globalData.cloudReady = true
      console.log('☁️ 云开发已初始化，环境:', this.globalData.cloudEnvId)
    } else {
      this.globalData.cloudReady = false
      console.log('📦 使用本地Mock数据模式')
    }
  },

  globalData: {
    appName: '投研鸭',
    version: '5.0.0',
    currentDate: '',
    currentDateISO: '',

    // ===== 云开发配置 =====
    // 开通云开发后，修改以下两个值：
    //   useCloud: true
    //   cloudEnvId: '你在微信开发者工具中看到的环境ID'
    useCloud: true,            // 总开关：true=用云数据库, false=用Mock数据
    cloudEnvId: 'cloud1-3g6wj06h84f38ea8',  // 云环境ID
    cloudReady: false,         // 云开发是否初始化成功（自动设置，勿手动改）

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
