# Olimpia Splendid UNICO – Home Assistant Custom Integration v0.4.8

Lokale Home-Assistant-Integration für den getesteten **Olimpia Splendid UNICO EVO 25 HP PVAN (02455)** über Tuya LAN 3.4.

> **Unofficial community project:** This project is not affiliated with, endorsed by, or supported by Olimpia Splendid S.p.A.

## Status

Diese Version ist ein **früher öffentlicher Entwicklungsstand / Public Beta**.

Bisher hauptsächlich getestet mit:

- **Olimpia Splendid UNICO EVO 25 HP PVAN**
- interner Gerätecode **02455**
- lokaler Kommunikation über **Tuya LAN 3.4**

### Modell-Kompatibilität

- **Getestet:** UNICO EVO 25 HP PVAN (02455)
- **Wahrscheinlich kompatibel:** aktuelle **OS Home**-Modelle der Reihen UNICO EVO, UNICO NEXT und UNICO PRO
- **Experimentell:** UNICO VERTICAL / VERTICAL-NK
- **Nicht kompatibel:** ältere Geräte mit dem WLAN-Nachrüstmodul **B1015** bzw. der früheren UNICO-WLAN-Plattform

Die Einschätzung für weitere Modelle basiert auf der gemeinsamen OS-Home-/Tuya-Plattform und bekannten ähnlichen Datenpunkt-Schemata. Sie ist keine Garantie; außer dem 02455 wurden diese Modelle mit dieser Integration bislang nicht praktisch verifiziert.

## Unterstützte Funktionen

- Ein / Aus
- Kühlen / Heizen / Automatik / Entfeuchten / Nur Lüften
- Solltemperatur und aktuelle Raumtemperatur
- Lüfter Auto / Niedrig / Mittel / Hoch
- Oszillation
- Eco / Silent / Eco + Silent
- Diagnose- und interne Sensordaten
- lokale Statusabfrage und Wiederverbindungslogik

## Device ID, Local Key und Datenschutz

Für die lokale Verbindung benötigt die Integration IP-Adresse, **Device ID** und **Local Key** des eigenen UNICO. Device ID und Local Key müssen derzeit vom Benutzer selbst ermittelt werden. Eine Schritt-für-Schritt-Beschreibung befindet sich in [`docs/GETTING_KEYS.md`](docs/GETTING_KEYS.md); das experimentelle Frida-Hilfsskript liegt unter `tools/oshome_key.js`.

> [!WARNING]
> Der Local Key ist ein Zugangsschlüssel zum eigenen Gerät. **Device ID und Local Key nicht in Issues, Logs, Screenshots oder Foren veröffentlichen.** Die Anleitung ist ausschließlich für den eigenen Account und das eigene Gerät gedacht.

Die Integration speichert Device ID und Local Key im normalen Home-Assistant-Config-Entry, weil beide Werte für die lokale Tuya-Kommunikation benötigt werden. Home-Assistant-Konfigurationsdateien unter `.storage/` und vollständige Konfigurations-Backups können daher Zugangsdaten enthalten. Diese Dateien nicht veröffentlichen oder an Issues anhängen und Backups geschützt bzw. verschlüsselt aufbewahren.

In Home-Assistant-Geräte-Identifiern und Entity-Unique-IDs verwendet die Integration statt der echten Device ID einen stabilen SHA-256-basierten Fingerprint. Diagnosedaten redigieren Host, Device ID und Local Key.

**Debug-Hinweis:** Rohes TinyTuya-Debug-Logging kann Protokoll- und Gerätedaten enthalten. TinyTuya-Debug-Logs deshalb niemals ungeprüft veröffentlichen; vor dem Teilen immer auf IP-Adressen, Device IDs, Local Keys, Tokens und andere Zugangsdaten prüfen und diese redigieren.

## Installation

### Manuelle Installation

1. Dieses Repository herunterladen oder klonen.
2. `custom_components/olimpia_unico/` nach `/config/custom_components/olimpia_unico/` kopieren.
3. Home Assistant vollständig neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen.
5. Nach **Olimpia Splendid UNICO** suchen.
6. IP-Adresse, Device ID und Local Key eintragen.
7. Die Integration prüft anschließend die lokale Verbindung zum Gerät.

### Upgrade

Bei einem Upgrade den vorhandenen Ordner `/config/custom_components/olimpia_unico/` durch die neue Version ersetzen und Home Assistant anschließend neu starten. Der bestehende Config-Eintrag kann normalerweise erhalten bleiben. Für den normalen Betrieb ist **kein Debug-Logging** erforderlich.

## Netzwerk-Hinweis

Da die Integration lokal mit der IP-Adresse des Geräts arbeitet, ist eine **DHCP-Reservierung** im Router empfehlenswert.

## Entstehung der Integration

