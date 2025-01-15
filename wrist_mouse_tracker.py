# this is a separate script because:
# 1. the bluetooth dependency had some obscure error when running within talon
# 2. having a sidecar process will probably make testing and reuse easier
# pip install pyautogui
from enum import Enum
from pathlib import Path
from touch_sdk.watch import Watch, SensorFrame,Hand
try:
    import pyautogui
    import numpy as np
    from scipy.spatial.transform import Rotation
except ImportError:
    pass

class TrackingMode(Enum):
    ROTATIONAL = "ROTATIONAL"
    PLANAR = "PLANAR"

PLAYBACK_DUMP_FILE = Path('./positions.jsonl')

# TODO use as single source of truth for config, probably
TOGGLE_FILE = Path('~/.talon/wrist_mouse_toggle').expanduser()

def serialize_sensor_frame(frame: SensorFrame):
    return {
        "acceleration": frame.acceleration,
        "gravity": frame.gravity,
        "angular_velocity": frame.angular_velocity,
        "orientation": frame.orientation,
        "timestamp": frame.timestamp,
    }

_mode: TrackingMode | None = None
_last_poll_time = 0.0
def poll_tracking_mode() -> TrackingMode | None:
    global _mode, _last_poll_time
    if not TOGGLE_FILE.exists():
        return None
    last_file_update = TOGGLE_FILE.stat().st_mtime
    if last_file_update == _last_poll_time:
        return _mode
    with TOGGLE_FILE.open('r') as f:
        _last_poll_time = last_file_update
        text = f.read().strip()
        _mode = None if text == "" else TrackingMode(text)
    print(f"polling tracking mode changed to {_mode}")
    return _mode

def set_tracking_mode(mode: TrackingMode | None):
    TOGGLE_FILE.write_text(mode.value if mode else "")


class MouseWatch(Watch):
    base_speed: int = 40
    acceleration: float = 0

    @property
    def tracking_mode(self) -> TrackingMode | None:
        return poll_tracking_mode()

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

    def resolve_relative_delta(self, sensor_frame: SensorFrame) -> tuple[float, float, float]:
        rot = Rotation.from_quat([*sensor_frame.orientation])
        handedness_scale = -1 if self._hand == Hand.LEFT else 1
        x, y, z =  rot.apply(sensor_frame.angular_velocity, inverse=True)
        return x, y, z


   #pinch_state = False
   #def on_gesture_probability(self, prob):
   #    if prob >= 0.5 and not self.pinch_state:
   #        self.pinch_state = True
   #        pyautogui.mouseDown(_pause=False)
   #    elif prob < 0.5 and self.pinch_state:
   #        self.pinch_state = False
   #        pyautogui.mouseUp(_pause=False)
   #def on_sensors(self, sensor: SensorFrame):
   #    if not self.tracking_mode == TrackingMode.ROTATIONAL:
   #        return
   #    delta_x, delta_y, delta_z = self.resolve_relative_delta(sensor)
   #    if not self.is_tracking:
   #        return
   #    self.movement_thread.update_target(delta_x,delta_z)

    def on_arm_direction_change(self, delta_x: float, delta_y: float):
        if not self.tracking_mode == TrackingMode.PLANAR:
            return

        return pyautogui.moveRel(
            self.base_speed * delta_x, self.base_speed * delta_y,
            #scaled_x, scaled_y,
            duration=0.01,
            _pause=False
        )
        #print(f"{delta_x=}, {delta_y=}")
        # todo not really working right
        total_distance = abs(np.hypot(delta_x, delta_y))
        scaled = total_distance * self.base_speed + (total_distance * self.acceleration) ** 2
        scaled_x = delta_x * scaled / total_distance
        scaled_y = delta_y * scaled / total_distance


if __name__ == "__main__":
    watch = MouseWatch()
    watch.start()
