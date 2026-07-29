# Bedrohungsmodell

## Schutzwerte

Profile, Unterschriften, erzeugte PDFs, Zugangstokens, Lizenzdaten, Unternehmensvorlagen und Plugin-Berechtigungen.

## Vertrauensgrenzen

- importierte PDFs und Pakete
- Community-Templates und -Plugins
- Worker-Prozesse
- Betriebssystem-Mailprogramm/Drucker
- optionale Netzwerkdienste

## Hauptrisiken und Kontrollen

| Risiko | Kontrolle |
|---|---|
| manipuliertes PDF | keine aktiven Inhalte, isolierter Worker, Größenlimits |
| Pfadtraversierung im Paket | kanonische Zielprüfung, Whitelist |
| schädliches Plugin | Manifest, Rechte, Isolation, Standard aus |
| Daten in Logs | zentrale Redaction und Tests |
| Signaturabfluss | geschützter Speicher, Export standardmäßig aus |
| falscher Empfänger | Entwurf statt Versand, Sicherheitsvorschau |
| manipuliertes Update | offizielle Quelle, Prüfsumme, Signatur |
| Migration/Datenverlust | Vorab-Backup, Transaktion, Rollback |

