// pages/briefing/briefing.js
// 简报页 v7.1 — 三段式精简架构：①今日结论+重点事件 ②全球资产反应 ③聪明钱动向(+可选操作提示) ④风险情绪 ⑤核心判断(折叠)

var api = require('../../services/api')
var formatUtil = require('../../utils/format')
var colorUtil = require('../../utils/color')
var animate = require('../../utils/animate')

Page({
  data: {
    loading: true,
    // v1.3 时间状态栏
    timeStatus: null,
    marketStatus: '',
    marketStatusOpen: false,
    // 今日核心结论
    takeaway: '',
    takeawaySegments: [],
    // §1 核心事件
    coreEvent: null,
    // §1 全球资产反应
    globalReaction: [],
    // §1 三大核心判断
    coreJudgments: [],
    // §1 行动提示（可选，仅高置信机会时出现）
    actionHints: [],
    // §2 市场情绪
    sentimentScore: 0,
    displaySentiment: 0,
    sentimentLabel: '',
    marketSummaryPoints: [],
    // §4 聪明钱速览
    smartMoney: [],
    // 重点持仓
    topHoldings: [],
    // 风险提示
    riskPoints: [],
    riskNote: '', // @deprecated 旧格式兼容，新产出已改为 riskPoints 数组
    // 数据截止时间
    dataTime: '',
    dataFreshness: '',
    // v1.3 元数据
    dataMeta: null,
    // 数据源模式
    isCloud: false,
    // v1.3.1 参考源展开状态（key=判断index）
    expandedRefs: {},
    // 动画控制
    animateReady: false,
    // v1.4 语音播报
    audioUrl: '',
    isPlaying: false,
    audioLoading: false
  },

  _animTimer: null,
  _audioCtx: null,

  onLoad: function() {
    this.setData({
      isCloud: api.isCloudMode()
    })
    this._updateTimeStatus()

    // 缓存优先秒开：先读缓存渲染，再后台静默刷新
    var cached = api.getCache('briefing')
    if (cached && cached.success && cached.data) {
      this._applyData(cached.data, false)
      // 后台静默刷新（不显示loading）
      this.fetchData(false, true)
    } else {
      this.fetchData()
    }
  },

  onShow: function() {
    this._updateTimeStatus()
  },

  onUnload: function() {
    if (this._animTimer) clearInterval(this._animTimer)
    this._destroyAudio()
  },

  onPullDownRefresh: function() {
    api.clearCache()
    this.fetchData(true)
  },

  fetchData: function(isRefresh, isSilent) {
    var that = this
    var dateISO = formatUtil.formatDateISO()

    if (!isRefresh && !isSilent) {
      that.setData({ loading: true, animateReady: false })
    }

    api.getBriefing(dateISO).then(function(res) {
      if (res.success && res.data) {
        that._applyData(res.data, !isSilent)
      } else if (!isSilent) {
        that.setData({ loading: false })
      }

      if (isRefresh) {
        wx.stopPullDownRefresh()
        wx.showToast({ title: '已更新至最新', icon: 'success', duration: 1500 })
      }
    }).catch(function(err) {
      console.error('[Briefing] 数据加载失败:', err)
      if (!isSilent) {
        that.setData({ loading: false })
      }
      if (isRefresh) {
        wx.stopPullDownRefresh()
        wx.showToast({ title: '更新失败', icon: 'none', duration: 1500 })
      }
    })
  },

  _applyData: function(d, withAnimation) {
    var that = this

    // 操作提示（可选，扁平列表；兼容旧版 today/week 分组格式）
    var mapAction = function(item) {
      var info = colorUtil.getActionInfo(item.type)
      return {
        type: item.type,
        content: item.content,
        reason: item.reason || '',
        label: info.label,
        tagClass: info.tagClass
      }
    }
    var actionHints = []
    if (d.actionHints && d.actionHints.length) {
      actionHints = d.actionHints.map(mapAction)
    } else if (d.actions) {
      // 兼容旧格式：合并 today + week 为扁平列表
      var todayArr = d.actions.today || []
      var weekArr = d.actions.week || []
      actionHints = todayArr.concat(weekArr).map(mapAction)
    }

    // chain 字段兼容：支持新版对象数组 { title, brief, source, url } 及旧版字符串数组
    var coreEvent = null
    if (d.coreEvent) {
      var rawChain = d.coreEvent.chain || []
      var mappedChain = rawChain.map(function(item) {
        if (typeof item === 'string') {
          return { title: item, brief: '', source: '', url: '' }
        }
        return {
          title: item.title || '',
          brief: item.brief || '',
          source: item.source || '',
          url: item.url || ''
        }
      })
      coreEvent = {
        title: d.coreEvent.title || '',
        chain: mappedChain
      }
    }

    // v1.3 核心判断扩展字段映射
    var coreJudgments = (d.coreJudgments || []).map(function(item) {
      var result = {
        title: item.title,
        confidence: item.confidence,
        logic: item.logic
      }
      // 可选扩展字段
      if (item.keyActor) result.keyActor = item.keyActor
      if (item.references && item.references.length) {
        // v1.3.1 兼容新旧格式
        result.references = item.references.map(function(ref) {
          if (typeof ref === 'string') {
            return { name: ref, summary: '', url: '', domain: '' }
          }
          var url = ref.url || ''
          // 提取域名供前端显示（如 https://www.reuters.com/... → reuters.com）
          var domain = ''
          try {
            var m = url.match(/^https?:\/\/(?:www\.)?([^/]+)/)
            domain = m ? m[1] : url
          } catch (e) { domain = url }
          return {
            name: ref.name || '',
            summary: ref.summary || '',
            url: url,
            domain: domain
          }
        })
        result.refCount = item.references.length
        // 收起态显示的来源名称列表
        result.refNames = result.references.map(function(r) { return r.name }).join(', ')
        // 是否有丰富内容（有 summary 才算可展开）
        result.hasRichRef = item.references.some(function(ref) {
          return typeof ref !== 'string' && ref.summary
        })
      }
      if (item.probability) {
        result.probability = item.probability
        result.probClass = colorUtil.getProbabilityInfo(item.probability).tagClass
      }
      if (item.trend) {
        var trendInfo = colorUtil.getJudgmentTrendInfo(item.trend)
        result.trend = item.trend
        result.trendArrow = trendInfo.arrow
        result.trendClass = trendInfo.tagClass
      }
      result.hasExtension = !!(item.keyActor || (item.references && item.references.length) || item.probability || item.trend)
      return result
    })

    // v1.3 数据新鲜度
    var dataFreshness = formatUtil.getRelativeTime(
      d._meta && d._meta.generatedAt ? d._meta.generatedAt : d.dataTime
    )

    // v1.4 globalReaction direction normalize
    // 统一把日报层可能出现的各种 direction 变体规范为 up/down/flat
    // 对应样式：.reaction-up（红）/ .reaction-down（绿）/ .reaction-flat（灰）
    var normalizeDirection = function(dir) {
      if (!dir) return 'flat'
      var s = String(dir).toLowerCase().trim()
      if (s === 'up' || s === 'positive' || s === 'rise' || s === 'bull' || s === 'bullish') return 'up'
      if (s === 'down' || s === 'negative' || s === 'fall' || s === 'bear' || s === 'bearish') return 'down'
      return 'flat' // neutral / stable / unknown 全部兜底为 flat
    }
    var globalReaction = (d.globalReaction || []).map(function(item) {
      return {
        name: item.name || '',
        value: item.value || '--',
        direction: normalizeDirection(item.direction),
        note: item.note || ''
      }
    })

    // takeaway 富文本解析：【关键词】→ 红色高亮片段
    // 格式：[{ text: '...', highlight: false }, { text: '...', highlight: true }, ...]
    var parseTakeaway = function(str) {
      if (!str) return []
      var segments = []
      var reg = /【([^】]+)】/g
      var lastIndex = 0
      var match
      while ((match = reg.exec(str)) !== null) {
        if (match.index > lastIndex) {
          segments.push({ text: str.slice(lastIndex, match.index), highlight: false })
        }
        segments.push({ text: match[1], highlight: true })
        lastIndex = reg.lastIndex
      }
      if (lastIndex < str.length) {
        segments.push({ text: str.slice(lastIndex), highlight: false })
      }
      return segments
    }

    // marketSummaryPoints：支持新版数组；旧版字符串按句号/分号自动拆分兜底
    var marketSummaryPoints = []
    if (Array.isArray(d.marketSummaryPoints) && d.marketSummaryPoints.length) {
      marketSummaryPoints = d.marketSummaryPoints
    } else if (d.marketSummary) {
      // @deprecated 兼容旧格式（字符串型 marketSummary），新产出已改为 marketSummaryPoints 数组
      marketSummaryPoints = d.marketSummary
        .split(/[；;。]/)
        .map(function(s) { return s.trim() })
        .filter(function(s) { return s.length > 0 })
    }

    // riskPoints：支持新版数组；旧版 riskNote 字符串按句号自动拆分兜底
    var riskPoints = []
    if (Array.isArray(d.riskPoints) && d.riskPoints.length) {
      riskPoints = d.riskPoints
    } else if (d.riskNote) {
      riskPoints = d.riskNote
        .split(/[。]/)
        .map(function(s) { return s.trim() })
        .filter(function(s) { return s.length > 0 })
    }

    that.setData({
      takeaway: d.takeaway || '',
      takeawaySegments: parseTakeaway(d.takeaway || ''),
      coreEvent: coreEvent,
      globalReaction: globalReaction,
      coreJudgments: coreJudgments,
      actionHints: actionHints,
      sentimentScore: typeof d.sentimentScore === 'number' ? d.sentimentScore : 50,
      displaySentiment: withAnimation ? 0 : (typeof d.sentimentScore === 'number' ? d.sentimentScore : 50),
      sentimentLabel: d.sentimentLabel || '',
      marketSummaryPoints: marketSummaryPoints,
      smartMoney: d.smartMoney || [],
      topHoldings: d.topHoldings || [],
      riskPoints: riskPoints,
      riskNote: d.riskNote || '',
      dataTime: (d.dataTime || '').trim(),
      dataFreshness: dataFreshness || '',
      dataMeta: d._meta || null,
      audioUrl: d.audioUrl || '',
      loading: false
    })

    setTimeout(function() {
      that.setData({ animateReady: true })
    }, 50)

    if (withAnimation) {
      if (that._animTimer) clearInterval(that._animTimer)
      that._animTimer = animate.animateInteger({
        from: 0,
        to: d.sentimentScore || 50,
        duration: 1000,
        onUpdate: function(val) {
          that.setData({ displaySentiment: val })
        }
      })
    }
  },

  // v1.3 更新时间状态栏
  _updateTimeStatus: function() {
    var tz = formatUtil.getMultiTimezone()
    var status = formatUtil.getMarketStatus()
    this.setData({
      timeStatus: tz,
      marketStatus: status,
      marketStatusOpen: status === '美股交易中'
    })
  },

  // 全球资产反应点击 → 跳转市场页（美股Tab）
  onReactionTap: function() {
    getApp().globalData.navigateTo.marketsTab = 0
    wx.switchTab({ url: '/pages/markets/markets' })
  },

  // v1.3.1 参考源展开/收起切换
  onRefToggle: function(e) {
    var jIdx = e.currentTarget.dataset.jIdx
    var key = 'expandedRefs.' + jIdx
    var current = this.data.expandedRefs[jIdx]
    this.setData({ [key]: !current })
  },

  // 聪明钱速览点击 → 跳转雷达页
  onSmartMoneyTap: function() {
    wx.switchTab({ url: '/pages/radar/radar' })
  },

  // chain 来源链接点击 → 内嵌 WebView 打开
  onChainLinkTap: function(e) {
    var url = e.currentTarget.dataset.url
    var name = e.currentTarget.dataset.name || '原文'
    if (!url) return
    if (!/^https?:\/\//i.test(url)) {
      wx.showToast({ title: '链接格式不支持', icon: 'none', duration: 2000 })
      return
    }
    wx.navigateTo({
      url: '/pages/webview/webview?url=' + encodeURIComponent(url) + '&title=' + encodeURIComponent(name),
      fail: function() {
        wx.showToast({ title: '无法打开链接，请稍后重试', icon: 'none', duration: 2500 })
      }
    })
  },

  // v1.3.1 参考源链接点击 → 内嵌 WebView 打开
  onRefLinkTap: function(e) {
    var url = e.currentTarget.dataset.url
    var name = e.currentTarget.dataset.name || '文章详情'

    if (!url) return

    // 确保有 http/https 协议
    if (!/^https?:\/\//i.test(url)) {
      wx.showToast({ title: '链接格式不支持', icon: 'none', duration: 2000 })
      return
    }

    var encodedUrl = encodeURIComponent(url)
    var encodedName = encodeURIComponent(name)

    wx.navigateTo({
      url: '/pages/webview/webview?url=' + encodedUrl + '&title=' + encodedName,
      fail: function() {
        // navigateTo 失败时（如达到页面栈上限），降级 toast 提示
        wx.showToast({ title: '无法打开链接，请稍后重试', icon: 'none', duration: 2500 })
      }
    })
  },

  // v1.4 语音播报：点击播放/停止
  onVoiceTap: function() {
    var that = this

    // 如果正在播放，停止
    if (this.data.isPlaying) {
      this._destroyAudio()
      this.setData({ isPlaying: false, audioLoading: false })
      return
    }

    var audioUrl = this.data.audioUrl
    if (!audioUrl) {
      wx.showToast({ title: '暂无语音播报', icon: 'none', duration: 1500 })
      return
    }

    that.setData({ audioLoading: true })

    // cloud:// 格式需要先获取临时链接
    if (/^cloud:\/\//.test(audioUrl)) {
      wx.cloud.getTempFileURL({
        fileList: [audioUrl],
        success: function(res) {
          var fileList = res.fileList || []
          if (fileList.length > 0 && fileList[0].tempFileURL) {
            that._playAudio(fileList[0].tempFileURL)
          } else {
            that.setData({ audioLoading: false })
            wx.showToast({ title: '音频加载失败', icon: 'none', duration: 1500 })
          }
        },
        fail: function() {
          that.setData({ audioLoading: false })
          wx.showToast({ title: '音频加载失败', icon: 'none', duration: 1500 })
        }
      })
    } else {
      // 已经是 https 链接，直接播放
      that._playAudio(audioUrl)
    }
  },

  // 播放音频
  _playAudio: function(url) {
    var that = this
    this._destroyAudio()

    var ctx = wx.createInnerAudioContext()
    ctx.src = url
    ctx.onPlay(function() {
      that.setData({ isPlaying: true, audioLoading: false })
    })
    ctx.onEnded(function() {
      that.setData({ isPlaying: false })
    })
    ctx.onError(function(err) {
      console.error('[Briefing] 音频播放错误:', err)
      that.setData({ isPlaying: false, audioLoading: false })
      wx.showToast({ title: '播放失败', icon: 'none', duration: 1500 })
    })
    ctx.onStop(function() {
      that.setData({ isPlaying: false })
    })
    this._audioCtx = ctx
    ctx.play()
  },

  // 销毁音频上下文
  _destroyAudio: function() {
    if (this._audioCtx) {
      try {
        this._audioCtx.stop()
        this._audioCtx.destroy()
      } catch (e) {
        // ignore
      }
      this._audioCtx = null
    }
  }
})
