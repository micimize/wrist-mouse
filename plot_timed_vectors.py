# %%
import plotly.graph_objs as go
import numpy as np
from touch_sdk.watch import SensorFrame
from scipy.spatial.transform import Rotation

import json
from pathlib import Path

# right, left, up, down, forward, backward
PLAYBACK_DUMP_FILE = Path('../sensor_frames.json')
PLAYBACK_FORWARD = Path('../sensor_frames_moving_forward.json')
PLAYBACK_RIGHT = Path('../sensor_frames_moving_right.json')
PLAYBACK_UP = Path('../sensor_frames_moving_up.json')

def load_sensor_frames(file: Path = PLAYBACK_DUMP_FILE) -> list[SensorFrame]:
    with file.open('r') as f:
        return [SensorFrame(**frame, magnetic_field=None, magnetic_field_calibration=None) for frame in json.load(f)]

is_right_handed = True


# %%

def plot_3d_scatter_with_time_gradient(timestamped_coordinates: list[tuple[int, tuple[float, float, float]]]):
    """
    Creates a 3D scatter plot with Plotly where the color of the points represents the
    gradient of time differences from the earliest timestamp.

    Parameters:
    data (list): A list of tuples, where each tuple contains a timestamp (int)
                 and a coordinate triple (x, y, z).

    Returns:
    None
    """
    # Unpack timestamps and coordinates
    timestamps, coordinates = zip(*timestamped_coordinates)
    x, y, z = zip(*coordinates)

    # Calculate time differences relative to the earliest timestamp
    time_differences = np.array(timestamps) - min(timestamps)

    # Normalize time differences for color mapping
    colors = time_differences / max(time_differences)

    # Create the scatter plot
    scatter = go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode='markers',
        marker=dict(
            size=5,
            color=colors,  # Use normalized time differences as colors
            colorscale='Viridis',  # Color scale
            colorbar=dict(title='Time Difference'),
            opacity=0.8
        )
    )

    # Create layout
    layout = go.Layout(
        scene=dict(
            xaxis=dict(title='X', range=(-10, 10)),
            yaxis=dict(title='Y', range=(-10, 10)),
            zaxis=dict(title='Z', range=(-10, 10)),
            camera_up=dict(x=0, y=1, z=0),
            camera_projection=dict(type='orthographic'),
            aspectmode='cube'
        ),
        title='3D Scatter Plot with Time Gradient'
    )

    # Create and show the figure
    fig = go.Figure(data=[scatter], layout=layout)
    fig.show()

# %%
# Example usage
example_data = [
    (1609459200, (1, 2, 3)),
    (1609459260, (4, 5, 6)),
    (1609459320, (7, 8, 9)),
    (1609459380, (10, 11, 12))
]
# %%


class OffsetResolver:
    x: float = 0
    y: float = 0
    z: float = 0

    def resolve_relative_delta(self, sensor_frame: SensorFrame) -> tuple[float, float, float]:
        rot = Rotation.from_quat([*sensor_frame.orientation])
        handedness_scale = -1 if is_right_handed else 1
        delta_x, delta_y, delta_z =  rot.apply(sensor_frame.angular_velocity, inverse=False)
        self.x += delta_x
        self.y += delta_y
        self.z += delta_z
        return self.x, self.y, self.z

offset_resolver = OffsetResolver()

plot_3d_scatter_with_time_gradient([(frame.timestamp, offset_resolver.resolve_relative_delta(frame)) for frame in load_sensor_frames(PLAYBACK_FORWARD)])
# %%
"""
for some reason the forward frames are all on the x axis
"""