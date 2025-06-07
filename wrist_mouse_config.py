# this is a separate script because:
# 1. the bluetooth dependency had some obscure error when running within talon
# 2. having a sidecar process will probably make testing and reuse easier
# pip install pyautogui
from enum import Enum, StrEnum
import os
from pathlib import Path
import sys
from typing import Final, Tuple


WRIST_MOUSE_TOGGLE_STATE_PATH: Final = Path(os.environ.get(
    "WRIST_MOUSE_TRACKING_STATE_PATH",
    "~/.config/wrist_mouse/tracking_state"   
)).expanduser()



class TrackingMode(Enum):
    OFF = ""
    HAND_UP = "HAND_UP"
    # TODO: The idea here is to eventually have a mode for standing with hands prone to sides,
    # but I haven't gotten the math to be goodly yet
    # HAND_DOWN = "HAND_DOWN"

_mode: TrackingMode = TrackingMode.OFF
_last_poll_time = 0.0
def poll_tracking_mode() -> TrackingMode:
    global _mode, _last_poll_time
    if not WRIST_MOUSE_TOGGLE_STATE_PATH.exists():
        return TrackingMode.OFF

    last_file_update = WRIST_MOUSE_TOGGLE_STATE_PATH.stat().st_mtime
    if last_file_update == _last_poll_time:
        return _mode

    with WRIST_MOUSE_TOGGLE_STATE_PATH.open('r') as f:
        _last_poll_time = last_file_update
        text = f.read().strip()
        _mode = TrackingMode(text)

    print(f"newly polled tracking mode: {_mode}")
    return _mode

def set_tracking_mode(mode: TrackingMode):
    if not WRIST_MOUSE_TOGGLE_STATE_PATH.exists():
        WRIST_MOUSE_TOGGLE_STATE_PATH.parent.mkdir()
        WRIST_MOUSE_TOGGLE_STATE_PATH.touch(exist_ok=True)

    WRIST_MOUSE_TOGGLE_STATE_PATH.write_text(mode.value)
    print(f"set_tracking_mode to {poll_tracking_mode()}")

def toggle_wrist_mouse_tracking():
    "toggle_wrist_mouse_tracking"
    if poll_tracking_mode() == TrackingMode.OFF:
        set_tracking_mode(TrackingMode.HAND_UP)
    else:
        set_tracking_mode(TrackingMode.OFF)

if __name__ == "__main__":
    action = sys.argv[1]
    if action == "toggle":
        toggle_wrist_mouse_tracking()
    elif action == "set":
        assert len(sys.argv) > 2, "no value to set to mode"
        value = sys.argv[2]
        assert value in (TrackingMode.OFF, TrackingMode.HAND_UP)
        set_tracking_mode(value)