import numpy as np
import argparse
from svg.path import parse_path
from xml.dom import minidom
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

SLIDE_MAP = {
    'digit': ['v1', 16],
    'lasa': ['v1', 16],
    'maze': ['v3', 20],
}

def extract_path_coordinates(svg_file, L=0.03, velocity=0.04, hz=50) -> np.ndarray:
    """
    Extract coordinates from an SVG path, adjusting timesteps based on velocity and frequency.

    Args:
        svg_file (str): Path to the SVG file.
        velocity (float): Desired velocity in meters per second.
        hz (int): Sampling frequency in Hz.

    Returns:
        list: List of (x, y) coordinates in meters.
    """
    # Parse the SVG file
    doc = minidom.parse(svg_file)

    svg = doc.getElementsByTagName('svg')[0]
    viewbox_str = svg.getAttribute('viewBox')
    if viewbox_str:
        viewbox = list(map(float, viewbox_str.split()))
        viewbox_width = viewbox[2]
        scale_factor = L * 1000.0 / viewbox_width  # mm per SVG unit
        print("SVG viewBox:", viewbox)
    else:
        scale_factor = L / 1.0  # Default scale factor if no viewBox is provided

    path_strings = [path.getAttribute('d') for path in doc.getElementsByTagName('path')]
    doc.unlink()

    coordinates = []

    print(f"Loaded SVG: {len(path_strings)} paths found.")
    

    for path_string in path_strings:
        path = parse_path(path_string)
        dt = 1.0 / hz
        step = velocity * dt  # meters per step

        total_length = path.length() / 1000.0  # m
        distances = np.arange(0, total_length, step)

        for d in distances:
            t = d / total_length
            t = min(max(t, 0.0), 1.0)  # Clamp t to [0, 1]
            p = path.point(t)
            coordinates.append((p.real * scale_factor / 1000.0, p.imag * scale_factor / 1000.0))

    # Flipping Y-axis
    coordinates = [(x, L - y) for x, y in coordinates]

    return np.array(coordinates)


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


def plot_colorLine(ax, path, L=0.03):
    path_rotated = rotate_path_deg(path, center=(L/2, L/2), degree=90,ccw=True)
    x = path_rotated[:, 0]
    y = path_rotated[:, 1]
    N = path_rotated.shape[0]
    print(f"x, y init position: {x[0]:.5f}, {y[0]:.5f}")

    # Create line segments for LineCollection
    points = path_rotated.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    norm = plt.Normalize(0, N)
    lc = LineCollection(segments, cmap='viridis', norm=norm)
    lc.set_array(np.arange(N))
    lc.set_linewidth(2)

    ax.add_collection(lc)
    ax.scatter(x, y, c=np.arange(N), cmap='viridis', s=20)

    ax.set_aspect('equal')
    ax.set_xlabel('X (m)', fontsize=8)
    ax.set_ylabel('Y (m)', fontsize=8)
    ax.grid(True)
    ax.set_xlim(-0.005, L + 0.005)
    ax.set_ylim(-0.005, L + 0.005)

    return lc, norm


def main():

    parser = argparse.ArgumentParser(description="Plot SVG paths.")
    parser.add_argument('--slide', type=str, default=None,
                        help='Choose slide folder to plot.')
    args = parser.parse_args()
    slide_folder = "./slide-" + args.slide + "/"
    ver_slide = SLIDE_MAP.get(args.slide)[0]
    n_svg = SLIDE_MAP.get(args.slide)[1]
    svg_file = f"{args.slide}_{ver_slide}" # digit_v1


    L = 0.03            # [m]; Length of the square path in meters
    velocity = 0.04     # [m/s]; Robot velocity in meters per second
    frequency = 50      # [Hz]; Command frequency in Hz

    svg_list = [f"{svg_file}-{i:02d}"  for i in range(1, n_svg + 1)]  # lasa_v1-01 ...
    print(f'Number of Available SVG files: {len(svg_list)}')

    nrows = 4
    ncols = int(np.ceil(len(svg_list) / nrows))

    last_lc = None
    last_norm = None

    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(16, 10), constrained_layout=True)
    for ax, svg_name in zip(axes.flatten(), svg_list):
        # Generate the path
        svg_file = slide_folder + "path_" + svg_name + ".svg"
        path = extract_path_coordinates(svg_file, L, velocity, frequency)
        print(f"Processing SVG: {svg_name}")
        print(f"Path Shape: {path.shape} -> {path.shape[0]} steps")
        
        lc, norm = plot_colorLine(ax, path, L=L)
        last_lc = lc
        last_norm = norm
        ax.set_title(svg_name, fontsize=9)

    # Turn off any unused subplots
    for ax in axes.flatten()[len(svg_list):]:
        ax.axis('off')

    # One shared colorbar
    sm = plt.cm.ScalarMappable(norm=last_norm, cmap=last_lc.cmap)
    sm.set_array([])

    cbar = fig.colorbar(sm, ax=axes, orientation='vertical', fraction=0.02, pad=0.04)
    cbar.set_label('Step Index')

    plt.show()

    
if __name__ == "__main__":
    main()
