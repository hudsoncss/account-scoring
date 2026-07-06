import streamlit as st
import pandas as pd
import json

from enrichment import run_enrichment_batch
from scoring import score_all, DEFAULT_WEIGHTS


# ─── Custom theme CSS (mirrors hudsonrevops.com design system) ─────────────────

_CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@700;800&family=Lexend+Deca:wght@300;400;600&display=swap');

/* ── Base typography ── */
html, body, [class*="css"] {
    font-family: 'Lexend Deca', sans-serif;
    color: #32444f;
}

[data-testid="stAppViewContainer"] {
    background-color: #f7f7f4;
}

[data-testid="stHeader"] {
    background-color: rgba(0,0,0,0);
}

h1, h2, h3, h4,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
    font-family: 'Archivo', sans-serif;
    color: #0e1f2b;
}

h1, h2,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2 {
    font-weight: 800;
    letter-spacing: -0.02em;
}

a, [data-testid="stMarkdownContainer"] a {
    color: #0d7377;
}

/* ── Eyebrow label ── */
.hrops-eyebrow {
    text-transform: uppercase;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #0d7377;
    font-family: 'Lexend Deca', sans-serif;
    margin-bottom: 0.25rem;
    display: block;
}

/* ── Sidebar: dark section with dot-grid texture ── */
[data-testid="stSidebar"] {
    background-color: #14222e;
    background-image: radial-gradient(rgba(46,230,207,0.1) 1px, transparent 1px);
    background-size: 24px 24px;
}

[data-testid="stSidebar"] * {
    color: #b8c5cf;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4 {
    font-family: 'Archivo', sans-serif;
    color: #ffffff;
}

[data-testid="stSidebar"] a {
    color: #2ee6cf;
}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] small {
    color: #8fa2ac;
}

[data-testid="stSidebar"] hr {
    border-color: #2a3d4c;
}

/* Widget labels (slider, selectbox, multiselect, text_input, file_uploader) */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #b8c5cf !important;
    font-weight: 600;
}

/* Text inputs / password inputs */
[data-testid="stSidebar"] input[type="text"],
[data-testid="stSidebar"] input[type="password"] {
    background-color: #1b2c3a;
    border: 1px solid #2a3d4c;
    color: #e8eef2;
}

[data-testid="stSidebar"] [data-baseweb="input"] {
    background-color: #1b2c3a;
    border-radius: 6px;
}

[data-testid="stSidebar"] [data-baseweb="base-input"] {
    background-color: #1b2c3a;
}

/* Selectbox / multiselect (BaseWeb) */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #1b2c3a;
    border-color: #2a3d4c;
    color: #e8eef2;
}

[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: #0d7377;
}

/* Sliders — spark cyan accent */
[data-testid="stSidebar"] [data-baseweb="slider"] div[role="slider"] {
    background-color: #2ee6cf;
    border-color: #2ee6cf;
}

[data-testid="stSidebar"] [data-testid="stSlider"] [data-baseweb="slider"] > div > div {
    background: #2ee6cf;
}

/* Expander */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background-color: #1b2c3a;
    border: 1px solid #2a3d4c;
    border-radius: 8px;
}

[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    color: #e8eef2;
}

/* File uploader dropzone */
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background-color: #1b2c3a;
    border: 1px dashed #2a3d4c;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
    color: #b8c5cf !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
    background-color: #0d7377;
    color: #ffffff;
    border: 1px solid rgba(46,230,207,0.6);
}

/* Alerts inside sidebar (success/error/info) keep readable text */
[data-testid="stSidebar"] [data-testid="stAlertContentSuccess"],
[data-testid="stSidebar"] [data-testid="stAlertContentInfo"],
[data-testid="stSidebar"] [data-testid="stAlertContentError"],
[data-testid="stSidebar"] [data-testid="stAlertContentWarning"] {
    color: #e8eef2;
}

