import argparse
import rtde_control
# import rtde_receive
import time
import numpy as np
from scipy.spatial.transform import Rotation as R
import math

PI = math.pi


def parse_arguments():
    """Handles CLI argument parsing."""
    parser = argparse.ArgumentParser(description="UR Robot Control for Data Acquisition")
    
    parser.add_argument("--ip", type=str, default="192.168.10.2", help="IP address of the UR robot")
    parser.add_argument(
        "--traj", 
        type=str, 
        default="linear", 
        choices=["linear", "floor1", "floor2", "floor34","type2", "all"], 
        help="Trajectory type to execute"
    )
    parser.add_argument("linear_length", type=int, nargs='?', default=220, help="Length of linear trajectory in mm (only for 'linear' traj)")
    
    return parser.parse_args()


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




def main(args):

    global pose_count
    pose_count = 0

    ROBOT_IP = args.ip  # Change to your robot's IP

    # Connect to RTDE interfaces
    rtde_c = rtde_control.RTDEControlInterface(ROBOT_IP)
    # rtde_r = rtde_receive.RTDEReceiveInterface(ROBOT_IP)

    def move_ur(current_pose, move_speed, acceleration, rest_time):

        global pose_count
        pose_count += 1
        # print(f"  Pose {pose_count}: RPY({rx}, {ry}, {rz}°) -> ", end="")
        print(f"  Pose {pose_count}: ", end="")
        try:
            rtde_c.moveL(current_pose, move_speed, acceleration)
            print(f"Moving... ", end="")
            time.sleep(rest_time)
            print(f"Rest complete")
        except Exception as e:
            print(f"ERROR: {e}")
    

    # Get current pose
    # current_pose = rtde_r.getActualTCPPose()  # [x, y, z, Rx, Ry, Rz]
    # print("Current TCP Pose:", current_pose)

    n_set = 1
    
    # Base position and orientation
    base_position = (-0.32918, 0.04309, 0.00550)  # in meters
    base_orientation = (-180, 0, -180)  # in degrees
    
    # Generate 20 points in upper hemisphere (convert mm to m)
    MM_TO_M = 0.001

    linear_length = args.linear_length*MM_TO_M
    x_offset2 = 60*MM_TO_M

    floor1 = [(-50*MM_TO_M, y*MM_TO_M, 0, True) for y in [200, 100, -100, -200]] + [(-150*MM_TO_M, y*MM_TO_M, 0, True) for y in [-100, 0, 100]]
    floor2 = [(-50*MM_TO_M, y*MM_TO_M, 75*MM_TO_M, True) for y in np.linspace(200, -200, 5)]\
      + [(-150*MM_TO_M, y*MM_TO_M, 75*MM_TO_M, True) for y in np.linspace(-100, 100, 3)]
    floor34 = [(-50*MM_TO_M, y*MM_TO_M, 150*MM_TO_M, True) for y in np.linspace(100, -100, 3)]\
      + [(-150*MM_TO_M, 0, 150*MM_TO_M, True), (-50*MM_TO_M, 0, 225*MM_TO_M, True)]

    # linear = [(x, 0.0, 0.0, False) for x in [0, -linear_length, 0]] * 10 * n_set
    linear = [(x, 0.0, 0.0, False) for x in [-x_offset2, -linear_length, -x_offset2]] * 10 * n_set

    
    type2_radius = 125*MM_TO_M
    type2_sphere = [(0, 0, 0, False), (-x_offset2, 0, 0, True), (0, 0, 0 ,False)] + \
                   [(0, 0, 0, False), (-x_offset2, 0, 0, False), (-x_offset2, type2_radius, 0, True), (-x_offset2, 0, 0, False), (0, 0, 0, False)] + \
                   [(0, 0, 0, False), (-x_offset2, 0, 0, False), (-x_offset2, -type2_radius, 0, True), (-x_offset2, 0, 0, False), (0, 0, 0, False)] + \
                   [(0, 0, 0, False), (-x_offset2, 0, 0, False), (-x_offset2 - type2_radius, 0, 0, True), (-x_offset2, 0, 0, False), (0, 0, 0, False)] + \
                   [(0, 0, 0, False), (-x_offset2, 0, 0, False), (-x_offset2, 0, type2_radius, True), (-x_offset2, 0, 0, False), (0, 0, 0, False)]

    trajectory_map = {
        "linear": linear,
        "floor1": floor1,
        "floor2": floor2,
        "floor34": floor34,
        "type2": type2_sphere,
        "all": floor1 + floor2 + floor34  # Combines all points into one sequence
    }
    
    # Dynamically assign sphere_points based on the CLI argument
    sphere_points = trajectory_map[args.traj]

    # Orientation offsets
    orientation_offsets = [-10, 0, 10]
    if sphere_points == linear:
        orientation_offsets = [0]

    # Motion parameters
    move_speed = 0.05  # m/s
    acceleration = 0.3  # m/s^2
    rest_time = 1.0  # seconds at each pose
    
    x_base, y_base, z_base = base_position
    rx_base, ry_base, rz_base = base_orientation
    
    print(f"\nBase position: {base_position}")
    print(f"Base orientation (degrees): {base_orientation}")
    print(f"Total sphere points: {len(sphere_points)}")
    print(f"Orientation combinations: {len(orientation_offsets)**3}")
    print(f"Total poses: {len(sphere_points) * len(orientation_offsets)**3}")
    print(f"\nStarting sphere sampling motion...\n")
     

    # Go to the First Position
    sphere_offset = sphere_points[0]
    x_point = x_base + sphere_offset[0]
    y_point = y_base + sphere_offset[1]
    z_point = z_base + sphere_offset[2]
    rotvec = ur_rpy_to_rotvec(rx_base, ry_base, rz_base, degrees=True)
    current_pose = [x_point, y_point, z_point, rotvec[0], rotvec[1], rotvec[2]]
    # print(f"  Pose {pose_count}: RPY({rx}, {ry}, {rz}°) -> ", end="")
    move_ur(current_pose, move_speed, acceleration, rest_time)

    # For each sphere point
    for point_idx, sphere_offset in enumerate(sphere_points):
        x_point = x_base + sphere_offset[0]
        y_point = y_base + sphere_offset[1]
        z_point = z_base + sphere_offset[2]
        is_turn = sphere_offset[3]

        print(f"Point {point_idx + 1}/{len(sphere_points)}: ({x_point:.5f}, {y_point:.5f}, {z_point:.5f})")

        rotvec = ur_rpy_to_rotvec(rx_base, ry_base, rz_base, degrees=True)
        current_pose = [x_point, y_point, z_point, rotvec[0], rotvec[1], rotvec[2]]
        move_ur(current_pose, move_speed, acceleration, rest_time)

        if is_turn:
            # 27 combinations: rx, ry, rz each with 3 values (-10, 0, +10)
            for rx_offset in orientation_offsets:
                for ry_offset in orientation_offsets:
                    for rz_offset in orientation_offsets:
                        rx = rx_base + rx_offset
                        ry = ry_base + ry_offset
                        rz = rz_base + rz_offset  # Unit: Degree
                        
                        rotvec = ur_rpy_to_rotvec(rx, ry, rz, degrees=True)
                        current_pose = [x_point, y_point, z_point, rotvec[0], rotvec[1], rotvec[2]]
                        move_ur(current_pose, move_speed, acceleration, rest_time)
        
        rotvec = ur_rpy_to_rotvec(rx_base, ry_base, rz_base, degrees=True)
        current_pose = [x_point, y_point, z_point, rotvec[0], rotvec[1], rotvec[2]]
        move_ur(current_pose, move_speed, acceleration, rest_time)

    print(f"Returning to the original position")
    rotvec = ur_rpy_to_rotvec(rx_base, ry_base, rz_base, degrees=True)
    move_ur([x_base, y_base, z_base, rotvec[0], rotvec[1], rotvec[2]], move_speed, acceleration, rest_time)

    time.sleep(5.0)
    print(f"\nCompleted {pose_count} poses!")
    
    # rtde_c.servoStop()
    rtde_c.disconnect()


if __name__ == '__main__':
    print('Starting UR robot sphere sampling motion...')
    # Parse command-Line arguments
    args = parse_arguments()
    main(args)