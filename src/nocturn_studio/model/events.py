from dataclasses import dataclass
from enum import Enum, auto
import time

class ControlEventType(Enum):
    ENCODER_TURN = auto()
    BUTTON_PRESS = auto()
    BUTTON_RELEASE = auto()
    TOUCH_START = auto()
    TOUCH_END = auto()
    CROSSFADER_MOVE = auto()

@dataclass
class ControlEvent:
    source_id: str
    type: ControlEventType
    value: int # Delta for encoders, 0/1 for buttons, absolute for crossfader
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
