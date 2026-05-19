import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QFileDialog, 
    QColorDialog, QMessageBox, QMenuBar, QStatusBar, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
)
from PyQt6.QtGui import QFont, QKeySequence, QAction, QColor
from PyQt6.QtCore import Qt

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

        self._build_ui()
        self.apply_colors(
            self.settings.get("bg_color", "#1e1e1e"),
            self.settings.get("fg_color", "#f2f2f2")
        )

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_editor(main_layout)
        self._build_menu()
        self._build_toolbar(main_layout)
        self._build_statusbar()

        self.update_title()

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
        self.add_action(view_menu, "Zoom In", "Ctrl++", self.zoom_in)
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

    def _build_toolbar(self, layout):
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(4, 4, 4, 4)
        toolbar_layout.setSpacing(4)

        buttons = [
            ("New", self.new_file),
            ("Open", self.open_file),
            ("Save", self.save_file),
            ("BG Color", self.choose_bg_color),
            ("Text Color", self.choose_fg_color),
        ]

        for text, cmd in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(cmd)
            toolbar_layout.addWidget(btn)
        
        toolbar_layout.addStretch()
        layout.addWidget(toolbar_widget)

    def _build_editor(self, layout):
        self.text = QTextEdit()
        self.text.setFont(QFont("Consolas", self.font_size))
        self.text.textChanged.connect(self.on_modified)
        self.text.cursorPositionChanged.connect(self.update_cursor_position)
        layout.addWidget(self.text)

    def _build_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ln 1, Col 1")

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
        self.status.showMessage(f"Zoom: {self.font_size}pt", 2000)

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

    # ── Colors ────────────────────────────────────────────────────────────────

    def apply_colors(self, bg, fg):
        self.settings["bg_color"] = bg
        self.settings["fg_color"] = fg
        style = f"background-color: {bg}; color: {fg}; selection-background-color: #4a6984; border: none;"
        self.text.setStyleSheet(style)

    def reset_theme(self):
        self.apply_colors("#1e1e1e", "#f2f2f2")
        self.save_settings()

    def choose_bg_color(self):
        # FIX: seed dialog with the CURRENT background color instead of hardcoded black
        current = QColor(self.settings.get("bg_color", "#1e1e1e"))
        color = QColorDialog.getColor(current, self, "Choose background color")
        if color.isValid():
            self.apply_colors(color.name(), self.settings.get("fg_color", "#f2f2f2"))
            self.save_settings()

    def choose_fg_color(self):
        # FIX: seed dialog with the CURRENT text color instead of hardcoded white
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

    # ── File ops ──────────────────────────────────────────────────────────────

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

    def open_file(self):
        if not self.confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text files (*.txt);;All files (*.*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text.setPlainText(content)
            self.current_file = path
            self.text.document().setModified(False)
            self.update_title()
        except Exception as e:
            QMessageBox.critical(self, "Open failed", f"Could not open file:\n{e}")

    def save_file(self):
        if self.current_file is None:
            return self.save_as()
        try:
            content = self.text.toPlainText()
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.text.document().setModified(False)
            self.update_title()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"Could not save file:\n{e}")
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

    def update_cursor_position(self):
        cursor = self.text.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.status.showMessage(f"Ln {line}, Col {col}")

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
