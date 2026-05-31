# traffic-logger

### API-Key
https://platform.here.com

### Auslesen der Polyline
- Gehe auf https://router.hereapi.com/v8/routes?transportMode=car&origin=[Start-lat und -lng]&destination=[Ziel-lat und -lng]&spans=segmentId,streetAttributes&return=polyline,actions,instructions,summary&apiKey=[API_KEY]
- Kopiere die JSON-Datei und überprüfe sie auf https://placematic.com/tools/here-route-v8-decoder
-  Kopiere den Polyline-Wert

### Auslesen passender Koordinaten für Suche
- Gehe auf https://data.traffic.hereapi.com/v7/flow?in=circle:[lat],[lng];r=500&locationReferencing=shape&apiKey=[DEIN_KEY] oder besser auf https://data.traffic.hereapi.com/v7/flow?in=corridor:[polyline];r=5&locationReferencing=shape&apiKey=[API_KEY]
- Kopiere die dort erzeuge JSON-Datei
- Gehe auf https://wh92wi.github.io/traffic-logger/map_viewer.html
- Kopiere die JSON-Datei aus der Zwischenablage hinein
- Suche dir den am besten passenden Abschnitt aus
- Übertrage die Koordinaten und weitere Angaben in die locations.csv

### HERE Maps
Dokumentation der Traffic API: https://www.here.com/docs/bundle/traffic-api-developer-guide-v7/page/README.html
