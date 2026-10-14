"""Transparent, non-interactive corner glow for KDE/XWayland."""
import fcntl
import json
import math
import os
import sys
import time
from pathlib import Path

# XWayland supplies reliable above-fullscreen positioning on KDE, while
# WindowTransparentForInput keeps the overlay out of the input path.
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QUrl
from PySide6.QtGui import QColor, QPainter, QRadialGradient, QFont, QIcon, QPixmap, QCursor, QPen
from PySide6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu
from activity import Activity, runtime_dir
from feedback import Session
from PySide6.QtNetwork import QLocalServer
from PySide6.QtMultimedia import QSoundEffect


class Halo(QWidget):
    def __init__(self, screen):
        flags = (Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
                 | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowTransparentForInput
                 | Qt.WindowType.WindowDoesNotAcceptFocus | Qt.WindowType.X11BypassWindowManagerHint)
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowTitle("Codex — indicateur d’activité")
        self.setGeometry(screen.geometry())
        screen.geometryChanged.connect(self.setGeometry)
        self.opacity = 0.0
        self.label = "Codex utilise le PC"

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(self.opacity)
        w, h = self.width(), self.height()
        radius = min(240, w * .2, h * .3)
        for x, y in ((0, 0), (w, 0), (0, h), (w, h)):
            glow = QRadialGradient(QPointF(x, y), radius)
            glow.setColorAt(0, QColor(28, 155, 255, 220))
            glow.setColorAt(.28, QColor(33, 124, 255, 120))
            glow.setColorAt(.66, QColor(40, 88, 245, 42))
            glow.setColorAt(1, QColor(40, 88, 245, 0))
            p.fillRect(self.rect(), glow)
        p.setFont(QFont("Sans Serif", 10))
        width = p.fontMetrics().horizontalAdvance(self.label) + 60
        badge = QRectF((w - width) / 2, 18, width, 34)
        p.setPen(QColor(67, 156, 255, 190))
        p.setBrush(QColor(13, 27, 47, 235))
        p.drawRoundedRect(badge, 17, 17)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(62, 173, 255))
        p.drawEllipse(QPointF(badge.left() + 17, badge.center().y()), 4, 4)
        p.setPen(QColor(233, 244, 255))
        p.drawText(badge.adjusted(30, 0, -10, 0), Qt.AlignmentFlag.AlignCenter, self.label)
        cursor = self.mapFromGlobal(QCursor.pos())
        if self.rect().contains(cursor):
            p.setPen(QPen(QColor(36, 174, 255, 245), 3))
            p.setBrush(QColor(26, 108, 235, 35))
            p.drawEllipse(QPointF(cursor), 15, 15)
            p.setPen(QPen(QColor(227, 247, 255, 235), 1))
            p.drawEllipse(QPointF(cursor), 19, 19)


