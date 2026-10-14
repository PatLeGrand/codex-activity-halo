"""Transparent, non-interactive corner glow for KDE/XWayland."""
import fcntl
import json
import math
import os
import sys
import socket
import struct
import time
from pathlib import Path

# XWayland supplies reliable above-fullscreen positioning on KDE, while
# WindowTransparentForInput keeps the overlay out of the input path.
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, QUrl, QSocketNotifier
from PySide6.QtGui import QColor, QPainter, QRadialGradient, QFont, QIcon, QPixmap, QCursor, QPen
from PySide6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QPushButton
from activity import Activity, runtime_dir
from feedback import Session, control_caption
from takeover_state import Takeover
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
        self.paused = False
        self.opacity = 0.0
        self.label = "Codex utilise le PC"

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(self.opacity)
        w, h = self.width(), self.height()
        blue = QColor(255, 172, 47) if self.paused else QColor(36, 174, 255)
        radius = min(240, w * .2, h * .3)
        for x, y in ((0, 0), (w, 0), (0, h), (w, h)):
            glow = QRadialGradient(QPointF(x, y), radius)
            glow.setColorAt(0, QColor(blue.red(), blue.green(), blue.blue(), 220))
            glow.setColorAt(.28, QColor(blue.red(), blue.green(), blue.blue(), 120))
            glow.setColorAt(.66, QColor(blue.red(), blue.green(), blue.blue(), 42))
            glow.setColorAt(1, QColor(blue.red(), blue.green(), blue.blue(), 0))
            p.fillRect(QRectF(x - radius, y - radius, radius * 2, radius * 2).intersected(QRectF(self.rect())), glow)
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
            p.setPen(QPen(QColor(blue.red(), blue.green(), blue.blue(), 245), 3))
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
    takeover = Takeover()
    takeover_path = Path(os.environ.get("XDG_RUNTIME_DIR", str(root.parent))) / "computer-use-mcp-takeover"
    takeover.paused = takeover_path.exists()
    def stop_control():
        first = not takeover.paused
        takeover.paused = True
        takeover_path.touch(mode=0o600, exist_ok=True)
        session.active = False
        if first:
            play("end")
    activity_path = root / "activity.sock"
    activity_path.unlink(missing_ok=True)
    activity_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    activity_socket.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    activity_socket.bind(str(activity_path))
    activity_path.chmod(0o600)
    activity_socket.setblocking(False)
    activity_notifier = QSocketNotifier(activity_socket.fileno(), QSocketNotifier.Type.Read, app)
    def physical_activity(*_):
        while True:
            try:
                data, ancillary, _, _ = activity_socket.recvmsg(1024, socket.CMSG_SPACE(12))
            except BlockingIOError:
                break
            credentials = [struct.unpack("3i", value[:12]) for level, kind, value in ancillary
                           if level == socket.SOL_SOCKET and kind == socket.SCM_CREDENTIALS]
            if not credentials or credentials[0][1] != os.getuid():
                continue
            try:
                message = json.loads(data)
                already_paused = takeover.paused
                if takeover.signal(message, session.active):
                    # signal() latches the logical state; stop_control writes the
                    # existing native cooperative interruption signal immediately.
                    takeover.paused = already_paused
                    stop_control()
            except (ValueError, TypeError, AttributeError):
                pass
    activity_notifier.activated.connect(physical_activity)
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
                    elif op == "ready":
                        response = {"ok": True} if takeover.allowed() else {"error": "Physical control resumed or monitoring unavailable; desktop call blocked"}
                    elif op == "begin":
                        if not takeover.allowed():
                            response = {"error": "Human takeover monitoring is unavailable, a key is held, or control is paused"}
                        elif sounds["start"].status() != QSoundEffect.Status.Ready:
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
    resume = menu.addAction("Reprendre le contrôle Codex")
    def resume_control():
        session.active = False
        takeover.resume()
        takeover_path.unlink(missing_ok=True)
    resume.triggered.connect(resume_control)
    control_button = QPushButton()
    control_button.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
                                 | Qt.WindowType.WindowDoesNotAcceptFocus)
    control_button.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    control_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    control_button.setWindowTitle("Codex — contrôle du PC")
    control_button.setFixedSize(320, 64)
    def position_control():
        screen = next((s for s in app.screens() if s.name() == "HDMI-A-1"), app.primaryScreen())
        rect = screen.availableGeometry()
        control_button.move(rect.right() - control_button.width() - 16, rect.top() + 70)
    position_control()
    for screen in app.screens():
        screen.availableGeometryChanged.connect(lambda *_: position_control())
    def toggle_control():
        if takeover.paused:
            resume_control()
        else:
            stop_control()
    control_button.clicked.connect(toggle_control)
    menu.addSeparator()
    menu.addAction("Quitter l’indicateur", app.quit)
    tray.setContextMenu(menu)
    tray.show()
    ticks = 0
    def tick():
        nonlocal ticks
        active = tracker.poll()
        if session.active and not takeover.ready():
            stop_control()
        if session.tick():
            play("end")
        active = active or session.active or takeover.paused
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
        if takeover.paused:
            label = "Vous avez la main — Codex suspendu"
        resume.setEnabled(takeover.paused)
        control_button.setText(control_caption(takeover.paused, session.countdown()))
        color = "#c77816" if takeover.paused else "#176bc2"
        control_button.setStyleSheet(f"QPushButton {{ background: {color}; color: white; font-size: 14px; padding: 6px; border-radius: 8px; }}")
        control_button.setVisible(takeover.paused or session.active)
        for window in windows.values():
            target = .92 + .08 * math.sin(time.monotonic() * 2) if active else 0
            window.opacity += (target - window.opacity) * .35
            window.label = label
            window.paused = takeover.paused
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
                     "chimes_played": plays, "feedback_session": session.active,
                     "human_monitor_ready": takeover.ready(), "human_paused": takeover.paused,
                     "human_input_held": takeover.held}
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
        control_button.close()
        tray.hide()
        server.close()
        QLocalServer.removeServer(socket_path)
        activity_socket.close()
        activity_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
