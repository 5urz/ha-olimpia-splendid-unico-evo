> Entwicklung ruht seit 25.09.2026. Experimentelles Expertenwerkzeug; 0.1.2 ist noch nicht am Tablet bestätigt.

# UNICO Key-Helfer – begrenzter Versuch 0.1.2

Stand: 25.09.2026. **0.1.1 hat bei der Maintainer Zugangsdaten gelesen; UNICO wurde damit erfolgreich in HA hinzugefügt. 0.1.2 ergänzt manuelles Auslösen und ist bisher nur lokal geprüft.**

Dieser Helfer vereinfacht die bereits im Projekt verwendete Methode: OS Home ist mit dem eigenen Konto angemeldet; der Helfer liest die Geräte-ID und den Local Key aus den geladenen Geräteobjekten. Anschließend werden die Werte in Home Assistant eingetragen. Kein Werksreset, kein neues Pairing, keine private Cloud-API und keine BLE-Analyse.

## Die entscheidende Grenze

Ein **bereits vorbereiteter Root-/Frida-Aufbau** ist weiterhin nötig. Dieses Paket rootet kein Smartphone und erstellt keinen Emulator. Ohne diesen Aufbau ist der Versuch an dieser Stelle blockiert; bitte keine zusätzlichen Geräte kaufen oder das Alltagshandy dafür rooten.

Wenn ein neuer Nutzer schon an dieser Vorbereitung scheitert, zählt das als fehlgeschlagener Nutzbarkeitstest. Wir rechnen den Aufwand für Android Studio, Root und Frida nicht aus dem Ergebnis heraus.

Der bisherige DeviceBean-Ausleseweg wurde mit OS Home 2.0.7 dokumentiert. der Maintainer hat 0.1.1 mit OS Home 2.0.3 erfolgreich zum Hinzufügen in HA verwendet. Andere App-Versionen werden gestoppt. **Keine vorhandene App herabstufen:** Ein nicht unterstützter Versionsstand ist ein Testergebnis.

## 1. Vorbedingungen prüfen

- Die UNICO ist bereits mit der offiziellen OS-Home-App eingerichtet und im WLAN.
- Das eigene Konto zeigt das Gerät in OS Home auf dem Android-Gerät/Emulator, aus dem gelesen werden soll. Das muss nicht das Telefon sein, mit dem ursprünglich gekoppelt wurde.
- Windows-PC mit Python 3.10 oder neuer inklusive Tkinter und dem `py`-Starter.
- ADB ist vorhanden, üblicherweise unter `%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe`.
- Android-Gerät/Emulator ist für USB-Debugging freigegeben.
- Root und ein ausführbarer Frida-Server sind bereits eingerichtet. Erwarteter Speicherort: `/data/local/tmp/frida-server`. Der Helfer kann diesen vorhandenen Server auf Knopfdruck starten.
- Frida auf PC und Android haben **exakt dieselbe Version**. Bekannte Umgebung: gerootetes Samsung SM-T585, **Frida 16.7.19** auf PC und Tablet sowie **frida-tools 13.7.1** auf dem PC. Genau diese PC-Versionen stehen in `requirements.txt`. Andere übereinstimmende Frida-Versionen werden nicht pauschal blockiert, sind aber für 0.1.2 nicht bestätigt.

