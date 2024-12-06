"""
enabling wristmouse will:
jump to a layer with quadrant hops and click buttons
record the current wrist position


"""
import time
import threading
import numpy as np
from talon import ctrl, ui
from talon.screen import Screen
from touch_sdk.watch import Watch, SensorFrame,Hand


screen: Screen = ui.screens()[0]

# Movement Thread for smoother cursor movement
class CursorMovementThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.current_x, self.current_y = ctrl.mouse_pos()
        self.target_x, self.target_y = self.current_x, self.current_y
        self.running = True
        self.active = False
        self.jitter_threshold = 0.003

    def smooth_move_step(self):
        distance = np.hypot(self.target_x - self.current_x, self.target_y - self.current_y)
        screen_diagonal = np.hypot(screen.width, screen.height)
        if distance / screen_diagonal <= self.jitter_threshold:
            return
        step = max(0.0001, distance / 12)  # Smoother movement
        if distance != 0:
            step_x = (self.target_x - self.current_x) / distance * step
            step_y = (self.target_y - self.current_y) / distance * step
            self.current_x += step_x
            self.current_y += step_y
            ctrl.mouse_move(self.current_x, self.current_y)#_pause=False)


    def run(self):
        while self.running:
            if self.active:
                self.smooth_move_step()
                time.sleep(0) # idk why this is here?
            else:
                time.sleep(0.1)

    def update_target(self, x, y):
        self.target_x, self.target_y = x, y

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def stop(self):
        self.running = False

# Initialize the movement and scroll threads
movement_thread = CursorMovementThread()
movement_thread.start()

:
class MouseWatch(Watch):
    scale = 30

    def resolve_relative_delta(self, sensor_frame: SensorFrame) -> tuple[float, float, float]:
        # copied from _on_arm_direction_change then mangeld 
        def normalize(vector):
            length = sum(x * x for x in vector) ** 0.5
            return [x / length for x in vector]

        grav = normalize(sensor_frame.gravity)

        # no idea whats going on here
        av_z = -sensor_frame.angular_velocity[0]  # forward = +
        av_y = -sensor_frame.angular_velocity[1]  # down = +
        av_x = -sensor_frame.angular_velocity[2]  # right = +

        handedness_scale = -1 if self._hand == Hand.LEFT else 1

        delta_x = av_x * grav[2] + av_y * grav[1]
        # cargoculting
        # really if the mvp is decent at all we want to map rotation from the elbow, not abolutes
        delta_z = av_z * grav[2] + av_z * grav[1]
        delta_y = handedness_scale * (av_y * grav[2] - av_x * grav[1])

        return delta_z, delta_y, delta_x


   #pinch_state = False
   #def on_gesture_probability(self, prob):
   #    if prob >= 0.5 and not self.pinch_state:
   #        self.pinch_state = True
   #        pyautogui.mouseDown(_pause=False)
   #    elif prob < 0.5 and self.pinch_state:
   #        self.pinch_state = False
   #        pyautogui.mouseUp(_pause=False)
    def on_sensors(self, sensor: SensorFrame):
        delta_z, delta_y, delta_x = self.resolve_relative_delta(sensor)
        movement_thread.update_target(delta_x,delta_z)



watch = MouseWatch()
watch.start()