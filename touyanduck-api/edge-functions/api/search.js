// /api/search?q=NVDA&limit=10 — 在历史简报中搜索关键词

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
    const query = url.searchParams.get('q');
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '10', 10), 50);

    if (!query || query.trim().length === 0) {
      return new Response(JSON.stringify({
        error: 'missing_query',
        message: '请提供搜索关键词',
        example: '/api/search?q=NVDA',
      }), { status: 400, headers: CORS_HEADERS });
    }

    const queryLower = query.toLowerCase();

    if (KV) {
      const index = await KV.get('index:dates', { type: 'json' });
      if (index && index.dates && index.dates.length > 0) {
        const results = [];
        const searchDates = index.dates.slice(0, 90);
        for (const date of searchDates) {
          if (results.length >= limit) break;
          const summary = await KV.get(`summary:${date}`, { type: 'json' });
          if (!summary) continue;
          const searchFields = [
            summary.coreEvent || '',
            summary.takeaway || '',
            summary.actionSummary || '',
            summary.smartMoneySummary || '',
            JSON.stringify(summary.topMovers || []),
          ].join(' ').toLowerCase();
          if (searchFields.includes(queryLower)) {
            results.push({
              date: summary.date,
              coreEvent: summary.coreEvent,
              takeaway: summary.takeaway,
              sentiment: summary.sentiment,
              risk: summary.risk,
              matchedIn: getMatchedFields(summary, queryLower),
            });
          }
        }
        return new Response(JSON.stringify({ query, count: results.length, results }), { headers: CORS_HEADERS });
      }
    }

    // fallback: 搜索静态 briefing.json
    const origin = new URL(request.url).origin;
    const res = await fetch(`${origin}/briefing.json`);
    if (res.ok) {
      const briefing = await res.json();
      const text = JSON.stringify(briefing).toLowerCase();
      if (text.includes(queryLower)) {
        return new Response(JSON.stringify({
          query,
          count: 1,
          results: [{
            date: briefing.date,
            coreEvent: briefing.coreEvent?.title || '',
            takeaway: briefing.takeaway || '',
            matched: true,
          }],
          source: 'static-fallback',
        }), { headers: CORS_HEADERS });
      }
    }

    return new Response(JSON.stringify({
      query,
      results: [],
      count: 0,
      message: '暂无匹配结果',
    }), { headers: CORS_HEADERS });
  } catch (err) {
    return new Response(JSON.stringify({
      error: 'internal_error',
      message: err.message,
    }), { status: 500, headers: CORS_HEADERS });
  }
}

function getMatchedFields(summary, queryLower) {
  const matched = [];
  if ((summary.coreEvent || '').toLowerCase().includes(queryLower)) matched.push('coreEvent');
  if ((summary.takeaway || '').toLowerCase().includes(queryLower)) matched.push('takeaway');
  if ((summary.actionSummary || '').toLowerCase().includes(queryLower)) matched.push('actionSummary');
  if ((summary.smartMoneySummary || '').toLowerCase().includes(queryLower)) matched.push('smartMoney');
  if (JSON.stringify(summary.topMovers || []).toLowerCase().includes(queryLower)) matched.push('topMovers');
  return matched;
}
