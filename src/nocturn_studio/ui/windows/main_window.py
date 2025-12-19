import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QPushButton, QLabel, QFrame, QStatusBar)
from PySide6.QtCore import Qt, QSize, QObject, Signal, Slot
from PySide6.QtGui import QColor, QPalette

class UIController(QObject):
    """Bridge for thread-safe UI updates from hardware thread"""
    update_signal = Signal(str, int)
    label_signal = Signal(str, str) # control_id, label
    status_signal = Signal(str, str, bool) # mode, page, shift
    plugin_signal = Signal(str)
    learn_signal = Signal(bool)

    def trigger_update(self, control_id: str, value: int):
        self.update_signal.emit(control_id, value)

    def trigger_label(self, control_id: str, label: str):
        self.label_signal.emit(control_id, label)
        
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
    def __init__(self, name, parent=None, color="#555"):
        super().__init__(parent)
        self.setFixedSize(90, 130)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        self.base_color = color
        
        # Knob visual placeholder
        self.knob = QFrame()
        self.knob.setFixedSize(50, 50)
        self.knob.setStyleSheet(f"""
            QFrame {{
                background-color: #1a1a1a;
                border: 3px solid {color};
                border-radius: 25px;
            }}
        """)
        
        self.label = QLabel(name)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color: #fff; font-size: 11px; font-weight: bold; margin-top: 2px;")
        
        self.value_label = QLabel("0")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("color: #0c0; font-family: 'Courier New', monospace; font-size: 10px; font-weight: bold;")

        layout.addWidget(self.knob, 0, Qt.AlignCenter)
        layout.addWidget(self.label)
        layout.addWidget(self.value_label)

    def set_label(self, text: str):
        self.label.setText(text)

    def set_value(self, val: int):
        self.value_label.setText(str(val))
        # Visual feedback: modulate the base color brightness
        opacity = 50 + int((val / 127) * 205)
        # For simplicity, we'll just keep the base color but maybe grow the border?
        # Or change the value label color
        pass

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
        
        # Status Bar / Panel
        self.status_panel = QHBoxLayout()
        self.status_panel.setSpacing(20)
        self.mode_label = QLabel("MODE: EQ")
        self.page_label = QLabel("PAGE: 1")
        self.shift_label = QLabel("SHIFT")
        
        for lbl in [self.mode_label, self.page_label, self.shift_label]:
            lbl.setStyleSheet("font-weight: bold; color: #444; font-family: 'Courier New', monospace; padding: 5px; border: 1px solid #333;")
            self.status_panel.addWidget(lbl)
        
        self.mode_label.setStyleSheet(self.mode_label.styleSheet() + "color: #0f0; border-color: #0f0;")
        header_layout.addLayout(self.status_panel)
        
        self.main_layout.addLayout(header_layout)

        # Center Section (SSL STRIPS)
        self.strips_layout = QHBoxLayout()
        self.strips_layout.setSpacing(30)
        
        def create_strip(name, controls, color):
            strip = QVBoxLayout()
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; margin-bottom: 5px;")
            strip.addWidget(lbl)
            for cid in controls:
                enc = NocturnEncoder(cid, color=color)
                strip.addWidget(enc)
                self.controls[cid] = enc
            return strip

        # Define Bands
        self.strips_layout.addLayout(create_strip("LOW", ["encoder_1", "encoder_2"], "#888"))
        self.strips_layout.addLayout(create_strip("LO-MID", ["encoder_3", "encoder_4"], "#0af"))
        self.strips_layout.addLayout(create_strip("HI-MID", ["encoder_7", "encoder_6"], "#0f0"))
        self.strips_layout.addLayout(create_strip("HIGH", ["speed_dial", "encoder_8"], "#f0f"))
        
        # Crossfader is separate
        fader_strip = QVBoxLayout()
        fader_strip.setAlignment(Qt.AlignBottom)
        self.fader_label = QLabel("OUTPUT")
        self.fader_label.setAlignment(Qt.AlignCenter)
        self.fader_label.setStyleSheet("color: #f00; font-weight: bold; font-size: 12px;")
        
        self.fader = QSlider(Qt.Horizontal)
        self.fader.setRange(0, 127)
        self.fader.setFixedWidth(100)
        self.fader.setStyleSheet("""
            QSlider::handle:horizontal {
                background: #f00;
                width: 25px;
                border-radius: 4px;
            }
        """)
        self.controls["crossfader"] = self.fader
        fader_strip.addWidget(self.fader_label)
        fader_strip.addWidget(self.fader)
        self.strips_layout.addLayout(fader_strip)

        self.main_layout.addLayout(self.strips_layout)

        # Buttons Section (Original grid but smaller)
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
                ctrl.setChecked(value > 0)
            elif isinstance(ctrl, QSlider):
                ctrl.setValue(value)

    @Slot(str, str)
    def set_control_label(self, control_id: str, label: str):
        if control_id in self.controls:
            ctrl = self.controls[control_id]
            if hasattr(ctrl, "set_label"):
                ctrl.set_label(label)

    @Slot(str)
    def set_plugin_name(self, name: str):
        self.plugin_label.setText(f"Focus: {name}")
        self.status.showMessage(f"Active Profile: {name}")
        
        # Color coding based on focus quality
        if "Global" in name or "None" in name:
            color = "#888" # Grey for generic
        elif "(" in name:
            color = "#ff0" # Yellow for app-level focus
        else:
            color = "#0f0" # Green for specific plugin mapped
            
        self.plugin_label.setStyleSheet(f"font-size: 14px; color: {color}; font-family: 'Courier New', monospace; margin-bottom: 10px;")
        
    @Slot(str, str, bool)
    def update_console_status(self, mode: str, page: str, shift: bool):
        self.mode_label.setText(f"MODE: {mode}")
        self.page_label.setText(f"PAGE: {page}")
        self.shift_label.setStyleSheet(
            "font-weight: bold; font-family: 'Courier New', monospace; padding: 5px; border: 1px solid #0f0; color: #0f0;" if shift 
            else "font-weight: bold; font-family: 'Courier New', monospace; padding: 5px; border: 1px solid #333; color: #444;"
        )
        # Highlight Mode
        self.mode_label.setStyleSheet(
            "font-weight: bold; font-family: 'Courier New', monospace; padding: 5px; border: 1px solid #0f0; color: #0f0;" if mode == "EQ"
            else "font-weight: bold; font-family: 'Courier New', monospace; padding: 5px; border: 1px solid #0af; color: #0af;"
        )

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
