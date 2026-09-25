# UNICO-Key-Helfer 0.1.2 – experimentell, Entwicklung ruhend

Lokales Windows-Werkzeug zur einmaligen Übernahme der Zugangsdaten einer bereits im eigenen OS-Home-Konto eingerichteten UNICO nach Home Assistant. Root/ADB/Frida müssen vorbereitet sein. Kein allgemeiner Einrichtungsassistent und kein cloudfreies Erstpairing.

## Nachweisstand

- **0.1.1:** Auf SM-T585 mit OS Home 2.0.3, Frida PC/Tablet 16.7.19 und frida-tools 13.7.1 wurde ein Gerät gelesen und anschließend erfolgreich in HA hinzugefügt.
- **0.1.2 (dieser Quellstand):** Manuelle Lesebestätigung für langsame Geräte. 28 lokale Python-Tests, 6 JS-Szenarien und Syntaxprüfungen bestanden. Noch kein Tablet-Test von 0.1.2, keine visuelle GUI-Prüfung und kein unabhängiger Nutzbarkeitstest.

## Verwendung

Den kompletten Ordner herunterladen, nicht nur helper.py. `Start.cmd` öffnen, Verbindung prüfen und gegebenenfalls den vorhandenen Frida-Server starten. „2. OS Home zum Lesen starten“ beendet OS Home auf dem ausgewählten Gerät und spawnt es mit geladenem Reader. Frida setzt es automatisch fort. In Ruhe die UNICO-Seite laden lassen, dann „3. Seite geladen – jetzt lesen“ klicken.

Der Helfer wartet bis zu 3 Minuten auf den Start, anschließend bis zu 10 Minuten auf die manuelle Bestätigung und danach bis zu 60 Sekunden auf das Ergebnis. Kein automatischer Scan nach 20 Sekunden. Nach dem Ergebnis wird die Frida-Verbindung beendet; ein Weiterlaufen von OS Home wird nicht garantiert. Die Ursache eines möglichen App-Endes ist nicht automatisch ein bewiesener Absturz.

Ausführlich: [LIESMICH](LIESMICH.md), [Testbogen](TESTBOGEN.md), [Nutzung und Drittanbieter](THIRD_PARTY_NOTICES.md), [MIT-Lizenz](LICENSE).

## Tests ohne Gerät

```text
python -m unittest discover -s tests -v
node tests/test_reader.cjs
python -m py_compile helper.py
node --check reader.js
```

Die Tests nutzen künstliche Daten. Python muss Tkinter importieren können; für das eigentliche Fenster wird eine vollständige Tcl/Tk-Installation benötigt. Kein automatischer Upload, keine Credential-Datei. Zwischenablage und HA-Backups bleiben mögliche Speicherorte von Zugangsdaten.
