import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

SHAPE_LIST = ['square','squareCCW','triangle','diagonal1','diagonal2','diagonal3','diagonal4',
                'diagonal1_2','diagonal1_3','diagonal1_4','diagonal1_5',
                'diagonal2_2','diagonal2_3','diagonal2_4','diagonal2_5',
                'diagonal3_2','diagonal3_3','diagonal3_4','diagonal3_5',
                'diagonal4_2','diagonal4_3','diagonal4_4','diagonal4_5',
                'toEast_1','toEast_2','toEast_3','toNorth_1','toNorth_2','toNorth_3',
                'toWest_1','toWest_2','toWest_3','toSouth_1','toSouth_2','toSouth_3',
                'circle','circleCCW']

def generate_path(L: float=0.03, hz: int=50, velocity: float=0.04, shape='square') -> np.ndarray:
    """
    Generate a path with dynamic time steps and rest time at corners.

    Parameters:
        hz (int): Command frequency in Hz (e.g., 10).
        velocity (float): Robot velocity in meters per second (e.g., 0.06 m/s).
        shape (str): Shape of the path ('square', 'triangle', 'line').

    Returns:
        np.ndarray: Generated path as a numpy array of shape (N, 2).
    """
    # Parameters
    rest_time = 0.5 # [s]; Rest time at corners in seconds

    # Define points for different shapes [[x1, y1], [x2, y2], ...]
    if shape == 'square':
        points = np.array([[0, L], [L, L], [L, 0], [0, 0], [0, L]]) # Square
    elif shape == 'squareCCW':
        points = np.array([[0, L], [0, 0], [L, 0], [L, L], [0, L]]) # Square CCW
    elif shape == 'triangle':
        points = np.array([[0, 0], [L, 0], [L/2, L], [0, 0]])  # Triangle
    elif shape.startswith('diagonal'):
        suffix = shape[len('diagonal'):]
        parts = suffix.split('_')

        base = int(parts[0])
        variant = int(parts[1]) if len(parts) > 1 else None

        if variant is None:
            base_points = {
                1: np.array([[0, L], [L, 0]]),  # Line
                2: np.array([[0, 0], [L, L]]),  # Line
                3: np.array([[L, 0], [0, L]]),  # Line
                4: np.array([[L, L], [0, 0]])   # Line
            }
            points = base_points.get(base)
        else:
            variant_points = {
                1: np.array([[0, L/4], [L/4, 0]]),
                2: np.array([[0, L/2], [L/2, 0]]),
                3: np.array([[0, 3*L/4], [3*L/4, 0]]),
                4: np.array([[L/4, L], [L, L/4]]),
                5: np.array([[L/2, L], [L, L/2]]),
                6: np.array([[3*L/4, L], [L, 3*L/4]])
            }
            points = variant_points.get(variant)

            rotation_angles = {1: 0, 2: 90, 3: 180, 4: 270}
            angle = rotation_angles.get(base)
            points = rotate_path_deg(points, center=(L/2, L/2), degree=angle, ccw=True)

    elif shape.startswith('to'):                         # e.g., toEast_1, toNorth_2
        suffix = shape[len('to'):]
        parts = suffix.split('_')

        direction = parts[0]
        variant = int(parts[1]) if len(parts) > 1 else None

        if variant is None:
            raise ValueError("Variant number is required for 'to' shapes (e.g., toEast_1).")
        else:
            variant_points = {
                1: np.array([[0, L/4], [L, L/4]]),
                2: np.array([[0, L/2], [L, L/2]]),
                3: np.array([[0, 3*L/4], [L, 3*L/4]])
            }
            points = variant_points.get(variant)

            rotation_angles = {'East': 0, 'North': 90, 'West': 180, 'South': 270}
            angle = rotation_angles.get(direction)
            points = rotate_path_deg(points, center=(L/2, L/2), degree=angle, ccw=True)
    else:
        raise ValueError("Invalid shape. Use 'square', 'triangle', or 'diagonal'.")

    # Rest points at corners
    rest_steps = int(rest_time * hz)
    path = []

    # Generate segments for each pair of consecutive points
    for i in range(points.shape[0] - 1):
        # Add rest points at the start of the segment (corners)
        if i > 0:
            corner_x, corner_y = points[i, :]
            rest_segment = np.tile([[corner_x, corner_y]], (rest_steps, 1))
            path.append(rest_segment)

        # Calculate the distance and time for the segment
        x_start, x_end = points[i, 0], points[i + 1, 0]
        y_start, y_end = points[i, 1], points[i + 1, 1]
        distance = np.sqrt((x_end - x_start) ** 2 + (y_end - y_start) ** 2)
        time = distance / velocity
        time_steps = max(1, int(time * hz))

        # Interpolate the segment
        x_segment = np.linspace(x_start, x_end, time_steps, endpoint=True)
        y_segment = np.linspace(y_start, y_end, time_steps, endpoint=True)
        path.append(np.stack([x_segment, y_segment], axis=1))

    # Combine all segments into a single array
    path = np.vstack(path)

    return path

