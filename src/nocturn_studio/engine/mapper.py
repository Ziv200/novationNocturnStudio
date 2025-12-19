import time
from typing import Dict, Optional, Callable, Any
from ..utils.persistence import PersistenceManager
from ..model.events import ControlEvent, ControlEventType
from ..model.mapping import Mapping, MappingMode, MappingTarget, TargetType
from ..model.functional import ChannelFunction
from ..daw.midi import MidiOutputInterface, MidiMessage

class MappingEngine:
    def __init__(self, midi_out: MidiOutputInterface, 
                 feedback_callback: Optional[Callable[[str, int], None]] = None,
                 status_callback: Optional[Callable[[str, str, bool], None]] = None):
        self.midi_out = midi_out
        self.feedback_callback = feedback_callback
        self.status_callback = status_callback
        self.persistence = PersistenceManager()
        self.mappings: Dict[str, Mapping] = {}
        # Store current values for controls (virtual state)
        # keyed by source_id -> int (0-127 usually)
        self.values: Dict[str, int] = {} 
        # New: Tracking values per function to allow seamless Shift/Page swaps
        self.functional_values: Dict[ChannelFunction, int] = {}
        # Pre-fill with defaults (center)
        for func in ChannelFunction:
            self.functional_values[func] = 64
        self.current_profile = "Global"
        
        # New: State-Aware Functional Engine
        self.shift_active = False
        self.current_page = 0
        self.current_mode = "EQ" # "EQ" or "DYNAMICS"
        
        # Mode -> Page -> Control ID -> {base: Function, shift: Function}
        self.functional_layouts: Dict[str, Dict[int, Dict[str, Dict[str, ChannelFunction]]]] = {
            "EQ": {
                0: { # Page 1
                    "encoder_1": {"base": ChannelFunction.EQ_LOW_GAIN},
                    "encoder_2": {"base": ChannelFunction.EQ_LOW_FREQ, "shift": ChannelFunction.EQ_LOW_Q},
                    "encoder_3": {"base": ChannelFunction.EQ_LOMID_GAIN},
                    "encoder_4": {"base": ChannelFunction.EQ_LOMID_FREQ, "shift": ChannelFunction.EQ_LOMID_Q},
                    "encoder_7": {"base": ChannelFunction.EQ_HIMID_GAIN},
                    "encoder_6": {"base": ChannelFunction.EQ_HIMID_FREQ, "shift": ChannelFunction.EQ_HIMID_Q},
                    "speed_dial": {"base": ChannelFunction.EQ_HIGH_GAIN},
                    "encoder_8": {"base": ChannelFunction.EQ_HIGH_FREQ, "shift": ChannelFunction.EQ_HIGH_Q},
                }
            },
            "DYNAMICS": {
                0: { # Page 1 (Placeholders)
                    "encoder_1": {"base": ChannelFunction.COMP_THRESHOLD},
                    "encoder_2": {"base": ChannelFunction.COMP_RATIO},
                    "encoder_3": {"base": ChannelFunction.COMP_ATTACK},
                    "encoder_4": {"base": ChannelFunction.COMP_RELEASE},
                    "encoder_5": {"base": ChannelFunction.COMP_GAIN},
                    "encoder_6": {"base": ChannelFunction.GATE_THRESHOLD},
                    "encoder_7": {"base": ChannelFunction.GATE_RANGE},
                    "encoder_8": {"base": ChannelFunction.GATE_RELEASE},
                }
            }
        }
        
        # Crossfader is ALWAYS Output Gain in all modes
        self.fixed_functional_layout = {
            "crossfader": {"base": ChannelFunction.OUTPUT_GAIN}
        }
        
        # Plugin Parameter Map: ChannelFunction -> Target Mapping
        self.plugin_parameters: Dict[ChannelFunction, Mapping] = {}
        
        # MIDI Learn State
        self.learn_mode = False
        self.last_touched_id: Optional[str] = None
        self.global_mappings = {}
        
        # Initial LED state
        # (Will be called properly when device connects, but good for local state)

    def load_mappings(self, mappings: Dict[str, Mapping], profile_name: str = "Global"):
        self.mappings = mappings
        self.current_profile = profile_name
        
        if profile_name == "Global":
            self.global_mappings = mappings
        
        # Initialize values to 0 if unknown
        for k in mappings:
            if k not in self.values:
                self.values[k] = 0

    def switch_profile(self, profile_name: str):
        if profile_name == self.current_profile:
            return
            
        # Try to load from persistence
        new_mappings = self.persistence.load_preset(profile_name)
        if new_mappings:
            print(f"[Engine] Switched to profile: {profile_name}")
            # In Channel Strip mode, we interpret presets as ChannelFunction -> MIDI
            if self._is_functional_profile(new_mappings):
                self.plugin_parameters = self._convert_to_functional(new_mappings)
                # We still want the UI to see the mappings
                gui_mappings = self._generate_gui_mappings_from_functional()
                self.load_mappings(gui_mappings, profile_name)
            else:
                self.load_mappings(new_mappings, profile_name)
        else:
            # Generate a "Smart Default" if it's a real focus (not global/none)
            if profile_name and profile_name not in ["Global", "None", ""]:
                print(f"[Engine] Generating Smart Default profile for: {profile_name}")
                default_mappings = self._generate_default_mappings()
                self.load_mappings(default_mappings, profile_name)
                # Auto-save so it persists as the base for this plugin
                self.save_current_profile()
            else:
                # Fallback to Global
                if self.current_profile != "Global":
                    print(f"[Engine] Reverting to Global.")
                    self.load_mappings(self.global_mappings, "Global")
        
        # Refresh UI/Hardware with current values
        self._sync_navigation_leds()
        for source_id, val in self.values.items():
            if self.feedback_callback:
                self.feedback_callback(source_id, val)
            time.sleep(0.001) # Small delay to prevent USB flood

    def handle_event(self, event: ControlEvent):
        # 1. Intercept Navigation / Modifiers
        is_press = (event.type == ControlEventType.BUTTON_PRESS)
        
        if event.source_id == "button_16": # Shift
            self.shift_active = is_press
            if self.feedback_callback:
                self.feedback_callback("button_16", 127 if is_press else 0)
            self._refresh_functional_mappings()
            return

        if event.source_id == "button_11": # Page Down
            if is_press:
                if self.current_page > 0:
                    self.current_page -= 1
                elif self.current_mode == "DYNAMICS":
                    self.current_mode = "EQ"
                    # Go to last page of EQ
                    eq_pages = sorted(self.functional_layouts["EQ"].keys())
                    self.current_page = eq_pages[-1] if eq_pages else 0
                self._sync_navigation_leds()
                self._refresh_functional_mappings()
            if self.feedback_callback:
                self.feedback_callback("button_11", 127 if is_press else 0)
            return
            
        if event.source_id == "button_12": # Page Up
            if is_press:
                mode_layout = self.functional_layouts.get(self.current_mode, {})
                if (self.current_page + 1) in mode_layout:
                    self.current_page += 1
                elif self.current_mode == "EQ":
                    self.current_mode = "DYNAMICS"
                    self.current_page = 0
                self._sync_navigation_leds()
                self._refresh_functional_mappings()
            if self.feedback_callback:
                self.feedback_callback("button_12", 127 if is_press else 0)
            return

        if event.source_id in ["button_13", "button_14"]:
            if is_press:
                self.current_mode = "EQ" if event.source_id == "button_13" else "DYNAMICS"
                print(f"[Console] Mode Switched: >>> {self.current_mode} MODULE <<<")
                self.current_page = 0
                self._sync_navigation_leds()
                self._refresh_functional_mappings()
            return # Intercept both press and release

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
            
            # Save to functional registry if mapped
            func = self._get_function_for_hw_id(event.source_id)
            if func:
                self.functional_values[func] = new_val
            
            label = self.get_label_for_control(event.source_id) or event.source_id
            print(f"[Console] {label:20} | Value: {new_val:3} [{'#' * (new_val // 10):13}]")
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

    def _generate_default_mappings(self) -> Dict[str, Mapping]:
        """Creates a standard layout for new/unknown plugins."""
        m = {}
        # Encoders 1-8 -> CC 10-17
        for i in range(1, 9):
            m[f"encoder_{i}"] = Mapping(
                source_id=f"Knob {i}",
                target=MappingTarget(type=TargetType.MIDI_CC, channel=0, identifier=9+i),
                mode=MappingMode.RELATIVE_TWOS_COMP
            )
        # Buttons 1-16 -> Notes 40-55
        for i in range(1, 17):
            m[f"button_{i}"] = Mapping(
                source_id=f"Button {i}",
                target=MappingTarget(type=TargetType.MIDI_NOTE, channel=0, identifier=39+i),
                mode=MappingMode.SWITCH_TOGGLE
            )
        # Speed Dial -> CC 18
        m["speed_dial"] = Mapping(
            source_id="Speed Dial",
            target=MappingTarget(type=TargetType.MIDI_CC, channel=0, identifier=18),
            mode=MappingMode.RELATIVE_TWOS_COMP
        )
        # Crossfader -> CC 19
        m["crossfader"] = Mapping(
            source_id="Crossfader",
            target=MappingTarget(type=TargetType.MIDI_CC, channel=0, identifier=19),
            mode=MappingMode.ABSOLUTE
        )
        return m

    def _is_functional_profile(self, new_mappings: Dict[str, Any]) -> bool:
        """Checks if any keys in the mappings dict are ChannelFunction names."""
        valid_funcs = [f.name for f in ChannelFunction]
        return any(k in valid_funcs for k in new_mappings.keys())

    def _convert_to_functional(self, new_mappings: Dict[str, Any]) -> Dict[ChannelFunction, Mapping]:
        """Converts name-based keys from persistence to Enum-based keys."""
        res = {}
        for func in ChannelFunction:
            if func.name in new_mappings:
                res[func] = new_mappings[func.name]
        return res

    def _sync_navigation_leds(self):
        """Ensures mode buttons (13-15) show latched/exclusive LEDs."""
        # 1. Calculate states
        btn_states = {
            "button_13": 127 if self.current_mode == "EQ" else 0,
            "button_14": 127 if self.current_mode == "DYNAMICS" else 0,
            # Button 15 placeholder (latched but maybe not assigned to a mode yet)
            "button_15": 0 
        }
        
        # 2. Update internal values so bulk refreshes don't overwrite
        self.values.update(btn_states)
        
        # 3. Push to hardware/UI (Using 127 for latched buttons as they seem to work well)
        if self.feedback_callback:
            for sid, val in btn_states.items():
                self.feedback_callback(sid, val)

    def _refresh_functional_mappings(self):
        """Updates active mappings and UI labels based on Shift/Page/Mode."""
        gui_mappings = self._generate_gui_mappings_from_functional()
        self.load_mappings(gui_mappings, self.current_profile)
        
        # 1. Update Hardware/UI values from the functional registry
        for hw_id in gui_mappings.keys():
            func = self._get_function_for_hw_id(hw_id)
            if func and func in self.functional_values:
                val = self.functional_values[func]
                self.values[hw_id] = val
                if self.feedback_callback:
                    self.feedback_callback(hw_id, val)

        # 2. Notify UI about current state (Page/Mode)
        status_msg = f"{self.current_mode} - Page {self.current_page + 1}"
        if self.shift_active: status_msg += " (SHIFT)"
        
        print(f"[Console] {status_msg}")
        
        if self.status_callback:
            self.status_callback(self.current_mode, str(self.current_page + 1), self.shift_active)

    def _generate_gui_mappings_from_functional(self) -> Dict[str, Mapping]:
        """Generates a hardware-indexed mapping dict for the UI/Main loop."""
        gui_map = {}
        gui_map.update(self.global_mappings)
        
        # 1. Get current mode's layout
        mode_layout = self.functional_layouts.get(self.current_mode, {})
        # 2. Get current page (clamp to available pages)
        available_pages = sorted(mode_layout.keys())
        active_page = self.current_page if self.current_page in available_pages else (available_pages[-1] if available_pages else 0)
        
        page_layout = mode_layout.get(active_page, {})
        
        # Combine page-specific and fixed layouts
        active_layout = {}
        active_layout.update(self.fixed_functional_layout)
        active_layout.update(page_layout)
        
        for hw_id, func_data in active_layout.items():
            # Resolve function based on state
            func = func_data.get("shift") if self.shift_active and "shift" in func_data else func_data.get("base")
            
            # Use the functional name as the label ALWAYS
            label = func.value if isinstance(func, ChannelFunction) else hw_id
            
            if func in self.plugin_parameters:
                base_map = self.plugin_parameters[func]
                gui_map[hw_id] = Mapping(
                    source_id=label,
                    target=base_map.target,
                    mode=base_map.mode,
                    min_val=base_map.min_val,
                    max_val=base_map.max_val
                )
            else:
                # Still set the label so the UI knows the "Job"
                # Use a dummy mapping or just update the source_id of the global mapping
                if hw_id in gui_map:
                    gui_map[hw_id].source_id = label
                else:
                    gui_map[hw_id] = Mapping(source_id=label, target=MappingTarget(TargetType.MIDI_CC, identifier=0))
                    
            # Ensure UI shows the label immediately
            if self.feedback_callback:
                self.feedback_callback(hw_id, self.values.get(hw_id, 0))
                    
        return gui_map

    def _get_function_for_hw_id(self, hw_id: str) -> Optional[ChannelFunction]:
        """Resolves which function is currently active on a piece of hardware."""
        mode_layout = self.functional_layouts.get(self.current_mode, {})
        page_layout = mode_layout.get(self.current_page, {})
        
        # 1. Check current page
        func_data = page_layout.get(hw_id)
        
        # 2. Fallback to fixed layout if not in page (e.g. Crossfader)
        if not func_data:
             func_data = self.fixed_functional_layout.get(hw_id)

        if not func_data:
            return None
            
        return func_data.get("shift") if self.shift_active and "shift" in func_data else func_data.get("base")

    def get_label_for_control(self, control_id: str) -> Optional[str]:
        """Returns the functional name (e.g. 'EQ High Freq') or the source_id."""
        func = self._get_function_for_hw_id(control_id)
        if func:
            return func.value
            
        if control_id in self.mappings:
            return self.mappings[control_id].source_id
        return None
