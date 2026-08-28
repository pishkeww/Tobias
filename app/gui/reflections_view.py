from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
)


def _format_date(iso):
    if not isinstance(iso, str):
        return ""
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is not None:
            dt = dt.astimezone()
        return dt.strftime("%B %d")
    except Exception:
        return ""


def _format_source(source):
    if not source:
        return ""
    # storage.py prefixes sources with "conversation: " or "journal: "
    if source.startswith("conversation:"):
        title = source[len("conversation:"):].strip()
        return "Saved from a conversation" + (" \u00b7 " + title if title else "")
    if source.startswith("journal:"):
        title = source[len("journal:"):].strip()
        return "Saved from your journal" + (" \u00b7 " + title if title else "")
    return source


class _card(QWidget):
    delete_requested = pyqtSignal(str)

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.setObjectName("reflection_card")
        self._ref_id = item["id"]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        text_label = QLabel("\u201c" + item["text"] + "\u201d")
        text_label.setObjectName("reflection_text")
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(text_label)

        meta = QHBoxLayout()
        meta.setSpacing(8)
        meta.addStretch()
        date_str = _format_date(item.get("created_at"))
        src_str = _format_source(item.get("source"))
        parts = [p for p in ([src_str, date_str] if not src_str else [src_str, date_str]) if p]
        if parts:
            meta_label = QLabel(" \u00b7 ".join(parts))
            meta_label.setObjectName("reflection_meta")
            meta.addWidget(meta_label)
        delete_btn = QPushButton("remove")
        delete_btn.setObjectName("reflection_delete_button")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self._ref_id))
        meta.addWidget(delete_btn)
        layout.addLayout(meta)


class reflections_view(QWidget):
    delete_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(10)

        self.title = QLabel("Reflections")
        self.title.setObjectName("reflections_title")
        root.addWidget(self.title)
        self.subtitle = QLabel(
            "Thoughts you've saved to revisit later. Everything stays on this device.")
        self.subtitle.setObjectName("reflections_subtitle")
        self.subtitle.setWordWrap(True)
        root.addWidget(self.subtitle)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("reflection_scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.container = QWidget()
        self.container.setObjectName("reflection_container")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 4, 8, 4)
        self.container_layout.setSpacing(10)
        self.container_layout.addStretch()
        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)

    def populate(self, items):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for r in items:
            card = _card(r)
            card.delete_requested.connect(self.delete_requested.emit)
            self.container_layout.insertWidget(self.container_layout.count() - 1, card)
        if not items:
            empty = QLabel("Nothing pinned yet.\nPin a Tobias response in a conversation to save it here.")
            empty.setObjectName("empty_label")
            empty.setAlignment(Qt.AlignTop)
            self.container_layout.insertWidget(0, empty)
