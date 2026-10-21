import sys, subprocess, importlib.util

# Modo auxiliar integrado: el mismo ejecutable se copia temporalmente y se
# vuelve a lanzar para reemplazar el .exe principal cuando ya no esté en uso.
def _run_embedded_updater():
    import os, time, shutil, subprocess
    from pathlib import Path
    args = sys.argv
    if len(args) < 5 or args[1] != "--openanime-apply-update":
        return False
    target, staged, parent_pid = Path(args[2]), Path(args[3]), int(args[4])
    try:
        for _ in range(120):
            try:
                os.kill(parent_pid, 0)
                time.sleep(1)
            except OSError:
                break
        if not staged.is_file() or staged.stat().st_size < 1_000_000:
            raise RuntimeError("El archivo descargado no parece un ejecutable válido.")
        backup = target.with_suffix(target.suffix + ".bak")
        if target.exists():
            shutil.copy2(target, backup)
        os.replace(str(staged), str(target))
        subprocess.Popen([str(target)], cwd=str(target.parent), close_fds=True)
        try:
            Path(sys.executable).unlink(missing_ok=True)
        except Exception:
            pass
    except Exception:
        # Intenta recuperar la copia previa si el reemplazo no pudo completarse.
        try:
            backup = target.with_suffix(target.suffix + ".bak")
            if backup.exists():
                shutil.copy2(backup, target)
                subprocess.Popen([str(target)], cwd=str(target.parent), close_fds=True)
        except Exception:
            pass
    return True


if _run_embedded_updater():
    raise SystemExit(0)


def _ensure_deps():
    needed = {"requests": "requests", "bs4": "beautifulsoup4", "PySide6": "PySide6", "yt_dlp": "yt-dlp"}
    missing = [pkg for mod, pkg in needed.items() if importlib.util.find_spec(mod) is None]
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])


if not getattr(sys, "frozen", False):
    _ensure_deps()

import re, json, base64, time, ctypes, os, shutil
from pathlib import Path
from urllib.parse import urljoin, quote_plus

import requests
from bs4 import BeautifulSoup
from PySide6.QtCore import (Qt, QObject, Signal, Slot, QRunnable, QThreadPool, QUrl, QSize, QTimer,
                            QPropertyAnimation, QEasingCurve, QByteArray, QAbstractAnimation, QPoint)
from PySide6.QtGui import QPixmap, QColor, QPainter, QIcon, QDesktopServices, QGuiApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy,
    QScrollArea, QStackedWidget, QLineEdit, QFrame, QGridLayout, QButtonGroup, QDialog,
    QListWidget, QListWidgetItem, QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QProgressBar, QFileDialog, QMessageBox,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineSettings, QWebEngineUrlRequestInterceptor
)

APP_NAME = "OpenAnime"
BASE = "https://latanime.org"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "es-ES,es;q=0.9", "Referer": BASE + "/"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
DATA_FILE = Path.home() / ".openanime_data.json"
ACCENT = "#60CDFF"
CREATOR = "Kyuu TB Tech"
CHANNEL_URL = "https://youtube.com/@kyuutbtech?si=u3_8Z3iJPxLfVfPO"
LATANIME_URL = "https://latanime.org"
VERSION = "1.1.0"
GITHUB_REPO = "JGRyuuTB/OpenAnime"

ICONS = {
    "youtube": "M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z",
    "verified": "M23 12l-2.44-2.79.34-3.69-3.61-.82-1.89-3.2L12 2.96 8.6 1.5 6.71 4.69 3.1 5.5l.34 3.7L1 12l2.44 2.79-.34 3.7 3.61.82L8.6 22.5l3.4-1.47 3.4 1.46 1.89-3.19 3.61-.82-.34-3.69L23 12zm-12.91 4.72l-3.8-3.81 1.48-1.48 2.32 2.33 5.85-5.87 1.48 1.48-7.33 7.35z",
    "heart": "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z",
    "home": "M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z",
    "grid": "M4 8h4V4H4v4zm6 12h4v-4h-4v4zm-6 0h4v-4H4v4zm0-6h4v-4H4v4zm6 0h4v-4h-4v4zm6-10v4h4V4h-4zm-6 4h4V4h-4v4zm6 6h4v-4h-4v4zm0 6h4v-4h-4v4z",
    "live": "M12 11c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm6 2c0-3.31-2.69-6-6-6s-6 2.69-6 6c0 2.22 1.21 4.15 3 5.19l1-1.74c-1.19-.7-2-1.97-2-3.45 0-2.21 1.79-4 4-4s4 1.79 4 4c0 1.48-.81 2.75-2 3.45l1 1.74c1.79-1.04 3-2.97 3-5.19zM12 3C6.48 3 2 7.48 2 13c0 3.7 2.01 6.92 4.99 8.65l1-1.73C5.61 18.53 4 15.96 4 13c0-4.42 3.58-8 8-8s8 3.58 8 8c0 2.96-1.61 5.53-4 6.92l1 1.73c2.99-1.73 5-4.95 5-8.65 0-5.52-4.48-10-10-10z",
    "star": "M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z",
    "star_o": "M22 9.24l-7.19-.62L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.63-7.03L22 9.24zM12 15.4l-3.76 2.27 1-4.28-3.32-2.88 4.38-.38L12 6.1l1.71 4.04 4.38.38-3.32 2.88 1 4.28L12 15.4z",
    "history": "M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z",
    "download": "M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z",
    "play": "M8 5v14l11-7z",
    "search": "M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z",
    "back": "M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z",
    "next": "M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z",
    "prev": "M6 6h2v12H6zm3.5 6l8.5 6V6z",
    "folder": "M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z",
    "list": "M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z",
    "close": "M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z",
    "check": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z",
    "info": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z",
    "code": "M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z",
    "refresh": "M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z",
    "tv": "M21 3H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h5v2h8v-2h5c1.1 0 1.99-.9 1.99-2L23 5c0-1.1-.9-2-2-2zm0 14H3V5h18v12z",
    "clean": "M15 16h4v2h-4zm0-8h7v2h-7zm0 4h6v2h-6zM3 18c0 1.1.9 2 2 2h6c1.1 0 2-.9 2-2V8H3v10zM14 5h-3l-1-1H6L5 5H2v2h12z",
}
_pix_cache = {}


def pix(name, color="#ffffff", size=20):
    key = (name, color, size)
    if key in _pix_cache:
        return _pix_cache[key]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
           f'<path fill="{color}" d="{ICONS[name]}"/></svg>')
    r = QSvgRenderer(QByteArray(svg.encode()))
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    r.render(p)
    p.end()
    pm.setDevicePixelRatio(2)
    _pix_cache[key] = pm
    return pm


def icon(name, color="#ffffff", on_color=None, size=20):
    ic = QIcon()
    ic.addPixmap(pix(name, color, size), QIcon.Normal, QIcon.Off)
    ic.addPixmap(pix(name, on_color or color, size), QIcon.Normal, QIcon.On)
    ic.addPixmap(pix(name, "#6a6a6a", size), QIcon.Disabled, QIcon.Off)
    return ic


def app_icon_pixmap(size=64):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
           f'<rect width="24" height="24" rx="6" fill="{ACCENT}"/>'
           '<path fill="#000" transform="translate(4.6 4.6) scale(0.62)" d="M8 5v14l11-7z"/></svg>')
    r = QSvgRenderer(QByteArray(svg.encode()))
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    r.render(p)
    p.end()
    pm.setDevicePixelRatio(2)
    return pm


def btn(text="", ic=None, name=None, ic_color="#ffffff", tip=None, size=18):
    b = QPushButton(text)
    if ic:
        b.setIcon(icon(ic, ic_color, size=size))
        b.setIconSize(QSize(size, size))
    if name:
        b.setObjectName(name)
    if tip:
        b.setToolTip(tip)
    b.setCursor(Qt.PointingHandCursor)
    return b


def open_channel():
    QDesktopServices.openUrl(QUrl(CHANNEL_URL))


def creator_widget(show_label=True, text_btn=True):
    w = QWidget()
    h = QHBoxLayout(w)
    h.setContentsMargins(0, 0, 0, 0)
    h.setSpacing(6)
    if show_label:
        lab = QLabel("Creado por")
        lab.setObjectName("muted")
        h.addWidget(lab)
    name = QLabel(CREATOR)
    name.setStyleSheet("font-weight:600;")
    h.addWidget(name)
    ver = QLabel()
    ver.setPixmap(pix("verified", "#3ea6ff", 16))
    ver.setToolTip("Canal verificado")
    h.addWidget(ver)
    h.addStretch(1)
    if text_btn:
        b = btn("Mi canal", "youtube", None, "#ff3b3b", "Abrir canal de YouTube", 18)
    else:
        b = btn("", "youtube", "iconbtn", "#ff3b3b", "Abrir canal de YouTube", 20)
    b.clicked.connect(open_channel)
    h.addWidget(b)
    return w


def info_card(ic, color, title, text, buttons=(), extra=None):
    f = QFrame()
    f.setObjectName("row")
    h = QHBoxLayout(f)
    h.setContentsMargins(20, 18, 18, 18)
    h.setSpacing(18)
    i = QLabel()
    i.setPixmap(pix(ic, color, 30))
    i.setFixedWidth(36)
    h.addWidget(i, 0, Qt.AlignTop)
    col = QVBoxLayout()
    col.setSpacing(6)
    t = QLabel(title)
    t.setStyleSheet("font-weight:600;font-size:16px;")
    d = QLabel(text)
    d.setWordWrap(True)
    d.setStyleSheet("color:#c5c5c5;")
    col.addWidget(t)
    col.addWidget(d)
    if extra is not None:
        col.addSpacing(4)
        col.addWidget(extra)
    h.addLayout(col, 1)
    for b in buttons:
        h.addWidget(b, 0, Qt.AlignVCenter)
    return f


