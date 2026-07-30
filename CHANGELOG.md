# Changelog

## Unreleased

## [1.0.0-rc.8] – 2026-07-30

### Added

- Template-eigene Formularangaben für Ja/Nein- und Optionsgruppen.
- Bearbeitbare Formularfrage, Gruppenkennung und Auswahlwerte.
- Aktueller Auswahlwert wird in Vorschau und PDF-Ausgabe als X dargestellt.
- Eine Datenzuordnung kann gelöst werden, ohne das erkannte Feld zu löschen.

### Fixed

- Optionsfelder werden nicht mehr fälschlich Profilfeldern wie dem Namen zugeordnet.
- AcroForm-Optionsgruppen übernehmen Gruppenname und Exportwert direkt aus dem PDF.

## [1.0.0-rc.7] – 2026-07-30

### Added

- Normale, flache PDFs sind jetzt der primäre Vorlagen-Workflow.
- Sichtbare Ja/Nein-Kästchen werden als Optionsfelder vorgeschlagen.
- Fehlende Felder können direkt mit der Maus auf der PDF-Seite aufgezogen werden.
- Feldtyp, Position und Größe lassen sich im Analysefenster korrigieren.
- Korrigierte Analysen können als wiederverwendbare lokale Vorlage gespeichert werden.
- Die Feldliste zeigt Erkennungsart, Feldtyp und PDF-Koordinaten.
- Dokumente werden über einen stabilen Fingerabdruck automatisch lokalen Vorlagen zugeordnet.
- Anonyme Vorlagenbeiträge enthalten nur Feldschema, Koordinaten und Fingerabdruck.
- Geprüfte Vorlagen können mit Releases ausgeliefert und beim Start installiert werden.
- Beim Start wird optional und ohne Zugangsdaten nach neuen Katalogvorlagen gesucht.
- Neue Vorlagen werden im Startfenster angezeigt und nur auf Wunsch installiert.
- Vorlagen speichern Institution, Kategorie, Ort, Dokumentart, Zielgruppe,
  Veröffentlichungsdatum, Gültigkeit und Schlagwörter.

### Changed

- Nur das ausgewählte Feld wird standardmäßig umrahmt; alle Rahmen sind optional.
- PDF24-JSON ist ein optionaler Import und keine Voraussetzung.
- PDF24-Import ist nur in der separaten Maintainer-Version sichtbar.
- Menüeinträge verzichten auf gequetschte Tastenkürzel.

## [1.0.0-rc.6] – 2026-07-30

### Added

- eigenständige linke Feldspalte in der PDF-Analyse
- blauer Fokusrahmen für das aktuell ausgewählte Feld
- direktes Anlegen und Befüllen neuer Profilfelder aus einem erkannten PDF-Feld
- dynamische Datenquellen aus importiertem Feldlexikon und ausgewähltem Profil
- getrennte Profilwerte für Festnetz und Mobiltelefon

### Changed

- Einstellungen stehen in einer eigenen, scrollbareren rechten Spalte
- Lexikonkonflikte können nach ausdrücklicher Bestätigung ersetzt werden
- ältere Quelle `contact.mobil` wird automatisch zu `contact.mobile` migriert
- vollständige Namen von Teilnehmenden und Erziehungsberechtigten können als
  zusammengesetzte Datenquelle verwendet werden

### Fixed

- neue Quellen aus importierten Lexikondateien fehlen nicht mehr in der Zuordnungsliste
- „mobil“ und „handynummer“ bleiben nicht mehr fälschlich dem Festnetz zugeordnet

## [1.0.0-rc.5] – 2026-07-30

### Added

- dreigeteilter Template-Designer mit Feldliste, PDF-Arbeitsfläche und Eigenschaften
- direktes Anlegen von Text-, Datums-, Auswahl-, Checkbox- und Signaturfeldern
- sichtbare Koordinaten- und Größenbearbeitung für ausgewählte Felder
- Import von PDF24-Formularbeschreibungen im JSON-Format
- sichtbare Löschfunktion und synchronisierte Auswahl zwischen Feldliste und PDF

### Changed

- Template-Seiten werden beim Öffnen und bei Fenstergrößenänderungen automatisch eingepasst
- der Template-Designer kann regulär maximiert und frei skaliert werden
- die PDF-Arbeitsfläche hebt sich als dunkler, ruhiger Arbeitsbereich ab

## [1.0.0-rc.4] – 2026-07-30

### Added

- Profilwahl direkt in der PDF-Analyse
- sichtbare Profilwerte in der Vorschau und in gespeicherten, gedruckten und
  per E-Mail vorbereiteten PDFs
- Größenregler und Löschfunktion für die ausgewählte Bildunterschrift
- anwendungsinterne Druckvorschau

### Changed

- Unterschriften werden zunächst automatisch im erkannten Unterschriftsbereich platziert
- Tabellenlinien bestimmen die Feldrahmen statt pauschaler Breiten bis zum Seitenrand
- der größte sichtbare Formulartitel ersetzt ungeeignete interne PDF-Metadaten
- neue Standardbegriffe unterscheiden Teilnehmer- und Erziehungsberechtigtendaten

### Fixed

- lange Profilwerte wie E-Mail-Adressen werden passend skaliert und vollständig exportiert
- Fußzeilen wie Datenschutz, Geschäftsführung und Kontaktdaten werden nicht als Felder markiert
- aktualisierte Standardbegriffe werden in vorhandene lokale Feldlexika übernommen

## [1.0.0-rc.3] – 2026-07-30

### Added

