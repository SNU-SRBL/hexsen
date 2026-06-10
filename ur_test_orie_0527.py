import rtde_control
# import rtde_receive
import time
import numpy as np
from scipy.spatial.transform import Rotation as R
import math

PI = math.pi

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




def main():

    global pose_count
    pose_count = 0

    ROBOT_IP = "192.168.10.2"  # Change to your robot's IP

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
    
    # Base position and orientation
    base_position = (-0.32918, 0.04309, 0.00550)  # in meters
    base_orientation = (-180, 0, -180)  # in degrees
    
    # Generate 20 points in upper hemisphere (convert mm to m)
    MM_TO_M = 0.001

    floor1 = [(-50*MM_TO_M, y*MM_TO_M, 0) for y in [200, 100, -100, -200]] + [(-150*MM_TO_M, y*MM_TO_M, 0) for y in [-100, 0, 100]]
    floor2 = [(-50*MM_TO_M, y*MM_TO_M, 75*MM_TO_M) for y in np.linspace(200, -200, 5)]\
      + [(-150*MM_TO_M, y*MM_TO_M, 75*MM_TO_M) for y in np.linspace(-100, 100, 3)]
    floor34 = [(-50*MM_TO_M, y*MM_TO_M, 150*MM_TO_M) for y in np.linspace(100, -100, 3)]\
      + [(-150*MM_TO_M, 0, 150*MM_TO_M), (-50*MM_TO_M, 0, 225*MM_TO_M)]
    
    linear = [(x*MM_TO_M, 0.0, 0.0) for x in [0, -220, 0]] * 10
    
    sphere_points = linear


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
        
        print(f"Point {point_idx + 1}/{len(sphere_points)}: ({x_point:.5f}, {y_point:.5f}, {z_point:.5f})")

        rotvec = ur_rpy_to_rotvec(rx_base, ry_base, rz_base, degrees=True)
        current_pose = [x_point, y_point, z_point, rotvec[0], rotvec[1], rotvec[2]]
        move_ur(current_pose, move_speed, acceleration, rest_time)

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

    print(f"\nCompleted {pose_count} poses!")
    time.sleep(2.0)
    
    # rtde_c.servoStop()
    rtde_c.disconnect()


if __name__ == '__main__':
    print('Starting UR robot sphere sampling motion...')
    main()