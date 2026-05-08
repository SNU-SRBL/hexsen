import numpy as np
import csv
from pathlib import Path
from typing import List, Tuple

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
    
    def linear_motion_y_axis(self,
                            initial_pose: Tuple[float, float, float, float, float, float],
                            distance: float = 0.05,
                            speed: float = 0.1,
                            rest_time: float = 0.5,
                            filename: str = "path_linear_y.csv") -> List[List[float]]:
        """
        Linear motion along Y axis: rest -> move down -> rest -> move up -> rest
        
        Args:
            initial_pose: (x, y, z, rx, ry, rz) initial pose
            distance: Distance to move in meters (default 50mm = 0.05m)
            speed: Linear speed in m/s (default 0.1 m/s)
            rest_time: Rest time at each position in seconds (default 0.5s)
            filename: Output CSV filename
        
        Returns:
            List of [x, y, z, rx, ry, rz] poses
        """
        trajectory = []
        x, y, z, rx, ry, rz = initial_pose
        
        # Phase 1: Rest at initial pose
        rest_points = int(rest_time * self.sampling_rate)
        for _ in range(rest_points):
            trajectory.append([x, y, z, rx, ry, rz])
        
        # Phase 2: Move down along -Y
        move_duration = distance / speed
        move_points = int(move_duration * self.sampling_rate)
        for i in range(move_points):
            progress = i / move_points
            y_current = y - distance * progress
            trajectory.append([x, y_current, z, rx, ry, rz])
        
        # Phase 3: Rest at lower position
        for _ in range(rest_points):
            trajectory.append([x, y - distance, z, rx, ry, rz])
        
        # Phase 4: Move back up along +Y
        for i in range(move_points):
            progress = i / move_points
            y_current = (y - distance) + distance * progress
            trajectory.append([x, y_current, z, rx, ry, rz])
        
        # Phase 5: Rest at initial pose again
        for _ in range(rest_points):
            trajectory.append([x, y, z, rx, ry, rz])
        
        self._save_csv(trajectory, filename)
        return trajectory
    
    def square_motion(self,
                     initial_pose: Tuple[float, float, float, float, float, float],
                     side_length: float = 0.025,
                     speed: float = 0.1,
                     rest_time: float = 0.5,
                     filename: str = "path_square.csv") -> List[List[float]]:
        """
        Square motion with rest at each corner:
        initial -> rest -> +X(25mm) -> rest -> -Y(50mm) -> rest -> -X(50mm) -> rest -> +Y(50mm) -> rest -> +X(25mm) -> rest -> initial -> rest
        
        Args:
            initial_pose: (x, y, z, rx, ry, rz) initial pose
            side_length: Half side length (default 25mm = 0.025m for 50mm square)
            speed: Linear speed in m/s
            rest_time: Rest time at each corner in seconds
            filename: Output CSV filename
        
        Returns:
            List of [x, y, z, rx, ry, rz] poses
        """
        trajectory = []
        x0, y0, z0, rx, ry, rz = initial_pose
        
        # Define waypoints
        waypoints = [
            (x0, y0, z0),                          # Start
            (x0 + side_length, y0, z0),           # +X (25mm)
            (x0 + side_length, y0 - 2*side_length, z0),  # -Y (50mm)
            (x0 - side_length, y0 - 2*side_length, z0),  # -X (50mm)
            (x0 - side_length, y0, z0),           # +Y (50mm)
            (x0, y0, z0),                          # Back to start
        ]
        
        trajectory = self._interpolate_waypoints_with_rest(waypoints, rx, ry, rz, speed, rest_time)
        self._save_csv(trajectory, filename)
        return trajectory
    
    def triangle_motion(self,
                       initial_pose: Tuple[float, float, float, float, float, float],
                       side_length: float = 0.025,
                       speed: float = 0.1,
                       rest_time: float = 0.5,
                       filename: str = "path_triangle.csv") -> List[List[float]]:
        """
        Triangle motion with rest at each vertex:
        initial -> rest -> +X(25mm) -> rest -> -Y(25*sqrt(3)mm) -> rest -> -X(25mm) -> rest -> back to initial -> rest
        
        Args:
            initial_pose: (x, y, z, rx, ry, rz) initial pose
            side_length: Side length (default 25mm = 0.025m)
            speed: Linear speed in m/s
            rest_time: Rest time at each vertex in seconds
            filename: Output CSV filename
        
        Returns:
            List of [x, y, z, rx, ry, rz] poses
        """
        trajectory = []
        x0, y0, z0, rx, ry, rz = initial_pose
        
        # Equilateral triangle vertices
        y_offset = side_length * np.sqrt(3)
        
        waypoints = [
            (x0, y0, z0),                    # Start (bottom center)
            (x0 + side_length, y0, z0),     # Right vertex (+X 25mm)
            (x0, y0 - y_offset, z0),        # Top vertex (-Y 25*sqrt(3)mm)
            (x0 - side_length, y0, z0),     # Left vertex (-X 25mm)
            (x0, y0, z0),                    # Back to start
        ]
        
        trajectory = self._interpolate_waypoints_with_rest(waypoints, rx, ry, rz, speed, rest_time)
        self._save_csv(trajectory, filename)
        return trajectory
    
    def circle_motion(self,
                     initial_pose: Tuple[float, float, float, float, float, float],
                     radius: float = 0.025,
                     speed: float = 0.1,
                     rest_time: float = 0.5,
                     ccw: bool = True,
                     filename: str = "path_circle.csv") -> List[List[float]]:
        """
        Circle motion in XY plane with CCW direction and rest at start
        Center point: initial_pose + (0, -radius, 0)
        
        Args:
            initial_pose: (x, y, z, rx, ry, rz) initial pose (start point on circle)
            radius: Circle radius in meters (default 25mm = 0.025m for 50mm diameter)
            speed: Linear speed in m/s
            rest_time: Rest time at initial pose in seconds
            ccw: Counter-clockwise direction (True) or clockwise (False)
            filename: Output CSV filename
        
        Returns:
            List of [x, y, z, rx, ry, rz] poses
        """
        trajectory = []
        x0, y0, z0, rx, ry, rz = initial_pose
        
        # Rest at initial pose
        rest_points = int(rest_time * self.sampling_rate)
        for _ in range(rest_points):
            trajectory.append([x0, y0, z0, rx, ry, rz])
        
        # Center of circle: initial_pose + (0, -radius, 0)
        center_x = x0
        center_y = y0 - radius
        
        # Circumference and duration
        circumference = 2 * np.pi * radius
        duration = circumference / speed
        num_points = int(duration * self.sampling_rate)
        
        for i in range(num_points):
            t = i * self.dt
            # Full circle: 0 -> 2*pi
            angle = 2 * np.pi * (t / duration)
            
            # CCW: start from top (pi/2) and go counter-clockwise
            if ccw:
                angle = np.pi / 2 - angle  # Start at top, go CCW
            else:
                angle = np.pi / 2 + angle  # Start at top, go CW
            
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            
            trajectory.append([x, y, z0, rx, ry, rz])
        
        self._save_csv(trajectory, filename)
        return trajectory
    
    def _interpolate_waypoints_with_rest(self, waypoints: List[Tuple[float, float, float]], 
                                        rx: float, ry: float, rz: float, speed: float, rest_time: float) -> List[List[float]]:
        """Interpolate between waypoints with linear motion and rest at each waypoint"""
        trajectory = []
        rest_points = int(rest_time * self.sampling_rate)
        
        for i in range(len(waypoints)):
            # Rest at current waypoint
            for _ in range(rest_points):
                trajectory.append([waypoints[i][0], waypoints[i][1], waypoints[i][2], rx, ry, rz])
            
            # Move to next waypoint (if not the last one)
            if i < len(waypoints) - 1:
                p1 = np.array(waypoints[i])
                p2 = np.array(waypoints[i + 1])
                
                distance = np.linalg.norm(p2 - p1)
                duration = distance / speed
                num_points = int(duration * self.sampling_rate)
                
                for j in range(num_points):
                    progress = j / num_points if num_points > 0 else 0
                    
                    # Linear interpolation
                    current_pose = p1 + progress * (p2 - p1)
                    trajectory.append([current_pose[0], current_pose[1], current_pose[2], rx, ry, rz])
        
        return trajectory
    
    def _save_csv(self, trajectory: List[List[float]], filename: str) -> None:
        """Save trajectory to CSV file"""
        filepath = self.output_dir / filename
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for pose in trajectory:
                writer.writerow(pose)
        
        print(f"✓ Saved {len(trajectory)} poses to {filepath}")


