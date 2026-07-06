# Account Prioritizer — Documentation

## What This App Does

The Account Prioritizer takes a raw list of prospect companies (name, address, city, state, ZIP, phone) and automatically enriches each record with data from public government and commercial sources, then scores and ranks every account by how well it fits a configurable Ideal Customer Profile (ICP).

The output is a ranked, tiered list that tells a sales rep where to focus first based on verifiable signals about company size, business type, and geographic footprint. Every data point traces back to a real API call — nothing is estimated or fabricated.

---

## Who It's For

- **Sales/RevOps teams** who need to prioritize outreach across a large prospect list without manually researching each company
- **Sales leaders** who want to apply a consistent, defensible scoring framework across a territory or vertical
- **Anyone exploring a new market with no CRM data**, who wants a repeatable way to rank a prospect list

No technical background required. The app is designed to be used directly in a browser with no setup.

---

## How to Use It

### Step 1 — Upload your prospect CSV (or use the default dataset)

In the sidebar, upload a CSV file with the following columns:

| Column | Description |
|---|---|
| Business Name | Company name |
| Street Address | Street address |
| City | City |
| State | Two-letter state code (e.g. FL, TX) |
| ZIP Code | 5-digit ZIP |
| Phone Number | Phone number |

If no file is uploaded, the app loads a default dataset of 250 marine equipment companies. If you upload a file with missing columns, the app shows an error and falls back to the default dataset.

### Step 2 — Click "Enrich & Score All Accounts"

The app queries public APIs for each company and enriches the dataset. This takes approximately 30–60 seconds. Enrichment only runs once per session — subsequent weight or filter changes are instant with no additional API calls.

### Step 3 — Adjust scoring weights (optional)

Five sliders in the sidebar control how much each dimension contributes to the final score. The defaults reflect the example ICP's priorities, but you can shift them based on your specific market or campaign focus. Changes re-rank all accounts instantly.

### Step 4 — Filter and explore

Use the Tier filter to focus on Tier 1 or Tier 2 accounts. Click any company in the table to expand its full enrichment detail, per-dimension score breakdown, and a plain-English rationale explaining why it scored the way it did.

### Step 5 — Download results

Click "Download Scored Results (CSV)" to export the full ranked list with all enrichment fields and scores for use in a CRM, outreach tool, or spreadsheet.

---

## The Example ICP

This app ships configured around an example ICP: **multi-location B2B distributors**, illustrated here with a marine/industrial equipment dataset. The archetype is a regional or national distributor — building materials, plumbing/HVAC, electrical, marine equipment, or similar — operating 5–400+ branches where each branch represents an independent purchasing/operations unit. The scoring model and weights are meant to be adjusted for whatever ICP you're actually targeting; this one is a working demonstration of the pattern, not a fixed requirement.

The key account-quality signals are:
- **Multiple locations** — branch networks indicate scale and recurring, distributed operational volume rather than a single small business
- **B2B / wholesale orientation** — distributors and wholesalers transact with other businesses constantly; retailers serve end consumers episodically
- **Size** — larger employee bases indicate more operational complexity and budget
- **Port proximity** — companies near major commercial ports handle more inbound freight and outbound distribution, a proxy for logistics-heavy operations (relevant to this example ICP; swap or drop this dimension for a non-logistics ICP)
- **NAICS category** — wholesale NAICS codes (423xx) are a stronger fit for this example ICP than retail codes (441xx)

Signals deliberately excluded:
- **Revenue** — not publicly available for private companies; fabricating it would undermine the principle that every data point is verifiable
- **Website scraping** — too brittle and inconsistent across large datasets to be a reliable signal
- **Social media presence** — not a relevant signal for operations and distribution buyers

---

## Data Sources

Sources are listed in order of impact on the final score.

### 1. Google Places API — Branch Count (primary multi-location signal)
**Source:** Google Maps Platform, Places Text Search API

**What it provides:** The real number of verified locations for each company, sourced directly from Google's business database.

