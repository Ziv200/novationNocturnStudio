from enum import Enum, auto
from dataclasses import dataclass

class ControlType(Enum):
    ENCODER = auto()
    BUTTON = auto()
    CROSSFADER = auto()

@dataclass
class HardwareControl:
    id: str         # Unique ID, e.g., "encoder_1", "btn_user"
    type: ControlType
    name: str       # Human readable name
    midi_id: int    # Internal ID used by the hardware protocol if applicable
