from datetime import datetime, timezone
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QLabel,
    QFileDialog, QMessageBox, QStackedWidget
)
from PyQt5.QtCore import Qt, QTimer
from app import config, rag, journal, prompts, reflections
from app.storage import storage
from app.ollama_client import chatworker, test_connection, model_exists
from app.rag import rag_index
from app.gui.sidebar import sidebar
from app.gui.input_area import input_area
from app.gui.message_widget import message_widget
from app.gui.settings_dialog import settings_dialog
from app.gui.journal_view import journal_view
from app.gui.reflections_view import reflections_view

GREETING = "Hey, I'm Tobias. How can I help you?"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class mainwindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tobias - The [Anal]yst-The[rapist]")
        self.resize(1100, 750)

        self.settings = config.load_settings()
        self.db = storage()
        self.current_conversation_id = None
        self.worker = None
        self.streaming_widget = None
        self.streaming_text = ""
        self._streaming_status_set = False

        self.current_journal_path = None
        self._journal_dirty = False
        self._journal_timer = QTimer(self)
        self._journal_timer.setSingleShot(True)
        self._journal_timer.setInterval(1200)
        self._journal_timer.timeout.connect(self.save_journal)

        self._pinned_texts = set(r.get("text") for r in reflections.load_reflections())
        self._current_prompt = None
        self._journal_selection = set()
        self._journal_selection_mode = False

        self.rag = rag_index(config.get_db_path(), self.settings.get("rag_source_dir"))
        self._rag_thread = None
        self._start_rag_build()

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = sidebar()
        self.sidebar.new_chat_requested.connect(self.on_new_chat)
        self.sidebar.conversation_selected.connect(self.on_conversation_selected)
        self.sidebar.conversation_renamed.connect(self.on_conversation_renamed)
        self.sidebar.conversation_deleted.connect(self.on_conversation_deleted)
        self.sidebar.conversation_exported.connect(self.on_export)
        self.sidebar.search_changed.connect(self.on_search_changed)
        self.sidebar.settings_requested.connect(self.on_settings_requested)
        self.sidebar.import_requested.connect(self.on_import)
        self.sidebar.mode_changed.connect(self.show_mode)
        self.sidebar.journal_new_requested.connect(self.on_journal_new)
        self.sidebar.journal_selected.connect(self.on_journal_selected)
        self.sidebar.journal_search_changed.connect(self.on_journal_search)
        self.sidebar.journal_delete_requested.connect(self.on_journal_delete)
        self.sidebar.reflect_selected_requested.connect(self.on_reflect_selected)
        self.sidebar.reflections_view_requested.connect(self.on_show_reflections)
        self.sidebar.reflection_delete_requested.connect(self.on_reflection_delete)
        self.sidebar.setFixedWidth(280)
        root.addWidget(self.sidebar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("content_stack")

        self.chat_page = QWidget()
        chat_page_layout = QVBoxLayout(self.chat_page)
        chat_page_layout.setContentsMargins(0, 0, 0, 0)
        chat_page_layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setObjectName("top_bar")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(16, 8, 16, 8)
        self.conversation_title_label = QLabel("")
        self.conversation_title_label.setObjectName("conversation_title_label")
        top_bar_layout.addWidget(self.conversation_title_label)
        top_bar_layout.addStretch()
        self.local_indicator = QLabel("\u25cf Local")
        self.local_indicator.setObjectName("local_indicator")
        self.local_indicator.setToolTip("Tobias runs locally on this device")
        top_bar_layout.addWidget(self.local_indicator)
        self.status_label = QLabel("checking connection...")
        self.status_label.setObjectName("status_label")
        top_bar_layout.addWidget(self.status_label)
        chat_page_layout.addWidget(top_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_container = QWidget()
        self.chat_container.setObjectName("chat_container")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(16, 8, 16, 8)
        self.chat_layout.setSpacing(2)
        self.chat_layout.addStretch()
        self.scroll_area.setWidget(self.chat_container)
        chat_page_layout.addWidget(self.scroll_area, 1)

        self.input_area = input_area()
        self.input_area.send_clicked.connect(self.on_send)
        self.input_area.stop_clicked.connect(self.on_stop)
        chat_page_layout.addWidget(self.input_area)

        self.content_stack.addWidget(self.chat_page)

        self.journal_view = journal_view()
        self.journal_view.reflect_requested.connect(self.on_journal_reflect)
        self.journal_view.save_requested.connect(self.on_journal_save)
        self.journal_view.editor.textChanged.connect(self.on_journal_edited)
        self.journal_view.prompt_requested.connect(self.on_journal_prompt_requested)
        self.content_stack.addWidget(self.journal_view)

        self.reflections_view = reflections_view()
        self.reflections_view.delete_requested.connect(self.on_reflection_delete)
        self.content_stack.addWidget(self.reflections_view)

        right_layout.addWidget(self.content_stack, 1)

        root.addWidget(right, 1)
        self.setCentralWidget(central)

        self.refresh_sidebar()
        self.refresh_journal_sidebar()
        self.refresh_reflections()
        conversations = self.db.list_conversations()
        if conversations:
            self.load_conversation(conversations[0]["id"])
        else:
            self.on_new_chat()

        self.connection_timer = QTimer(self)
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(15000)
        self.check_connection()

    def _start_rag_build(self):
        if self._rag_thread and self._rag_thread.is_alive():
            return
        self._rag_thread = threading.Thread(target=self.rag.background_build, daemon=True)
        self._rag_thread.start()

    def set_status(self, text, active=False):
        self.status_label.setText(text)
        self.status_label.setProperty("generating", active)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def check_connection(self):
        ok, models = test_connection(self.settings.get("ollama_url", ""))
        if not ok:
            self.set_status("disconnected")
            return
        model = self.settings.get("model", "")
        if model and not model_exists(self.settings.get("ollama_url", ""), model):
            self.set_status("connected, model unavailable")
            return
        self.set_status("connected")

    def refresh_sidebar(self, search=None):
        conversations = self.db.list_conversations(search)
        self.sidebar.populate(conversations, self.current_conversation_id, flat=bool(search))

    def on_search_changed(self, text):
        self.refresh_sidebar(text.strip() or None)

    def on_new_chat(self):
        conv_id = self.db.create_conversation("new conversation")
        if not self.db.get_messages(conv_id):
            self.db.add_message(conv_id, "assistant", GREETING)
        self.refresh_sidebar()
        self.load_conversation(conv_id)

    def on_conversation_selected(self, conv_id):
        if conv_id != self.current_conversation_id:
            self.load_conversation(conv_id)

    def on_conversation_renamed(self, conv_id, title):
        self.db.rename_conversation(conv_id, title)
        self.refresh_sidebar()

    def on_conversation_deleted(self, conv_id):
        self.db.delete_conversation(conv_id)
        if conv_id == self.current_conversation_id:
            conversations = self.db.list_conversations()
            if conversations:
                self.load_conversation(conversations[0]["id"])
            else:
                self.on_new_chat()
        else:
            self.refresh_sidebar()

    def on_settings_requested(self):
        dialog = settings_dialog(self.settings, self, generating=self.worker is not None)
        if dialog.exec_():
            new_settings = dialog.get_settings()
            if new_settings.get("rag_source_dir") != self.settings.get("rag_source_dir"):
                self.rag = rag_index(config.get_db_path(), new_settings.get("rag_source_dir"))
                self._rag_thread = None
                self._start_rag_build()
            self.settings = new_settings
            config.save_settings(self.settings)
            self.check_connection()

    def show_mode(self, mode):
        if mode == "journal":
            if self.content_stack.currentWidget() != self.journal_view:
                self.save_journal_now()
                self.content_stack.setCurrentWidget(self.journal_view)
        elif mode == "reflections":
            if self.content_stack.currentWidget() != self.reflections_view:
                self.save_journal_now()
                self.content_stack.setCurrentWidget(self.reflections_view)
            self.refresh_reflections()
        else:
            if self.content_stack.currentWidget() != self.chat_page:
                self.save_journal_now()
                self.content_stack.setCurrentWidget(self.chat_page)

    def on_show_reflections(self):
        self.sidebar.set_mode("reflections")
        self.show_mode("reflections")

    def refresh_journal_sidebar(self, query=None):
        entries = journal.search(query or "")
        self.sidebar.populate_journal(entries, self.current_journal_path, flat=bool(query))

    def on_journal_search(self, text):
        self.refresh_journal_sidebar(text.strip() or None)

    def on_journal_new(self):
        self.save_journal_now()
        self._ensure_entry_path()
        self.show_mode("journal")
        self.journal_view.editor.setFocus()

    def _ensure_entry_path(self):
        if self.current_journal_path is not None:
            return
        path = journal.new_entry_path()
        journal.write_entry(path, "")
        date_line, time_line = journal.header_for(path)
        self.current_journal_path = path
        self._journal_dirty = False
        self.journal_view.set_header(date_line, time_line)
        self.refresh_journal_sidebar()

    def on_journal_selected(self, path):
        if path != self.current_journal_path:
            self._open_journal(path)

    def _open_journal(self, path):
        if self.current_journal_path and path != self.current_journal_path and self._journal_dirty:
            self.save_journal()
        body = journal.read_entry(path)
        date_line, time_line = journal.header_for(path)
        self.current_journal_path = path
        self._journal_dirty = False
        self.journal_view.set_header(date_line, time_line)
        self.journal_view.set_body(body)
        self.journal_view.set_status("Saved locally on this device")
        self.refresh_journal_sidebar()

    def on_journal_edited(self):
        self._ensure_entry_path()
        self._journal_dirty = True
        self.journal_view.set_status("Saving\u2026")
        self._journal_timer.start()

    def save_journal(self):
        if not self.current_journal_path:
            return
        try:
            journal.write_entry(self.current_journal_path, self.journal_view.body())
            self._journal_dirty = False
            self.journal_view.set_status("Saved locally on this device")
        except OSError:
            self.journal_view.set_status("Could not save")

    def save_journal_now(self):
        if self._journal_timer.isActive():
            self._journal_timer.stop()
        self.save_journal()

    def on_journal_save(self):
        self.save_journal_now()

    def on_journal_delete(self, path):
        was_active = path == self.current_journal_path
        journal.delete_entry(path)
        if was_active:
            self.current_journal_path = None
            self.journal_view.clear()
            self.on_journal_new()
        else:
            self.refresh_journal_sidebar()

    def on_journal_reflect(self, body):
        self.save_journal_now()
        content = self.journal_view.body()
        if not content.strip():
            self.journal_view.set_status("Write something first, then reflect\u2026")
            return
        conv_id = self.db.create_conversation("Reflection on journal")
        first_line = content.strip().splitlines()[0][:40] if content.strip() else "journal entry"
        self.db.rename_conversation(conv_id, "Reflection \u00b7 " + first_line)
        self.db.add_message(conv_id, "user", content)
        self.sidebar.set_mode("conversations")
        self.show_mode("conversations")
        self.load_conversation(conv_id)
        self.input_area.setFocus()
        self.start_generation()

    def on_journal_prompt_requested(self):
        self._current_prompt = prompts.get_prompt(self._current_prompt)
        self.journal_view.set_prompt(self._current_prompt)

    def on_reflect_selected(self):
        paths = self.sidebar.selected_journal_paths()
        if not paths:
            return
        self.save_journal_now()
        entries, _ = journal.read_selected(paths)
        if not entries:
            self.journal_view.set_status("Nothing to reflect on\u2026")
            return
        context = journal.format_selected_for_reflection(entries)
        n = len(entries)
        intro = (
            "I'm sharing %d journal entr%s with you to reflect on together. "
            "Please read only what's below. Don't diagnose me \u2014 just notice "
            "themes, connections, and questions, and check whether what you see "
            "feels accurate to me.\n\n"
            "Journal entries:\n\n%s"
        ) % (n, "ies" if n != 1 else "y", context)
        conv_id = self.db.create_conversation("Reflection on entries")
        self.db.rename_conversation(conv_id, "Reflection on %d entr%s" % (n, "ies" if n != 1 else "y"))
        self.db.add_message(conv_id, "user", intro)
        self.sidebar.clear_journal_selection()
        self.sidebar.set_mode("conversations")
        self.show_mode("conversations")
        self.load_conversation(conv_id)
        self.input_area.setFocus()
        self.start_generation()

    def refresh_reflections(self):
        items = reflections.load_reflections()
        self.reflections_view.populate(items)
        self.sidebar.populate_reflections(items)

    def on_reflection_delete(self, ref_id):
        reflections.remove_reflection(ref_id)
        self._pinned_texts = set(r.get("text") for r in reflections.load_reflections())
        self.refresh_reflections()
        if self.current_conversation_id:
            self.load_conversation(self.current_conversation_id)

    def clear_chat_layout(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def load_conversation(self, conv_id):
        self.current_conversation_id = conv_id
        self.clear_chat_layout()
        messages = self.db.get_messages(conv_id)
        if not messages:
            self.db.add_message(conv_id, "assistant", GREETING)
            messages = self.db.get_messages(conv_id)
        has_user = any(m["role"] == "user" for m in messages)
        last_assistant_index = None
        for i, m in enumerate(messages):
            if m["role"] == "assistant":
                last_assistant_index = i
        for i, m in enumerate(messages):
            is_last = i == last_assistant_index
            is_greeting = m["role"] == "assistant" and m["content"] == GREETING
            show_regen = (
                is_last
                and m["role"] == "assistant"
                and has_user
                and not is_greeting
            )
            self.add_message_widget(m["role"], m["content"], m["timestamp"], show_regen)
        conversations = self.db.list_conversations()
        current = next((c for c in conversations if c["id"] == conv_id), None)
        self.conversation_title_label.setText(current["title"] if current else "")
        self.refresh_sidebar()
        self.scroll_to_bottom()

    def add_message_widget(self, role, content, timestamp, show_regenerate=False):
        pinned = role == "assistant" and self._is_text_pinned(content)
        widget = message_widget(role, content, timestamp, show_regenerate, pinned=pinned)
        widget.regenerate_requested.connect(self.on_regenerate)
        widget.pin_requested.connect(self.on_pin_message)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, widget)
        return widget

    def _is_text_pinned(self, text):
        return (text or "").strip() in self._pinned_texts

    def on_pin_message(self):
        widget = self.sender()
        if widget is None or getattr(widget, "role", None) != "assistant":
            return
        text = widget.raw_content.strip()
        if not text or self._is_text_pinned(text):
            return
        title = ""
        if self.current_conversation_id:
            convs = self.db.list_conversations()
            cur = next((c for c in convs if c["id"] == self.current_conversation_id), None)
            if cur:
                title = cur.get("title", "")
        reflections.add_reflection(text, source="conversation:" + title)
        self._pinned_texts = set(r.get("text") for r in reflections.load_reflections())
        widget.set_pinned()
        self.refresh_reflections()

    def scroll_to_bottom(self):
        bar = self.scroll_area.verticalScrollBar()
        QTimer.singleShot(0, lambda: bar.setValue(bar.maximum()))

    def build_ollama_messages(self):
        messages = [{"role": "system", "content": self.settings.get("system_prompt", "")}]
        history = self.db.get_messages(self.current_conversation_id)
        for m in history:
            messages.append({"role": m["role"], "content": m["content"]})
        return messages

    def on_send(self):
        text = self.input_area.get_text()
        if not text or self.worker is not None:
            return
        msg = self.db.add_message(self.current_conversation_id, "user", text)
        self.add_message_widget("user", text, msg["timestamp"])
        conversations = self.db.list_conversations()
        current = next((c for c in conversations if c["id"] == self.current_conversation_id), None)
        if current and current["title"] == "new conversation":
            title = text[:40] + ("..." if len(text) > 40 else "")
            self.db.rename_conversation(self.current_conversation_id, title)
        self.input_area.clear_text()
        self.refresh_sidebar()
        self.scroll_to_bottom()
        self.start_generation()

    def start_generation(self):
        messages = self.build_ollama_messages()
        self.streaming_text = ""
        self.streaming_widget = self.add_message_widget("assistant", "", now_iso())
        if self.settings.get("rag_enabled") and self.rag is not None:
            self.streaming_widget.set_processing("Looking through your reference material...")
            self.set_status("Preparing a response...", True)
        else:
            self.streaming_widget.set_processing("Preparing a response...")
            self.set_status("Preparing a response...", True)
        self.scroll_to_bottom()
        self.input_area.set_generating(True)

        self.worker = chatworker(
            self.settings.get("ollama_url", ""),
            self.settings.get("model", ""),
            messages,
            self.settings.get("temperature", 0.7),
            self.settings.get("context_length", 4096),
            self.settings.get("max_tokens", 1024),
            self.settings.get("streaming", True),
            rag_index=self.rag if self.settings.get("rag_enabled") else None,
            rag_top_k=self.settings.get("rag_top_k", 5),
            rag_embed_model=self.settings.get("rag_embed_model", "nomic-embed-text")
        )
        self.worker.token_received.connect(self.on_token)
        self.worker.finished_ok.connect(self.on_generation_finished)
        self.worker.failed.connect(self.on_generation_failed)
        self.worker.sources_ready.connect(self.on_sources_ready)
        self.worker.start()

    def on_sources_ready(self, sources):
        if self.streaming_widget:
            self.streaming_widget.set_sources(sources)
            self.streaming_widget.set_processing_text("Generating response...")
        self.set_status("Generating response...", True)

    def on_token(self, token):
        self.streaming_text += token
        if self.streaming_widget:
            self.streaming_widget.update_content(self.streaming_text)
        if not self._streaming_status_set:
            self.set_status("Tobias is responding...", True)
            self._streaming_status_set = True
        self.scroll_to_bottom()

    def on_generation_finished(self):
        if self.streaming_text.strip():
            self.db.add_message(self.current_conversation_id, "assistant", self.streaming_text)
        elif self.streaming_widget:
            self.streaming_widget.setParent(None)
            self.streaming_widget.deleteLater()
        self.finish_generation()
        self.load_conversation(self.current_conversation_id)

    def on_generation_failed(self, error_text):
        if self.streaming_widget:
            self.streaming_widget.update_content("error: " + error_text)
        self.finish_generation()

    def finish_generation(self):
        self.input_area.set_generating(False)
        self.streaming_widget = None
        self.streaming_text = ""
        self._streaming_status_set = False
        if self.worker:
            self.worker.deleteLater()
        self.worker = None
        self.check_connection()

    def on_stop(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(2000)
            if self.streaming_text.strip():
                self.db.add_message(
                    self.current_conversation_id,
                    "assistant",
                    self.streaming_text + "\n\n*stopped by user*"
                )
            self.finish_generation()
            self.load_conversation(self.current_conversation_id)

    def on_regenerate(self):
        if self.worker is not None or not self.current_conversation_id:
            return
        messages = self.db.get_messages(self.current_conversation_id)
        if not messages or messages[-1]["role"] != "assistant":
            return
        if messages[-1]["content"] == GREETING:
            return
        self.db.delete_last_assistant_message(self.current_conversation_id)
        self.load_conversation(self.current_conversation_id)
        self.start_generation()

    def on_export(self, conv_id=None):
        target = conv_id or self.current_conversation_id
        if not target:
            return
        path, _ = QFileDialog.getSaveFileName(self, "export conversation", "conversation.json", "json files (*.json)")
        if path:
            try:
                self.db.export_conversation(target, path)
                QMessageBox.information(self, "export complete", "conversation exported to " + path)
            except (OSError, ValueError) as e:
                QMessageBox.warning(self, "export failed", str(e))

    def on_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "import conversation", "", "json files (*.json)")
        if path:
            try:
                conv_id = self.db.import_conversation(path)
                self.refresh_sidebar()
                self.load_conversation(conv_id)
            except (OSError, ValueError) as e:
                QMessageBox.warning(self, "import failed", str(e))

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
            self.worker.wait(2000)
        self.save_journal_now()
        event.accept()