// Native iOS alerts share the existing fuel feeds and cron routes. Apple keys stay on the server.
type Dependencies = {
  base: () => string;
  headers: () => Record<string, string>;
  fuelRows: (fuel: string, state: string) => Promise<any>;
  rank: (rows: any[], lat: number, lng: number, radius: number, tank: number, economy: number) => any;
};

const table = "/rest/v1/native_push_subscriptions";
const bundleID = "au.com.fillmenow.app";
const encoder = new TextEncoder();
const frequencies = new Set(["off", "daily", "weekdays", "twice_daily", "price_drop_only"]);
const fuels = new Set(["Diesel", "U91", "E10", "U95", "U98"]);
const signingCache = new Map<string, { token: string; issued: number }>();
let appleClient: Deno.HttpClient | null = null;

function appleConfig(environment = "production") {
  return {
    keyID: Deno.env.get(environment === "sandbox" ? "APNS_SANDBOX_KEY_ID" : "APNS_KEY_ID") || "",
    teamID: Deno.env.get("APNS_TEAM_ID") || "",
    privateKey: Deno.env.get(environment === "sandbox" ? "APNS_SANDBOX_PRIVATE_KEY" : "APNS_PRIVATE_KEY") || "",
  };
}

export function nativePushConfigured(environment = "production") {
  const config = appleConfig(environment);
  return Deno.env.get("APNS_ENABLED") === "true" &&
    /^[A-Z0-9]{10}$/.test(config.keyID) && /^[A-Z0-9]{10}$/.test(config.teamID) && !!config.privateKey;
}

function numeric(v: any, min: number, max: number) {
  return typeof v === "number" && Number.isFinite(v) && v >= min && v <= max;
}

export function nativeSettings(body: any) {
  if (!numeric(body?.latitude, -90, 90) || !numeric(body?.longitude, -180, 180) ||
      !["NSW", "WA", "TAS"].includes(body?.state_code) || !fuels.has(body?.fuel_type) ||
      !frequencies.has(body?.notification_frequency) ||
      !numeric(body?.radius_km, 1, 100) || !numeric(body?.tank_litres, 20, 1500) ||
      !numeric(body?.economy_l_per_100km, 2, 80)) return null;
  const hm = /^(?:[01]\d|2[0-3]):[0-5]\d$/;
  if (!hm.test(body?.notify_time || "") || !hm.test(body?.notify_time_2 || "")) return null;
  const off = body.notification_frequency === "off";
  const threshold = off || body.price_drop_threshold == null ? null : body.price_drop_threshold;
  if (threshold !== null && !numeric(threshold, 1, 1000)) return null;
  if (body.notification_frequency === "price_drop_only" && threshold === null) return null;
  return {
    latitude: body.latitude, longitude: body.longitude, state_code: body.state_code,
    location_label: String(body.location_label || "").trim().slice(0, 120),
    fuel_type: body.fuel_type, radius_km: body.radius_km,
    tank_litres: body.tank_litres, economy_l_per_100km: body.economy_l_per_100km,
    notification_frequency: body.notification_frequency,
    notify_time: body.notify_time, notify_time_2: body.notify_time_2,
    price_drop_threshold: threshold, active: !off,
  };
}

async function identity(body: any) {
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(body?.installation_id || "") ||
      !/^[0-9a-f]{64}$/.test(body?.installation_secret || "")) return null;
  const hash = await crypto.subtle.digest("SHA-256", encoder.encode(body.installation_secret));
  return { id: body.installation_id, installation_secret_hash: Array.from(new Uint8Array(hash), n => n.toString(16).padStart(2, "0")).join("") };
}

async function database(deps: Dependencies, query: string, method = "GET", body?: any) {
  const response = await fetch(deps.base() + table + query, {
    method, headers: { ...deps.headers(), "content-type": "application/json", prefer: "return=representation" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }), signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) throw new Error("native_subscription_store_failed");
  return response.status === 204 ? [] : await response.json();
}

export async function nativePushAPI(api: string, request: Request, deps: Dependencies) {
  if (api === "native-push-status") return { status: 200, body: { ok: true, configured: nativePushConfigured(new URL(request.url).searchParams.get("environment") === "sandbox" ? "sandbox" : "production") } };
  if (api !== "native-subscribe" && api !== "native-unsubscribe") return null;
  if (request.method !== "POST") return { status: 405, body: { ok: false, error: "method_not_allowed" } };
  try {
    const body = await request.json(), owner = await identity(body);
    if (!owner) return { status: 400, body: { ok: false, error: "invalid_installation" } };
    const settings = api === "native-subscribe" ? nativeSettings(body) : null;
    if (api === "native-subscribe" && (!settings || !/^(?:[0-9a-f]{2}){16,512}$/.test(body.device_token || "") ||
        !["sandbox", "production"].includes(body.apns_environment))) {
      return { status: 400, body: { ok: false, error: "invalid_alert_settings" } };
    }
    const query = "?id=eq." + owner.id;
    const current = await database(deps, query + "&select=id,installation_secret_hash&limit=1");
    if (current[0] && current[0].installation_secret_hash !== owner.installation_secret_hash) {
      return { status: 401, body: { ok: false, error: "unauthorized_installation" } };
    }
    if (api === "native-unsubscribe") {
      if (current[0]) await database(deps, query + "&installation_secret_hash=eq." + owner.installation_secret_hash, "DELETE");
      return { status: 200, body: { ok: true } };
    }
    if (!nativePushConfigured(body.apns_environment)) return { status: 503, body: { ok: false, error: "notifications_unavailable" } };
    await appleProviderToken(body.apns_environment); // Reject an invalid signing key before accepting a subscription.
    const row = { ...settings, ...owner, device_token: body.device_token, apns_environment: body.apns_environment,
      updated_at: new Date().toISOString(), failure_count: 0, last_error: null };
    const saved = await database(deps, current[0] ? query + "&installation_secret_hash=eq." + owner.installation_secret_hash : "", current[0] ? "PATCH" : "POST", row);
    if (!saved.length) throw new Error("native_subscription_store_failed");
    return { status: 200, body: { ok: true, active: row.active } };
  } catch {
    return { status: 503, body: { ok: false, error: "alert_save_unavailable" } };
  }
}

