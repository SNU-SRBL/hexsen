import numpy as np
import csv
from pathlib import Path
from typing import List, Tuple
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def ur_rpy_to_rotvec(roll, pitch, yaw, degrees=True):
    """
    Convert UR teach pendant RPY to UR rotation vector.

    Parameters
    ----------
    roll : float
        Rotation about X axis
    pitch : float
        Rotation about Y axis
    yaw : float
        Rotation about Z axis
    degrees : bool
        True if input is degrees

    Returns
    -------
    np.ndarray shape (3,)
        Rotation vector [rx, ry, rz]
    """

    # UR pendant uses extrinsic XYZ rotations
    rot = R.from_euler('XYZ', [roll, pitch, yaw], degrees=degrees)

    rotvec = rot.as_rotvec()

    return rotvec


class PathGenerator:
    """Generate robot end-effector trajectories and save as CSV"""
    
    def __init__(self, output_dir: str = "./", sampling_rate: float = 50.0):
        """
        Args:
            output_dir: Directory to save CSV files
            sampling_rate: Sampling frequency in Hz (default 50 Hz)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sampling_rate = sampling_rate
        self.dt = 1.0 / sampling_rate
    
    
    def sphere_sampling_motion(self,
                              base_pose: Tuple[float, float, float],
                              sphere_points: List[Tuple[float, float, float]],
                              base_orientation: Tuple[float, float, float] = (-180, 0, -180),
                              orientation_offsets: List[float] = [-30, 0, 30],
                              rest_time: float = 1.0,
                              move_speed: float = 0.02,
                              filename: str = "path_sphere.csv") -> List[List[float]]:
        """
        Visit multiple points in sphere space with 27 orientation combinations at each point.
        Includes interpolated motion between positions and orientations.
        
        Args:
            base_pose: (x, y, z) base position
            sphere_points: List of (x, y, z) offsets from base_pose (20 points in upper hemisphere)
            base_orientation: (rx, ry, rz) base orientation in degrees
            orientation_offsets: List of angle offsets in degrees (default [-30, 0, 30])
            rest_time: Rest time at each pose in seconds (default 1.0s)
            move_speed: Linear speed for moving between positions in m/s (default 0.02 m/s for slower motion)
            filename: Output CSV filename
        
        Returns:
            List of [x, y, z, rx, ry, rz] poses
        """
        trajectory = []
        x_base, y_base, z_base = base_pose
        rx_base, ry_base, rz_base = base_orientation
        
        rest_points = int(rest_time * self.sampling_rate)
        
        # Convert sphere points to absolute positions
        absolute_sphere_points = [
            (x_base + pt[0], y_base + pt[1], z_base + pt[2])
            for pt in sphere_points
        ]
        
        previous_pose = None
        
        # For each sphere point
        for point_idx, current_position in enumerate(absolute_sphere_points):
            x_point, y_point, z_point = current_position
            
            # 27 combinations: rx, ry, rz each with 3 values (-30, 0, +30)
            for rx_offset in orientation_offsets:
                for ry_offset in orientation_offsets:
                    for rz_offset in orientation_offsets:
                        rx = rx_base + rx_offset
                        ry = ry_base + ry_offset
                        rz = rz_base + rz_offset # Unit: Degree

                        rotvec = ur_rpy_to_rotvec(rx, ry, rz, degrees=True)

                        current_pose = [x_point, y_point, z_point, rotvec[0], rotvec[1], rotvec[2]]
                        
                        # If not the first pose, interpolate motion from previous pose
                        if previous_pose is not None:
                            interpolated = self._interpolate_pose(
                                previous_pose, 
                                current_pose, 
                                move_speed
                            )
                            trajectory.extend(interpolated)
                        
                        # Rest at current pose for 1 second
                        for _ in range(rest_points):
                            trajectory.append(current_pose)
                        
                        previous_pose = current_pose
        
        self._save_csv(trajectory, filename)
        return trajectory
    
    def _interpolate_pose(self, 
                         start_pose: List[float], 
                         end_pose: List[float], 
                         speed: float) -> List[List[float]]:
        """
        Interpolate between two poses (position and orientation).
        Linear interpolation for position, linear interpolation for orientation.
        
        Args:
            start_pose: [x, y, z, rx, ry, rz]
            end_pose: [x, y, z, rx, ry, rz]
            speed: Linear speed in m/s (slower speed = more dense interpolation)
        
        Returns:
            List of interpolated poses (denser trajectory for slower motion)
        """
        trajectory = []
        
        # Extract position and orientation
        start_pos = np.array(start_pose[:3])
        end_pos = np.array(end_pose[:3])
        start_orient = np.array(start_pose[3:])
        end_orient = np.array(end_pose[3:])
        
        # Calculate distance
        position_distance = np.linalg.norm(end_pos - start_pos)
        
        # If positions are the same, just interpolate orientation
        if position_distance < 1e-6:
            # Orientation-only change, use shorter duration
            # Slower rotation speed: 30 deg/s (slower than before)
            orient_distance = np.linalg.norm(end_orient - start_orient)
            duration = orient_distance / 10.0
        else:
            # duration = distance / speed (slower speed creates longer duration = more points)
            duration = position_distance / speed
        
        num_points = int(duration * self.sampling_rate)
        num_points = max(2, num_points)  # At least 2 points for interpolation
        
        for i in range(num_points):
            progress = i / (num_points - 1)
            
            # Linear interpolation of position
            current_pos = start_pos + progress * (end_pos - start_pos)
            
            # Linear interpolation of orientation
            current_orient = start_orient + progress * (end_orient - start_orient)
            
            pose = list(current_pos) + list(current_orient)
            trajectory.append(pose)
        
        return trajectory

    
    def _save_csv(self, trajectory: List[List[float]], filename: str) -> None:
        """Save trajectory to CSV file"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for pose in trajectory:
                writer.writerow(pose)
        
        print(f"Saved {len(trajectory)} poses to {filepath}")

    def plot_trajectory_3d(self, trajectory: List[List[float]], 
                          title: str = "3D Trajectory", 
                          save_plot: bool = True,
                          plot_filename: str = "trajectory_3d.png") -> None:
        """
        Plot trajectory in 3D space (x, y, z coordinates).
        
        Args:
            trajectory: List of [x, y, z, rx, ry, rz] poses
            title: Title of the plot
            save_plot: Whether to save the plot to file
            plot_filename: Filename to save the plot
        """
        # Extract position data
        positions = np.array([pose[:3] for pose in trajectory])
        x = positions[:, 0]
        y = positions[:, 1]
        z = positions[:, 2]
        
        # Create figure and 3D axis
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot trajectory line
        ax.plot(x, y, z, 'b-', linewidth=1, alpha=0.7, label='Trajectory')
        
        # Plot start point
        ax.scatter(x[0], y[0], z[0], color='green', s=100, marker='o', label='Start', zorder=5)
        
        # Plot end point
        ax.scatter(x[-1], y[-1], z[-1], color='red', s=100, marker='s', label='End', zorder=5)
        
        # Plot sample waypoints (every Nth point to avoid clutter)
        step = max(1, len(trajectory) // 50)  # Show ~50 waypoints
        ax.scatter(x[::step], y[::step], z[::step], color='orange', s=30, alpha=0.5, label='Waypoints')
        
        # Set labels and title
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Set equal aspect ratio
        ax.set_box_aspect([1,1,1])
        
        if save_plot:
            plot_path = self.output_dir / plot_filename
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            print(f"Saved plot to {plot_path}")
        
        plt.show()


if __name__ == "__main__":
    # Initial pose of UR5e robot
    # initial_pose = (-0.64043, -0.10277 - 0.010, 0.04389, 2.22124, 2.2214, 0.0)
    base_position = (-0.51500-0.150, 0.060277 - 0.0, 0.08189)
    base_orientation = (-180, 0, -180)  # in degrees
    
    output_directory = "/home/seunghoon/Documents/BYJ-6axis/data/sphere"
    gen = PathGenerator(output_dir=output_directory, sampling_rate=50.0)
    
    print("Generating trajectories...")
    print(f"Initial pose: {base_position}\n")
    print(f"Base orientation: {base_orientation}\n")

    print("=== Sphere sampling motion (20 points, 27 orientations, 0.5s rest each) ===")
    
    # Generate 20 points in upper hemisphere (z >= 0)
    # You can customize these points based on your sphere coordinates
    sphere_points = [(x, -50, 0) for x in [200, 100, -100, -200]] \
    + [(x, -150, 0) for x in [-100, 0, 100]] \
    + [(x, -50, 75) for x in np.linspace(200, -200, 5)] \
    + [(x, -150, 75) for x in np.linspace(-100, 100, 3)] \
    + [(x, -50, 150) for x in np.linspace(100, -100, 3)] \
    + [(0, -150, 150), (0, -50, 225)]
    
    sphere_points = [
    tuple(v * 0.001 for v in point)
    for point in sphere_points
    ]

    trajectory = gen.sphere_sampling_motion(
        base_pose=base_position,
        sphere_points=sphere_points,
        base_orientation=base_orientation,
        orientation_offsets=[-10, 0, 10], # [-30, 0, 30]
        rest_time=2.0,          # Rest for 2 seconds at each pose
        move_speed=0.03,        # 0.03 m/s (slower motion = more dense interpolation)
        filename="path_sphere.csv"
    )

    print("\nGenerating 3D plots...")
    gen.plot_trajectory_3d(trajectory, 
                           title="Sphere Sampling Motion - 3D Trajectory",
                           plot_filename="trajectory_3d.png")
    
    print("\nAll trajectories generated successfully!")