/* ── Buttons: signature teal glow ── */
.stButton > button,
[data-testid="stDownloadButton"] > button,
[data-testid="baseButton-primary"] {
    background-color: #0d7377;
    color: #ffffff;
    border: 1px solid rgba(46,230,207,0.6);
    border-radius: 8px;
    font-family: 'Archivo', sans-serif;
    font-weight: 700;
    box-shadow: 0 0 14px -6px rgba(46,230,207,0.7);
    transition: all 0.15s ease-in-out;
}

.stButton > button:hover,
[data-testid="stDownloadButton"] > button:hover {
    background-color: #0a8f86;
    color: #ffffff;
    box-shadow: 0 0 22px -6px rgba(46,230,207,0.9);
    border-color: rgba(46,230,207,0.9);
}

/* ── Main-area cards: dataframe / expander / metric containers ── */
[data-testid="stDataFrame"],
[data-testid="stExpander"] {
    background-color: #ffffff;
    border: 1px solid #dde2da;
    border-radius: 12px;
    box-shadow: 0 2px 8px -4px rgba(14,31,43,0.08);
}

[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #dde2da;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 2px 8px -4px rgba(14,31,43,0.08);
}

[data-testid="stMetricValue"] {
    color: #0e1f2b;
    font-family: 'Archivo', sans-serif;
    font-weight: 800;
}

[data-testid="stMetricLabel"] {
    color: #5d6f78;
    text-transform: uppercase;
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    font-weight: 700;
}

/* ── Tabs ── */
[data-testid="stTabs"] button[data-baseweb="tab"] {
    color: #5d6f78;
    font-family: 'Archivo', sans-serif;
    font-weight: 700;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: #0d7377;
    border-bottom-color: #0d7377;
}

