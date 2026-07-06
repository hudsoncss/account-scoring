"""
Build data/port_zip_lookup.json from ZIP codes in the source dataset.
Uses pgeocode for ZIP->lat/lon, then computes geodesic distance to
major US marine ports sourced from Army Corps of Engineers waterborne
commerce data (top-30 ports by annual tonnage).

Run once: python scripts/build_port_lookup.py
"""

import json
import math
import pandas as pd
import pgeocode

# Top 30 US marine ports by Army Corps waterborne commerce tonnage.
# Coordinates are port centroid lat/lon. Tonnage rank = Army Corps rank.
ARMY_CORPS_PORTS = [
    {"name": "South Louisiana / New Orleans",  "lat": 29.95,  "lon": -90.07,  "rank": 1},
    {"name": "Houston",                         "lat": 29.73,  "lon": -95.27,  "rank": 2},
    {"name": "New York / New Jersey",           "lat": 40.66,  "lon": -74.04,  "rank": 3},
    {"name": "Beaumont",                         "lat": 30.08,  "lon": -94.13,  "rank": 4},
    {"name": "Port of Los Angeles",             "lat": 33.74,  "lon": -118.26, "rank": 5},
    {"name": "Long Beach",                      "lat": 33.75,  "lon": -118.22, "rank": 6},
    {"name": "Corpus Christi",                  "lat": 27.80,  "lon": -97.40,  "rank": 7},
    {"name": "Port Arthur",                     "lat": 29.87,  "lon": -93.93,  "rank": 8},
    {"name": "Texas City",                      "lat": 29.39,  "lon": -94.90,  "rank": 9},
    {"name": "Baton Rouge",                     "lat": 30.44,  "lon": -91.19,  "rank": 10},
    {"name": "Tampa Bay",                       "lat": 27.93,  "lon": -82.45,  "rank": 11},
    {"name": "Baltimore",                       "lat": 39.27,  "lon": -76.58,  "rank": 12},
    {"name": "Mobile",                          "lat": 30.70,  "lon": -88.05,  "rank": 13},
    {"name": "Seattle / Puget Sound",           "lat": 47.60,  "lon": -122.33, "rank": 14},
    {"name": "Norfolk / Hampton Roads",         "lat": 36.85,  "lon": -76.30,  "rank": 15},
    {"name": "Pittsburgh",                      "lat": 40.44,  "lon": -80.00,  "rank": 16},
    {"name": "Lake Charles",                    "lat": 30.22,  "lon": -93.22,  "rank": 17},
    {"name": "Port Everglades / Fort Lauderdale","lat": 26.09,  "lon": -80.13,  "rank": 18},
    {"name": "Portland OR",                     "lat": 45.52,  "lon": -122.67, "rank": 19},
    {"name": "Cleveland",                       "lat": 41.50,  "lon": -81.69,  "rank": 20},
    {"name": "Savannah",                        "lat": 32.08,  "lon": -81.10,  "rank": 21},
    {"name": "Charleston SC",                   "lat": 32.78,  "lon": -79.93,  "rank": 22},
    {"name": "Miami",                           "lat": 25.77,  "lon": -80.19,  "rank": 23},
    {"name": "Philadelphia",                    "lat": 39.95,  "lon": -75.17,  "rank": 24},
    {"name": "Boston",                          "lat": 42.36,  "lon": -71.05,  "rank": 25},
    {"name": "Duluth / Superior",               "lat": 46.78,  "lon": -92.10,  "rank": 26},
    {"name": "Detroit",                         "lat": 42.33,  "lon": -83.05,  "rank": 27},
    {"name": "Tacoma",                          "lat": 47.25,  "lon": -122.43, "rank": 28},
    {"name": "Jacksonville",                    "lat": 30.33,  "lon": -81.66,  "rank": 29},
    {"name": "Pascagoula",                      "lat": 30.36,  "lon": -88.56,  "rank": 30},
    # Additional coastal ports with significant marine commerce
    {"name": "Wilmington NC",                   "lat": 34.24,  "lon": -77.95,  "rank": 31},
    {"name": "Morehead City NC",                "lat": 34.72,  "lon": -76.73,  "rank": 32},
    {"name": "Pensacola",                       "lat": 30.42,  "lon": -87.22,  "rank": 33},
    {"name": "Gulfport MS",                     "lat": 30.37,  "lon": -89.09,  "rank": 34},
    {"name": "Providence RI",                   "lat": 41.82,  "lon": -71.41,  "rank": 35},
    {"name": "New Haven CT",                    "lat": 41.30,  "lon": -72.92,  "rank": 36},
    {"name": "Albany NY",                       "lat": 42.65,  "lon": -73.75,  "rank": 37},
    {"name": "Everett WA",                      "lat": 47.98,  "lon": -122.21, "rank": 38},
    {"name": "Astoria OR",                      "lat": 46.19,  "lon": -123.83, "rank": 39},
    {"name": "Eureka CA",                       "lat": 40.80,  "lon": -124.16, "rank": 40},
    {"name": "San Diego",                       "lat": 32.71,  "lon": -117.17, "rank": 41},
    {"name": "Oakland",                         "lat": 37.80,  "lon": -122.27, "rank": 42},
    {"name": "Honolulu",                        "lat": 21.31,  "lon": -157.86, "rank": 43},
    {"name": "Anchorage",                       "lat": 61.22,  "lon": -149.90, "rank": 44},
]


