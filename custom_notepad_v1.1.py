import sys
import os
import json
from PyQt6.QtWidgets import ( 
    QApplication, QMainWindow, QTextEdit, QFileDialog, QColorDialog, 
    QMessageBox, QMenuBar, QVBoxLayout, QWidget, QHBoxLayout, 
    QPushButton, QLabel 
)
from PyQt6.QtGui import QFont, QKeySequence, QAction, QColor
from PyQt6.QtCore import Qt, QFileSystemWatcher

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".custom_notepad_settings.json")
DEFAULT_FONT_SIZE = 11
MIN_FONT_SIZE = 6
MAX_FONT_SIZE = 72

class CustomNotepad(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Notepad")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(640, 420)

        self.current_file = None
        self.font_size = DEFAULT_FONT_SIZE
        self.settings = self.load_settings()

        # File watcher to detect external modifications
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self.on_file_changed_externally)
        self.last_mtime = 0

        self._build_ui()
        self.apply_colors(
            self.settings.get("bg_color", "#1e1e1e"),
            self.settings.get("fg_color", "#f2f2f2")
        )

    def _build_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_editor(main_layout)
        self._build_menu()
        self._build_bottom_bar(main_layout)

        self.update_title()
        self.update_status_label()

    def _build_menu(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("File")
        self.add_action(file_menu, "New", "Ctrl+N", self.new_file)
        self.add_action(file_menu, "Open...", "Ctrl+O", self.open_file)
        self.add_action(file_menu, "Save", "Ctrl+S", self.save_file)
        self.add_action(file_menu, "Save As...", "Ctrl+Shift+S", self.save_as)
        file_menu.addSeparator()
        self.add_action(file_menu, "Exit", "", self.close)

        # Edit Menu
        edit_menu = menubar.addMenu("Edit")
        self.add_action(edit_menu, "Undo", "Ctrl+Z", self.text.undo)
        self.add_action(edit_menu, "Redo", "Ctrl+Y", self.text.redo)
        edit_menu.addSeparator()
        self.add_action(edit_menu, "Cut", "Ctrl+X", self.text.cut)
        self.add_action(edit_menu, "Copy", "Ctrl+C", self.text.copy)
        self.add_action(edit_menu, "Paste", "Ctrl+V", self.text.paste)
        self.add_action(edit_menu, "Select All", "Ctrl+A", self.text.selectAll)

        # View Menu
        view_menu = menubar.addMenu("View")
        self.wrap_action = QAction("Word Wrap", self, checkable=True)
        self.wrap_action.setChecked(True)
        self.wrap_action.triggered.connect(self.toggle_wrap)
        view_menu.addAction(self.wrap_action)
        view_menu.addSeparator()
        self.add_action(view_menu, "Zoom In", "Ctrl+=", self.zoom_in)
        self.add_action(view_menu, "Zoom Out", "Ctrl+-", self.zoom_out)
        self.add_action(view_menu, "Reset Zoom", "Ctrl+0", self.zoom_reset)

        # Theme Menu
        theme_menu = menubar.addMenu("Theme")
        self.add_action(theme_menu, "Set Background Color...", "", self.choose_bg_color)
        self.add_action(theme_menu, "Set Text Color...", "", self.choose_fg_color)
        theme_menu.addSeparator()
        self.add_action(theme_menu, "Reset Theme", "", self.reset_theme)

        # Help Menu
        help_menu = menubar.addMenu("Help")
        self.add_action(help_menu, "About", "", self.show_about)

    def add_action(self, menu, label, shortcut, callback):
        action = QAction(label, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(callback)
        menu.addAction(action)
        return action

    def _build_editor(self, layout):
        self.text = QTextEdit()
        self.text.setFont(QFont("Consolas", self.font_size))
        self.text.textChanged.connect(self.on_modified)
        self.text.cursorPositionChanged.connect(self.update_status_label)
        layout.addWidget(self.text)

    def _build_bottom_bar(self, layout):
        # The new combined bar! 
        bottom_widget = QWidget()
        bottom_widget.setObjectName("BottomWidget")
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(8, 6, 8, 6)
        bottom_layout.setSpacing(10)

        # Status Label on the left
        self.status_label = QLabel("Ln 1, Col 1")
        bottom_layout.addWidget(self.status_label)

        # Toolbar buttons beside it
        buttons = [
            ("New", self.new_file),
            ("Open", self.open_file),
            ("Save", self.save_file),
            ("BG Color", self.choose_bg_color),
            ("Text Color", self.choose_fg_color),
        ]

        for text, cmd in buttons:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(cmd)
            bottom_layout.addWidget(btn)
        
        # Pushes everything to the left
        bottom_layout.addStretch()
        layout.addWidget(bottom_widget)

    # ── Zoom ──────────────────────────────────────────────────────────────────

    def zoom_in(self):
        self.font_size = min(self.font_size + 1, MAX_FONT_SIZE)
        self._apply_font_size()

    def zoom_out(self):
        self.font_size = max(self.font_size - 1, MIN_FONT_SIZE)
        self._apply_font_size()

    def zoom_reset(self):
        self.font_size = DEFAULT_FONT_SIZE
        self._apply_font_size()

    def _apply_font_size(self):
        font = self.text.font()
        font.setPointSize(self.font_size)
        self.text.setFont(font)
        self.update_status_label()

    def wheelEvent(self, event):
        """Ctrl+Scroll also zooms, just like Notepad/browsers."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    # ── Settings ──────────────────────────────────────────────────────────────

    def load_settings(self):
        default = {"bg_color": "#1e1e1e", "fg_color": "#f2f2f2"}
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        default.update(data)
        except Exception:
            pass
        return default

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass

    # ── Colors & Global Styling ───────────────────────────────────────────────

    def apply_colors(self, bg, fg):
        self.settings["bg_color"] = bg
        self.settings["fg_color"] = fg
        
        # This styles all the "main" things universally!
        style = f"""
            QMainWindow, #CentralWidget, #BottomWidget, QTextEdit, QLabel, QMenuBar, QMenu {{
                background-color: {bg};
                color: {fg};
            }}
            QTextEdit {{
                selection-background-color: #4a6984;
                border: none;
                padding-left: 10px;
            }}
            QPushButton {{
                border: 1px solid {fg};
                padding: 4px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #4a6984;
                color: #ffffff;
                border: 1px solid #4a6984;
            }}
            QMenuBar::item:selected, QMenu::item:selected {{
                background-color: #4a6984;
                color: #ffffff;
            }}
            QScrollBar:vertical {{
                background: {bg};
                width: 12px;
            }}
            QScrollBar::handle:vertical {{
                background: {fg};
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """
        self.setStyleSheet(style)

    def reset_theme(self):
        self.apply_colors("#1e1e1e", "#f2f2f2")
        self.save_settings()

    def choose_bg_color(self):
        current = QColor(self.settings.get("bg_color", "#1e1e1e"))
        color = QColorDialog.getColor(current, self, "Choose background color")
        if color.isValid():
            self.apply_colors(color.name(), self.settings.get("fg_color", "#f2f2f2"))
            self.save_settings()

    def choose_fg_color(self):
        current = QColor(self.settings.get("fg_color", "#f2f2f2"))
        color = QColorDialog.getColor(current, self, "Choose text color")
        if color.isValid():
            self.apply_colors(self.settings.get("bg_color", "#1e1e1e"), color.name())
            self.save_settings()

    def toggle_wrap(self):
        if self.wrap_action.isChecked():
            self.text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

    # ── File ops & Watcher ────────────────────────────────────────────────────

    def update_watcher(self):
        """Updates the File Watcher so it only monitors the current file."""
        if self.watcher.files():
            self.watcher.removePaths(self.watcher.files())
        if self.current_file and os.path.exists(self.current_file):
            self.watcher.addPath(self.current_file)
            self.last_mtime = os.path.getmtime(self.current_file)

    def on_file_changed_externally(self, path):
        """Triggered when another program modifies the opened file."""
        if path != self.current_file or not os.path.exists(path):
            return
            
        try:
            current_mtime = os.path.getmtime(path)
        except Exception:
            return

        if current_mtime == self.last_mtime:
            return
            
        if not self.text.document().isModified():
            self.reload_file()
        else:
            reply = QMessageBox.question(
                self, "File Modified",
                f"The file '{os.path.basename(path)}' has been modified by another program.\nDo you want to reload it and lose your unsaved changes?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.reload_file()
            else:
                self.last_mtime = current_mtime

    def reload_file(self):
        if not self.current_file or not os.path.exists(self.current_file):
            return
        try:
            with open(self.current_file, "r", encoding="utf-8-sig") as f:
                content = f.read()
            
            cursor = self.text.textCursor()
            pos = cursor.position()
            v_scroll = self.text.verticalScrollBar().value()

            self.text.setPlainText(content)
            self.text.document().setModified(False)
            self.update_title()
            self.update_watcher()

            cursor.setPosition(min(pos, len(self.text.toPlainText())))
            self.text.setTextCursor(cursor)
            self.text.verticalScrollBar().setValue(v_scroll)
        except Exception as e:
            QMessageBox.critical(self, "Reload failed", f"Could not reload file:\n{e}")

    def closeEvent(self, event):
        if self.confirm_discard_changes():
            self.save_settings()
            event.accept()
        else:
            event.ignore()

    def confirm_discard_changes(self):
        if self.text.document().isModified():
            box = QMessageBox()
            box.setWindowTitle("Unsaved changes")
            box.setText("Save changes before continuing?")
            box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            answer = box.exec()

            if answer == QMessageBox.StandardButton.Cancel:
                return False
            if answer == QMessageBox.StandardButton.Yes:
                return self.save_file()
        return True

    def new_file(self):
        if not self.confirm_discard_changes():
            return
        self.text.clear()
        self.current_file = None
        self.text.document().setModified(False)
        self.update_title()
        self.update_watcher()

    def open_file(self):
        if not self.confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text files (*.txt);;All files (*.*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
            self.text.setPlainText(content)
            self.current_file = path
            self.text.document().setModified(False)
            self.update_title()
            self.update_watcher()
        except Exception as e:
            QMessageBox.critical(self, "Open failed", f"Could not open file:\n{e}")

    def save_file(self):
        if self.current_file is None:
            return self.save_as()
        try:
            if self.watcher.files():
                self.watcher.removePaths(self.watcher.files())

            content = self.text.toPlainText()
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(content)

            self.text.document().setModified(False)
            self.update_title()
            self.update_watcher()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"Could not save file:\n{e}")
            self.update_watcher()
            return False

    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "Text files (*.txt);;All files (*.*)")
        if not path:
            return False
        self.current_file = path
        return self.save_file()

    def on_modified(self):
        self.update_title()

    def update_title(self):
        name = os.path.basename(self.current_file) if self.current_file else "Untitled"
        star = "*" if self.text.document().isModified() else ""
        self.setWindowTitle(f"{name}{star} - Custom Notepad")

    def update_status_label(self):
        cursor = self.text.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.status_label.setText(f"Ln {line}, Col {col}   |   Zoom: {self.font_size}pt")

    def show_about(self):
        QMessageBox.information(
            self, "About",
            "Custom Notepad\n\nA simple text editor built with Python and PyQt6.\nIt supports plain text only, with customizable background and text colors."
        )


if __name__ == "__main__": 
    app = QApplication(sys.argv) 
    notepad = CustomNotepad()
    notepad.show() 
    sys.exit(app.exec())
