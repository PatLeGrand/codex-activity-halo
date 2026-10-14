"""Forward MCP unchanged, announcing foreground calls before dispatch."""
import json
import os
import socket
import subprocess
import sys
import threading
import time
from activity import runtime_dir
from server import ensure_overlay


def feedback(op, call):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        sock.connect(str(runtime_dir() / 'feedback.sock'))
        sock.sendall((json.dumps({'op': op, 'call': call}) + '\n').encode())
        return json.loads(sock.makefile('rb').readline(4096))


def foreground_request(message):
    if message.get('method') != 'tools/call':
        return False
    params = message.get('params', {})
    if params.get('name') == 'help':
        return False
    args = params.get('arguments', {})
    args = args.get('arguments', args)
    return args.get('desktop') != 'background'


class Proxy:
    def __init__(self, child):
        self.child = child
        self.pending = {}
        self.lock = threading.RLock()
        self.write_lock = threading.Lock()
        self.output_lock = threading.Lock()
        self.workers = []

    def output(self, line):
        with self.output_lock:
            sys.stdout.write(line)
            sys.stdout.flush()

    def forward(self, line):
        with self.write_lock:
            self.child.stdin.write(line)
            self.child.stdin.flush()

    def reject(self, message, detail):
        self.output(json.dumps({'jsonrpc': '2.0', 'id': message['id'], 'result': {
            'content': [{'type': 'text', 'text': 'Action not started: ' + detail}],
            'isError': True}}) + '\n')

    def prepare(self, message, line, item):
        try:
            response = feedback('begin', item['call'])
            if response.get('error'):
                raise RuntimeError(response['error'])
            if item['cancel'].wait(response.get('wait_ms', 0) / 1000):
                raise RuntimeError('cancelled during the two-second warning')
            readiness = feedback('ready', item['call'])
            if readiness.get('error'):
                raise RuntimeError(readiness['error'])
            with self.lock:
                if item['cancel'].is_set():
                    raise RuntimeError('cancelled before dispatch')
                self.forward(line)
                item['sent'] = True
        except (OSError, ValueError, RuntimeError) as error:
            with self.lock:
                self.pending.pop(str(message['id']), None)
            try:
                feedback('end', item['call'])
            except (OSError, ValueError):
                pass
            self.reject(message, str(error))

    def handle(self, message, line):
        if message.get('method') == 'notifications/cancelled':
            key = str(message.get('params', {}).get('requestId'))
            with self.lock:
                item = self.pending.get(key)
                if item and not item['sent']:
                    item['cancel'].set()
                    return
        if foreground_request(message):
            key = str(message['id'])
            item = {'call': f'{os.getpid()}-{key}', 'cancel': threading.Event(), 'sent': False}
            with self.lock:
                self.pending[key] = item
            worker = threading.Thread(target=self.prepare, args=(message, line, item), daemon=True)
            self.workers = [thread for thread in self.workers if thread.is_alive()]
            self.workers.append(worker)
            worker.start()
        else:
            self.forward(line)

    def read_output(self):
        for line in self.child.stdout:
            try:
                response = json.loads(line)
                with self.lock:
                    item = self.pending.pop(str(response.get('id')), None)
                if item:
                    try:
                        feedback('end', item['call'])
                    except (OSError, ValueError):
                        pass
            except ValueError:
                pass
            self.output(line)


def main():
    ensure_overlay()
    for _ in range(50):
        if (runtime_dir() / 'feedback.sock').exists():
            break
        time.sleep(.1)
    child = subprocess.Popen(sys.argv[1:], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             text=True, bufsize=1)
    proxy = Proxy(child)
    reader = threading.Thread(target=proxy.read_output, daemon=True)
    reader.start()
    try:
        for line in sys.stdin:
            proxy.handle(json.loads(line), line)
    finally:
        with proxy.lock:
            for item in proxy.pending.values():
                if not item['sent']:
                    item['cancel'].set()
        for worker in proxy.workers:
            worker.join(timeout=2)
        child.stdin.close()
        try:
            child.wait(timeout=3)
        except subprocess.TimeoutExpired:
            child.terminate()
        reader.join(timeout=1)
        for item in list(proxy.pending.values()):
            try:
                feedback('end', item['call'])
            except (OSError, ValueError):
                pass


if __name__ == '__main__':
    main()
