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

Die Templateverwaltung aus `0.3.0-alpha` ist über **Templates → Templates
verwalten** oder `Strg+T` erreichbar. Importiert werden `.psfstemplate`- oder
ZIP-Pakete nach vollständiger Sicherheitsprüfung. Bestehende Versionen werden
nicht still überschrieben.

Mit `0.4.0-alpha` öffnet **Eigenes PDF bearbeiten** die lokale PDF-Analyse.
AcroForm-Felder und Beschriftungen flacher PDFs erscheinen in einer Vorschau:
grün/✓ für zugeordnet, gelb/⚠ für unsicher und rot/✕ für fehlend. Die Rahmen
gehören nur zur Vorschau und werden nicht in das Original geschrieben.

Ab `0.5.0-alpha` können erkannte Felder direkt manuell zugeordnet werden.
Optional lernt das lokale Feldlexikon die bestätigte Bezeichnung für künftige
Formulare. JSON-Import und -Export enthalten ausschließlich Begriffe und
Zuordnungen – niemals Namen, Adressen oder andere Profilwerte.

`0.6.0-alpha` ergänzt eine lokale Unterschriftenbibliothek für zwei
erziehungsberechtigte Personen. PNG/JPG-Dateien können zugeschnitten, im
Kontrast verbessert und von weißem Hintergrund befreit werden. In der
PDF-Vorschau lassen sie sich mit der Maus verschieben und mit dem Mausrad
skalieren. Es handelt sich um sichtbare Bildunterschriften, nicht um
qualifizierte elektronische Signaturen.

Mit `0.7.0-alpha` öffnet **Templates → Neues Template aus PDF** den visuellen
Designer. Felder werden auf der PDF-Seite mit der Maus aufgezogen, per
Pfeiltasten fein verschoben und einer Datenquelle sowie einem Feldtyp
zugeordnet. Das Ergebnis wird als geprüftes `.psfstemplate`-Paket gespeichert
und lokal installiert.

`0.8.0-alpha` ergänzt Speichern, Drucken und E-Mail-Entwürfe. Titel,
Empfängeradressen und Betreff werden ausschließlich lokal vorgeschlagen und
müssen vor Verwendung geprüft werden. Verteilerlisten bleiben lokal;
Austauschpakete enthalten bewusst ein leeres Profil, keine Unterschrift und
eine kurze Anleitung mit Link zum offiziellen Repository.

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