QSS = f"""
* {{ font-family: 'Segoe UI Variable Text','Segoe UI','Inter',sans-serif; font-size: 13px; color: #ffffff; }}
QMainWindow, QWidget#root {{ background: #202020; }}
QWidget#content {{ background: #272727; border-top-left-radius: 8px; border: 1px solid #333333; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #5a5a5a; border-radius: 3px; min-height: 40px; }}
QScrollBar::handle:vertical:hover {{ background: #8a8a8a; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QLabel {{ background: transparent; }}
QLabel#title {{ font-size: 24px; font-weight: 600; }}
QLabel#subtitle {{ color: #c5c5c5; font-size: 13px; }}
QLabel#muted {{ color: #9d9d9d; }}
QLabel#section {{ font-size: 20px; font-weight: 600; }}
QToolTip {{ background: #3a3a3a; color: #fff; border: 1px solid #4a4a4a; padding: 5px 8px; border-radius: 4px; }}
QPushButton {{ background: #2f2f2f; border: 1px solid #3a3a3a; border-radius: 6px; padding: 7px 11px; }}
QPushButton:hover {{ background: #3a3a3a; border-color: {ACCENT}; }}
QPushButton:pressed {{ background: #2a2a2a; color: #c5c5c5; }}
QPushButton:disabled {{ color: #6a6a6a; background: #2a2a2a; border-color: #303030; }}
QPushButton#accent {{ background: {ACCENT}; color: #000000; border: 1px solid {ACCENT}; font-weight: 600; }}
QPushButton#accent:hover {{ background: #7ad6ff; }}
QPushButton#accent:pressed {{ background: #3da3d3; }}
QPushButton#accent:disabled {{ background: #3a4a52; color: #7a8a92; border-color: #3a4a52; }}
QPushButton#server {{ border-radius: 15px; padding: 6px 16px; }}
QPushButton#server:checked {{ background: {ACCENT}; color: #000; border-color: {ACCENT}; font-weight: 600; }}
QPushButton#nav {{ background: transparent; border: none; text-align: left; padding: 9px 13px;
    border-radius: 6px; margin: 1px 8px; }}
QPushButton#nav:hover {{ background: #2d2d2d; }}
QPushButton#nav:checked {{ background: #333333; font-weight: 600; }}
QPushButton#tab {{ background: transparent; border: none; border-bottom: 3px solid transparent;
    border-radius: 0; padding: 8px 18px; color: #c5c5c5; font-weight: 600; min-height: 22px; }}
QPushButton#tab:hover {{ color: #ffffff; background: #2f2f2f; }}
QPushButton#tab:checked {{ border-bottom: 3px solid {ACCENT}; color: #ffffff; }}
QPushButton#ep {{ padding: 9px 8px; border-top-right-radius: 0; border-bottom-right-radius: 0; }}
QPushButton#epdl {{ padding: 9px 8px; border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: none; }}
QPushButton#iconbtn {{ padding: 7px; border-radius: 6px; background: transparent; border: none; }}
QPushButton#iconbtn:hover {{ background: #3f3f3f; }}
QLineEdit {{ background: #323232; border: 1px solid #3d3d3d; border-bottom: 2px solid #8a8a8a;
    border-radius: 6px; padding: 8px 12px; selection-background-color: {ACCENT}; selection-color: #000; }}
QLineEdit:focus {{ border: 1px solid {ACCENT}; border-bottom: 2px solid {ACCENT}; background: #1c1c1c; }}
QScrollArea, QFrame#card, QDialog {{ outline: none; }}
QProgressBar {{ border-radius: 5px; }}
QProgressBar::chunk {{ border-radius: 5px; }}
QFrame#card {{ background: #2f2f2f; border: 1px solid #383838; border-radius: 8px; }}
QFrame#card:hover {{ background: #3a3a3a; border: 1px solid {ACCENT}; }}
QFrame#row {{ background: #2f2f2f; border: 1px solid #383838; border-radius: 8px; }}
QFrame#welcome {{ background: #2b2b2b; border: 1px solid #454545; border-radius: 14px; }}
QProgressBar {{ background: #1f1f1f; border: none; border-radius: 3px; max-height: 6px; min-height: 6px; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 3px; }}
QListWidget {{ background: transparent; border: none; outline: none; }}
QListWidget::item {{ background: #2f2f2f; border: 1px solid #383838; border-radius: 6px;
    padding: 11px 14px; margin: 3px 2px; }}
QListWidget::item:hover {{ background: #3a3a3a; border-color: #4a4a4a; }}
QListWidget::item:selected {{ background: #3a3a3a; color: #ffffff; }}
QLabel#toast {{ background: #3b3b3b; border: 1px solid #505050; border-radius: 10px; padding: 11px 20px; }}
"""

class Invoker(QObject):
    sig = Signal(object, object, bool)

    def __init__(self):
        super().__init__()
        self.sig.connect(self._run)

    @Slot(object, object, bool)
    def _run(self, cb, val, ok):
        if cb:
            try:
                cb(val)
            except RuntimeError:
                pass
            except Exception as e:
                print("callback error:", e)


INVOKER = None
POOL = None
STORE = None
DOWNLOADS = None
MAIN = None


class Job(QRunnable):
    def __init__(self, fn, ok_cb, err_cb):
        super().__init__()
        self.fn, self.ok_cb, self.err_cb = fn, ok_cb, err_cb

    def run(self):
        try:
            res = self.fn()
            INVOKER.sig.emit(self.ok_cb, res, True)
        except Exception as e:
            INVOKER.sig.emit(self.err_cb, e, False)


def run_async(fn, ok_cb, err_cb=None):
    POOL.start(Job(fn, ok_cb, err_cb))


def http_get(url):
    r = SESSION.get(url, timeout=25)
    r.raise_for_status()
    return r.text


IMG_CACHE = {}
PAGE_POSTER_CACHE = {}


def fetch_image(url):
    if url in IMG_CACHE:
        return IMG_CACHE[url]
    r = SESSION.get(url, timeout=25)
    r.raise_for_status()
    IMG_CACHE[url] = r.content
    return r.content


def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()


def safe_name(s):
    return re.sub(r'[\\/:*?"<>|]+', " ", s or "").strip(" .") or "Anime"


def toast(text, ic="check"):
    if MAIN:
        MAIN.toast.popup(text, ic)


def fade_in(widget, ms=280, delay=0):
    def go():
        try:
            eff = QGraphicsOpacityEffect(widget)
            eff.setOpacity(0)
            widget.setGraphicsEffect(eff)
            a = QPropertyAnimation(eff, b"opacity", widget)
            a.setDuration(ms)
            a.setStartValue(0.0)
            a.setEndValue(1.0)
            a.setEasingCurve(QEasingCurve.OutCubic)

            def fin():
                try:
                    widget.setGraphicsEffect(None)
                except RuntimeError:
                    pass

            a.finished.connect(fin)
            a.start(QAbstractAnimation.DeleteWhenStopped)
        except RuntimeError:
            pass

    if delay:
        QTimer.singleShot(delay, go)
    else:
        go()


def poster_from_img(img):
    if not img:
        return None
    for attr in ("data-src", "data-original", "data-lazy-src", "src"):
        v = img.get(attr)
        if v and not re.search(r"logito|playbtn|banner|logo", v):
            return urljoin(BASE, v)
    return None


def parse_cards(html):
    soup = BeautifulSoup(html, "html.parser")
    out, idx = [], {}
    for a in soup.select('a[href*="/anime/"]'):
        href = urljoin(BASE, a.get("href", ""))
        if not re.search(r"/anime/[^/?#]+/?$", href):
            continue
        img = a.find("img")
        poster = poster_from_img(img)
        if not poster:
            m = re.search(r"url\(['\"]?([^'\")]+)", str(a))
            if m and not re.search(r"logito|playbtn|banner", m.group(1)):
                poster = urljoin(BASE, m.group(1))
        title = ""
        h = a.find(re.compile(r"^h[1-6]$"))
        if h:
            title = clean(h.get_text())
        if not title and img and img.get("alt"):
            title = clean(img.get("alt"))
        if not title:
            title = clean(a.get_text()).split(" Ver ahora")[0][:90]
        if not title:
            continue
        if href in idx:
            if poster and not out[idx[href]]["poster"]:
                out[idx[href]]["poster"] = poster
            continue
        idx[href] = len(out)
        out.append({"url": href, "title": title, "poster": poster})
    return out


def parse_recent_episodes(html):
    soup = BeautifulSoup(html, "html.parser")
    out, seen = [], set()
    for a in soup.select('a[href*="/ver/"]'):
        href = urljoin(BASE, a.get("href", ""))
        txt = clean(a.get_text())
        if href in seen or not txt:
            continue
        seen.add(href)
        out.append({"url": href, "title": txt})
    return out


