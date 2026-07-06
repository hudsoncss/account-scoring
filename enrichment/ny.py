"""
New York boat dealer license lookup via data.ny.gov Socrata API.
Dataset: Car, Boat, and Snowmobile Dealerships Across NYS (p9e5-nfyh)
Business type DLB = boat dealer (confirmed).
Covers 9 NY companies in the dataset.
"""

import requests
import streamlit as st

NY_SOCRATA = "https://data.ny.gov/resource/p9e5-nfyh.json"

_EMPTY = {"ny_license_type": None, "ny_license_status": None, "ny_expiration": None}


@st.cache_data(ttl=86400, show_spinner=False)
def get_ny_dealer_data(company_name: str) -> dict:
    """
    Search NY DMV boat dealer registry by company name.
    Returns license type, status, and expiration date if found.
    """
    # Strip common suffixes for better matching
    clean_name = company_name.upper().replace(" LLC", "").replace(" INC", "").replace(" CO.", "").strip()

    try:
        resp = requests.get(
            NY_SOCRATA,
            params={
                "$where": f"upper(facility_name) like '%{clean_name}%' AND business_type='DLB'",
                "$limit": 5,
                "$order": "expiration_date DESC",
            },
            timeout=8,
        )
        if resp.status_code == 200:
            results = resp.json()
            if results:
                best = results[0]
                return {
                    "ny_license_type":   "Boat Dealer (DLB)",
                    "ny_license_status": "Active" if _is_active(best.get("expiration_date", "")) else "Expired",
                    "ny_expiration":     best.get("expiration_date", "")[:10],
                    "ny_city":           best.get("facility_city"),
                }
    except Exception:
        pass
    return _EMPTY.copy()


def _is_active(expiration_str: str) -> bool:
    if not expiration_str:
        return False
    try:
        from datetime import datetime
        exp = datetime.fromisoformat(expiration_str[:10])
        return exp > datetime.now()
    except Exception:
        return False
