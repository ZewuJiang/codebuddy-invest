// /api/briefing — 返回最新简报的结构化摘要
// 优先从 KV 读取，KV 不可用时 fallback 到静态 JSON

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
    // 优先从 KV 读取
    if (KV) {
      const summary = await KV.get('summary:latest', { type: 'json' });
      if (summary) {
        return new Response(JSON.stringify(summary), { headers: CORS_HEADERS });
      }
    }

    // KV 不可用或无数据时，fallback 到静态 briefing.json
    const origin = new URL(request.url).origin;
    const res = await fetch(`${origin}/briefing.json`);
    if (res.ok) {
      const data = await res.json();
      return new Response(JSON.stringify(data), { headers: CORS_HEADERS });
    }

    return new Response(JSON.stringify({
      error: 'no_data',
      message: '暂无数据，请先执行数据同步',
    }), { status: 404, headers: CORS_HEADERS });
  } catch (err) {
    return new Response(JSON.stringify({
      error: 'internal_error',
      message: err.message,
    }), { status: 500, headers: CORS_HEADERS });
  }
}
