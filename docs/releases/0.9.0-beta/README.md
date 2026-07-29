# Version 0.9.0-beta – Hardening

## Ziel

Die erste Beta schließt die sicherheitskritischen Benutzerabläufe vor der
Community-Version. Ausgaben benötigen eine bewusste Kontrolle, lokale Daten
lassen sich sichern und konfliktfrei wiederherstellen, temporäre
Arbeitsbereiche werden bereinigt und Plugins bleiben standardmäßig inaktiv.

## Enthalten

- verpflichtende Sicherheitsvorschau vor Speichern, Drucken und E-Mail-Entwurf
- sichtbare Anzahl zugeordneter und offener Felder
- sichtbare Empfänger, Betreff, Anhänge und verwendete Bildunterschriften
- offenes `.psfsbackup`-Format mit Manifest und SHA-256-Prüfsummen
- Wiederherstellungsvorschau und Konflikterkennung
- kein stilles Überschreiben vorhandener Dateien
- automatischer Sicherungspunkt vor jeder Wiederherstellung
- besonders sensible Unterschriften standardmäßig vom Backup ausgeschlossen
- zufällige, anwendungseigene Arbeitsverzeichnisse mit sicherer Bereinigung
- Plugin-Manifest- und Berechtigungsprüfung ohne Ausführung fremden Codes
- Tastaturfokus und zugängliche Beschriftungen für neue Sicherheitsdialoge

## Bewusste Grenzen der Beta

- Backups mit Unterschriften sind noch nicht verschlüsselt und zeigen deshalb
  eine deutliche Warnung. Verschlüsselung ist Voraussetzung für Version 1.0.
- Plugins können nur beschrieben und geprüft, aber noch nicht aktiviert oder
  ausgeführt werden.
- Ein signierter Windows-Installer ist noch nicht Bestandteil der Beta. Der
  reproduzierbare PyInstaller-Build wird weiterhin in der CI geprüft.
- Eine Wiederherstellung ergänzt standardmäßig nur fehlende Dateien. Ein
  gezielter Vergleich und bewusstes Ersetzen einzelner Konflikte folgt später.

## Freigabekriterien

- keine offenen Fehler mit Datenverlust
- alle automatisierten Qualitätsprüfungen erfolgreich
- Backup-Manipulation wird blockiert
- bestehende Daten werden bei Wiederherstellung nicht ungefragt ersetzt
- Sicherheitsvorschau lässt die Aktion erst nach Bestätigung zu
- Windows-Build erfolgreich

Siehe [Testbericht](test-report.md) und [bekannte Einschränkungen](known-issues.md).
