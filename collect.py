import requests
import csv
import os
import datetime
import math
import zoneinfo

API_KEY        = os.environ["HERE_API_KEY"]
CSV_FILE       = "traffic_log.csv"
LOCATIONS_FILE = "locations.csv"
LOCAL_TZ       = zoneinfo.ZoneInfo("Europe/Berlin")

def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

def nearest_matching_segment(results, lat, lon, street_name):
    """
    Gibt das nächstgelegene und kürzeste Segment zurück,
    dessen HERE-Name exakt mit street_name übereinstimmt.
    Gibt None zurück wenn kein passendes Segment gefunden wird.
    """
    matching = [
        s for s in results
        if s["location"].get("description", "").strip().lower()
        == street_name.strip().lower()
    ]

    if not matching:
        return None

    def score(segment):
        links  = segment["location"]["shape"]["links"]
        point  = links[0]["points"][0]
        dist   = distance(lat, lon, point["lat"], point["lng"])
        length = segment["location"].get("length", 9999)
        return dist * 1000 + length

    return min(matching, key=score)

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
                "street_name": row["street_name"],
                "position_id": row["position_id"],
                "annotation":  row.get("annotation", ""),
                "lat":         float(row["lat"]),
                "lon":         float(row["lon"])
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
                "street_name", "position_id", "annotation", "here_name",
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

                for radius in [50, 100, 200, 350, 500]:
                    if results:
                        break
                    params["in"] = f"circle:{loc['lat']},{loc['lon']};r={radius}"
                    r = requests.get(url, params=params, timeout=10)
                    r.raise_for_status()
                    results = r.json().get("results", [])

                if not results:
                    print(f"WARNUNG: Keine Segmente in der Nähe von "
                          f"{loc['street_name']} #{loc['position_id']}")
                    continue

                segment = nearest_matching_segment(
                    results, loc["lat"], loc["lon"], loc["street_name"]
                )

                if segment is None:
                    available = list({
                        s["location"].get("description", "")
                        for s in results
                    })
                    print(f"WARNUNG: Kein Segment '{loc['street_name']}' gefunden. "
                          f"Verfügbare Straßen: {available}")
                    continue

                now_utc   = datetime.datetime.now(datetime.timezone.utc)
                now_local = now_utc.astimezone(LOCAL_TZ)

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
                    loc["street_name"],
                    loc["position_id"],
                    loc["annotation"],
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
                print(f"{loc['street_name']} #{loc['position_id']} ({loc['annotation']}) "
                      f"({here_name}, {segment_length}m): "
                      f"jam={jamFactor}, speed={speed}")

            except Exception as e:
                print(f"Fehler bei {loc['street_name']} #{loc['position_id']}: {e}")

collect()
