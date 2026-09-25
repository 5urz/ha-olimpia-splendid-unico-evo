# Device ID und Local Key ermitteln

Stand 25.09.2026; Entwicklung ruht. Bereits funktionierende HA-Einrichtungen benötigen kein erneutes Auslesen.

Home Assistant benötigt IP/Host, Device ID und Local Key. Die IP kann im Router ermittelt und per DHCP reserviert werden. ID und Key gehören zum eigenen Gerät, nicht in Logs, Screenshots oder Issues.

## Aktueller Expertenweg

Der [UNICO-Key-Helfer 0.1.2](../tools/unico-key-helper/README.md) ist ein separates Windows-Werkzeug. Root, ADB und Frida müssen vorbereitet sein; das Paket rootet kein Gerät und enthält keine APK oder Frida-Binärdatei.

Bekannter erfolgreicher Aufbau mit **0.1.1**: Samsung SM-T585, OS Home 2.0.3, Frida 16.7.19 auf PC/Tablet, frida-tools 13.7.1. READ_OK für ein Gerät und anschließendes Hinzufügen in HA bestätigt. Der aktuelle **0.1.2**-Stand mit manuellem Lesezeitpunkt ist nur lokal getestet.

1. UNICO im bisherigen OS-Home-Konto eingerichtet lassen. Kein Reset/Pairing.
2. Den vollständigen Helferordner herunterladen. `Start.cmd` öffnen; erforderlichenfalls die [Vorbereitung](../tools/unico-key-helper/LIESMICH.md) beachten.
3. Verbindung prüfen, gewünschtes Tablet auswählen und vorhandenen Frida-Server bei Bedarf starten. PC-/Server-Frida-Version müssen exakt übereinstimmen.
4. „OS Home zum Lesen starten“ anklicken. Der Helfer führt ADB force-stop aus, spawnt OS Home mit Frida über `-D` und `-f`, lädt reader.js und lässt Frida den Prozess fortsetzen.
5. UNICO-Seite vollständig laden lassen. Erst dann „Seite geladen – jetzt lesen“ drücken.
6. Gerät auswählen und Werte in HA unter Einstellungen → Geräte & Dienste → Integration hinzufügen → Olimpia Splendid UNICO übernehmen. Die lokale HA-Verbindung muss erfolgreich geprüft werden.

Frida-Verbindung und App-Stabilität sind verschiedene Dinge. Der Helfer beendet nach dem Ergebnis die Verbindung und fordert keinen weiteren Android-App-Stopp an. Ob OS Home dabei weiterläuft, wird nicht bestätigt.

## Historischer Emulatorweg

Das ältere [Konsolenskript](../tools/oshome_key.js) stammt aus der Untersuchung von OS Home 2.0.7 im gerooteten Emulator und gibt Credentials in der Konsole aus. Es bleibt als historische Quelle erhalten. Seine Ausgabe nicht veröffentlichen.

Die frühere Empfehlung, bei Problemen grundsätzlich an eine laufende App anzuhängen, gilt **nicht für den SM-T585**: Hier ist Force-stop plus Spawn der bestätigte Weg. Emulator- und Tabletbeobachtungen nicht vermischen; nicht pauschal die App herabstufen.

## Handywechsel und Schlüssel

OS Home auf dem Haupthandy installieren und mit demselben Konto/Region anmelden, vorhandenes Zuhause/Gerät auswählen. Bei bloßer zusätzlicher Anmeldung ist keine Key-Änderung zu erwarten; das ist eine technische Ableitung, keine für jede Firmware garantierte Herstellerzusage.

Nicht erneut pairen oder das Gerät aus dem Konto löschen. Beim Pairing kann der Local Key wechseln, auch wenn die Device ID unverändert bleibt. Bei HA-Verbindungsproblemen zuerst IP/LAN und dann Credentials prüfen. [OS-Home-Handbuch](https://www.olimpiasplendid.com/media/files/9336_264133G_OSHOME_11-2023_ML_1.pdf), [Tuya Local](https://github.com/make-all/tuya-local/blob/main/README.md#local_key).

Der Helfer löst keinen unabhängigen BLE-/Cloud-Bootstrap. Der [Abschlussstand](PROJEKTUEBERGABE.md) dokumentiert Erkenntnisse und Grenzen für eine spätere Fortsetzung.
