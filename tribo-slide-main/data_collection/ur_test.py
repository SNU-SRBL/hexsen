import rtde_control
import rtde_receive
import time
import math

def main():
    ROBOT_IP = "192.168.10.2"  # Change to your robot's IP

    # Connect to RTDE interfaces
    rtde_c = rtde_control.RTDEControlInterface(ROBOT_IP)
    rtde_r = rtde_receive.RTDEReceiveInterface(ROBOT_IP)

    # Get current pose
    current_pose = rtde_r.getActualTCPPose()  # [x, y, z, Rx, Ry, Rz]
    print("Current TCP Pose:", current_pose)
    
    # Desired joint positions in radians
    q = [0.0, -1.57, 1.57, -1.57, -1.57, 0.0]

    # Send servoJ command (realtime joint-level control)
    # print("Sending servoJ command...")
    # rtde_c.moveJ(q, 0.06, 0.2) # velocity, accelration
    # rtde_c.servoJ(q, 0.06, 0.01, 0.01, 0.2, 300)  # target_q, velocity, acceleration, dt, lookahead_time, gain

    print("Sending moveL command...")
    # p = [-0.62500, -0.00400, 0.27000, 0.0, -1/2 * math.pi, 0.0] # Unit [m]
    # rtde_c.moveL(p, 0.03, 0.2) # velocity, accelration

    time.sleep(1.0)
    
    rtde_c.servoStop()
    rtde_c.disconnect()

if __name__ == '__main__':
    print('hi')
    main()