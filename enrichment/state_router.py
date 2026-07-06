"""
Routes each company to the appropriate state enrichment module.
States with confirmed working public APIs get dedicated lookups.
All others return an empty dict (graceful degradation).
"""

from enrichment.ny import get_ny_dealer_data
from enrichment.wa import get_wa_dealer_data

_DEDICATED = {"NY", "WA"}


def get_state_enrichment(company_name: str, state: str) -> dict:
    """
    Returns state-specific enrichment dict. Always returns a dict, never raises.
    States without a dedicated module return {}.
    """
    try:
        if state == "NY":
            return get_ny_dealer_data(company_name)
        if state == "WA":
            return get_wa_dealer_data(company_name)
    except Exception:
        pass
    return {}


def has_dedicated_module(state: str) -> bool:
    return state in _DEDICATED
