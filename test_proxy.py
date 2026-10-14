import io
import json
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from feedback_proxy import Proxy


class ProxyTests(unittest.TestCase):
    def test_cancel_during_warning_never_reaches_backend(self):
        child = SimpleNamespace(stdin=io.StringIO())
        proxy = Proxy(child)
        output = []
        proxy.output = output.append
        began = threading.Event()
        def fake(op, call):
            if op == 'begin':
                began.set()
                return {'wait_ms': 2000}
            return {'ok': True}
        message = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'dispatch', 'arguments': {'action': 'act'}}}
        with patch('feedback_proxy.feedback', fake):
            proxy.handle(message, json.dumps(message) + '\n')
            self.assertTrue(began.wait(1))
            proxy.handle({'method': 'notifications/cancelled', 'params': {'requestId': 1}}, '')
            for worker in proxy.workers:
                worker.join(1)
        self.assertEqual(child.stdin.getvalue(), '')
        self.assertTrue(json.loads(output[0])['result']['isError'])
        self.assertEqual(proxy.pending, {})

    def test_help_and_background_do_not_start_warning(self):
        child = SimpleNamespace(stdin=io.StringIO())
        proxy = Proxy(child)
        for params in [ {'name': 'help'}, {'name': 'dispatch', 'arguments': {'action': 'list_desktop', 'arguments': {'desktop': 'background'}}} ]:
            message = {'id': 1, 'method': 'tools/call', 'params': params}
            with patch('feedback_proxy.feedback') as mocked:
                proxy.handle(message, json.dumps(message) + '\n')
                mocked.assert_not_called()
        self.assertEqual(len(child.stdin.getvalue().splitlines()), 2)

    def test_unavailable_indicator_fails_before_dispatch(self):
        child = SimpleNamespace(stdin=io.StringIO())
        proxy = Proxy(child)
        output = []
        proxy.output = output.append
        message = {'id': 1, 'method': 'tools/call', 'params': {'name': 'dispatch'}}
        with patch('feedback_proxy.feedback', side_effect=OSError('not running')):
            proxy.handle(message, json.dumps(message) + '\n')
            for worker in proxy.workers:
                worker.join(1)
        self.assertEqual(child.stdin.getvalue(), '')
        self.assertTrue(json.loads(output[0])['result']['isError'])

    def test_physical_takeover_during_warning_blocks_dispatch(self):
        child = SimpleNamespace(stdin=io.StringIO())
        proxy = Proxy(child)
        output = []
        proxy.output = output.append
        message = {'id': 1, 'method': 'tools/call', 'params': {'name': 'dispatch'}}
        def fake(op, call):
            if op == 'begin':
                return {'wait_ms': 0}
            if op == 'ready':
                return {'error': 'physical activity detected'}
            return {'ok': True}
        with patch('feedback_proxy.feedback', fake):
            proxy.handle(message, json.dumps(message) + '\n')
            for worker in proxy.workers:
                worker.join(1)
        self.assertEqual(child.stdin.getvalue(), '')
        self.assertIn('physical activity', json.loads(output[0])['result']['content'][0]['text'])


if __name__ == '__main__':
    unittest.main()
