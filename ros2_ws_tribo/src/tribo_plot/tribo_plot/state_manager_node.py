#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String, Float32
import numpy as np
import threading

class StateManagerNode(Node):
    """
    Manages sensor buffer, state transitions, and publishes window data when ready.
    Runs at sensor frequency (1.2ms = ~833Hz)
    """
    
    def __init__(self):
        super().__init__('state_manager_node')
        
        # Subscribers
        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/sensorT', # '/sensorT' for real sensor data, '/sensorT_fake' for mock data
            self.sensor_callback,
            10
        )
        
        # Publishers
        self.state_pub = self.create_publisher(String, '/tribo/state', 10)
        self.touch_metric_pub = self.create_publisher(Float32, '/tribo/touch_metric', 10)
        self.window_pub = self.create_publisher(Float32MultiArray, '/tribo/window_buffer', 10)
        self.touch_pose_pub = self.create_publisher(Float32MultiArray, '/tribo/touch_pose', 10)
        
        # State management
        self.__state = 'idle'
        self.last_state = 'idle'
        self.update_pause_cnt = 0  # Counter to pause _update_state for 1000 timesteps
        
        # Buffers
        # self.buffer_size = 200  # Reduced from 1000 (200ms at 1kHz)
        self.window_size = 50
        self.window = np.zeros((4, self.window_size))
        self.window_cnt = 0
        self.touch_buffer = np.zeros((4, self.window_size))  # (4, 50) rolling buffer for metric_touch
        self.touch_max = np.zeros(4)  # Track max values during touch pause period
        
        # Threading and locking
        self.lock = threading.Lock()
        
        self.get_logger().info('StateManager Node initialized')
    
    @property
    def state(self):
        return self.__state
    
    @state.setter
    def state(self, value):
        if value not in ['idle', 'touch', 'stay', 'slide', 'detach']:
            raise ValueError(f"Invalid state: {value}")
        self.__state = value
    
    def sensor_callback(self, msg):
        """
        High-frequency callback: updates buffer, calculates metrics, manages state transitions
        Optimized: use circular indexing instead of np.roll
        """
        data = np.array(msg.data, dtype=np.float32)
        
        with self.lock:
            # Update touch_buffer using circular indexing for metric_touch
            touch_buffer_idx = (self.window_cnt if self.window_cnt < self.window_size else self.window_size - 1)
            # Actually, let's keep a rolling window in touch_buffer
            self.touch_buffer = np.roll(self.touch_buffer, -1, axis=1)
            self.touch_buffer[:, -1] = data
            
            # Track max values during pause period (500→100) for touch pose calculation
            if self.state == 'touch' and self.update_pause_cnt > 100 and self.update_pause_cnt <= 500:
                # Update touch_max with element-wise maximum
                self.touch_max = np.maximum(self.touch_max, data)
            elif self.state == 'touch' and self.update_pause_cnt == 100:
                touch_sum = np.sum(self.touch_max)
                if touch_sum > 0:  # Avoid division by zero
                    alpha = (self.touch_max[2] + self.touch_max[3]) / touch_sum
                    beta = (self.touch_max[0] + self.touch_max[3]) / touch_sum
                    touch_pose_msg = Float32MultiArray(data=[alpha, beta])
                    self.touch_pose_pub.publish(touch_pose_msg)
                    self.get_logger().info(f'TOUCH_POSE: alpha={alpha:.4f}, beta={beta:.4f}')
                # Reset touch_max
                self.touch_max = np.zeros(4)
            
            # Only increment window_cnt when in 'stay' or 'slide' state (after pause counter ends)
            current_state = self.state
            if current_state in ['stay', 'slide'] and self.window_cnt < self.window_size:
                self.window[:, self.window_cnt] = data
                self.window_cnt += 1
            
            # Decrement pause counter
            if self.update_pause_cnt > 0:
                self.update_pause_cnt -= 1
        
        # Calculate metrics (optimized)
        touch_metric = self.metric_touch()
        
        # Publish touch_metric
        touch_msg = Float32(data=touch_metric)
        self.touch_metric_pub.publish(touch_msg)
        
        # State machine (only if not paused)
        if self.update_pause_cnt == 0:
            self._update_state(touch_metric)

    
    def _update_state(self, touch_metric):
        """
        State transition logic
        """
        with self.lock:
            if self.state == 'idle':
                if touch_metric > 60:
                    self.state = 'touch'
                    self.update_pause_cnt = 500
            
            elif self.state == 'touch':
                # Automatically transition to stay after pause
                self.state = 'stay'
            
            elif self.state == 'stay' or self.state == 'slide':
                # Check for detach
                if touch_metric < -300:
                    self.state = 'detach'
                    self.update_pause_cnt = 500
                    # Reset window counter when detaching
                    self.window_cnt = 0
                    self.window[:] = 0

                elif self.window_cnt == self.window_size:
                    # Calculate slide metric locally
                    slide_metric = self.metric_slide()
                    # DEBUG
                    self.get_logger().info(f'slide_metric {slide_metric} {self.window_cnt}')
                    
                    # Determine if stay or slide
                    if slide_metric < 40: # 800: # 200 :# 40: # 30
                        new_state = 'stay'
                    else:
                        new_state = 'slide'
                    self._publish_window()
                    
                    # Update state and publish (handles stay→stay, stay→slide, slide→stay, slide→slide)
                    self.state = new_state
                    state_msg = String(data=self.state)
                    self.state_pub.publish(state_msg)
                    self.last_state = self.state  # Update last_state to prevent double publish
                    self.get_logger().info(f'STATE: {self.state} (window full)')
                    
                    # Reset window counter
                    self.window_cnt = 0
                    self.window[:] = 0

            elif self.state == 'detach':
                # Automatically transition to idle after pause
                self.state = 'idle'
        
        # Publish state change for: idle→touch, touch→stay, stay→detach, slide→detach, detach→idle
        if self.state != self.last_state:
            state_msg = String(data=self.state)
            self.state_pub.publish(state_msg)
            self.last_state = self.state
            self.get_logger().info(f'STATE: {self.state}')
    
    def _publish_window(self):
        """
        Publish the full window buffer for inference
        Note: Called from within _update_state which already holds self.lock
        """
        # with self.lock:
        window_copy = self.window.copy()
        msg = Float32MultiArray(data=window_copy.flatten().tolist())
        self.window_pub.publish(msg)
    
    def metric_touch(self):
        """
        Calculate touch metric: sum of all sensor values
        Optimized: faster vectorized operation
        """
        # with self.lock:
        #     data = self.buffer # self.buffer.copy()  # Use full buffer
        data = self.touch_buffer
        
        # Sum all 4 channels across all buffer points, take mean
        metric = np.mean(np.sum(data, axis=0))
        
        # Update touch_buffer if metric is significant
        # if metric > 20:
        #     with self.lock:
        #         # Circular copy of current window to touch_buffer
        #         self.touch_buffer[:] = self.window[:, :self.window_size]
        
        return metric
    
    def metric_slide(self):
        """
        Calculate slide metric: mean of absolute values
        Optimized: only calculated when window is full and state is stay/slide
        """
        # with self.lock:
            # data = self.window.copy() # TODO: .copy() fast?
        data = self.window
        
        # metric = np.mean(np.abs(np.mean(data, axis=0)))  # mean of abs((50,)) shape
        metric = np.sum(np.abs(np.mean(data, axis=0)))
        return metric
    
    def get_touch_buffer(self):
        """
        Get copy of touch buffer (for touch model inference)
        """
        with self.lock:
            return self.touch_buffer.copy()


def main(args=None):
    rclpy.init(args=args)
    node = StateManagerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
