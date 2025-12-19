import time
import threading
from typing import Callable, Optional
from AppKit import NSWorkspace
from ApplicationServices import AXUIElementCreateApplication, AXUIElementCopyAttributeValue, kAXFocusedWindowAttribute, kAXTitleAttribute

class FocusMonitor(threading.Thread):
    """
    Background thread that monitors the frontmost window title on macOS.
    Useful for detecting which plugin/VST is currently focused in a DAW.
    """
    def __init__(self, callback: Callable[[str, str], None], interval: float = 0.5):
        super().__init__(daemon=True)
        self.callback = callback
        self.interval = interval
        self._running = False
        self._last_app = None
        self._last_title = None

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        print("[FocusMonitor] Thread started.")
        while self._running:
            try:
                self._check_focus()
            except Exception as e:
                print(f"[FocusMonitor] Error in loop: {e}")
            time.sleep(self.interval)

    def _check_focus(self):
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        if not active_app:
            return

        app_name = active_app.localizedName()
        pid = active_app.processIdentifier()
        
        # Get focused window title via Accessibility API
        title = self._get_focused_window_title(pid)
        
        if app_name != self._last_app or title != self._last_title:
            self._last_app = app_name
            self._last_title = title
            print(f"[FocusMonitor] Changed: {app_name} -> {title}")
            try:
                self.callback(app_name, title or "")
            except Exception as e:
                print(f"[FocusMonitor] Error in callback: {e}")

    def _get_focused_window_title(self, pid: int) -> Optional[str]:
        app_ref = AXUIElementCreateApplication(pid)
        if not app_ref:
            return None
            
        err, window_ref = AXUIElementCopyAttributeValue(app_ref, kAXFocusedWindowAttribute, None)
        if err != 0:
            if err == -1719: # kAXErrorAPIDisabled
                print("[FocusMonitor] Warning: Accessibility API is disabled. Grant permissions in System Settings.")
            elif err == -1728: # kAXErrorNoValue
                pass # Normal if no window is focused
            else:
                pass # print(f"[FocusMonitor] AX Error {err} getting window")
            return None
            
        if not window_ref:
            return None
            
        err, title = AXUIElementCopyAttributeValue(window_ref, kAXTitleAttribute, None)
        if err != 0:
            return None
            
        return str(title)
