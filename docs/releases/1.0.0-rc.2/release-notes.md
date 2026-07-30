# PDF SmartForms Studio 1.0.0-rc.2

Dieser zweite private Release Candidate konzentriert sich auf die Rückmeldungen
aus dem ersten realen Formular-Test.

## Verbesserungen

- Das PDF-Analysefenster lässt sich maximieren.
- Die vollständige PDF-Seite passt sich automatisch an die Vorschaufläche an.
- Manueller Zoom bleibt erhalten; „Seite“ stellt die passende Seitenansicht wieder her.
- Rechtstexte und kleine Fußzeilen werden seltener als Formularfelder erkannt.
- Dokumenttitel und vorgeschlagene Dateinamen sind kürzer und verständlicher.
- Die Feldliste bietet mehr Platz und eine noch nicht gewählte Zuordnung ist eindeutig.
- Fehlt eine Unterschrift, öffnet sich direkt die Unterschriftenverwaltung.
- Drucken erfolgt über einen eigenen Systemdialog und benötigt keine PDF-Dateizuordnung.
- Menüeinträge und deutsche Beschriftungen wurden bereinigt.

## Prüfung

- automatisierte Unit-, Integrations- und Regressionstests
- Format-, Lint-, Typ- und Architekturprüfung
- Windows-Build mit PyInstaller
- Releasepaket mit Buildinformationen, SBOM und SHA-256-Prüfsummen

## Testhinweis

Vor einer stabilen Veröffentlichung sollen insbesondere die Feldanalyse an
weiteren echten, rechtmäßig verwendbaren Formularen sowie Speichern, Drucken,
E-Mail-Entwurf und Unterschriftenplatzierung praktisch geprüft werden.
