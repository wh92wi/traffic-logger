import requests
import csv
import os
import datetime
import math

API_KEY  = os.environ["HERE_API_KEY"]
CSV_FILE = "traffic_log2.csv"
LOCATIONS_FILE = "locations.csv"

def distance(lat1, lon1, lat2, lon2):
    """Einfache euklidische Näherung für kurze Distanzen"""
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

def nearest_segment(results, lat, lon):
    """Gibt das Segment zurück, dessen erster Punkt am nächsten liegt"""
    best = None
    best_dist = float("inf")
    for segment in results:
        links = segment["location"]["shape"]["links"]
        point = links[0]["points"][0]
        d = distance(lat, lon, point["lat"], point["lng"])
        if d < best_dist:
            best_dist = d
            best = segment
    return best

def load_locations():
    locations = []
    with open(LOCATIONS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            locations.append({
                "name": row["name"],
                "lat":  float(row["lat"]),
                "lon":  float(row["lon"])
            })
    return locations

def collect():
    locations = load_locations()

    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp", "name",
                "jam_factor", "speed_current",
                "speed_freeflow", "color"
            ])

        for loc in locations:
            try:
                url = "https://data.traffic.hereapi.com/v7/flow"
                params = {
                    "in": f"circle:{loc['lat']},{loc['lon']};r=20",
                    "locationReferencing": "shape",
                    "apiKey": API_KEY
                }
                r = requests.get(url, params=params, timeout=10)
                r.raise_for_status()
                results = r.json().get("results", [])

                # Falls r=20 nichts liefert, Radius schrittweise vergrößern
                for radius in [50, 100, 200]:
                    if results:
                        break
                    params["in"] = f"circle:{loc['lat']},{loc['lon']};r={radius}"
                    r = requests.get(url, params=params, timeout=10)
                    r.raise_for_status()
                    results = r.json().get("results", [])

                if not results:
                    print(f"Keine Daten für {loc['name']}")
                    continue

                segment       = nearest_segment(results, loc["lat"], loc["lon"])
                currentFlow   = segment["currentFlow"]
                freeFlow      = flow["freeFlow"]
                speed         = flow["speed"]
                speedUncapped = flow["speedUncapped"]
                jamFactor     = flow["jamFactor"]
                jamTendency   = flow["jamTendency"]
                confidence     = flow["confidence"]

                writer.writerow([
                    datetime.datetime.utcnow().isoformat(),
                    loc["name"],
                    round(currentFlow, 1),
                    round(freeFlow, 1),
                    round(speed, 1),
                    round(speedUncapped, 1),
                    round(jamFactor, 2),
                    round(jamTendency, 2),
                    round(confidence, 2),
                ])
                print(f"{loc['name']}: jam={jamFactor}, {speed}")

            except Exception as e:
                print(f"Fehler bei {loc['name']}: {e}")

collect()
