// /api/sync — 数据同步端点
// 接收每日产出的 JSON 数据，写入 KV 存储
// 需要 Authorization: Bearer <TOKEN> 鉴权

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Content-Type': 'application/json; charset=utf-8',
};

// 同步密钥 — 部署后在 EdgeOne 控制台的环境变量中设置 SYNC_TOKEN
const DEFAULT_TOKEN = 'touyanduck-sync-2026';

export async function onRequest({ request, params, env }) {
  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: CORS_HEADERS });
  }

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'method_not_allowed',
      message: '请使用 POST 方法',
    }), { status: 405, headers: CORS_HEADERS });
  }

  const KV = env.TOUYANDUCK_KV;

  if (!KV) {
    return new Response(JSON.stringify({
      error: 'kv_not_bound',
      message: 'KV 存储未绑定，请在 EdgeOne 控制台绑定 TOUYANDUCK_KV 命名空间后重新部署',
    }), { status: 503, headers: CORS_HEADERS });
  }

  // 鉴权
  const authHeader = request.headers.get('Authorization') || '';
  const token = authHeader.replace('Bearer ', '');
  const expectedToken = env.SYNC_TOKEN || DEFAULT_TOKEN;

  if (token !== expectedToken) {
    return new Response(JSON.stringify({
      error: 'unauthorized',
      message: '鉴权失败，请提供正确的 Authorization: Bearer <token>',
    }), { status: 401, headers: CORS_HEADERS });
  }

  try {
    const payload = await request.json();
    const { date, briefing, markets, radar, watchlist, briefingMd } = payload;

    if (!date || !briefing) {
      return new Response(JSON.stringify({
        error: 'invalid_payload',
        message: '缺少必要字段: date, briefing',
      }), { status: 400, headers: CORS_HEADERS });
    }

    // 1. 存储各个完整 JSON
    const writeOps = [
      KV.put(`briefing:${date}`, JSON.stringify(briefing)),
      KV.put('briefing:latest', JSON.stringify(briefing)),
    ];

    if (markets) {
      writeOps.push(KV.put(`markets:${date}`, JSON.stringify(markets)));
      writeOps.push(KV.put('markets:latest', JSON.stringify(markets)));
    }
    if (radar) {
      writeOps.push(KV.put(`radar:${date}`, JSON.stringify(radar)));
      writeOps.push(KV.put('radar:latest', JSON.stringify(radar)));
    }
    if (watchlist) {
      writeOps.push(KV.put(`watchlist:${date}`, JSON.stringify(watchlist)));
      writeOps.push(KV.put('watchlist:latest', JSON.stringify(watchlist)));
    }
    if (briefingMd) {
      writeOps.push(KV.put(`md:${date}`, briefingMd));
      writeOps.push(KV.put('md:latest', briefingMd));
    }

    // 2. 生成并存储摘要（summary）
    const summary = generateSummary(date, briefing, markets, radar);
    writeOps.push(KV.put(`summary:${date}`, JSON.stringify(summary)));
    writeOps.push(KV.put('summary:latest', JSON.stringify(summary)));

    // 3. 更新日期索引
    const existingIndex = await KV.get('index:dates', { type: 'json' }) || { dates: [], count: 0 };
    if (!existingIndex.dates.includes(date)) {
      existingIndex.dates.unshift(date);
      existingIndex.dates.sort((a, b) => b.localeCompare(a)); // 降序
    }
    existingIndex.count = existingIndex.dates.length;
    existingIndex.latest = existingIndex.dates[0];
    existingIndex.updatedAt = new Date().toISOString();
    writeOps.push(KV.put('index:dates', JSON.stringify(existingIndex)));

    // 4. 更新趋势数据（预计算 7d / 14d / 30d）
    const trendOps = await updateTrend(KV, existingIndex.dates);
    writeOps.push(...trendOps);

    // 执行所有写入
    await Promise.all(writeOps);

    return new Response(JSON.stringify({
      success: true,
      date,
      message: `${date} 数据同步成功`,
      kvKeysWritten: writeOps.length,
      totalDates: existingIndex.count,
    }), { headers: CORS_HEADERS });
  } catch (err) {
    return new Response(JSON.stringify({
      error: 'sync_failed',
      message: err.message,
      stack: err.stack,
    }), { status: 500, headers: CORS_HEADERS });
  }
}

// 从完整 JSON 提取精简摘要
function generateSummary(date, briefing, markets, radar) {
  const summary = {
    date,
    updatedAt: new Date().toISOString(),
  };

  // 情绪
  summary.sentiment = {
    score: briefing.sentimentScore || 0,
    label: briefing.sentimentLabel || '未知',
  };

  // 核心事件
  summary.coreEvent = briefing.coreEvent?.title || '';
  summary.takeaway = briefing.takeaway || '';

  // 行动建议
  if (briefing.actionHints && briefing.actionHints.length > 0) {
    summary.actionSummary = briefing.actionHints[0].content || '';
  }

  // 聪明钱摘要
  if (briefing.smartMoney && briefing.smartMoney.length > 0) {
    summary.smartMoneySummary = briefing.smartMoney
      .slice(0, 3)
      .map(sm => `${sm.source}: ${sm.action}`)
      .join(' | ');
  }

  // 市场要点
  summary.topMovers = (briefing.marketSummaryPoints || []).slice(0, 3);

  // 风险
  if (radar) {
    summary.risk = {
      score: radar.riskScore || 0,
      level: radar.riskLevel || 'unknown',
    };

    // 红绿灯统计
    if (radar.trafficLights) {
      const lights = { red: 0, yellow: 0, green: 0 };
      radar.trafficLights.forEach(tl => {
        if (tl.status === 'red') lights.red++;
        else if (tl.status === 'yellow') lights.yellow++;
        else if (tl.status === 'green') lights.green++;
      });
      summary.trafficLights = lights;
    }
  }

  // 美股指数
  if (markets && markets.usMarkets) {
    summary.usMarkets = {};
    for (const m of markets.usMarkets) {
      const key = m.name.includes('标普') ? 'sp500'
        : m.name.includes('纳斯达克') ? 'nasdaq'
        : m.name.includes('道琼斯') ? 'dji'
        : m.name.includes('VIX') ? 'vix'
        : null;
      if (key) {
        summary.usMarkets[key] = { price: m.price, change: m.change };
      }
    }
    // 布伦特原油
    if (markets.commodities) {
      for (const c of markets.commodities) {
        if (c.name.includes('布伦特')) {
          summary.usMarkets.brent = { price: c.price, change: c.change };
        }
      }
    }
  }

  return summary;
}

// 预计算趋势数据
async function updateTrend(KV, allDates) {
  const ops = [];

  for (const days of [7, 14, 30]) {
    const recentDates = allDates.slice(0, days);
    const dataPoints = [];

    for (const d of recentDates) {
      const s = await KV.get(`summary:${d}`, { type: 'json' });
      if (s) {
        dataPoints.push({
          date: s.date,
          sentimentScore: s.sentiment?.score,
          riskScore: s.risk?.score,
          sp500: s.usMarkets?.sp500,
          vix: s.usMarkets?.vix,
          brent: s.usMarkets?.brent,
          coreEvent: s.coreEvent,
        });
      }
    }

    ops.push(KV.put(`trend:${days}d`, JSON.stringify({
      days,
      actualDays: dataPoints.length,
      data: dataPoints,
      updatedAt: new Date().toISOString(),
    })));
  }

  return ops;
}
