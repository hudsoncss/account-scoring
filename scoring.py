"""
Weighted ICP scoring engine. Accepts an enriched DataFrame and a weights dict,
returns the same DataFrame with score, tier, dimension scores, and rationale added.
No API calls — runs instantly on slider change.
"""

import math
import pandas as pd


def _s(val) -> str:
    """Safe string coercion — treats None and NaN (pandas missing) as ''."""
    if val is None:
        return ""
    try:
        if isinstance(val, float) and math.isnan(val):
            return ""
    except Exception:
        pass
    return str(val)


DEFAULT_WEIGHTS = {
    "multi":  35,
    "b2b":    25,
    "size":   20,
    "port":   12,
    "naics":   8,
}

EMP_BAND_SCORE = {
    "1-4":     0.00,
    "5-9":     0.25,
    "10-19":   0.50,
    "20-49":   0.75,
    "50-99":   0.90,
    "100-249": 1.00,
    "250-499": 1.00,
    "500-999": 1.00,
    "1000+":   1.00,
    "N/A":     0.30,   # Suppressed by Census = not the smallest firms
}

# NAICS prefix -> score fraction for pain fit dimension
NAICS_SCORE = {
    "423": 1.00,   # Durable goods wholesale (highest ICP fit)
    "424": 0.90,   # Nondurable goods wholesale
    "336": 0.70,   # Transportation equipment mfg (boat builders/parts)
    "713": 0.55,   # Marinas / amusement, recreation
    "441": 0.35,   # Retail motor vehicle / boat dealers
    "999": 0.40,   # Unknown
}

B2B_KEYWORDS = {
    "wholesale":    1.00,
    "distribut":    1.00,
    "industrial":   0.85,
    "warehouse":    0.80,
    "supply":       0.60,
    "parts":        0.55,
    "equipment":    0.50,
    "hardware":     0.50,
    "commercial":   0.45,
    "marine center":0.40,
}


def _b2b_from_name(name: str) -> float:
    name_l = name.lower()
    best = 0.20  # Baseline: marine industry is B2B-adjacent
    for kw, frac in B2B_KEYWORDS.items():
        if kw in name_l:
            best = max(best, frac)
    return best


def score_company(row: dict, weights: dict) -> dict:
    """Score a single enriched record. Returns dimension scores + total + tier."""

    # --- DIMENSION 1: Multi-location ---
    loc_count = row.get("location_count", 1) or 1
    is_known = row.get("is_known_chain", False)
    oc_branches = row.get("oc_branch_count") or 0

    if loc_count >= 10 or is_known:
        multi_raw = 1.00
    elif loc_count >= 3:
        multi_raw = 0.80
    elif loc_count == 2:
        multi_raw = 0.55
    else:
        multi_raw = 0.14

    # OpenCorporates branch confirmation bonus
    if oc_branches >= 3:
        multi_raw = min(1.0, multi_raw + 0.15)
    elif oc_branches == 2:
        multi_raw = min(1.0, multi_raw + 0.08)

    multi_score = round(multi_raw * weights["multi"])

    # --- DIMENSION 2: B2B / Wholesale ---
    b2b_raw = _b2b_from_name(row.get("Business Name", ""))

    # State API bonus: dealer license class signals wholesale
    license_class = (row.get("fl_license_class") or row.get("tx_dealer_type") or "").lower()
    if "wholesale" in license_class or "distributor" in license_class:
        b2b_raw = min(1.0, b2b_raw + 0.25)
    elif "dealer" in license_class:
        b2b_raw = min(1.0, b2b_raw + 0.10)

    # OpenCorporates entity type bonus
    entity_type = (row.get("entity_type") or "").lower()
    if "llc" in entity_type or "corp" in entity_type:
        b2b_raw = min(1.0, b2b_raw + 0.05)  # Formal entity slightly more B2B

    # NAICS wholesale prefix bonus
    naics = _s(row.get("naics_found"))
    if naics.startswith("423") or naics.startswith("424"):
        b2b_raw = min(1.0, b2b_raw + 0.20)

    b2b_score = round(b2b_raw * weights["b2b"])

    # --- DIMENSION 3: Size Proxy ---
    emp_band = row.get("emp_band") or "N/A"
    size_raw = EMP_BAND_SCORE.get(emp_band, 0.30)

    estab_count = row.get("estab_count") or 0
    if estab_count >= 3:
        size_raw = min(1.0, size_raw + 0.15)
    elif estab_count == 2:
        size_raw = min(1.0, size_raw + 0.08)

    size_score = round(size_raw * weights["size"])

    # --- DIMENSION 4: Port Proximity ---
    port_data = row.get("port_data") or {}
    port_raw = port_data.get("score_fraction", 0.0)
    port_score = round(port_raw * weights["port"])

    # --- DIMENSION 5: NAICS Pain Fit ---
    naics_prefix = naics[:3] if len(naics) >= 3 else "999"  # naics already _s()-coerced above
    naics_raw = NAICS_SCORE.get(naics_prefix, 0.40)
    naics_score = round(naics_raw * weights["naics"])

    # --- TOTAL (normalize to 0-100) ---
    raw_total = multi_score + b2b_score + size_score + port_score + naics_score
    max_possible = sum(weights.values())
    normalized = round((raw_total / max_possible) * 100)

    return {
        "score":       normalized,
        "multi_score": multi_score,
        "b2b_score":   b2b_score,
        "size_score":  size_score,
        "port_score":  port_score,
        "naics_score": naics_score,
        "tier":        _tier(normalized),
    }


