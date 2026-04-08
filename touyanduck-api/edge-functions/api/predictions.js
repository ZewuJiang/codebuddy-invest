// /api/predictions — 返回最新的预测市场数据（Polymarket / CME FedWatch）

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
      const radar = await KV.get('radar:latest', { type: 'json' });
      if (radar) {
        return new Response(JSON.stringify({
          date: radar.date,
          predictions: radar.predictions || [],
          trafficLights: radar.trafficLights || [],
          riskScore: radar.riskScore,
          riskLevel: radar.riskLevel,
          riskAdvice: radar.riskAdvice,
          events: radar.events || [],
        }), { headers: CORS_HEADERS });
      }
    }

    // fallback: 从静态 radar.json 读取
    const origin = new URL(request.url).origin;
    const res = await fetch(`${origin}/radar.json`);
    if (res.ok) {
      const radar = await res.json();
      return new Response(JSON.stringify({
        date: radar.date,
        predictions: radar.predictions || [],
        trafficLights: radar.trafficLights || [],
        riskScore: radar.riskScore,
        riskLevel: radar.riskLevel,
        riskAdvice: radar.riskAdvice,
        events: radar.events || [],
        source: 'static-fallback',
      }), { headers: CORS_HEADERS });
    }

    return new Response(JSON.stringify({
      date: null,
      predictions: [],
      trafficLights: [],
      message: '暂无预测市场数据',
    }), { headers: CORS_HEADERS });
  } catch (err) {
    return new Response(JSON.stringify({
      error: 'internal_error',
      message: err.message,
    }), { status: 500, headers: CORS_HEADERS });
  }
}
