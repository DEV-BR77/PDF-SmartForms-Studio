# Sicherheitsprüfung 1.0.0-rc.1

## Geprüfte Schutzmaßnahmen

- importierte ZIP-basierte Pakete blockieren absolute Pfade und `..`
- Austauschpakete und Backups besitzen Größen- und Integritätsprüfungen
- PDF-Analyse führt kein eingebettetes JavaScript aus
- E-Mails werden ausschließlich als lokaler Entwurf erzeugt
- jede Ausgabe benötigt eine bestätigte Sicherheitsvorschau
- bestehende Dateien werden bei Wiederherstellung nicht still überschrieben
- Plugins werden in diesem RC nicht ausgeführt
- temporäre Arbeitsverzeichnisse werden bereinigt

## Offene Punkte vor Stable

- Codesignatur für Windows-Artefakte
- verschlüsselte Backups bei Aufnahme von Bildunterschriften
- externer Review des endgültigen Lizenz- und Sicherheitsumfangs

Es sind keine bekannten offenen P0- oder P1-Sicherheitsfehler dokumentiert.