def parse_detail(html, url):
    soup = BeautifulSoup(html, "html.parser")
    og = soup.find("meta", property="og:image")
    poster = og["content"] if og and og.get("content") else None
    h2 = soup.find("h2")
    title = clean(h2.get_text()) if h2 else "Anime"
    sub = ""
    for h3 in soup.find_all("h3"):
        t = clean(h3.get_text())
        if t and "Cap" not in t:
            sub = t
            break
    meta = []
    for el in soup.find_all(["p", "div", "span"]):
        t = clean(el.get_text())
        if re.match(r"^(Estreno|Episodios)\s*:", t) and len(t) < 80 and t not in meta:
            meta.append(t)
    genres = [clean(g.get_text()) for g in soup.select('a[href*="/genero/"]')]
    paras = []
    for p in soup.find_all("p"):
        t = clean(p.get_text())
        if len(t) > 40 and "Descargo" not in t:
            paras.append(t)
    status = ""
    for el in soup.find_all(["span", "div", "a"]):
        t = clean(el.get_text())
        if t in ("Finalizado", "En emisión", "En Emisión", "Emisión"):
            status = t
            break
    eps, seen = [], set()
    for a in soup.select('a[href*="/ver/"]'):
        href = urljoin(BASE, a.get("href", ""))
        if href in seen:
            continue
        seen.add(href)
        txt = clean(a.get_text())
        m = re.search(r"[Cc]apitulo\s*([\d.]+)", txt)
        label = f"Episodio {m.group(1)}" if m else txt[:16]
        eps.append({"url": href, "label": label})
    return {"url": url, "title": title, "subtitle": sub, "meta": meta, "genres": genres,
            "synopsis": "\n\n".join(paras[:3]), "poster": poster, "episodes": eps, "status": status}


def decode_player(val):
    val = (val or "").strip()
    if val.startswith("http"):
        return val
    try:
        pad = val + "=" * (-len(val) % 4)
        dec = base64.b64decode(pad).decode("utf-8", "ignore").strip()
        if dec.startswith("//"):
            dec = "https:" + dec
        if dec.startswith("http"):
            return dec
        m = re.search(r"https?://[^\s\"'<>]+", dec)
        if m:
            return m.group(0)
    except Exception:
        pass
    return None


def parse_episode(html, url):
    soup = BeautifulSoup(html, "html.parser")
    h2 = soup.find("h2")
    title = clean(h2.get_text()) if h2 else "Episodio"
    players = []
    for el in soup.select("[data-player]"):
        u = decode_player(el.get("data-player"))
        name = clean(el.get_text()) or "Servidor"
        if u and all(u != p["url"] for p in players):
            players.append({"name": name, "url": u})
    if not players:
        for fr in soup.find_all("iframe"):
            src = fr.get("src") or fr.get("data-src")
            if src:
                players.append({"name": "Servidor", "url": urljoin(BASE, src)})
    nxt = prev = lst = None
    for a in soup.find_all("a"):
        t = clean(a.get_text()).lower()
        href = a.get("href")
        if not href:
            continue
        if t == "siguiente":
            nxt = urljoin(BASE, href)
        elif t == "anterior":
            prev = urljoin(BASE, href)
        elif t == "lista":
            lst = urljoin(BASE, href)
    return {"url": url, "title": title, "players": players, "next": nxt, "prev": prev, "list": lst}


def split_title(full):
    m = re.match(r"^(.*?)\s*-\s*([\d.]+)\s*$", full or "")
    if m:
        return m.group(1).strip(), f"Episodio {m.group(2)}"
    return full or "Anime", "Episodio"