/* ── Dividers ── */
[data-testid="stMainBlockContainer"] hr {
    border-color: #dde2da;
}
</style>
"""


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _chain_label(row) -> str:
    loc = int(row.get("location_count") or 1)
    is_known = bool(row.get("is_known_chain"))
    source = "(Places)" if row.get("places_confirmed") else "(CSV)"
    if is_known:
        return f"Large chain · {loc}+ locations {source}"
    if loc >= 3:
        states = row.get("location_states") or []
        return f"Chain · {loc} sites {source} ({', '.join(sorted(states)[:3])})"
    if loc == 2:
        return f"Multi-location · 2 sites {source}"
    return "Single location"


def _port_label(port_data) -> str:
    if not isinstance(port_data, dict):
        return "—"
    ports = port_data.get("ports") or []
    dist  = port_data.get("distance_miles")
    if ports and dist is not None:
        return f"{ports[0]} ({round(dist)}mi)"
    return "—"


REQUIRED_COLS = ["Business Name", "Street Address", "City", "State", "ZIP Code", "Phone Number"]

@st.cache_data
def _load_default() -> pd.DataFrame:
    return pd.read_csv("data/companies.csv", dtype=str)


def _get_census_key() -> str:
    try:
        return str(st.secrets["CENSUS_API_KEY"]).strip()
    except Exception:
        return ""


def _get_places_key() -> str:
    try:
        return str(st.secrets["GOOGLE_PLACES_API_KEY"]).strip()
    except Exception:
        return ""


# ─── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Account Prioritizer",
    page_icon="⚓",
    layout="wide",
)

st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)

# ─── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Account Prioritizer")
    st.divider()

    # ── Dataset source ──
    st.subheader("Dataset")
    uploaded = st.file_uploader(
        "Upload prospect CSV",
        type="csv",
        help="Required columns: " + ", ".join(REQUIRED_COLS),
    )

    _upload_error = None
    if uploaded is not None:
        try:
            raw_df = pd.read_csv(uploaded, dtype=str)
            missing = set(REQUIRED_COLS) - set(raw_df.columns)
            if missing:
                _upload_error = f"Missing columns: {', '.join(sorted(missing))}"
                raw_df = _load_default()
        except Exception as e:
            _upload_error = f"Could not parse CSV: {e}"
            raw_df = _load_default()
    else:
        raw_df = _load_default()

    # Clear enrichment whenever the data source changes
    _data_source = uploaded.name if uploaded else "__default__"
    if _data_source != st.session_state.get("_data_source"):
        st.session_state.pop("enriched_df", None)
        st.session_state.pop("enrichment_warnings", None)
        st.session_state["_data_source"] = _data_source

    if _upload_error:
        st.error(_upload_error)
    elif uploaded is not None:
        st.success(f"{len(raw_df)} accounts from **{uploaded.name}**")
    else:
        st.caption(f"Default dataset · {len(raw_df)} marine accounts")

    st.divider()

    st.subheader("Google Places API Key")
    st.caption(
        "Used to confirm multi-location / chain signal. Optional — the app runs fully "
        "without it, just without the Places-based location count."
    )
    _user_places_key = st.text_input(
        "Google Places API key (optional)",
        type="password",
        help="Paste your own key to use it for this session instead of the app's default key.",
    )
    _default_places_key = _get_places_key()
    if _user_places_key.strip():
        places_key = _user_places_key.strip()
        _places_key_source = "your key"
    elif _default_places_key:
        places_key = _default_places_key
        _places_key_source = "app default"
    else:
        places_key = ""
        _places_key_source = "not configured"

    census_key = _get_census_key()
    _places_status = {
        "your key":        "using your key",
        "app default":     "using app default",
        "not configured":  "not configured — Places data skipped",
    }[_places_key_source]
    st.caption(
        f"Census key: {'✓ loaded' if census_key else '✗ missing'} · "
        f"Places key: {_places_status}"
    )

    with st.expander("How to get a free Google Places API key"):
        st.markdown(
            "1. Create a project at [console.cloud.google.com](https://console.cloud.google.com)\n"
            "2. Enable the **Places API**\n"
            "3. Go to **Credentials** → **Create API key**\n"
            "4. Paste the key above\n\n"
            "Google's free monthly credit typically covers usage for this app."
        )

    st.divider()

    st.subheader("Scoring Weights")
    st.caption("Adjust weights to re-rank instantly — no API calls needed.")

    w_multi = st.slider("Multi-location / Chain",    0, 50, DEFAULT_WEIGHTS["multi"])
    w_b2b   = st.slider("B2B / Wholesale Signal",    0, 40, DEFAULT_WEIGHTS["b2b"])
    w_size  = st.slider("Size Proxy (Census)",        0, 30, DEFAULT_WEIGHTS["size"])
    w_port  = st.slider("Port Proximity (Delivery)",  0, 20, DEFAULT_WEIGHTS["port"])
    w_naics = st.slider("NAICS Pain Fit",             0, 15, DEFAULT_WEIGHTS["naics"])

    weights = {"multi": w_multi, "b2b": w_b2b, "size": w_size,
               "port": w_port,   "naics": w_naics}

    st.divider()
    st.subheader("Filters")
    all_states = sorted(raw_df["State"].dropna().unique().tolist())
    state_filter = st.multiselect("State", options=all_states, default=all_states)
    tier_filter  = st.multiselect("Tier",  options=["Tier 1", "Tier 2", "Tier 3"],
                                  default=["Tier 1", "Tier 2", "Tier 3"])

    st.divider()
    st.caption(
        "**Data sources:** Google Places (branch count) · "
        "Census County Business Patterns 2023 (employee bands, NAICS — most recent available; "
        "Census publishes with ~2 year lag) · "
        "Army Corps port tonnage (delivery proximity) · "
        "NY & WA state dealer registries · CSV name deduplication (chain detection)"
    )

# ─── Main content ──────────────────────────────────────────────────────────────

_dataset_label = uploaded.name if uploaded is not None else "(default dataset)"
st.markdown('<span class="hrops-eyebrow">Account Scoring &amp; Prioritization</span>', unsafe_allow_html=True)
st.title("Account Prioritizer")
st.markdown(
    f"Enriches prospects from *{_dataset_label}* then ranks by fit to a configurable "
    "Ideal Customer Profile (ICP).  "
    "Adjust scoring weights or filters in the sidebar to see results update instantly."
)

tab_main, tab_guide = st.tabs(["Prioritizer", "User Guide"])

with tab_main:
    enriched_df  = st.session_state.get("enriched_df")

    # ─── Enrich button ─────────────────────────────────────────────────────────────

    btn_col, status_col = st.columns([2, 5])

    with btn_col:
        btn_label = "Re-enrich Accounts" if enriched_df is not None else "Enrich & Score All Accounts"
        run_clicked = st.button(btn_label, type="primary", width='stretch')

    with status_col:
        if enriched_df is not None:
            st.success(f"Enrichment complete — {len(enriched_df)} accounts loaded. Adjust weights or filters to re-rank instantly.")
        else:
            st.info(f"Click **Enrich & Score All Accounts** to run the enrichment pipeline (~30–60 seconds for {len(raw_df)} records). Employee bands reflect 2023 Census data — the most recent publicly available.")

    if run_clicked:
        bar = st.progress(0, text="Starting…")
        with st.spinner("Enriching via Census CBP, port proximity, and state registries…"):
            result = run_enrichment_batch(
                raw_df,
                census_api_key=census_key,
                places_api_key=places_key,
                progress_callback=lambda f, t: bar.progress(f, text=t),
            )
        st.session_state["enriched_df"] = result
        st.session_state["enrichment_warnings"] = result.attrs.get("enrichment_warnings", [])
        enriched_df = result
        bar.empty()
        st.rerun()

    # ─── Score + display ───────────────────────────────────────────────────────────

    if enriched_df is not None:

        scored_df = score_all(enriched_df, weights)

        # Filters
        if state_filter:
            scored_df = scored_df[scored_df["State"].isin(state_filter)]
        if tier_filter:
            scored_df = scored_df[scored_df["tier"].isin(tier_filter)]

        # ── Metric cards ──
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accounts Shown",    len(scored_df))
        c2.metric("Tier 1 (High ICP)", len(scored_df[scored_df["tier"] == "Tier 1"]))
        c3.metric("Tier 2 (Mid ICP)",  len(scored_df[scored_df["tier"] == "Tier 2"]))
        avg = scored_df["score"].mean() if len(scored_df) else 0
        c4.metric("Avg ICP Score",     f"{avg:.0f} / 100")

        st.divider()

        # ── Build display table ──
        table_df = scored_df.copy()
        table_df["Chain Signal"]  = table_df.apply(_chain_label, axis=1)
        table_df["Nearest Port"]  = table_df["port_data"].apply(_port_label)

        show = table_df[[
            "Business Name", "City", "State",
            "score", "tier",
            "Chain Signal", "emp_band", "naics_label", "Nearest Port",
        ]].rename(columns={
            "score":      "ICP Score",
            "tier":       "Tier",
            "emp_band":   "Employees (Census)",
            "naics_label":"NAICS Category",
        })

        st.dataframe(
            show,
            column_config={
                "ICP Score": st.column_config.ProgressColumn(
                    "ICP Score", min_value=0, max_value=100, format="%d",
                ),
                "Tier":                st.column_config.TextColumn("Tier",       width="small"),
                "Business Name":       st.column_config.TextColumn("Company",    width="large"),
                "City":                st.column_config.TextColumn("City",       width="medium"),
                "State":               st.column_config.TextColumn("State",      width="small"),
                "Chain Signal":        st.column_config.TextColumn("Chain",      width="medium"),
                "Employees (Census)":  st.column_config.TextColumn("Employees",  width="small"),
                "NAICS Category":      st.column_config.TextColumn("NAICS",      width="large"),
                "Nearest Port":        st.column_config.TextColumn("Port (Army Corps)", width="large"),
            },
            width='stretch',
            hide_index=True,
            height=520,
        )

        # ── Download ──
        drop_cols = ["port_data", "chain_members", "location_states"]
        export_df = scored_df.drop(columns=drop_cols, errors="ignore")
        st.download_button(
            "Download Scored Results (CSV)",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="scored_accounts.csv",
            mime="text/csv",
        )

        # ── Account detail ──
        st.divider()
        st.subheader("Account Detail")
        selected = st.selectbox("Select account to inspect:", scored_df["Business Name"].tolist())

        if selected:
            row = scored_df[scored_df["Business Name"] == selected].iloc[0].to_dict()
            tier_icon = {"Tier 1": "🟢", "Tier 2": "🟡", "Tier 3": "🔴"}.get(row.get("tier", ""), "⚪")

            with st.expander(
                f"{tier_icon} {selected}  —  {row.get('tier')} · {row.get('score')}/100",
                expanded=True,
            ):
                left, right = st.columns(2)

                port_d = row.get("port_data") or {}

                with left:
                    st.markdown("**Enrichment Data**")
                    places_confirmed = row.get("places_confirmed", False)
                    places_loc = row.get("places_location_count")
                    places_err = row.get("places_error")
                    places_display = places_loc if places_confirmed else (places_err or "N/A")
                    st.json({
                        "Location count (Places)":  places_display,
                        "Location count (CSV dedup)":row.get("location_count", 1),
                        "Large chain (Places ≥10)":  row.get("is_known_chain", False),
                        "Places states":             row.get("places_states") or "N/A",
                        "Employee band":             row.get("emp_band") or "N/A",
                        "Establishments (ZIP)":      row.get("estab_count") or "N/A",
                        "NAICS code":                row.get("naics_found") or "N/A",
                        "NAICS label":               row.get("naics_label") or "N/A",
                        "Nearest port":              (port_d.get("ports") or ["N/A"])[0],
                        "Port distance (mi)":        port_d.get("distance_miles") or "N/A",
                        "Army Corps rank":           port_d.get("army_corps_rank") or "N/A",
                        "NY license status":         row.get("ny_license_status") or "—",
                        "WA license status":         row.get("wa_license_status") or "—",
                    })

                with right:
                    st.markdown("**Score Breakdown**")
                    breakdown = pd.DataFrame({
                        "Dimension":  ["Multi-location", "B2B/Wholesale", "Size Proxy",
                                       "Port Proximity", "NAICS Fit"],
                        "Score":      [row.get("multi_score", 0), row.get("b2b_score", 0),
                                       row.get("size_score", 0),  row.get("port_score", 0),
                                       row.get("naics_score", 0)],
                        "Max Weight": [w_multi, w_b2b, w_size, w_port, w_naics],
                    })
                    st.dataframe(breakdown, hide_index=True, width='stretch')

                    st.markdown("**Rationale**")
                    st.info(row.get("rationale", "No rationale generated."))

        # ── Non-blocking warnings ──
        warnings = st.session_state.get("enrichment_warnings", [])
        if warnings:
            with st.expander(f"Enrichment notes ({len(warnings)})"):
                for w in warnings:
                    st.caption(f"• {w}")

    else:
        # Pre-enrichment: show raw data
        st.subheader(f"Source Data ({len(raw_df)} accounts)")
        st.dataframe(raw_df, width='stretch', hide_index=True, height=400)
        st.caption("Click **Enrich & Score All Accounts** above to add Census, port proximity, and state registry data.")

with tab_guide:
    st.markdown("""