Offizielle Grundlagen: [Frida für Android](https://frida.re/docs/android/), [Android Platform Tools](https://developer.android.com/tools/releases/platform-tools), [Python für Windows](https://www.python.org/downloads/windows/).

## 2. Paket starten

1. ZIP vollständig in einen eigenen Ordner entpacken. Nicht direkt aus dem ZIP starten.
2. Wenn Python/Frida schon wie bisher eingerichtet sind: **Start.cmd** doppelklicken.
3. Falls der Helfer `FRIDA_MISSING` meldet: Fenster schließen und **Vorbereiten.cmd** starten. Nach Bestätigung legt es `.venv` ausschließlich im Paketordner an und installiert die festgelegten Frida-Pakete von PyPI. Danach **Start.cmd** erneut öffnen.
4. Fehlt Python oder wird `py` nicht erkannt, Python mit Launcher und Tkinter installieren. Bei dieser Stufe aufgewendete Zeit im Testbogen mitzählen.

Die Vorbereitung installiert keine Android-App und keinen Frida-Server. Einen bestehenden Frida-Aufbau nicht unbemerkt auf eine andere Serverversion umstellen. Ein neuer Aufbau ist in dieser Versuchsfassung bewusst kein automatisierter Schritt.

## 3. Zugangsdaten übernehmen

1. OS Home auf dem ausgewählten Android-Gerät manuell öffnen. Anmelden und die bereits eingerichtete UNICO-Geräteseite laden.
2. Im Helfer **Verbindung prüfen** wählen. Wird ADB nicht gefunden, über **Auswählen** die Datei `adb.exe` angeben.
3. Bei mehreren verbundenen Android-Geräten das richtige Gerät auswählen. Es wird nicht automatisch irgendeines verwendet.
4. Falls nötig **Frida-Server starten** wählen und Root-Abfrage auf Android bestätigen. Anschließend **2. OS Home zum Lesen starten** wählen. Der Helfer beendet OS Home auf dem ausgewählten Gerät mit `adb -s <Geräte-ID> shell am force-stop com.olimpiasplendid.oshome`. Erst bei Erfolg startet Frida mit `-D <Geräte-ID> -f com.olimpiasplendid.oshome -l reader.js`. Das Skript wird beim Spawn geladen; Frida setzt den Prozess automatisch fort. Keine PID-Abfrage oder PID-Attach. **OS Home in Ruhe vollständig laden lassen und die vorhandene UNICO-Seite öffnen. Erst dann am PC „3. Seite geladen – jetzt lesen“ anklicken.** Der Reader liest einmalig auf diesen Klick. Für die Startphase sind 3 Minuten vorgesehen; danach bleiben bis zu 10 Minuten für die Lesebestätigung, nach dem Klick 60 Sekunden für den Scan. „Leseversuch abbrechen“ beendet die Sitzung. Nach dem Ergebnis wird die Frida-Kommandozeile regulär mit `exit` beendet. Der Helfer fordert dabei kein Beenden von OS Home an; ob die App weiterläuft oder durch Instrumentierung/Detach abstürzt, wird nicht überprüft.
5. Falls mehrere Geräte gefunden werden, die gewünschte UNICO in der Ergebnisliste auswählen. OS Home kann auch andere Geräte enthalten; deren Anzeige bedeutet keine Kompatibilität mit der Integration.
6. In HA **Einstellungen → Geräte & Dienste → Integration hinzufügen → Olimpia Splendid UNICO** öffnen. Die bestehende Custom Integration muss installiert sein.
7. IP-Adresse, Device ID und Local Key mit den einzelnen **Kopieren**-Schaltflächen übertragen. Fehlt die IP-Adresse, im Router die aktuelle Adresse der UNICO ermitteln. Keine Adresse raten.
8. Die HA-Verbindungsprüfung abschließen. Erst deren Erfolg bestätigt die nutzbare lokale Verbindung. Der Helfer selbst prüft die LAN-Verbindung nicht.
9. Helfer schließen. Er entfernt die Werte aus dem Fenster und leert die aktuelle Zwischenablage, falls dort noch sein zuletzt kopierter Wert liegt. Ein aktivierter Windows-Zwischenablageverlauf oder eine Synchronisierung wird dadurch nicht gelöscht.

Keine Zugangsdaten in diesen Chat, ein GitHub-Issue oder einen Screenshot kopieren. Es gibt keinen automatischen Datei-Export und keinen Upload. Im Arbeitsspeicher und während des expliziten Kopierens sind die Werte notwendigerweise im Klartext vorhanden; sicheres Überschreiben des Prozessspeichers wird nicht versprochen.

## 4. Fehler ohne Einzelbetreuung einordnen

| Meldung | Ein begrenzter nächster Schritt |
|---|---|
| `PROGRAM_BLOCKED` / `ADB_FAILED` | ADB-Pfad prüfen; bei Windows-Sperre lokale Berechtigungen prüfen. Keine Sicherheitseinstellungen pauschal abschalten. |
| `NO_DEVICE` | USB/Debugging prüfen oder den vorhandenen Emulator starten. |
| `USB_UNAUTHORIZED` | Debugging-Abfrage auf Android bestätigen, erneut prüfen. |
| `FRIDA_MISSING` | `Vorbereiten.cmd` verwenden, wenn die Android-Serverversion dazu passt. |
| `SERVER_MISSING` | Bestehenden Frida-Aufbau prüfen. Ohne funktionsfähige Vorbereitung den Test hier als blockiert beenden. |
| `VERSION_MISMATCH` | PC- und Android-Version exakt angleichen. Nicht erneut auf gut Glück lesen. |
| `ROOT_MISSING` | Vorhandene Root-Freigabe auf Android prüfen. Fehlt der vorbereitete Aufbau, Test abbrechen. |
| `SERVER_START_FAILED` | Grenze des vorbereiteten Aufbaus erreicht; nicht mit neuen Hooks weiterforschen. |
| `APP_VERSION` | Versionsgrenze erreicht. Nicht downgraden; Test als blockiert melden. |
| `STOP_FAILED` | ADB-Verbindung/Berechtigungen prüfen. OS Home konnte nicht sicher beendet werden; Frida wurde nicht gestartet. |
| `SPAWN_FAILED` | **Frida-Server starten** wählen und Geräteverbindung prüfen. Spawn mit Reader konnte nicht bestätigt werden; kein manueller PID-Attach. Einmal wiederholen. |
| `FRIDA_START_FAILED` | Python-/Frida-Installation auf dem PC prüfen. |
| `SPAWN_TIMEOUT` | OS Home/Reader wurde innerhalb von 3 Minuten nicht bereit. App und Verbindung prüfen. |
| `PAGE_TIMEOUT` | Innerhalb von 10 Minuten wurde das Lesen nicht bestätigt. Bei Bedarf erneut starten. |
| `READER_TIMEOUT` | 60 Sekunden nach Bestätigung kein Ergebnis. |
| `CANCELLED` | Leseversuch vom Nutzer beendet. |
| `APP_TERMINATED` | Frida meldete den App-Prozess als beendet. Ursache unbekannt; der Helfer hat nach dem Spawn keinen App-Stopp angefordert. |
| `SESSION_ENDED` | Frida-Verbindung endete vor dem Ergebnis; das beweist keinen App-Absturz. |
| `READER_OUTPUT_LIMIT` | Unerwartet viel Prozessausgabe; Versuch beendet, keine Rohdaten angezeigt. |
| `READER_MISSING` / `READER_LOAD_FAILED` | `reader.js` im Paketordner bzw. vollständiges Paket und Frida-Version prüfen. |
| `READER_FAILED` | Reader startete, aber Skript oder Sitzung brach ab. App/Frida-Verbindung prüfen. |
| `NO_KEYS` / `NO_RESULT` | Konto prüfen; beim nächsten automatischen Neustart die UNICO-Seite vollständig laden lassen und erst dann Lesen bestätigen. Einmal wiederholen, danach abbrechen. |
| `CONFLICT` / `TOO_MANY` | OS Home manuell schließen und öffnen; nur die UNICO-Seite laden. Einmal wiederholen. |
| `APP_UNSUPPORTED` / `BAD_RESULT` / `INTERNAL` | Kein weiteres Reverse Engineering durch den Tester. Versuch abbrechen und Fehlercode melden. |
| `TIMEOUT` | Verbindung/App prüfen. Einmal wiederholen, danach abbrechen. |
| HA meldet `cannot_connect` | IP, Erreichbarkeit von HA und vollständig kopierte Felder prüfen. Ein gelesener Schlüssel kann veraltet sein; nicht zurücksetzen oder neu koppeln. |

Über **Technischen Status ohne Zugangsdaten kopieren** lassen sich nur Helferversion, Ergebniscode und nach erfolgreichem Lesen App-/Frida-/frida-tools-Version, Lesemodus `spawn`, manueller Auslöser, Art des Sitzungsendes, ungeprüfter App-Zustand sowie Geräteanzahl übernehmen. Keine Geräte-ID, IP, Schlüssel oder Android-Seriennummer. Das ist der einzige für Rückmeldungen vorgesehene Status.

## Erfolgskriterien und Abbruch

- Dieser erste Lauf muss auf dem bekannten Entwicklungsaufbau lesen und die bestehende HA-Einrichtung ermöglichen. Ist das bereits nicht reproduzierbar, erfolgt keine Veröffentlichung als fertiger Helfer.
- Danach muss ein zweiter Nutzer ausschließlich mit dieser Anleitung zum HA-Verbindungserfolg kommen. Gesamtdauer und Vorbereitung getrennt erfassen, aber beides berücksichtigen.
- Richtwert: nach vorhandenem Aufbau höchstens 30 Minuten, höchstens eine Wiederholung. Keine neuen individuellen Hooks, kein APK-Patchen, keine neuen Pairing-Traces.
- Gesamtbudget des Abschlussversuchs: höchstens zwei konzentrierte Arbeitstage. Fremdtests/Wartezeiten werden getrennt erfasst, verlängern aber nicht die Forschungsarbeit.
- Benötigt der zweite Nutzer individuelle Android-/Root-/Frida-Betreuung, ist das breite Nutzerziel **nicht erreicht**, auch wenn das Auslesen technisch funktioniert. Das Paket kann dann höchstens als Expertenwerkzeug dienen.

## Technische Grenzen

- Es werden ausschließlich die bekannten `DeviceBean`-Getter gelesen, keine Methoden verändert und keine App-/Cloud-Schlüssel kopiert.
- Doppelte identische Geräteobjekte werden zusammengeführt. Widersprüchliche Local Keys führen zum Abbruch.
- Das Programm speichert keine Zugangsdaten. Der JavaScript-Leser transportiert sie über eine vom Helfer abgefangene Prozessausgabe. **reader.js nicht separat mit Frida ausführen oder dessen Ausgabe protokollieren.**
- Der Einsatz der Frida-Kommandozeile ist beabsichtigt. In [frida-tools 13.7.1](https://github.com/frida/frida-tools/blob/13.7.1/frida_tools/repl.py) lädt `_start()` zuerst das Skript und ruft danach automatisch Resume auf. Deshalb weder `--pause` noch das alte `--no-pause` verwenden. Der Reader wartet asynchron und blockiert diesen Start nicht.
- Ein Heap-Leseversuch kann die App kurz beanspruchen. Ein Absturz wird nicht durch automatisches Neustarten oder Reset behandelt.
- Das Paket ist unabhängig von der HA-Integration. Es enthält weder APK noch Android-Image, Root-Werkzeug oder Frida-Binärdatei. Die HA-Laufzeitintegration wird durch diesen Helfer nicht verändert.

## Änderungen und lokaler Test

0.1.1 ersetzte den fehlerhaften PID-Attach durch Force-stop und Spawn. der Maintainer meldete damit `READ_OK` für ein Gerät (OS Home 2.0.3, Frida 16.7.19, frida-tools 13.7.1) und anschließend erfolgreiches Hinzufügen der UNICO in HA. Ein erneutes Auslesen ist für diese erfolgreiche Einrichtung nicht erforderlich.

0.1.2 entfernt den automatischen Scan nach 20 Sekunden und das feste CLI-Ende nach 30 Sekunden. Der Reader wartet auf „Seite geladen – jetzt lesen“. ADB-/Versionsprüfungen und Credential-Auswertung bleiben erhalten. Der technische Status weist `read_trigger: manual` und `session_end` aus. `helper_quit_after_read` bedeutet reguläres Beenden der PC-Frida-Kommandozeile nach dem Ergebnis; `pc_cli_forced_stop` bedeutet, dass sie nicht innerhalb von 5 Sekunden auf `exit` reagierte und auf dem PC beendet werden musste. `already_ended` bedeutet, dass sie bereits beendet war. `app_state_after_read: not_checked` stellt klar, dass daraus keine Aussage über den App-Zustand folgt.

Der bestehende Ordnername darf bleiben; maßgeblich sind Fenstertitel und Status 0.1.2. `Start.cmd` bevorzugt eine vorhandene `.venv`; die bekannte Frida-Installation muss nicht geändert werden.

Lokale Prüfungen: `python -m unittest discover -s tests -v`, `node tests/test_reader.cjs`, `python -m py_compile helper.py`, `node --check reader.js`. 28 Python-Tests und 6 JavaScript-Szenarien bestanden. Dazu gehören echte lokale Prozess-Pipes mit einer synthetischen CLI für manuelles Auslösen, Abbruch und phasenspezifische Zeitlimits. Kein neuer Tablet-Test; visuelle GUI-Prüfung wegen fehlender Tcl/Tk-Laufzeit nicht möglich.
