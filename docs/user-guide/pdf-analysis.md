# PDF-Analyse und Feldzuordnung

Die Analyse liest vorhandene AcroForm-Felder und versucht bei flachen PDFs
Beschriftungen zu erkennen. Eingebettetes JavaScript wird nicht ausgeführt.

| Anzeige | Bedeutung | Aktion |
|---|---|---|
| Grün / ✓ | sicher zugeordnet | Wert prüfen |
| Gelb / ⚠ | unsicher | Zuordnung bestätigen |
| Rot / ✕ | kein Profilfeld gefunden | zuordnen, neu anlegen oder leer lassen |

Farbe ist nie das einzige Signal; Liste und Statussymbol zeigen denselben
Zustand. Beim Anklicken eines Eintrags wird das Feld in der Vorschau
hervorgehoben.

## Profilwerte prüfen

Oben rechts wird das Profil für Vorschau und Ausgabe ausgewählt. Zugeordnete
Werte werden innerhalb der grünen Feldrahmen angezeigt. Dadurch ist vor dem
Speichern erkennbar, welcher Wert an welcher Position ausgegeben wird.

Ein Vorschlag, der gar kein Formularfeld ist, kann in der Feldliste markiert
und über **Erkennung entfernen** aus der aktuellen Analyse gelöscht werden.

## Lernendes Feldlexikon

Eine bestätigte Zuordnung kann lokal in das Feldlexikon übernommen werden.
Dabei wird nur die Feldbezeichnung mit der Datenquelle gespeichert – keine
Namen, Adressen oder Profilwerte. Lexika können als JSON importiert und
exportiert werden; Konflikte werden angezeigt und nicht still überschrieben.
