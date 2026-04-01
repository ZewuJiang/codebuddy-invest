/**
 * radar-mock.js — 雷达/风险监控 Mock 数据 v4.0
 * 对齐 Skill §5: 7-8项红绿灯 + 监控阈值表 + 风险提示 + §4聪明钱动向
 */
module.exports = {
  "trafficLights": [
    { "name": "VIX波动率", "value": "13.0", "status": "green", "threshold": "<18绿 / 18-25黄 / >25红" },
    { "name": "10Y美债收益率", "value": "4.21%", "status": "yellow", "threshold": "<4.0%绿 / 4.0-4.5%黄 / >4.5%红" },
    { "name": "布伦特原油", "value": "$87.48", "status": "yellow", "threshold": "<80绿 / 80-95黄 / >95红" },
    { "name": "美元指数 DXY", "value": "104.5", "status": "yellow", "threshold": "<102绿 / 102-107黄 / >107红" },
    { "name": "HY信用利差", "value": "3.42%", "status": "green", "threshold": "<4%绿 / 4-5%黄 / >5%红" },
    { "name": "外资动向", "value": "港股均涨+1.8%", "status": "green", "threshold": "港股均涨≥+1.5%绿 / 0~+1.5%黄 / 跌红（北向净买额已于2024-08-19停止披露）" },
    { "name": "离岸人民币 CNH", "value": "7.2650", "status": "yellow", "threshold": "<7.15绿 / 7.15-7.30黄 / >7.30红" }
  ],

  "riskScore": 38,
  "riskLevel": "medium",
  "riskAdvice": "当前市场处于中等风险区间，建议维持6成仓位，保留现金应对潜在波动。",

  "monitorTable": [
    { "condition": "VIX突破25", "action": "将股票仓位降至5成以下，增配国债ETF" },
    { "condition": "10Y美债破4.5%", "action": "减持高估值成长股，增配短久期债券" },
    { "condition": "布伦特原油破$95", "action": "关注通胀回升风险，减持消费/航空" },
    { "condition": "DXY突破107", "action": "减持新兴市场/大宗商品，美元资产避险" },
    { "condition": "港股单日均跌超-2%（外资动向转红）", "action": "A/H股短期回避，等待外资情绪企稳" },
    { "condition": "CNH破7.30", "action": "减持港股人民币计价资产" }
  ],

  "riskAlerts": [
    {
      "title": "非农数据超预期风险",
      "probability": "35%",
      "impact": "高",
      "response": "若非农>25万+时薪>4%，降息预期将大幅推后，科技股或回调3-5%",
      "level": "high"
    },
    {
      "title": "英伟达GTC利好兑现卖出",
      "probability": "45%",
      "impact": "中",
      "response": "GTC后若NVDA回调，视为加仓机会（支撑位$820附近）",
      "level": "medium"
    },
    {
      "title": "地缘冲突升级（中东/乌俄）",
      "probability": "20%",
      "impact": "高",
      "response": "原油/黄金跳涨，股市短期承压，VIX飙升",
      "level": "medium"
    }
  ],

  "events": [
    { "date": "周一", "title": "ISM制造业PMI公布", "impact": "medium" },
    { "date": "周三", "title": "ADP就业数据", "impact": "medium" },
    { "date": "周三", "title": "美联储会议纪要", "impact": "high" },
    { "date": "周五", "title": "非农就业数据", "impact": "high" },
    { "date": "周五", "title": "失业率公布", "impact": "high" }
  ],

  "alerts": [
    { "level": "danger", "text": "英伟达盘后大涨4.2%，带动AI板块情绪，注意追高风险", "time": "23:30" },
    { "level": "warning", "text": "10年期美债收益率突破4.2%，若上破4.35%需警惕", "time": "22:15" },
    { "level": "warning", "text": "黄金突破2200美元，RSI进入超买区间（72.5）", "time": "21:40" },
    { "level": "info", "text": "VIX降至13下方，市场恐慌情绪偏低，适合布局", "time": "21:00" }
  ],

  "smartMoneyDetail": [
    {
      "tier": "T1旗舰",
      "funds": [
        { "name": "桥水基金", "action": "增持中国ETF $2.3亿，减持美债", "signal": "bullish" },
        { "name": "伯克希尔", "action": "继续增持西方石油OXY，现金$189B创新高", "signal": "neutral" },
        { "name": "文艺复兴", "action": "期权数据显示增持科技股看涨头寸", "signal": "bullish" }
      ]
    },
    {
      "tier": "T2成长",
      "funds": [
        { "name": "ARK木头姐", "action": "减持TSLA，加仓COIN/PLTR", "signal": "neutral" },
        { "name": "高瓴资本", "action": "加仓PDD/BYD，减持JD", "signal": "bullish" },
        { "name": "老虎环球", "action": "加仓印度IT外包公司", "signal": "neutral" }
      ]
    },
    {
      "tier": "策略师观点",
      "funds": [
        { "name": "高盛策略师", "action": "维持SPX年末目标5200，AI盈利周期刚开始", "signal": "bullish" },
        { "name": "摩根士丹利", "action": "建议增配日本/印度股票，减持欧洲", "signal": "neutral" }
      ]
    }
  ],

  "dataTime": "2026-03-31 09:00 BJT"
}
