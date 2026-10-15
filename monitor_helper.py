#!/usr/bin/python3
"""Read physical evdev activity; emit only activity/held/coverage booleans.

The service opens read-only device FDs as root, then permanently drops to the
specified user before processing any events. There is no input-injection API.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import selectors
import socket
import struct
import sys
import time

EVENT = struct.Struct('@llHHi')
KEY_BYTES = 128
EVIOCGKEY = (2 << 30) | (KEY_BYTES << 16) | (ord('E') << 8) | 0x18


def bitmap(text):
    bits = struct.calcsize('L') * 8
    return sum(int(word, 16) << (i * bits) for i, word in enumerate(reversed(text.split())))


def device_kind(path):
    try:
        device = path / 'device'
        bus = int((device / 'id/bustype').read_text().strip(), 16)
        # BUS_VIRTUAL and devices without a real bus are not physical sources.
        if bus in (0, 6):
            return None
        keys = bitmap((device / 'capabilities/key').read_text())
        events = bitmap((device / 'capabilities/ev').read_text())
        keyboard = bool(keys & (1 << 30) and keys & (1 << 28))
        pointer = bool(events & ((1 << 2) | (1 << 3)) or keys & (1 << 272))
        if keyboard or pointer:
            return keyboard, pointer
    except (OSError, ValueError):
        pass
    return None


def discover():
    result = []
    for path in sorted(Path('/sys/class/input').glob('event*')):
        kind = device_kind(path)
        if kind:
            result.append((Path('/dev/input') / path.name, *kind))
    return result


def event_activity(data, absolute):
    changed = False
    for offset in range(0, len(data) - EVENT.size + 1, EVENT.size):
        _, _, kind, code, value = EVENT.unpack_from(data, offset)
        if kind == 1 and value >= 0:
            changed = True
        elif kind == 2 and value != 0:
            changed = True
        elif kind == 3:
            previous = absolute.get(code)
            absolute[code] = value
            if previous != value:
                changed = True
    return changed


def held(fd):
    buffer = bytearray(KEY_BYTES)
    fcntl.ioctl(fd, EVIOCGKEY, buffer, True)
    return any(buffer)


def packet(activity, is_held, keyboard_count, pointer_count):
    # Never include key/button codes, pointer coordinates, or raw input bytes.
    return {'activity': bool(activity), 'held': bool(is_held),
            'keyboard_devices': keyboard_count, 'pointer_devices': pointer_count,
            'monitor': 'codex-input-activity'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--uid', type=int)
    parser.add_argument('--gid', type=int)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    devices = discover()
    if args.check:
        print(json.dumps({'devices': len(devices), 'keyboards': sum(k for _, k, _ in devices),
                          'pointers': sum(p for _, _, p in devices)}))
        return
    if os.geteuid() != 0 or not args.uid or args.uid < 1000 or args.gid is None:
        raise SystemExit('Run the system service installer; direct root startup needs a normal user UID/GID.')
    selector = selectors.DefaultSelector()
    opened = []
    for path, keyboard, pointer in devices:
        fd = None
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW)
            held(fd)  # Require the same held-key query that will be used later.
            item = {'fd': fd, 'path': path, 'keyboard': keyboard, 'pointer': pointer,
                    'buffer': b'', 'absolute': {}}
            selector.register(fd, selectors.EVENT_READ, item)
            opened.append(item)
        except OSError:
            if fd is not None:
                os.close(fd)
    keyboards = sum(d['keyboard'] for d in opened)
    pointers = sum(d['pointer'] for d in opened)
    if len(opened) != len(devices) or not keyboards or not pointers:
        raise SystemExit('No complete physical keyboard/pointer coverage; monitoring unavailable.')
    # Retain only the already-open read-only FDs; never retain root authority.
    os.setgroups([])
    os.setgid(args.gid)
    os.setuid(args.uid)
    if os.geteuid() != args.uid:
        raise SystemExit('Privilege drop failed.')
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    address = f'/run/user/{args.uid}/codex-activity-halo/activity.sock'
    known = {str(path) for path, _, _ in devices}
    last_heartbeat = 0.0
    last_scan = 0.0
    pending = False
    print(f'Physical activity detector running without root on {len(opened)} devices.', flush=True)
    while True:
        for key, _ in selector.select(.02):
            item = key.data
            try:
                data = os.read(item['fd'], EVENT.size * 256)
                if not data:
                    raise SystemExit('An input device disconnected; restart to refresh coverage.')
            except BlockingIOError:
                continue
            item['buffer'] += data
            size = len(item['buffer']) // EVENT.size * EVENT.size
            pending = event_activity(item['buffer'][:size], item['absolute']) or pending
            item['buffer'] = item['buffer'][size:]
        now = time.monotonic()
        if pending or now - last_heartbeat >= .5:
            try:
                is_held = any(held(d['fd']) for d in opened)
                sock.sendto(json.dumps(packet(pending, is_held, keyboards, pointers)).encode(), address)
            except (ConnectionRefusedError, FileNotFoundError):
                pass  # The user companion may not be running yet.
            except OSError:
                raise SystemExit('Input monitoring failed; restart to refresh devices.')
            pending = False
            last_heartbeat = now
        if now - last_scan >= 1:
            if {str(path) for path, _, _ in discover()} != known:
                raise SystemExit('Input devices changed; restart to refresh coverage.')
            last_scan = now


if __name__ == '__main__':
    main()