## What you're looking at

This app takes a list of prospect companies and turns it into a ranked, prioritized
call list. Upload a CSV (or use the built-in sample), click one button to enrich every
company with public data, and the app scores each one from **0 to 100** based on how
well it fits an Ideal Customer Profile (ICP) — then ranks and tiers the whole list so
you know exactly who to call first.

Nothing here is estimated or guessed. Every signal used in scoring traces back to a
real, live public data source — Google Places, U.S. Census County Business Patterns,
Army Corps of Engineers port tonnage data, and state dealer registries.
""")

    st.markdown("""
## The example ICP

The app ships configured around a working example ICP: **multi-location B2B marine /
industrial distributors**. Think regional or national distributor networks —
5 to 400+ branch locations, each one an independent purchasing and operations unit.
You can retarget the weights below to a completely different ICP; this one is a
demonstration of the pattern, not a fixed requirement.

Why each signal indicates fit for *this* example ICP:

- **Multiple locations** — a branch network means scale and recurring, distributed
  operational volume, not a single small storefront.
- **B2B / wholesale orientation** — distributors and wholesalers buy and sell to other
  businesses constantly; retailers transact with end consumers episodically.
- **Size** — a larger employee headcount signals more operational complexity and more
  purchasing budget.
- **Port proximity** — companies near major commercial ports handle more inbound
  freight and outbound distribution — a proxy for logistics-heavy operations.
