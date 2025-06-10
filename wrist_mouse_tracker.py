# pip install pyautogui touch_sdk
from asyncio import run
from dataclasses import dataclass
from functools import cached_property
from typing import Final
import pyautogui
from touch_sdk.watch import Watch
from wrist_mouse.wrist_mouse_config import TrackingMode, poll_tracking_mode, load_acceleration_config, AccelerationConfig
from time import sleep
from datetime import datetime
import math

@dataclass
class _BatteryCheckin:
    checkin_time: datetime
    remaining_battery: float

    def is_time_for_new_checkin(self, checkin_interval_in_seconds: int) -> bool:
        if self.remaining_battery < 0:
            return True
        elapsed_seconds = (datetime.now() -  self.checkin_time).total_seconds()
        return elapsed_seconds > checkin_interval_in_seconds

def report_battery_info(previous: _BatteryCheckin, latest: _BatteryCheckin) -> None:
    elapsed_seconds = (latest.checkin_time - previous.checkin_time).total_seconds()
    elapsed_minutes = int(elapsed_seconds / 60)
    drained = latest.remaining_battery - previous.remaining_battery
    if previous.remaining_battery == -1:
        drained = 100 - latest.remaining_battery
    current_battery = latest.remaining_battery
    time = f"{latest.checkin_time}".rsplit(":", 1)[0]
    print(f"{time}: {current_battery=}%, {drained=}% over {elapsed_minutes}min")


class MouseWatch(Watch):
    def __init__(self):
        super().__init__()
        self.config = load_acceleration_config()
        self.battery_checkin_interval_in_seconds: int = 600
        self.last_battery_checkin: _BatteryCheckin = _BatteryCheckin(datetime.now(), -1)
        self.is_update_info_requested: bool = False

    def is_time_to_checkin_on_battery(self) -> bool:
        if self.is_update_info_requested:
            return False
        if self.battery_percentage == -1:
            return True
        return self.last_battery_checkin.is_time_for_new_checkin(self.battery_checkin_interval_in_seconds)

    def _checkin_and_report_on_battery(self) -> None:
        new_checkin = _BatteryCheckin(datetime.now(), self.battery_percentage)
        report_battery_info(self.last_battery_checkin, new_checkin)
        self.last_battery_checkin = new_checkin
    
    def on_info_update(self):
        self._checkin_and_report_on_battery()
        self.is_update_info_requested = False

    # battery won't update unless we force the re-request, which happens in _fetch_info
    def force_update_info(self) -> None:
        if self.is_update_info_requested:
            return
        self.is_update_info_requested = True
        assert self._event_loop is not None
        self._event_loop.create_task(self._fetch_info(self._client))
    
    def _apply_acceleration(self, delta_x: float, delta_y: float) -> tuple[float, float]:
        """Apply macOS-style acceleration to movement deltas."""
        if not self.config.enabled:
            return delta_x, delta_y
        
        # Calculate the magnitude of movement
        magnitude = math.sqrt(delta_x * delta_x + delta_y * delta_y)
        
        if magnitude < self.config.threshold:
            # No acceleration for very small movements
            return delta_x, delta_y
        
        # Calculate acceleration multiplier using power curve
        # Normalized magnitude (0-1) raised to the power curve
        normalized_magnitude = min(magnitude, 1.0)  # Cap at 1.0 for stability
        acceleration_factor = math.pow(normalized_magnitude, self.config.curve)
        
        # Apply max acceleration limit
        acceleration_factor = min(acceleration_factor * self.config.max_acceleration, self.config.max_acceleration)
        
        # Apply acceleration to both axes proportionally
        accelerated_x = delta_x * acceleration_factor
        accelerated_y = delta_y * acceleration_factor
        
        return accelerated_x, accelerated_y
    
    def on_arm_direction_change(self, delta_x: float, delta_y: float):
        if self.is_time_to_checkin_on_battery():
            self.force_update_info()
        if not poll_tracking_mode() == TrackingMode.HAND_UP:
            return
        
        # Apply acceleration to the raw deltas
        accelerated_x, accelerated_y = self._apply_acceleration(delta_x, delta_y)
        
        # Scale by base speed
        scaled_x = self.config.base_speed * accelerated_x
        scaled_y = self.config.base_speed * accelerated_y
        
        return pyautogui.moveRel(scaled_x, scaled_y, duration=0.01, _pause=False)
        
