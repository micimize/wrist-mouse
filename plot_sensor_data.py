# To use this example, make sure to install extra dependencies:
# pip install matplotlib numpy

from threading import Thread
from queue import Queue, Empty
from collections import deque

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from touch_sdk import Watch
import logging
# Get helpful log info
logging.basicConfig(level=logging.INFO)


class MyWatch(Watch):
    def __init__(self, name=""):
        super().__init__(name)
        self.sensor_queue = Queue()

    def on_sensors(self, sensors):
        self.sensor_queue.put(sensors)


def anim(_, watch, ax, lines, gyro_data):

    while True:
        try:
            sensors = watch.sensor_queue.get(block=False)
        except Empty:
            break

        gyro_data.append(sensors.angular_velocity)

    while len(gyro_data) > 100:
        gyro_data.popleft()

    if len(gyro_data) == 0:
        return (ax,)

    arr = np.array(gyro_data).T

    ymax, ymin = np.max(arr), np.min(arr)zt
    range = max(abs(ymax), abs(ymin))
    ax.set_ylim(range, -range)

    x = np.arange(arr.shape[1])
    for line, data in zip(lines, arr):
        line.set_data(x, data)

    return lines


def animated_3d_plot():
    fig = plt.figure()
    ax = fig.add_subplot(111,projection = '3d')

    ax.set_xlim3d([-5.0, 5.0])
    ax.set_xlabel('x')


    ax.set_ylim3d([-5.0, 5.0])
    ax.set_ylabel('Y')


    ax.set_zlim3d([-5.0, 5.0])
    ax.set_zlabel('Z')
    ax.set_title("3D Plot over Time")
    pts = ax.scatter(0, 0, 0, s=30)
    return fig, ax, pts


if __name__ == "__main__":
    fig, ax, pts = animated_3d_plot()

    watch = MyWatch()
    thread = Thread(target=watch.start)
    thread.start()

    gyro_data = deque()

    _ = FuncAnimation(
        fig, anim, fargs=(watch, lambda point: , gyro_data), interval=1, blit=True,
        cache_frame_data=False
    )

    plt.show()
    watch.stop()
    thread.join()