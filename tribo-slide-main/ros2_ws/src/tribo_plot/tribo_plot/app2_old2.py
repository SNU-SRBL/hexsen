#!/usr/bin/env python3
"""
Application Node 2 - Socket-based velocity sender
Listens to /tribo/velocity and /tribo/state topics
Sends dx, dy, click via UDP socket using sender.py's protocol
Modified to mimic laptop touchpad behavior
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
      
      # Timing Constants
      self.TAP_THRESHOLD = 1.0     # Max duration for a "tap" (seconds)
      self.DOUBLE_TAP_GAP = 1.0    # Max time between taps (seconds)
      
      # State tracking
      self.lock = threading.Lock()
      self.touch_start_time = 0.0
      self.last_detach_time = 0.0
      self.is_drag_active = False
      self.tap_count = 0
      
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

      self.get_logger().info('Full Touchpad Emulation (Taps & Double-Clicks) Active')

   def state_callback(self, msg):
      """
      Track state changes for touch detection and double-tap recognition
      
      State machine:
      - touch: Start of touch sequence (sensor contact)
      - detach: Release touch (sensor uncontact)
      """
      state = msg.data
      now = time.time()
      
      with self.lock:
         if state == 'touch':
            self.touch_start_time = now
            time_since_last = now - self.last_detach_time
            
            # If we touch again quickly, it's either a second tap or a drag
            if time_since_last < self.DOUBLE_TAP_GAP:
               self.is_drag_active = True
            else:
               self.tap_count = 0 # Reset tap sequence if gap is too long
               self.is_drag_active = False

         elif state == 'detach':
            duration = now - self.touch_start_time
            self.last_detach_time = now
            
            # If the touch was brief, it's a "Tap"
            if duration < self.TAP_THRESHOLD:
               self.tap_count += 1
               
               if self.tap_count == 1:
                  # Register a single click
                  self.get_logger().info('Single Tap Click')
                  self._fire_instant_click()
               elif self.tap_count == 2:
                  # Register a double click
                  self.get_logger().info('Double Tap Click')
                  self._fire_instant_click()
                  self._fire_instant_click()
                  self.tap_count = 0 # Reset
            
            self.is_drag_active = False

   def _fire_instant_click(self):
      """Sends a momentary click-down and click-up packet."""
      # Send press (dx=0, dy=0, click=1)
      self.sock.sendto(struct.pack("<iiB", 0, 0, 1), self.addr)
      time.sleep(0.02) # Shortest possible physical click duration
      # Send release (dx=0, dy=0, click=0)
      self.sock.sendto(struct.pack("<iiB", 0, 0, 0), self.addr)

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
         
         scaler = 20.0

         # Step 3: Scale by 1000 (convert from m to mm)
         vel_scaled = vel_rotated * 1000.0 * scaler

         # Step 4: Convert to integers for socket transmission
         dx = int(np.round(vel_scaled[0]))
         dy = int(np.round(vel_scaled[1]))
         
         # Step 5: Send via socket
         # If we are in drag mode, keep the click high while moving
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