if __name__ == "__main__":
    watch = MouseWatch()
    watch.start()
   

"""SCRATCHPAD/NOTES from earlier efforts

import numpy as np
from scipy.spatial.transform import Rotation
from touch_sdk.watch import SensorFrame, Hand

A potential option for controlling the toggle from the main script.
Probably better to just outsource to whatever hotkey or voice control system the user might use elsewhere due to permissions troubles
    from pynput import keyboard
def listen_for_tracking_key_toggles_in_background(enable_tracking: keyboard.KeyCode, disable_tracking: keyboard.KeyCode) -> keyboard.Listener:
    def on_press(key: keyboard.Key | keyboard.KeyCode | None):
        print(f"{key=}")
        if key == enable_tracking:
            set_tracking_mode(TrackingMode.PLANAR)
            print(f"enable {poll_tracking_mode()=}")
        if key == disable_tracking:
            set_tracking_mode(None)
            print(f"disable {poll_tracking_mode()=}")
            
    listener = keyboard.Listener(on_press=on_press)
    assert listener.IS_TRUSTED, f"need to run as root {listener.IS_TRUSTED=}"
    listener.start()
    print(f"toggle listener started for {enable_tracking=} and {disable_tracking=}")
    return listener


    various ill-fated efforts to get hands-down tracking to work

    def resolve_relative_delta(self, sensor_frame: SensorFrame) -> tuple[float, float, float]:
        # def normalize(vector):
        #     length = sum(x * x for x in vector) ** 0.5
        #     return [x / length for x in vector]

        # grav = normalize(sensor_frame.gravity)
        rot = Rotation.from_quat([*sensor_frame.orientation])
        handedness_scale = -1 if self._hand == Hand.LEFT else 1
        rot = Rotation.from_quat([*sensor_frame.orientation])
        z, y, x =  rot.apply(sensor_frame.angular_velocity, inverse=True)
        return x, y, z


    #def resolve_relative_delta(self, sensor_frame: SensorFrame) -> tuple[float, float, float]:
    #    # copied from _on_arm_direction_change then mangeld 
    #    def normalize(vector):
    #        length = sum(x * x for x in vector) ** 0.5
    #        return [x / length for x in vector]

    #    grav = normalize(sensor_frame.gravity)

    #    av_x = -sensor_frame.angular_velocity[2]  # right = +
    #    av_y = -sensor_frame.angular_velocity[1]  # down = +
    #    av_z = sensor_frame.angular_velocity[0]  # forward = +

    #    handedness_scale = -1 if self._hand == Hand.LEFT else 1

    #    delta_x = av_x * grav[2] + av_y * grav[1]
    #    delta_y = handedness_scale * (av_y * grav[2] - av_x * grav[1])
    #    delta_z = handedness_scale * (av_y * grav[2] - av_x * grav[1])

    #    return delta_x, delta_y, delta_z

    #pinch_state = False
    #def on_gesture_probability(self, prob):
    #    if prob >= 0.5 and not self.pinch_state:
    #        self.pinch_state = True
    #        pyautogui.mouseDown(_pause=False)
    #    elif prob < 0.5 and self.pinch_state:
    #        self.pinch_state = False
    #        pyautogui.mouseUp(_pause=False)
        # def on_sensors(self, sensor: SensorFrame):
        #     tracking_mode=poll_tracking_mode()
        #     if not tracking_mode:
        #         return
        #     delta_x, delta_y, delta_z = self.resolve_relative_delta(sensor)
        #     if tracking_mode == TrackingMode.HORIZONTAL:
        #         delta_y=delta_z
        #     return pyautogui.moveRel(
        #         self.base_speed * delta_x, self.base_speed * delta_y,
        #         #scaled_x, scaled_y,
        #         duration=0.01,
        #         _pause=False
        #     )
    """
            