const UPSTREAM_BASE = "https://tbh-market.com/api";

const TTL_BY_PATH: Record<string, number> = {
  item: 300,
  items: 300,
  stats: 300,
  filters: 3600,
  rate: 1800,
  movers: 600,
  orderbook: 60,
};

function responseHeaders(ttl: number) {
  return {
    "content-type": "application/json; charset=utf-8",
    "cache-control": `public, max-age=60, s-maxage=${ttl}, stale-while-revalidate=${ttl * 2}`,
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET, OPTIONS",
  };
}

export const onRequest = async (context: {
  request: Request;
  params: { path?: string | string[] };
  waitUntil?: (promise: Promise<unknown>) => void;
}) => {
  const requestUrl = new URL(context.request.url);
  if (context.request.method === "OPTIONS") {
    return new Response(null, { headers: responseHeaders(300) });
  }
  if (context.request.method !== "GET") {
    return new Response(JSON.stringify({ error: "method_not_allowed" }), { status: 405, headers: responseHeaders(300) });
  }

  const rawPath = context.params.path;
  const path = Array.isArray(rawPath) ? rawPath.join("/") : rawPath || "stats";
  const endpoint = path.split("/")[0] || "stats";
  if (!["item", "items", "stats", "filters", "rate", "movers", "orderbook"].includes(endpoint)) {
    return new Response(JSON.stringify({ error: "unknown_market_endpoint" }), { status: 404, headers: responseHeaders(300) });
  }

  const upstream = new URL(`${UPSTREAM_BASE}/${path}`);
  upstream.search = requestUrl.search;
  const ttl = TTL_BY_PATH[endpoint] ?? 300;
  const cache = caches.default;
  const cacheKey = new Request(upstream.toString(), context.request);
  const cached = await cache.match(cacheKey);
  if (cached) {
    return cached;
  }

  const upstreamResponse = await fetch(upstream.toString(), {
    headers: {
      accept: "application/json",
      "user-agent": "TaskBarHeroWiki/1.0 (+https://taskbarhero.wiki)",
    },
    cf: { cacheTtl: ttl, cacheEverything: true },
  });
  const body = await upstreamResponse.text();
  const response = new Response(body, {
    status: upstreamResponse.ok ? 200 : upstreamResponse.status,
    headers: responseHeaders(ttl),
  });
  if (upstreamResponse.ok) {
    context.waitUntil?.(cache.put(cacheKey, response.clone()));
  }
  return response;
};
