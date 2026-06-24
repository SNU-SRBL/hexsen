import rtde_control
import rtde_receive
import time
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
    ROBOT_IP = "192.168.10.2"  # Change to your robot's IP

    # Connect to RTDE interfaces
    rtde_c = rtde_control.RTDEControlInterface(ROBOT_IP)
    rtde_r = rtde_receive.RTDEReceiveInterface(ROBOT_IP)

    # Get current pose
    current_pose = rtde_r.getActualTCPPose()  # [x, y, z, Rx, Ry, Rz]
    print("Current TCP Pose:", current_pose)

    print("Sending moveL command...")
    base_position = (-0.32918, 0.04309, 0.00550)  # in meters
    base_orientation = (-180, 0, 180)  # in degrees

    x_base, y_base, z_base = base_position
    rx_base, ry_base, rz_base = base_orientation

    for _ in range(10):
        rotvec = ur_rpy_to_rotvec(rx_base, ry_base, rz_base - 45, degrees=True)
        p = [x_base - 0.10, y_base, z_base, rotvec[0], rotvec[1], rotvec[2]] # Unit [m, rad]
        rtde_c.moveL(p, 0.05, 0.3) # velocity, accelration

        rotvec = ur_rpy_to_rotvec(rx_base, ry_base, rz_base, degrees=True)
        p = [x_base - 0.10, y_base, z_base, rotvec[0], rotvec[1], rotvec[2]] # Unit [m, rad]
        rtde_c.moveL(p, 0.05, 0.3) # velocity, accelration

        

    time.sleep(2.0)
    
    # rtde_c.servoStop()
    rtde_c.disconnect()



if __name__ == '__main__':
    print('hi')
    main()