from talon import Module
from .wrist_mouse_tracker import TrackingMode, poll_tracking_mode, set_tracking_mode

mod = Module()

@mod.action_class
class TalonWristMouse:
    def toggle_wrist_mouse_tracking():
        "toggle_wrist_mouse_tracking"
        set_tracking_mode(None if poll_tracking_mode() else TrackingMode.PLANAR)
        print(f"{poll_tracking_mode()=}")

    def enable_wrist_mouse_tracking():
        "enable_wrist_mouse_tracking"
        set_tracking_mode(TrackingMode.PLANAR)
        print(f"enable {poll_tracking_mode()=}")

    def disable_wrist_mouse_tracking():
        "disable_wrist_mouse_tracking"
        set_tracking_mode(None)
        print(f"disable {poll_tracking_mode()=}")