- **Industry code (NAICS) match** — wholesale NAICS codes line up with this ICP far
  better than retail codes do.
""")

    st.markdown("""
## How scoring works

Every account is scored across **five weighted dimensions**. For each dimension, the
enrichment data is converted into a raw fraction between 0 and 1 (how strongly that
company matches the ideal signal), which is then multiplied by that dimension's weight
to produce points earned for that dimension.

```
dimension points = raw fraction (0–1) × dimension weight
```

All five dimensions' points are added together, then normalized against the sum of the
active weights to produce the final **0–100 score**:

```
final score = (sum of all dimension points ÷ sum of active weights) × 100
```

Accounts are then sorted into tiers:

| Tier | Score range | Meaning |
|---|---|---|
| **Tier 1** | 70–100 | Strong ICP fit — prioritize for outreach |
| **Tier 2** | 40–69 | Moderate fit — worth qualifying |
| **Tier 3** | 0–39 | Weak fit — deprioritize |
""")

    st.markdown("""
## The five parameters

### 1. Multi-location / Chain — default weight 35 (35% of the 100-point scale)

**Measures:** how many locations the company operates — the single strongest signal
for this example ICP.

**Data source:** Google Places (verified location count), with CSV name-deduplication
as a fallback floor when Places has no confirmed count.

