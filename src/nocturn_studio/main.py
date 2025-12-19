import sys
import os
from PySide6.QtWidgets import QApplication
from .ui.windows.main_window import MainWindow
from .engine.mapper import MappingEngine
from .daw.midi import RTMidiOutput, MockMidiOutput, RTMidiInput
from .hardware.device import MockNocturnDevice, RealNocturnDevice
from .hardware.monitor import FocusMonitor
from .model.mapping import Mapping, MappingTarget, TargetType

from PySide6.QtCore import QTimer
import random

def main():
    # 3. Setup UI
    app = QApplication(sys.argv)
    window = MainWindow()

    # 1. Initialize Components
    try:
        midi_out = RTMidiOutput()
        midi_out.open()
    except Exception as e:
        print(f"MIDI Error: {e}. Falling back to Mock.")
        midi_out = MockMidiOutput()

    # Pass UI update method via bridge for thread-safety
    from .ui.windows.main_window import UIController
    ui_controller = UIController()
    ui_controller.update_signal.connect(window.update_control)
    
    # MIDI Input for Learn/Feedback
    midi_in = RTMidiInput()
    device = RealNocturnDevice()
    if not device.connect():
        print("[System] Real hardware not found. Falling back to Mock.")
        device = MockNocturnDevice()
        device.connect()
        window.status.showMessage("Connected (MOCK DEVICE)")
    else:
        window.status.showMessage("Connected (REAL HARDWARE)")

    def handle_feedback(control_id, value):
        ui_controller.trigger_update(control_id, value)
        device.set_led(control_id, value)
    
    engine = MappingEngine(midi_out, feedback_callback=handle_feedback)
    device.add_event_listener(engine.handle_event)

    def on_focus_changed(app_name, window_title):
        # We try to find a mapping for the window title first, then app name
        # For simplicity, we'll use the window title as the profile name if it exists, 
        # but cleanup is needed (e.g. remove " - " separator common in DAW windows)
        profile = window_title if window_title else app_name
        
        # Filter profile name (you can add more logic here)
        # e.g. "Serum - Preset Name" -> "Serum"
        for common_vst in ["Serum", "VocalSynth", "Sylenth", "FabFilter"]:
            if common_vst.lower() in profile.lower():
                profile = common_vst
                break
        
        engine.switch_profile(profile)
        ui_controller.trigger_plugin(engine.current_profile)

    ui_controller.plugin_signal.connect(window.set_plugin_name)
    
    def on_learn_toggled(checked):
        engine.learn_mode = checked
        print(f"[System] MIDI Learn: {'ON' if checked else 'OFF'}")
        if not checked:
            # Save the profile when exiting learn mode
            engine.save_current_profile()

    # Hook up the UI learn button to the engine
    window.learn_btn.clicked.connect(on_learn_toggled)

    midi_in.open(engine.handle_midi_input)
    
    monitor = FocusMonitor(on_focus_changed)
    monitor.start()
    
    # 3. Comprehensive Mappings (All controls)
    all_mappings = {}
    
    # Encoders 1-8 -> CC 10-17
    for i in range(8):
        id = f"encoder_{i+1}"
        all_mappings[id] = Mapping(id, MappingTarget(TargetType.MIDI_CC, identifier=10+i))
    
    all_mappings["speed_dial"] = Mapping("speed_dial", MappingTarget(TargetType.MIDI_CC, identifier=18))
    all_mappings["crossfader"] = Mapping("crossfader", MappingTarget(TargetType.MIDI_CC, identifier=19))
    
    # Buttons 1-16 -> Notes 40-55
    for i in range(16):
        id = f"button_{i+1}"
        all_mappings[id] = Mapping(id, MappingTarget(TargetType.MIDI_NOTE, identifier=40+i))
        
    all_mappings["button_speed_dial"] = Mapping("button_speed_dial", MappingTarget(TargetType.MIDI_NOTE, identifier=56))

    engine.load_mappings(all_mappings)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
