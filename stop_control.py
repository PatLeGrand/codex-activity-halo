"""Global stop: assert the native latch even if the companion is unavailable."""
import json
import os
from pathlib import Path
import socket
from activity import runtime_dir


def stop():
    root = runtime_dir()
    flag = Path(os.environ.get("XDG_RUNTIME_DIR", str(root.parent))) / "computer-use-mcp-takeover"
    fd = os.open(flag, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    os.close(fd)
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(2)
            client.connect(str(root / "feedback.sock"))
            client.sendall(b'{"op":"stop"}\n')
            response = json.loads(client.makefile("rb").readline(4096))
            if not response.get("ok"):
                raise RuntimeError("Companion did not acknowledge stop")
    except OSError:
        # The native signal persists and will be read at companion startup.
        pass


if __name__ == "__main__":
    stop()
