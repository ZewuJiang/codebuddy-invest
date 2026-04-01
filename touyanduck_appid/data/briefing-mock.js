/**
 * briefing-mock.js — 简报页面 Mock 数据 v4.0
 * 对齐 investment-agent-daily Skill §1+§2摘要+§4摘要
 */
module.exports = {
  // §1 核心事件
  coreEvent: {
    title: '英伟达GTC大会发布Blackwell Ultra架构，AI算力竞赛进入新阶段',
    chain: [
      'NVIDIA发布Blackwell Ultra GPU + Vera Rubin路线图',
      '训练成本预计下降40%，推理效率提升3倍',
      '微软/Meta/谷歌抢先锁定2026年产能',
      'AI算力资本开支预期上修，供应链全线受益'
    ]
  },

  // §1 全球资产反应（5-6项核心资产当日涨跌）
  globalReaction: [
    { name: '标普500', value: '+0.87%', direction: 'up' },
    { name: '纳斯达克', value: '+1.42%', direction: 'up' },
    { name: '恒生科技', value: '+2.15%', direction: 'up' },
    { name: '黄金', value: '-0.32%', direction: 'down' },
    { name: '10Y美债', value: '4.23%', direction: 'flat' },
    { name: 'BTC', value: '+3.18%', direction: 'up' }
  ],

  // §1 三大核心判断
  coreJudgments: [
    {
      title: 'AI基础设施投资周期远未见顶',
      confidence: 85,
      logic: 'Blackwell Ultra性能跃升→云厂商CAPEX上修→算力链订单能见度延长至2027'
    },
    {
      title: '美联储6月降息概率提升但非确定性事件',
      confidence: 65,
      logic: 'PCE通胀温和→就业市场降温→但核心服务通胀粘性仍在→需观察5月非农'
    },
    {
      title: '中国互联网平台估值修复行情延续',
      confidence: 70,
      logic: '政策暖风频吹→回购力度加大→南向资金持续流入→恒生科技PE仍处历史低位'
    }
  ],

  // §1 行动建议
  actions: {
    today: [
      { type: 'buy', content: 'AI算力链（NVDA/AVGO/TSM）逢低加仓，GTC催化尚未完全定价' },
      { type: 'hold', content: '黄金多头继续持有，美债利率下行趋势支撑金价' }
    ],
    week: [
      { type: 'bullish', content: '关注本周五非农数据，若弱于预期将强化降息叙事' },
      { type: 'sell', content: '减持前期涨幅过大的小盘成长股，锁定部分利润' },
      { type: 'hold', content: 'A股维持半仓观望，等待4月政治局会议政策信号' }
    ]
  },

  // §2 市场情绪
  sentimentScore: 62,
  sentimentLabel: '偏贪婪',
  marketSummary: '全球风险偏好回升，科技股领涨，VIX回落至低位，但需警惕非农数据扰动',

  // §4 聪明钱速览
  smartMoney: [
    {
      source: '桥水基金',
      action: '增持中国ETF约$2.3亿',
      signal: 'bullish'
    },
    {
      source: '木头姐ARK',
      action: '继续减持TSLA，加仓COIN和PLTR',
      signal: 'neutral'
    },
    {
      source: '港股成交代理',
      action: '港股均涨+1.8%，外资动向代理指标为绿灯信号（北向净买额已于2024-08-19停止披露）',
      signal: 'bullish'
    }
  ],

  // 风险提示
  riskNote: '本周五公布非农数据，若大超预期可能逆转降息预期。英伟达GTC利好已部分price in，注意"买预期卖事实"风险。',

  // 数据截止时间
  dataTime: '2026-03-31 09:00 BJT'
}
