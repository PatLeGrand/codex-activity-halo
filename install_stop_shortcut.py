"""Register the persistent KDE application shortcut without sudo."""
import os
from pathlib import Path
import subprocess

COMPONENT = "codex-stop.desktop"
KEY = 218103825  # Qt Ctrl+Alt+End


def dbus(method, signature, *args):
    return subprocess.check_output(["busctl", "--user", "call", "org.kde.kglobalaccel",
        "/kglobalaccel", "org.kde.KGlobalAccel", method, signature,
        *map(str, args)], text=True).strip()


def main():
    if dbus("isGlobalShortcutAvailable", "is", KEY, COMPONENT) != "b true":
        raise SystemExit("Ctrl+Alt+End is occupied; no existing shortcut was changed.")
    folder = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "kglobalaccel"
    folder.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve().with_name("stop_control.py")
    (folder / COMPONENT).write_text(f"[Desktop Entry]\nType=Application\nName=Arrêter le contrôle Codex\nExec=/usr/bin/python3 \"{script}\"\nIcon=process-stop\nNoDisplay=true\nX-KDE-Shortcuts=Ctrl+Alt+End\n")
    action = [4, COMPONENT, "_launch", "Codex", "Arrêter le contrôle Codex"]
    dbus("doRegister", "as", *action)
    result = dbus("setShortcut", "asaiu", *action, 1, KEY, 0)
    if str(KEY) not in result:
        raise SystemExit(f"Shortcut registration failed: {result}")
    print("Ctrl+Alt+End registered:", result)


if __name__ == "__main__":
    main()
