from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QFrame
)


class journal_view(QWidget):
    reflect_requested = pyqtSignal(str)
    save_requested = pyqtSignal()
    prompt_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(10)
        left = QVBoxLayout()
        left.setSpacing(3)
        self.date_label = QLabel("")
        self.date_label.setObjectName("journal_date")
        self.time_label = QLabel("")
        self.time_label.setObjectName("journal_time")
        left.addWidget(self.date_label)
        left.addWidget(self.time_label)
        top.addLayout(left)
        top.addStretch()
        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("journal_save_button")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self.save_requested.emit)
        top.addWidget(self.save_button)
        self.start_point_button = QPushButton("Need a starting point?")
        self.start_point_button.setObjectName("start_point_button")
        self.start_point_button.setCursor(Qt.PointingHandCursor)
        self.start_point_button.clicked.connect(self.prompt_requested.emit)
        top.addWidget(self.start_point_button)
        self.reflect_button = QPushButton("Reflect with Tobias")
        self.reflect_button.setObjectName("reflect_button")
        self.reflect_button.setCursor(Qt.PointingHandCursor)
        self.reflect_button.clicked.connect(self._on_reflect)
        top.addWidget(self.reflect_button)
        root.addLayout(top)

        self.editor = QTextEdit()
        self.editor.setObjectName("journal_editor")
        self.editor.setPlaceholderText("What\u2019s on your mind?")
        self.editor.setAcceptRichText(False)
        self.editor.setTabChangesFocus(False)
        root.addWidget(self.editor, 1)

        self.prompt_box = QFrame()
        self.prompt_box.setObjectName("journal_prompt_box")
        pb = QVBoxLayout(self.prompt_box)
        pb.setContentsMargins(12, 8, 12, 8)
        pb.setSpacing(6)
        self.prompt_label = QLabel("")
        self.prompt_label.setObjectName("journal_prompt_text")
        self.prompt_label.setWordWrap(True)
        pb.addWidget(self.prompt_label)
        prompt_actions = QHBoxLayout()
        prompt_actions.setSpacing(8)
        prompt_actions.addStretch()
        self.prompt_use_button = QPushButton("Use this")
        self.prompt_use_button.setObjectName("journal_prompt_button")
        self.prompt_use_button.setCursor(Qt.PointingHandCursor)
        self.prompt_use_button.clicked.connect(self._use_prompt)
        prompt_actions.addWidget(self.prompt_use_button)
        self.prompt_again_button = QPushButton("Try another prompt")
        self.prompt_again_button.setObjectName("journal_prompt_button")
        self.prompt_again_button.setCursor(Qt.PointingHandCursor)
        self.prompt_again_button.clicked.connect(self.prompt_requested.emit)
        prompt_actions.addWidget(self.prompt_again_button)
        self.prompt_dismiss_button = QPushButton("Close")
        self.prompt_dismiss_button.setObjectName("journal_prompt_button")
        self.prompt_dismiss_button.setCursor(Qt.PointingHandCursor)
        self.prompt_dismiss_button.clicked.connect(self.hide_prompt)
        prompt_actions.addWidget(self.prompt_dismiss_button)
        pb.addLayout(prompt_actions)
        self.prompt_box.hide()
        root.addWidget(self.prompt_box)

        self.status_label = QLabel("Saved locally on this device")
        self.status_label.setObjectName("journal_status")
        root.addWidget(self.status_label)

    def _use_prompt(self):
        prompt = self.prompt_label.text().strip()
        if not prompt:
            return
        current = self.editor.toPlainText()
        if current.strip():
            self.editor.setPlainText(current.rstrip() + "\n\n" + prompt)
        else:
            self.editor.setPlainText(prompt)
        self.hide_prompt()
        self.editor.setFocus()

    def set_prompt(self, prompt):
        self.prompt_label.setText(prompt)
        self.prompt_box.show()

    def hide_prompt(self):
        self.prompt_box.hide()

    def _on_reflect(self):
        self.reflect_requested.emit(self.editor.toPlainText())

    def set_header(self, date_line, time_line):
        self.date_label.setText(date_line)
        self.time_label.setText(time_line)

    def set_body(self, text):
        self.editor.setPlainText(text)

    def body(self):
        return self.editor.toPlainText()

    def set_status(self, text):
        self.status_label.setText(text)

    def set_reflect_enabled(self, enabled):
        self.reflect_button.setEnabled(enabled)

    def clear(self):
        self.editor.clear()
