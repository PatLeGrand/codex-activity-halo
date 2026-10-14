"""MCP companion: start the halo and expose status / a labelled preview."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from activity import runtime_dir

ROOT = Path(__file__).resolve().parent


def ensure_overlay():
    root = runtime_dir()
    try:
        state = json.loads((root / "status.json").read_text())
        if time.time() - state["updated_at"] < 3 and Path(f'/proc/{state["pid"]}').exists():
            return
    except (OSError, ValueError, KeyError):
        pass
    with (root / "overlay.log").open("a") as log:
        subprocess.Popen([sys.executable, str(ROOT / "overlay.py")],
                         stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                         start_new_session=True, env={**os.environ, "QT_QPA_PLATFORM": "xcb"})


def main():
    ensure_overlay()
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except ValueError:
            continue
        if "id" not in message:
            continue
        method = message.get("method")
        result, error = {}, None
        if method == "initialize":
            result = {"protocolVersion": message.get("params", {}).get("protocolVersion", "2024-11-05"),
                      "capabilities": {"tools": {}}, "serverInfo": {"name": "activity-halo", "version": "0.3.2"}}
        elif method == "tools/list":
            result = {"tools": [
                {"name": "status", "description": "Read whether the blue desktop activity halo is running.",
                 "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
                 "annotations": {"readOnlyHint": True}},
                {"name": "preview", "description": "Show a clearly labelled blue corner halo preview for eight seconds.",
                 "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}}]}
        elif method == "tools/call":
            name = message.get("params", {}).get("name")
            if name not in {"status", "preview"}:
                error = {"code": -32602, "message": "Unknown tool"}
            else:
                if name == "preview":
                    ensure_overlay()
                    (runtime_dir() / "preview.json").write_text(json.dumps({"until": time.time() + 8}))
                    text = "Aperçu du halo bleu lancé pour 8 secondes."
                else:
                    try:
                        text = (runtime_dir() / "status.json").read_text()
                    except OSError:
                        text = '{"running":false}'
                result = {"content": [{"type": "text", "text": text}]}
        elif method != "ping":
            error = {"code": -32601, "message": "Method not found"}
        response = {"jsonrpc": "2.0", "id": message["id"]}
        response["error" if error else "result"] = error or result
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
