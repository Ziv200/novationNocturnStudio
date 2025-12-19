import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QPushButton, QLabel, QFrame, QStatusBar)
from PySide6.QtCore import Qt, QSize, QObject, Signal, Slot
from PySide6.QtGui import QColor, QPalette

class UIController(QObject):
    """Bridge for thread-safe UI updates from hardware thread"""
    update_signal = Signal(str, int)
    plugin_signal = Signal(str)
    learn_signal = Signal(bool)

    def trigger_update(self, control_id: str, value: int):
        self.update_signal.emit(control_id, value)
        
    def trigger_plugin(self, name: str):
        self.plugin_signal.emit(name)

class NocturnButton(QPushButton):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        self.setFixedSize(45, 30)
        self.setCheckable(True)
        self.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #888;
                border-radius: 4px;
                border: 1px solid #444;
                font-size: 9px;
            }
            QPushButton:checked {
                background-color: #0c0;
                color: black;
                border: 1px solid #0f0;
            }
        """)

class NocturnEncoder(QWidget):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.setFixedSize(70, 110)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Knob visual placeholder
        self.knob = QFrame()
        self.knob.setFixedSize(50, 50)
        self.knob.setStyleSheet("""
            QFrame {
                background-color: #222;
                border: 2px solid #555;
                border-radius: 25px;
            }
        """)
        
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("color: #0f0; font-family: 'Courier New', monospace; font-size: 11px;")

        self.label = QLabel(name)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #aaa; font-size: 10px;")
        
        layout.addWidget(self.knob, 0, Qt.AlignCenter)
        layout.addWidget(self.value_label)
        layout.addWidget(self.label)

    def set_value(self, val: int):
        self.value_label.setText(str(val))
        # Visual feedback: brighten the border
        # val is 0-127. Let's map to a green brightness.
        brightness = 100 + val
        # Use RGB for standard compatibility
        self.knob.setStyleSheet(f"""
            QFrame {{
                background-color: #222;
                border: 2px solid rgb(0, {brightness}, 0);
                border-radius: 25px;
            }}
        """)

from PySide6.QtWidgets import QSlider

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nocturn Studio")
        self.resize(1000, 650)
        self.controls = {} # Combined dict for all visual controls
        
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(25, 25, 25))
        palette.setColor(QPalette.WindowText, Qt.white)
        self.setPalette(palette)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(25)
        self.main_layout.setContentsMargins(40, 40, 40, 40)

        # Header
        header_layout = QVBoxLayout()
        self.header = QLabel("NOCTURN STUDIO")
        self.header.setStyleSheet("font-size: 28px; font-weight: bold; color: #fff; letter-spacing: 5px;")
        
        self.plugin_label = QLabel("Focus: Global")
        self.plugin_label.setStyleSheet("font-size: 14px; color: #0f0; font-family: 'Courier New', monospace; margin-bottom: 10px;")
        
        self.learn_btn = QPushButton("MIDI LEARN")
        self.learn_btn.setCheckable(True)
        self.learn_btn.setFixedSize(120, 35)
        self.learn_btn.setStyleSheet("""
            QPushButton {
                background-color: #222;
                color: #555;
                font-weight: bold;
                border: 2px solid #333;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #f00;
                color: white;
                border: 2px solid #ff4444;
            }
        """)
        self.learn_btn.clicked.connect(self._on_learn_clicked)
        
        header_layout.addWidget(self.header, 0, Qt.AlignCenter)
        header_layout.addWidget(self.plugin_label, 0, Qt.AlignCenter)
        header_layout.addWidget(self.learn_btn, 0, Qt.AlignCenter)
        self.main_layout.addLayout(header_layout)

        # Center Section (Encoders + Speed Dial)
        self.top_row = QHBoxLayout()
        
        # Encoders 1-8
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        for i in range(8):
            enc_id = f"encoder_{i+1}"
            encoder = NocturnEncoder(f"Knob {i+1}")
            self.grid_layout.addWidget(encoder, i // 4, i % 4)
            self.controls[enc_id] = encoder
        
        self.top_row.addLayout(self.grid_layout)
        
        # Right Side (Speed Dial + Crossfader)
        self.side_layout = QVBoxLayout()
        self.side_layout.setAlignment(Qt.AlignCenter)
        
        self.speed_dial = NocturnEncoder("Speed Dial")
        self.controls["speed_dial"] = self.speed_dial
        self.side_layout.addWidget(self.speed_dial)
        
        self.fader_label = QLabel("Crossfader")
        self.fader_label.setAlignment(Qt.AlignCenter)
        self.fader_label.setStyleSheet("color: #666; font-size: 10px;")
        
        self.fader = QSlider(Qt.Horizontal)
        self.fader.setRange(0, 127)
        self.fader.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #555;
                width: 20px;
                border-radius: 3px;
            }
        """)
        self.controls["crossfader"] = self.fader
        
        self.side_layout.addSpacing(20)
        self.side_layout.addWidget(self.fader_label)
        self.side_layout.addWidget(self.fader)
        
        self.top_row.addLayout(self.side_layout)
        self.main_layout.addLayout(self.top_row)

        # Buttons Section (2 rows of 8)
        self.buttons_grid = QGridLayout()
        self.buttons_grid.setSpacing(10)
        for i in range(16):
            btn_id = f"button_{i+1}"
            btn = NocturnButton(f"BT{i+1}")
            self.buttons_grid.addWidget(btn, i // 8, i % 8)
            self.controls[btn_id] = btn
        
        # Speed Dial Button
        self.sd_btn = NocturnButton("SD BTN")
        self.buttons_grid.addWidget(self.sd_btn, 0, 8)
        self.controls["button_speed_dial"] = self.sd_btn

        self.main_layout.addLayout(self.buttons_grid)

        # Status Bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.setStyleSheet("color: #888; background-color: #111; border-top: 1px solid #333;")
        self.status.showMessage("Initializing...")

    @Slot(str, int)
    def update_control(self, control_id: str, value: int):
        if control_id in self.controls:
            ctrl = self.controls[control_id]
            if isinstance(ctrl, NocturnEncoder):
                ctrl.set_value(value)
            elif isinstance(ctrl, NocturnButton):
                # UI toggle based on value (0 or 127)
                ctrl.setChecked(value > 0)
            elif isinstance(ctrl, QSlider):
                ctrl.setValue(value)

    @Slot(str)
    def set_plugin_name(self, name: str):
        self.plugin_label.setText(f"Focus: {name}")
        self.status.showMessage(f"Active Profile: {name}")
        
    def _on_learn_clicked(self, checked):
        # Notify whoever is listening (Main app/Engine)
        # We use a signal to keep it decoupled
        pass 

def run_app():
    app = sys.modules.get('PySide6.QtWidgets').QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
