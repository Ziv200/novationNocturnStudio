from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional

class ChannelFunction(Enum):
    # EQ
    EQ_LOW_FREQ = "EQ Low Freq"
    EQ_LOW_GAIN = "EQ Low Gain"
    EQ_LOW_Q = "EQ Low Q"
    EQ_LOMID_FREQ = "EQ LoMid Freq"
    EQ_LOMID_GAIN = "EQ LoMid Gain"
    EQ_LOMID_Q = "EQ LoMid Q"
    EQ_HIMID_FREQ = "EQ HiMid Freq"
    EQ_HIMID_GAIN = "EQ HiMid Gain"
    EQ_HIMID_Q = "EQ HiMid Q"
    EQ_HIGH_FREQ = "EQ High Freq"
    EQ_HIGH_GAIN = "EQ High Gain"
    EQ_HIGH_Q = "EQ High Q"
    
    # Filters
    FILTER_HP = "High Pass"
    FILTER_LP = "Low Pass"
    
    # Dynamics
    COMP_THRESHOLD = "Comp Thresh"
    COMP_RATIO = "Comp Ratio"
    COMP_ATTACK = "Comp Attack"
    COMP_RELEASE = "Comp Release"
    COMP_GAIN = "Comp Gain"
    GATE_THRESHOLD = "Gate Thresh"
    GATE_RANGE = "Gate Range"
    GATE_RELEASE = "Gate Release"
    
    # Master
    INPUT_GAIN = "Input Gain"
    OUTPUT_GAIN = "Output Gain"
    PHASE_REVERSE = "Phase"
    BYPASS = "Bypass"

@dataclass
class FunctionalMapping:
    function: ChannelFunction
    cc: int
    note: Optional[int] = None
    relative: bool = True