def generate_circle_path(L: float=0.03, hz: int=50, velocity: float=0.04, direction='CW'):
    """
    Generate a circular path.

    Parameters:
        hz (float): Command frequency in Hz (e.g., 10).
        velocity (float): Robot velocity in meters per second (e.g., 0.06 m/s).
        radius (float): Radius of the circle in meters (default: 0.015).
        center (tuple): Center of the circle as (x, y) (default: (0.015, 0.015)).
        direction (str): 'CW' for clockwise or 'CCW' for counterclockwise.

    Returns:
        np.ndarray: Circle path as a numpy array of shape (N, 2).
    """
    radius = L / 2
    center=(radius, radius)

    # Calculate the time step
    circumference = 2 * np.pi * radius
    total_time = circumference / velocity
    total_steps = int(total_time * hz)

    # Generate angles for the circle
    if direction == 'CW':
        angles = np.linspace(0, -2 * np.pi, total_steps, endpoint=True)
    elif direction == 'CCW':
        angles = np.linspace(0, 2 * np.pi, total_steps, endpoint=True)
    else:
        raise ValueError("Invalid direction. Use 'CW' or 'CCW'.")

    # Compute the points on the circle
    x = center[0] + radius * np.cos(angles)
    y = center[1] + radius * np.sin(angles)

    return np.stack((x, y), axis=1)

def rotate_path_deg(path, center=(0.015, 0.015), degree=90, ccw=True):
    """
    Rotate (N, 2) path by ±90 degrees around a given center.

    path   : np.ndarray of shape (N, 2)
    center : (cx, cy)
    ccw    : True  -> +90° (counter-clockwise)
             False -> -90° (clockwise)
    """
    cx, cy = center
    translated_path = path - np.array([cx, cy])

    rad = np.deg2rad(degree)
    # Rotation matrix for +theta or -theta degrees
    if ccw:
        rotation_matrix = np.array([[np.cos(rad), -np.sin(rad)],
                                     [np.sin(rad),  np.cos(rad)]])
    else:
        rotation_matrix = np.array([[np.cos(rad),  np.sin(rad)],
                                     [-np.sin(rad), np.cos(rad)]])
    rotated_path = translated_path @ rotation_matrix.T
    rotated_path += np.array([cx, cy])
    return rotated_path


def plot_colorLine(ax, path, L=0.03, cmap='viridis'):
    path_rotated = rotate_path_deg(path, center=(L/2, L/2), degree=90,ccw=True)
    x = path_rotated[:, 0]
    y = path_rotated[:, 1]
    N = path_rotated.shape[0]

    # Create line segments for LineCollection
    points = path_rotated.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    norm = plt.Normalize(0, N)
    lc = LineCollection(segments, cmap=cmap, norm=norm)
    lc.set_array(np.arange(N))
    lc.set_linewidth(1.2) # 2

    ax.add_collection(lc)
    ax.scatter(x, y, c=np.arange(N), cmap=cmap, s=20)

    ax.set_aspect('equal')
    ax.set_xlabel('X (m)', fontsize=8)
    ax.set_ylabel('Y (m)', fontsize=8)
    ax.grid(True)
    ax.set_xlim(-0.005, L + 0.005)
    ax.set_ylim(-0.005, L + 0.005)

    return lc, norm


