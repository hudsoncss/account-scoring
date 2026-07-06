"""
Washington State vehicle/vessel dealer license lookup via data.wa.gov Socrata API.
Dataset: Vehicle and Vessel Dealer Licenses with Department of Licensing (4pvz-wrik)
Marine companies appear under "Misc Vehicle Dealer" license type.
Covers 8 WA companies in the dataset.
"""

import requests
import streamlit as st

WA_SOCRATA = "https://data.wa.gov/resource/4pvz-wrik.json"

_EMPTY = {"wa_license_type": None, "wa_license_status": None, "wa_expiration": None}


@st.cache_data(ttl=86400, show_spinner=False)
def get_wa_dealer_data(company_name: str) -> dict:
    """
    Search WA DOL vehicle/vessel dealer registry by company name.
    Returns license type and status if found.
    """
    clean_name = company_name.upper().replace(" LLC", "").replace(" INC", "").strip()

    try:
        resp = requests.get(
            WA_SOCRATA,
            params={
                "$where": f"upper(business_name) like '%{clean_name}%'",
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
                    "wa_license_type":   best.get("license_type"),
                    "wa_license_status": best.get("license_status"),
                    "wa_expiration":     (best.get("expiration_date") or "")[:10],
                }
    except Exception:
        pass
    return _EMPTY.copy()
