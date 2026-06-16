import argparse
import rtde_control
# import rtde_receive
import time
import pandas as pd
import numpy as np
from scipy.spatial.transform import Rotation as R
import math

PI = math.pi


def parse_arguments():
    """Handles CLI argument parsing."""
    parser = argparse.ArgumentParser(description="UR Robot Control for Data Acquisition")
    
    parser.add_argument("--ip", type=str, default="192.168.10.2", help="IP address of the UR robot")
  
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

    n_set = 1 # 5

    # Generate 20 points in upper hemisphere (convert mm to m)
    MM_TO_M = 0.001

    # Load walk trajectory file
    df = pd.read_csv('./walk/walk_slow.csv')

    # Verify the result
    print(df.head())
    print(df)

    traj_walk = []
    for i in range(0, 100, 10):
        row = df.iloc[i].copy()
        row.iloc[:3] *= MM_TO_M  # Convert position from mm to m
        traj_walk.append(row.tolist())

    print(f'Loaded trajectory points: {len(traj_walk)}')

    # Base position and orientation
    base_position = (-0.32918, 0.04309, 0.00550)  # in meters
    base_orientation = (-180, 0, -180)  # in degrees
    
    # Dynamically assign sampling_points based on the CLI argument
    sampling_points = traj_walk * n_set

    # Motion parameters
    move_speed = 0.03  # m/s
    acceleration = 0.3  # m/s^2
    rest_time = 0.0  # seconds at each pose
    
    x_base, y_base, z_base = base_position
    rx_base, ry_base, rz_base = base_orientation
    
    print(f"\nBase position: {base_position}")
    print(f"Base orientation (degrees): {base_orientation}")
    print(f"Total sphere points: {len(sampling_points)}")
    print(f"\nStarting sphere sampling motion...\n")
     

    # Go to the First Position
    sphere_offset = sampling_points[0]
    x_point = x_base + sphere_offset[0]
    y_point = y_base + sphere_offset[1]
    z_point = z_base + sphere_offset[2]
    rotvec = ur_rpy_to_rotvec(rx_base, ry_base, rz_base, degrees=True)
    current_pose = [x_point, y_point, z_point, rotvec[0], rotvec[1], rotvec[2]]
    # print(f"  Pose {pose_count}: RPY({rx}, {ry}, {rz}°) -> ", end="")
    move_ur(current_pose, move_speed, acceleration, rest_time)

    # For each sphere point
    for point_idx, sphere_offset in enumerate(sampling_points):
        x_point = x_base + sphere_offset[0]
        y_point = y_base + sphere_offset[1]
        z_point = z_base + sphere_offset[2]

        print(f"Point {point_idx + 1}/{len(sampling_points)}: ({x_point:.5f}, {y_point:.5f}, {z_point:.5f})")

        # rotvec = ur_rpy_to_rotvec(rx_base, ry_base, rz_base, degrees=True)
        # current_pose = [x_point, y_point, z_point, rotvec[0], rotvec[1], rotvec[2]]
        # move_ur(current_pose, move_speed, acceleration, rest_time)

        rx_offset = sphere_offset[3]
        ry_offset = sphere_offset[4]
        rz_offset = sphere_offset[5]  # Unit: Degree

        rx = rx_offset
        ry = ry_offset
        rz = rz_offset  # Unit: Degree
        
        rotvec = ur_rpy_to_rotvec(rx, ry, rz, degrees=True)
        current_pose = [x_point, y_point, z_point, rotvec[0], rotvec[1], rotvec[2]]
        move_ur(current_pose, move_speed, acceleration, rest_time)

        # rotvec = ur_rpy_to_rotvec(rx_base, ry_base, rz_base, degrees=True)
        # current_pose = [x_point, y_point, z_point, rotvec[0], rotvec[1], rotvec[2]]
        # move_ur(current_pose, move_speed, acceleration, rest_time)

    print(f"Returning to the original position")
    rotvec = ur_rpy_to_rotvec(rx_base, ry_base, rz_base, degrees=True)
    move_ur([x_base, y_base, z_base, rotvec[0], rotvec[1], rotvec[2]], move_speed, acceleration, rest_time)

    time.sleep(5.0)
    print(f"\nCompleted {pose_count} poses!")
    
    # rtde_c.servoStop()
    rtde_c.disconnect()
    


if __name__ == '__main__':
    print('Starting UR robot walk sampling motion...')
    # Parse command-Line arguments
    args = parse_arguments()
    main(args)