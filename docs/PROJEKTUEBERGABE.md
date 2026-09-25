# Projektabschluss und Wiederaufnahme – Stand 25.09.2026

**Die Entwicklung ruht.** Das Repository bleibt als unabhängiges Community-Projekt, Dokumentation und Ausgangspunkt für Forks verfügbar. Regelmäßige Wartung, Antworten oder neue Funktionen werden nicht zugesagt.

## Erreichtes Ergebnis

Die Home-Assistant-Integration bleibt bei Version 0.4.9. Lokale Steuerung über TinyTuya 1.20.0 / Tuya LAN 3.4 ist für UNICO EVO 25 HP PVAN (02455) dokumentiert. Benötigt werden Host/IP, Device ID und Local Key. Die Integration selbst benötigt im normalen Betrieb keinen Hersteller-Cloudzugriff; dies behauptet keine vollständige Cloudfreiheit des Geräts oder seiner Ersteinrichtung.

Am 25.09.2026 bestätigte der Maintainer mit Helfer **0.1.1** READ_OK für ein Gerät und anschließend erfolgreiches Hinzufügen in HA. Aufbau: gerootetes Samsung SM-T585, OS Home 2.0.3, Frida 16.7.19 auf PC und Tablet, frida-tools 13.7.1. Dies ist ein Erfolg auf dem bekannten Aufbau, kein unabhängiger Nutzbarkeitstest.

Der aktuelle veröffentlichte Helferquellstand **0.1.2** lässt den Nutzer den Lesezeitpunkt bestätigen. Er ist lokal geprüft, aber noch nicht erneut am Tablet getestet. Die erfolgreiche 0.1.1-Einrichtung ist kein Hardwaretest von 0.1.2.

## Der entscheidende Frida-Befund

Am SM-T585 scheiterte das Anhängen an eine laufende OS-Home-PID mit ATTACH_FAILED. Funktionierender Weg: OS Home per ADB force-stop beenden, dann über die ausgewählte Frida-Geräte-ID und den Paketnamen `com.olimpiasplendid.oshome` selbst spawnen, Reader vor Resume laden. Kein PID-Attach als Voraussetzung.

0.1.1 scannte nach 20 Sekunden und beendete die Frida-Kommandozeile nach etwa 30 Sekunden. Das war für das langsame Tablet zu knapp. Trotz erfolgreichem Lesen blieb offen, ob die App später abstürzte oder beim Trennen von Frida Probleme hatte. READ_OK ist kein App-Stabilitätsnachweis.

0.1.2 startet denselben Spawn-Pfad, wartet auf „Seite geladen – jetzt lesen“ und beendet danach die Frida-Verbindung. Es gibt Abbruch und getrennte Start-/Warte-/Scan-Zeitlimits. Der technische Status nennt den manuellen Auslöser und das Sitzungsende, stellt aber ausdrücklich keinen überprüften App-Zustand nach dem Lesen dar.

## Ansätze und Grenzen

| Ansatz | Ergebnis und Entscheidung |
|---|---|
| Lokale HA-Steuerung | Funktionierende Grundlage beibehalten. Climate, Eco/Silent, Swing, Display und Sensoren für ein Referenzmodell dokumentiert. |
| Ältere UNICO/B1015-Integration | Relevante Vorarbeit, aber andere Kommunikationsplattform; am Referenzgerät kein passender Weg. |
| OS Comfort/Midea | Architekturvergleich, kein übertragbarer OS-Home-Zugang belegt. |
| Android-Emulator | Für Objektanalyse/älteren Schlüsselweg hilfreich; damaliges reales BLE/WLAN-Onboarding nicht reproduziert. |
| Frida/DeviceBean | Praktischer Expertenweg; Root und Versionsabhängigkeiten bleiben die Nutzerhürde. |
| App-Datenimport | Kein einfacher Schlüsselimport aus dem untersuchten Archiv gefunden; keine allgemeine Unmöglichkeit bewiesen. |
| Breite Traces/Hooks | Teilweise instabil; mehr Beobachtungen ergaben nicht automatisch ein Produkt. |
| Eigenes BLE-Onboarding | Wesentliche Teile statisch untersucht, aber kein kompletter unabhängiger Ablauf bis zur LAN-Verbindung nachgewiesen. |
| Private Cloud-Aufrufe | Session-/appgebundene Signaturabhängigkeiten; kein einfacher autorisierter Konto/OTP-Zugang nachgewiesen. |
| Eigene Tuya-App | Eigener Client bedeutet nicht Zugriff auf Geräte des OS-Home-Kontos. |
| Offizielles OAuth/Data Sharing | Ziel-App im getesteten Kontext nicht freigeschaltet; weiterer Versuch vor Abschluss gestoppt. Keine generelle Unmöglichkeitsaussage. |

Eine erfolgreiche Anmeldung oder Cloud-Geräteliste beweist nicht, dass der für LAN erforderliche Local Key bereitgestellt wird. Ein Schlüsselabruf für eine bekannte Device ID ist kein Nachweis eigener Erstaktivierung eines neuen Geräts.

## Was ältere Zusammenfassungen nicht zuverlässig abbilden

