import rtmidi
from dataclasses import dataclass
from typing import List

@dataclass
class MidiMessage:
    status: int
    data1: int
    data2: int

class MidiOutputInterface:
    def send(self, msg: MidiMessage):
        raise NotImplementedError

class RTMidiOutput(MidiOutputInterface):
    """Real MIDI output using rtmidi and virtual ports."""
    def __init__(self, port_name: str = "Nocturn Studio Out"):
        self.midi_out = rtmidi.MidiOut()
        self.port_name = port_name
        self.is_open = False

    def open(self):
        # On macOS, we create a virtual port
        self.midi_out.open_virtual_port(self.port_name)
        self.is_open = True
        print(f"[MIDI] Virtual port '{self.port_name}' opened.")

    def send(self, msg: MidiMessage):
        if not self.is_open:
            return
        # rtmidi expects a list of bytes
        self.midi_out.send_message([msg.status, msg.data1, msg.data2])

class MockMidiOutput(MidiOutputInterface):
    def __init__(self):
        self.sent_messages: List[MidiMessage] = []

    def send(self, msg: MidiMessage):
        self.sent_messages.append(msg)
        print(f"[MockMIDI] Sent: {msg}")
