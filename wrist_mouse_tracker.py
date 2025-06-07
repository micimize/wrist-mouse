# pip install pyautogui touch_sdk
import pyautogui
from touch_sdk.watch import Watch
from wrist_mouse.wrist_mouse_config import TrackingMode, poll_tracking_mode

class MouseWatch(Watch):
    base_speed: int = 40
    acceleration: float = 0
    
    def on_arm_direction_change(self, delta_x: float, delta_y: float):
        if not poll_tracking_mode() == TrackingMode.HAND_UP:
            return
        scaled_x = self.base_speed * delta_x
        scaled_y = self.base_speed * delta_y
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
            