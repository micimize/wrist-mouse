from collections import deque
import json
from pathlib import Path
from touch_sdk import Watch

import time
import threading
from typing import Deque
from touch_sdk.watch import Watch, SensorFrame

from touch_sdk import Watch

PLAYBACK_DUMP_FILE = Path('./sensor_frames.json')

def serialize_sensor_frame(frame: SensorFrame):
    return {
        "acceleration": frame.acceleration,
        "gravity": frame.gravity,
        "angular_velocity": frame.angular_velocity,
        "orientation": frame.orientation,
        "timestamp": frame.timestamp,
    }

def load_sensor_frames(file: Path = PLAYBACK_DUMP_FILE) -> list[SensorFrame]:
    with file.open('r') as f:
        return [SensorFrame(**frame) for frame in json.load(f)]

class RecorderWatch(Watch):
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.frames: Deque[dict] = deque(maxlen=1_000_000)


    def on_sensors(self, sensors):
        self.frames.append(serialize_sensor_frame(sensors))


if __name__ == "__main__":
    watch = RecorderWatch()
    thread = threading.Thread(target=watch.start)
    thread.start()
    while not watch.frames:
        print("Waiting for sensor data...")
        time.sleep(1)
    print("Recording sensor data...")
    time.sleep(5)
    watch.stop()
    thread.join()
    with PLAYBACK_DUMP_FILE.open('w') as f:
        f.write(json.dumps(list(watch.frames)))
    print(f"Recorded {len(watch.frames)} frames to {PLAYBACK_DUMP_FILE}")