Die Forschung wechselte zwischen OS Home 2.0.3 und 2.0.7, mehreren Verbindungszweigen und unterschiedlichen Testumgebungen. Ältere pauschale Aussagen über Pair-Kommandos, Security-Flags, feste Payloadlängen und invertierte Advertising-Bits wurden durch gezielte spätere statische Analysen korrigiert. Alte Wiederanlaufdateien sind deshalb kein unverändert gültiger Implementierungsvertrag.

Diese öffentliche Übergabe enthält bewusst keine extrahierten Originalmethoden oder detaillierten dekompilierten Protokollspezifikationen. Statische Paketbauer und synthetische Tests sind kein bestätigter eigener Geräte-Onboardingpfad.

## Nachweisstand und offene Aufgaben

- Referenzmodell 02455: lokale Steuerbarkeit dokumentiert. Andere EVO/NEXT/PRO/VERTICAL-Modelle bleiben Kandidaten, nicht bestätigt. Legacy-B1015 ist eine andere Plattform.
- Diagnosedaten: DP102/103, 105 und 110 sind im Projekt stärker gestützt; DP101/104/107 bleiben Hypothesen, DP111 mäßig gestützt, DP115/117 unbekannt. Nicht für sicherheitskritische Steuerung verwenden.
- 0.1.2: 28 Python-Tests einschließlich echter lokaler Pipes mit synthetischer CLI, 6 JavaScript-Szenarien, Syntaxprüfung bestanden. Kein neuer Tablet-/GUI-/unabhängiger Nutzertest.
- Mehrwöchige Stabilität, Wiederanlauf nach Netz-/Geräteausfällen, Firmwareabweichungen und weitere Modelle bleiben sinnvolle nächste Arbeiten.
- Allgemein einfacher Schlüsselzugang und vollständig cloudfreie Erstinstallation bleiben ungelöst.

## App auf einem anderen Handy

OS Home mit demselben Konto/Region verwenden und das bereits zugeordnete Gerät laden. Für eine reine zusätzliche Anmeldung sind keine neuen Geräte-Credentials zu erwarten; für den konkreten App-/Firmwarestand ist das keine separat getestete Garantie. Das [Herstellerhandbuch](https://www.olimpiasplendid.com/media/files/9336_264133G_OSHOME_11-2023_ML_1.pdf) unterscheidet Login und Gerätehinzufügen. Bei fehlendem Gerät zuerst Konto/Zuhause/Region prüfen, nicht neu pairen.

Reset, Entfernen aus dem Konto oder erneutes Pairing vermeiden. Beim erneuten Pairing ändert sich bei Tuya der Local Key; siehe [Tuya Local](https://github.com/make-all/tuya-local/blob/main/README.md#local_key). Eine gleich gebliebene Device ID beweist keinen gleich gebliebenen Schlüssel.

## Recht, Sicherheit und Weiterverwendung

Der eigene Projektcode steht unter MIT; [Lizenz](../LICENSE) und [Drittanbieterhinweise](../THIRD_PARTY_NOTICES.md) beachten. Namen dienen nur der Kompatibilitätsangabe, keine Herstellerfreigabe. Forschung und Helfer ausschließlich an eigenen bzw. ausdrücklich autorisierten Geräten/Konten einsetzen.

Die Veröffentlichung ist eine begrenzte Auswahl eigenen Codes und neu formulierter Ergebnisse, keine Rechtsfreigabe des gesamten Forschungsbestands. Laufzeitbeobachtung und Interoperabilitätsanalyse haben gesetzliche Voraussetzungen; insbesondere ist Dekompilierung nicht mit unbeschränkter öffentlicher Weitergabe gleichzusetzen. Konkrete Verträge und Rechtsordnungen bleiben relevant: [§ 69d UrhG](https://www.gesetze-im-internet.de/urhg/__69d.html), [§ 69e UrhG](https://www.gesetze-im-internet.de/urhg/__69e.html).

Keine APKs, DEX/SO, Hersteller-Code-Dumps, App-Backups, Rohlogs, privaten Chatverläufe oder echten Zugangsdaten hochladen. Helfer-Ausgaben und HA-Backups können Credentials enthalten. [Sicherheitsrichtlinie](../SECURITY.md).

## Wiedereinstieg

1. Funktionierende HA-Konfiguration und Credentials geschützt sichern; Gerät nicht vorsorglich zurücksetzen.
2. Repository-/App-/Firmware-/Frida-Versionen erfassen; bestätigten Betrieb von Hypothesen trennen.
3. Falls erforderlich, zuerst den [Helfer](../tools/unico-key-helper/README.md) in der bekannten Umgebung prüfen. Bereits funktionierende HA-Einrichtung benötigt kein erneutes Auslesen.
4. Für allgemeine Nutzbarkeit einen unabhängigen Test einschließlich der Android-/Root-/Frida-Vorbereitung durchführen.
5. LAN-Stabilität und Modellvalidierung priorisieren. Eine getrennte Geräte-Library/CredentialProvider-Struktur ist ein mögliches Architekturziel, kein bereits vollendetes Produkt.
6. Neue BLE-/Cloud-Forschung nur mit konkreter begrenzter Frage und autorisiertem Zugang. Keine proprietären App-Geheimnisse in die Integration einbauen.

Ausgangspunkt bleibt: **OS Home einmalig einrichten → eigene Zugangsdaten übernehmen → HA lokal betreiben.**
