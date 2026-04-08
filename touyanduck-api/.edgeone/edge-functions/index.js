
      let global = globalThis;
      globalThis.global = globalThis;

      if (typeof global.navigator === 'undefined') {
        global.navigator = {
          userAgent: 'edge-runtime',
          language: 'en-US',
          languages: ['en-US'],
        };
      } else {
        if (typeof global.navigator.language === 'undefined') {
          global.navigator.language = 'en-US';
        }
        if (!global.navigator.languages || global.navigator.languages.length === 0) {
          global.navigator.languages = [global.navigator.language];
        }
        if (typeof global.navigator.userAgent === 'undefined') {
          global.navigator.userAgent = 'edge-runtime';
        }
      }

      class MessageChannel {
        constructor() {
          this.port1 = new MessagePort();
          this.port2 = new MessagePort();
        }
      }
      class MessagePort {
        constructor() {
          this.onmessage = null;
        }
        postMessage(data) {
          if (this.onmessage) {
            setTimeout(() => this.onmessage({ data }), 0);
          }
        }
      }
      global.MessageChannel = MessageChannel;

      // if ((typeof globalThis.fetch === 'undefined' || typeof globalThis.Headers === 'undefined' || typeof globalThis.Request === 'undefined' || typeof globalThis.Response === 'undefined') && typeof require !== 'undefined') {
      //   try {
      //     const undici = require('undici');
      //     if (undici.fetch && !globalThis.fetch) {
      //       globalThis.fetch = undici.fetch;
      //     }
      //     if (undici.Headers && typeof globalThis.Headers === 'undefined') {
      //       globalThis.Headers = undici.Headers;
      //     }
      //     if (undici.Request && typeof globalThis.Request === 'undefined') {
      //       globalThis.Request = undici.Request;
      //     }
      //     if (undici.Response && typeof globalThis.Response === 'undefined') {
      //       globalThis.Response = undici.Response;
      //     }
      //   } catch (polyfillError) {
      //     console.warn('Edge middleware polyfill failed:', polyfillError && polyfillError.message ? polyfillError.message : polyfillError);
      //   }
      // }

      '__MIDDLEWARE_BUNDLE_CODE__'

      function recreateRequest(request, overrides = {}) {
        const cloned = typeof request.clone === 'function' ? request.clone() : request;
        const headers = new Headers(cloned.headers);

        if (overrides.headerPatches) {
          Object.keys(overrides.headerPatches).forEach((key) => {
            const value = overrides.headerPatches[key];
            if (value === null || typeof value === 'undefined') {
              headers.delete(key);
            } else {
              headers.set(key, value);
            }
          });
        }

        if (overrides.headers) {
          const extraHeaders = new Headers(overrides.headers);
          extraHeaders.forEach((value, key) => headers.set(key, value));
        }

        const url = overrides.url || cloned.url;
        const method = overrides.method || cloned.method || 'GET';
        const canHaveBody = method && method.toUpperCase() !== 'GET' && method.toUpperCase() !== 'HEAD';
        const body = overrides.body !== undefined ? overrides.body : canHaveBody ? cloned.body : undefined;

        // 如果rewrite传入的是完整URL（第三方地址），需要更新host
        if (overrides.url) {
          try {
            const newUrl = new URL(overrides.url, cloned.url);
            // 只有当新URL是绝对路径（包含协议和host）时才更新host
            if (overrides.url.startsWith('http://') || overrides.url.startsWith('https://')) {
              headers.set('host', newUrl.host);
            }
            // 相对路径时保持原有host不变
          } catch (e) {
            // URL解析失败时保持原有host
          }
        }

        const init = {
          method,
          headers,
          redirect: cloned.redirect,
          credentials: cloned.credentials,
          cache: cloned.cache,
          mode: cloned.mode,
          referrer: cloned.referrer,
          referrerPolicy: cloned.referrerPolicy,
          integrity: cloned.integrity,
          keepalive: cloned.keepalive,
          signal: cloned.signal,
        };

        if (canHaveBody && body !== undefined) {
          init.body = body;
        }

        if ('duplex' in cloned) {
          init.duplex = cloned.duplex;
        }

        return new Request(url, init);

      }

      
      async function executeMiddleware(context) {
        return null; // 没有中间件，继续执行后续函数
      }
    

      async function handleRequest(context){
        let routeParams = {};
        let pagesFunctionResponse = null;
        let request = context.request;
        const waitUntil = context.waitUntil;
        let urlInfo = new URL(request.url);
        const eo = request.eo || {};

        const normalizePathname = () => {
          if (urlInfo.pathname !== '/' && urlInfo.pathname.endsWith('/')) {
            urlInfo.pathname = urlInfo.pathname.slice(0, -1);
          }
        };

        function getSuffix(pathname = '') {
          // Use a regular expression to extract the file extension from the URL
          const suffix = pathname.match(/.([^.]+)$/);
          // If an extension is found, return it, otherwise return an empty string
          return suffix ? '.' + suffix[1] : null;
        }

        normalizePathname();

        let matchedFunc = false;

        
        const runEdgeFunctions = () => {
          
          if(!matchedFunc && '/api/archive' === urlInfo.pathname) {
            matchedFunc = true;
              (() => {
  // edge-functions/api/archive.js
  var CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };
  async function onRequest({ request, params, env }) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }
    const KV = env.TOUYANDUCK_KV;
    try {
      const url = new URL(request.url);
      const date = url.searchParams.get("date");
      const type = url.searchParams.get("type") || "summary";
      if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
        return new Response(JSON.stringify({
          error: "invalid_date",
          message: "\u8BF7\u63D0\u4F9B\u6709\u6548\u7684\u65E5\u671F\u53C2\u6570\uFF0C\u683C\u5F0F: YYYY-MM-DD",
          example: "/api/archive?date=2026-04-08"
        }), { status: 400, headers: CORS_HEADERS });
      }
      if (KV) {
        if (type === "full") {
          const [briefing, markets, radar, watchlist, md] = await Promise.all([
            KV.get(`briefing:${date}`, { type: "json" }),
            KV.get(`markets:${date}`, { type: "json" }),
            KV.get(`radar:${date}`, { type: "json" }),
            KV.get(`watchlist:${date}`, { type: "json" }),
            KV.get(`md:${date}`, { type: "text" })
          ]);
          if (briefing) {
            return new Response(JSON.stringify({ date, briefing, markets, radar, watchlist, briefingMd: md }), { headers: CORS_HEADERS });
          }
        } else {
          const summary = await KV.get(`summary:${date}`, { type: "json" });
          if (summary) {
            return new Response(JSON.stringify(summary), { headers: CORS_HEADERS });
          }
        }
      }
      const origin = new URL(request.url).origin;
      const metaRes = await fetch(`${origin}/meta.json`);
      if (metaRes.ok) {
        const meta = await metaRes.json();
        const staticDate = meta.date || meta.generatedAt?.split("T")[0];
        if (staticDate === date) {
          if (type === "full") {
            const [bRes2, mRes, rRes, wRes, mdRes] = await Promise.all([
              fetch(`${origin}/briefing.json`),
              fetch(`${origin}/markets.json`),
              fetch(`${origin}/radar.json`),
              fetch(`${origin}/watchlist.json`),
              fetch(`${origin}/briefing.md`)
            ]);
            return new Response(JSON.stringify({
              date,
              briefing: bRes2.ok ? await bRes2.json() : null,
              markets: mRes.ok ? await mRes.json() : null,
              radar: rRes.ok ? await rRes.json() : null,
              watchlist: wRes.ok ? await wRes.json() : null,
              briefingMd: mdRes.ok ? await mdRes.text() : null,
              source: "static-fallback"
            }), { headers: CORS_HEADERS });
          }
          const bRes = await fetch(`${origin}/briefing.json`);
          if (bRes.ok) {
            const data = await bRes.json();
            return new Response(JSON.stringify({ ...data, source: "static-fallback" }), { headers: CORS_HEADERS });
          }
        }
      }
      return new Response(JSON.stringify({
        error: "not_found",
        message: `\u6CA1\u6709\u627E\u5230 ${date} \u7684\u6570\u636E`,
        hint: "\u4F7F\u7528 /api/dates \u67E5\u770B\u6240\u6709\u53EF\u7528\u65E5\u671F"
      }), { status: 404, headers: CORS_HEADERS });
    } catch (err) {
      return new Response(JSON.stringify({
        error: "internal_error",
        message: err.message
      }), { status: 500, headers: CORS_HEADERS });
    }
  }

        pagesFunctionResponse = onRequest;
      })();
          }
        

          if(!matchedFunc && '/api/briefing' === urlInfo.pathname) {
            matchedFunc = true;
              (() => {
  // edge-functions/api/briefing.js
  var CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };
  async function onRequest({ request, params, env }) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }
    const KV = env.TOUYANDUCK_KV;
    try {
      if (KV) {
        const summary = await KV.get("summary:latest", { type: "json" });
        if (summary) {
          return new Response(JSON.stringify(summary), { headers: CORS_HEADERS });
        }
      }
      const origin = new URL(request.url).origin;
      const res = await fetch(`${origin}/briefing.json`);
      if (res.ok) {
        const data = await res.json();
        return new Response(JSON.stringify(data), { headers: CORS_HEADERS });
      }
      return new Response(JSON.stringify({
        error: "no_data",
        message: "\u6682\u65E0\u6570\u636E\uFF0C\u8BF7\u5148\u6267\u884C\u6570\u636E\u540C\u6B65"
      }), { status: 404, headers: CORS_HEADERS });
    } catch (err) {
      return new Response(JSON.stringify({
        error: "internal_error",
        message: err.message
      }), { status: 500, headers: CORS_HEADERS });
    }
  }

        pagesFunctionResponse = onRequest;
      })();
          }
        

          if(!matchedFunc && '/api/dates' === urlInfo.pathname) {
            matchedFunc = true;
              (() => {
  // edge-functions/api/dates.js
  var CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };
  async function onRequest({ request, params, env }) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }
    const KV = env.TOUYANDUCK_KV;
    try {
      if (KV) {
        const index = await KV.get("index:dates", { type: "json" });
        if (index) {
          return new Response(JSON.stringify(index), { headers: CORS_HEADERS });
        }
      }
      const origin = new URL(request.url).origin;
      const res = await fetch(`${origin}/meta.json`);
      if (res.ok) {
        const meta = await res.json();
        return new Response(JSON.stringify({
          dates: [meta.date || meta.generatedAt?.split("T")[0]].filter(Boolean),
          count: 1,
          latest: meta.date,
          source: "static-fallback"
        }), { headers: CORS_HEADERS });
      }
      return new Response(JSON.stringify({
        dates: [],
        count: 0,
        message: "\u6682\u65E0\u5386\u53F2\u6570\u636E"
      }), { headers: CORS_HEADERS });
    } catch (err) {
      return new Response(JSON.stringify({
        error: "internal_error",
        message: err.message
      }), { status: 500, headers: CORS_HEADERS });
    }
  }

        pagesFunctionResponse = onRequest;
      })();
          }
        

          if(!matchedFunc && '/api/predictions' === urlInfo.pathname) {
            matchedFunc = true;
              (() => {
  // edge-functions/api/predictions.js
  var CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };
  async function onRequest({ request, params, env }) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }
    const KV = env.TOUYANDUCK_KV;
    try {
      if (KV) {
        const radar = await KV.get("radar:latest", { type: "json" });
        if (radar) {
          return new Response(JSON.stringify({
            date: radar.date,
            predictions: radar.predictions || [],
            trafficLights: radar.trafficLights || [],
            riskScore: radar.riskScore,
            riskLevel: radar.riskLevel,
            riskAdvice: radar.riskAdvice,
            events: radar.events || []
          }), { headers: CORS_HEADERS });
        }
      }
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
          source: "static-fallback"
        }), { headers: CORS_HEADERS });
      }
      return new Response(JSON.stringify({
        date: null,
        predictions: [],
        trafficLights: [],
        message: "\u6682\u65E0\u9884\u6D4B\u5E02\u573A\u6570\u636E"
      }), { headers: CORS_HEADERS });
    } catch (err) {
      return new Response(JSON.stringify({
        error: "internal_error",
        message: err.message
      }), { status: 500, headers: CORS_HEADERS });
    }
  }

        pagesFunctionResponse = onRequest;
      })();
          }
        

          if(!matchedFunc && '/api/search' === urlInfo.pathname) {
            matchedFunc = true;
              (() => {
  // edge-functions/api/search.js
  var CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };
  async function onRequest({ request, params, env }) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }
    const KV = env.TOUYANDUCK_KV;
    try {
      const url = new URL(request.url);
      const query = url.searchParams.get("q");
      const limit = Math.min(parseInt(url.searchParams.get("limit") || "10", 10), 50);
      if (!query || query.trim().length === 0) {
        return new Response(JSON.stringify({
          error: "missing_query",
          message: "\u8BF7\u63D0\u4F9B\u641C\u7D22\u5173\u952E\u8BCD",
          example: "/api/search?q=NVDA"
        }), { status: 400, headers: CORS_HEADERS });
      }
      const queryLower = query.toLowerCase();
      if (KV) {
        const index = await KV.get("index:dates", { type: "json" });
        if (index && index.dates && index.dates.length > 0) {
          const results = [];
          const searchDates = index.dates.slice(0, 90);
          for (const date of searchDates) {
            if (results.length >= limit)
              break;
            const summary = await KV.get(`summary:${date}`, { type: "json" });
            if (!summary)
              continue;
            const searchFields = [
              summary.coreEvent || "",
              summary.takeaway || "",
              summary.actionSummary || "",
              summary.smartMoneySummary || "",
              JSON.stringify(summary.topMovers || [])
            ].join(" ").toLowerCase();
            if (searchFields.includes(queryLower)) {
              results.push({
                date: summary.date,
                coreEvent: summary.coreEvent,
                takeaway: summary.takeaway,
                sentiment: summary.sentiment,
                risk: summary.risk,
                matchedIn: getMatchedFields(summary, queryLower)
              });
            }
          }
          return new Response(JSON.stringify({ query, count: results.length, results }), { headers: CORS_HEADERS });
        }
      }
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
              coreEvent: briefing.coreEvent?.title || "",
              takeaway: briefing.takeaway || "",
              matched: true
            }],
            source: "static-fallback"
          }), { headers: CORS_HEADERS });
        }
      }
      return new Response(JSON.stringify({
        query,
        results: [],
        count: 0,
        message: "\u6682\u65E0\u5339\u914D\u7ED3\u679C"
      }), { headers: CORS_HEADERS });
    } catch (err) {
      return new Response(JSON.stringify({
        error: "internal_error",
        message: err.message
      }), { status: 500, headers: CORS_HEADERS });
    }
  }
  function getMatchedFields(summary, queryLower) {
    const matched = [];
    if ((summary.coreEvent || "").toLowerCase().includes(queryLower))
      matched.push("coreEvent");
    if ((summary.takeaway || "").toLowerCase().includes(queryLower))
      matched.push("takeaway");
    if ((summary.actionSummary || "").toLowerCase().includes(queryLower))
      matched.push("actionSummary");
    if ((summary.smartMoneySummary || "").toLowerCase().includes(queryLower))
      matched.push("smartMoney");
    if (JSON.stringify(summary.topMovers || []).toLowerCase().includes(queryLower))
      matched.push("topMovers");
    return matched;
  }

        pagesFunctionResponse = onRequest;
      })();
          }
        

          if(!matchedFunc && '/api/smart-money' === urlInfo.pathname) {
            matchedFunc = true;
              (() => {
  // edge-functions/api/smart-money.js
  var CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };
  async function onRequest({ request, params, env }) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }
    const KV = env.TOUYANDUCK_KV;
    const url = new URL(request.url);
    const fund = url.searchParams.get("fund");
    try {
      if (KV) {
        if (fund) {
          const index = await KV.get("index:dates", { type: "json" });
          if (!index || !index.dates || index.dates.length === 0) {
            return new Response(JSON.stringify({ fund, records: [], message: "\u6682\u65E0\u5386\u53F2\u6570\u636E" }), { headers: CORS_HEADERS });
          }
          const records = [];
          const searchDates = index.dates.slice(0, 30);
          for (const date of searchDates) {
            const briefing = await KV.get(`briefing:${date}`, { type: "json" });
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
        const latestBriefing = await KV.get("briefing:latest", { type: "json" });
        if (latestBriefing && latestBriefing.smartMoney) {
          return new Response(JSON.stringify({
            date: latestBriefing.date,
            smartMoney: latestBriefing.smartMoney || [],
            topHoldings: latestBriefing.topHoldings || [],
            smartMoneyDetail: latestBriefing.smartMoneyDetail || [],
            smartMoneyHoldings: latestBriefing.smartMoneyHoldings || []
          }), { headers: CORS_HEADERS });
        }
      }
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
          source: "static-fallback"
        }), { headers: CORS_HEADERS });
      }
      return new Response(JSON.stringify({
        date: null,
        smartMoney: [],
        topHoldings: [],
        message: "\u6682\u65E0\u806A\u660E\u94B1\u6570\u636E"
      }), { headers: CORS_HEADERS });
    } catch (err) {
      return new Response(JSON.stringify({
        error: "internal_error",
        message: err.message
      }), { status: 500, headers: CORS_HEADERS });
    }
  }

        pagesFunctionResponse = onRequest;
      })();
          }
        

          if(!matchedFunc && '/api/sync' === urlInfo.pathname) {
            matchedFunc = true;
              (() => {
  // edge-functions/api/sync.js
  var CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Content-Type": "application/json; charset=utf-8"
  };
  var DEFAULT_TOKEN = "touyanduck-sync-2026";
  async function onRequest({ request, params, env }) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }
    if (request.method !== "POST") {
      return new Response(JSON.stringify({
        error: "method_not_allowed",
        message: "\u8BF7\u4F7F\u7528 POST \u65B9\u6CD5"
      }), { status: 405, headers: CORS_HEADERS });
    }
    const KV = env.TOUYANDUCK_KV;
    if (!KV) {
      return new Response(JSON.stringify({
        error: "kv_not_bound",
        message: "KV \u5B58\u50A8\u672A\u7ED1\u5B9A\uFF0C\u8BF7\u5728 EdgeOne \u63A7\u5236\u53F0\u7ED1\u5B9A TOUYANDUCK_KV \u547D\u540D\u7A7A\u95F4\u540E\u91CD\u65B0\u90E8\u7F72"
      }), { status: 503, headers: CORS_HEADERS });
    }
    const authHeader = request.headers.get("Authorization") || "";
    const token = authHeader.replace("Bearer ", "");
    const expectedToken = env.SYNC_TOKEN || DEFAULT_TOKEN;
    if (token !== expectedToken) {
      return new Response(JSON.stringify({
        error: "unauthorized",
        message: "\u9274\u6743\u5931\u8D25\uFF0C\u8BF7\u63D0\u4F9B\u6B63\u786E\u7684 Authorization: Bearer <token>"
      }), { status: 401, headers: CORS_HEADERS });
    }
    try {
      const payload = await request.json();
      const { date, briefing, markets, radar, watchlist, briefingMd } = payload;
      if (!date || !briefing) {
        return new Response(JSON.stringify({
          error: "invalid_payload",
          message: "\u7F3A\u5C11\u5FC5\u8981\u5B57\u6BB5: date, briefing"
        }), { status: 400, headers: CORS_HEADERS });
      }
      const writeOps = [
        KV.put(`briefing:${date}`, JSON.stringify(briefing)),
        KV.put("briefing:latest", JSON.stringify(briefing))
      ];
      if (markets) {
        writeOps.push(KV.put(`markets:${date}`, JSON.stringify(markets)));
        writeOps.push(KV.put("markets:latest", JSON.stringify(markets)));
      }
      if (radar) {
        writeOps.push(KV.put(`radar:${date}`, JSON.stringify(radar)));
        writeOps.push(KV.put("radar:latest", JSON.stringify(radar)));
      }
      if (watchlist) {
        writeOps.push(KV.put(`watchlist:${date}`, JSON.stringify(watchlist)));
        writeOps.push(KV.put("watchlist:latest", JSON.stringify(watchlist)));
      }
      if (briefingMd) {
        writeOps.push(KV.put(`md:${date}`, briefingMd));
        writeOps.push(KV.put("md:latest", briefingMd));
      }
      const summary = generateSummary(date, briefing, markets, radar);
      writeOps.push(KV.put(`summary:${date}`, JSON.stringify(summary)));
      writeOps.push(KV.put("summary:latest", JSON.stringify(summary)));
      const existingIndex = await KV.get("index:dates", { type: "json" }) || { dates: [], count: 0 };
      if (!existingIndex.dates.includes(date)) {
        existingIndex.dates.unshift(date);
        existingIndex.dates.sort((a, b) => b.localeCompare(a));
      }
      existingIndex.count = existingIndex.dates.length;
      existingIndex.latest = existingIndex.dates[0];
      existingIndex.updatedAt = (/* @__PURE__ */ new Date()).toISOString();
      writeOps.push(KV.put("index:dates", JSON.stringify(existingIndex)));
      const trendOps = await updateTrend(KV, existingIndex.dates);
      writeOps.push(...trendOps);
      await Promise.all(writeOps);
      return new Response(JSON.stringify({
        success: true,
        date,
        message: `${date} \u6570\u636E\u540C\u6B65\u6210\u529F`,
        kvKeysWritten: writeOps.length,
        totalDates: existingIndex.count
      }), { headers: CORS_HEADERS });
    } catch (err) {
      return new Response(JSON.stringify({
        error: "sync_failed",
        message: err.message,
        stack: err.stack
      }), { status: 500, headers: CORS_HEADERS });
    }
  }
  function generateSummary(date, briefing, markets, radar) {
    const summary = {
      date,
      updatedAt: (/* @__PURE__ */ new Date()).toISOString()
    };
    summary.sentiment = {
      score: briefing.sentimentScore || 0,
      label: briefing.sentimentLabel || "\u672A\u77E5"
    };
    summary.coreEvent = briefing.coreEvent?.title || "";
    summary.takeaway = briefing.takeaway || "";
    if (briefing.actionHints && briefing.actionHints.length > 0) {
      summary.actionSummary = briefing.actionHints[0].content || "";
    }
    if (briefing.smartMoney && briefing.smartMoney.length > 0) {
      summary.smartMoneySummary = briefing.smartMoney.slice(0, 3).map((sm) => `${sm.source}: ${sm.action}`).join(" | ");
    }
    summary.topMovers = (briefing.marketSummaryPoints || []).slice(0, 3);
    if (radar) {
      summary.risk = {
        score: radar.riskScore || 0,
        level: radar.riskLevel || "unknown"
      };
      if (radar.trafficLights) {
        const lights = { red: 0, yellow: 0, green: 0 };
        radar.trafficLights.forEach((tl) => {
          if (tl.status === "red")
            lights.red++;
          else if (tl.status === "yellow")
            lights.yellow++;
          else if (tl.status === "green")
            lights.green++;
        });
        summary.trafficLights = lights;
      }
    }
    if (markets && markets.usMarkets) {
      summary.usMarkets = {};
      for (const m of markets.usMarkets) {
        const key = m.name.includes("\u6807\u666E") ? "sp500" : m.name.includes("\u7EB3\u65AF\u8FBE\u514B") ? "nasdaq" : m.name.includes("\u9053\u743C\u65AF") ? "dji" : m.name.includes("VIX") ? "vix" : null;
        if (key) {
          summary.usMarkets[key] = { price: m.price, change: m.change };
        }
      }
      if (markets.commodities) {
        for (const c of markets.commodities) {
          if (c.name.includes("\u5E03\u4F26\u7279")) {
            summary.usMarkets.brent = { price: c.price, change: c.change };
          }
        }
      }
    }
    return summary;
  }
  async function updateTrend(KV, allDates) {
    const ops = [];
    for (const days of [7, 14, 30]) {
      const recentDates = allDates.slice(0, days);
      const dataPoints = [];
      for (const d of recentDates) {
        const s = await KV.get(`summary:${d}`, { type: "json" });
        if (s) {
          dataPoints.push({
            date: s.date,
            sentimentScore: s.sentiment?.score,
            riskScore: s.risk?.score,
            sp500: s.usMarkets?.sp500,
            vix: s.usMarkets?.vix,
            brent: s.usMarkets?.brent,
            coreEvent: s.coreEvent
          });
        }
      }
      ops.push(KV.put(`trend:${days}d`, JSON.stringify({
        days,
        actualDays: dataPoints.length,
        data: dataPoints,
        updatedAt: (/* @__PURE__ */ new Date()).toISOString()
      })));
    }
    return ops;
  }

        pagesFunctionResponse = onRequest;
      })();
          }
        

          if(!matchedFunc && '/api/trend' === urlInfo.pathname) {
            matchedFunc = true;
              (() => {
  // edge-functions/api/trend.js
  var CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json; charset=utf-8"
  };
  async function onRequest({ request, params, env }) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS_HEADERS });
    }
    const KV = env.TOUYANDUCK_KV;
    try {
      const url = new URL(request.url);
      const days = parseInt(url.searchParams.get("days") || "7", 10);
      const validDays = [7, 14, 30].includes(days) ? days : 7;
      if (KV) {
        const trend = await KV.get(`trend:${validDays}d`, { type: "json" });
        if (trend) {
          return new Response(JSON.stringify(trend), { headers: CORS_HEADERS });
        }
        const index = await KV.get("index:dates", { type: "json" });
        if (index && index.dates && index.dates.length > 0) {
          const recentDates = index.dates.slice(0, validDays);
          const dataPoints = [];
          for (const date of recentDates) {
            const summary = await KV.get(`summary:${date}`, { type: "json" });
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
                coreEvent: summary.coreEvent
              });
            }
          }
          return new Response(JSON.stringify({
            days: validDays,
            actualDays: dataPoints.length,
            data: dataPoints
          }), { headers: CORS_HEADERS });
        }
      }
      return new Response(JSON.stringify({
        days: validDays,
        data: [],
        message: "\u8D8B\u52BF\u6570\u636E\u9700\u8981\u591A\u65E5\u79EF\u7D2F\uFF0C\u6682\u65F6\u4EC5\u652F\u6301\u5F53\u5929\u6570\u636E\u67E5\u8BE2",
        source: "static-fallback"
      }), { headers: CORS_HEADERS });
    } catch (err) {
      return new Response(JSON.stringify({
        error: "internal_error",
        message: err.message
      }), { status: 500, headers: CORS_HEADERS });
    }
  }

        pagesFunctionResponse = onRequest;
      })();
          }
        
        };
      

        
        const runMiddleware = typeof executeMiddleware !== 'undefined' ? executeMiddleware : async function() { return null; };
        let middlewareResponseHeaders = null; // 保存中间件设置的响应头
        const middlewareResponse = await runMiddleware({
          request,
          urlInfo: new URL(urlInfo.toString()),
          env: {"NG_CLI_ANALYTICS":"false","NUXT_TELEMETRY_DISABLED":"1","COREPACK_ENABLE_DOWNLOAD_PROMPT":"0","COREPACK_ENABLE_STRICT":"0","YARN_ENABLE_INTERACTIVE":"0","NPM_CONFIG_YES":"true","CI":"true","TMPDIR":"/var/folders/_v/3ng3wcbj0815xxzd2sm145t40000gn/T/"},
          waitUntil
        });

        if (middlewareResponse) {
          const headers = middlewareResponse.headers;
          const hasNext = headers && headers.get('x-middleware-next') === '1';
          const rewriteTarget = headers && headers.get('x-middleware-rewrite');
          const requestHeadersOverride = headers && headers.get('x-middleware-request-headers');
          // Next.js 使用 x-middleware-override-headers 传递需要修改的请求头列表
          const overrideHeadersList = headers && headers.get('x-middleware-override-headers');

          if (rewriteTarget) {
            try {
              const rewrittenUrl = rewriteTarget.startsWith('http://') || rewriteTarget.startsWith('https://')
                ? rewriteTarget
                : new URL(rewriteTarget, urlInfo.origin).toString();
              request = recreateRequest(request, { url: rewrittenUrl });
              urlInfo = new URL(rewrittenUrl);
              normalizePathname();
            } catch (rewriteError) {
              console.error('Middleware rewrite error:', rewriteError);
            }
          }

          // 处理 Next.js 的 x-middleware-override-headers 机制
          if (overrideHeadersList) {
            try {
              const overrideKeys = overrideHeadersList.split(',').map(k => k.trim());
              for (const key of overrideKeys) {
                const newValue = headers.get('x-middleware-request-' + key);
                if (newValue !== null) {
                  request.headers.set(key, newValue);
                } else {
                  request.headers.delete(key);
                }
              }
            } catch (overrideError) {
              console.error('Middleware override headers error:', overrideError);
            }
          }
          // 处理旧的 x-middleware-request-headers 机制（兼容）
          else if (requestHeadersOverride) {
            try {
              const decoded = decodeURIComponent(requestHeadersOverride);
              const headerPatch = JSON.parse(decoded);
              Object.keys(headerPatch).forEach((key) => {
                const value = headerPatch[key];
                if (value === null || typeof value === 'undefined') {
                  request.headers.delete(key);
                } else {
                  request.headers.set(key, value);
                }
              });
            } catch (requestPatchError) {
              console.error('Middleware request header override error:', requestPatchError);
            }
          }

          if (!hasNext && !rewriteTarget) {
            return middlewareResponse;
          }

          if (hasNext) {
            middlewareResponseHeaders = new Headers();
            const skipHeaders = new Set([
              'x-middleware-next',
              'x-middleware-rewrite',
              'x-middleware-request-headers',
              'x-middleware-override-headers',
              'x-middleware-set-cookie',
              'date',
              'connection',
              'content-length',
              'content-encoding', // 避免中间件传递的压缩头覆盖到最终响应，破坏流式响应
              'transfer-encoding',
              'set-cookie', // Set-Cookie 需要特殊处理，避免重复
            ]);
            headers.forEach((value, key) => {
              const lowerKey = key.toLowerCase();
              // 过滤内部使用的 header：skipHeaders 中的 + x-middleware-request-* 前缀的请求头修改标记
              if (!skipHeaders.has(lowerKey) && !lowerKey.startsWith('x-middleware-request-')) {
                middlewareResponseHeaders.set(key, value);
              }
            });
            // 特殊处理 Set-Cookie，可能有多个，使用 getSetCookie 获取完整的 cookie 值
            const setCookies = headers.getSetCookie ? headers.getSetCookie() : [];
            setCookies.forEach(cookie => {
              middlewareResponseHeaders.append('Set-Cookie', cookie);
            });
          }
        }
      
        
        // 走到这里说明：
        // 1. 没有中间件响应（middlewareResponse 为 null/undefined）
        // 2. 或者中间件返回了 next
        // 需要判断是否命中边缘函数

        runEdgeFunctions();

        //没有命中边缘函数，执行回源
        if (!matchedFunc) {
          // 允许压缩的文件后缀白名单
          const ALLOW_COMPRESS_SUFFIXES = [
            '.html', '.htm', '.xml', '.txt', '.text', '.conf', '.def', '.list', '.log', '.in',
            '.css', '.js', '.json', '.rss', '.svg', '.tif', '.tiff', '.rtx', '.htc',
            '.java', '.md', '.markdown', '.ico', '.pl', '.pm', '.cgi', '.pb', '.proto',
            '.xhtml', '.xht', '.ttf', '.otf', '.woff', '.eot', '.wasm', '.binast', '.webmanifest'
          ];
          
          // 检查请求路径是否有允许压缩的后缀
          const pathname = urlInfo.pathname;
          const suffix = getSuffix(pathname);
          const hasCompressibleSuffix = ALLOW_COMPRESS_SUFFIXES.includes(suffix);
          
          // 如果不是可压缩的文件类型，删除 Accept-Encoding 头以禁用 CDN 压缩
          if (!hasCompressibleSuffix) {
              request.headers.delete('accept-encoding');
          }
          
          const originResponse = await fetch(request);
          
          // 如果中间件设置了响应头，合并到回源响应中
          if (middlewareResponseHeaders) {
            const mergedHeaders = new Headers(originResponse.headers);
            // 删除可能导致问题的编码相关头
            mergedHeaders.delete('content-encoding');
            mergedHeaders.delete('content-length');
            middlewareResponseHeaders.forEach((value, key) => {
              if (key.toLowerCase() === 'set-cookie') {
                mergedHeaders.append(key, value);
              } else {
                mergedHeaders.set(key, value);
              }
            });
            return new Response(originResponse.body, {
              status: originResponse.status,
              statusText: originResponse.statusText,
              headers: mergedHeaders,
            });
          }
          
          return originResponse;
        }
        
        // 命中了边缘函数，继续执行边缘函数逻辑

        const params = {};
        if (routeParams.id) {
          if (routeParams.mode === 1) {
            const value = urlInfo.pathname.match(routeParams.left);        
            for (let i = 1; i < value.length; i++) {
              params[routeParams.id[i - 1]] = value[i];
            }
          } else {
            const value = urlInfo.pathname.replace(routeParams.left, '');
            const splitedValue = value.split('/');
            if (splitedValue.length === 1) {
              params[routeParams.id] = splitedValue[0];
            } else {
              params[routeParams.id] = splitedValue;
            }
          }
          
        }
        const edgeFunctionResponse = await pagesFunctionResponse({request, params, env: {"NG_CLI_ANALYTICS":"false","NUXT_TELEMETRY_DISABLED":"1","COREPACK_ENABLE_DOWNLOAD_PROMPT":"0","COREPACK_ENABLE_STRICT":"0","YARN_ENABLE_INTERACTIVE":"0","NPM_CONFIG_YES":"true","CI":"true","TMPDIR":"/var/folders/_v/3ng3wcbj0815xxzd2sm145t40000gn/T/"}, waitUntil, eo });
        
        // 如果中间件设置了响应头，合并到边缘函数响应中
        if (middlewareResponseHeaders && edgeFunctionResponse) {
          const mergedHeaders = new Headers(edgeFunctionResponse.headers);
          // 删除可能导致问题的编码相关头
          mergedHeaders.delete('content-encoding');
          mergedHeaders.delete('content-length');
          middlewareResponseHeaders.forEach((value, key) => {
            if (key.toLowerCase() === 'set-cookie') {
              mergedHeaders.append(key, value);
            } else {
              mergedHeaders.set(key, value);
            }
          });
          return new Response(edgeFunctionResponse.body, {
            status: edgeFunctionResponse.status,
            statusText: edgeFunctionResponse.statusText,
            headers: mergedHeaders,
          });
        }
        
        return edgeFunctionResponse;
      }
      addEventListener('fetch', event=>{return event.respondWith(handleRequest({request:event.request,params: {}, env: {"NG_CLI_ANALYTICS":"false","NUXT_TELEMETRY_DISABLED":"1","COREPACK_ENABLE_DOWNLOAD_PROMPT":"0","COREPACK_ENABLE_STRICT":"0","YARN_ENABLE_INTERACTIVE":"0","NPM_CONFIG_YES":"true","CI":"true","TMPDIR":"/var/folders/_v/3ng3wcbj0815xxzd2sm145t40000gn/T/"}, waitUntil: event.waitUntil.bind(event) }))});