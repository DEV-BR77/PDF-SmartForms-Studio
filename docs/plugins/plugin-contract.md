# Plugin-Vertrag

Ein Plugin muss:

- gültiges Manifest und kompatible App-Version besitzen,
- alle Fähigkeiten fein granular deklarieren,
- neue Rechte nach einem Update erneut bestätigen lassen,
- ohne externen Dienst kontrolliert fehlschlagen,
- keine internen Datenbank- oder UI-Objekte importieren,
- Deinstallation ohne ungefragten Datenverlust erlauben,
- Datenzugriff und Netzwerkziele dokumentieren.

Beispiele für Ports: `EmailDraftProvider`, `StorageProvider`, `OcrProvider`, `PrintProvider`.

