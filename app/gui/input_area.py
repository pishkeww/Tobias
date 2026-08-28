from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QTextEdit, QPushButton, QLabel,
    QSizePolicy
)


class chat_text_edit(QTextEdit):
    send_requested = pyqtSignal()
    height_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min_h = 44
        self._max_h = 120
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.document().documentLayout().documentSizeChanged.connect(
            self._content_changed)
        self.setFixedHeight(self._min_h)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.height_changed.emit()

    def _content_changed(self, *args):
        doc_h = int(self.document().size().height() or 0)
        target = min(max(doc_h + 16, self._min_h), self._max_h)
        if self.height() != target:
            self.setFixedHeight(target)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
            self.send_requested.emit()
            return
        super().keyPressEvent(event)


class input_area(QWidget):
    send_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("input_area")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 12)
        layout.setSpacing(6)

        self.composer = QFrame()
        self.composer.setObjectName("composer")
        composer_layout = QHBoxLayout(self.composer)
        composer_layout.setContentsMargins(6, 6, 6, 6)
        composer_layout.setSpacing(6)

        self.text_edit = chat_text_edit()
        self.text_edit.setObjectName("message_input")
        self.text_edit.setPlaceholderText("What\u2019s on your mind?")
        self.text_edit.send_requested.connect(self.on_send)
        self.text_edit.height_changed.connect(self._reflow)
        composer_layout.addWidget(self.text_edit, 1)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("send_button")
        self.send_button.setFixedHeight(38)
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.clicked.connect(self.on_send)
        composer_layout.addWidget(self.send_button, 0, Qt.AlignBottom)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stop_button")
        self.stop_button.setFixedHeight(38)
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.hide()
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        composer_layout.addWidget(self.stop_button, 0, Qt.AlignBottom)

        layout.addWidget(self.composer)
        self.composer.setFixedHeight(self.text_edit.height() + 12)

        self.privacy_label = QLabel("Runs locally on this device")
        self.privacy_label.setObjectName("input_privacy")
        layout.addWidget(self.privacy_label)

    def on_send(self):
        text = self.text_edit.toPlainText().strip()
        if text and self.send_button.isVisible():
            self.send_clicked.emit()

    def _reflow(self):
        te_h = self.text_edit.height()
        if self.composer.height() != te_h + 12:
            self.composer.setFixedHeight(te_h + 12)
        self.updateGeometry()
        if self.layout() is not None:
            self.layout().invalidate()
            self.layout().activate()
        parent = self.parentWidget()
        if parent is not None and parent.layout() is not None:
            parent.layout().invalidate()
            parent.layout().activate()

    def get_text(self):
        return self.text_edit.toPlainText().strip()

    def clear_text(self):
        self.text_edit.clear()

    def set_generating(self, generating):
        if generating:
            self.send_button.hide()
            self.stop_button.show()
        else:
            self.send_button.show()
            self.stop_button.hide()
        self.text_edit.setEnabled(True)