if __name__ == "__main__":
    # Initial pose of UR5e robot
    initial_pose = (-0.64043, -0.10277 - 0.010, 0.04389, 2.22124, 2.2214, 0.0)
    
    output_directory = "/home/seunghoon/Documents/BYJ-6axis/data/basic"
    gen = PathGenerator(output_dir=output_directory, sampling_rate=50.0)
    
    print("Generating trajectories...")
    print(f"Initial pose: {initial_pose}\n")
    
    # 1. Linear motion along Y axis (with rest)
    print("1. Linear motion (Y axis, ±50mm, with 0.5s rest)...")
    gen.linear_motion_y_axis(
        initial_pose=initial_pose,
        distance=0.05,  # 50mm
        speed=0.05,     # 0.05 m/s # 0.1m/s
        rest_time=0.5,  # 0.5 second rest
        filename="path_trajectory.csv"
    )
    
    # 2. Square motion (with rest)
    print("2. Square motion (50mm x 50mm, with 0.5s rest at corners)...")
    gen.square_motion(
        initial_pose=initial_pose,
        side_length=0.025,  # 25mm (50mm total side)
        speed=0.05,
        rest_time=0.5,
        filename="path_square.csv"
    )
    
    # 3. Triangle motion (with rest)
    print("3. Triangle motion (25mm side, with 0.5s rest at vertices)...")
    gen.triangle_motion(
        initial_pose=initial_pose,
        side_length=0.025,  # 25mm
        speed=0.05,
        rest_time=0.5,
        filename="path_triangle.csv"
    )
    
    # 4. Circle motion (with rest)
    print("4. Circle motion (25mm radius, CCW, with 0.5s rest at start)...")
    gen.circle_motion(
        initial_pose=initial_pose,
        radius=0.025,  # 25mm radius (50mm diameter)
        speed=0.05,
        rest_time=0.5,
        ccw=True,
        filename="path_circle.csv"
    )
    
    print("\n✓ All trajectories generated successfully!")