from typing import Dict, Optional, Callable
from ..utils.persistence import PersistenceManager
from ..model.events import ControlEvent, ControlEventType
from ..model.mapping import Mapping, MappingMode, TargetType
from ..daw.midi import MidiOutputInterface, MidiMessage

class MappingEngine:
    def __init__(self, midi_out: MidiOutputInterface, feedback_callback: Optional[Callable[[str, int], None]] = None):
        self.midi_out = midi_out
        self.feedback_callback = feedback_callback
        self.persistence = PersistenceManager()
        self.mappings: Dict[str, Mapping] = {}
        # Store current values for controls (virtual state)
        # keyed by source_id -> int (0-127 usually)
        self.values: Dict[str, int] = {} 
        self.current_profile = "Global"
        
        # MIDI Learn State
        self.learn_mode = False
        self.last_touched_id: Optional[str] = None

    def load_mappings(self, mappings: Dict[str, Mapping], profile_name: str = "Global"):
        self.mappings = mappings
        self.current_profile = profile_name
        # Initialize values to 0 if unknown
        for k in mappings:
            if k not in self.values:
                self.values[k] = 0

    def switch_profile(self, profile_name: str):
        if profile_name == self.current_profile:
            return
            
        print(f"[Engine] Searching for profile: {profile_name}")
        # Try to load from persistence
        new_mappings = self.persistence.load_preset(profile_name)
        if new_mappings:
            self.load_mappings(new_mappings, profile_name)
            print(f"[Engine] Switched to profile: {profile_name}")
            # Refresh UI/Hardware with current values
            for source_id, val in self.values.items():
                if self.feedback_callback:
                    self.feedback_callback(source_id, val)
        else:
            # Fallback to Global if not already there
            if profile_name != "Global":
                self.switch_profile("Global")

    def handle_event(self, event: ControlEvent):
        # Track last touched control for MIDI Learn
        self.last_touched_id = event.source_id
        
        if event.source_id not in self.mappings:
            return

        mapping = self.mappings[event.source_id]
        
        if event.type == ControlEventType.ENCODER_TURN:
            self._handle_encoder(event, mapping)
        elif event.type in (ControlEventType.BUTTON_PRESS, ControlEventType.BUTTON_RELEASE):
            self._handle_button(event, mapping)
        elif event.type == ControlEventType.CROSSFADER_MOVE:
            self._handle_fader(event, mapping)

    def _handle_encoder(self, event: ControlEvent, mapping: Mapping):
        # We assume MappingMode.ABSOLUTE target for now (Virtual CC 0-127)
        # But input is RELATIVE (delta).
        
        current_val = self.values.get(event.source_id, 0)
        
        # Calculate new value
        # event.value is delta (positive or negative)
        new_val = current_val + event.value
        
        # Clamp
        new_val = max(mapping.min_val, min(mapping.max_val, new_val))
        
        if new_val != current_val:
            self.values[event.source_id] = new_val
            self._send_midi(mapping, new_val)
            if self.feedback_callback:
                self.feedback_callback(event.source_id, new_val)

    def _handle_button(self, event: ControlEvent, mapping: Mapping):
        # We pass the raw value (0 or 127) to MIDI and UI
        val = 127 if event.type == ControlEventType.BUTTON_PRESS else 0
        self._send_midi(mapping, val)
        if self.feedback_callback:
            self.feedback_callback(event.source_id, val)

    def _handle_fader(self, event: ControlEvent, mapping: Mapping):
        # event.value is 0-127
        self._send_midi(mapping, event.value)
        if self.feedback_callback:
            self.feedback_callback(event.source_id, event.value)

    def handle_midi_input(self, msg: MidiMessage):
        """Handle incoming MIDI from DAW for feedback or Learning."""
        # 1. Feedback Loop: If a CC matches a mapping, update local value and hardware
        matched_any = False
        for source_id, mapping in self.mappings.items():
            if mapping.target.type == TargetType.MIDI_CC and mapping.target.identifier == msg.data1:
                self.values[source_id] = msg.data2
                if self.feedback_callback:
                    self.feedback_callback(source_id, msg.data2)
                matched_any = True
        
        # 2. MIDI Learn: If in learn mode, assign last touched hardware to this MIDI CC
        if self.learn_mode and self.last_touched_id and not matched_any:
            if (msg.status & 0xF0) == 0xB0: # Control Change
                new_target = MappingTarget(TargetType.MIDI_CC, identifier=msg.data1, channel=(msg.status & 0x0F))
                self.mappings[self.last_touched_id] = Mapping(self.last_touched_id, new_target)
                print(f"[Engine] Learned: {self.last_touched_id} -> CC {msg.data1}")
                # Save immediately? For now just keep in memory
                # self.save_current_profile()
    
    def save_current_profile(self):
        self.persistence.save_preset(self.current_profile, self.mappings)

    def _send_midi(self, mapping: Mapping, value: int):
        if mapping.target.type == TargetType.MIDI_CC:
            # Construct CC message: 0xB0 | channel, CC number, value
            status = 0xB0 | (mapping.target.channel & 0x0F)
            msg = MidiMessage(status, mapping.target.identifier, value)
            self.midi_out.send(msg)
