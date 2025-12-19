from typing import Dict, Optional, Callable
from ..model.events import ControlEvent, ControlEventType
from ..model.mapping import Mapping, MappingMode, TargetType
from ..daw.midi import MidiOutputInterface, MidiMessage

class MappingEngine:
    def __init__(self, midi_out: MidiOutputInterface, feedback_callback: Optional[Callable[[str, int], None]] = None):
        self.midi_out = midi_out
        self.feedback_callback = feedback_callback
        self.mappings: Dict[str, Mapping] = {}
        # Store current values for controls (virtual state)
        # keyed by source_id -> int (0-127 usually)
        self.values: Dict[str, int] = {} 

    def load_mappings(self, mappings: Dict[str, Mapping]):
        self.mappings = mappings
        # Initialize values to 0 if unknown
        for k in mappings:
            if k not in self.values:
                self.values[k] = 0

    def handle_event(self, event: ControlEvent):
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

    def _send_midi(self, mapping: Mapping, value: int):
        if mapping.target.type == TargetType.MIDI_CC:
            # Construct CC message: 0xB0 | channel, CC number, value
            status = 0xB0 | (mapping.target.channel & 0x0F)
            msg = MidiMessage(status, mapping.target.identifier, value)
            self.midi_out.send(msg)
