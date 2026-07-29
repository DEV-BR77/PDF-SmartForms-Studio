# Installation unter Windows

## Offizielles Release

1. Das gewünschte Release im privaten beziehungsweise offiziellen
   GitHub-Repository öffnen.
2. `PDF-SmartForms-Studio-<Version>-Windows.zip` herunterladen.
3. Die veröffentlichte SHA-256-Prüfsumme mit `SHA256SUMS.txt` vergleichen.
4. ZIP-Datei in einen eigenen Ordner entpacken.
5. `PDF-SmartForms-Studio.exe` starten.

Die Anwendung benötigt keine Administratorrechte. Windows kann bei einem noch
nicht codesignierten Vorab-Build einen Sicherheitshinweis anzeigen. Nur
Artefakte aus dem offiziellen Repository verwenden.

## Start aus dem Quellcode

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pdf-smartforms
```

Unterstützt wird zunächst Windows 11 mit Python 3.12.

## Lokale Daten

Anwendungsdaten liegen im benutzereigenen lokalen Datenverzeichnis. Über
**Daten → Datensicherung und Wiederherstellung** können sie exportiert werden.
Das Programm schreibt nicht ungefragt in Systemordner.
