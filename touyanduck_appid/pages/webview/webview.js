// pages/webview/webview.js
// 内嵌网页页面 — 用于在小程序内打开参考源链接

Page({
  data: {
    url: '',
    title: '文章详情',
    urlInvalid: false
  },

  onLoad: function(options) {
    var rawUrl = options.url ? decodeURIComponent(options.url) : ''
    var title = options.title ? decodeURIComponent(options.title) : '文章详情'

    if (!rawUrl || !/^https?:\/\//i.test(rawUrl)) {
      this.setData({ urlInvalid: true })
      wx.showToast({ title: '链接无效', icon: 'none' })
      return
    }

    this.setData({ url: rawUrl, title: title })

    // 动态设置导航栏标题
    wx.setNavigationBarTitle({ title: title })
  },

  // web-view 加载完成
  onWebviewLoad: function() {
    console.log('[WebView] 加载完成:', this.data.url)
  },

  // web-view 加载失败
  onWebviewError: function(e) {
    console.error('[WebView] 加载失败:', e.detail)
    wx.showToast({
      title: '页面加载失败',
      icon: 'none',
      duration: 2000
    })
  }
})
