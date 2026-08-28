from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDoubleSpinBox, QSpinBox,
    QTextEdit, QCheckBox, QPushButton, QHBoxLayout, QLabel, QMessageBox,
    QComboBox
)
from app.ollama_client import test_connection, model_exists
from app.config import MODEL_CHOICES, model_description, DEFAULT_MODEL


class settings_dialog(QDialog):
    def __init__(self, settings, parent=None, generating=False):
        super().__init__(parent)
        self.setWindowTitle("settings")
        self.setMinimumWidth(480)
        self.settings = dict(settings)
        self.generating = generating

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.url_edit = QLineEdit(self.settings.get("ollama_url", "http://localhost:11434"))
        form.addRow("ollama url", self.url_edit)

        current = self.settings.get("model", DEFAULT_MODEL)
        self.model_combo = QComboBox()
        self.model_combo.setObjectName("model_combo")
        for i, choice in enumerate(MODEL_CHOICES):
            self.model_combo.addItem(choice["label"], choice["id"])
            if choice["id"] == current:
                self.model_combo.setCurrentIndex(i)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        form.addRow("model", self.model_combo)

        self.model_description_label = QLabel("")
        self.model_description_label.setObjectName("model_description")
        self.model_description_label.setWordWrap(True)
        form.addRow("", self.model_description_label)
        self._update_model_description()

        if self.generating:
            self.model_combo.setEnabled(False)
            note = QLabel("Waiting for the current response to finish before the model can be changed.")
            note.setObjectName("model_description")
            note.setWordWrap(True)
            form.addRow("", note)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.05)
        self.temperature_spin.setValue(self.settings.get("temperature", 0.7))
        form.addRow("temperature", self.temperature_spin)

        self.context_spin = QSpinBox()
        self.context_spin.setRange(256, 131072)
        self.context_spin.setValue(self.settings.get("context_length", 4096))
        form.addRow("context length", self.context_spin)

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(16, 32768)
        self.max_tokens_spin.setValue(self.settings.get("max_tokens", 1024))
        form.addRow("max output tokens", self.max_tokens_spin)

        self.streaming_check = QCheckBox("stream responses")
        self.streaming_check.setChecked(self.settings.get("streaming", True))
        form.addRow(self.streaming_check)

        self.rag_check = QCheckBox("use textbook context (RAG)")
        self.rag_check.setChecked(self.settings.get("rag_enabled", True))
        form.addRow(self.rag_check)

        self.rag_top_spin = QSpinBox()
        self.rag_top_spin.setRange(1, 20)
        self.rag_top_spin.setValue(self.settings.get("rag_top_k", 5))
        form.addRow("rag context chunks", self.rag_top_spin)

        self.rag_embed_edit = QLineEdit(self.settings.get("rag_embed_model", "nomic-embed-text"))
        form.addRow("rag embed model", self.rag_embed_edit)

        layout.addLayout(form)

        layout.addWidget(QLabel("system prompt"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlainText(self.settings.get("system_prompt", ""))
        self.prompt_edit.setMinimumHeight(160)
        layout.addWidget(self.prompt_edit)

        test_row = QHBoxLayout()
        self.test_button = QPushButton("test ollama connection")
        self.test_button.clicked.connect(self.on_test)
        self.status_label = QLabel("")
        test_row.addWidget(self.test_button)
        test_row.addWidget(self.status_label)
        test_row.addStretch()
        layout.addLayout(test_row)

        button_row = QHBoxLayout()
        save_button = QPushButton("save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("cancel")
        cancel_button.clicked.connect(self.reject)
        button_row.addStretch()
        button_row.addWidget(save_button)
        button_row.addWidget(cancel_button)
        layout.addLayout(button_row)

    def _on_model_changed(self):
        self._update_model_description()

    def _update_model_description(self):
        model_id = self.model_combo.currentData()
        self.model_description_label.setText(model_description(model_id) or "")

    def on_test(self):
        url = self.url_edit.text().strip()
        model = self.model_combo.currentData() or ""
        ok, models = test_connection(url)
        if not ok:
            self.status_label.setText("disconnected")
            QMessageBox.warning(self, "connection failed", "could not connect to ollama at " + url)
            return
        if model and not model_exists(url, model):
            self.status_label.setText("connected, model not found")
            QMessageBox.warning(self, "model unavailable", "connected to ollama, but model '" + model + "' was not found")
            return
        self.status_label.setText("connected")
        suffix = " and found model '" + model + "'" if model else ""
        QMessageBox.information(self, "connection ok", "successfully connected to ollama" + suffix)

    def get_settings(self):
        self.settings["ollama_url"] = self.url_edit.text().strip()
        self.settings["model"] = self.model_combo.currentData()
        self.settings["temperature"] = self.temperature_spin.value()
        self.settings["context_length"] = self.context_spin.value()
        self.settings["max_tokens"] = self.max_tokens_spin.value()
        self.settings["streaming"] = self.streaming_check.isChecked()
        self.settings["rag_enabled"] = self.rag_check.isChecked()
        self.settings["rag_top_k"] = self.rag_top_spin.value()
        self.settings["rag_embed_model"] = self.rag_embed_edit.text().strip()
        self.settings["system_prompt"] = self.prompt_edit.toPlainText()
        return self.settings
