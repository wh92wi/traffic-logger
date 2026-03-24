import requests
import csv
import os
import datetime
import math
import zoneinfo

API_KEY        = os.environ["HERE_API_KEY"]
CSV_FILE       = "traffic_log-v2.csv"
LOCATIONS_FILE = "locations.csv"
LOCAL_TZ       = zoneinfo.ZoneInfo("Europe/Berlin")

def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

def nearest_segment(results, lat, lon):
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

def get_segment_endpoints(segment):
    links = segment["location"]["shape"]["links"]
    first = links[0]["points"][0]
    last  = links[-1]["points"][-1]
    return first, last

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
    locations   = load_locations()
    file_exists = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp_utc", "timestamp_local",
                "my_name", "here_name",
                "segment_length_m",
                "seg_start_lat", "seg_start_lon",
                "seg_end_lat", "seg_end_lon",
                "freeFlow", "speed", "speedUncapped",
                "jamFactor", "jamTendency", "confidence"
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

                now_utc   = datetime.datetime.now(datetime.timezone.utc)
                now_local = now_utc.astimezone(LOCAL_TZ)

                segment     = nearest_segment(results, loc["lat"], loc["lon"])
                currentFlow = segment["currentFlow"]
                first, last = get_segment_endpoints(segment)

                here_name      = segment["location"].get("description", "")
                segment_length = segment["location"].get("length", "")
                freeFlow       = currentFlow["freeFlow"]
                speed          = currentFlow["speed"]
                speedUncapped  = currentFlow["speedUncapped"]
                jamFactor      = currentFlow["jamFactor"]
                jamTendency    = currentFlow.get("jamTendency", "")
                confidence     = currentFlow["confidence"]

                writer.writerow([
                    now_utc.isoformat(),
                    now_local.isoformat(),
                    loc["name"],
                    here_name,
                    segment_length,
                    first["lat"], first["lng"],
                    last["lat"],  last["lng"],
                    round(freeFlow, 1),
                    round(speed, 1),
                    round(speedUncapped, 1),
                    round(jamFactor, 2),
                    jamTendency,
                    round(confidence, 2),
                ])
                print(f"{loc['name']} ({here_name}): jam={jamFactor}, speed={speed}")

            except Exception as e:
                print(f"Fehler bei {loc['name']}: {e}")

collect()
