# Testbericht 0.9.0-beta.1

Stand: 30. Juli 2026

| Prüfung | Ergebnis |
|---|:---:|
| Ruff | ✅ |
| Black | ✅ |
| mypy strict | ✅ |
| pytest | ✅ 53 Tests |
| Backup-Roundtrip | ✅ |
| manipulierte Backup-Prüfsumme | ✅ blockiert |
| Wiederherstellung mit Konflikt | ✅ vorhandene Datei bleibt erhalten |
| temporäre Arbeitsbereiche | ✅ bereinigt |
| Plugin ohne Ausführung entdecken | ✅ |
| unbekannte Plugin-Berechtigung | ✅ blockiert |
| PyQt6-Offscreen-Smoke-Test | ✅ |
| Windows-PyInstaller-Build | ✅ |

Die bekannten PyMuPDF-SWIG-Deprecation-Warnungen stammen aus einer
Drittbibliothek und beeinträchtigen den Testlauf nicht.
