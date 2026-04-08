// /api/archive?date=2026-04-08&type=summary|full — 按日期查询历史简报

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
    const date = url.searchParams.get('date');
    const type = url.searchParams.get('type') || 'summary';

    if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      return new Response(JSON.stringify({
        error: 'invalid_date',
        message: '请提供有效的日期参数，格式: YYYY-MM-DD',
        example: '/api/archive?date=2026-04-08',
      }), { status: 400, headers: CORS_HEADERS });
    }

    if (KV) {
      if (type === 'full') {
        const [briefing, markets, radar, watchlist, md] = await Promise.all([
          KV.get(`briefing:${date}`, { type: 'json' }),
          KV.get(`markets:${date}`, { type: 'json' }),
          KV.get(`radar:${date}`, { type: 'json' }),
          KV.get(`watchlist:${date}`, { type: 'json' }),
          KV.get(`md:${date}`, { type: 'text' }),
        ]);
        if (briefing) {
          return new Response(JSON.stringify({ date, briefing, markets, radar, watchlist, briefingMd: md }), { headers: CORS_HEADERS });
        }
      } else {
        const summary = await KV.get(`summary:${date}`, { type: 'json' });
        if (summary) {
          return new Response(JSON.stringify(summary), { headers: CORS_HEADERS });
        }
      }
    }

    // fallback: 从静态文件获取当天数据
    const origin = new URL(request.url).origin;
    const metaRes = await fetch(`${origin}/meta.json`);
    if (metaRes.ok) {
      const meta = await metaRes.json();
      const staticDate = meta.date || meta.generatedAt?.split('T')[0];
      if (staticDate === date) {
        if (type === 'full') {
          const [bRes, mRes, rRes, wRes, mdRes] = await Promise.all([
            fetch(`${origin}/briefing.json`),
            fetch(`${origin}/markets.json`),
            fetch(`${origin}/radar.json`),
            fetch(`${origin}/watchlist.json`),
            fetch(`${origin}/briefing.md`),
          ]);
          return new Response(JSON.stringify({
            date,
            briefing: bRes.ok ? await bRes.json() : null,
            markets: mRes.ok ? await mRes.json() : null,
            radar: rRes.ok ? await rRes.json() : null,
            watchlist: wRes.ok ? await wRes.json() : null,
            briefingMd: mdRes.ok ? await mdRes.text() : null,
            source: 'static-fallback',
          }), { headers: CORS_HEADERS });
        }
        const bRes = await fetch(`${origin}/briefing.json`);
        if (bRes.ok) {
          const data = await bRes.json();
          return new Response(JSON.stringify({ ...data, source: 'static-fallback' }), { headers: CORS_HEADERS });
        }
      }
    }

    return new Response(JSON.stringify({
      error: 'not_found',
      message: `没有找到 ${date} 的数据`,
      hint: '使用 /api/dates 查看所有可用日期',
    }), { status: 404, headers: CORS_HEADERS });
  } catch (err) {
    return new Response(JSON.stringify({
      error: 'internal_error',
      message: err.message,
    }), { status: 500, headers: CORS_HEADERS });
  }
}