def main():
    root = runtime_dir()
    lock = (root / "daemon.lock").open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    history = Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "computer-use-mcp/history"
    tracker = Activity(history)
    session = Session()
    sounds = {}
    plays = {"start": 0, "end": 0}
    for name in plays:
        effect = QSoundEffect(app)
        effect.setSource(QUrl.fromLocalFile(str(Path(__file__).parent / "assets" / f"{name}.wav")))
        effect.setVolume(.22)
        sounds[name] = effect
    def play(name):
        sounds[name].play()
        plays[name] += 1
    server = QLocalServer(app)
    socket_path = str(root / "feedback.sock")
    QLocalServer.removeServer(socket_path)
    if not server.listen(socket_path):
        raise RuntimeError(server.errorString())
    clients = set()
    def accept():
        while server.hasPendingConnections():
            client = server.nextPendingConnection()
            clients.add(client)
            def read(client=client):
                if not client.canReadLine():
                    return
                try:
                    request = json.loads(bytes(client.readLine(4096)))
                    op = request.get("op")
                    if op == "cursor":
                        point = QCursor.pos()
                        screen = app.screenAt(point)
                        if screen is None:
                            response = {"error": "Cursor is outside known screens"}
                        else:
                            geometry = screen.geometry()
                            response = {"x": point.x(), "y": point.y(), "screen": screen.name(),
                                        "position": [geometry.x(), geometry.y()],
                                        "size": [geometry.width(), geometry.height()]}
                    elif op == "begin":
                        if sounds["start"].status() != QSoundEffect.Status.Ready:
                            response = {"error": "Start sound is not ready"}
                        else:
                            fresh, wait_ms = session.begin(str(request.get("call")))
                            if fresh:
                                play("start")
                            response = {"wait_ms": wait_ms}
                    elif op == "end":
                        session.end(str(request.get("call")))
                        response = {"ok": True}
                    elif op == "quit":
                        response = {"ok": True}
                        QTimer.singleShot(50, app.quit)
                    else:
                        response = {"error": "Unknown operation"}
                except (ValueError, TypeError):
                    response = {"error": "Invalid request"}
                client.write((json.dumps(response) + "\n").encode())
                client.flush()
            client.readyRead.connect(read)
            def disconnected(client=client):
                clients.discard(client)
                client.deleteLater()
            client.disconnected.connect(disconnected)
    server.newConnection.connect(accept)
    windows = {}
    def add(screen):
        windows[screen] = Halo(screen)
    for screen in app.screens():
        add(screen)
    app.screenAdded.connect(add)
    def remove(screen):
        window = windows.pop(screen, None)
        if window:
            window.close()
    app.screenRemoved.connect(remove)
    icon = QPixmap(32, 32)
    icon.fill(Qt.GlobalColor.transparent)
    painter = QPainter(icon)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(45, 148, 255))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, 24, 24)
    painter.end()
    tray = QSystemTrayIcon(QIcon(icon), app)
    tray.setToolTip("Codex — halo d’activité mirsella")
    menu = QMenu()
    enabled = menu.addAction("Afficher l’indicateur")
    enabled.setCheckable(True)
    enabled.setChecked(True)
    preview = menu.addAction("Aperçu pendant 8 secondes")
    def demo():
        (root / "preview.json").write_text(json.dumps({"until": time.time() + 8}))
    preview.triggered.connect(demo)
    menu.addSeparator()
    menu.addAction("Quitter l’indicateur", app.quit)
    tray.setContextMenu(menu)
    tray.show()
    ticks = 0
    def tick():
        nonlocal ticks
        active = tracker.poll()
        if session.tick():
            play("end")
        active = active or session.active
        demo_until = 0
        try:
            demo_until = json.loads((root / "preview.json").read_text())["until"]
        except (OSError, ValueError, KeyError):
            pass
        demo_active = time.time() < demo_until
        active = enabled.isChecked() and (active or demo_active)
        label = "Codex — aperçu de l’indicateur" if demo_active else tracker.label
        if session.countdown() > 0:
            label = f"Codex commence dans {math.ceil(session.countdown())} s"
        for window in windows.values():
            target = .92 + .08 * math.sin(time.monotonic() * 2) if active else 0
            window.opacity += (target - window.opacity) * .35
            window.label = label
            if window.opacity > .015:
                if not window.isVisible():
                    window.show()
                window.update()
            elif window.isVisible():
                window.hide()
        ticks += 1
        if ticks % 30 == 0:
            state = {"pid": os.getpid(), "enabled": enabled.isChecked(), "active": active,
                     "screens": len(windows), "updated_at": time.time(), "label": label,
                     "audio": {name: effect.status().name for name, effect in sounds.items()},
                     "chimes_played": plays, "feedback_session": session.active}
            temp = root / "status.tmp"
            temp.write_text(json.dumps(state))
            temp.replace(root / "status.json")
    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(33)
    try:
        app.exec()
    finally:
        (root / "status.json").unlink(missing_ok=True)
        tray.hide()
        server.close()
        QLocalServer.removeServer(socket_path)


if __name__ == "__main__":
    main()
