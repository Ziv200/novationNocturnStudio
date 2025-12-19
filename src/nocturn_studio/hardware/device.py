import threading
import time
import usb.core
import usb.util
import sys
from typing import Callable, List, Optional
from ..model.events import ControlEvent, ControlEventType

class DeviceInterface:
    def __init__(self):
        self.connected = False
        self.callbacks: List[Callable[[ControlEvent], None]] = []

    def connect(self) -> bool:
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def add_event_listener(self, callback: Callable[[ControlEvent], None]):
        self.callbacks.append(callback)

    def _emit(self, event: ControlEvent):
        for cb in self.callbacks:
            cb(event)

    def set_led(self, control_id: str, value: int):
        pass

class RealNocturnDevice(DeviceInterface):
    VID = 0x1235
    PID = 0x000A

    def __init__(self):
        super().__init__()
        self.dev = None
        self._running = False
        self._thread = None
        self._ep_in = None
        self._ep_out = None

    def connect(self) -> bool:
        try:
            print(f"[RealDevice] Searching for VID:0x{self.VID:04X} PID:0x{self.PID:04X}...")
            self.dev = usb.core.find(idVendor=self.VID, idProduct=self.PID)
            
            if self.dev is None:
                print("[RealDevice] Device not found on USB bus.")
                return False

            # On macOS, we usually don't need (or can't) detach kernel drivers for vendor-spec
            if sys.platform != "darwin":
                try:
                    if self.dev.is_kernel_driver_active(0):
                        self.dev.detach_kernel_driver(0)
                except Exception as e:
                    print(f"[RealDevice] Warning: Could not detach kernel driver: {e}")

            self.dev.set_configuration()
            
            # Find endpoints
            cfg = self.dev.get_active_configuration()
            intf = cfg[(0,0)]

            self._ep_in = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)

            self._ep_out = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)

            if not self._ep_in or not self._ep_out:
                print("[RealDevice] Could not find endpoints.")
                return False

            # Init command (from protocol)
            self._write_raw(0, 0, 176)
            self._init_leds()
            
            self.connected = True
            self._running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            print("[RealDevice] Connected to Novation Nocturn via PyUSB.")
            return True
        except Exception as e:
            print(f"[RealDevice] Connection failed: {e}")
            return False

    def disconnect(self):
        self._running = False
        self.connected = False

    def _read_loop(self):
        while self._running:
            try:
                # Read 8 bytes
                data = self.dev.read(self._ep_in.bEndpointAddress, 8, timeout=10)
                if data and len(data) >= 3:
                    self._parse_report(data)
            except usb.core.USBError as e:
                if e.errno == 60 or "timeout" in str(e).lower():
                    pass # Timeout is fine
                else:
                    print(f"[RealDevice] Read error: {e}")
                    break
            except Exception as e:
                print(f"[RealDevice] Unexpected error: {e}")
                break
            time.sleep(0.001)

    def _parse_report(self, data):
        # cc = data[1], val = data[2]
        cc = data[1]
        val = data[2]

        event_type = None
        source_id = None
        event_val = val

        # Encoders 1-8
        if 64 <= cc <= 71:
            source_id = f"encoder_{cc - 63}"
            event_type = ControlEventType.ENCODER_TURN
            event_val = self._decode_delta(val)
        # Speed Dial
        elif cc == 74:
            source_id = "speed_dial"
            event_type = ControlEventType.ENCODER_TURN
            event_val = self._decode_delta(val)
        # Crossfader
        elif cc == 72:
            source_id = "crossfader"
            event_type = ControlEventType.CROSSFADER_MOVE
        # Buttons 1-16
        elif 112 <= cc <= 127:
            source_id = f"button_{cc - 111}"
            event_type = ControlEventType.BUTTON_PRESS if val > 0 else ControlEventType.BUTTON_RELEASE
        # Speed Dial Button
        elif cc == 81:
            source_id = "button_speed_dial"
            event_type = ControlEventType.BUTTON_PRESS if val > 0 else ControlEventType.BUTTON_RELEASE

        if source_id and event_type:
            self._emit(ControlEvent(source_id, event_type, event_val))

    def _decode_delta(self, val):
        if val < 64:
            return val + 1
        else:
            return val - 128

    def _write_raw(self, *data):
        if self.dev and self._ep_out:
            try:
                self.dev.write(self._ep_out.bEndpointAddress, data, timeout=10)
            except Exception as e:
                print(f"[RealDevice] Write error: {e}")

    def _init_leds(self):
        # Style 1: Standard Bar (0=Empty, 127=Full)
        # 72-79 for encoders 1-8, 81 for speed dial ring
        for addr in range(72, 80):
            self._write_raw(addr, 1)
        self._write_raw(81, 1)

    def set_led(self, source_id: str, value: int):
        addr = self._get_led_address(source_id)
        if addr is not None:
            # Direct mapping as per user: 0=Off, 127=Full
            self._write_raw(addr, value)

    def _get_led_address(self, source_id: str) -> Optional[int]:
        if source_id.startswith("encoder_"):
            idx = int(source_id.split("_")[1])
            return 63 + idx 
        if source_id == "speed_dial": return 80
        if source_id.startswith("button_"):
            idx = int(source_id.split("_")[1])
            return 111 + idx 
        if source_id == "button_speed_dial": 
            # Speed dial button LED is often the same address as its style or button? 
            # In some protocols it's 81 or 128. Let's try 128 as a fallback or skip.
            return None 
        return None

class MockNocturnDevice(DeviceInterface):
    def connect(self) -> bool:
        print("[MockDevice] Connected.")
        self.connected = True
        return True

    def disconnect(self):
        print("[MockDevice] Disconnected.")
        self.connected = False

    def simulate_turn(self, encoder_id: str, delta: int):
        """Call this from test code to simulate a knob turn"""
        if not self.connected: 
            return
        evt = ControlEvent(source_id=encoder_id, type=ControlEventType.ENCODER_TURN, value=delta)
        # print(f"[MockDevice] Simulating turn: {encoder_id} delta={delta}")
        self._emit(evt)

    def simulate_press(self, button_id: str):
        if not self.connected: return
        evt = ControlEvent(source_id=button_id, type=ControlEventType.BUTTON_PRESS, value=127)
        self._emit(evt)
