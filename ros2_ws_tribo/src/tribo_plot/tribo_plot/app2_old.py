#!/usr/bin/env python3
"""
Application Node 2 - Socket-based velocity sender
Listens to /tribo/velocity and /tribo/state topics
Sends dx, dy, click via UDP socket using sender.py's protocol
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
import numpy as np
import threading
import socket
import struct
import time


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
        
        # State tracking
        self.current_state = 'idle'
        self.n_touch = 0
        self.current_touch_idx = 0
        self.is_touching = False  # Track if currently touching
        self.is_double_touch = False  # Track double touch for sliding
        self.last_detach_time = None  # Track time of last detach
        self.lock = threading.Lock()
        
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
        
        self.get_logger().info('App2 Node initialized')
    
    def state_callback(self, msg):
        """
        Track state changes for touch detection and double-tap recognition
        
        State machine:
        - touch: Start of touch sequence (sensor contact)
        - stay: Holding position while touching
        - slide: Moving while touching
        - detach: Released from sensor
        - idle: System idle
        
        Double-tap logic:
        - If touch comes within 1.5 seconds of previous detach, treat as double-tap
        - Keep is_touching=True during stay/slide phases
        """
        state = msg.data
        
        with self.lock:
            prev_state = self.current_state
            self.current_state = state
            
            # Start of touch sequence
            if state == 'touch':
                if prev_state in ['idle', 'detach']:
                    # Check if this is a double touch (within 1.5 seconds of last detach)
                    current_time = time.time()
                    if self.last_detach_time is not None:
                        time_since_detach = current_time - self.last_detach_time
                        if time_since_detach < 1.0:
                            self.is_double_touch = True
                            self.get_logger().info(f'Double touch detected! (Δt={time_since_detach:.2f}s)')
                        else:
                            self.is_double_touch = False
                    else:
                        self.is_double_touch = False
                    
                    self.current_touch_idx = self.n_touch
                    self.is_touching = True
                    self.get_logger().info(
                        f'Touch detected: touch_idx={self.current_touch_idx}, '
                        f'double_touch={self.is_double_touch}'
                    )
            
            # Keep touching during stay and slide phases
            elif state in ['stay', 'slide']:
                self.is_touching = True
                if state == 'slide' and self.is_double_touch:
                    self.get_logger().debug('Sliding with double-touch active')
            
            # Release on detach
            elif state == 'detach':
                self.is_touching = False
                self.last_detach_time = time.time()
                self.n_touch += 1
                self.get_logger().info(f'Detach detected: n_touch={self.n_touch}')
            
            # Reset when idle
            elif state == 'idle':
                self.is_touching = False
                self.is_double_touch = False
    
    def velocity_callback(self, msg):
        """
        Receive velocity from inference node and send via socket
        msg.data: [vx, vy] in meters
        
        Processing:
        1. Apply +90 degree rotation: vel = [-vy, vx]
        2. Invert Y for AHK compatibility: vel[1] *= -1
        3. Scale by 1000 to convert m to mm
        4. Convert to integers and send via socket
        """
        vel = np.array(msg.data, dtype=np.float32)
        
        with self.lock:
            # Step 1: Rotation by +90 degrees around center (0, 0)
            # This matches the rotation in widget.py
            vel_rotated = np.array([-vel[1], vel[0]], dtype=np.float32)
            
            # Step 2: Invert Y direction for AutoHotkey compatibility
            # (AHK uses inverted Y-axis for mouse movements)
            vel_rotated[1] *= -1.0

            scaler = 10.0 # 7.0
            
            # Step 3: Scale by 1000 (convert from m to mm)
            vel_scaled = vel_rotated * 1000.0 * scaler
            
            # Step 4: Convert to integers for socket transmission
            dx = int(np.round(vel_scaled[0]))
            dy = int(np.round(vel_scaled[1]))
            
            # Determine click state (True during touch/slide phases)
            click = self.is_touching
            
            # Step 5: Send via socket
            self._send_socket(dx, dy, click)
            
            self.get_logger().debug(
                f'Velocity -> Socket: vel={vel} -> rotated={vel_rotated} -> '
                f'scaled={vel_scaled} -> (dx={dx}, dy={dy}, click={click})'
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
            self.get_logger().error(f'Socket send error: {e}')


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
