# this is a separate script because:
# 1. the bluetooth dependency had some obscure error when running within talon
# 2. having a sidecar process will probably make testing and reuse easier
# pip install pyautogui
from enum import Enum
from pathlib import Path
import time
import threading
from matplotlib import scale
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


# Movement Thread for smoother cursor movement
# TODO: I'm suspicious of inheriting from thread
class CursorMovementThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.current_x, self.current_y = pyautogui.position()
        self.target_x, self.target_y = self.current_x, self.current_y
        self.running = True
        self.active = False
        self.jitter_threshold = 0.003

    def smooth_move_step(self):
        distance = np.hypot(self.target_x - self.current_x, self.target_y - self.current_y)
        screen_diagonal = np.hypot(*pyautogui.size())
        if distance / screen_diagonal <= self.jitter_threshold:
            return
        step = max(0.0001, distance / 12)  # Smoother movement
        if distance != 0:
        #if distance > 0.0001:
            step_x = (self.target_x - self.current_x) / distance * step
            step_y = (self.target_y - self.current_y) / distance * step
            self.current_x += step_x
            self.current_y += step_y
            print(f"mouse_move({self.current_x=}, {self.current_y=})")
            pyautogui.moveTo(self.current_x, self.current_y,_pause=False)


    def run(self):
        while self.running:
            if self.active:
                self.smooth_move_step()
                time.sleep(0) # idk why this is here?
            else:
                time.sleep(0.1)

    def update_target(self, x, y):
        print(f"{x=}, {y=}")
        self.target_x, self.target_y = x, y

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def stop(self):
        self.running = False

class MouseWatch(Watch):
    base_speed: int = 40
    acceleration: float = 0
    movement_thread: CursorMovementThread

    def __init__(self, name_filter: str | None =None):
        super().__init__(name_filter=name_filter)
        self.movement_thread = CursorMovementThread()
        # Initialize the movement and scroll threads
        self.movement_thread = CursorMovementThread()
        self.movement_thread.start()
    
    @property
    def tracking_mode(self) -> TrackingMode | None:
        return poll_tracking_mode()

    def start(self):
        # For now we have the movement thread always going,
        # but may want to account for other mouse takeover actions or something
        #self.movement_thread.active = True
        #self.movement_thread.start()
        super().start()

    def stop(self):
        self.movement_thread.stop()
        return super().stop()

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
        print(f"{delta_x=}, {delta_y=}")
        total_distance = abs(np.hypot(delta_x, delta_y))
        scaled = total_distance * self.base_speed + (total_distance * self.acceleration) ** 2
        scaled_x = delta_x * scaled / total_distance
        scaled_y = delta_y * scaled / total_distance
        pyautogui.moveRel(
            scaled_x, scaled_y,
            duration=0.01,
            _pause=False
        )


if __name__ == "__main__":
    watch = MouseWatch()
    watch.start()
