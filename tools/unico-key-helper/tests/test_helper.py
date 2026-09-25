import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1] / 'helper.py'
spec = importlib.util.spec_from_file_location('helper', FILE)
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)

def row(**kw):
    return dict(name='UNICO', device_id='testdevice1234567890123', local_key='0123456789abcdef', host='192.168.1.22', **kw)

def payload(rows, **kw):
    return h.PREFIX + json.dumps(dict(schema=1, devices=rows, **kw))

class ReaderTests(unittest.TestCase):
    def setUp(self):
        # Orchestration tests simulate the interactive transport separately.
        # Its actual pipes, cancellation and timing are covered in test_session.py.
        def transport(args, *unused):
            result = h.run(args, 50)
            result.session_end = 'helper_quit_after_read'
            return result
        mocked = patch.object(h, 'run_frida', side_effect=transport)
        mocked.start()
        self.addCleanup(mocked.stop)

    def test_adb_states(self):
        self.assertEqual(h.devices('List of devices attached\na device\nb unauthorized\nc offline\n* daemon started successfully *'), [('a','device'),('b','unauthorized'),('c','offline')])

    def test_dedup(self):
        self.assertEqual(len(h.parse_result(payload([row(), row()]))), 1)

    def test_conflict(self):
        other = row(); other['local_key'] = 'fedcba9876543210'
        with self.assertRaises(h.Failure) as ctx: h.parse_result(payload([row(), other]))
        self.assertEqual(ctx.exception.code, 'CONFLICT')
        self.assertNotIn(other['local_key'], str(ctx.exception))

    def test_invalid_values_are_not_credentials(self):
        for key in ('', 'null', '<unavailable>', 'short', 'A'*17, '\n'+'A'*15):
            r = row(); r['local_key'] = key
            with self.subTest(key=key), self.assertRaises(h.Failure): h.parse_result(payload([r]))

    def test_ip_not_required_and_suspicious_ip_discarded(self):
        for host in ('', 'null', '8.8.8.8', '127.0.0.1', '0.0.0.0', '169.254.1.1'):
            r = row(); r['host'] = host
            self.assertEqual(h.parse_result(payload([r]))[0]['host'], '')

    def test_missing_duplicate_or_truncated_results(self):
        for raw in ('no result', payload([row()])+'\n'+payload([row()]), payload([row()], truncated=True)):
            with self.assertRaises(h.Failure): h.parse_result(raw)

    def test_bad_formats(self):
        for raw in ('[]', '{}', 'null', '"secret"', '{', '{"schema":1,"devices":"secret"}'):
            with self.assertRaises(h.Failure): h.parse_result(h.PREFIX+raw)

    def test_no_external_diagnostics_echo(self):
        with self.assertRaises(h.Failure) as ctx: h.parse_result('password=not-for-display')
        self.assertNotIn('not-for-display', str(ctx.exception))

    def test_ansi_and_valid_records(self):
        self.assertEqual(h.parse_result('\x1b[32m'+payload([row()])+'\x1b[0m')[0], row())

    def test_java_unavailable(self):
        with self.assertRaises(h.Failure) as ctx: h.parse_result(h.PREFIX+'{"schema":1,"error":"JAVA_UNAVAILABLE"}')
        self.assertEqual(ctx.exception.code, 'APP_UNSUPPORTED')

    @patch.object(h.importlib.metadata, 'version', return_value='16.7.19')
    def test_read_stops_selected_device_then_spawns_with_reader(self, _):
        results = [subprocess.CompletedProcess([],0,'versionName=2.0.7',''), subprocess.CompletedProcess([],0,'16.7.19\n',''), subprocess.CompletedProcess([],0,'1234\n',''), subprocess.CompletedProcess([],0,payload([row()]),'')]
        with patch.object(h, 'run', side_effect=results) as run:
            rows, report = h.read_keys('adb.exe', 'test-serial')
        args = run.call_args_list[-1].args[0]
        self.assertNotIn('-p', args)
        self.assertNotIn('-q', args)
        self.assertNotIn('-t', args)
        self.assertEqual(args[args.index('-f')+1], h.PACKAGE)
        self.assertEqual(args[args.index('-l')+1], str(h.BASE / 'reader.js'))
        self.assertNotIn('--pause', args)
        self.assertNotIn('--kill-on-exit', args)
        self.assertEqual(run.call_args_list[2].args[0], ['adb.exe', '-s', 'test-serial', 'shell', 'am', 'force-stop', h.PACKAGE])
        self.assertFalse(any('pidof' in c.args[0] for c in run.call_args_list))
        self.assertEqual(report['read_mode'], 'spawn')
        self.assertEqual(report['read_trigger'], 'manual')
        self.assertEqual(args[args.index('-D')+1], 'test-serial')
        self.assertNotIn('local_key', report)
        self.assertNotIn(rows[0]['device_id'], json.dumps(report))

    @patch.object(h.importlib.metadata, 'version', return_value='16.7.19')
    def test_version_mismatch_stops_before_force_stop(self, _):
        results = [subprocess.CompletedProcess([],0,'versionName=2.0.7',''), subprocess.CompletedProcess([],0,'16.7.18','')]
        with patch.object(h, 'run', side_effect=results) as run, self.assertRaises(h.Failure) as ctx: h.read_keys('adb', 'serial')
        self.assertEqual(ctx.exception.code, 'VERSION_MISMATCH'); self.assertEqual(run.call_count, 2)

    @patch.object(h.importlib.metadata, 'version', return_value='16.7.19')
    def test_failed_spawn_discards_raw_stderr(self, _):
        results = [subprocess.CompletedProcess([],0,'versionName=2.0.3',''), subprocess.CompletedProcess([],0,'16.7.19',''), subprocess.CompletedProcess([],0,'123',''), subprocess.CompletedProcess([],1,'','SECRET')]
        with patch.object(h, 'run', side_effect=results), self.assertRaises(h.Failure) as ctx: h.read_keys('adb', 'serial')
        self.assertNotIn('SECRET', str(ctx.exception)); self.assertEqual(ctx.exception.code, 'SPAWN_FAILED')

    def test_timeout_does_not_echo_process_output(self):
        with patch.object(h.subprocess, 'run', side_effect=subprocess.TimeoutExpired('cmd', 1, output='SECRET')), self.assertRaises(h.Failure) as ctx: h.run(['cmd'])
        self.assertNotIn('SECRET', str(ctx.exception))

    @patch.object(h.importlib.metadata, 'version', return_value='16.7.19')
    def test_server_already_running_is_not_restarted(self, _):
        results = [subprocess.CompletedProcess([],0,'16.7.19',''), subprocess.CompletedProcess([],0,'123','')]
        with patch.object(h, 'run', side_effect=results) as run:
            self.assertIn('bereits', h.start_server('adb', 'serial'))
        self.assertEqual(run.call_count, 2)

    @patch.object(h.importlib.metadata, 'version', return_value='16.7.19')
    def test_server_start_uses_existing_root_only(self, _):
        results = [subprocess.CompletedProcess([],0,'16.7.19',''), subprocess.CompletedProcess([],1,'',''), subprocess.CompletedProcess([],0,'uid=2000(shell)',''), subprocess.CompletedProcess([],0,'uid=0(root)',''), subprocess.CompletedProcess([],0,'','')]
        with patch.object(h, 'run', side_effect=results) as run:
            h.start_server('adb', 'serial')
        self.assertEqual(run.call_args.args[0][-1], "su -c '/data/local/tmp/frida-server -D'")
        self.assertTrue(all(c.args[0][1:3] == ['-s','serial'] for c in run.call_args_list))

    @patch.object(h.importlib.metadata, 'version', return_value='16.7.19')
    def test_no_root_stops_server_start(self, _):
        results = [subprocess.CompletedProcess([],0,'16.7.19',''), subprocess.CompletedProcess([],1,'',''), subprocess.CompletedProcess([],0,'uid=2000(shell)',''), subprocess.CompletedProcess([],1,'','denied')]
        with patch.object(h, 'run', side_effect=results) as run, self.assertRaises(h.Failure) as ctx: h.start_server('adb', 'serial')
        self.assertEqual(ctx.exception.code, 'ROOT_MISSING'); self.assertEqual(run.call_count, 4)


    @patch.object(h.importlib.metadata, 'version', side_effect=lambda name: '13.7.1' if name == 'frida-tools' else '16.7.19')
    def test_spawn_and_reader_failures_are_separate(self, _):
        cp = lambda rc=0, out='', err='': subprocess.CompletedProcess([], rc, out, err)
        for last, code in [
            (cp(1, '', 'Failed to spawn: SECRET'), 'SPAWN_FAILED'),
            (cp(1, '', 'Failed to load script: SECRET'), 'READER_LOAD_FAILED'),
            (cp(1, h.READER_STARTED, 'SECRET'), 'READER_FAILED'),
            (cp(1, payload([row()]), 'SECRET'), 'READER_FAILED'),
            (cp(0, h.READER_STARTED), 'NO_RESULT'),
            (cp(0, payload([])), 'NO_KEYS'),
            (cp(0, h.PREFIX+'{"schema":1,"error":"SCAN_FAILED"}'), 'APP_UNSUPPORTED'),
            (cp(0, h.PREFIX+'{'), 'BAD_RESULT'),
            (h.Failure('TIMEOUT', 'SECRET'), 'FRIDA_TIMEOUT'),
            (h.Failure('PROGRAM_BLOCKED', 'SECRET'), 'FRIDA_START_FAILED'),
        ]:
            with self.subTest(code=code), patch.object(h, 'run', side_effect=[cp(out='versionName=2.0.7'), cp(out='16.7.19'), cp(), last]), self.assertRaises(h.Failure) as ctx:
                h.read_keys('adb', 'serial')
            self.assertEqual(ctx.exception.code, code)
            self.assertNotIn('SECRET', str(ctx.exception))

    @patch.object(h.importlib.metadata, 'version', return_value='16.7.19')
    def test_force_stop_failure_prevents_spawn(self, _):
        cp = lambda rc=0, out='', err='': subprocess.CompletedProcess([], rc, out, err)
        for last in [cp(1, '', 'SECRET'), cp(0, 'Error: SECRET'), h.Failure('TIMEOUT', 'SECRET')]:
            with self.subTest(last=type(last)), patch.object(h, 'run', side_effect=[cp(out='versionName=2.0.7'), cp(out='16.7.19'), last]) as run, self.assertRaises(h.Failure) as ctx:
                h.read_keys('adb', 'serial')
            self.assertEqual(ctx.exception.code, 'STOP_FAILED')
            self.assertEqual(run.call_count, 3)
            self.assertNotIn('SECRET', str(ctx.exception))

    @patch.object(h.importlib.metadata, 'version', return_value='16.7.19')
    def test_missing_reader_prevents_force_stop(self, _):
        cp = lambda out: subprocess.CompletedProcess([], 0, out, '')
        with patch.object(h, 'run', side_effect=[cp('versionName=2.0.7'), cp('16.7.19')]) as run, patch.object(h.Path, 'is_file', return_value=False), self.assertRaises(h.Failure) as ctx:
            h.read_keys('adb', 'serial')
        self.assertEqual(ctx.exception.code, 'READER_MISSING')
        self.assertEqual(run.call_count, 2)

    @patch.object(h.importlib.metadata, 'version', side_effect=lambda name: '13.7.1' if name == 'frida-tools' else '16.7.19')
    def test_progress_and_known_versions(self, _):
        cp = lambda out: subprocess.CompletedProcess([], 0, out, '')
        progress = []
        with patch.object(h, 'run', side_effect=[cp('versionName=2.0.3'), cp('16.7.19'), cp(''), cp(h.READER_STARTED+'\n'+payload([row()]))]):
            rows, report = h.read_keys('adb', 'serial', progress.append)
        self.assertEqual(len(progress), 3)
        self.assertEqual(report['frida_version'], '16.7.19')
        self.assertEqual(report['frida_tools_version'], '13.7.1')
        self.assertEqual(report['result'], 'READ_OK')
        self.assertNotIn(rows[0]['local_key'], json.dumps(report))

if __name__ == '__main__': unittest.main(verbosity=2)