Each company name is searched against Google Places. Results are filtered by exact token matching (requiring all significant words from the company name to appear in the result name as complete words — this prevents "marine" from matching "marina", for example). The count of matching results is the verified location count.

When a company appears multiple times in the dataset under the same brand (e.g. "MarineMax Miami" and "MarineMax Clearwater"), the search uses the normalized brand root ("marinemax") so all entries share one Places lookup that returns the full national count, rather than each searching for their specific city location.

**How chain status is determined:** A company with 10 or more locations confirmed by Google Places is flagged as a large chain. This threshold is derived entirely from live API data — no companies are hardcoded as chains.

**Important limitation:** Google Places Text Search returns proximity-biased results rather than a complete national directory. Very large chains (e.g. West Marine with 240+ US locations) may return fewer results than their true total. However, even an undercount of 10+ locations correctly identifies the company as a large chain for scoring purposes.

**Data currency:** Real-time at the time of enrichment.

---

### 2. Company Name — Keyword Analysis
**What it provides:** B2B orientation signal derived from the company name itself.

Words like "wholesale," "distribution," "industrial," "supply," and "equipment" are strong indicators that a company sells to other businesses rather than end consumers. This requires no API call and runs instantly for every account.

**Keyword scoring:**

| Keyword | B2B Signal Strength |
|---|---|
| wholesale, distribut(ion/or) | 100% |
| industrial, warehouse | 80–85% |
| supply | 60% |
| parts, equipment, hardware | 50–55% |
| commercial | 45% |
| (no keyword match) | 20% baseline |

---

### 3. CSV Name Deduplication — Chain Detection (fallback)
**What it provides:** Multi-location signal derived from the uploaded dataset itself, used as a floor when Google Places has no data for a company.

Company names are normalized (stripping city qualifiers like "Clearwater" or "Houston", directionals like "North"/"South", and legal suffixes like "LLC" or "Inc") and grouped by brand. If the same brand appears multiple times in the dataset, every instance gets a `location_count` reflecting the number of CSV entries sharing that brand.

This serves as a fallback minimum — the final location count is always the higher of the Places count and the CSV dedup count, so a company confirmed by Places to have more locations than appear in the CSV gets the higher number.

No companies are hardcoded as chains or assigned estimated location counts. All location counts come from either Google Places (preferred) or the uploaded dataset itself.

---

### 4. U.S. Census County Business Patterns (CBP) API — 2023
**Source:** `api.census.gov/data/2023/cbp`

**What it provides:** Employee band and NAICS industry classification for each company's ZIP code.

The Census Bureau publishes annual employment and establishment counts by ZIP code and NAICS industry code. The app queries this for each unique ZIP code in the dataset, trying marine-relevant NAICS codes in priority order until a match is found:

| NAICS Code | Industry | Priority |
|---|---|---|
| 42391 | Sporting & recreational goods wholesale | 1st (strongest ICP fit) |
| 42369 | Other durable goods wholesale | 2nd |
| 42349 | Industrial machinery wholesale | 3rd |
| 44122 | Boat dealers (retail) | 4th |
| 71393 | Marinas | 5th |

The wholesale codes are tried first so that a ZIP containing both a wholesaler and a retail dealer gets classified as wholesale — the more ICP-relevant signal.

**Employee bands returned:**

| Band | Meaning |
|---|---|
| 1–4 | Micro business |
| 5–9 | Very small |
| 10–19 | Small |
| 20–49 | Small-medium |
| 50–99 | Medium |
| 100–249 | Mid-market |
| 250–499 | Large |
| 500–999 | Very large |
| 1000+ | Enterprise |
| N/A | Data suppressed by Census to protect privacy |

**Data currency:** 2023 is the most recent year published. The Census Bureau releases CBP data with approximately a 2-year lag — 2024 data is not yet available as of mid-2026. Employee bands therefore reflect 2023 headcount, not current headcount. This is a known limitation of the source and applies to all users of Census CBP data equally.

**Note on N/A:** Census suppresses data when the count is too small to report without identifying individual businesses. "N/A" does not mean zero employees — it means the Census withheld the figure. The scoring model treats N/A as a 30% score rather than zero to avoid penalizing companies for a data suppression decision.