def _tier(score: int) -> str:
    if score >= 70: return "Tier 1"
    if score >= 40: return "Tier 2"
    return "Tier 3"


def generate_rationale(row: dict) -> str:
    name = row.get("Business Name", "This company")
    score = row.get("score", 0)
    tier = row.get("tier", "Tier 3")
    tier_num = tier.split()[-1]

    signals = []

    loc = row.get("location_count", 1) or 1
    if row.get("is_known_chain"):
        places_count = row.get("places_location_count") or loc
        signals.append(f"large chain · {places_count}+ locations confirmed via Google Places")
    elif loc >= 3:
        states = row.get("location_states") or []
        states_str = ", ".join(sorted(states)[:3])
        signals.append(f"confirmed chain with {loc} locations across {states_str}")
    elif loc == 2:
        signals.append("multi-location with 2 sites in dataset")

    name_l = _s(row.get("Business Name")).lower()
    naics_found = _s(row.get("naics_found"))
    if "wholesale" in name_l or "distribut" in name_l:
        signals.append("name explicitly signals wholesale/distribution")
    elif naics_found.startswith("423"):
        signals.append(f"Census NAICS {naics_found} = durable goods wholesale")
    elif naics_found.startswith("424"):
        signals.append(f"Census NAICS {naics_found} = nondurable goods wholesale")

    emp = _s(row.get("emp_band"))
    if emp and emp not in ("1-4", "N/A"):
        signals.append(f"Census employee band {emp}")

    port_data = row.get("port_data") or {}
    if not isinstance(port_data, dict):
        port_data = {}
    ports = port_data.get("ports") or []
    dist = port_data.get("distance_miles")
    if ports and dist and dist <= 60:
        signals.append(f"{round(dist)} miles from {ports[0]}")

    lc = (_s(row.get("fl_license_class")) or _s(row.get("tx_dealer_type"))).strip()
    if lc:
        signals.append(f"state license class: {lc}")

    if not signals:
        signals.append("single-location marine operator, limited public data available")

    primary = signals[0]
    secondary = f"; {signals[1]}" if len(signals) > 1 else ""
    tertiary  = f"; {signals[2]}" if len(signals) > 2 else ""

    return (
        f"{name} scores {score}/100 (Tier {tier_num}). "
        f"Key signals: {primary}{secondary}{tertiary}."
    )


def score_all(enriched_df: pd.DataFrame, weights: dict) -> pd.DataFrame:
    """Apply scoring to all rows; returns new DataFrame with score columns appended."""
    records = enriched_df.to_dict("records")
    scored = []
    for row in records:
        s = score_company(row, weights)
        row.update(s)
        row["rationale"] = generate_rationale(row)
        scored.append(row)
    df = pd.DataFrame(scored)
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    return df
