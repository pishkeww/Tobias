dark_stylesheet = """
QMainWindow {
    background-color: #F4EFE7;
}

QWidget {
    background-color: #F4EFE7;
    color: #3F3934;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}

QPushButton {
    background-color: #E8E1D6;
    border: 1px solid #D8CFC2;
    border-radius: 8px;
    padding: 7px 12px;
    color: #3F3934;
}
QPushButton:hover { background-color: #DED5C8; }
QPushButton:pressed { background-color: #D4CABB; }
QPushButton:disabled { color: #AAA198; }

QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #FAF7F2;
    border: 1px solid #D8CFC2;
    border-radius: 8px;
    padding: 6px 8px;
    color: #3F3934;
    selection-background-color: #9DB7A3;
    selection-color: #2E2925;
}

QComboBox QAbstractItemView {
    background-color: #FAF7F2;
    color: #3F3934;
    border: 1px solid #D8CFC2;
    selection-background-color: #E8E1D6;
    selection-color: #3F3934;
}

#model_combo { min-height: 30px; }

#model_description {
    color: #81776E;
    font-size: 11px;
    background: transparent;
}

QScrollArea { border: none; background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QTextBrowser { background: transparent; border: none; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #D3C9BC; border-radius: 5px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: #BFB4A7; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: #D3C9BC; border-radius: 5px; min-width: 28px; }
QScrollBar::handle:horizontal:hover { background: #BFB4A7; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

#sidebar {
    background-color: #ECE5DA;
    border-right: 1px solid #DDD3C6;
}
#brand_name {
    color: #3F3934;
    font-size: 19px;
    font-weight: 600;
    background: transparent;
}
#brand_subtitle {
    color: #81776E;
    font-size: 11px;
    background: transparent;
}

#new_chat_button {
    background-color: #E3EBE2;
    border: 1px solid #C7D7C9;
    border-radius: 8px;
    padding: 9px 12px;
    color: #3F3934;
    font-weight: 500;
}
#new_chat_button:hover {
    background-color: #D6E2D6;
    border-color: #9DB7A3;
}

#nav_button {
    background: transparent;
    border: none;
    border-radius: 7px;
    color: #81776E;
    font-weight: 500;
    padding: 8px 10px;
}
#nav_button:hover {
    background-color: #E2D9CE;
    color: #3F3934;
}
#nav_button:checked {
    background-color: #E3EBE2;
    color: #3F3934;
    border-left: 3px solid #8EAD91;
    padding-left: 7px;
}

#content_stack { border: none; }

#journal_date {
    color: #3F3934;
    font-size: 18px;
    font-weight: 600;
    background: transparent;
}
#journal_time {
    color: #93887D;
    font-size: 12px;
    background: transparent;
}
#journal_editor {
    background-color: #FAF7F2;
    border: 1px solid #D8CFC2;
    border-radius: 12px;
    padding: 16px;
    font-family: 'Georgia', 'Segoe UI', serif;
    font-size: 16px;
    color: #3F3934;
    selection-background-color: #9DB7A3;
    selection-color: #2E2925;
}
#journal_editor:focus { border-color: #9DB7A3; }
#journal_editor QScrollBar:vertical { background: transparent; width: 10px; }

#reflect_button {
    background-color: #8EAD91;
    color: #FFFFFF;
    border: none;
    border-radius: 9px;
    padding: 8px 16px;
    font-weight: 600;
}
#reflect_button:hover { background-color: #78977B; }
#reflect_button:pressed { background-color: #66866D; }
#reflect_button:disabled {
    background-color: #D4D0C9;
    color: #AAA198;
}

#journal_save_button {
    background-color: #E8E1D6;
    color: #514A44;
    border: 1px solid #D8CFC2;
    border-radius: 9px;
    padding: 8px 16px;
}
#journal_save_button:hover { background-color: #DED5C8; }
#journal_save_button:pressed { background-color: #D4CABB; }

#journal_status {
    color: #93887D;
    font-size: 11px;
    background: transparent;
}

#search_box {
    background-color: #F7F3ED;
    border: 1px solid #D8CFC2;
    border-radius: 8px;
    padding: 7px 10px;
}
#search_box:focus { border-color: #9DB7A3; }

#group_header {
    background: transparent;
    color: #93887D;
    font-size: 10px;
    font-weight: 600;
    padding: 14px 10px 4px 10px;
}

#conversation_item {
    background: transparent;
    border: none;
    border-radius: 7px;
    padding: 8px 10px;
    text-align: left;
    color: #665E57;
}
#conversation_item:hover {
    background-color: #E2D9CE;
    color: #3F3934;
}
#conversation_item[selected="true"] {
    background-color: #E3EBE2;
    color: #3F3934;
    border-left: 3px solid #8EAD91;
    padding-left: 7px;
}

#empty_label {
    color: #93887D;
    font-size: 12px;
    padding: 10px;
}

#privacy_label {
    color: #93887D;
    font-size: 11px;
}
#settings_button {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #81776E;
    text-align: left;
    padding: 6px 10px;
}
#settings_button:hover {
    background-color: #E2D9CE;
    color: #3F3934;
}

#top_bar {
    background-color: #F4EFE7;
    border-bottom: 1px solid #E2D9CE;
}
#conversation_title_label {
    color: #514A44;
    font-size: 13px;
    font-weight: 500;
    background: transparent;
}
#local_indicator {
    color: #66866D;
    font-size: 11px;
    background-color: #E3EBE2;
    padding: 3px 8px;
    border: 1px solid #C7D7C9;
    border-radius: 10px;
}
#status_label {
    color: #81776E;
    font-size: 11px;
    background: transparent;
    padding: 2px 8px;
}
#status_label[generating="true"] { color: #66866D; }

#chat_container { background: transparent; }
#message_widget { background: transparent; }
#message_widget QWidget { background: transparent; }

#message_content { background: transparent; }

#speaker_label {
    color: #66866D;
    font-size: 11px;
    font-weight: 600;
    background: transparent;
}
#speaker_label[role="user"] { color: #81776E; }

#message_time {
    color: #AAA198;
    font-size: 11px;
    background: transparent;
}

#user_text {
    background-color: #E8DCCB;
    border-radius: 10px;
    padding: 10px 14px;
    color: #3F3934;
}

#assistant_browser {
    background: transparent;
    border: none;
    color: #3F3934;
    font-size: 14px;
}

#processing_bar { background: transparent; }
#processing_dots {
    color: #8EAD91;
    font-size: 14px;
    background: transparent;
}
#processing_status {
    color: #81776E;
    font-size: 12px;
    background: transparent;
}

#copy_button, #regen_button {
    background: transparent;
    border: none;
    border-radius: 5px;
    color: #93887D;
    font-size: 11px;
    padding: 3px 8px;
}
#copy_button:hover, #regen_button:hover {
    background-color: #E8E1D6;
    color: #514A44;
}

#sources_toggle {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #66866D;
    font-size: 11px;
    padding: 3px 8px;
}
#sources_toggle:hover {
    background-color: #E3EBE2;
    color: #527258;
}

#sources_box {
    background-color: #F7F3ED;
    border: 1px solid #DDD3C6;
    border-radius: 8px;
    padding: 8px 10px;
}
#source_label {
    color: #81776E;
    font-size: 11px;
    padding: 2px 0;
}

#input_area {
    background-color: #F4EFE7;
    border-top: 1px solid #E2D9CE;
}

#composer {
    background-color: #FAF7F2;
    border: 1px solid #D8CFC2;
    border-radius: 14px;
}
#composer:focus-within { border-color: #9DB7A3; }

#message_input {
    background: transparent;
    border: none;
    padding: 6px 10px;
    font-size: 14px;
    color: #3F3934;
}

#send_button {
    background-color: #8EAD91;
    color: #FFFFFF;
    border: none;
    border-radius: 9px;
    padding: 0 18px;
    font-weight: 600;
}
#send_button:hover { background-color: #78977B; }
#send_button:disabled {
    background-color: #D4D0C9;
    color: #AAA198;
}

#stop_button {
    background-color: #E8E1D6;
    color: #514A44;
    border: 1px solid #D8CFC2;
    border-radius: 9px;
    padding: 0 18px;
}
#stop_button:hover { background-color: #DED5C8; }

#input_privacy {
    color: #93887D;
    font-size: 11px;
}

QDialog {
    background-color: #F7F3ED;
}
QDialog QLabel {
    background: transparent;
    color: #3F3934;
}
QDialog QLineEdit, QDialog QTextEdit, QDialog QSpinBox, QDialog QDoubleSpinBox {
    background-color: #FAF7F2;
    border: 1px solid #D8CFC2;
    border-radius: 6px;
    color: #3F3934;
}
QDialog QPushButton {
    background-color: #E8E1D6;
    border: 1px solid #D8CFC2;
    border-radius: 6px;
    padding: 6px 12px;
}
QDialog QPushButton:hover { background-color: #DED5C8; }

QMessageBox {
    background-color: #F7F3ED;
}
QMessageBox QLabel {
    color: #3F3934;
    background: transparent;
}

QMenu {
    background-color: #FAF7F2;
    color: #3F3934;
    border: 1px solid #D8CFC2;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #E8E1D6;
}
QMenu::separator {
    height: 1px;
    background: #DDD3C6;
    margin: 4px 8px;
}

QToolTip {
    background-color: #3F3934;
    color: #F7F3ED;
    border: 1px solid #514A44;
}

#pin_button {
    background: transparent;
    border: none;
    border-radius: 5px;
    color: #93887D;
    font-size: 11px;
    padding: 3px 8px;
}
#pin_button:hover {
    background-color: #E3EBE2;
    color: #527258;
}
#pin_button[pinned="true"] {
    color: #66866D;
    background-color: #E3EBE2;
}

#start_point_button {
    background: transparent;
    border: none;
    border-radius: 6px;
    color: #81776E;
    font-size: 11px;
    padding: 4px 8px;
}
#start_point_button:hover {
    background-color: #E2D9CE;
    color: #514A44;
}

#journal_prompt_box {
    background-color: #F0E9DD;
    border: 1px solid #DDD3C6;
    border-radius: 10px;
}
#journal_prompt_text {
    background: transparent;
    color: #514A44;
    font-family: 'Georgia', 'Segoe UI', serif;
    font-size: 14px;
    font-style: italic;
}
#journal_prompt_button {
    background: transparent;
    border: none;
    border-radius: 5px;
    color: #66866D;
    font-size: 11px;
    padding: 3px 8px;
}
#journal_prompt_button:hover {
    background-color: #E3EBE2;
    color: #527258;
}

#select_toggle_button {
    background: transparent;
    border: 1px solid #D8CFC2;
    border-radius: 8px;
    color: #81776E;
    font-size: 11px;
    padding: 4px 10px;
}
#select_toggle_button:hover {
    background-color: #E2D9CE;
    color: #514A44;
}
#select_toggle_button:checked {
    background-color: #E3EBE2;
    border-color: #9DB7A3;
    color: #527258;
}

#reflect_selected_button {
    background-color: #8EAD91;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 10px;
    font-weight: 600;
}
#reflect_selected_button:hover { background-color: #78977B; }

#reflections_title {
    color: #3F3934;
    font-size: 20px;
    font-weight: 600;
    background: transparent;
}
#reflections_subtitle {
    color: #81776E;
    font-size: 12px;
    background: transparent;
}
#reflection_card {
    background-color: #FFFFFF;
    border: 1px solid #E4DBCE;
    border-radius: 12px;
}
#reflection_text {
    background: transparent;
    color: #3F3934;
    font-family: 'Georgia', 'Segoe UI', serif;
    font-size: 15px;
}
#reflection_meta {
    color: #93887D;
    font-size: 11px;
    background: transparent;
}
#reflection_delete_button {
    background: transparent;
    border: none;
    border-radius: 5px;
    color: #93887D;
    font-size: 11px;
    padding: 3px 8px;
}
#reflection_delete_button:hover {
    background-color: #E8DCCB;
    color: #8A5A4B;
}
"""