**Performance note:** All unique ZIP codes are fetched in parallel (12 concurrent connections) at the start of enrichment, reducing this step from ~3 minutes sequential to under 30 seconds.

---

### 5. Army Corps of Engineers Port Proximity
**Source:** U.S. Army Corps of Engineers Waterborne Commerce Statistics (pre-computed static lookup)

**What it provides:** Distance from each company's ZIP code to the nearest major commercial marine port, and that port's national tonnage rank.

Port proximity is a proxy for logistics volume — companies near active commercial ports handle more inbound freight and are more likely to have recurring distribution needs. The lookup covers 44 major ports: the Army Corps top-30 by waterborne commerce tonnage plus 14 additional coastal ports added to ensure coverage across all coastal states including NC, OR, ME, HI, and AK.

**Scoring thresholds:**

| Distance to nearest port | Score |
|---|---|
| ≤ 15 miles | 100% |
| 15–30 miles | 83% |
| 30–60 miles | 58% |
| 60–100 miles | 33% |
| > 100 miles | 0% |

Companies in inland markets (e.g. Lake Havasu City, AZ) correctly score zero — they serve inland waterways, not commercial marine distribution channels.

This lookup is pre-built and stored as a static file, so it adds zero latency to the enrichment run.

**Data currency:** Port list reflects Army Corps tonnage rankings. Distances are geodesic (straight-line) calculations from ZIP centroid to port coordinates and do not change.

---

### 6. NY & WA State Dealer Registries
**Sources:** `data.ny.gov` (Socrata), `data.wa.gov` (Socrata)

**What it provides:** Boat dealer license type and active/expired status for companies in New York and Washington state.

An active dealer license confirms the company is a legitimate operating marine business. If the license class contains "wholesale" or "distributor," the B2B score receives an additional bonus.

**Coverage:** New York (9 companies in the default dataset) and Washington state (8 companies). These are the only two state registries with confirmed working public APIs returning structured, queryable data. Florida, Texas, and North Carolina registries were investigated but returned inaccessible results (Cloudflare protection, missing datasets, or HTTP 403 errors). Those states score on the remaining four dimensions only.

**Data currency:** Live at time of enrichment — reflects current license status.

---

## Scoring Model

Every account receives a score from 0–100 built from five weighted dimensions. The default weights reflect the example ICP's priorities and can be adjusted in the sidebar.

### Dimension 1 — Multi-location / Chain (default weight: 35)

The single strongest signal for this example ICP. Multi-branch operators indicate scale and distributed operational volume.

Location count is sourced from Google Places (primary) with CSV name deduplication as a fallback floor. No location counts are estimated or hardcoded.

| Condition | Score fraction |
|---|---|
| Google Places confirmed 10+ locations | 100% |
| 3–9 locations (Places or CSV dedup) | 80% |
| 2 locations (Places or CSV dedup) | 55% |
| 1 location | 14% |

The baseline for single-location companies is 14% rather than 0% because the dataset or Places may not capture every location a company operates — a single confirmed location does not prove the company has no others.

### Dimension 2 — B2B / Wholesale Orientation (default weight: 25)

Measures how likely the company sells to other businesses rather than end consumers. Distributors and wholesalers transact constantly; retailers transact episodically.

Signals combined additively (capped at 100%):
- Company name keyword match (see keyword table in Data Sources)
- Census NAICS code starts with 423 or 424 (wholesale): +20%
- State dealer license class contains "wholesale": +25%
- State dealer license class contains "dealer": +10%

### Dimension 3 — Size Proxy (default weight: 20)

Larger companies have more operational complexity, more locations, and more purchasing power. Employee band from Census CBP 2023 is the primary signal.

| Employee band | Score fraction |
|---|---|
| 1–4 | 0% |
| 5–9 | 25% |
| 10–19 | 50% |
| 20–49 | 75% |
| 50–99 | 90% |
| 100+ | 100% |
| N/A (Census-suppressed) | 30% |