class Store:
    def __init__(self):
        self.d = {"favs": {}, "history": [], "hide_welcome": False, "dl_dir": ""}
        try:
            self.d.update(json.loads(DATA_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass

    def save(self):
        try:
            DATA_FILE.write_text(json.dumps(self.d, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def is_fav(self, url):
        return url in self.d["favs"]

    def toggle_fav(self, url, title, poster):
        if url in self.d["favs"]:
            del self.d["favs"][url]
        else:
            self.d["favs"][url] = {"title": title, "poster": poster}
        self.save()

    def add_history(self, ep_url, title, anime_url):
        h = [x for x in self.d["history"] if x["url"] != ep_url]
        h.insert(0, {"url": ep_url, "title": title, "anime": anime_url, "ts": time.time()})
        self.d["history"] = h[:100]
        self.save()


class Cancelled(Exception):
    pass


class Task:
    _n = 0

    def __init__(self, anime, label, url):
        Task._n += 1
        self.id = Task._n
        self.anime, self.label, self.url = anime, label, url
        self.state = "queued"
        self.text = "En cola"
        self.pct = 0.0
        self.path = None
        self.cancel = False

    @property
    def title(self):
        return f"{self.anime} - {self.label}"


PRIORITY = ["voe", "mixdrop", "streamtape", "doodstream", "dood", "mp4upload", "streamwish", "filemoon",
            "dsvplay", "hexload", "savefiles", "byse", "ok"]


def order_players(players):
    def key(p):
        n = p["name"].lower()
        for i, k in enumerate(PRIORITY):
            if k in n:
                return i
        return len(PRIORITY)

    return sorted([p for p in players if "mega" not in p["name"].lower()], key=key)


def find_media(embed):
    try:
        r = SESSION.get(embed, headers={"Referer": BASE + "/", "User-Agent": UA}, timeout=25)
        txt = r.text.replace("\\/", "/")
        urls = re.findall(r"https?://[^\s\"'<>\\]+?\.(?:m3u8|mp4)[^\s\"'<>\\]*", txt)
        return list(dict.fromkeys(urls))[:4]
    except Exception:
        return []


class DownloadJob(QRunnable):
    def __init__(self, task, folder):
        super().__init__()
        self.task, self.folder = task, folder

    def emit(self, state, text, pct=None, path=None):
        INVOKER.sig.emit(DOWNLOADS._apply, (self.task, state, text, pct, path), True)

    def run(self):
        t = self.task
        try:
            if t.cancel:
                raise Cancelled()
            self.emit("run", "Preparando...", 0)
            d = parse_episode(http_get(t.url), t.url)
            players = order_players(d["players"])
            if not players:
                raise Exception("no hay servidores descargables")
            last = None
            for p in players:
                if t.cancel:
                    raise Cancelled()
                self.emit("run", f"Probando {p['name']}...", t.pct)
                try:
                    path = self._try(p["url"])
                    self.emit("done", "Completado", 100, path)
                    return
                except Cancelled:
                    raise
                except Exception as e:
                    if t.cancel:
                        raise Cancelled()
                    last = e
            raise Exception(f"ningún servidor permitió descargar ({str(last)[:90]})")
        except Cancelled:
            self.emit("cancel", "Cancelado")
        except Exception as e:
            if t.cancel:
                self.emit("cancel", "Cancelado")
            else:
                self.emit("error", f"Error: {str(e)[:120]}")

    def _try(self, embed):
        import yt_dlp
        t = self.task
        out_dir = Path(self.folder) / safe_name(t.anime)
        out_dir.mkdir(parents=True, exist_ok=True)
        tmpl = str(out_dir / (safe_name(f"{t.anime} - {t.label}") + ".%(ext)s"))

        def hook(d):
            if t.cancel:
                raise Cancelled()
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done = d.get("downloaded_bytes") or 0
                pct = (done / total * 100) if total else t.pct
                sp = d.get("speed")
                txt = f"Descargando {pct:.0f}%"
                if sp:
                    txt += f"  -  {sp / 1048576:.1f} MB/s"
                self.emit("run", txt, pct)

        def attempt(target, referer):
            opts = {
                "outtmpl": tmpl,
                # Prioriza MP4 + audio M4A; evita elegir WebM cuando exista MP4.
                # Para combinar pistas separadas/remuxear se necesita FFmpeg.
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
                "merge_output_format": "mp4",
                "postprocessors": [{
                    "key": "FFmpegVideoRemuxer",
                    "preferedformat": "mp4",
                }],
                "quiet": True,
                "no_warnings": True,
                "noprogress": True,
                "retries": 5,
                "fragment_retries": 10,
                "file_access_retries": 3,
                "extractor_retries": 3,
                "concurrent_fragment_downloads": 8,
                "continuedl": True,
                "overwrites": False,
                "windowsfilenames": True,
                "progress_hooks": [hook],
                "http_headers": {"User-Agent": UA, "Referer": referer},
            }
            with yt_dlp.YoutubeDL(opts) as y:
                info = y.extract_info(target, download=True)
                if info and info.get("entries"):
                    info = next((entry for entry in info["entries"] if entry), None)
                if not info:
                    raise RuntimeError("El servidor no devolvió información del video")
                # yt-dlp puede devolver el nombre anterior al remux. Comprueba
                # primero el archivo final y no inventa una extensión MP4.
                prepared = Path(y.prepare_filename(info))
                candidates = [
                    prepared.with_suffix(".mp4"),
                    prepared,
                    prepared.with_suffix(".mkv"),
                    prepared.with_suffix(".webm"),
                ]
                for candidate in candidates:
                    if candidate.is_file() and candidate.stat().st_size > 0:
                        if candidate.suffix.lower() != ".mp4":
                            raise RuntimeError(
                                "El servidor no ofrece MP4 y FFmpeg no pudo convertirlo. "
                                "Instala FFmpeg para remuxear el video."
                            )
                        return str(candidate)
                # Algunos extractores informan la ruta real en requested_downloads.
                for item in info.get("requested_downloads") or []:
                    filename = item.get("filepath")
                    if filename and Path(filename).is_file():
                        candidate = Path(filename)
                        if candidate.suffix.lower() == ".mp4":
                            return str(candidate)
                raise RuntimeError(
                    "No se encontró el MP4 final. Comprueba que FFmpeg esté instalado."
                )

        errs = []
        origin = re.match(r"https?://[^/]+/", embed)
        ref = origin.group(0) if origin else BASE + "/"
        try:
            return attempt(embed, ref)
        except Cancelled:
            raise
        except Exception as e:
            if t.cancel:
                raise Cancelled()
            errs.append(e)
        for media in find_media(embed):
            try:
                return attempt(media, ref)
            except Cancelled:
                raise
            except Exception as e:
                if t.cancel:
                    raise Cancelled()
                errs.append(e)
        raise errs[-1]


class DownloadManager(QObject):
    changed = Signal(object)

    def __init__(self):
        super().__init__()
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(2)
        self.tasks = []

    def folder(self):
        p = STORE.d.get("dl_dir")
        if p:
            return Path(p)
        v = Path.home() / "Videos"
        return (v if v.exists() else Path.home() / "Downloads") / APP_NAME

    def add(self, anime, label, url):
        for t in self.tasks:
            if t.url == url and t.state in ("queued", "run"):
                return None
        t = Task(anime, label, url)
        self.tasks.append(t)
        self.changed.emit(t)
        try:
            self.folder().mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self.pool.start(DownloadJob(t, str(self.folder())))
        return t

    def cancel(self, t):
        t.cancel = True
        if t.state == "queued":
            self._apply((t, "cancel", "Cancelado", None, None))

    def _apply(self, payload):
        t, state, text, pct, path = payload
        if t.state in ("cancel", "done") and state not in ("done",):
            if t.state == "cancel":
                return
        t.state, t.text = state, text
        if pct is not None:
            t.pct = pct
        if path:
            t.path = path
        self.changed.emit(t)

    def clear_finished(self):
        self.tasks = [t for t in self.tasks if t.state in ("queued", "run")]


class FadeStack(QStackedWidget):
    def setCurrentWidget(self, w):
        if w is self.currentWidget():
            return
        super().setCurrentWidget(w)
        if getattr(w, "no_fade", False):
            return
        fade_in(w, 260)


class PosterCard(QFrame):
    clicked = Signal(str)
    W, CH = 164, 296

    def __init__(self, item):
        super().__init__()
        self.setObjectName("card")
        self.item = item
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(self.W, self.CH)
        self.setToolTip(item["title"])
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)
        self.img = QLabel()
        self.img.setFixedSize(self.W - 16, 214)
        self.img.setAlignment(Qt.AlignCenter)
        self.img.setStyleSheet("background:#1f1f1f;border-radius:6px;color:#666;font-size:40px;")
        self.img.setText((item["title"][:1] or "?").upper())
        self.lbl = QLabel(item["title"])
        self.lbl.setWordWrap(True)
        self.lbl.setFixedHeight(48)
        self.lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lbl.setStyleSheet("font-weight:600;font-size:12px;")
        lay.addWidget(self.img)
        lay.addWidget(self.lbl)
        self.sh = QGraphicsDropShadowEffect(self)
        self.sh.setBlurRadius(12)
        self.sh.setOffset(0, 3)
        self.sh.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(self.sh)
        self._anims = []
        self._load()

    def _animate(self, blur, yoff):
        for prop, val in ((b"blurRadius", blur), (b"yOffset", yoff)):
            a = QPropertyAnimation(self.sh, prop, self)
            a.setDuration(170)
            a.setEndValue(float(val))
            a.setEasingCurve(QEasingCurve.OutCubic)
            a.start(QAbstractAnimation.DeleteWhenStopped)

    def enterEvent(self, e):
        self._animate(28, 8)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate(12, 3)
        super().leaveEvent(e)

    def _load(self):
        p = self.item.get("poster")
        if p:
            self._fetch(p)
            return
        url = self.item["url"]
        if url in PAGE_POSTER_CACHE:
            if PAGE_POSTER_CACHE[url]:
                self._fetch(PAGE_POSTER_CACHE[url])
            return

        def job():
            soup = BeautifulSoup(http_get(url), "html.parser")
            og = soup.find("meta", property="og:image")
            return og["content"] if og and og.get("content") else None

        def done(u):
            PAGE_POSTER_CACHE[url] = u
            if u:
                self._fetch(u)

        run_async(job, done)

    def _fetch(self, url):
        run_async(lambda: fetch_image(url), self._set_img)

    def _set_img(self, data):
        try:
            pm = QPixmap()
            pm.loadFromData(data)
            if pm.isNull():
                return
            size = self.img.size()
            pm = pm.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            pm = pm.copy((pm.width() - size.width()) // 2, (pm.height() - size.height()) // 2,
                         size.width(), size.height())
            self.img.setText("")
            self.img.setPixmap(self._round(pm))
        except RuntimeError:
            pass

    @staticmethod
    def _round(pm):
        out = QPixmap(pm.size())
        out.fill(Qt.transparent)
        p = QPainter(out)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(pm)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(out.rect(), 6, 6)
        p.end()
        return out

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.item["url"])


class GridView(QScrollArea):
    card_clicked = Signal(str)
    more_requested = Signal()
    PAD = 8
    GAP = 6

    def __init__(self, with_more=False):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.inner = QWidget()
        self.setWidget(self.inner)
        self.v = QVBoxLayout(self.inner)
        self.v.setContentsMargins(0, 4, 12, 16)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(self.GAP)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.v.addWidget(self.grid_host)
        self.info = QLabel("")
        self.info.setObjectName("muted")
        self.info.setAlignment(Qt.AlignCenter)
        self.v.addWidget(self.info)
        self.more = btn("Cargar más", "refresh")
        self.more.setVisible(with_more)
        self.more.clicked.connect(self.more_requested.emit)
        self.v.addWidget(self.more, 0, Qt.AlignHCenter)
        self.v.addStretch(1)
        self.cards = []
        self._cols = 0

    def clear(self):
        for c in self.cards:
            c.setParent(None)
            c.deleteLater()
        self.cards = []
        self._cols = 0
        self.info.setText("")

    def add_items(self, items):
        base = len(self.cards)
        for n, it in enumerate(items):
            card = PosterCard(it)
            card.clicked.connect(self.card_clicked.emit)
            box = QWidget()
            box.setFixedSize(PosterCard.W + 2 * self.PAD, PosterCard.CH + 2 * self.PAD)
            lay = QVBoxLayout(box)
            lay.setContentsMargins(self.PAD, self.PAD, self.PAD, self.PAD)
            lay.addWidget(card)
            self.cards.append(box)
            fade_in(box, 380, min(n, 18) * 40)
        self._relayout(force=True)

    def set_info(self, t):
        self.info.setText(t)

    def _relayout(self, force=False):
        w = self.viewport().width() - 16
        cols = max(1, w // (PosterCard.W + 2 * self.PAD + self.GAP))
        if cols == self._cols and not force:
            return
        self._cols = cols
        for i, c in enumerate(self.cards):
            self.grid.addWidget(c, i // cols, i % cols)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._relayout()


def make_header(text, sub=None):
    box = QVBoxLayout()
    box.setSpacing(2)
    t = QLabel(text)
    t.setObjectName("title")
    t.setWordWrap(True)
    box.addWidget(t)
    if sub:
        s = QLabel(sub)
        s.setObjectName("muted")
        box.addWidget(s)
    return box


class Toast(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        self.hide()
        self.eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.eff)
        self.anim = QPropertyAnimation(self.eff, b"opacity", self)
        self.anim.setDuration(220)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._out)
        self.anim.finished.connect(self._after)
        self._hiding = False

    def popup(self, text, ic="check"):
        self.setText(f"  {text}")
        self.adjustSize()
        p = self.parentWidget()
        self.move((p.width() - self.width()) // 2, p.height() - self.height() - 36)
        self._hiding = False
        self.show()
        self.raise_()
        self.anim.stop()
        self.anim.setStartValue(self.eff.opacity())
        self.anim.setEndValue(1.0)
        self.anim.start()
        self.timer.start(2400)

    def _out(self):
        self._hiding = True
        self.anim.stop()
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.start()

    def _after(self):
        if self._hiding:
            self.hide()


class WelcomeDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent, Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(26, 26, 26, 26)
        card = QFrame()
        card.setObjectName("welcome")
        card.setFixedWidth(540)
        sh = QGraphicsDropShadowEffect(card)
        sh.setBlurRadius(40)
        sh.setOffset(0, 8)
        sh.setColor(QColor(0, 0, 0, 180))
        card.setGraphicsEffect(sh)
        outer.addWidget(card)
        v = QVBoxLayout(card)
        v.setContentsMargins(34, 30, 34, 26)
        v.setSpacing(10)
        logo = QLabel()
        logo.setPixmap(app_icon_pixmap(64))
        logo.setAlignment(Qt.AlignCenter)
        v.addWidget(logo)
        t = QLabel(f"Bienvenido a {APP_NAME}")
        t.setObjectName("title")
        t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)
        s = QLabel("Esta es una aplicación de código abierto.\nNo permitas que nadie te cobre por ella.")
        s.setObjectName("subtitle")
        s.setAlignment(Qt.AlignCenter)
        s.setWordWrap(True)
        v.addWidget(s)
        v.addSpacing(8)
        rows = [("code", "Código abierto", "Cualquiera puede revisarla, modificarla y compartirla."),
                ("check", "Gratis para siempre", "Usarla y descargar episodios no cuesta nada."),
                ("info", "¿Pagaste por ella?", "Si alguien te la vendió, te estafaron. Pide un reembolso.")]
        for ic, h, d in rows:
            r = QHBoxLayout()
            r.setSpacing(14)
            i = QLabel()
            i.setPixmap(pix(ic, ACCENT, 26))
            i.setFixedWidth(34)
            r.addWidget(i, 0, Qt.AlignTop)
            col = QVBoxLayout()
            col.setSpacing(0)
            a = QLabel(h)
            a.setStyleSheet("font-weight:600;font-size:15px;")
            b = QLabel(d)
            b.setObjectName("muted")
            b.setWordWrap(True)
            col.addWidget(a)
            col.addWidget(b)
            r.addLayout(col, 1)
            v.addLayout(r)
        v.addSpacing(6)
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background:#3d3d3d;")
        v.addWidget(sep)
        v.addSpacing(2)
        v.addWidget(creator_widget(True, True))
        v.addSpacing(8)
        bar = QHBoxLayout()
        self.no_show = btn("No mostrar de nuevo", "close")
        self.ok = btn("Entendido", "check", "accent", "#000000")
        self.no_show.clicked.connect(self._never)
        self.ok.clicked.connect(self.accept)
        bar.addWidget(self.no_show)
        bar.addStretch(1)
        bar.addWidget(self.ok)
        v.addLayout(bar)
        self.ok.setDefault(True)

    def _never(self):
        STORE.d["hide_welcome"] = True
        STORE.save()
        self.accept()

    def showEvent(self, e):
        super().showEvent(e)
        p = self.parentWidget()
        if p:
            g = p.geometry()
            self.move(g.x() + (g.width() - self.width()) // 2, g.y() + (g.height() - self.height()) // 2)
        self.setWindowOpacity(0)
        a = QPropertyAnimation(self, b"windowOpacity", self)
        a.setDuration(380)
        a.setStartValue(0.0)
        a.setEndValue(1.0)
        a.setEasingCurve(QEasingCurve.OutCubic)
        a.start(QAbstractAnimation.DeleteWhenStopped)


class HomePage(QWidget):
    open_anime = Signal(str)
    open_episode = Signal(str)

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 14, 8)
        v.addLayout(make_header("Inicio", "Series destacadas y últimos episodios"))
        v.addSpacing(6)
        tabs = QHBoxLayout()
        tabs.setSpacing(4)
        self.b1 = btn("Series", "tv", "tab", size=16)
        self.b2 = btn("Nuevos episodios", "play", "tab", size=16)
        for b in (self.b1, self.b2):
            b.setCheckable(True)
            tabs.addWidget(b)
        tabs.addStretch(1)
        self.b1.setChecked(True)
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        grp.addButton(self.b1, 0)
        grp.addButton(self.b2, 1)
        v.addLayout(tabs)
        self.stack = FadeStack()
        self.grid = GridView()
        self.grid.card_clicked.connect(self.open_anime.emit)
        self.eps = QListWidget()
        self.eps.setIconSize(QSize(18, 18))
        self.eps.itemClicked.connect(lambda it: self.open_episode.emit(it.data(Qt.UserRole)))
        self.stack.addWidget(self.grid)
        self.stack.addWidget(self.eps)
        v.addWidget(self.stack, 1)
        grp.idClicked.connect(lambda i: self.stack.setCurrentIndex(i) or fade_in(self.stack.currentWidget(), 240))
        self.loaded = False

    def load(self, force=False):
        if self.loaded and not force:
            return
        self.loaded = True
        self.grid.clear()
        self.grid.set_info("Cargando...")

        def done(html):
            self.grid.set_info("")
            self.grid.add_items(parse_cards(html))
            self.eps.clear()
            ic = icon("play", "#ffffff", size=18)
            for e in parse_recent_episodes(html):
                it = QListWidgetItem(ic, "  " + e["title"])
                it.setData(Qt.UserRole, e["url"])
                self.eps.addItem(it)

        def err(e):
            self.loaded = False
            self.grid.set_info(f"No se pudo cargar el contenido. Revisa tu conexión. ({e})")

        run_async(lambda: http_get(BASE), done, err)


class DirectoryPage(QWidget):
    open_anime = Signal(str)

    def __init__(self, title, path, sub=None, searchable=True, paged=True):
        super().__init__()
        self.path, self.paged = path, paged
        self.page_no, self.query, self.loaded, self.busy = 1, "", False, False
        self.seen = set()
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 14, 8)
        top = QHBoxLayout()
        top.addLayout(make_header(title, sub))
        top.addStretch(1)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar anime...")
        self.search.addAction(icon("search", "#9d9d9d"), QLineEdit.LeadingPosition)
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(300)
        self.search.setVisible(searchable)
        self.search.returnPressed.connect(self.do_search)
        top.addWidget(self.search, 0, Qt.AlignTop)
        v.addLayout(top)
        v.addSpacing(6)
        self.grid = GridView(with_more=paged)
        self.grid.card_clicked.connect(self.open_anime.emit)
        self.grid.more_requested.connect(self.load_page)
        v.addWidget(self.grid, 1)

    def do_search(self):
        self.query = self.search.text().strip()
        self.reset()
        self.load_page()

    def reset(self):
        self.page_no, self.loaded = 1, True
        self.seen.clear()
        self.grid.clear()

    def load(self, force=False):
        if self.loaded and not force:
            return
        self.reset()
        self.load_page()

    def _url(self):
        if self.query:
            return f"{BASE}/buscar?q={quote_plus(self.query)}&page={self.page_no}"
        sep = "&" if "?" in self.path else "?"
        return f"{BASE}{self.path}{sep}page={self.page_no}" if self.paged else f"{BASE}{self.path}"

    def load_page(self):
        if self.busy:
            return
        self.busy = True
        self.grid.set_info("Cargando...")
        url = self._url()

        def done(html):
            self.busy = False
            items = [i for i in parse_cards(html) if i["url"] not in self.seen]
            for i in items:
                self.seen.add(i["url"])
            self.grid.add_items(items)
            self.grid.set_info("" if items else "No hay más resultados")
            self.grid.more.setVisible(self.paged and bool(items))
            self.page_no += 1

        def err(e):
            self.busy = False
            self.loaded = False
            self.grid.set_info(f"No se pudo cargar. Revisa tu conexión. ({e})")

        run_async(lambda: http_get(url), done, err)


class FavoritesPage(QWidget):
    open_anime = Signal(str)

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 14, 8)
        v.addLayout(make_header("Favoritos", "Tus series guardadas"))
        v.addSpacing(6)
        self.grid = GridView()
        self.grid.card_clicked.connect(self.open_anime.emit)
        v.addWidget(self.grid, 1)

    def load(self, force=True):
        self.grid.clear()
        items = [{"url": u, "title": d["title"], "poster": d.get("poster")} for u, d in STORE.d["favs"].items()]
        self.grid.add_items(items)
        if not items:
            self.grid.set_info("Aún no tienes favoritos. Abre una serie y pulsa Favorito.")


class HistoryPage(QWidget):
    open_episode = Signal(str)

    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 14, 8)
        v.addLayout(make_header("Historial", "Últimos episodios vistos"))
        v.addSpacing(6)
        self.list = QListWidget()
        self.list.setIconSize(QSize(18, 18))
        self.list.itemClicked.connect(lambda it: self.open_episode.emit(it.data(Qt.UserRole)))
        v.addWidget(self.list, 1)
        self.empty = QLabel("Todavía no has visto nada.")
        self.empty.setObjectName("muted")
        self.empty.setAlignment(Qt.AlignCenter)
        v.addWidget(self.empty)

    def load(self, force=True):
        self.list.clear()
        ic = icon("history", "#ffffff", size=18)
        for h in STORE.d["history"]:
            it = QListWidgetItem(ic, "  " + h["title"])
            it.setData(Qt.UserRole, h["url"])
            self.list.addItem(it)
        self.empty.setVisible(not STORE.d["history"])


