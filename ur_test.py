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

    # Get current Force Torque
    current_force = rtde_r.getActualTCPForce()
    print("Current TCP Force:", current_force)

    # Desired joint positions in radians
    q = [0.0, -1.57, 1.57, -1.57, -1.57, 0.0]

    # Send servoJ command (realtime joint-level control)
    # print("Sending servoJ command...")
    # rtde_c.moveJ(q, 0.06, 0.2) # velocity, accelration
    # rtde_c.servoJ(q, 0.06, 0.01, 0.01, 0.2, 300)  # target_q, velocity, acceleration, dt, lookahead_time, gain
    print("Sending moveL command...")
    # p = [-0.46053, -0.19553, 0.41646, 2.24908, 2.13796, -0.14939] # Unit [m]
    # p = [-0.66042, -0.10032, 0.03160, 2.2214, 2.2214, 0.0] # Unit [m, rad]
    # p = [-0.64043, -0.10277 - 0.010, 0.04389, 2.22124, 2.2214, 0.0] # Unit [m, rad]
    rotvec = ur_rpy_to_rotvec(-180, 0, -180, True)
    p = [-0.63800, 0.11738, 0.04562, rotvec[0], rotvec[1], rotvec[2]] # Unit [m, rad]
    # p = [-0.66042, -0.10032, 0.25160, 3.14, 0.0, 1.57] # Unit [m, rad]
    # Y = -102 ~ -102+75mm
    p = [-0.48322, -0.12599, 0.2, 0.0, -PI, 0.0]
    p = [-0.32918, 0.04309, 0.00550, 0.0, PI, 0.0]
    rtde_c.moveL(p, 0.04, 0.2) # velocity, accelration
    time.sleep(2.0)
    
    # rtde_c.servoStop()
    rtde_c.disconnect()



if __name__ == '__main__':
    print('hi')
    main()