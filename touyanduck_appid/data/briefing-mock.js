/**
 * briefing-mock.js — 简报页面 Mock 数据 v5.0
 * 对齐 investment-agent-daily Skill §1+§2摘要+§4摘要
 * v5.0 变更：删除 keyDeltas，新增 takeaway；chain 升级为对象数组；globalReaction 加 note；actions 加 reason
 */
module.exports = {
  // 今日核心结论（一句话 takeaway，有立场有行动方向）
  takeaway: 'AI基建周期确认延长，云厂商CAPEX上修已成共识——GTC催化尚未完全定价，逢低加仓算力链，等待6月降息窗口确认。',

  // §1 核心事件
  coreEvent: {
    title: '英伟达GTC发布Blackwell Ultra架构，AI算力竞赛进入新阶段',
    chain: [
      {
        title: 'NVIDIA发布Blackwell Ultra + Vera Rubin路线图',
        brief: '训练成本预计下降40%，推理效率提升3倍，供应链能见度延长至2027',
        source: 'NVIDIA GTC',
        url: 'https://www.nvidia.com/en-us/events/gtc/'
      },
      {
        title: '微软/Meta/谷歌抢先锁定2026年产能',
        brief: '三大云厂商同步上修CAPEX指引，AI算力资本开支进入新一轮扩张周期',
        source: 'Bloomberg'
      },
      {
        title: 'AI算力链全线受益，供应链订单能见度大幅提升',
        brief: 'AVGO/TSM/ASML随NVDA同步上涨，板块整体估值仍低于历史均值',
        source: 'Reuters'
      }
    ]
  },

  // §1 全球资产反应（5-6项核心资产当日涨跌）
  globalReaction: [
    { name: '标普500', value: '+0.87%', direction: 'up', note: 'GTC催化风险偏好回升' },
    { name: '纳斯达克', value: '+1.42%', direction: 'up', note: '科技股领涨，AI板块强势' },
    { name: '恒生科技', value: '+2.15%', direction: 'up', note: '南向资金持续流入' },
    { name: '黄金', value: '-0.32%', direction: 'down', note: '风险偏好回升压制避险' },
    { name: '10Y美债', value: '4.23%', direction: 'flat', note: '降息预期基本稳定' },
    { name: 'BTC', value: '+3.18%', direction: 'up', note: '风险资产同步上涨' }
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

  // §1 行动建议（每条加 reason）
  actions: {
    today: [
      {
        type: 'buy',
        content: 'AI算力链（NVDA/AVGO/TSM）逢低加仓，GTC催化尚未完全定价',
        reason: 'NVDA NTM P/E约33x低于12个月均值35x，GTC后机构目标价中位数$1050'
      },
      {
        type: 'hold',
        content: '黄金多头继续持有，美债利率下行趋势支撑金价',
        reason: '实际利率仍处回落通道，黄金与美债负相关逻辑完整'
      }
    ],
    week: [
      {
        type: 'bullish',
        content: '关注本周五非农数据，若弱于预期将强化降息叙事',
        reason: '当前市场定价6月降息概率约65%，弱非农将推升至75%以上'
      },
      {
        type: 'sell',
        content: '减持前期涨幅过大的小盘成长股，锁定部分利润',
        reason: '小盘成长估值已回到历史80分位，性价比低于大盘AI核心标的'
      },
      {
        type: 'hold',
        content: 'A股维持半仓观望，等待4月政治局会议政策信号',
        reason: '政治局会议预计4月下旬，政策方向未明前不宜重仓追涨'
      }
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
      action: '港股均涨+1.8%，外资动向代理指标为绿灯信号',
      signal: 'bullish'
    }
  ],

  // 风险提示
  riskNote: '本周五公布非农数据，若大超预期可能逆转降息预期。英伟达GTC利好已部分price in，注意"买预期卖事实"风险。',

  // 数据截止时间
  dataTime: '2026-03-31 09:00 BJT'
}
