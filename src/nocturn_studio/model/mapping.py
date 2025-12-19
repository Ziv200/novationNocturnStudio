from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

class MappingMode(Enum):
    ABSOLUTE = auto()
    RELATIVE_TWOS_COMP = auto() # Standard MIDI relative
    RELATIVE_BINARY_OFFSET = auto() # 63=dec, 65=inc
    RELATIVE_SIGNED_BIT = auto()
    SWITCH_TOGGLE = auto()
    SWITCH_MOMENTARY = auto()

class TargetType(Enum):
    MIDI_CC = auto()
    MIDI_NOTE = auto()
    MIDI_PITCHBEND = auto()
    KEYBOARD_SHORTCUT = auto() # Future proofing

@dataclass
class MappingTarget:
    type: TargetType
    channel: int = 0
    identifier: int = 0 # CC Number or Note Number
    
@dataclass
class Mapping:
    source_id: str
    target: MappingTarget
    mode: MappingMode = MappingMode.ABSOLUTE
    min_val: int = 0
    max_val: int = 127
    enabled: bool = True