- Schaltfläche „Erkennung entfernen“ für Vorschläge, die keine Formularfelder sind
- sichtbare Versionsnummer direkt in der Titelleiste der PDF-Analyse

### Fixed

- Analysefenster verwendet ausdrücklich normale Minimieren- und Maximieren-Schaltflächen
- PDF-Seite wird nach dem Anzeigen und nach Größenänderungen zuverlässig neu eingepasst

## [1.0.0-rc.2] – 2026-07-30

### Added

- maximierbares Analysefenster mit automatisch eingepasster PDF-Seite
- Schaltfläche „Seite“ zum Wiederherstellen der vollständigen Seitenansicht
- eigener Qt-Druckdialog ohne Abhängigkeit von einer Windows-PDF-Zuordnung
- direkter Einstieg in den Unterschriftenimport aus der PDF-Analyse

### Changed

- kompaktere Dokumenttitel und sichere, verständliche Standarddateinamen
- größere Liste erkannter Felder und eindeutige leere manuelle Zuordnung
- Menüeinträge ohne überlagernde Tastenkürzel
- restriktivere Beschriftungsanalyse gegen Treffer in Rechtstexten und Fußzeilen

### Fixed

- Drucken schlägt nicht mehr mit Windows-Fehler 1155 fehl
- PDF-Vorschau bleibt bei einer Fenstergrößenänderung vollständig sichtbar
- fehlende Unterschriften führen nicht mehr in einen Sackgassen-Hinweis

### Added

- Produktauftrag, Architektur und ADR-0001 bis ADR-0014
- Roadmap, Feature-Matrix, Versionsplan und umsetzungsfertiger Backlog
- Contribution-, Security-, Privacy-, Lizenz- und Impressumsgrundlagen
- GitHub Issue- und Pull-Request-Templates
- Python-Projekt und PyQt6-App-Shell für `0.1.0-alpha.1`
- lokale, getrennte Datenpfade ohne Administratorrechte
- datenschutzfreundliches, begrenztes Logging mit Maskierung
- About-Dialog mit Version, Edition, Build und Commit
- Tests, Architekturregel, CI und Windows-Build-Prototyp
- flexible lokale Profile mit Kern- und Zusatzfeldern
- Profilübersicht sowie Anlegen, Bearbeiten und Löschen mit Sicherheitsabfrage
- Kalenderauswahl für Geburtsdaten und Schutz vor versehentlichem Jahr 1900
- zwei erziehungsberechtigte Personen und optionale Nachnamenübernahme
- gemeinsames Ortsfeld für Anschrift und späteren Unterschriftsort
- versioniertes Template- und Feldmodell mit PDF-Koordinaten
- lokale Templateverwaltung mit Vertrauensstatus
- sicherer ZIP/PSFS-Import mit Pfad-, Typ- und Größenprüfung
- optionale SHA-256-Prüfsummenprüfung ohne stilles Überschreiben
- schreibgeschützte AcroForm- und Textanalyse für PDFs
- visuelle PDF-Vorschau mit Zoom und Seitenwechsel
- grüne, gelbe und rote Feldrahmen mit zusätzlichen Symbol- und Textstatus
- lokale Feldzuordnung mit nachvollziehbarer Konfidenz
- lokales lernendes Feldlexikon ohne Profilwerte
- manuelle Feldzuordnung direkt in der PDF-Vorschau
- ausdrücklich bestätigtes Lernen neuer Feldbezeichnungen
- JSON-Import und -Export mit Konfliktbericht ohne stilles Überschreiben
- lokale Unterschriftenbibliothek für erziehungsberechtigte Person 1 und 2
- sicherer PNG/JPG-Import mit Größen- und Pixelgrenzen
- automatisches Zuschneiden, Kontrastverbesserung und optionale Weißtransparenz
- bewegliche und per Mausrad skalierbare Unterschriftenbilder in der PDF-Vorschau
- deutliche Abgrenzung von Bildunterschrift und qualifizierter elektronischer Signatur
- visueller, mehrseitiger Template-Designer
- Felder per Maus aufziehen, auswählen und verschieben
- Feldtyp, Datenquelle und Pflichtstatus bearbeiten
- Tastatur-Feinsteuerung sowie Undo/Redo für Anlegen und Löschen
- selbstvalidierende `.psfstemplate`-Pakete mit PDF und SHA-256-Prüfsummen
- lokale Vorschläge für Dokumenttitel, Empfänger und Betreff
- PDF-Arbeitskopien mit eingebetteten Unterschriftenbildern
- bestätigtes Drucken über den Windows-Standarddrucker
- verpflichtende Sicherheitsvorschau vor Speichern, Drucken und E-Mail-Entwurf
- versionierte lokale Backups mit Manifest und SHA-256-Prüfsummen
- Wiederherstellungsvorschau, Konfliktschutz und automatischer Sicherungspunkt
- sichere zufällige Arbeitsverzeichnisse mit Bereinigung nach Nutzung und Programmstart
- deaktiviertes Plugin-Grundgerüst mit Manifest- und Berechtigungsprüfung
- vollständiges deutschsprachiges Benutzerhandbuch
- geprüfte Screenshots für Startseite, Datensicherung und Sicherheitsvorschau
- eigenes App-Icon als SVG, PNG und Windows-ICO
- Windows-Releasepaket mit Buildinformationen
- CycloneDX-Softwarestückliste und SHA-256-Prüfsummen
- lokale `.eml`-Entwürfe mit Sicherheitszusammenfassung statt automatischem Versand
- Verteilerlisten sowie Austauschpakete mit leerem Profil, Anleitung und Repository-Link
