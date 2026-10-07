# FillMeNow fuel API

## Production release — 8 October 2026 (Australia/Brisbane)

The existing Supabase `fueldrop` function in project `psytztnkeeymavzmpomv` was updated from version 61 to version 62. No replacement function, database migration or subscriber operation was performed.

Version 62 bundles the following immutable source module:

`https://raw.githubusercontent.com/ippyippy/fillmenow/a876bbedde40341c4c5bbfe094d94c7f5ef49328/backend/fueldrop/index.ts`

Deployment entrypoint:

```ts
import "https://raw.githubusercontent.com/ippyippy/fillmenow/a876bbedde40341c4c5bbfe094d94c7f5ef49328/backend/fueldrop/index.ts";
```

This is a static import bundled by the Edge Function deployment, not a mutable branch import or per-request GitHub fetch. Future releases must pin a new tested commit. The `native-push.ts` and `legacy-assets.ts` dependencies are part of the same pinned module graph.

Function metadata after deployment: ACTIVE, version 62, `verify_jwt=false`, ESZip SHA-256 `364e246dd190b4c10d319019aaf338e6c9246b2d78ba31bcc9e9ac045acbb0bd`.

## Behavioural change

`publicPricePayload` rejects failed reads, error-bearing envelopes, and missing/non-array rows. The existing prices route catches these failures and returns HTTP 500 with only `{"ok":false,"rows":[],"error":"price_unavailable"}`. Genuine successful empty results still return HTTP 200. The existing public station-field whitelist is preserved.

The browser already has a retry state for this error. No web source, company-logo asset, Dash artwork, map selection behaviour, native binary or signing configuration changed in this backend release.

## Source organisation

Previously the deployed function was not tracked in this repository. Active backend functions and its existing native notification dependency are now versioned here. The old embedded HTML, icon, manifest and service worker were moved into a separate immutable module; their response bytes, including the standalone export, match the v61 responses. Unused legacy HTML-injection helpers were not carried into the active module. This is therefore a source-organisation change as well as the price-response guard, not a claim that the entire original source file is byte-identical.

The public app continues to be served from `web/` on Vercel. The legacy assets are retained only for compatibility with the older Edge Function routes.

## Verification

GitHub Actions run `37703460345` completed successfully. Run locally with Node supporting `node:module.stripTypeScriptTypes`:

```sh
node tools/backend-route-test.cjs
node tools/polish-backend.cjs backend/fueldrop/index.ts
```

There are 34 full-handler/dependency checks and nine focused guard checks. They exercise the actual source with isolated mocked database responses. They cover the before-fix regression, credential failures, date and price read failures, network/JSON errors, failure after a successful pagination page, real empty results, response-field filtering, geographic parameters, authentication/method guards, native disabled/Off behaviour and byte-level legacy asset compatibility. Tests do not contact a database or send notifications.

After deployment, real read-only queries returned HTTP 200 with rows dated 2026-10-08 for the selected NSW, WA and Tasmania test areas. Web-push configuration remained present; native APNs status remained unconfigured. All five legacy response bodies remained hash-identical. Both primary and AU Vercel URLs continued to serve released HTML Git blob `9a67e475c30e143471398323b83e77a224c2e1bc`; BP, Shell and Caltex logo bytes were unchanged.

## Authentication and release boundaries

`verify_jwt=false` is preserved from version 61 intentionally: fuel-price reads are public, while administrative sync and notification-send routes retain their existing custom credentials checks. No credential values are stored in this repository. Notification signing credentials stay in the server environment.

This release does not certify physical iPhone/Android installation, GPS, actual push delivery or app-store readiness. It does not change other Edge Functions, fuel-feed schedules or table policies. Faults were simulated in isolated tests rather than induced against production.
