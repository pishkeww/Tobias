import os
from datetime import datetime

import markdown
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QPushButton,
    QSizePolicy, QFrame
)

MAX_MESSAGE_WIDTH = 1000


def render_markdown(text):
    return markdown.markdown(text, extensions=["fenced_code", "tables", "nl2br"])


def _format_time(ts):
    if not isinstance(ts, str):
        return ""
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is not None:
            dt = dt.astimezone()
        return dt.strftime("%H:%M")
    except Exception:
        return ts[11:19] if len(ts) >= 19 else ""


class autoheighttextbrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setOpenExternalLinks(True)
        self.setFrameStyle(0)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.document().documentLayout().documentSizeChanged.connect(self.update_height)

    def update_height(self, *args):
        margins = self.contentsMargins()
        height = self.document().size().height() + margins.top() + margins.bottom() + 10
        self.setFixedHeight(int(height))


class message_widget(QWidget):
    regenerate_requested = pyqtSignal()
    pin_requested = pyqtSignal()

    def __init__(self, role, content, timestamp, show_regenerate=False, pinned=False, parent=None):
        super().__init__(parent)
        self.setObjectName("message_widget")
        self.role = role
        self.raw_content = content
        self.sources = []
        self._processing = False
        self._pinned = pinned

        # The outer widget spans the full conversation width. The content column
        # expands up to MAX_MESSAGE_WIDTH and is anchored to the appropriate side.
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 6, 0, 6)
        outer.setSpacing(0)

        content_col = QWidget()
        content_col.setObjectName("message_content")
        content_col.setMaximumWidth(MAX_MESSAGE_WIDTH)
        content_col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        content_layout = QVBoxLayout(content_col)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        header = QHBoxLayout()
        who = QLabel("Tobias" if role == "assistant" else "You")
        who.setObjectName("speaker_label")
        who.setProperty("role", role)
        time_label = QLabel(_format_time(timestamp))
        time_label.setObjectName("message_time")
        header.addWidget(who)
        header.addStretch()
        header.addWidget(time_label)
        content_layout.addLayout(header)

        self.processing_bar = QWidget()
        self.processing_bar.setObjectName("processing_bar")
        pbar = QHBoxLayout(self.processing_bar)
        pbar.setContentsMargins(0, 0, 0, 0)
        pbar.setSpacing(8)
        self.dot_label = QLabel("")
        self.dot_label.setObjectName("processing_dots")
        self.status_label = QLabel("")
        self.status_label.setObjectName("processing_status")
        pbar.addWidget(self.dot_label)
        pbar.addWidget(self.status_label)
        pbar.addStretch()
        content_layout.addWidget(self.processing_bar)
        self._dot_index = 0
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._animate_dots)
        self._dot_timer.setInterval(450)
        self.processing_bar.hide()

        if role == "user":
            self.user_label = QLabel(content)
            self.user_label.setObjectName("user_text")
            self.user_label.setWordWrap(True)
            self.user_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            content_layout.addWidget(self.user_label)
            self.browser = None
        else:
            self.browser = autoheighttextbrowser()
            self.browser.setObjectName("assistant_browser")
            self.browser.setHtml(render_markdown(content))
            content_layout.addWidget(self.browser)

        actions = QHBoxLayout()
        actions.addStretch()
        if role == "assistant":
            self.pin_btn = QPushButton("pinned" if self._pinned else "pin")
            self.pin_btn.setObjectName("pin_button")
            self.pin_btn.setProperty("pinned", self._pinned)
            self.pin_btn.setCursor(Qt.PointingHandCursor)
            self.pin_btn.clicked.connect(self._on_pin)
            actions.addWidget(self.pin_btn)
        copy_btn = QPushButton("copy")
        copy_btn.setObjectName("copy_button")
        copy_btn.clicked.connect(self.copy_content)
        actions.addWidget(copy_btn)
        self.regen_btn = None
        if show_regenerate and role == "assistant":
            self.regen_btn = QPushButton("regenerate")
            self.regen_btn.setObjectName("regen_button")
            self.regen_btn.clicked.connect(self.regenerate_requested.emit)
            actions.addWidget(self.regen_btn)
        content_layout.addLayout(actions)

        self.sources_toggle = QPushButton()
        self.sources_toggle.setObjectName("sources_toggle")
        self.sources_toggle.setCursor(Qt.PointingHandCursor)
        self.sources_toggle.clicked.connect(self.toggle_sources)
        self.sources_toggle.hide()

        self.sources_box = QFrame()
        self.sources_box.setObjectName("sources_box")
        self.sources_box_layout = QVBoxLayout(self.sources_box)
        self.sources_box_layout.setContentsMargins(10, 8, 10, 8)
        self.sources_box_layout.setSpacing(2)
        self.sources_box.hide()

        self._sources_visible = False
        content_layout.addWidget(self.sources_toggle)
        content_layout.addWidget(self.sources_box)

        if role == "user":
            outer.addStretch(1)
            outer.addWidget(content_col, 100)
        else:
            outer.addWidget(content_col, 100)
            outer.addStretch(1)

    # ---- processing indicator ----

    def set_processing(self, text):
        if self.browser is None:
            return
        self._processing = True
        self.status_label.setText(text)
        self.dot_label.setText("\u25cf\u2003\u2003")
        self._dot_index = 0
        self.processing_bar.show()
        self._dot_timer.start()

    def set_processing_text(self, text):
        self.status_label.setText(text)

    def _animate_dots(self):
        dots = ["\u25cf\u2003\u2003", "\u2003\u25cf\u2003", "\u2003\u2003\u25cf"]
        self._dot_index = (self._dot_index + 1) % len(dots)
        self.dot_label.setText(dots[self._dot_index])

    def _stop_processing(self):
        self._processing = False
        self._dot_timer.stop()
        self.processing_bar.hide()

    def copy_content(self):
        QGuiApplication.clipboard().setText(self.raw_content)

    def _on_pin(self):
        if self.role != "assistant":
            return
        if self._pinned:
            return
        self.pin_requested.emit()

    def set_pinned(self):
        self._pinned = True
        if getattr(self, "pin_btn", None) is not None:
            self.pin_btn.setText("pinned")
            self.pin_btn.setProperty("pinned", True)
            self.pin_btn.style().unpolish(self.pin_btn)
            self.pin_btn.style().polish(self.pin_btn)

    def update_content(self, content):
        self.raw_content = content
        if self.browser is None:
            return
        if self._processing and content:
            self._stop_processing()
        self.browser.setHtml(render_markdown(content))
        self.browser.update_height()

    def show_content(self, content):
        self._stop_processing()
        self.raw_content = content
        if self.browser is not None:
            self.browser.setHtml(render_markdown(content))
            self.browser.update_height()

    def set_sources(self, sources):
        if not sources:
            return
        self.sources = sources
        n = len(sources)
        self.sources_toggle.setText(
            "Used %d reference document%s" % (n, "s" if n != 1 else ""))
        while self.sources_box_layout.count():
            item = self.sources_box_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for src in sources:
            name = os.path.basename(src.get("source") or "").replace(".pdf", "")
            title = name.strip() or "Reference document"
            page = src.get("page")
            label = QLabel(title + (" \u00b7 p.%d" % page if page else ""))
            label.setObjectName("source_label")
            label.setWordWrap(True)
            self.sources_box_layout.addWidget(label)
        self.sources_box_layout.addStretch()
        self.sources_toggle.show()

    def toggle_sources(self):
        self._sources_visible = not self._sources_visible
        self.sources_box.setVisible(self._sources_visible)
