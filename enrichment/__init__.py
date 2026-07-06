"""
Batch enrichment runner. Call run_enrichment_batch() once per session;
result is stored in st.session_state to avoid repeat API calls.
"""

import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from enrichment.deduplication import detect_chains
from enrichment.census import fetch_cbp_raw
from enrichment.places import get_places_data
from enrichment.state_router import get_state_enrichment

_EMPTY_CENSUS = {"emp_band": "N/A", "estab_count": 0, "naics_found": None, "naics_label": None}
_EMPTY_PLACES = {"places_location_count": 0, "places_states": [], "places_confirmed": False, "places_error": "API key not loaded"}


def _prefetch_census(zips: list, api_key: str) -> dict:
    """Fetch Census data for all unique ZIPs in parallel (12 workers)."""
    results = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        future_to_zip = {ex.submit(fetch_cbp_raw, z, api_key): z for z in zips}
        for future in as_completed(future_to_zip):
            z = future_to_zip[future]
            try:
                results[z] = future.result()
            except Exception:
                results[z] = _EMPTY_CENSUS.copy()
    return results


def _prefetch_places(search_names: list, api_key: str) -> dict:
    """Fetch Google Places data for unique search names in parallel (8 workers)."""
    if not api_key:
        return {}
    results = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        future_to_name = {ex.submit(get_places_data, n, api_key): n for n in search_names}
        for future in as_completed(future_to_name):
            n = future_to_name[future]
            try:
                results[n] = future.result()
            except Exception:
                results[n] = _EMPTY_PLACES.copy()
    return results


def _load_port_lookup() -> dict:
    try:
        with open("data/port_zip_lookup.json") as f:
            return json.load(f)
    except Exception:
        return {}


def run_enrichment_batch(
    df: pd.DataFrame,
    census_api_key: str = "",
    places_api_key: str = "",
    progress_callback=None,
) -> pd.DataFrame:
    """
    Enriches all rows in df. Designed to run once and be cached in session_state.

    progress_callback: callable(fraction: float, text: str) — updates a progress bar.
    Returns a new DataFrame with enrichment columns appended.
    """
    total = len(df)
    warnings = []

    # Step 1: Chain detection (instant, no API)
    chain_data = detect_chains(df)

    # Step 2: Load static port proximity table
    port_lookup = _load_port_lookup()

    # Step 3: Build Places search keys.
    # When a brand appears multiple times in the CSV, chain_group is the normalized
    # brand root (e.g. "marinemax"). Searching by that finds all chain locations
    # rather than just the one specific city entry.
    # Single-entry companies (chain_group=None) search by their full name.
    def _places_key(name):
        cg = chain_data.get(name, {}).get("chain_group")
        return cg if cg else name

    unique_zips         = df["ZIP Code"].apply(lambda z: str(z).strip().zfill(5)).unique().tolist()
    unique_places_keys  = list({_places_key(str(n).strip()) for n in df["Business Name"]})

    if progress_callback:
        progress_callback(0.02,
            f"Fetching Census ({len(unique_zips)} ZIPs) and "
            f"Places ({len(unique_places_keys)} brands) in parallel…")

    with ThreadPoolExecutor(max_workers=2) as outer:
        census_future = outer.submit(_prefetch_census, unique_zips, census_api_key)
        places_future = outer.submit(_prefetch_places, unique_places_keys, places_api_key)

    census_cache = census_future.result()
    places_cache = places_future.result()

    enriched_rows = []

    for i, (_, row) in enumerate(df.iterrows()):
        name    = str(row["Business Name"]).strip()
        state   = str(row["State"]).strip()
        zip_raw = str(row["ZIP Code"]).strip().zfill(5)

        record = row.to_dict()

        # Chain detection from CSV (baseline)
        csv_chain = chain_data.get(name, {
            "chain_group":     None,
            "location_count":  1,
            "location_states": [state],
            "chain_members":   [],
            "is_known_chain":  False,
        })
        record.update(csv_chain)

        # Google Places — authoritative location count and chain flag
        # Look up by brand root (chain_group) so all MarineMax entries share one result
        pk = _places_key(name)
        places = places_cache.get(pk, _EMPTY_PLACES.copy())
        record.update(places)
        if places["places_confirmed"]:
            record["location_count"] = max(
                places["places_location_count"],
                csv_chain.get("location_count", 1),
            )
            # is_known_chain: Places verified 10+ locations = confirmed large chain
            record["is_known_chain"] = places["places_location_count"] >= 10
            csv_states = set(csv_chain.get("location_states") or [state])
            record["location_states"] = sorted(csv_states | set(places["places_states"]))

        # Census CBP — pre-fetched in parallel above, now a dict lookup
        record.update(census_cache.get(zip_raw, _EMPTY_CENSUS.copy()))

        # Port proximity (static dict lookup — instant)
        record["port_data"] = port_lookup.get(zip_raw, {
            "score_fraction": 0.0, "ports": [], "distance_miles": None
        })

        # State enrichment (NY and WA have real APIs; others return {})
        try:
            state_data = get_state_enrichment(name, state)
            record.update(state_data)
        except Exception as e:
            warnings.append(f"State enrichment failed for {name}: {e}")

        enriched_rows.append(record)

        if progress_callback:
            pct = 0.02 + 0.98 * (i + 1) / total
            label = f"Processing {i + 1}/{total}: {name[:45]}…"
            progress_callback(pct, label)

    result_df = pd.DataFrame(enriched_rows)
    result_df.attrs["enrichment_warnings"] = warnings
    return result_df
