# PDF SmartForms Studio 1.0.0-rc.8

Dieser Teststand trennt persönliche Profildaten von Entscheidungen, die nur für ein
bestimmtes Formular gelten.

## Neu

- Ja/Nein- und Optionsfelder können als Template-eigene Formularangaben gruppiert werden.
- Frage, technische Gruppenkennung und Auswahlwert sind im Analysefenster bearbeitbar.
- Der aktuelle Wert einer Optionsgruppe kann für Vorschau und PDF-Ausgabe gewählt werden.
- **Zuordnung lösen** entfernt eine falsche Datenquelle, behält das erkannte Feld aber bei.
- AcroForm-Optionsgruppen übernehmen ihre Gruppe und Werte wie `Ja` und `Nein` automatisch.

## Korrigiert

- Ja/Nein-Felder werden nicht mehr über benachbarten Text einem Namensfeld im Profil
  zugeordnet.

## Testhinweis

Wähle ein Optionsfeld aus. Prüfe rechts Formularfrage, Optionsgruppe und Auswahlwert.
Bei falscher Zuordnung zunächst **Zuordnung lösen** und anschließend
**Als Formularangabe übernehmen** wählen. Sobald beide Werte einer Gruppe eingerichtet
sind, kann unter **Aktueller Wert** zwischen ihnen gewechselt werden.
