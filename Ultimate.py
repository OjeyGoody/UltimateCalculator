import sys
import os
import shutil
import math
import platform
import subprocess
import urllib.request
import urllib.parse
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QLineEdit,
                             QTextEdit, QStackedWidget, QLabel, QGraphicsDropShadowEffect,
                             QTabWidget, QListWidget, QFileDialog, QMessageBox)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, QTimer

# --- UI/UX DESIGN SYSTEM ---
BG_COLOR = "#0D0D12"
NEON_CYAN = "#08f7fe"
NEON_PINK = "#fe53bb"
NEON_GREEN = "#39ff14"
SECRET_PIN = "7777"


class NeonButton(QPushButton):
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        self.setMinimumHeight(60)
        self.color = color

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #15151A;
                color: {self.color};
                border: 2px solid {self.color};
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background-color: #22222A;
            }}
            QPushButton:pressed {{
                background-color: {self.color};
                color: #000000;
            }}
        """)

        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(20)
        self.glow.setColor(QColor(self.color))
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)


class CalculatorVault(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberCalc OS")
        self.setFixedSize(450, 700)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.vault_dir = os.path.join(os.getcwd(), "secret_vault_files")
        os.makedirs(self.vault_dir, exist_ok=True)

        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.animated_glows = []

        self.init_calculator_ui()
        self.init_vault_ui()

        self.anim_step = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.pulse_glows)
        self.timer.start(50)

    def init_calculator_ui(self):
        calc_widget = QWidget()
        layout = QVBoxLayout(calc_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setFont(QFont("Consolas", 36, QFont.Weight.Bold))
        self.display.setStyleSheet(f"""
            QLineEdit {{
                background-color: #101015;
                color: {NEON_CYAN};
                border: 2px solid {NEON_CYAN};
                border-radius: 10px;
                padding: 10px;
            }}
        """)

        display_glow = QGraphicsDropShadowEffect()
        display_glow.setBlurRadius(30)
        display_glow.setColor(QColor(NEON_CYAN))
        display_glow.setOffset(0, 0)
        self.display.setGraphicsEffect(display_glow)
        self.animated_glows.append((display_glow, 25, 20))
        layout.addWidget(self.display)

        grid = QGridLayout()
        grid.setSpacing(15)
        buttons = [
            ('C', 0, 0, NEON_PINK), ('(', 0, 1, NEON_CYAN), (')', 0, 2, NEON_CYAN), ('/', 0, 3, NEON_PINK),
            ('7', 1, 0, NEON_CYAN), ('8', 1, 1, NEON_CYAN), ('9', 1, 2, NEON_CYAN), ('*', 1, 3, NEON_PINK),
            ('4', 2, 0, NEON_CYAN), ('5', 2, 1, NEON_CYAN), ('6', 2, 2, NEON_CYAN), ('-', 2, 3, NEON_PINK),
            ('1', 3, 0, NEON_CYAN), ('2', 3, 1, NEON_CYAN), ('3', 3, 2, NEON_CYAN), ('+', 3, 3, NEON_PINK),
            ('0', 4, 0, NEON_CYAN), ('.', 4, 1, NEON_CYAN), ('<', 4, 2, NEON_PINK), ('=', 4, 3, NEON_GREEN)
        ]

        for text, row, col, color in buttons:
            btn = NeonButton(text, color)
            btn.clicked.connect(lambda checked, t=text: self.on_calc_click(t))
            grid.addWidget(btn, row, col)

        layout.addLayout(grid)
        self.stack.addWidget(calc_widget)

    def init_vault_ui(self):
        vault_widget = QWidget()
        layout = QVBoxLayout(vault_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QLabel("ENCRYPTED VAULT")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Consolas", 26, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {NEON_GREEN};")

        header_glow = QGraphicsDropShadowEffect()
        header_glow.setBlurRadius(30)
        header_glow.setColor(QColor(NEON_GREEN))
        header_glow.setOffset(0, 0)
        header.setGraphicsEffect(header_glow)
        self.animated_glows.append((header_glow, 30, 25))
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 2px solid {NEON_GREEN}; border-radius: 10px; background: #0A0A0E; }}
            QTabBar::tab {{ background: #15151A; color: {NEON_GREEN}; padding: 10px 20px; font-family: Consolas; font-weight: bold; border: 1px solid {NEON_GREEN}; }}
            QTabBar::tab:selected {{ background: {NEON_GREEN}; color: #000000; }}
        """)

        tabs_glow = QGraphicsDropShadowEffect()
        tabs_glow.setColor(QColor(NEON_GREEN))
        tabs_glow.setOffset(0, 0)
        tabs.setGraphicsEffect(tabs_glow)
        self.animated_glows.append((tabs_glow, 15, 10))

        # --- Tab 1: Notes (UPDATED WITH SHARE BUTTON) ---
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)

        self.secret_pad = QTextEdit()
        self.secret_pad.setFont(QFont("Consolas", 12))
        self.secret_pad.setPlaceholderText("Write your secrets here...")
        self.secret_pad.setStyleSheet("background-color: transparent; color: #39ff14; border: none; padding: 10px;")

        share_btn = NeonButton("GENERATE SHARE LINK", NEON_CYAN)
        share_btn.setMinimumHeight(40)
        share_btn.clicked.connect(self.share_note)

        notes_layout.addWidget(self.secret_pad)
        notes_layout.addWidget(share_btn)
        tabs.addTab(notes_tab, "Secret Notes")

        # --- Tab 2: File Storage ---
        file_tab = QWidget()
        file_layout = QVBoxLayout(file_tab)

        self.file_list = QListWidget()
        self.file_list.setFont(QFont("Consolas", 10))
        self.file_list.setStyleSheet(f"""
            QListWidget {{ background-color: transparent; color: #fff; border: none; padding: 5px; }}
            QListWidget::item:selected {{ background-color: {NEON_GREEN}; color: #000; }}
        """)
        file_layout.addWidget(self.file_list)

        btn_layout = QHBoxLayout()
        add_btn = NeonButton("+ ADD FILE", NEON_CYAN)
        add_btn.setMinimumHeight(40)
        add_btn.clicked.connect(self.add_file)

        open_btn = NeonButton("OPEN SELECTED", NEON_GREEN)
        open_btn.setMinimumHeight(40)
        open_btn.clicked.connect(self.open_file)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(open_btn)
        file_layout.addLayout(btn_layout)
        tabs.addTab(file_tab, "Secure Files")

        layout.addWidget(tabs)

        lock_btn = NeonButton("LOCK VAULT", NEON_PINK)
        lock_btn.clicked.connect(self.lock_vault)
        layout.addWidget(lock_btn)

        self.stack.addWidget(vault_widget)

    def pulse_glows(self):
        self.anim_step += 0.1
        pulse_multiplier = (math.sin(self.anim_step) + 1) / 2
        for effect, base_blur, pulse_intensity in self.animated_glows:
            current_blur = base_blur + (pulse_multiplier * pulse_intensity)
            effect.setBlurRadius(current_blur)

    def on_calc_click(self, text):
        current = self.display.text()
        if text == 'C':
            self.display.clear()
        elif text == '<':
            self.display.setText(current[:-1])
        elif text == '=':
            if current == SECRET_PIN:
                self.unlock_vault()
                return
            try:
                open_parens = current.count('(')
                close_parens = current.count(')')
                if open_parens > close_parens:
                    current += ')' * (open_parens - close_parens)
                result = str(eval(current))
                self.display.setText(result)
            except Exception:
                self.display.setText("ERROR")
        else:
            if current == "ERROR":
                self.display.setText(text)
            else:
                self.display.setText(current + text)

    # --- VAULT LOGIC ---
    def unlock_vault(self):
        self.display.clear()
        self.refresh_file_list()
        self.stack.setCurrentIndex(1)

    def lock_vault(self):
        self.stack.setCurrentIndex(0)

    def share_note(self):
        text = self.secret_pad.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Empty Note", "There is no text to share!")
            return

        # Security Warning before beaming to the internet
        reply = QMessageBox.question(self, 'Security Warning',
                                     "This will encrypt and temporarily upload your note to the internet to generate a link.\n\nContinue?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Send the text to a self-destructing text API
                url = 'https://dpaste.com/api/v2/'
                data = urllib.parse.urlencode({'content': text, 'expiry_days': 1}).encode('utf-8')
                req = urllib.request.Request(url, data=data)

                with urllib.request.urlopen(req) as response:
                    # Get the generated URL
                    link = response.read().decode('utf-8').strip()

                    # Copy link to the user's system clipboard
                    QApplication.clipboard().setText(link)

                    QMessageBox.information(self, "Success",
                                            f"Link generated and copied to clipboard!\n\n{link}\n\n(It will self-destruct in 1 day)")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not generate link. Check your internet connection.\n\n{e}")

    def refresh_file_list(self):
        self.file_list.clear()
        for filename in os.listdir(self.vault_dir):
            self.file_list.addItem(filename)

    def add_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select File to Hide")
        if filepath:
            filename = os.path.basename(filepath)
            dest_path = os.path.join(self.vault_dir, filename)
            try:
                shutil.copy2(filepath, dest_path)
                self.refresh_file_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add file:\n{e}")

    def open_file(self):
        selected = self.file_list.selectedItems()
        if not selected:
            return

        filename = selected[0].text()
        filepath = os.path.join(self.vault_dir, filename)

        if platform.system() == 'Darwin':
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':
            os.startfile(filepath)
        else:
            subprocess.call(('xdg-open', filepath))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    calc = CalculatorVault()
    calc.show()
    sys.exit(app.exec())