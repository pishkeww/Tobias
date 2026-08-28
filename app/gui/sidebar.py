from datetime import date, datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QScrollArea, QMenu, QInputDialog, QMessageBox, QStackedLayout
)

from app import journal

GROUP_LABELS = ["Today", "Yesterday", "Previous 7 days", "Older"]


def _local_date(iso):
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is not None:
            dt = dt.astimezone()
        return dt.date()
    except Exception:
        return None


def _bucket_for(d):
    if d is None:
        return "Older"
    diff = (date.today() - d).days
    if diff <= 0:
        return "Today"
    if diff == 1:
        return "Yesterday"
    if diff <= 7:
        return "Previous 7 days"
    return "Older"


class sidebar(QWidget):
    new_chat_requested = pyqtSignal()
    conversation_selected = pyqtSignal(str)
    conversation_renamed = pyqtSignal(str, str)
    conversation_deleted = pyqtSignal(str)
    conversation_exported = pyqtSignal(str)
    search_changed = pyqtSignal(str)
    settings_requested = pyqtSignal()
    import_requested = pyqtSignal()
    mode_changed = pyqtSignal(str)
    journal_new_requested = pyqtSignal()
    journal_selected = pyqtSignal(str)
    journal_search_changed = pyqtSignal(str)
    journal_delete_requested = pyqtSignal(str)
    select_mode_toggled = pyqtSignal(bool)
    reflect_selected_requested = pyqtSignal()
    reflections_view_requested = pyqtSignal()
    reflection_delete_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 14, 10, 10)
        root.setSpacing(8)

        brand = QLabel("Tobias")
        brand.setObjectName("brand_name")
        root.addWidget(brand)
        subtitle = QLabel("Local \u00b7 private \u00b7 on this device")
        subtitle.setObjectName("brand_subtitle")
        root.addWidget(subtitle)
        root.addSpacing(6)

        nav = QHBoxLayout()
        nav.setSpacing(4)
        self.conversations_button = QPushButton("Conversations")
        self.conversations_button.setObjectName("nav_button")
        self.conversations_button.setCheckable(True)
        self.conversations_button.setCursor(Qt.PointingHandCursor)
        self.conversations_button.clicked.connect(self._select_conversations)
        self.journal_button = QPushButton("Journal")
        self.journal_button.setObjectName("nav_button")
        self.journal_button.setCheckable(True)
        self.journal_button.setCursor(Qt.PointingHandCursor)
        self.journal_button.clicked.connect(self._select_journal)
        self.reflections_button = QPushButton("Reflections")
        self.reflections_button.setObjectName("nav_button")
        self.reflections_button.setCheckable(True)
        self.reflections_button.setCursor(Qt.PointingHandCursor)
        self.reflections_button.clicked.connect(self._select_reflections)
        nav.addWidget(self.conversations_button, 1)
        nav.addWidget(self.journal_button, 1)
        nav.addWidget(self.reflections_button, 1)
        root.addLayout(nav)

        self.mode = "conversations"
        self._journal_selection_mode = False
        self._journal_selected = {}

        self.chat_frame = QWidget()
        chat_layout = QVBoxLayout(self.chat_frame)
        chat_layout.setContentsMargins(0, 8, 0, 0)
        chat_layout.setSpacing(8)

        self.new_chat_button = QPushButton("+ New conversation")
        self.new_chat_button.setObjectName("new_chat_button")
        self.new_chat_button.clicked.connect(self.new_chat_requested.emit)
        chat_layout.addWidget(self.new_chat_button)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("search_box")
        self.search_box.setPlaceholderText("Search conversations")
        self.search_box.textChanged.connect(self.search_changed.emit)
        chat_layout.addWidget(self.search_box)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("conversation_scroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.container = QWidget()
        self.container.setObjectName("conversation_container")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 4, 0)
        self.container_layout.setSpacing(2)
        self.scroll.setWidget(self.container)
        chat_layout.addWidget(self.scroll, 1)

        self.journal_frame = QWidget()
        jl = QVBoxLayout(self.journal_frame)
        jl.setContentsMargins(0, 8, 0, 0)
        jl.setSpacing(8)

        jl_header = QHBoxLayout()
        jl_header.setSpacing(4)
        self.new_entry_button = QPushButton("+ New entry")
        self.new_entry_button.setObjectName("new_chat_button")
        self.new_entry_button.clicked.connect(self.journal_new_requested.emit)
        jl_header.addWidget(self.new_entry_button, 1)
        self.select_button = QPushButton("Select")
        self.select_button.setObjectName("select_toggle_button")
        self.select_button.setCheckable(True)
        self.select_button.setCursor(Qt.PointingHandCursor)
        self.select_button.toggled.connect(self._on_select_toggled)
        jl_header.addWidget(self.select_button)
        jl.addLayout(jl_header)

        self.reflect_selected_button = QPushButton("Reflect on selected")
        self.reflect_selected_button.setObjectName("reflect_selected_button")
        self.reflect_selected_button.setCursor(Qt.PointingHandCursor)
        self.reflect_selected_button.clicked.connect(self.reflect_selected_requested.emit)
        self.reflect_selected_button.hide()
        jl.addWidget(self.reflect_selected_button)

        self.journal_search_box = QLineEdit()
        self.journal_search_box.setObjectName("search_box")
        self.journal_search_box.setPlaceholderText("Search journal")
        self.journal_search_box.textChanged.connect(self.journal_search_changed.emit)
        jl.addWidget(self.journal_search_box)

        self.journal_scroll = QScrollArea()
        self.journal_scroll.setObjectName("conversation_scroll")
        self.journal_scroll.setWidgetResizable(True)
        self.journal_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.journal_container = QWidget()
        self.journal_container.setObjectName("conversation_container")
        self.journal_container_layout = QVBoxLayout(self.journal_container)
        self.journal_container_layout.setContentsMargins(0, 0, 4, 0)
        self.journal_container_layout.setSpacing(2)
        self.journal_scroll.setWidget(self.journal_container)
        jl.addWidget(self.journal_scroll, 1)

        self.reflections_frame = QWidget()
        rl = QVBoxLayout(self.reflections_frame)
        rl.setContentsMargins(0, 8, 0, 0)
        rl.setSpacing(8)
        self.reflections_scroll = QScrollArea()
        self.reflections_scroll.setObjectName("conversation_scroll")
        self.reflections_scroll.setWidgetResizable(True)
        self.reflections_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reflections_container = QWidget()
        self.reflections_container.setObjectName("conversation_container")
        self.reflections_container_layout = QVBoxLayout(self.reflections_container)
        self.reflections_container_layout.setContentsMargins(0, 0, 4, 0)
        self.reflections_container_layout.setSpacing(2)
        self.reflections_scroll.setWidget(self.reflections_container)
        rl.addWidget(self.reflections_scroll, 1)

        self.stack = QStackedLayout()
        self.stack.addWidget(self.chat_frame)
        self.stack.addWidget(self.journal_frame)
        self.stack.addWidget(self.reflections_frame)
        root.addLayout(self.stack, 1)

        privacy = QLabel("Local data \u00b7 runs on this device")
        privacy.setObjectName("privacy_label")
        root.addWidget(privacy)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("settings_button")
        self.settings_button.clicked.connect(self.settings_requested.emit)
        root.addWidget(self.settings_button)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_blank_menu)

        self._sync_mode()

    def _select_conversations(self):
        self.set_mode("conversations")

    def _select_journal(self):
        self.set_mode("journal")

    def _select_reflections(self):
        self.set_mode("reflections")

    def set_mode(self, mode):
        if mode == self.mode:
            self._sync_mode()
            return
        leaving_journal = self.mode == "journal"
        self.mode = mode
        if leaving_journal and mode != "journal":
            self.clear_journal_selection()
        self._sync_mode()
        self.mode_changed.emit(mode)

    def _sync_mode(self):
        if self.mode == "journal":
            self.journal_button.setChecked(True)
            self.conversations_button.setChecked(False)
            self.reflections_button.setChecked(False)
            self.stack.setCurrentWidget(self.journal_frame)
        elif self.mode == "reflections":
            self.reflections_button.setChecked(True)
            self.conversations_button.setChecked(False)
            self.journal_button.setChecked(False)
            self.stack.setCurrentWidget(self.reflections_frame)
        else:
            self.conversations_button.setChecked(True)
            self.journal_button.setChecked(False)
            self.reflections_button.setChecked(False)
            self.stack.setCurrentWidget(self.chat_frame)

    def _make_row(self, conv, active_id):
        btn = QPushButton(conv["title"])
        btn.setObjectName("conversation_item")
        btn.setProperty("selected", conv["id"] == active_id)
        btn.setToolTip(conv["title"])
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda p, cid=conv["id"]: self.show_row_menu(cid, p))
        btn.clicked.connect(lambda _, cid=conv["id"]: self.conversation_selected.emit(cid))
        btn._conv_id = conv["id"]
        return btn

    def populate(self, conversations, active_id=None, flat=False):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not conversations:
            empty = QLabel("No conversations yet")
            empty.setObjectName("empty_label")
            self.container_layout.addWidget(empty)
            self.container_layout.addStretch()
            return

        if flat:
            for conv in conversations:
                self.container_layout.addWidget(self._make_row(conv, active_id))
        else:
            groups = {label: [] for label in GROUP_LABELS}
            for conv in conversations:
                groups[_bucket_for(_local_date(conv.get("updated_at")))].append(conv)
            for label in GROUP_LABELS:
                items = groups[label]
                if not items:
                    continue
                header = QLabel(label.upper())
                header.setObjectName("group_header")
                self.container_layout.addWidget(header)
                for conv in items:
                    self.container_layout.addWidget(self._make_row(conv, active_id))

        self.container_layout.addStretch()

    def _make_journal_row(self, entry, active_path):
        if self._journal_selection_mode:
            btn = QPushButton(journal.preview(entry["body"]))
            btn.setObjectName("conversation_item")
            btn.setProperty("selected", entry["path"] in self._journal_selected)
            btn.setToolTip(journal.preview(entry["body"]))
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, e=entry: self._toggle_journal_selection(e))
            if entry["path"] in self._journal_selected:
                btn.setText("\u2713 " + btn.text())
            return btn
        title = journal.preview(entry["body"])
        btn = QPushButton(title)
        btn.setObjectName("conversation_item")
        btn.setProperty("selected", entry["path"] == active_path)
        btn.setToolTip(title)
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda p, e=entry: self.show_journal_menu(e, p))
        btn.clicked.connect(lambda _, e=entry: self.journal_selected.emit(e["path"]))
        return btn

    def populate_journal(self, entries, active_path=None, flat=False):
        self._last_entries = entries
        self._last_active_path = active_path
        self._last_flat = flat
        while self.journal_container_layout.count():
            item = self.journal_container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not entries:
            empty = QLabel("No journal entries yet")
            empty.setObjectName("empty_label")
            self.journal_container_layout.addWidget(empty)
            self.journal_container_layout.addStretch()
            return

        if flat:
            for entry in entries:
                self.journal_container_layout.addWidget(self._make_journal_row(entry, active_path))
        else:
            groups = {label: [] for label in journal.BUCKET_LABELS}
            for entry in entries:
                groups[entry.get("bucket", "Older")].append(entry)
            for label in journal.BUCKET_LABELS:
                items = groups[label]
                if not items:
                    continue
                header = QLabel(label.upper())
                header.setObjectName("group_header")
                self.journal_container_layout.addWidget(header)
                for entry in items:
                    self.journal_container_layout.addWidget(self._make_journal_row(entry, active_path))

        self.journal_container_layout.addStretch()

    def _on_select_toggled(self, checked):
        self.set_journal_selection_mode(checked)

    def set_journal_selection_mode(self, enabled):
        self._journal_selection_mode = enabled
        if not enabled:
            self._journal_selected = {}
        self._update_reflect_button()
        self._re_render_journal()

    def _toggle_journal_selection(self, entry):
        path = entry["path"]
        if path in self._journal_selected:
            del self._journal_selected[path]
        else:
            self._journal_selected[path] = entry
        self._update_reflect_button()
        self._re_render_journal()

    def _re_render_journal(self):
        entries = getattr(self, "_last_entries", [])
        if not entries:
            return
        self.populate_journal(
            entries,
            getattr(self, "_last_active_path", None),
            flat=getattr(self, "_last_flat", False))

    def _update_reflect_button(self):
        n = len(self._journal_selected)
        if self._journal_selection_mode and n > 0:
            self.reflect_selected_button.setText(
                "Reflect on selected (%d)" % n)
            self.reflect_selected_button.show()
        else:
            self.reflect_selected_button.hide()

    def selected_journal_paths(self):
        return list(self._journal_selected.keys())

    def clear_journal_selection(self):
        if self._journal_selection_mode:
            self.select_button.setChecked(False)
        self.set_journal_selection_mode(False)

    def populate_reflections(self, items):
        while self.reflections_container_layout.count():
            item = self.reflections_container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not items:
            empty = QLabel("No reflections yet")
            empty.setObjectName("empty_label")
            self.reflections_container_layout.addWidget(empty)
            self.reflections_container_layout.addStretch()
            return
        for item in items:
            row = self._make_reflection_row(item)
            self.reflections_container_layout.addWidget(row)
        self.reflections_container_layout.addStretch()

    def _make_reflection_row(self, item):
        text = item.get("text", "")
        plain = " ".join(text.strip().split()) or "Untitled"
        btn = QPushButton(plain if len(plain) <= 60 else plain[:60].rstrip() + "\u2026")
        btn.setObjectName("conversation_item")
        btn.setToolTip(text)
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda p, it=item: self.show_reflection_menu(it, p))
        btn.clicked.connect(self.reflections_view_requested.emit)
        return btn

    def show_reflection_menu(self, item, pos):
        menu = QMenu(self)
        remove_action = menu.addAction("Remove reflection")
        sender = self.sender()
        anchor = sender if sender is not None else self
        action = menu.exec_(anchor.mapToGlobal(pos))
        if action == remove_action:
            self.reflection_delete_requested.emit(item["id"])

    def show_row_menu(self, conv_id, pos):
        menu = QMenu(self)
        rename_action = menu.addAction("Rename")
        export_action = menu.addAction("Export")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        sender = self.sender()
        anchor = sender if sender is not None else self
        action = menu.exec_(anchor.mapToGlobal(pos))

        if action == rename_action:
            current = getattr(sender, "text", lambda: "")()
            new_title, ok = QInputDialog.getText(self, "Rename conversation", "Conversation title:", text=current)
            if ok and new_title.strip():
                self.conversation_renamed.emit(conv_id, new_title.strip())
        elif action == export_action:
            self.conversation_exported.emit(conv_id)
        elif action == delete_action:
            confirm = QMessageBox.question(
                self, "Delete conversation",
                "Delete this conversation? This cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.conversation_deleted.emit(conv_id)

    def show_journal_menu(self, entry, pos):
        menu = QMenu(self)
        delete_action = menu.addAction("Delete entry")
        sender = self.sender()
        anchor = sender if sender is not None else self
        action = menu.exec_(anchor.mapToGlobal(pos))
        if action == delete_action:
            confirm = QMessageBox.question(
                self, "Delete journal entry",
                "Delete this journal entry? This cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                self.journal_delete_requested.emit(entry["path"])

    def show_blank_menu(self, pos):
        if self.childAt(pos) is not None:
            return
        menu = QMenu(self)
        import_action = menu.addAction("Import conversation\u2026")
        menu.addSeparator()
        settings_action = menu.addAction("Settings")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == import_action:
            self.import_requested.emit()
        elif action == settings_action:
            self.settings_requested.emit()

    def clear(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