**Raw fraction:**

| Condition | Fraction |
|---|---|
| Google Places confirms 10+ locations | 1.00 |
| 3–9 locations (Places or CSV dedup) | 0.80 |
| 2 locations (Places or CSV dedup) | 0.55 |
| 1 location | 0.14 |

### 2. B2B / Wholesale Signal — default weight 25 (25% of the 100-point scale)

**Measures:** how likely the company sells to other businesses rather than end
consumers.

**Data source:** company name keyword analysis, boosted by Census NAICS code and
state dealer license class where available.

**Raw fraction:** starts from a name-keyword match (baseline 0.20 with no match; up to
1.00 for "wholesale" / "distribut…" in the name — see table below), then additively
boosted (capped at 1.00):
- NAICS code starts with 423 or 424 (wholesale): **+0.20**
- State dealer license class contains "wholesale": **+0.25**
- State dealer license class contains "dealer": **+0.10**

| Name keyword | Fraction |
|---|---|
| wholesale, distribut(ion/or) | 1.00 |
| industrial | 0.85 |
| warehouse | 0.80 |
| supply | 0.60 |
| parts | 0.55 |
| equipment, hardware | 0.50 |
| commercial | 0.45 |
| marine center | 0.40 |
| (no match) | 0.20 baseline |

### 3. Size Proxy — default weight 20 (20% of the 100-point scale)

**Measures:** company size as a proxy for operational complexity and purchasing power.

**Data source:** U.S. Census County Business Patterns (CBP) 2023, by ZIP code.

**Raw fraction:** from the employee band, plus up to a **+0.15** bonus if the ZIP code
has 3+ marine-industry establishments (or **+0.08** for exactly 2):

