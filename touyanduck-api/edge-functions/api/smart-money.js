// /api/smart-money?fund=伯克希尔 — 聪明钱历史动态查询

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
  const url = new URL(request.url);
  const fund = url.searchParams.get('fund');

  try {
    if (KV) {
      if (fund) {
        const index = await KV.get('index:dates', { type: 'json' });
        if (!index || !index.dates || index.dates.length === 0) {
          return new Response(JSON.stringify({ fund, records: [], message: '暂无历史数据' }), { headers: CORS_HEADERS });
        }
        const records = [];
        const searchDates = index.dates.slice(0, 30);
        for (const date of searchDates) {
          const briefing = await KV.get(`briefing:${date}`, { type: 'json' });
          if (briefing && briefing.smartMoney) {
            for (const sm of briefing.smartMoney) {
              if (sm.source && sm.source.includes(fund)) {
                records.push({ date, source: sm.source, action: sm.action, signal: sm.signal });
              }
            }
          }
        }
        return new Response(JSON.stringify({ fund, count: records.length, records }), { headers: CORS_HEADERS });
      }

      const latestBriefing = await KV.get('briefing:latest', { type: 'json' });
      if (latestBriefing && latestBriefing.smartMoney) {
        return new Response(JSON.stringify({
          date: latestBriefing.date,
          smartMoney: latestBriefing.smartMoney || [],
          topHoldings: latestBriefing.topHoldings || [],
          smartMoneyDetail: latestBriefing.smartMoneyDetail || [],
          smartMoneyHoldings: latestBriefing.smartMoneyHoldings || [],
        }), { headers: CORS_HEADERS });
      }
    }

    // fallback: 从静态 briefing.json 读取
    const origin = new URL(request.url).origin;
    const res = await fetch(`${origin}/briefing.json`);
    if (res.ok) {
      const briefing = await res.json();
      return new Response(JSON.stringify({
        date: briefing.date,
        smartMoney: briefing.smartMoney || [],
        topHoldings: briefing.topHoldings || [],
        smartMoneyDetail: briefing.smartMoneyDetail || [],
        smartMoneyHoldings: briefing.smartMoneyHoldings || [],
        source: 'static-fallback',
      }), { headers: CORS_HEADERS });
    }

    return new Response(JSON.stringify({
      date: null, smartMoney: [], topHoldings: [], message: '暂无聪明钱数据',
    }), { headers: CORS_HEADERS });
  } catch (err) {
    return new Response(JSON.stringify({
      error: 'internal_error',
      message: err.message,
    }), { status: 500, headers: CORS_HEADERS });
  }
}
