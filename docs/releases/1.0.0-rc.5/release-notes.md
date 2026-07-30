# PDF SmartForms Studio 1.0.0-rc.5

## Schwerpunkt

Der visuelle Template-Designer erhält einen klaren, an etablierten PDF-Editoren
orientierten Arbeitsablauf, ohne die zusätzliche SmartForms-Profilzuordnung zu
verlieren.

## Neu

- Feldliste links, skalierbare PDF-Arbeitsfläche in der Mitte und Eigenschaften rechts
- Feldtypen direkt über „Feld hinzufügen“ auswählen und auf der PDF-Seite aufziehen
- X-/Y-Position, Breite und Höhe numerisch bearbeiten
- Felder sichtbar löschen sowie per `Entf`, `Strg+Z` und `Strg+Y` bearbeiten
- PDF24-Formularbeschreibungen (`.json`) einschließlich Namen, Typen, Koordinaten und
  Pflichtfeldkennzeichen importieren
- Seitenansicht beim Maximieren und Ändern der Fenstergröße automatisch einpassen

## Getestetes Beispieldokument

Das bereitgestellte WOLLINO-Formular wurde mit 29 PDF24-Feldern geprüft:

- 13 Textfelder
- 15 Kontrollkästchen
- 1 Signaturfeld

Alle Felder werden mit dem PDF-Koordinatenursprung oben links positionsgetreu importiert.

## Bekannte Grenze

PDF24-spezifische JavaScript-Aktionen und Darstellungseigenschaften werden nicht
importiert. PDF SmartForms Studio übernimmt die für Templates relevanten Feldtypen,
Namen, Positionen, Größen und Pflichtfeldkennzeichen. Profilquellen müssen anschließend
bestätigt werden.
