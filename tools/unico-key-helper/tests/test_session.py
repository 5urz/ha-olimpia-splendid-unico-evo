"""Exercise real local subprocess pipes with a synthetic CLI; no Android/Frida."""
import queue
import sys
import threading
import unittest
from unittest.mock import patch, MagicMock
from test_helper import h, payload, row


class SessionTests(unittest.TestCase):
    def invoke(self, script, request=None, cancel=None, ready=lambda: None):
        return h.run_frida([sys.executable, '-u', '-c', script],
                           request if request is not None else threading.Event(),
                           cancel if cancel is not None else threading.Event(), ready, lambda _: None)

    def test_waits_for_manual_request_then_quits_gracefully(self):
        request, ready = threading.Event(), threading.Event()
        outcomes = queue.Queue()
        script = "import sys; print('UNICO_READER_V1:STARTED', flush=True); command=input(); assert command=='globalThis.unicoRead();'; print('[Device::app]-> '+" + repr(payload([row()])) + ", flush=True); assert input()=='exit'"
        def work():
            try:
                outcomes.put(self.invoke(script, request=request, ready=ready.set))
            except Exception as err:
                outcomes.put(err)
        worker = threading.Thread(target=work)
        worker.start()
        try:
            self.assertTrue(ready.wait(5))
            # The subprocess blocks on input; no automatic read or CLI timeout.
            with self.assertRaises(queue.Empty):
                outcomes.get(timeout=0.2)
            request.set()
            result = outcomes.get(timeout=10)
            if isinstance(result, Exception):
                raise result
            self.assertEqual(h.parse_result(result.stdout), [row()])
            self.assertEqual(result.session_end, 'helper_quit_after_read')
            self.assertEqual(result.returncode, 0)
        finally:
            request.set()
            worker.join(timeout=10)
        self.assertFalse(worker.is_alive())

    def test_cancel_while_waiting(self):
        cancel = threading.Event()
        script = "print('UNICO_READER_V1:STARTED', flush=True); assert input()=='exit'"
        with self.assertRaises(h.Failure) as ctx:
            self.invoke(script, cancel=cancel, ready=cancel.set)
        self.assertEqual(ctx.exception.code, 'CANCELLED')

    def test_detects_app_termination_before_read(self):
        script = "print('UNICO_READER_V1:STARTED'); print('Process terminated'); input()"
        with self.assertRaises(h.Failure) as ctx:
            self.invoke(script)
        self.assertEqual(ctx.exception.code, 'APP_TERMINATED')

    def test_session_disappears_while_waiting(self):
        with self.assertRaises(h.Failure) as ctx:
            self.invoke("print('UNICO_READER_V1:STARTED')")
        self.assertEqual(ctx.exception.code, 'SESSION_ENDED')

    def test_start_failure_returns_private_output_for_classification(self):
        result = self.invoke("import sys; print('Failed to spawn: synthetic'); sys.exit(1)")
        self.assertEqual(result.returncode, 1)

    def test_phase_specific_timeouts(self):
        cases = [
            ('START_TIMEOUT', "input()", None, 'SPAWN_TIMEOUT'),
            ('PAGE_TIMEOUT', "print('UNICO_READER_V1:STARTED', flush=True); input()", None, 'PAGE_TIMEOUT'),
            ('SCAN_TIMEOUT', "print('UNICO_READER_V1:STARTED', flush=True); input(); input()", True, 'READER_TIMEOUT'),
        ]
        for limit, script, do_read, code in cases:
            request = threading.Event()
            if do_read:
                request.set()
            with self.subTest(code=code), patch.object(h, limit, 0.1), self.assertRaises(h.Failure) as ctx:
                self.invoke(script, request=request)
            self.assertEqual(ctx.exception.code, code)

    def test_gui_ready_keeps_other_controls_locked_and_cancel_wins(self):
        app = h.App.__new__(h.App)
        app.root = MagicMock()
        app.events = queue.Queue()
        app.busy = True
        app.cancelled = threading.Event()
        app.scan_button = {'state': 'disabled'}
        app.events.put(('ready', None))
        app.poll()
        self.assertTrue(app.busy)
        self.assertEqual(app.scan_button['state'], 'normal')
        app.scan_button['state'] = 'disabled'
        app.cancelled.set()
        app.events.put(('ready', None))
        app.poll()
        self.assertEqual(app.scan_button['state'], 'disabled')


if __name__ == '__main__':
    unittest.main()