| Employee band | Fraction |
|---|---|
| 1–4 | 0.00 |
| 5–9 | 0.25 |
| 10–19 | 0.50 |
| 20–49 | 0.75 |
| 50–99 | 0.90 |
| 100+ (100–249, 250–499, 500–999, 1000+) | 1.00 |
| N/A (Census-suppressed) | 0.30 |

### 4. Port Proximity — default weight 12 (12% of the 100-point scale)

**Measures:** distance to the nearest major commercial marine port, as a proxy for
inbound freight / distribution volume.

**Data source:** a pre-computed static lookup built from Army Corps of Engineers
waterborne commerce tonnage data (44 major ports), keyed by ZIP code.

**Raw fraction:**

| Distance to nearest port | Fraction |
|---|---|
| ≤ 15 miles | 1.00 |
| 15–30 miles | 0.83 |
| 30–60 miles | 0.58 |
| 60–100 miles | 0.33 |
| > 100 miles | 0.00 |

### 5. NAICS Pain Fit — default weight 8 (8% of the 100-point scale)

**Measures:** how well the company's Census-reported industry code aligns with the
example ICP.

**Data source:** Census CBP NAICS code for the company's ZIP.

**Raw fraction:**

| NAICS prefix | Industry | Fraction |
|---|---|---|
| 423 | Durable goods wholesale | 1.00 |
| 424 | Nondurable goods wholesale | 0.90 |
| 336 | Transportation equipment manufacturing | 0.70 |
| 713 | Marinas / recreation | 0.55 |
| 441 | Retail boat dealers | 0.35 |
| Unknown | No Census match | 0.40 |

**Default weight summary** (weight ÷ sum of default weights = share of the 100-point scale;
default weights sum to 100, so each share equals its weight):

| Dimension | Default weight | Share of total score |
|---|---|---|
| Multi-location / Chain | 35 | 35% |
| B2B / Wholesale Signal | 25 | 25% |
| Size Proxy | 20 | 20% |
| Port Proximity | 12 | 12% |
| NAICS Pain Fit | 8 | 8% |
""")

    st.markdown("""
## Adjusting the weights

The five sliders in the sidebar (**Scoring Weights**) set the *maximum points* each
dimension can contribute to the 100-point scale. Raising a slider increases that
dimension's share of the final score; lowering it decreases that share. Setting a
slider to **0** removes that dimension from scoring entirely — it stops affecting the
score and the rank order.

Weight changes re-score and re-rank every account **instantly**, with no re-enrichment
and no additional API calls — scoring is pure computation over data that's already
been fetched. Adjust the sliders freely to explore how the ranking shifts for a
different emphasis (e.g. weight Size Proxy higher if you care more about company scale
than port logistics).
""")

    st.markdown("""
## Reading an account's score

After enrichment, scroll to the **Account Detail** section below the results table and
select any company from the dropdown. This expands a panel with:

- **Enrichment Data** — the raw signals pulled for that company: Places-confirmed
  location count, CSV dedup location count, chain flag, employee band, ZIP
  establishment count, NAICS code and label, nearest port and distance, Army Corps
  rank, and NY/WA license status where applicable.
- **Score Breakdown** — a small table showing the points earned on each of the five
  dimensions next to that dimension's current max weight (from the sidebar sliders).
- **Rationale** — a plain-English sentence explaining the top 1–3 signals driving that
  company's score and tier, generated directly from the same enrichment data.
""")

    st.markdown("""
## Improving accuracy (optional)

The app runs fully without any configuration — Census, port proximity, and state
registry data all work out of the box. Google Places is the one enrichment source that
benefits from a personal API key: pasting your own key in the sidebar's **Google
Places API Key** section enables (or improves) national location-count lookups, which
strengthens the multi-location / chain detection signal.

Without a Places key, the app simply falls back to CSV-based name deduplication for
location counts — nothing breaks, the multi-location signal is just less complete.

See the **"How to get a free Google Places API key"** expander in the sidebar for a
4-step walkthrough. Google's free monthly credit typically covers usage for this app.
""")
