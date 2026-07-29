# Zielarchitektur

```text
PyQt6 UI
  ↓
Application Services / Use Cases
  ↓
Domain Core
  ↑
Infrastructure Adapters
  ↑
Isolated Workers / Plugin Host
```

## Module

```text
src/pdf_smartforms/
├── domain/              # Entitäten, Regeln, Ports
├── application/         # Anwendungsfälle
├── pdf/                 # Analyse, Rendering, Export
├── profiles/            # Kern- und benutzerdefinierte Felder
├── templates/           # Template-Schema und Designer
├── field_dictionary/    # Aliase, Konfidenz, Lernvorgänge
├── signatures/          # Bildimport und Platzierung
├── distribution/        # Verteilerlisten und Pakete
├── plugins/             # Manifest, Rechte, Host
├── infrastructure/      # Dateisystem, Schlüsselspeicher
└── ui/                  # PyQt6
```

## Abhängigkeitsregeln

- `domain` importiert weder PyQt6 noch konkrete PDF-, Mail- oder Cloud-Bibliotheken.
- `ui` enthält keine PDF-Geschäftslogik.
- Plugins erhalten ausschließlich explizite Fähigkeiten.
- PDF, OCR, Vorschau und Community-Plugins laufen perspektivisch in Worker-Prozessen.
- Ein defektes Plugin darf den Anwendungskern nicht blockieren.

## Zentrale Domänenobjekte

- `Profile`, `ProfileField`, `SensitiveValue`
- `Template`, `TemplateField`, `FieldMapping`
- `DetectedField`, `MatchSuggestion`, `Confidence`
- `SignatureAsset`, `SignaturePlacement`
- `GeneratedDocument`, `EmailDraft`
- `DistributionList`, `ExchangePackage`
- `PluginManifest`, `PermissionGrant`

## Technologierichtung

- Python 3.12+
- PyQt6
- PyMuPDF für Rendering/Textanalyse
- pypdf für AcroForm-nahe Verarbeitung
- Pillow für Signaturbilder
- pytest, Ruff, Black, mypy/pyright
- PyInstaller oder vergleichbarer Windows-Build

