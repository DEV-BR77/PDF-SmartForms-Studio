# PDF SmartForms Studio 1.0.0-rc.4

Dieser private Release Candidate schließt die Lücke zwischen Feldanalyse,
Profilverwaltung, Vorschau und tatsächlicher PDF-Ausgabe.

## Profilwerte

- Das gewünschte Profil wird direkt in der PDF-Analyse ausgewählt.
- Zugeordnete Werte erscheinen sofort innerhalb der erkannten Formularzellen.
- Dieselben Werte werden beim Speichern, Drucken und Erstellen eines E-Mail-Entwurfs
  in die PDF geschrieben.
- Teilnehmer- und Erziehungsberechtigtendaten werden getrennt zugeordnet.

## Feldrahmen

- Tabellenlinien begrenzen die erkannten Eingabezellen exakt.
- Kleine Fußzeilen, Kontaktdaten und Überschriften wie „Datenschutz“ werden nicht mehr
  als Eingabefelder vorgeschlagen.
- Falsche Vorschläge können weiterhin über „Erkennung entfernen“ entfernt werden.

## Unterschriften

- Neue Unterschriften werden zunächst im erkannten Unterschriftsbereich abgelegt.
- Eine Unterschrift wird direkt in der Vorschau ausgewählt.
- Der Größenregler reagiert unmittelbar.
- „Ausgewählte Unterschrift löschen“ entfernt eine versehentlich oder mehrfach
  eingefügte Unterschrift.

## Dokumenttitel und Drucken

- Der sichtbare Formulartitel wird gegenüber ungeeigneten internen PDF-Metadaten bevorzugt.
- Drucken beginnt mit einer anwendungsinternen Seitenvorschau.

## Prüfung

- automatisierte Tests für Profildaten, PDF-Ausgabe, Tabellenkoordinaten,
  Unterschriftenskalierung, Löschen und Dokumenttitel
- Sichtprüfung des gerenderten WOLLINO-Originalformulars
- vollständige Qualitäts-, Typ- und Windows-Buildprüfung