# for Paper Figure
def plot_single_path(
        path, 
        L=0.03, 
        save_path=None, 
        show=True):
    
    # Physical figure size: 15 mm × 15 mm
    mm = 1 / 25.4
    fig, ax = plt.subplots(figsize=(15 * mm, 15 * mm))

    # Plot (reuse your existing logic)
    lc, norm = plot_colorLine(ax, path, L=L, cmap='plasma')

    # ---- Styling: exactly what you asked ----
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('')

    ax.tick_params(
        direction='in',
        length=2,
        width=0.4,
        labelsize=6
    )
    ax.tick_params(labelbottom=False)
    ax.tick_params(labelleft=False)
    ax.set_xticks([])
    ax.set_yticks([])

    # Box on
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.2)

    ax.grid(False)

    # Tight layout without padding
    plt.tight_layout(pad=0.2)

    # ---- Save ----
    if save_path is not None:
        if save_path.endswith('.svg'):
            plt.savefig(save_path, format='svg')
        else:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

    if show:
        plt.show()
    else:
        plt.close(fig)
    



def main():
    # Parameters
    L = 0.03            # [m]; Length of the square path in meters
    velocity = 0.04     # [m/s]; Robot velocity in meters per second
    frequency = 50      # [Hz]; Command frequency in Hz
    # shape_list = ['square','squareCCW','triangle','diagonal1','diagonal2','diagonal3','diagonal4',
    #               'diagonal1_1','diagonal1_2','diagonal1_3','diagonal1_4','diagonal1_5','diagonal1_6',
    #               'diagonal2_1','diagonal2_2','diagonal2_3','diagonal2_4','diagonal2_5','diagonal2_6',
    #               'diagonal3_1','diagonal3_2','diagonal3_3','diagonal3_4','diagonal3_5','diagonal3_6',
    #               'diagonal4_1','diagonal4_2','diagonal4_3','diagonal4_4','diagonal4_5','diagonal4_6',
    #               'toEast_1','toEast_2','toEast_3','toNorth_1','toNorth_2','toNorth_3',
    #               'toWest_1','toWest_2','toWest_3','toSouth_1','toSouth_2','toSouth_3',
    #               'circle','circleCCW']
    shape_list = SHAPE_LIST

    print(f'Number of Available Shapes: {len(shape_list)}')

    nrows = 5
    ncols = int(np.ceil(len(shape_list) / nrows))

    last_lc = None
    last_norm = None

    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(16, 10), constrained_layout=True)
    for ax, shape in zip(axes.flatten(), shape_list):
        # Generate the path
        if shape == 'circle':
            path = generate_circle_path(L=L, hz=frequency, velocity=velocity, direction='CW')
        elif shape == 'circleCCW':
            path = generate_circle_path(L=L, hz=frequency, velocity=velocity, direction='CCW')
        else:
            path = generate_path(L=L, hz=frequency, velocity=velocity, shape=shape)

        print(f"Path Shape: {shape} -> {path.shape[0]} steps")

        # Save Figure for paper
        plot_single_path(
            path, 
            L=L, 
            save_path=f'./figures/{shape}_path_figure.svg', # .png or .svg
            show=False)
        
        lc, norm = plot_colorLine(ax, path, L=L)
        last_lc = lc
        last_norm = norm
        ax.set_title(shape, fontsize=9)

    # Turn off any unused subplots
    for ax in axes.flatten()[len(shape_list):]:
        ax.axis('off')

    # One shared colorbar
    sm = plt.cm.ScalarMappable(norm=last_norm, cmap=last_lc.cmap)
    sm.set_array([])

    cbar = fig.colorbar(sm, ax=axes, orientation='vertical', fraction=0.02, pad=0.04)
    cbar.set_label('Step Index')

    # plt.tight_layout()
    plt.show()

    # plt.figure(figsize=(6,6))
    # plt.plot(path[:, 0])
    # plt.plot(path[:, 1])
    # plt.show()

if __name__ == "__main__":
  main()