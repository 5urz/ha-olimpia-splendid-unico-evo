# UNICO EVO / Home Assistant – Projektübergabe und bisherige Ansätze

Stand: 19. September 2026; technischer Erkenntnisstand vom 18. September 2026.

Dieses unabhängige Community-Projekt sucht Mitwirkende, die die vorhandene lokale Integration pflegen, weitere Geräte testen oder den Zugang zu den benötigten Geräteschlüsseln vereinfachen möchten. Es besteht keine Verbindung zum Hersteller und keine Unterstützung oder Freigabe durch ihn.

Repository: [ha-olimpia-splendid-unico-evo](https://github.com/5urz/ha-olimpia-splendid-unico-evo). Die bestehende Integration ist öffentlich und unter MIT lizenziert. Forks und Weiterentwicklung sind unter den dortigen Lizenzbedingungen möglich. Diese Übergabe überträgt weder die Repository-Verwaltung noch Rechte an fremder Software.

## Ergebnis und eigentliche Hürde

Die lokale Steuerung eines UNICO EVO 25 HP PVAN, Produktcode 02455, ist im Projekt dokumentiert. Home Assistant kommuniziert über TinyTuya und Tuya LAN 3.4 mit dem eingerichteten Gerät. Dafür werden Host/IP-Adresse, Device ID und Local Key benötigt. Die Integration ruft im normalen Betrieb keine Hersteller-Cloud auf. Daraus folgt nicht, dass die Klimaanlage selbst keine Internetverbindungen aufbaut.

Die zentrale ungelöste Aufgabe ist die einfache, reproduzierbare Beschaffung dieser Zugangsdaten. Ein technisch funktionierender Expertenweg über die laufende OS-Home-App ist vorhanden. Eine Einrichtung für beliebige Nutzer ohne spezielle Android-Vorbereitung ist bislang nicht nachgewiesen.

Die Funktionsangaben beruhen auf dem bestehenden Repository und dokumentierten früheren Gerätetests. Für diese Übergabe wurden keine neuen Hardwaretests durchgeführt. Andere Modelle bleiben unbestätigt.

## Ansätze, Ergebnisse und Gründe für den Wechsel

| Ansatz | Ergebnis | Grenze / Grund für das Zurückstellen |
|---|---|---|
| Lokale Steuerung mit TinyTuya / Tuya LAN 3.4 | Tragfähige Grundlage; Climate, Schalter und Sensoren für das Referenzmodell dokumentiert. | Weitere Modelle, längere Stabilitätstests und Wiederanlauf nach Netz-/Geräteausfällen bleiben Aufgaben. Dieser Ansatz wurde nicht aufgegeben. |
| GitHub und HACS | Öffentliche Beta vorhanden; Installation als HACS-Custom-Repository dokumentiert. | Kein Nachweis einer Aufnahme in die HACS-Standardliste. Öffentliche Verfügbarkeit löst die Einrichtungshürde nicht. |
| Bestehende Integration für ältere UNICO-Geräte | Hilfreich als Vergleich und Vorarbeit. | Ältere B1015-/WLAN-Plattform unterscheidet sich vom hier verwendeten Tuya-System; kein unmittelbar übertragbarer Zugang. |
| OS Comfort / Midea-basierte Lösungen | Architekturvergleich für einmalige Einrichtung und anschließenden lokalen Betrieb. | Anderer Protokoll-/Backendpfad; keine im Projekt bestätigte Lösung für OS Home. |
| DeviceBean-Auslesen mit Frida | Geräte-ID und Local Key konnten laut Entwicklungsdokumentation aus dem eigenen angemeldeten App-Kontext gelesen werden. | Root-/Instrumentierungsaufbau, App-Versionen und Fehlerbehebung machen den Weg für normale Nutzer aufwendig. |
| Neuer UNICO-Key-Helfer 0.1 | Lokaler Testkandidat mit Geräteauswahl, Versionsprüfung, begrenztem Leseablauf und Kopierfeldern vorbereitet. | Automatisierte Tests mit künstlichen Daten sind dokumentiert; echter Gerätetest, erfolgreicher HA-Import und unabhängiger Nutzertest stehen aus. Root/Frida wird weiterhin vorausgesetzt. |
| Netzwerk- und BLE-Mitschnitte; breite Laufzeit-Hooks | Transport und Teile der Abläufe wurden sichtbar. | Mehr Traces ergaben nicht automatisch einen nutzbaren Einrichtungsweg. Breite Hooks verursachten teilweise Instabilität. |
| Android-Emulator | Für App-/Objektanalyse und den dokumentierten Schlüsselzugang hilfreich. | Der reale BLE-/WLAN-Ersteinrichtungsablauf war im damaligen Aufbau nicht reproduzierbar; hierfür wurde physische Android-Hardware verwendet. |
| Eigenes BLE-Onboarding | Teile des Transport- und Protokollablaufs wurden beobachtet bzw. statisch rekonstruiert. | Kein vollständig eigener Ablauf vom unkonfigurierten Gerät bis zur bestätigten LAN-Steuerung nachgewiesen. Der untersuchte Herstellerablauf bezieht außerdem Cloud-Werte ein. |
| Private OS-Home-Cloud-Aufrufe | Projektanalysen fanden zusätzliche appgebundene Signierungsabhängigkeiten neben der Benutzeranmeldung. | Kein belegter einfacher, unabhängig autorisierter Zugang ausschließlich mit Benutzerkonto/OTP. Übernahme fremder App-Geheimnisse ist kein Projektziel. |
| Eigener Tuya-Client / eigene App | Eigener Zugang wurde untersucht. | Eigene App-Credentials vermitteln nicht automatisch Zugriff auf Geräte eines OS-Home-Kontos. |
| Offizielles OAuth / Device Data Sharing | Offizielle Freigabemechanismen wurden untersucht. | Im getesteten OAuth-Kontext war die Ziel-App nicht freigeschaltet; ein weiterer Sharing-Test wurde vor Abschluss beendet. Nicht allgemein widerlegt, aber kein funktionierender OS-Home-Schlüsselzugang nachgewiesen. |

## Was bei der Fortsetzung nicht verwechselt werden darf

- Funktionierende lokale Steuerung ist nicht gleich einfache Erstinstallation.
- Ein gelesener Schlüssel muss durch eine echte lokale HA-Verbindung bestätigt werden.
- Zugriff auf Geräteinformationen oder Cloud-Steuerung beweist nicht, dass ein Local Key verfügbar ist.
- Schlüsselabruf für ein bereits bekanntes Gerät löst nicht automatisch die Erstaktivierung eines neuen Geräts.
- Statische Analyse und synthetische Tests belegen keinen erfolgreichen Ablauf auf der Gerätefirmware.
- Die Untersuchung mehrerer App-Versionen darf nicht zu einem vermeintlich einheitlichen Protokollstand zusammengezogen werden.

Frühere interne Zusammenfassungen wurden durch spätere Analysen teilweise korrigiert. Insbesondere wurden Protokollzweige und bedingte Paketlängen zeitweise zu pauschal beschrieben. Die alten Arbeitsstände sind deshalb kein unverändert gültiger Implementierungsvertrag. Detaillierte, durch Dekompilierung ermittelte Spezifikationen sind nicht Bestandteil dieser öffentlichen Übergabe.

## Sinnvolle nächste Arbeiten

1. **Vorhandene LAN-Integration stabilisieren:** Wiederanlauf bei Netzwerk-/Geräteneustarts, Langzeitbetrieb und klar abgegrenzte Kompatibilitätstests.
2. **Schlüsselübernahme prüfen:** Den vorbereiteten Helfer am bekannten Aufbau testen, danach einen unabhängigen Nutzer ausschließlich nach Anleitung arbeiten lassen. Erfolg ist erst die bestätigte HA-Verbindung. Aufwand für Root/Frida zählt zum Gesamtaufwand.
3. **Offiziellen Zugang klären:** Prüfen, ob eine vom Plattform-/App-Betreiber autorisierte Freigabe tatsächlich den benötigten Local Key zugänglich macht. Ein erfolgreicher Login allein reicht nicht.
4. **Forschung begrenzen:** Weitere BLE-/Cloud-Arbeit erst mit einer konkreten überprüfbaren Frage beginnen, deren Antwort eine Produktentscheidung verändert.

Wenn der vereinfachte Schlüsselzugang weiterhin individuelle Android-/Frida-Betreuung benötigt, bleibt die Integration eine Expertenlösung. Ein komfortables oder vollständig cloudfreies Onboarding wird nicht zugesagt.

## Datenschutz und Beiträge

Für einen Kompatibilitätsbericht genügen zunächst Modell/Produktcode, Softwareversionen, getestete Funktionen und ein bereinigter Fehlercode. Keine Seriennummern, Geräte-IDs, Local Keys, Kontodaten, MAC-Adressen, WLAN-Namen, Tokens oder vollständigen Diagnose-/Trace-Dateien veröffentlichen. Auch stabile Hashes und verkürzte Kennungen können wiedererkennbar bleiben.

Das vorhandene Frida-Konsolenskript gibt Zugangsdaten aus. Seine Ausgabe ist kein öffentlich teilbares Protokoll. Der neue Helfer hält Werte lokal vor; Screenshots, Zwischenablageverlauf und Synchronisierung können sie trotzdem weitergeben. Home-Assistant-Konfiguration und Backups können die Zugangsdaten enthalten.

Diese Übergabe enthält keine Hersteller-App, extrahierten Programmcode, echten Schlüssel, Gerätemitschnitte oder privaten Chatverläufe. Forschung ist auf eigene beziehungsweise ausdrücklich autorisierte Geräte und Konten zu beschränken.

## Einstieg für Mitwirkende

- [Projektbeschreibung und Installation](https://github.com/5urz/ha-olimpia-splendid-unico-evo/blob/main/README.md)
- [Bisheriger Forschungsbericht](https://github.com/5urz/ha-olimpia-splendid-unico-evo/blob/main/RESEARCH.md)
- [Bestehende Anleitung zur Schlüsselbeschaffung](https://github.com/5urz/ha-olimpia-splendid-unico-evo/blob/main/docs/GETTING_KEYS.md)
- [Lizenz](https://github.com/5urz/ha-olimpia-splendid-unico-evo/blob/main/LICENSE) und [Drittanbieterhinweise](https://github.com/5urz/ha-olimpia-splendid-unico-evo/blob/main/THIRD_PARTY_NOTICES.md)
- [Sicherheitsmeldungen](https://github.com/5urz/ha-olimpia-splendid-unico-evo/blob/main/SECURITY.md)

Der separate Key-Helfer 0.1 ist zum Zeitpunkt dieser Übergabe als lokaler Testkandidat vorbereitet; eine Veröffentlichung oder Verfügbarkeit im Repository wird hier nicht behauptet.