Diese Integration ist im Rahmen eines privaten Reverse-Engineering-Projekts entstanden. Die Analyse, Entwicklung und schrittweise Umsetzung wurden gemeinsam mit **ChatGPT** durchgeführt. Ziel war eine vollständig lokale Home-Assistant-Anbindung ohne Abhängigkeit von der Hersteller-Cloud im laufenden Betrieb.

Zur Untersuchung wurden unter anderem Android Studio / Android Emulator, Magisk / rootAVD, ADB, Frida / frida-server, das ThingClips/Tuya-SDK, TinyTuya sowie Home-Assistant-Debug-Logs und praktische Funktionstests am eigenen Gerät verwendet.

Die Integration basiert **nicht auf einer offiziellen API oder offiziellen Protokolldokumentation von Olimpia Splendid**. Es werden keine APK-Dateien oder proprietären Herstellerdateien mit diesem Projekt verteilt.

## Vorarbeiten und Danksagung

Ein wichtiger Ausgangspunkt und eine Referenz war die vorhandene Home-Assistant-Integration von **Daneel87 / Davide Melle**. Auf dem für dieses Projekt verwendeten UNICO EVO 25 HP PVAN (02455) konnte diese vorhandene Integration jedoch keine funktionierende Kommunikation herstellen, weshalb die Untersuchung unabhängig weitergeführt wurde.

Repository der Vorarbeit: `Daneel87/ha-olimpia-splendid-unico` auf GitHub. Hinweise zu übernommenen bzw. als Referenz verwendeten Drittarbeiten und deren Lizenz befinden sich in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Geplante BLE-Einrichtung

Der größte derzeitige Nachteil ist die manuelle Ermittlung von Device ID und Local Key. Langfristig soll geprüft werden, ob BLE-Erkennung und Provisionierung direkt aus Home Assistant möglich sind. Diese BLE-basierte Einrichtung ist **noch nicht implementiert**.

## Diagnose-DPS

| DP | Entitätsname | Einheit | Status |
|---:|---|---|---|
| 101 | Außen-/Ansauglufttemperatur (DP101, unsicher) | °C | unsicher |
| 102 | Innenwärmetauschertemperatur (DP102) | °C | hohe Sicherheit |
| 103 | Außenwärmetauschertemperatur (DP103) | °C | hohe Sicherheit |
| 104 | Kompressor-/Heißgastemperatur (DP104, unsicher) | °C | unsicher |
| 105 | Kompressorfrequenz (DP105) | Hz | sehr hohe Sicherheit |
| 107 | Expansionsventil-Position (DP107, unsicher) | steps | unsicher |
| 110 | Innenlüfterdrehzahl (DP110) | rpm | sehr hohe Sicherheit |
| 111 | Außenlüfterdrehzahl (DP111, unsicher) | rpm | wahrscheinlich |
| 115 | Diagnosewert DP115 (unbekannt) | – | unbekannt |
| 117 | Diagnosewert DP117 (unbekannt) | – | unbekannt |

## Bekannte Grenzen

- bisher nur ein Gerätemodell intensiv getestet
- Device ID und Local Key müssen noch manuell ermittelt werden
- BLE-Onboarding noch nicht implementiert
- keine offizielle Hersteller-API
- interne Diagnose-DPS teilweise noch nicht eindeutig zugeordnet

## Disclaimer

This is an unofficial, community-developed Home Assistant integration and is not affiliated with, endorsed by, or supported by Olimpia Splendid.

The integration was developed through independent analysis and reverse engineering of communication used by the official OS Home application, with the goal of achieving interoperability and local control of the user's own device. Users are responsible for ensuring that their use of the reverse-engineering instructions complies with applicable law and with any terms applicable to software or services they use.

No source code, APK files, credentials, device keys, or other proprietary files from Olimpia Splendid are distributed with this project. Users are responsible for obtaining and using credentials only for devices and accounts they are authorized to access.

This software is provided without warranty. Use it at your own risk. Product names, company names, trademarks, and logos belong to their respective rights holders and are used only for identification and compatibility-description purposes.

## Lizenz und Markenhinweis

Der in diesem Repository entwickelte Quellcode steht unter der **MIT License**. Siehe [`LICENSE`](LICENSE). Die Projektlizenz gewährt **keine Rechte an Marken, Logos, Produktnamen oder sonstigen Kennzeichen Dritter**. Hinweise und Lizenztexte zu Drittarbeiten befinden sich in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

**Olimpia Splendid**, **UNICO**, **OS Home** und weitere genannte Produkt- oder Markennamen sind Marken bzw. Kennzeichen ihrer jeweiligen Rechteinhaber. Ihre Nennung dient ausschließlich der Beschreibung der Kompatibilität dieses unabhängigen Projekts. Das Repository verwendet bewusst **kein offizielles Olimpia-Splendid-Logo**; das enthaltene HVAC-Symbol ist ein eigenständig erstelltes, neutrales Projekt-Icon.
