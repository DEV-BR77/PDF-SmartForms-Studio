# Backup, Restore und Migration

Das Backupformat `.psfsbackup` ist ein dokumentierter Container mit:

- `manifest.json`
- versionierten Datenbereichen
- `checksums.json`
- optionaler Verschlüsselung

Vor Restore: Integrität prüfen, Inhalt/Vorschau anzeigen, Konflikte einzeln lösen und Wiederherstellungspunkt erstellen. Vor jeder Schema-Migration wird ein Backup erzeugt. Migrationen sind versioniert, wiederholbar und mit alten Fixtures getestet. Tokens des Betriebssystem-Schlüsselspeichers werden bei Rechnerwechsel nicht übertragen.

