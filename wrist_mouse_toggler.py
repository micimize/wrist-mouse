from talon import Module
from .wrist_mouse_config import TrackingMode, poll_tracking_mode, set_tracking_mode, toggle_wrist_mouse_tracking

mod = Module()

@mod.action_class
class TalonWristMouse:
    def toggle_wrist_mouse_tracking():
        "toggle_wrist_mouse_tracking"
        toggle_wrist_mouse_tracking()
        print(f"{poll_tracking_mode()=}")

    def enable_wrist_mouse_tracking():
        "enable_wrist_mouse_tracking"
        set_tracking_mode(TrackingMode.HAND_UP)
        print(f"enable {poll_tracking_mode()=}")

    def disable_wrist_mouse_tracking():
        "disable_wrist_mouse_tracking"
        set_tracking_mode(TrackingMode.OFF)
        print(f"disable {poll_tracking_mode()=}")
