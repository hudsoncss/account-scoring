# Account Prioritizer

A Streamlit app that enriches a CSV of prospect companies with data from free public APIs, then scores and ranks them against a configurable Ideal Customer Profile (ICP). Ships with a sample dataset of 250 marine equipment companies as a working example, but the enrichment and scoring logic generalize to any B2B prospect list.

## Try it

> Live demo: <streamlit-cloud-url>

No setup needed — the app loads a sample dataset out of the box and works fully without any API keys.

## How it works

The app is split into two phases:

1. **Enrichment** — runs once per session (on button click) and calls out to public APIs: Google Places (optional, verified location counts), U.S. Census County Business Patterns (employee bands and NAICS industry codes by ZIP), NY/WA state dealer registries, and a static Army Corps of Engineers port-proximity lookup. Takes ~30–60 seconds.
2. **Scoring** — pure computation over the cached enriched data, with no further API calls. Re-runs instantly on every slider or filter change, so adjusting weights doesn't require re-fetching anything.

Every account gets a 0–100 score from five weighted dimensions:

| Dimension | Default weight | Signal |
|---|---|---|
| Multi-location / chain | 35 | Verified branch count (Google Places, with CSV name-dedup fallback) |
| B2B / wholesale orientation | 25 | Name keywords, NAICS code, state dealer license class |
| Size | 20 | Census employee band |
| Port proximity | 12 | Distance to nearest major commercial port |
| NAICS fit | 8 | Census industry code alignment |

Scores normalize to 0–100 and bucket into Tier 1 (≥70), Tier 2 (≥40), or Tier 3. See `DOCUMENTATION.md` for full data-source and scoring rationale.

## Google Places API (optional)

The app works without it — Places-derived signals are simply skipped and the rest of the enrichment/scoring pipeline runs normally.

To enable verified location counts:
1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project (or use an existing one).
2. Enable the **Places API**.
3. Go to **Credentials** → **Create Credentials** → **API key**.
4. Paste the key into the app's sidebar (password-masked input) — no server-side config needed.

Google provides a free monthly credit that comfortably covers light usage. Restrict the key to the Places API in the Google Cloud Console to limit its scope.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Optional: copy `.streamlit/secrets.toml.template` to `.streamlit/secrets.toml` to set `CENSUS_API_KEY` and/or `GOOGLE_PLACES_API_KEY` as environment defaults instead of pasting a Places key into the sidebar each session. Both are optional — the app degrades gracefully without either.

## Project structure

```
app.py                      Streamlit UI, session state, sidebar controls
scoring.py                  Pure scoring logic (no API calls) — five weighted dimensions
enrichment/                 API integrations: Places, Census CBP, NY/WA state registries, dedup logic
data/                       Sample dataset (companies.csv) and static port-proximity lookup
scripts/                    One-off script to regenerate the port-proximity lookup
```