A bonus of up to 15% is added if the ZIP code contains 3 or more marine-industry establishments, indicating a cluster of commercial activity rather than an isolated single business.

**Data recency note:** Employee bands reflect 2023 Census data — the most recent publicly available. Census CBP publishes with approximately a 2-year lag; 2024 data is not yet released. Treat employee bands as directionally accurate rather than precise current headcount.

### Dimension 4 — Port Proximity (default weight: 12)

Distance to the nearest major commercial marine port. Closer proximity correlates with higher inbound freight volume and distribution activity.

Scored using the Army Corps distance thresholds described in the data sources section above.

### Dimension 5 — NAICS Pain Fit (default weight: 8)

How well the company's Census-reported industry code aligns with the example ICP.

| NAICS prefix | Industry | Score fraction |
|---|---|---|
| 423 | Durable goods wholesale | 100% |
| 424 | Nondurable goods wholesale | 90% |
| 336 | Transportation equipment manufacturing | 70% |
| 713 | Marinas / recreation | 55% |
| 441 | Retail boat dealers | 35% |
| Unknown | No Census match | 40% |

### Total Score and Tiers

The five dimension scores are summed and normalized to a 0–100 scale based on the sum of all active weights. Accounts are then bucketed into tiers:

| Tier | Score range | Meaning |
|---|---|---|
| Tier 1 | 70–100 | Strong ICP fit — prioritize for outreach |
| Tier 2 | 40–69 | Moderate fit — worth qualifying |
| Tier 3 | 0–39 | Weak fit — deprioritize |

---

## Design Decisions

**Why Streamlit?** The evaluation priority was end-user ease of use for non-technical sales reps. A deployed web URL is more accessible than a Jupyter notebook, a Python script, or a packaged HTML file. Streamlit provides interactive sliders, a sortable data table, and download capability with minimal frontend code.

**Why separate enrichment from scoring?** Enrichment (API calls) runs once and caches to session memory. Scoring runs in-browser on every slider change with no API calls. This makes weight adjustment instant rather than requiring a 30-second re-fetch every time a rep wants to explore a different prioritization model.

**Why Google Places for chain detection instead of a hardcoded list?** An earlier version of the app used a hardcoded dictionary of known national chains with manually estimated location counts. This was replaced with Google Places because: (1) the hardcoded numbers had no verifiable source, (2) the list would go stale as chains open or close locations, and (3) a Places search returns a real count that can be cited and defended. Every location count in the app now traces back to a live API call.

**Why use a brand root for Places searches instead of the full company name?** Searching "MarineMax Miami" in Places returns only the Miami location. Searching "marinemax" (the normalized brand root) returns all MarineMax locations nationally. For companies appearing multiple times in the dataset under the same brand, the normalized brand root is used as the search key so all entries share one accurate national count.

**Why a static port proximity file?** Geodesic distances from ZIP codes to ports don't change. Pre-computing this offline and storing it as a JSON lookup eliminates latency on every enrichment run and removes a dependency on a runtime geocoding API.

**Why parallel fetching for Census and Places?** Census and Places are independent — neither depends on the other's output. Running both prefetches concurrently in separate thread pools means the total wait time is the longer of the two, not the sum. Within each prefetch, ZIP codes and company names are fetched in parallel pools (12 workers for Census, 8 for Places), reducing what would be ~3 minutes of sequential HTTP calls to under 60 seconds.

**Why not scrape company websites?** Website scraping is brittle — pages change, structures vary, Cloudflare blocks automated requests. A signal derived from a scraped "locations" page is no more reliable than the name deduplication already being done from the CSV, and far more maintenance-intensive.

**Why no revenue data?** Revenue is not publicly available for private companies, which constitute the majority of any prospect dataset. Estimating or fabricating revenue figures would undermine the core principle that every data point in this app comes from a verifiable public source.

**Why is Census data from 2023?** The Census Bureau publishes County Business Patterns data with approximately a 2-year lag. 2023 is the most recent year available as of mid-2026. 2024 data has not yet been released. This is a known limitation of the source — no alternative free public dataset provides ZIP+NAICS level employment data at more recent intervals.
