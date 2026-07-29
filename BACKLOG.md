# Umsetzungsbacklog

Jede Aufgabe ist GitHub/Codex-tauglich formuliert. IDs bleiben stabil.

## EPIC-01 Foundation · Milestone 0.1.0-alpha

- **PSFS-001 Repository und Python-Paket initialisieren**  
  Akzeptanz: `src/`-Layout, `pyproject.toml`, Testlauf und Startkommando dokumentiert.
- **PSFS-002 PyQt6 App-Shell erstellen**  
  Akzeptanz: Startseite bietet „Eigenes PDF“ und „Erhaltenes Paket“; Navigation ist tastaturbedienbar.
- **PSFS-003 Konfiguration und lokale Datenpfade**  
  Akzeptanz: getrennte Ordner, keine Schreibrechte im Installationsordner nötig.
- **PSFS-004 Datenschutzkonformes Logging**  
  Akzeptanz: strukturierte Logs, Redaction-Tests für E-Mail, Namen und Pfade.
- **PSFS-005 Build-Metadaten und About-Dialog**  
  Akzeptanz: Version, Edition, Build, Commit, Quelle und Copyright sichtbar.
- **PSFS-006 CI und Release-Prototyp**  
  Akzeptanz: Lint, Typprüfung, Tests, Architekturcheck und Windows-Build.

## EPIC-02 Profiles · Milestone 0.2.0-alpha

- **PSFS-020 Profilschema mit Core/Custom/Runtime-Feldern**
- **PSFS-021 Profilübersicht und Suchfunktion**
- **PSFS-022 Profil neu/bearbeiten/löschen mit Bestätigung**
- **PSFS-023 DatePicker und lokalisierte Datumsvalidierung**
- **PSFS-024 Guardian 1/2 und Nachnamenübernahme**
- **PSFS-025 Sensitivitäts-, Speicher- und Exportregeln**
- **PSFS-026 Profil Import/Export JSON/CSV**

## EPIC-03 Templates · Milestone 0.3.0-alpha

- **PSFS-030 Template JSON Schema**
- **PSFS-031 sicherer Paketimport mit Whitelist**
- **PSFS-032 Koordinaten- und Rotationstransformation**
- **PSFS-033 Templateverwaltung und Vertrauensstufen**
- **PSFS-034 Versionierung und Konfliktvergleich**

## EPIC-04 PDF Analysis · Milestone 0.4.0-alpha

- **PSFS-040 PDF-Worker-Prozess**
- **PSFS-041 AcroForm-Felder extrahieren**
- **PSFS-042 flache PDF-Texte und Linien analysieren**
- **PSFS-043 Qt-Vorschau mit Zoom und Seitenwechsel**
- **PSFS-044 Feldrahmen grün/gelb/rot plus Statussymbol**
- **PSFS-045 Feldliste, Auswahl-Synchronisation und manuelle Zuordnung**

## EPIC-05 Field Dictionary · Milestone 0.5.0-alpha

- **PSFS-050 Alias- und Normalisierungsmodell**
- **PSFS-051 Confidence-Scoring**
- **PSFS-052 bestätigtes lokales Lernen**
- **PSFS-053 Import/Export und Konfliktlösung**
- **PSFS-054 Seed-Lexikon für Schule, Sport und Familie**

## EPIC-06 Signatures · Milestone 0.6.0-alpha

- **PSFS-060 geschützter Signaturspeicher**
- **PSFS-061 PNG/JPG Import und MIME-Prüfung**
- **PSFS-062 Auto-Crop, Kontrast, Weißtransparenz**
- **PSFS-063 verschiebbares/skaliertes GraphicsItem**
- **PSFS-064 Guardian 1/2 einzeln oder gemeinsam**
- **PSFS-065 Signatur-Exportwarnung und Audit-Ereignis**

## EPIC-07 Designer · Milestone 0.7.0-alpha

- **PSFS-070 Rechtecke per Maus anlegen**
- **PSFS-071 Feldtyp und Datenquelle zuordnen**
- **PSFS-072 Pflicht-, Speicher- und Laufzeitregeln**
- **PSFS-073 Tastaturfeinsteuerung, Zoom und Undo/Redo**
- **PSFS-074 Test-PDF und Templatevalidierung**

## EPIC-08 Distribution · Milestone 0.8.0-alpha

- **PSFS-080 Dokumenttitel aus Überschrift/Dateiname vorschlagen**
- **PSFS-081 E-Mail-Adressen und Empfänger vorschlagen**
- **PSFS-082 Betreff und kurze Anleitung erzeugen**
- **PSFS-083 Speichern und Drucken**
- **PSFS-084 systemweiten E-Mail-Entwurf öffnen**
- **PSFS-085 Verteilerlisten verwalten**
- **PSFS-086 Austauschpaket mit leerem Profil erzeugen/importieren**

## EPIC-09 Hardening · Milestone 0.9.0-beta

- **PSFS-090 Sicherheitsvorschau**
- **PSFS-091 Backupformat, Verschlüsselung und Restore**
- **PSFS-092 Schema-Migrationen**
- **PSFS-093 sicherer Modus und Crash Recovery**
- **PSFS-094 Plugin-Manifest, Rechte und Host-Prototyp**
- **PSFS-095 Barrierefreiheit und High-DPI**
- **PSFS-096 Windows-Installer und Upgrade-Test**

## EPIC-10 Release · Milestone 1.0.0

- **PSFS-100 vollständiges Benutzerhandbuch und Screenshots**
- **PSFS-101 PDF-Regression- und Golden-Master-Suite**
- **PSFS-102 Threat Model und Security Review**
- **PSFS-103 Privacy Review und Löschtest**
- **PSFS-104 SBOM, Prüfsummen, Releasebericht**
- **PSFS-105 Lizenztext juristisch finalisieren**

