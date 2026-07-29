# Versionsdokumentation

## 0.1.0-alpha – Foundation

**Ziel:** lauffähige PyQt6-Anwendung mit sauberer Architektur.

- Paketstruktur und Dependency Injection
- App-Shell, Navigation, Theme und Icon-Platzhalter
- Konfiguration und lokaler Datenpfad
- Logging ohne personenbezogene Daten
- CI, Tests und Build-Prototyp
- About-Dialog mit Version, Build, Commit und Repository

**Exit:** App startet als Standardbenutzer; Architekturtests und CI grün; Installationsanleitung vorhanden.

## 0.2.0-alpha – Profiles

- Kernfelder, Guardians und flexible Custom Fields
- Profil neu/bearbeiten/löschen
- DatePicker und Validierung
- ein Feld `Ort` für Wohn- und Unterschriftsort
- optional Nachname des Kindes übernehmen
- Schutzstufen und Einmalfelder

## 0.3.0-alpha – Templates

- JSON Schema
- Import/Export und Vertrauensstufe
- Koordinatenmodell und Seitendrehung
- Templateversionen und Kompatibilität

## 0.4.0-alpha – Analysis & Preview

- AcroForm-Auswertung
- Text-/Layoutheuristik für flache PDFs
- grün/gelb/rot plus Symbole
- manuelle Zuordnung und Konfidenz

## 0.5.0-alpha – Field Dictionary

- Aliasregister
- bestätigtes Lernen
- lokaler Import/Export
- Konflikt- und Confidence-Modell

## 0.6.0-alpha – Signatures

- PNG/JPG-Import
- Zuschneiden, Kontrast und Weißtransparenz
- Drag & Drop, Skalieren, Positionieren
- ein oder zwei Guardians
- klare Abgrenzung zur Zertifikatssignatur

## 0.7.0-alpha – Designer

- Felder per Maus zeichnen
- Typ, Quelle, Pflichtstatus und Speicherverhalten
- Zoom, Seitenwechsel, Tastaturfeinsteuerung
- Template testen und speichern

## 0.8.0-alpha – Distribution

- Dokumenttitel, Empfänger und Betreff vorschlagen
- Speichern, Drucken, E-Mail-Entwurf
- Verteilerlisten
- Austauschpaket mit PDF, Template, leerem Profil, Anleitung und Repository-Link

## 0.9.0-beta – Hardening

- Sicherheitsvorschau
- Backup/Restore/Migration
- sichere temporäre Dateien
- Plugin-Grundgerüst
- Barrierefreiheit, Performance, Installer

## 1.0.0 – Community

- vollständiges Handbuch
- geprüfte Installer-Artefakte
- SBOM, Prüfsummen und Releasebericht
- keine offenen P0/P1-Fehler

### 1.0.0-rc.1 – privater Release Candidate

- vollständiges deutschsprachiges Benutzerhandbuch
- visuell geprüfte Screenshots und eigenes App-Icon
- Windows-ZIP mit Buildinformationen
- CycloneDX-SBOM und SHA-256-Prüfsummen
- Security-, Privacy-, Test- und Freigabebericht
- keine öffentliche Stable-Freigabe vor Lizenzprüfung und Codesignaturentscheidung