class DownloadRow(QFrame):
    def __init__(self, task):
        super().__init__()
        self.setObjectName("row")
        self.task = task
        h = QHBoxLayout(self)
        h.setContentsMargins(16, 12, 12, 12)
        h.setSpacing(14)
        self.ic = QLabel()
        self.ic.setPixmap(pix("download", ACCENT, 26))
        h.addWidget(self.ic)
        col = QVBoxLayout()
        col.setSpacing(5)
        self.title = QLabel(task.title)
        self.title.setStyleSheet("font-weight:600;")
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.status = QLabel("")
        self.status.setObjectName("muted")
        col.addWidget(self.title)
        col.addWidget(self.bar)
        col.addWidget(self.status)
        h.addLayout(col, 1)
        self.b_open = btn("", "folder", "iconbtn", tip="Mostrar en carpeta")
        self.b_open.clicked.connect(self._open)
        self.b_cancel = btn("", "close", "iconbtn", tip="Cancelar")
        self.b_cancel.clicked.connect(lambda: DOWNLOADS.cancel(self.task))
        h.addWidget(self.b_open)
        h.addWidget(self.b_cancel)
        self.update_task()

    def _open(self):
        p = self.task.path
        if p and os.path.exists(p):
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", os.path.normpath(p)])
                return
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(p)))
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(DOWNLOADS.folder())))

    def update_task(self):
        t = self.task
        self.status.setText(t.text)
        a = QPropertyAnimation(self.bar, b"value", self)
        a.setDuration(280)
        a.setEndValue(int(t.pct))
        a.setEasingCurve(QEasingCurve.OutCubic)
        a.start(QAbstractAnimation.DeleteWhenStopped)
        active = t.state in ("queued", "run")
        self.b_cancel.setVisible(active)
        self.b_open.setVisible(t.state == "done")
        color = {"done": "#6ccb5f", "error": "#ff6b6b", "cancel": "#9d9d9d"}.get(t.state, ACCENT)
        name = {"done": "check", "error": "info"}.get(t.state, "download")
        self.ic.setPixmap(pix(name, color, 26))


class DownloadsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.rows = {}
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 14, 8)
        top = QHBoxLayout()
        top.addLayout(make_header("Descargas", "Los episodios se guardan en tu carpeta de videos"))
        top.addStretch(1)
        self.b_open = btn("Abrir carpeta", "folder")
        self.b_open.clicked.connect(lambda: (DOWNLOADS.folder().mkdir(parents=True, exist_ok=True),
                                             QDesktopServices.openUrl(QUrl.fromLocalFile(str(DOWNLOADS.folder())))))
        self.b_change = btn("Cambiar carpeta", "list")
        self.b_change.clicked.connect(self._change)
        self.b_clear = btn("Limpiar", "clean")
        self.b_clear.clicked.connect(self._clear)
        for b in (self.b_open, self.b_change, self.b_clear):
            top.addWidget(b, 0, Qt.AlignTop)
        v.addLayout(top)
        self.path_lbl = QLabel("")
        self.path_lbl.setObjectName("muted")
        v.addWidget(self.path_lbl)
        v.addSpacing(6)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        body = QWidget()
        sc.setWidget(body)
        self.col = QVBoxLayout(body)
        self.col.setContentsMargins(0, 0, 10, 10)
        self.col.setSpacing(8)
        self.col.addStretch(1)
        v.addWidget(sc, 1)
        self.empty = QLabel("No hay descargas todavía.\nAbre una serie y pulsa el botón de descarga junto a un episodio.")
        self.empty.setObjectName("muted")
        self.empty.setAlignment(Qt.AlignCenter)
        v.addWidget(self.empty)
        DOWNLOADS.changed.connect(self.on_change)

    def load(self, force=True):
        self.path_lbl.setText(f"Carpeta: {DOWNLOADS.folder()}")
        self.empty.setVisible(not self.rows)

    def on_change(self, task):
        row = self.rows.get(task.id)
        if row is None:
            row = DownloadRow(task)
            self.rows[task.id] = row
            self.col.insertWidget(0, row)
            fade_in(row, 300)
        else:
            row.update_task()
        self.empty.setVisible(not self.rows)
        if task.state == "done":
            toast(f"Descargado: {task.title}")
        elif task.state == "error":
            toast("Error en la descarga", "info")

    def _change(self):
        d = QFileDialog.getExistingDirectory(self, "Carpeta de descargas", str(DOWNLOADS.folder()))
        if d:
            STORE.d["dl_dir"] = d
            STORE.save()
            self.load()
            toast("Carpeta de descargas actualizada")

    def _clear(self):
        DOWNLOADS.clear_finished()
        keep = {t.id for t in DOWNLOADS.tasks}
        for tid in list(self.rows):
            if tid not in keep:
                r = self.rows.pop(tid)
                r.setParent(None)
                r.deleteLater()
        self.empty.setVisible(not self.rows)


def parse_ver(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or "")[:3])


def check_update():
    """Consulta la última release y busca un .exe instalable para Windows."""
    if "/" not in GITHUB_REPO or GITHUB_REPO.startswith("TU_USUARIO"):
        return None
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
        headers={"User-Agent": UA, "Accept": "application/vnd.github+json"}, timeout=12
    )
    if r.status_code == 404:
        return {"error": "No se encontró una release pública en el repositorio configurado."}
    r.raise_for_status()
    data = r.json()
    tag = data.get("tag_name", "")
    assets = data.get("assets", []) or []
    exe_asset = next((a for a in assets if a.get("name", "").lower() in ("openanime.exe", "openanime-windows.exe")), None)
    py_asset = next((a for a in assets if a.get("name", "").lower() == "main.py"), None)
    return {
        "tag": tag,
        "url": data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases/latest"),
        "newer": parse_ver(tag) > parse_ver(VERSION),
        "asset": exe_asset if getattr(sys, "frozen", False) else py_asset,
        "assets": assets,
        "notes": (data.get("body") or "").strip(),
    }


def _stage_exe_update(asset):
    """Descarga y verifica el nuevo ejecutable sin tocar el .exe actual."""
    import hashlib
    if not getattr(sys, "frozen", False):
        raise RuntimeError("La actualización automática del ejecutable solo funciona en la versión .exe.")
    if not asset or not asset.get("browser_download_url"):
        raise RuntimeError("La release debe incluir OpenAnime.exe como asset.")
    target = Path(sys.executable).resolve()
    staged = target.with_name(target.stem + ".update.exe")
    digest = hashlib.sha256()
    total = 0
    response = requests.get(asset["browser_download_url"], headers={"User-Agent": UA}, timeout=60, stream=True)
    response.raise_for_status()
    try:
        with staged.open("wb") as f:
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > 500 * 1024 * 1024:
                    raise RuntimeError("La actualización supera el límite de 500 MB.")
                digest.update(chunk)
                f.write(chunk)
        if total < 1_000_000:
            raise RuntimeError("La descarga está incompleta o no es un ejecutable válido.")
        expected = (asset.get("digest") or "").lower()
        if expected.startswith("sha256:") and digest.hexdigest().lower() != expected.split(":", 1)[1]:
            raise RuntimeError("La verificación SHA-256 de la actualización falló.")
        return target, staged
    except Exception:
        staged.unlink(missing_ok=True)
        raise
    finally:
        response.close()


def _launch_embedded_replacer(target, staged):
    """Lanza una copia temporal del propio .exe en modo actualizador."""
    import tempfile
    helper = Path(tempfile.gettempdir()) / f"OpenAnimeUpdater-{os.getpid()}.exe"
    shutil.copy2(sys.executable, helper)
    subprocess.Popen(
        [str(helper), "--openanime-apply-update", str(target), str(staged), str(os.getpid())],
        cwd=str(target.parent), close_fds=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )


def notify_update(res, manual=False):
    if res is None:
        if manual:
            QMessageBox.information(MAIN, "Actualizaciones", "No se pudo consultar GitHub. Revisa la configuración del repositorio.")
        return
    if res.get("error"):
        if manual:
            QMessageBox.warning(MAIN, "Actualizaciones", res["error"])
        return
    if res.get("newer"):
        asset = res.get("asset")
        is_exe = bool(getattr(sys, "frozen", False))
        kind = "Se descargará y aplicará desde OpenAnime." if (asset and is_exe) else "Esta release no incluye un ejecutable compatible; se abrirá GitHub."
        answer = QMessageBox.question(
            MAIN, f"OpenAnime {res['tag']} disponible",
            f"Tu versión: {VERSION}\nNueva versión: {res['tag']}\n\n{kind}\n\n¿Quieres actualizar ahora?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        ) if (manual or not STORE.d.get("skip_update_prompts")) else QMessageBox.No
        if answer != QMessageBox.Yes:
            return
        if asset and is_exe:
            try:
                target, staged = _stage_exe_update(asset)
                _launch_embedded_replacer(target, staged)
                QMessageBox.information(MAIN, "Actualización preparada", "OpenAnime se cerrará y abrirá la nueva versión automáticamente.")
                MAIN.close()
            except Exception as e:
                QMessageBox.warning(MAIN, "No se pudo actualizar", f"{e}\n\nSe abrirá la página de la release.")
                QDesktopServices.openUrl(QUrl(res["url"]))
        else:
            QDesktopServices.openUrl(QUrl(res["url"]))
    elif manual:
        QMessageBox.information(MAIN, "Actualizaciones", f"Ya tienes la última versión ({VERSION}).")


class CreditsPage(QWidget):
    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 14, 8)
        outer.addLayout(make_header("Créditos", "Las personas y proyectos que hacen posible OpenAnime"))
        outer.addSpacing(6)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget()
        sc.setWidget(body)
        self.col = QVBoxLayout(body)
        self.col.setContentsMargins(0, 0, 12, 16)
        self.col.setSpacing(12)
        visit = btn("Visitar LatAnime", "tv", tip="Abrir latanime.org")
        visit.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(LATANIME_URL)))
        self.cards = [
            info_card("heart", "#ff6b8b", "LatAnime",
                      "Gracias al equipo y a toda la comunidad de LatAnime (latanime.org) por mantener el catálogo "
                      "de series, episodios y servidores que hacen posible esta aplicación. OpenAnime no está "
                      "afiliada a LatAnime y los videos son alojados por terceros.", (visit,)),
            info_card("code", ACCENT, "Creador de OpenAnime",
                      "Si te gusta el proyecto, pásate por el canal de YouTube para más programas y tutoriales.",
                      extra=creator_widget(False, True)),
            info_card("info", ACCENT, "Tecnologías",
                      "Hecha con Python, PySide6 (Qt), yt-dlp, Requests y BeautifulSoup."),
            info_card("check", "#6ccb5f", "Código abierto y gratuita",
                      "OpenAnime es gratuita. No permitas que nadie te cobre por ella. Los animes y sus derechos "
                      "pertenecen a sus respectivos dueños."),
        ]
        upd = btn("Buscar actualizaciones", "refresh")
        upd.clicked.connect(self._check)
        self.cards.insert(3, info_card("refresh", ACCENT, f"Versión {VERSION}",
                                       "OpenAnime se actualiza con las versiones publicadas en GitHub.", (upd,)))
        for c in self.cards:
            self.col.addWidget(c)
        self.col.addStretch(1)
        outer.addWidget(sc, 1)

    def _check(self):
        toast("Buscando actualizaciones...", "info")
        run_async(check_update, lambda r: notify_update(r, True),
                  lambda e: toast("No se pudo comprobar las actualizaciones", "info"))

    def load(self, force=True):
        for i, c in enumerate(self.cards):
            fade_in(c, 360, i * 90)


