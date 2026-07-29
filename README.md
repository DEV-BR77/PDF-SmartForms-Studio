# PDF SmartForms Studio

Lokale, modulare Desktop-Anwendung zum Analysieren, Zuordnen, Ausfüllen, Signieren, Prüfen und Verteilen von PDF-Formularen.

> Status: Produkt- und Architekturgrundlage abgeschlossen; Implementierung startet mit `0.1.0-alpha`.

## Leitgedanken

- Privacy by Design: lokale Verarbeitung, keine Telemetrie, keine automatische Cloud-Übertragung.
- Human in the Loop: Erkennungsergebnisse sind Vorschläge und werden vor Export oder E-Mail bestätigt.
- Modularer Kern: PDF, Profile, Templates, Feldlexikon, Signaturen und Export sind getrennte Domänen.
- Sichere Erweiterbarkeit: externe Systeme werden ausschließlich über freigegebene Provider/Plugins angebunden.
- Offene Datenformate: Profile, Templates, Backups und Lexika bleiben portabel.

## Erste Schritte für Mitwirkende

1. [Projektauftrag](docs/PROJECT.md) lesen.
2. [Architektur](docs/architecture/architecture.md) und [ADRs](docs/adr/README.md) prüfen.
3. Eine Aufgabe aus [BACKLOG.md](BACKLOG.md) wählen.
4. [CONTRIBUTING.md](CONTRIBUTING.md) und die Definition of Done beachten.
5. Gegen den Meilenstein `0.1.0-alpha` implementieren.

## Entwicklung starten

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pdf-smartforms
```

Qualitätsprüfung:

```powershell
ruff check .
black --check .
mypy
pytest
```

Windows-Build:

```powershell
.\build_windows.ps1
```

## Aktueller Entwicklungsstand

Die Profilverwaltung aus `0.2.0-alpha` ist über **Profile → Profile verwalten**
oder `Strg+P` erreichbar. Sie unterstützt zwei erziehungsberechtigte Personen,
Kalenderauswahl, flexible Zusatzfelder und lokales JSON.

## Repositories

- Anwendung: `DEV-BR77/PDF-SmartForms-Studio`
- Standards: `DEV-BR77/BR-Development-Framework`
- Projektvorlage: `DEV-BR77/BR-Project-Template`
- Formularvorlagen: `DEV-BR77/PDF-SmartForms-Templates`
- Plugins/SDK: `DEV-BR77/PDF-SmartForms-Plugins`
- Feldlexikon: `DEV-BR77/PDF-SmartForms-FieldDictionary`

Verbindliche gemeinsame Standards liegen im BR Development Framework. Projektspezifische Abweichungen benötigen eine ADR.

## Nutzung und Recht

Copyright © Björn Radke. Der geplante Lizenztyp ist **Source Available**. Kostenlose Nutzung ist für private Zwecke, Bildung sowie Sport- und gemeinnützige Organisationen vorgesehen. Kommerzielle Nutzung benötigt eine separate Vereinbarung. Vor einer öffentlichen Veröffentlichung ist der endgültige Lizenztext juristisch zu prüfen.
