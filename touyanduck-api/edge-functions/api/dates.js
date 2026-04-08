// /api/dates — 返回所有可用的历史数据日期列表

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
    if (KV) {
      const index = await KV.get('index:dates', { type: 'json' });
      if (index) {
        return new Response(JSON.stringify(index), { headers: CORS_HEADERS });
      }
    }

    // fallback: 从 meta.json 获取日期
    const origin = new URL(request.url).origin;
    const res = await fetch(`${origin}/meta.json`);
    if (res.ok) {
      const meta = await res.json();
      return new Response(JSON.stringify({
        dates: [meta.date || meta.generatedAt?.split('T')[0]].filter(Boolean),
        count: 1,
        latest: meta.date,
        source: 'static-fallback',
      }), { headers: CORS_HEADERS });
    }

    return new Response(JSON.stringify({
      dates: [],
      count: 0,
      message: '暂无历史数据',
    }), { headers: CORS_HEADERS });
  } catch (err) {
    return new Response(JSON.stringify({
      error: 'internal_error',
      message: err.message,
    }), { status: 500, headers: CORS_HEADERS });
  }
}