function base64url(bytes: Uint8Array) {
  return btoa(String.fromCharCode(...bytes)).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

export async function appleProviderToken(environment = "production") {
  const now = Math.floor(Date.now() / 1000);
  const cached = signingCache.get(environment);
  if (cached && now >= cached.issued && now - cached.issued < 3000) return cached.token;
  if (!nativePushConfigured(environment)) throw new Error("native_push_not_configured");
  const config = appleConfig(environment);
  const pem = config.privateKey.replace(/\\n/g, "\n");
  const der = Uint8Array.from(atob(pem.replace(/-----[^-]+-----|\s/g, "")), c => c.charCodeAt(0));
  const key = await crypto.subtle.importKey("pkcs8", der, { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
  const header = base64url(encoder.encode(JSON.stringify({ alg: "ES256", kid: config.keyID })));
  const claims = base64url(encoder.encode(JSON.stringify({ iss: config.teamID, iat: now })));
  const unsigned = header + "." + claims;
  const signature = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, key, encoder.encode(unsigned));
  const token = unsigned + "." + base64url(new Uint8Array(signature));
  signingCache.set(environment, { token, issued: now });
  return token;
}

export async function sendApplePush(sub: any, payload: any, collapseID: string) {
  const providerToken = await appleProviderToken(sub.apns_environment);
  if (!appleClient) appleClient = Deno.createHttpClient({ http1: false, http2: true });
  const host = sub.apns_environment === "sandbox" ? "api.sandbox.push.apple.com" : "api.push.apple.com";
  const message = JSON.stringify({ aps: { alert: { title: payload.title, body: payload.body }, sound: "default" }, fillmenow: payload.data });
  if (encoder.encode(message).byteLength > 4096) throw new Error("native_push_payload_too_large");
  const response = await fetch("https://" + host + "/3/device/" + sub.device_token, {
    method: "POST", client: appleClient, signal: AbortSignal.timeout(15000),
    headers: { authorization: "bearer " + providerToken, "apns-topic": bundleID, "apns-push-type": "alert",
      "apns-priority": "10", "apns-expiration": String(Math.floor(Date.now() / 1000) + 10800),
      "apns-collapse-id": collapseID, "content-type": "application/json" }, body: message,
  });
  if (response.status === 200) return { accepted: true, gone: false };
  const error = await response.json().catch(() => ({}));
  // A bad provider credential is an operator issue; it must not disable the installation.
  const gone = response.status === 410 || (response.status === 400 && ["BadDeviceToken", "DeviceTokenNotForTopic"].includes(error.reason));
  if (error.reason === "ExpiredProviderToken") signingCache.delete(sub.apns_environment);
  return { accepted: false, gone, reason: String(error.reason || "APNsRejected").slice(0, 120) };
}

function localParts(state: string, now: Date) {
  const tz = state === "WA" ? "Australia/Perth" : state === "TAS" ? "Australia/Hobart" : "Australia/Sydney";
  const parts = new Intl.DateTimeFormat("en-AU", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", weekday: "short", hourCycle: "h23" }).formatToParts(now);
  const get = (name: string) => parts.find(p => p.type === name)?.value || "";
  return { day: get("year") + "-" + get("month") + "-" + get("day"), hm: get("hour") + ":" + get("minute"), weekday: get("weekday") };
}

function due(now: string, target: string) {
  const minutes = (v: string) => Number(v.slice(0, 2)) * 60 + Number(v.slice(3, 5));
  // Do not wrap midnight: an evening alert must not turn into tomorrow's morning alert.
  const delta = minutes(now) - minutes(target);
  return delta >= 0 && delta < 16;
}

export function nativeDailyKey(sub: any, now: Date) {
  const local = localParts(sub.state_code, now);
  if (!sub.active || sub.notification_frequency === "off" || sub.notification_frequency === "price_drop_only" ||
      (sub.notification_frequency === "weekdays" && ["Sat", "Sun"].includes(local.weekday))) return null;
  const slot = due(local.hm, sub.notify_time) ? sub.notify_time :
    sub.notification_frequency === "twice_daily" && due(local.hm, sub.notify_time_2) ? sub.notify_time_2 : null;
  return slot ? local.day + "|" + slot : null;
}

async function subscriptions(deps: Dependencies) {
  const result: any[] = [];
  for (let offset = 0; offset < 100000; offset += 1000) {
    const page = await database(deps, "?active=eq.true&order=id.asc&limit=1000&offset=" + offset);
    result.push(...page);
    if (page.length < 1000) break;
  }
  return result;
}

export async function sendNativePushes(kind: "daily" | "price_drop", deps: Dependencies, now = new Date()) {
  const subs = await subscriptions(deps);
  const result = { ok: true, configured: nativePushConfigured() || nativePushConfigured("sandbox"), subscriptions: subs.length, accepted: 0, skipped: 0, failed: 0, gone: 0 };
  if (!subs.length) return result;
  if (!result.configured) return { ...result, ok: false, failed: subs.length };
  const cache = new Map<string, any>();
  for (const sub of subs) {
    if (!nativePushConfigured(sub.apns_environment)) { result.failed++; continue; }
    const dailyKey = kind === "daily" ? nativeDailyKey(sub, now) : null;
    if (!sub.active || sub.notification_frequency === "off" ||
        (kind === "daily" && (!dailyKey || dailyKey === sub.last_daily_key)) ||
        (kind === "price_drop" && !(Number(sub.price_drop_threshold) > 0))) { result.skipped++; continue; }
    try {
      const cacheKey = sub.state_code + "|" + sub.fuel_type;
      if (!cache.has(cacheKey)) cache.set(cacheKey, await deps.fuelRows(sub.fuel_type, sub.state_code));
      const snapshot = cache.get(cacheKey), day = localParts(sub.state_code, now).day;
      if (!snapshot?.rows?.length || snapshot.price_date !== day) { result.skipped++; continue; }
      const ranking = deps.rank(snapshot.rows, sub.latitude, sub.longitude, sub.radius_km, sub.tank_litres, sub.economy_l_per_100km);
      const best = kind === "daily" ? ranking.bestValue : ranking.cheapest;
      if (!best) { result.skipped++; continue; }
      const price = Number(best.price), dropKey = day + "|" + price.toFixed(1);
      if (kind === "price_drop" && (price > sub.price_drop_threshold ||
          (sub.last_drop_key?.startsWith(day + "|") && price >= Number(sub.last_drop_key.split("|")[1]) - 0.01))) { result.skipped++; continue; }
      const field = kind === "daily" ? "last_daily_key" : "last_drop_key", key = kind === "daily" ? dailyKey : dropKey;
      const prior = sub[field], condition = prior == null ? "is.null" : "eq." + encodeURIComponent(prior);
      const deviceQuery = "?id=eq." + sub.id + "&device_token=eq." + sub.device_token;
      const claimed = await database(deps, deviceQuery + "&active=eq.true&updated_at=eq." + encodeURIComponent(sub.updated_at) + "&" + field + "=" + condition, "PATCH", { [field]: key });
      if (!claimed.length) { result.skipped++; continue; }
      const payload = {
        title: kind === "daily" ? "FillMeNow · Best value near you" : "FillMeNow price alert · " + price.toFixed(1) + "¢/" + sub.fuel_type,
        body: String(best.station_name || "Fuel station").slice(0, 60) + " · " + price.toFixed(1) + "¢ · " + Number(best.distance_km).toFixed(1) + " km away",
        data: { screen: "explore", state: sub.state_code, fuel: sub.fuel_type, station_id: best.station_id },
      };
      let sent: { accepted: boolean; gone: boolean; reason?: string };
      try { sent = await sendApplePush(sub, payload, kind === "daily" ? "fillmenow-daily" : "fillmenow-price-drop"); }
      catch { sent = { accepted: false, gone: false, reason: "APNsRequestFailed" }; }
      if (!sent.accepted) {
        if (sent.gone) result.gone++;
        await database(deps, deviceQuery + "&" + field + "=eq." + encodeURIComponent(key!), "PATCH", {
          [field]: prior ?? null, ...(sent.gone ? { active: false } : {}),
          failure_count: (sub.failure_count || 0) + 1, last_error: sent.reason,
        });
        result.failed++;
      } else {
        result.accepted++;
        // Keep the claimed key after Apple accepts. An audit write failure must not resend the alert.
        await database(deps, deviceQuery, "PATCH", { last_accepted_at: now.toISOString(), failure_count: 0, last_error: null });
      }
    } catch { result.failed++; }
  }
  result.ok = result.failed === 0;
  return result;
}

export async function mergePushRuns(web: () => Promise<any>, native: () => Promise<any>) {
  const runs = await Promise.allSettled([web(), native()]);
  const value = (run: PromiseSettledResult<any>) => run.status === "fulfilled" ? run.value : { ok: false, subscriptions: 0, sent: 0, failed: 1, error: "notification_run_failed" };
  const browser = value(runs[0]), ios = value(runs[1]);
  return { ...browser, ok: browser.ok && ios.ok, native: ios };
}
