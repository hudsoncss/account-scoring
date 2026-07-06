"""
Google Places API enrichment — real branch count lookup.
Replaces CSV-only chain detection as the authoritative multi-location signal.
API: maps.googleapis.com/maps/api/place/textsearch/json
"""

import re
import time
import requests
import streamlit as st

PLACES_BASE = "https://maps.googleapis.com/maps/api/place/textsearch/json"

# Noise words stripped before name comparison
_STOP = {"inc", "llc", "co", "corp", "ltd", "the", "and", "of", "group", "company"}

# Hard cap on pages fetched — each page = 1 API call (~$0.032)
MAX_PAGES = 3  # Up to 60 results; enough for any chain in this dataset


def _tokens(name: str) -> set:
    """Lowercase word tokens with noise words removed."""
    words = re.sub(r"[^a-z0-9\s]", "", name.lower()).split()
    return {w for w in words if w not in _STOP and len(w) > 1}


def _name_matches(search_name: str, result_name: str) -> bool:
    """
    True if all significant words in search_name appear as exact tokens in
    result_name. Exact token match prevents "marine" matching "marina".
    """
    s_tokens = _tokens(search_name)
    r_tokens = _tokens(result_name)
    if not s_tokens:
        return False
    return s_tokens.issubset(r_tokens)


@st.cache_data(ttl=86400, show_spinner=False)
def get_places_data(company_name: str, api_key: str) -> dict:
    """
    Search Google Places for company_name (no state — we want national chain count).
    Filters results by exact token match to avoid unrelated businesses.
    Returns:
      places_location_count  — number of name-matched locations found
      places_states          — unique states those locations are in
      places_confirmed       — True if at least one result matched
    """
    if not api_key:
        return _empty("No API key configured")

    all_results = []
    next_page_token = None

    for _ in range(MAX_PAGES):
        if next_page_token:
            params = {"pagetoken": next_page_token, "key": api_key}
            time.sleep(3)  # Google requires a short delay before next_page_token
        else:
            params = {
                "query": company_name,
                "key": api_key,
                "type": "establishment",
                "region": "us",
                "location": "39.8283,-98.5795",  # geographic center of US — overrides server IP geolocation
                "radius": "50000",
            }

        try:
            resp = requests.get(PLACES_BASE, params=params, timeout=10)
            if resp.status_code != 200:
                if next_page_token:
                    break  # first page succeeded — use what we have
                return _empty(f"HTTP {resp.status_code}")
            data = resp.json()
            status = data.get("status")
            if status == "ZERO_RESULTS":
                break
            if status not in ("OK", "ZERO_RESULTS"):
                if next_page_token:
                    break  # pagetoken expired/invalid — use first page results
                return _empty(f"API status: {status} — {data.get('error_message', '')}")
            all_results.extend(data.get("results", []))
            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break
        except Exception as e:
            if next_page_token:
                break
            return _empty(f"Exception: {e}")

    # Filter to results whose name contains all significant words from our query
    matched = [r for r in all_results if _name_matches(company_name, r.get("name", ""))]

    if not matched:
        return _empty()

    # Extract state abbreviation from formatted_address (e.g. "..., Tampa, FL 33607, USA")
    states_found = set()
    for r in matched:
        addr = r.get("formatted_address", "")
        # Address format: "Street, City, ST ZIPCODE, USA"
        parts = addr.replace(", USA", "").split(", ")
        if len(parts) >= 2:
            state_zip = parts[-1].strip()
            state_part = state_zip.split(" ")[0]
            if len(state_part) == 2 and state_part.isalpha():
                states_found.add(state_part.upper())

    return {
        "places_location_count": len(matched),
        "places_states":         sorted(states_found),
        "places_confirmed":      True,
        "places_error":          None,
    }


def _empty(error: str = None) -> dict:
    return {
        "places_location_count": 0,
        "places_states":         [],
        "places_confirmed":      False,
        "places_error":          error,
    }
