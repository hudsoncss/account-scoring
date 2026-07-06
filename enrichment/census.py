"""
Census County Business Patterns API enrichment.
Covers all 249 records — the universal enrichment layer.
API: api.census.gov/data/2022/cbp
"""

import time
import requests
import streamlit as st

CBP_BASE = "https://api.census.gov/data/2023/cbp"

# NAICS codes tried in priority order — wholesale before retail
# so wholesalers get the more accurate NAICS tag.
MARINE_NAICS = [
    "42391",  # Sporting & recreational goods wholesale
    "42369",  # Other durable goods wholesale
    "42349",  # Industrial machinery wholesale
    "44122",  # Boat dealers (retail)
    "71393",  # Marinas
]

# CBP EMPSZES codes -> human-readable band (3-digit codes used by 2019+ API)
EMP_BAND_MAP = {
    "210": "1-4",
    "220": "5-9",
    "230": "10-19",
    "241": "20-49",
    "242": "50-99",
    "251": "100-249",
    "252": "250-499",
    "254": "500-999",
    "260": "1000+",
}

_EMPTY = {"emp_band": "N/A", "estab_count": 0, "naics_found": None, "naics_label": None}


def fetch_cbp_raw(zip_code: str, api_key: str = "") -> dict:
    """
    Core Census CBP fetch — no caching. Used directly by the parallel prefetch
    in run_enrichment_batch. Tries marine NAICS codes in priority order.
    """
    key_param = f"&key={api_key}" if api_key else ""
    zip_clean = str(zip_code).strip().zfill(5)

    for naics in MARINE_NAICS:
        url = (
            f"{CBP_BASE}?get=EMPSZES,ESTAB,NAICS2017_LABEL"
            f"&for=zip+code:{zip_clean}&NAICS2017={naics}{key_param}"
        )
        try:
            resp = requests.get(url, timeout=8, allow_redirects=False)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1:
                    # Row 0 = header; remaining rows are one per size band.
                    # "001" = total across all sizes; other codes = specific bands.
                    rows = data[1:]
                    total_row = next((r for r in rows if r[0] == "001"), None)
                    size_rows = [r for r in rows if r[0] != "001"]

                    estab_count = 0
                    if total_row:
                        try:
                            estab_count = int(total_row[1])
                        except (ValueError, TypeError):
                            pass

                    # Largest size band = last row (rows arrive in ascending order)
                    if size_rows:
                        top = size_rows[-1]
                        emp_band    = EMP_BAND_MAP.get(str(top[0]), "N/A")
                        naics_label = top[2] if len(top) > 2 else None
                    else:
                        emp_band    = "N/A"
                        naics_label = total_row[2] if total_row and len(total_row) > 2 else None

                    return {
                        "emp_band":    emp_band,
                        "estab_count": estab_count,
                        "naics_found": naics,
                        "naics_label": naics_label,
                    }
        except Exception:
            pass
        time.sleep(0.05)

    return _EMPTY.copy()


@st.cache_data(ttl=86400, show_spinner=False)
def get_cbp_data(zip_code: str, api_key: str = "") -> dict:
    """Cached wrapper around fetch_cbp_raw — used for single lookups."""
    return fetch_cbp_raw(zip_code, api_key)
