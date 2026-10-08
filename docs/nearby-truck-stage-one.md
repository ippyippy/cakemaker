# Nearby filters and truck profiles — stage one

This extends the existing FillMeNow app. It is not a second price engine, station directory, account system or truck navigator.

## User controls
Nearby Options → Filters provides value, pump-price, distance and eligible-deal sorting, a straight-line distance range (0–100 km) and verified-deal filters. The map retains the full selected search radius. Filters apply to the comparison list and their summary describes that scope. Reset restores the full list. A distance range never promises that stations are ahead or that a road trip avoids backtracking.

Vehicle Settings retains existing presets, tank/fill and consumption controls. Truck mode adds actual loaded height/width/length/weight and configuration. Height/width/length are metres, loaded combination weight is tonnes. Full length includes trailers. Switching between preset types does not delete previously saved dimensions. Opening settings no longer resets nondefault consumption and saving a truck no longer changes its type to Custom.

Truck navigation is NOT enabled. The standard directions button clearly warns that its map service does not use the saved dimensions. No route is classified truck-safe. Route-aware forward distance, detour entry/exit, axle restrictions, dangerous-goods restrictions and legal access are separate integration work. Do not use radial distance as a substitute.

## Reviewed station catalogue
`web/data/station-information.json` starts EMPTY. Never seed pretend discounts, expired deals or guessed truck clearances. Empty and failed catalogue loads have distinct user-facing messages. All stations remain discoverable by default.

Only maintainers should propose source-backed catalogue records through a reviewed pull request. No support message or public submission automatically becomes a verified measurement or offer. A brand-wide advert is not proof that every franchise participates. All entries use the actual existing provider station ID and state; customer-facing station IDs remain hidden.

### Offers
Required fields: `id`, `state`, `station_id`, `status` (verified), `title`, `terms`, `terms_url` (HTTPS), `starts_at`, `ends_at`, `verified_at` (ISO timestamps), `discount_cpl`, `max_litres`, `minimum_litres`, `eligibility` (everyone or conditions) and `fuels` (actual source grades).

Record all membership, voucher, purchase, payment-method and participating-station conditions in `terms`. Obtain the terms directly from the retailer. The current display requires review within seven days and excludes expired/future offers automatically. Conditional discounts apply only after a separate user confirmation for that offer. An offer fingerprint includes its terms, limits and dates, so changed terms require new confirmation. Fill-volume caps/minimums are enforced. Offers never stack; the largest eligible saving is used. Original pump price is not rewritten. Non-fuel offers and discounts exceeding the supported schema must not be forced into it.

### Truck-access records
Required for a full match: `state`, `station_id`, verified status, `height`, `width`, `length`, `weight` limits, `configurations`, `turning_access_verified`, `source_url`, `verified_at`, `expires_at`. Use documented station-specific limits that cover the approach into the site, lane and usable forecourt, not just a canopy photograph. Attach evidence in the controlled maintainer review, not users' identities. Limit records are not road-route permits.

The current rule permits a match only with all four measured limits, configuration and turning information, a current source (no more than 90 days old and not expired), and 0.1 m additional height/width clearance. This is a conservative UI rule, NOT a universal engineering clearance standard or a guarantee. Partial/old/unknown data is labelled unverified. Any known exceeded limit is labelled nonmatching. The match label explicitly states that the route is not checked. Unverified stations remain visible unless the user deliberately chooses the strict match filter.

## Source-price review safeguard
Source pump prices are retained. Records below 100 or above 500 cents per litre are flagged for review; this is an intentionally conservative product heuristic, not confirmation that a price is erroneous. No value is multiplied or replaced. Review flags prevent use in Best Stop, value savings and browser/native alert selection. A valid alternative diesel grade at the same station is preferred over a flagged grade. Affected stations remain discoverable and display warnings. If all nearby values need review, the app shows the stations but does not fabricate a recommendation.

Investigate and verify outliers with their retailer/provider before making a different source correction. This guard does not independently certify every price inside the range.

## Queensland area search
Use the Queensland Government AdministrativeBoundaries service: Locality layer 2 (`locality`) and Postcode layer 3 (`pc_pid`, example key QLD400031). Numeric searches match `QLD<postcode>%`; locality searches match a sanitised prefix. Project returned polygons to WGS84 and compute the largest ring's centroid. These are approximate labelled search centres, NOT station locations, street-address geocodes or routes. Provider station coordinates stay untouched. Query failures retain the station-reference fallback and otherwise produce an explicit retryable service error rather than claiming no such area exists.

Official service: https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Boundaries/AdministrativeBoundaries/MapServer
Attribution: © State of Queensland.

## Privacy and next integration gates
Truck measurements and per-offer eligibility live in local device storage. They are not attached to support reports or sent to routing services. The typed QLD locality/postcode goes to the official area service. Existing weekly anonymised support review remains in issue #8; do not create another support store.

Before route-aware release: select an authorised provider with Australian heavy-vehicle restriction coverage, confirm costs/quota and retention terms, configure its key privately, model destination plus route entry/exit/detour, handle stale GPS/heading and divided roads, integrate axle/configuration rules, and test real truck routes and stations. User destination and dimension transmission requires corresponding privacy text. No generic API key, trial credential or unrelated project's routing account should be borrowed.
