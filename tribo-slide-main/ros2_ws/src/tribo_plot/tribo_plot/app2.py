#!/usr/bin/env python3
"""
Application Node 2 - Socket-based velocity sender
Listens to /tribo/velocity and /tribo/state topics
Sends dx, dy, click via UDP socket using sender.py's protocol
Modified to use short press to move, long press to click and drag
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
import numpy as np
import threading
import socket
import struct

class App2Node(Node):
    """
    Socket sender node - sends velocity data via UDP
    Subscribes to: /tribo/velocity, /tribo/state
    Sends to: UDP socket (default: 172.28.16.1:5000)
    """
    
    def __init__(self, addr=("172.28.16.1", 5000)):
        super().__init__('app2_node')

        # Initialize UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addr = addr
        self.get_logger().info(f'Socket initialized for {self.addr}')
        
        # --- Configuration ---
        self.HOLD_DELAY = 1.0      # Time (s) to wait for mousedown
        self.MOVE_THRESHOLD = 0.0001  # Velocity threshold to cancel the click timer
        self.SCALER = 20.0         # Sensitivity scaler
        
        # State tracking
        self.lock = threading.Lock()
        self.is_drag_active = False
        self.click_timer = None
        self.click_cancelled_by_move = False
        
        # Subscribers
        self.velocity_sub = self.create_subscription(
            Float32MultiArray,
            '/tribo/velocity',
            self.velocity_callback,
            10
        )
        
        self.state_sub = self.create_subscription(
            String,
            '/tribo/state',
            self.state_callback,
            10
        )

        self.get_logger().info('Mode: Move-to-Cancel Click. Hold still for Drag.')

    def state_callback(self, msg):
        state = msg.data
        with self.lock:
            if state == 'touch':
                self._cancel_timer()
                self.click_cancelled_by_move = False
                self.is_drag_active = False
                # Start timer to register mousedown
                self.click_timer = threading.Timer(self.HOLD_DELAY, self._trigger_mousedown)
                self.click_timer.start()

            elif state == 'detach':
                self._cancel_timer()
                if self.is_drag_active:
                    self.get_logger().info('Mouse Released')
                
                self.is_drag_active = False
                self.click_cancelled_by_move = False
                # Always release mouse on detach
                self._send_socket(0, 0, False)

    def _trigger_mousedown(self):
        with self.lock:
            if not self.click_cancelled_by_move:
                self.is_drag_active = True
                self.get_logger().info('Mousedown Registered (Held Still)')
                self._send_socket(0, 0, True)

    def _cancel_timer(self):
        if self.click_timer:
            self.click_timer.cancel()
            self.click_timer = None

    def velocity_callback(self, msg):
        """
        Receive velocity from inference node and send via socket
        msg.data: [vx, vy]

        Processing:
        1. Apply +90 degree rotation: vel = [-vy, vx]
        2. Invert Y for AHK compatibility: vel[1] *= -1
        3. Convert to integers and send via socket
        """
        vel = np.array(msg.data, dtype=np.float32)
        speed = np.linalg.norm(vel)

        with self.lock:
            # Check if we should cancel the click because the user is moving
            if not self.is_drag_active and not self.click_cancelled_by_move:
                if speed > self.MOVE_THRESHOLD:
                    if self.click_timer:
                        self.get_logger().info('Movement detected: Click cancelled.')
                        self._cancel_timer()
                        self.click_cancelled_by_move = True

            # Process coordinates
            vel_rotated = np.array([-vel[1], vel[0]], dtype=np.float32)
            vel_rotated[1] *= -1.0 # AHK Inversion
            
            # Scale velocities and convert to integers for socket transmission
            vel_scaled = vel_rotated * 1000.0 * self.SCALER
            dx = int(np.round(vel_scaled[0]))
            dy = int(np.round(vel_scaled[1]))
            
            # Send movement. click=True only if the timer finished successfully.
            self._send_socket(dx, dy, self.is_drag_active)

            self.get_logger().debug(
                f'Velocity -> Socket: vel={vel} -> rotated={vel_rotated} -> '
                f'scaled={vel_scaled} -> (dx={dx}, dy={dy}, click={self.is_drag_active})'
            )

    def _send_socket(self, dx, dy, click):
        """
        Send dx, dy, click via UDP socket
        Protocol: struct.pack("<iiB", dx, dy, click_flag)
        """
        try:
            payload = struct.pack("<iiB", dx, dy, 1 if click else 0)
            self.sock.sendto(payload, self.addr)
        except Exception as e:
            self.get_logger().error(f'Socket error: {e}')


def main(args=None):
    rclpy.init(args=args)

    # Optional: configure socket address from command line arguments
    # Default: 172.28.16.1:5000 (Windows host IP)
    addr = ("172.28.16.1", 5000)

    node = App2Node(addr=addr)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.sock.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()