"""Local, bounded OS Home credential reader. No upload, log, or credential file."""
from __future__ import annotations

import importlib.metadata
import ipaddress
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk

PACKAGE = 'com.olimpiasplendid.oshome'
VERSION = '0.1.2'
PREFIX = 'UNICO_RESULT_V1:'
READER_STARTED = 'UNICO_READER_V1:STARTED'
BASE = Path(__file__).resolve().parent
START_TIMEOUT = 180
PAGE_TIMEOUT = 600
SCAN_TIMEOUT = 60


class Failure(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def run(args, timeout=15):
    try:
        return subprocess.run(args, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=timeout, stdin=subprocess.DEVNULL,
                              creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        raise Failure('TIMEOUT', 'Zeitlimit erreicht. App und Verbindung prüfen; danach erneut versuchen.') from None
    except OSError:
        raise Failure('PROGRAM_BLOCKED', 'Ein Hilfsprogramm fehlt oder Windows blockiert seinen Start.') from None


def devices(text):
    return [(p[0], p[1]) for line in text.splitlines()
            if len(p := line.split()) >= 2 and p[1] in ('device', 'offline', 'unauthorized')]


def parse_result(text):
    clean = re.sub(r'\x1b\[[0-9;]*m', '', text)
    lines = [line[len(PREFIX):] for line in clean.splitlines() if line.startswith(PREFIX)]
    if len(lines) != 1:
        raise Failure('NO_RESULT', 'Kein vollständiges Ergebnis. OS Home öffnen, Geräteseite laden und erneut lesen.')
    try:
        payload = json.loads(lines[0])
        if not isinstance(payload, dict) or payload.get('schema') != 1:
            raise ValueError()
        if payload.get('error'):
            raise Failure('APP_UNSUPPORTED', 'Die benötigten Geräteobjekte sind in dieser App nicht zugänglich.')
        rows = payload['devices']
        if not isinstance(rows, list) or len(rows) > 512:
            raise ValueError()
        result = {}
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError()
            did, key = row.get('device_id'), row.get('local_key')
            if not isinstance(did, str) or not re.fullmatch(r'[A-Za-z0-9_-]{6,64}', did):
                continue
            if not isinstance(key, str) or len(key.encode('utf-8')) != 16 or any(ord(c) < 32 for c in key):
                continue
            if did in result and result[did]['local_key'] != key:
                raise Failure('CONFLICT', 'Mehrere unterschiedliche Schlüssel für dasselbe Gerät gefunden. App neu öffnen und erneut lesen.')
            name = row.get('name') if isinstance(row.get('name'), str) else 'Gerät'
            name = ''.join(c for c in name if c.isprintable())[:100] or 'Gerät'
            host = row.get('host') if isinstance(row.get('host'), str) else ''
            try:
                addr = ipaddress.IPv4Address(host)
                if not addr.is_private or addr.is_unspecified or addr.is_loopback or addr.is_multicast or addr.is_link_local:
                    host = ''
            except ValueError:
                host = ''
            result[did] = dict(name=name, device_id=did, local_key=key, host=host)
        if payload.get('truncated'):
            raise Failure('TOO_MANY', 'Zu viele Geräteobjekte. App neu öffnen, nur die UNICO-Geräteseite laden und erneut lesen.')
        if not result:
            raise Failure('NO_KEYS', 'Keine vollständigen Zugangsdaten geladen. In OS Home anmelden und die bereits eingerichtete UNICO öffnen.')
        return list(result.values())
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise Failure('BAD_RESULT', 'Das Ergebnis hat ein unerwartetes Format. Keine Zugangsdaten übernommen.') from None


def run_frida(args, scan_requested, cancelled, ready, progress):
    """Private interactive CLI pipe: scan only on a user request, then quit cleanly."""
    try:
        proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                                errors='replace', bufsize=1,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except OSError:
        raise Failure('FRIDA_START_FAILED', 'Frida konnte auf dem PC nicht gestartet werden.') from None
    messages = queue.Queue()

    def receive():
        total = 0
        try:
            while True:
                line = proc.stdout.readline(1024 * 1024)
                if not line:
                    break
                total += len(line)
                if total > 2 * 1024 * 1024:
                    messages.put(('overflow', ''))
                    return
                messages.put(('line', line))
        except (OSError, ValueError):
            pass
        finally:
            messages.put(('eof', ''))

    reader = threading.Thread(target=receive, daemon=True)
    reader.start()
    output = []
    phase = 'start'
    deadline = time.monotonic() + START_TIMEOUT
    completed = None
    try:
        while True:
            if cancelled.is_set():
                raise Failure('CANCELLED', 'Leseversuch abgebrochen. Frida-Verbindung wird beendet; kein Beenden von OS Home angefordert.')
            if time.monotonic() >= deadline:
                code, message = {
                    'start': ('SPAWN_TIMEOUT', 'OS Home/Reader wurde in 3 Minuten nicht bereit.'),
                    'waiting': ('PAGE_TIMEOUT', '10 Minuten ohne Lesebestätigung. Frida-Verbindung wird beendet.'),
                    'scan': ('READER_TIMEOUT', 'Reader lieferte innerhalb von 60 Sekunden kein Ergebnis.'),
                }[phase]
                raise Failure(code, message)
            if phase == 'waiting' and scan_requested.is_set():
                proc.stdin.write('globalThis.unicoRead();\n')
                proc.stdin.flush()
                phase = 'scan'
                deadline = time.monotonic() + SCAN_TIMEOUT
                progress('Lese jetzt die geladenen Geräteobjekte …')
            try:
                kind, line = messages.get(timeout=0.1)
            except queue.Empty:
                continue
            if kind == 'overflow':
                raise Failure('READER_OUTPUT_LIMIT', 'Unerwartet viel Prozessausgabe. Versuch beendet; keine Rohdaten angezeigt.')
            if kind == 'eof':
                completed = subprocess.CompletedProcess(args, proc.wait(timeout=5), ''.join(output), '')
                if phase != 'start':
                    raise Failure('SESSION_ENDED', 'Frida-Sitzung endete vor dem Ergebnis. App oder Verbindung wurde beendet; ein Absturz ist damit nicht bewiesen.')
                break
            clean = re.sub(r'\x1b\[[0-9;]*m', '', line)
            # In non-quiet CLI mode a prompt may precede the reader's line.
            if PREFIX in clean:
                clean = clean[clean.index(PREFIX):]
            output.append(clean)
            if 'Process terminated' in clean:
                raise Failure('APP_TERMINATED', 'Frida meldet: OS-Home-Prozess beendet. Der Helfer hat nach dem Spawn kein Beenden der App angefordert; Ursache noch unbekannt.')
            if READER_STARTED in clean and phase == 'start':
                phase = 'waiting'
                deadline = time.monotonic() + PAGE_TIMEOUT
                progress('OS Home vollständig laden lassen und UNICO-Seite öffnen. Erst dann „Seite geladen – jetzt lesen“ klicken. Bis zu 10 Minuten Zeit; kein automatisches Lesen nach 20 Sekunden.')
                ready()
            if clean.startswith(PREFIX):
                completed = subprocess.CompletedProcess(args, 0, ''.join(output), '')
                break
    except (OSError, ValueError, subprocess.TimeoutExpired):
        raise Failure('SESSION_ENDED', 'Frida-Verbindung wurde unterbrochen. Keine Rohdaten übernommen.') from None
    finally:
        # Quit the PC CLI gracefully; never issue another Android force-stop.
        session_end = 'already_ended'
        if proc.poll() is None:
            try:
                proc.stdin.write('exit\n')
                proc.stdin.flush()
                proc.wait(timeout=5)
                session_end = 'helper_quit_after_read'
            except (OSError, ValueError, subprocess.TimeoutExpired):
                proc.kill()
                proc.wait(timeout=5)
                session_end = 'pc_cli_forced_stop'
        reader.join(timeout=2)
        proc.stdin.close()
        proc.stdout.close()
        if completed is not None:
            completed.session_end = session_end
    return completed


def read_keys(adb, serial, progress=lambda message: None, scan_requested=None,
              cancelled=None, ready=lambda: None):
    scan_requested = scan_requested if scan_requested is not None else threading.Event()
    cancelled = cancelled if cancelled is not None else threading.Event()
    progress('Prüfe OS Home und Frida-Versionen …')
    try:
        client = importlib.metadata.version('frida')
        tools_version = importlib.metadata.version('frida-tools')
    except importlib.metadata.PackageNotFoundError:
        raise Failure('FRIDA_MISSING', 'Frida fehlt in diesem Python. Siehe Vorbereitung in LIESMICH.md.') from None
    def shell(*args):
        return run([adb, '-s', serial, 'shell', *args])
    app = shell('dumpsys', 'package', PACKAGE)
    match = re.search(r'versionName=([^\s]+)', app.stdout)
    version = match.group(1) if match else 'unbekannt'
    if version not in ('2.0.3', '2.0.7'):
        raise Failure('APP_VERSION', 'Diese Testfassung unterstützt nur OS Home 2.0.3 und 2.0.7. Vorhandene App nicht herabstufen.')
    server = shell('/data/local/tmp/frida-server', '--version')
    if server.returncode != 0:
        raise Failure('SERVER_MISSING', 'Frida-Server unter /data/local/tmp/frida-server fehlt oder ist nicht ausführbar. Siehe Vorbereitung.')
    if server.stdout.strip() != client:
        raise Failure('VERSION_MISMATCH', 'PC-Frida und Android-Frida-Server müssen exakt dieselbe Version haben.')
    if not (BASE / 'reader.js').is_file():
        raise Failure('READER_MISSING', 'reader.js fehlt im Helferordner. Paket vollständig entpacken.')
    progress('Beende OS Home auf dem ausgewählten Android-Gerät …')
    try:
        stopped = shell('am', 'force-stop', PACKAGE)
    except Failure:
        raise Failure('STOP_FAILED', 'OS Home konnte über ADB nicht sicher beendet werden. Verbindung prüfen; kein Spawn ausgeführt.') from None
    if stopped.returncode != 0 or re.search(r'error|exception|denied', stopped.stdout + stopped.stderr, re.I):
        raise Failure('STOP_FAILED', 'OS Home konnte über ADB nicht beendet werden. Verbindung und Berechtigungen prüfen; kein Spawn ausgeführt.')
    if cancelled.is_set():
        raise Failure('CANCELLED', 'Leseversuch abgebrochen.')
    progress('Frida startet OS Home neu. App vollständig laden lassen; der Reader wartet anschließend auf deine Lesebestätigung …')
    try:
        # frida-tools 13.7.1 loads -l before automatically resuming -f.
        # Do not use --pause, a PID target, or --kill-on-exit here.
        completed = run_frida([sys.executable, '-u', '-m', 'frida_tools.repl', '-D', serial, '-f', PACKAGE,
                               '-l', str(BASE / 'reader.js'), '--no-auto-reload', '--exit-on-error'],
                              scan_requested, cancelled, ready, progress)
    except Failure as err:
        if err.code == 'TIMEOUT':
            raise Failure('FRIDA_TIMEOUT', 'Frida hat den Start-/Leseversuch nicht rechtzeitig beendet. Spawn- oder Reader-Phase nicht bestätigt. App und Verbindung prüfen.') from None
        if err.code == 'PROGRAM_BLOCKED':
            raise Failure('FRIDA_START_FAILED', 'Frida-Kommandozeile konnte auf dem PC nicht gestartet werden. Python-/Frida-Installation prüfen.') from None
        raise
    if completed.returncode != 0:
        output = completed.stdout + '\n' + completed.stderr
        if 'Failed to load script:' in output:
            raise Failure('READER_LOAD_FAILED', 'Frida konnte reader.js nicht laden. Paket und Frida-Version prüfen.')
        if READER_STARTED in output or PREFIX in output:
            raise Failure('READER_FAILED', 'Reader wurde gestartet, aber der Leseversuch brach ab. OS Home und Frida-Verbindung prüfen.')
        raise Failure('SPAWN_FAILED', 'Frida konnte OS Home nicht erfolgreich mit Reader starten. Frida-Server und Geräteverbindung prüfen; kein PID-Attach versuchen.')
    rows = parse_result(completed.stdout)
    return rows, {'app_version': version, 'frida_version': client, 'frida_tools_version': tools_version,
                  'read_mode': 'spawn', 'read_trigger': 'manual',
                  'session_end': completed.session_end, 'app_state_after_read': 'not_checked',
                  'result': 'READ_OK', 'device_count': len(rows)}


def discover_adb():
    candidates = [shutil.which('adb'), str(Path(os.environ.get('LOCALAPPDATA', '')) / 'Android/Sdk/platform-tools/adb.exe')]
    return next((p for p in candidates if p and Path(p).is_file()), '')


def start_server(adb, serial):
    """Start only an existing server on an already rooted Android installation."""
    def shell(command):
        return run([adb, '-s', serial, 'shell', command])
    try:
        client = importlib.metadata.version('frida')
    except importlib.metadata.PackageNotFoundError:
        raise Failure('FRIDA_MISSING', 'Frida fehlt in diesem Python. Siehe Vorbereitung.') from None
    version = shell('/data/local/tmp/frida-server --version')
    if version.returncode != 0:
        raise Failure('SERVER_MISSING', 'Frida-Server fehlt oder ist nicht ausführbar. Keine automatische Installation.')
    if version.stdout.strip() != client:
        raise Failure('VERSION_MISMATCH', 'PC-Frida und Android-Frida-Server müssen exakt dieselbe Version haben.')
    existing = shell('pidof frida-server')
    if existing.returncode == 0 and existing.stdout.strip():
        return 'Frida-Server läuft bereits. Jetzt Zugangsdaten lesen.'
    direct = shell('id')
    if 'uid=0(' in direct.stdout:
        command = '/data/local/tmp/frida-server -D'
    else:
        root = shell("su -c 'id'")
        if root.returncode != 0 or 'uid=0(' not in root.stdout:
            raise Failure('ROOT_MISSING', 'Kein Root-Zugriff. Eventuelle Root-Abfrage auf Android prüfen. Gerät nicht eigens dafür rooten.')
        command = "su -c '/data/local/tmp/frida-server -D'"
    result = shell(command)
    if result.returncode != 0:
        raise Failure('SERVER_START_FAILED', 'Vorhandener Frida-Server konnte nicht gestartet werden. Versuch hier abbrechen.')
    return 'Frida-Server gestartet. Jetzt Zugangsdaten lesen. Er läuft bis zum Android-Neustart bzw. manuellem Beenden weiter.'


class App:
    def __init__(self, root):
        self.root, self.events = root, queue.Queue()
        self.rows, self.targets, self.busy = [], [], False
        self.scan_requested, self.cancelled = threading.Event(), threading.Event()
        self.report = {'helper_version': VERSION, 'result': 'NOT_RUN'}
        self.copied = None
        root.title('UNICO – Zugangsdaten übernehmen (Test ' + VERSION + ')')
        root.geometry('860x700')
        root.minsize(820, 680)
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='OS Home einmalig nutzen → Home Assistant lokal einrichten', font=('', 13, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='UNICO bereits eingerichtet lassen und angemeldet bleiben.\nOS Home wird neu gestartet. In Ruhe laden lassen; erst auf der fertigen UNICO-Seite das Lesen bestätigen.', wraplength=760).pack(anchor='w', pady=10)
        self.adb = tk.StringVar(value=discover_adb())
        bar = ttk.Frame(frame); bar.pack(fill='x')
        ttk.Label(bar, text='ADB:').pack(side='left')
        self.adb_entry = ttk.Entry(bar, textvariable=self.adb)
        self.adb_entry.pack(side='left', fill='x', expand=True, padx=8)
        ttk.Button(bar, text='Auswählen', command=self.choose_adb).pack(side='left')
        self.device = ttk.Combobox(frame, state='readonly'); self.device.pack(fill='x', pady=10)
        self.device.bind('<<ComboboxSelected>>', lambda _: self.clear())
        buttons = ttk.Frame(frame); buttons.pack(fill='x')
        self.check_button = ttk.Button(buttons, text='1. Verbindung prüfen', command=self.check)
        self.check_button.pack(side='left')
        self.read_button = ttk.Button(buttons, text='2. OS Home zum Lesen starten', command=self.read, state='disabled')
        self.read_button.pack(side='left', padx=8)
        self.server_button = ttk.Button(buttons, text='Frida-Server starten', command=self.server, state='disabled')
        self.server_button.pack(side='left')
        reading = ttk.Frame(frame); reading.pack(fill='x', pady=6)
        self.scan_button = ttk.Button(reading, text='3. Seite geladen – jetzt lesen', command=self.confirm_read, state='disabled')
        self.scan_button.pack(side='left')
        self.cancel_button = ttk.Button(reading, text='Leseversuch abbrechen', command=self.cancel_read, state='disabled')
        self.cancel_button.pack(side='left', padx=8)
        self.status = tk.StringVar(value='Zuerst Verbindung prüfen. Ein vorbereiteter Root-/Frida-Aufbau ist weiterhin erforderlich.')
        ttk.Label(frame, textvariable=self.status, wraplength=760).pack(anchor='w', pady=15)
        self.selection = ttk.Combobox(frame, state='readonly'); self.selection.pack(fill='x')
        self.selection.bind('<<ComboboxSelected>>', lambda _: self.show())
        self.fields = {}
        for key, title in [('host', 'IP-Adresse'), ('device_id', 'Device ID'), ('local_key', 'Local Key')]:
            row = ttk.Frame(frame); row.pack(fill='x', pady=7)
            ttk.Label(row, text=title, width=13).pack(side='left')
            var = tk.StringVar(); self.fields[key] = var
            ttk.Entry(row, textvariable=var, state='readonly', show='•' if key == 'local_key' else '').pack(side='left', fill='x', expand=True)
            ttk.Button(row, text='Kopieren', command=lambda k=key: self.copy(k)).pack(side='left', padx=8)
        ttk.Label(frame, text='In HA: Einstellungen → Geräte & Dienste → Integration hinzufügen → Olimpia Splendid UNICO.\nFehlt die IP-Adresse, im Router nachsehen. HA prüft die tatsächliche lokale Verbindung.\nDas Auslesen allein bestätigt weder einen gültigen Schlüssel noch Modellkompatibilität.', wraplength=760).pack(anchor='w', pady=10)
        ttk.Label(frame, text='Zugangsdaten bleiben im Arbeitsspeicher. Kopieren schreibt den gewählten Wert in die Windows-\nZwischenablage (ggf. Verlauf/Synchronisierung beachten). Keine Schlüssel-Screenshots teilen.', wraplength=760).pack(anchor='w')
        ttk.Button(frame, text='Technischen Status ohne Zugangsdaten kopieren', command=self.copy_report).pack(anchor='w', pady=10)
        ttk.Button(frame, text='Zugangsdaten aus Fenster entfernen', command=self.clear).pack(anchor='w')
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)

    def choose_adb(self):
        if self.busy: return
        name = filedialog.askopenfilename(title='adb.exe auswählen', filetypes=[('ADB', 'adb.exe')])
        if name:
            self.adb.set(name); self.targets = []; self.device.set(''); self.read_button['state'] = 'disabled'; self.clear()

    def task(self, action):
        if self.busy: return
        self.busy = True
        self.check_button['state'] = self.read_button['state'] = self.server_button['state'] = 'disabled'
        self.device['state'] = self.adb_entry['state'] = 'disabled'
        def work():
            try: self.events.put(('ok', action()))
            except Failure as err: self.events.put(('error', (err.code, str(err))))
            except Exception: self.events.put(('error', ('INTERNAL', 'Unerwarteter Fehler. Keine Rohdaten protokolliert. Versuch abbrechen.')))
        threading.Thread(target=work, daemon=True).start()

    def check(self):
        if self.busy: return
        self.clear(); self.targets = []; self.device.set(''); self.device['values'] = ()
        adb = self.adb.get()
        self.status.set('Verbindung wird geprüft …')
        def work():
            result = run([adb, 'devices'])
            if result.returncode != 0: raise Failure('ADB_FAILED', 'ADB konnte keine Geräte abfragen.')
            listed = devices(result.stdout)
            ready = [serial for serial, state in listed if state == 'device']
            if not ready:
                if any(state == 'unauthorized' for _, state in listed):
                    raise Failure('USB_UNAUTHORIZED', 'USB-Debugging auf dem Android-Gerät bestätigen und erneut prüfen.')
                raise Failure('NO_DEVICE', 'Kein erreichbares Android-Gerät. USB-Kabel/Debugging prüfen oder vorbereiteten Emulator starten.')
            return ('targets', ready)
        self.task(work)

    def read(self):
        if self.busy: return
        index = self.device.current()
        if index < 0:
            self.status.set('Bitte zuerst das gewünschte Android-Gerät auswählen.'); return
        self.clear()
        adb, serial = self.adb.get(), self.targets[index]
        self.status.set('Prüfe Voraussetzungen für den Neustart durch Frida …')
        self.scan_requested.clear(); self.cancelled.clear()
        self.cancel_button['state'] = 'normal'
        self.task(lambda: ('keys', read_keys(adb, serial, lambda message: self.events.put(('progress', message)),
                                           self.scan_requested, self.cancelled,
                                           lambda: self.events.put(('ready', None)))))

    def confirm_read(self):
        self.scan_requested.set()
        self.scan_button['state'] = 'disabled'
        self.status.set('Lesen angefordert …')

    def cancel_read(self):
        self.cancelled.set()
        self.scan_button['state'] = self.cancel_button['state'] = 'disabled'
        self.status.set('Leseversuch wird beendet …')

    def server(self):
        if self.busy: return
        index = self.device.current()
        if index < 0:
            self.status.set('Bitte zuerst das gewünschte Android-Gerät auswählen.'); return
        self.clear()
        adb, serial = self.adb.get(), self.targets[index]
        self.status.set('Starte nur den vorhandenen Frida-Server. Eventuelle Root-Abfrage auf Android beachten …')
        self.task(lambda: ('server', start_server(adb, serial)))

    def poll(self):
        try:
            kind, value = self.events.get_nowait()
            if kind == 'ready':
                if not self.cancelled.is_set():
                    self.scan_button['state'] = 'normal'
                self.root.after(100, self.poll)
                return
            if kind == 'progress':
                self.status.set(value)
                self.root.after(100, self.poll)
                return
            self.busy = False
            self.scan_button['state'] = self.cancel_button['state'] = 'disabled'
            self.check_button['state'] = 'normal'
            self.read_button['state'] = self.server_button['state'] = 'normal' if self.targets else 'disabled'
            self.device['state'] = 'readonly'
            self.adb_entry['state'] = 'normal'
            if kind == 'error':
                self.report = {'helper_version': VERSION, 'result': value[0]}
                self.status.set(value[0] + ': ' + value[1])
            elif value[0] == 'targets':
                self.targets = value[1]
                self.device['values'] = [f'Android {i+1} – {s}' for i, s in enumerate(self.targets)]
                if len(self.targets) == 1: self.device.current(0)
                self.read_button['state'] = self.server_button['state'] = 'normal'
                self.status.set('Verbindung vorhanden. Zugangsdaten lesen startet OS Home durch Frida neu; danach die UNICO-Seite öffnen.')
            elif value[0] == 'server':
                self.status.set(value[1])
                self.report = {'helper_version': VERSION, 'result': 'SERVER_READY'}
            else:
                self.rows, report = value[1]
                self.report = {'helper_version': VERSION, **report}
                self.selection['values'] = [f'{i+1}. {r["name"]}' for i, r in enumerate(self.rows)]
                self.status.set('Zugangsdaten gefunden. Frida-Verbindung beendet; kein Beenden von OS Home angefordert. Ob die App weiterläuft, wurde nicht geprüft. Anschließend in HA prüfen.')
                if len(self.rows) == 1: self.selection.current(0); self.show()
        except queue.Empty: pass
        self.root.after(100, self.poll)

    def show(self):
        i = self.selection.current()
        if 0 <= i < len(self.rows):
            for k, v in self.fields.items(): v.set(self.rows[i][k])

    def put_clipboard(self, value):
        self.root.clipboard_clear(); self.root.clipboard_append(value); self.copied = value

    def copy(self, key):
        value = self.fields[key].get()
        if value: self.put_clipboard(value)

    def copy_report(self): self.put_clipboard(json.dumps(self.report, ensure_ascii=False, indent=2))

    def clear_clipboard(self):
        try:
            if self.copied is not None and self.root.clipboard_get() == self.copied: self.root.clipboard_clear()
        except tk.TclError: pass
        self.copied = None

    def clear(self):
        self.clear_clipboard(); self.rows = []; self.selection.set(''); self.selection['values'] = ()
        for var in self.fields.values(): var.set('')

    def close(self):
        if self.busy:
            self.status.set('Bitte den begrenzten Leseversuch abwarten, dann schließen.'); return
        self.clear(); self.root.destroy()


if __name__ == '__main__':
    try:
        root = tk.Tk()
    except tk.TclError:
        print('Das Fenster kann nicht gestartet werden. Python mit Tcl/Tk installieren oder reparieren; siehe LIESMICH.md.')
        sys.exit(1)
    App(root); root.mainloop()
