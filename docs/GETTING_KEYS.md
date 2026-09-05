# Device ID und Local Key ermitteln

Die aktuelle Version der Integration benötigt für die lokale Verbindung drei Angaben:

- **IP-Adresse** des UNICO
- **Device ID**
- **Local Key**

Die IP-Adresse lässt sich normalerweise im Router ermitteln. Für einen dauerhaft stabilen Betrieb empfiehlt sich eine DHCP-Reservierung, damit das Gerät immer dieselbe IP-Adresse erhält.

**Device ID und Local Key sind gerätespezifisch.** Sie werden nicht mit dieser Integration ausgeliefert und müssen derzeit vom Benutzer für das eigene Gerät ermittelt werden.

> [!WARNING]
> Der **Local Key ist ein Zugangsschlüssel zum eigenen Gerät**. Nicht in GitHub-Issues, Screenshots, Logs oder Forenbeiträgen veröffentlichen. Auch die Device ID sollte nicht unnötig öffentlich geteilt werden.

## Status dieser Methode

Die folgende Methode beschreibt den Weg, der während der Entwicklung dieser Integration verwendet wurde. Dabei wurde die Android-App **OS Home** zur Laufzeit untersucht.

Getesteter Entwicklungsstand:

- OS Home: **2.0.7**
- Android-Paket: `com.olimpiasplendid.oshome`
- Android-Studio-Emulator
- gerooteter Emulator mit **Magisk/rootAVD**
- **Frida** auf PC und Emulator

Die App und das verwendete ThingClips/Tuya-SDK können sich mit zukünftigen Versionen ändern. Die Methode ist deshalb ausdrücklich **experimentell**.

Diese Anleitung ist ausschließlich dafür gedacht, die Zugangsdaten des **eigenen Geräts und eigenen Accounts** auszulesen.

## Voraussetzungen

Benötigt werden:

1. Ein PC mit **Android Studio / ADB**.
2. Ein Android-Emulator, auf dem OS Home läuft.
3. Root-Zugriff im Emulator, z. B. über **Magisk/rootAVD**.
4. Python mit installierten `frida` / `frida-tools`.
5. Eine zur installierten Frida-Version passende `frida-server`-Binärdatei im Emulator.
6. OS Home mit dem eigenen Account und dem eigenen UNICO-Gerät.

Die vollständige Einrichtung eines gerooteten Android-Emulators ist nicht Bestandteil dieses Projekts. Wichtig ist am Ende lediglich, dass ADB, Root und Frida funktionieren.

## 1. ADB-Verbindung prüfen

```text
adb devices
```

Der Emulator sollte beispielsweise als `emulator-5554` erscheinen.

Root prüfen:

```text
adb shell su -c id
```

Eine funktionierende Root-Umgebung liefert eine Ausgabe mit `uid=0`.

## 2. Frida-Server starten

Die Version von `frida-server` sollte zur auf dem PC installierten Frida-Version passen.

Beispiel:

```text
adb push frida-server /data/local/tmp/frida-server
adb shell "su -c 'chmod 755 /data/local/tmp/frida-server'"
adb shell "su -c '/data/local/tmp/frida-server &'"
```

Anschließend auf dem PC prüfen:

```text
frida-ps -U
```

Wenn die Prozessliste des Emulators angezeigt wird, funktioniert die Verbindung.

## 3. OS Home vorbereiten

1. OS Home im Emulator starten.
2. Mit dem **eigenen Account** anmelden.
3. Warten, bis die Geräteliste geladen wurde.
4. Das eigene UNICO-Gerät öffnen bzw. die Geräteseite einige Sekunden geöffnet lassen.

Dadurch ist die Wahrscheinlichkeit höher, dass das ThingClips/Tuya-SDK die benötigten Geräteobjekte bereits im Speicher hält.

## 4. Experimentelles Frida-Hilfsskript verwenden

Im Repository befindet sich das Hilfsskript:

```text
tools/oshome_key.js
```

Es sucht im Java-Heap nach dem vom ThingClips/Tuya-SDK verwendeten `DeviceBean` und versucht daraus folgende Werte auszulesen:

- Gerätename
- Device ID
- Local Key
- IP-Adresse

### Variante A: laufende App verwenden

OS Home zuerst manuell öffnen und anschließend Frida an den laufenden Prozess anhängen:

```text
frida -U -n com.olimpiasplendid.oshome -l tools/oshome_key.js
```

Falls der Prozess unter einem anderen Namen erscheint, kann er mit folgendem Befehl gesucht werden:

```text
frida-ps -Uai
```

### Variante B: App über Frida starten

Alternativ:

```text
frida -U -f com.olimpiasplendid.oshome -l tools/oshome_key.js
```

Während unserer Entwicklung führte das Starten mit `-f` in einer Emulator-Konfiguration zeitweise zu einem App-Absturz. In diesem Fall ist **Variante A** vorzuziehen.

Das Skript wartet nach dem Laden einige Sekunden und durchsucht anschließend den Java-Heap.

Eine erfolgreiche Ausgabe sollte sinngemäß so aussehen:

```text
Name:       <Gerätename>
Device ID:  <deine Device ID>
Local Key:  <dein Local Key>
IP address: <Geräte-IP>
```

Die echten Werte niemals veröffentlichen.

## 5. Integration in Home Assistant einrichten

Nach der Installation der Custom Integration:

1. **Einstellungen → Geräte & Dienste** öffnen.
2. **Integration hinzufügen** wählen.
3. Nach **Olimpia Splendid UNICO** suchen.
4. Folgende Werte eintragen:
   - IP-Adresse
   - Device ID
   - Local Key
5. Die Integration prüft anschließend, ob eine lokale Verbindung zum Gerät aufgebaut werden kann.

## Fehlerbehebung

### Frida findet kein DeviceBean

- OS Home öffnen und die Geräteseite laden.
- Einige Sekunden warten.
- Skript erneut starten.
- Prüfen, ob OS Home wirklich angemeldet ist und das Gerät sichtbar ist.

### `frida-ps -U` zeigt nichts an

- ADB-Verbindung prüfen.
- Root prüfen.
- Prüfen, ob `frida-server` läuft.
- Prüfen, ob Client und Server dieselbe Frida-Hauptversion verwenden.

### OS Home stürzt beim Start über Frida ab

Die App manuell starten und anschließend mit `-n` an den laufenden Prozess anhängen.

### Home Assistant meldet `cannot_connect`

Prüfen:

- IP-Adresse korrekt?
- UNICO und Home Assistant im selben LAN/VLAN erreichbar?
- Device ID korrekt?
- Local Key vollständig und unverändert?
- Gerät bereits vollständig in OS Home eingerichtet?

## Warum ist das noch so umständlich?

Das ist der größte derzeitige Nachteil der Integration. Die laufende lokale Steuerung benötigt keine Hersteller-Cloud, aber die individuellen Zugangsdaten müssen aktuell noch manuell ermittelt werden.

Geplant ist deshalb die Untersuchung des **BLE-Pairings und WLAN-Provisionings** der offiziellen App. Langfristiges Ziel ist ein Home-Assistant-Config-Flow, der das Gerät möglichst selbst erkennt und die für die lokale Kommunikation erforderlichen Informationen während einer eigenen Einrichtung gewinnt, sodass Frida und ein gerooteter Android-Emulator für normale Benutzer nicht mehr erforderlich sind.

Ob und in welchem Umfang sich dieser Ablauf vollständig reproduzieren lässt, ist derzeit noch Gegenstand des Reverse Engineerings.
