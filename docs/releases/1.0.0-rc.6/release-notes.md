# PDF SmartForms Studio 1.0.0-rc.6

## Schwerpunkt

Die Analyseansicht folgt nun ebenfalls dem klaren Drei-Spalten-Modell und unterstützt
neue Profilfelder ohne manuelle JSON-Bearbeitung.

## Bedienung

- links: erkannte Felder, Statusfarben und Zusammenfassung
- Mitte: große PDF-Vorschau
- rechts: Profil, Zuordnung, Lexikon, Unterschrift und Ausgabe
- das ausgewählte Feld erhält in der Vorschau einen blauen Fokusrahmen
- die rechte Spalte kann unabhängig gescrollt werden

## Neue und unbekannte Felder

Bei einem roten Feld kann „Neues Profilfeld für diese Angabe“ gewählt werden. Danach:

1. Bezeichnung bestätigen,
2. Wert für das ausgewählte Profil eingeben,
3. Profilfeld, Lexikoneintrag und aktuelle Zuordnung werden gemeinsam gespeichert.

Importierte Lexikonquellen und vorhandene benutzerdefinierte Profilfelder erscheinen
automatisch in der Auswahlliste.

## Festnetz und Mobiltelefon

`contact.phone` und `contact.mobile` sind getrennte Profilwerte. Bestehende lokale
Lexika werden kompatibel migriert:

- `contact.mobil` wird zu `contact.mobile`
- „mobil“, „mobiltelefon“, „handy“ und „handynummer“ werden dem Mobiltelefon zugeordnet

Bei abweichenden importierten Zuordnungen fragt die Anwendung vor dem Ersetzen nach.

## Kompatibilität

Vorhandene Profile bleiben lesbar. Das neue Mobilfeld ist bei älteren Profilen zunächst
leer und kann beim nächsten Bearbeiten ergänzt werden.
