"""
Chain detection via name normalization. No API calls — runs instantly on the CSV.
Identifies multi-location brands by normalizing names to a canonical token,
then grouping. is_known_chain and verified location counts come from Google
Places in the batch runner — nothing is hardcoded here.
"""

import re
from collections import defaultdict

# Location qualifiers stripped from names to find the brand root
_LOCATION_QUALIFIERS = [
    r"\s+of\s+\w+(\s+\w+)?$",
    r"\s+(clearwater|miami|key largo|houston|dallas|lake ozark|louisville|"
    r"cincinnati|westchester|north shore|chesapeake|annapolis|everett|"
    r"astoria|minneapolis|st\s+paul|st\s+louis|kansas city|oklahoma city|"
    r"salt lake|las vegas|phoenix|tucson|denver|boulder|chicago|detroit|"
    r"cleveland|pittsburgh|philadelphia|boston|portland|seattle|tacoma|"
    r"sacramento|san diego|san jose|los angeles|long beach|orlando|"
    r"jacksonville|pensacola|savannah|columbia|charleston|raleigh|"
    r"charlotte|norfolk|richmond|atlanta|birmingham|nashville|memphis|"
    r"new orleans|baton rouge|san antonio|austin|fort worth|el paso|"
    r"albuquerque|tucson)\s*$",
]

_DIRECTIONAL = r"\s+(north|south|east|west|northeast|northwest|southeast|southwest)\s*$"

_SUFFIX = r"\s+(group|center|centres?|corp|llc|inc|co|company|sales|" \
          r"service|services|enterprises?|industries|international|usa)\s*$"


def _normalize(name: str) -> str:
    s = name.lower().strip()
    for pattern in _LOCATION_QUALIFIERS:
        s = re.sub(pattern, "", s, flags=re.IGNORECASE).strip()
    s = re.sub(_DIRECTIONAL, "", s, flags=re.IGNORECASE).strip()
    s = re.sub(_SUFFIX, "", s, flags=re.IGNORECASE).strip()
    s = re.sub(r"[^a-z0-9 ]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def detect_chains(df) -> dict:
    """
    Returns dict mapping Business Name -> chain metadata dict.
    Only uses the CSV itself — no hardcoded chain lists.
    Google Places data (injected later in the batch runner) provides
    the authoritative location count and is_known_chain flag.
    """
    brand_groups = defaultdict(list)

    for _, row in df.iterrows():
        brand = _normalize(row["Business Name"])
        brand_groups[brand].append({"name": row["Business Name"], "state": row["State"]})

    results = {}

    for brand, members in brand_groups.items():
        count = len(members)
        states = list({m["state"] for m in members})
        names = [m["name"] for m in members]

        for entry in members:
            results[entry["name"]] = {
                "chain_group":     brand if count > 1 else None,
                "location_count":  count,
                "location_states": states,
                "chain_members":   names if count > 1 else [],
                "is_known_chain":  False,  # set by batch runner from Places data
            }

    return results
