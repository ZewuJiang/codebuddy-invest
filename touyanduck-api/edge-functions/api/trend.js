// /api/trend?days=7|14|30 — 返回最近 N 天趋势数据

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Content-Type': 'application/json; charset=utf-8',
};

export async function onRequest({ request, params, env }) {
  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: CORS_HEADERS });
  }

  const KV = env.TOUYANDUCK_KV;

  try {
    const url = new URL(request.url);
    const days = parseInt(url.searchParams.get('days') || '7', 10);
    const validDays = [7, 14, 30].includes(days) ? days : 7;

    if (KV) {
      const trend = await KV.get(`trend:${validDays}d`, { type: 'json' });
      if (trend) {
        return new Response(JSON.stringify(trend), { headers: CORS_HEADERS });
      }

      const index = await KV.get('index:dates', { type: 'json' });
      if (index && index.dates && index.dates.length > 0) {
        const recentDates = index.dates.slice(0, validDays);
        const dataPoints = [];
        for (const date of recentDates) {
          const summary = await KV.get(`summary:${date}`, { type: 'json' });
          if (summary) {
            dataPoints.push({
              date: summary.date,
              sentimentScore: summary.sentiment?.score,
              sentimentLabel: summary.sentiment?.label,
              riskScore: summary.risk?.score,
              riskLevel: summary.risk?.level,
              sp500: summary.usMarkets?.sp500,
              vix: summary.usMarkets?.vix,
              brent: summary.usMarkets?.brent,
              coreEvent: summary.coreEvent,
            });
          }
        }
        return new Response(JSON.stringify({
          days: validDays,
          actualDays: dataPoints.length,
          data: dataPoints,
        }), { headers: CORS_HEADERS });
      }
    }

    // fallback: 仅有当天数据
    return new Response(JSON.stringify({
      days: validDays,
      data: [],
      message: '趋势数据需要多日积累，暂时仅支持当天数据查询',
      source: 'static-fallback',
    }), { headers: CORS_HEADERS });
  } catch (err) {
    return new Response(JSON.stringify({
      error: 'internal_error',
      message: err.message,
    }), { status: 500, headers: CORS_HEADERS });
  }
}
