# PDF SmartForms Studio 1.0.0-rc.7

## Schwerpunkt

RC.7 macht normale PDF-Dokumente zum Standardfall. Ein PDF24-Export ist nicht
erforderlich.

## Arbeitsablauf

1. Normales PDF öffnen.
2. Automatische Vorschläge prüfen.
3. Falsche Vorschläge entfernen.
4. Fehlende Felder direkt auf der Seite aufziehen.
5. Feldtyp, Position und Größe korrigieren.
6. Profilfelder zuordnen.
7. Die korrigierte Analyse als lokale Vorlage speichern.

## Neu

- Automatische Vorschläge für sichtbare Ja/Nein-Kästchen.
- Direkte Feldanlage auf der PDF-Vorschau.
- Bearbeitung von Feldtyp und Geometrie.
- Standardmäßig nur ein blauer Auswahlrahmen statt überlappender Rahmen.
- Erkennungsart, Feldtyp und Koordinaten in der Feldliste.
- Lokale Vorlagenspeicherung aus der Analyse.
- Optionaler, klar getrennter PDF24-Feldimport.
- Automatische Vorlagenerkennung über einen Fingerabdruck aus stabilen Metadaten,
  Seitengeometrie und normalisiertem sichtbarem Text.
- Datenschutzfreundlicher Beitrag zum Vorlagenarchiv ohne PDF, Profile,
  Feldwerte oder Unterschriften.
- Mit einem Release ausgelieferte Vorlagen werden beim Start lokal installiert.

## Community und Maintainer

Die Community-Version zeigt keine PDF24-Funktion. Für die Pflege und das
Anlernen des offiziellen Vorlagenarchivs gibt es einen separaten
Maintainer-Build. Dieser übernimmt Feldtyp, Seite, Position und Größe aus einer
PDF24-JSON-Datei. Das Ergebnis wird anschließend wie jede andere lokale Vorlage
gespeichert und über den Dokumentfingerabdruck wiedererkannt.

## Bekannte Grenze

Bei komplexen Scans oder ungewöhnlichen Layouts kann die automatische Erkennung
weiterhin Vorschläge übersehen oder Text fälschlich als Eingabefeld einstufen.
Diese Fälle können nun ohne ein externes Werkzeug im Analysefenster korrigiert
und dauerhaft als lokale Vorlage gespeichert werden.
