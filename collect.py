import requests
import csv
import os
import datetime

# --- Konfiguration ---
API_KEY  = 0XZMFOdQbXs852mYYkrINgnDgOB_CElRc8sG0Qa3WPU
LAT      = 53.552785   # Deine Koordinate
LON      = 10.058144   # Deine Koordinate
CSV_FILE = "traffic_log.csv"

def classify(jam):
    if jam < 3:   return "grün"
    elif jam < 7: return "gelb"
    else:         return "rot"

def collect():
    url = "https://data.traffic.hereapi.com/v7/flow"
    params = {
        "in": f"circle:{LAT},{LON};r=200",
        "locationReferencing": "shape",
        "apiKey": API_KEY
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    results = r.json().get("results", [])

    if not results:
        print("Keine Segmente gefunden.")
        return

    # CSV-Header anlegen falls Datei neu
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp", "street",
                "jam_factor", "speed_current",
                "speed_freeflow", "color"
            ])
        for segment in results:
            street    = segment["location"]["description"]
            flow      = segment["currentFlow"]
            jam       = flow["jamFactor"]
            speed     = flow["speed"]
            free_flow = flow["freeFlow"]
            color     = classify(jam)

            writer.writerow([
                datetime.datetime.utcnow().isoformat(),
                street,
                round(jam, 2),
                round(speed, 1),
                round(free_flow, 1),
                color
            ])
            print(f"{street}: jam={jam}, {color}")

collect()