class DetailPage(QWidget):
    open_episode = Signal(str)

    def __init__(self):
        super().__init__()
        self.data = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 14, 8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        body = QWidget()
        scroll.setWidget(body)
        self.v = QVBoxLayout(body)
        self.v.setContentsMargins(0, 0, 12, 20)
        head = QHBoxLayout()
        head.setSpacing(26)
        self.poster = QLabel()
        self.poster.setFixedSize(220, 310)
        self.poster.setAlignment(Qt.AlignCenter)
        self.poster.setStyleSheet("background:#1f1f1f;border-radius:10px;")
        head.addWidget(self.poster, 0, Qt.AlignTop)
        info = QVBoxLayout()
        info.setSpacing(6)
        self.title = QLabel()
        self.title.setObjectName("title")
        self.title.setWordWrap(True)
        self.sub = QLabel()
        self.sub.setObjectName("subtitle")
        self.sub.setWordWrap(True)
        self.meta = QLabel()
        self.meta.setObjectName("muted")
        self.meta.setWordWrap(True)
        self.syn = QLabel()
        self.syn.setWordWrap(True)
        self.syn.setStyleSheet("color:#dcdcdc;")
        btns = QHBoxLayout()
        btns.setSpacing(8)
        self.play = btn("Reproducir", "play", "accent", "#000000")
        self.play.clicked.connect(self._play_first)
        self.fav = btn("Favorito", "star_o")
        self.fav.clicked.connect(self._toggle_fav)
        self.dl_all = btn("Descargar todo", "download")
        self.dl_all.clicked.connect(self._download_all)
        for b in (self.play, self.fav, self.dl_all):
            btns.addWidget(b)
        btns.addStretch(1)
        for w in (self.title, self.sub, self.meta):
            info.addWidget(w)
        info.addSpacing(8)
        info.addLayout(btns)
        info.addSpacing(8)
        info.addWidget(self.syn)
        info.addStretch(1)
        head.addLayout(info, 1)
        self.v.addLayout(head)
        lbl = QLabel("Episodios")
        lbl.setObjectName("section")
        self.v.addSpacing(20)
        self.v.addWidget(lbl)
        self.ep_host = QWidget()
        self.ep_grid = QGridLayout(self.ep_host)
        self.ep_grid.setSpacing(10)
        self.ep_grid.setContentsMargins(0, 10, 0, 0)
        self.v.addWidget(self.ep_host)
        self.v.addStretch(1)
        self.status = QLabel("")
        self.status.setObjectName("muted")
        self.v.addWidget(self.status)

    def load(self, url):
        self.data = None
        self.title.setText("Cargando...")
        self.sub.setText("")
        self.meta.setText("")
        self.syn.setText("")
        self.poster.clear()
        self._clear_eps()

        def done(html):
            d = parse_detail(html, url)
            self.data = d
            self.title.setText(d["title"])
            self.sub.setText(d["subtitle"])
            meta = list(d["meta"])
            if d["status"]:
                meta.insert(0, d["status"])
            if d["genres"]:
                meta.append("Géneros: " + ", ".join(d["genres"]))
            self.meta.setText("   -   ".join(meta))
            self.syn.setText(d["synopsis"])
            self._update_fav()
            if d["poster"]:
                run_async(lambda: fetch_image(d["poster"]), self._set_poster)
            cols = 4
            for i, ep in enumerate(d["episodes"]):
                cell = QWidget()
                h = QHBoxLayout(cell)
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(0)
                b = btn(ep["label"], "play", "ep", size=15)
                b.setToolTip("Reproducir")
                b.clicked.connect(lambda _=False, u=ep["url"]: self.open_episode.emit(u))
                dl = btn("", "download", "epdl", tip="Descargar episodio", size=15)
                dl.clicked.connect(lambda _=False, e=ep: self._download(e))
                h.addWidget(b, 1)
                h.addWidget(dl)
                self.ep_grid.addWidget(cell, i // cols, i % cols)
                fade_in(cell, 300, min(i, 24) * 25)
            for c in range(cols):
                self.ep_grid.setColumnStretch(c, 1)
            self.status.setText("" if d["episodes"] else "No se encontraron episodios")
            self.dl_all.setEnabled(bool(d["episodes"]))
            self.play.setEnabled(bool(d["episodes"]))

        run_async(lambda: http_get(url), done, lambda e: self.title.setText(f"Error al cargar ({e})"))

    def _clear_eps(self):
        while self.ep_grid.count():
            w = self.ep_grid.takeAt(0).widget()
            if w:
                w.deleteLater()

    def _set_poster(self, data):
        pm = QPixmap()
        pm.loadFromData(data)
        if pm.isNull():
            return
        size = self.poster.size()
        pm = pm.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        pm = pm.copy((pm.width() - size.width()) // 2, (pm.height() - size.height()) // 2, size.width(), size.height())
        self.poster.setPixmap(PosterCard._round(pm))
        fade_in(self.poster, 350)

    def _play_first(self):
        if self.data and self.data["episodes"]:
            self.open_episode.emit(self.data["episodes"][0]["url"])

    def _download(self, ep):
        if self.data and DOWNLOADS.add(self.data["title"], ep["label"], ep["url"]):
            toast(f"Descarga en cola: {ep['label']}", "download")
        else:
            toast("Ese episodio ya se está descargando", "info")

    def _download_all(self):
        if not self.data:
            return
        n = 0
        for ep in self.data["episodes"]:
            if DOWNLOADS.add(self.data["title"], ep["label"], ep["url"]):
                n += 1
        toast(f"{n} episodios añadidos a la cola de descargas", "download")

    def _update_fav(self):
        if not self.data:
            return
        on = STORE.is_fav(self.data["url"])
        self.fav.setText("En favoritos" if on else "Favorito")
        self.fav.setIcon(icon("star" if on else "star_o", ACCENT if on else "#ffffff"))

    def _toggle_fav(self):
        if self.data:
            STORE.toggle_fav(self.data["url"], self.data["title"], self.data["poster"])
            self._update_fav()
            toast("Añadido a favoritos" if STORE.is_fav(self.data["url"]) else "Quitado de favoritos", "star")


class AdBlocker(QWebEngineUrlRequestInterceptor):
    """Bloqueo ligero de anuncios y rastreadores en el reproductor integrado.

    No es un bloqueador completo: los anuncios servidos desde el mismo dominio
    que el video pueden requerir reglas adicionales y bloquear dominios puede
    afectar a algunos reproductores.
    """
    BLOCKED_HOSTS = (
        "doubleclick.net", "googlesyndication.com", "googleadservices.com",
        "adservice.google.com", "adnxs.com", "popads.net", "popcash.net",
        "propellerads.com", "exoclick.com", "trafficjunky.net",
        "juicyads.com", "onclickads.net", "adsterra.com", "taboola.com",
        "outbrain.com", "criteo.com", "imasdk.googleapis.com",
    )
    BLOCKED_PATHS = (
        "/ads?", "/adserver", "/advertising", "/banner-ad", "/popunder",
        "/popup.php", "/tracking/", "/analytics.js",
    )

    def interceptRequest(self, info):
        try:
            url = info.requestUrl().toString().lower()
            host = info.requestUrl().host().lower()
            if any(host == d or host.endswith("." + d) for d in self.BLOCKED_HOSTS):
                info.block(True)
                return
            if any(part in url for part in self.BLOCKED_PATHS):
                info.block(True)
        except Exception:
            # Un fallo del filtro no debe interrumpir la reproducción.
            return


class VideoPage(QWebEnginePage):
    def createWindow(self, _type):
        # Evita que los anuncios abran ventanas nuevas.
        return None


class PlayerPage(QWidget):
    open_episode = Signal(str)
    open_list = Signal(str)
    no_fade = True

    def __init__(self):
        super().__init__()
        self.data = None
        self.v = QVBoxLayout(self)
        self.v.setContentsMargins(20, 14, 14, 8)
        top = QHBoxLayout()
        top.setSpacing(8)
        self.title = QLabel("")
        self.title.setObjectName("section")
        self.title.setMinimumWidth(0)
        self.title.setMaximumHeight(48)
        self.title.setWordWrap(True)
        self.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.title.setStyleSheet("font-size:16px;font-weight:700;padding:2px 4px;")
        self.title.setToolTip("Título del episodio")
        self.title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.lst = btn("Episodios", "list")
        self.dl = btn("Descargar", "download")
        self.prev = btn("Anterior", "prev")
        self.next = btn("Siguiente", "next", "accent", "#000000")
        self.prev.clicked.connect(lambda: self.data and self.data["prev"] and self.open_episode.emit(self.data["prev"]))
        self.next.clicked.connect(lambda: self.data and self.data["next"] and self.open_episode.emit(self.data["next"]))
        self.lst.clicked.connect(lambda: self.data and self.data["list"] and self.open_list.emit(self.data["list"]))
        self.dl.clicked.connect(self._download)
        top.addWidget(self.title, 1)
        for b in (self.lst, self.dl, self.prev, self.next):
            b.setMinimumWidth(0)
            b.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            b.setMaximumWidth(126)
            top.addWidget(b)
        self.v.addLayout(top)
        self.srv_box = QHBoxLayout()
        self.srv_box.setSpacing(8)
        self.srv_box.addStretch(1)
        self.v.addLayout(self.srv_box)
        self.web = QWebEngineView()
        page = VideoPage(self.web)
        self.web.setPage(page)
        self.ad_blocker = AdBlocker(self)
        # El interceptor debe conservarse como atributo para evitar que Python
        # lo destruya mientras Chromium todavía lo está usando.
        page.profile().setUrlRequestInterceptor(self.ad_blocker)
        s = self.web.settings()
        s.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        s.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
        s.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, False)
        self.web.page().setBackgroundColor(QColor("#000000"))
        self.web.page().fullScreenRequested.connect(self._fullscreen)
        self.v.addWidget(self.web, 1)
        self.msg = QLabel("")
        self.msg.setObjectName("muted")
        self.v.addWidget(self.msg)
        self.srv_btns = []
        self.cur_url = None

    def _download(self):
        if not self.data:
            return
        anime, label = split_title(self.data["title"])
        if DOWNLOADS.add(anime, label, self.cur_url):
            toast(f"Descarga en cola: {label}", "download")
        else:
            toast("Ese episodio ya se está descargando", "info")

    def _fullscreen(self, req):
        req.accept()
        if req.toggleOn():
            self.v.removeWidget(self.web)
            self.web.setParent(None)
            self.web.showFullScreen()
        else:
            self.web.showNormal()
            self.v.insertWidget(2, self.web, 1)
            self.web.show()

    def stop(self):
        self.web.setHtml("<body style='background:#000'></body>")

    def load(self, url):
        self.stop()
        self.cur_url = url
        self.title.setText("Cargando...")
        self.msg.setText("")
        for b in self.srv_btns:
            b.setParent(None)
            b.deleteLater()
        self.srv_btns = []

        def done(html):
            d = parse_episode(html, url)
            self.data = d
            self.title.setText(d["title"])
            self.prev.setEnabled(bool(d["prev"]))
            self.next.setEnabled(bool(d["next"]))
            self.lst.setEnabled(bool(d["list"]))
            STORE.add_history(url, d["title"], d["list"] or "")
            grp = QButtonGroup(self)
            grp.setExclusive(True)
            for p in d["players"]:
                b = btn(p["name"].capitalize(), None, "server")
                b.setCheckable(True)
                b.clicked.connect(lambda _=False, pl=p: self._play(pl))
                grp.addButton(b)
                self.srv_box.insertWidget(self.srv_box.count() - 1, b)
                self.srv_btns.append(b)
                fade_in(b, 300)
            self._grp = grp
            if d["players"]:
                self.srv_btns[0].setChecked(True)
                self._play(d["players"][0])
            else:
                self.msg.setText("No se encontraron servidores de reproducción para este episodio.")

        run_async(lambda: http_get(url), done, lambda e: self.title.setText(f"Error al cargar ({e})"))

    def _play(self, player):
        html = (
            "<html><body style='margin:0;background:#000'>"
            f"<iframe src='{player['url']}' allowfullscreen "
            "allow='autoplay; fullscreen; encrypted-media; picture-in-picture' "
            "referrerpolicy='origin' "
            "style='position:fixed;inset:0;width:100%;height:100%;border:0'></iframe></body></html>"
        )
        self.web.setHtml(html, QUrl(BASE + "/"))
        self.msg.setText("Si un servidor no carga, prueba con otro de la lista.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(app_icon_pixmap(64)))
        # Abrir en un tamaño cómodo y respetar la resolución disponible.
        screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        if available:
            w = min(1120, max(820, available.width() - 80))
            h = min(720, max(560, available.height() - 70))
            self.resize(w, h)
            self.setMinimumSize(min(780, available.width()), min(520, available.height()))
        else:
            self.resize(1120, 720)
            self.setMinimumSize(780, 520)
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        nav = QWidget()
        nav.setFixedWidth(205)
        nv = QVBoxLayout(nav)
        nv.setContentsMargins(0, 16, 0, 12)
        nv.setSpacing(0)
        brand = QHBoxLayout()
        brand.setContentsMargins(20, 4, 10, 18)
        logo = QLabel()
        logo.setPixmap(app_icon_pixmap(30))
        bt = QLabel(APP_NAME)
        bt.setStyleSheet("font-size:18px;font-weight:700;")
        brand.addWidget(logo)
        brand.addSpacing(8)
        brand.addWidget(bt)
        brand.addStretch(1)
        nv.addLayout(brand)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        entries = [("Inicio", "home"), ("Directorio", "grid"), ("En emisión", "live"),
                   ("Favoritos", "star"), ("Descargas", "download"), ("Historial", "history"),
                   ("Créditos", "heart")]
        for i, (txt, ic) in enumerate(entries):
            b = QPushButton("   " + txt)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setIcon(icon(ic, "#d0d0d0", ACCENT, 20))
            b.setIconSize(QSize(20, 20))
            nv.addWidget(b)
            self.nav_group.addButton(b, i)
        nv.addStretch(1)
        self.back = btn("   Atrás", "back", "nav", "#d0d0d0", size=20)
        self.back.clicked.connect(self.go_back)
        nv.addWidget(self.back)
        cw = creator_widget(False, False)
        cw.setContentsMargins(22, 6, 14, 0)
        nv.addWidget(cw)
        free = QLabel("Código abierto y gratuito")
        free.setObjectName("muted")
        free.setStyleSheet("font-size:11px;padding:8px 22px 0 22px;")
        nv.addWidget(free)
        h.addWidget(nav)

        content = QWidget()
        content.setObjectName("content")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        self.stack = FadeStack()
        cl.addWidget(self.stack)
        h.addWidget(content, 1)

        self.home = HomePage()
        self.dir = DirectoryPage("Directorio", "/animes", "Todos los animes disponibles")
        self.air = DirectoryPage("En emisión", "/emision", "Series que se están emitiendo ahora", searchable=False)
        self.fav = FavoritesPage()
        self.dls = DownloadsPage()
        self.his = HistoryPage()
        self.credits = CreditsPage()
        self.detail = DetailPage()
        self.player = PlayerPage()
        self.pages = [self.home, self.dir, self.air, self.fav, self.dls, self.his, self.credits]
        for p in self.pages + [self.detail, self.player]:
            self.stack.addWidget(p)

        for p in (self.home, self.dir, self.air, self.fav):
            p.open_anime.connect(self.show_anime)
        self.home.open_episode.connect(self.show_episode)
        self.his.open_episode.connect(self.show_episode)
        self.detail.open_episode.connect(self.show_episode)
        self.player.open_episode.connect(self.show_episode)
        self.player.open_list.connect(self.show_anime)
        self.nav_group.idClicked.connect(self.show_section)
        self.history_stack = []
        self.toast = Toast(self)
        self.nav_group.button(0).setChecked(True)
        self.show_section(0)

    def show_section(self, i):
        self.player.stop()
        page = self.pages[i]
        self.stack.setCurrentWidget(page)
        self.history_stack = [("section", i)]
        page.load() if i in (0, 1, 2) else page.load(True)

    def show_anime(self, url):
        self.player.stop()
        self.history_stack.append(("anime", url))
        self.detail.load(url)
        self.stack.setCurrentWidget(self.detail)

    def show_episode(self, url):
        self.history_stack.append(("ep", url))
        self.stack.setCurrentWidget(self.player)
        self.player.load(url)

    def go_back(self):
        self.player.stop()
        if len(self.history_stack) > 1:
            self.history_stack.pop()
        kind, val = self.history_stack[-1]
        if kind == "section":
            self.stack.setCurrentWidget(self.pages[val])
            if val >= 3:
                self.pages[val].load(True)
        elif kind == "anime":
            self.history_stack.pop()
            self.show_anime(val)
        else:
            self.history_stack.pop()
            self.show_episode(val)

    def showEvent(self, e):
        super().showEvent(e)
        if not getattr(self, "_shown", False):
            self._shown = True
            self.setWindowOpacity(0)
            a = QPropertyAnimation(self, b"windowOpacity", self)
            a.setDuration(450)
            a.setStartValue(0.0)
            a.setEndValue(1.0)
            a.setEasingCurve(QEasingCurve.OutCubic)
            a.start(QAbstractAnimation.DeleteWhenStopped)
            if not STORE.d.get("hide_welcome"):
                QTimer.singleShot(450, lambda: WelcomeDialog(self).exec())
            QTimer.singleShot(4000, lambda: run_async(check_update, lambda r: notify_update(r, False)))


def apply_dark_titlebar(win):
    if sys.platform != "win32":
        return
    try:
        hwnd = int(win.winId())
        v = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(v), ctypes.sizeof(v))
        c = ctypes.c_int(0x00202020)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(c), ctypes.sizeof(c))
    except Exception:
        pass


def main():
    global INVOKER, POOL, STORE, DOWNLOADS, MAIN
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("OpenAnime.App")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    INVOKER = Invoker()
    POOL = QThreadPool.globalInstance()
    POOL.setMaxThreadCount(12)
    STORE = Store()
    DOWNLOADS = DownloadManager()
    MAIN = MainWindow()
    MAIN.show()
    apply_dark_titlebar(MAIN)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