def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def distance_to_score(miles):
    if miles <= 15:   return 1.00
    if miles <= 30:   return 0.83
    if miles <= 60:   return 0.58
    if miles <= 100:  return 0.33
    return 0.0


def build_lookup(zip_codes):
    nomi = pgeocode.Nominatim("us")
    lookup = {}

    for zip_code in zip_codes:
        result = nomi.query_postal_code(zip_code)
        if result is None or pd.isna(result.latitude):
            lookup[zip_code] = {"score_fraction": 0.0, "ports": [], "distance_miles": None}
            continue

        lat, lon = result.latitude, result.longitude

        best_dist = float("inf")
        best_ports = []

        for port in ARMY_CORPS_PORTS:
            dist = haversine_miles(lat, lon, port["lat"], port["lon"])
            if dist < best_dist:
                best_dist = dist
                best_ports = [port["name"]]
                best_rank = port["rank"]
            elif dist < best_dist + 20:  # Include near-ties within 20 miles
                best_ports.append(port["name"])

        lookup[zip_code] = {
            "score_fraction":       distance_to_score(best_dist),
            "ports":                best_ports[:2],
            "distance_miles":       round(best_dist, 1),
            "army_corps_rank":      best_rank,
        }

    return lookup


if __name__ == "__main__":
    df = pd.read_csv("data/companies.csv", dtype=str)
    zip_codes = df["ZIP Code"].str.strip().str.zfill(5).unique().tolist()
    print(f"Building port proximity lookup for {len(zip_codes)} unique ZIPs...")

    lookup = build_lookup(zip_codes)

    out_path = "data/port_zip_lookup.json"
    with open(out_path, "w") as f:
        json.dump(lookup, f, indent=2)

    print(f"Written to {out_path}")

    # Spot-check a few notable ZIPs
    checks = {
        "33316": "Fort Lauderdale (expect Port Everglades, ~0 miles)",
        "77008": "Houston TX (expect Houston port, ~0 miles)",
        "86403": "Lake Havasu City AZ (expect score 0.0 -- inland)",
        "28405": "Wilmington NC (expect some coastal port)",
    }
    for z, label in checks.items():
        if z in lookup:
            d = lookup[z]
            print(f"  {z} ({label}): {d['ports']} @ {d['distance_miles']}mi → score {d['score_fraction']}")
