#!/usr/bin/env python3
# Refactored App Node - focuses on visualization only
# StateManager Node - handles buffering and state transitions
# Inference Node - handles ML model inference

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
import numpy as np
import threading

from PyQt5 import QtWidgets
from tribo_plot.utils.widget import AppPlotter


class AppNode(Node):
    """
    Main application node - visualizes trajectory and state
    Subscribes to: /tribo/velocity, /tribo/state
    """
    
    def __init__(self, plotter):
        super().__init__('app_node')
        
        self.plotter = plotter
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
        
        self.sensor_sub = self.create_subscription(
            Float32MultiArray,
            '/sensorT', # '/sensorT' for real sensor data, '/sensorT_fake' for mock data
            self.sensor_callback,
            10
        )
        
        self.touch_pose_sub = self.create_subscription(
            Float32MultiArray,
            '/tribo/touch_pose',
            self.touch_pose_callback,
            10
        )
        
        self.get_logger().info('App Node initialized')
    
    def velocity_callback(self, msg):
        """
        Receive velocity output from inference node
        msg.data: [vx, vy]
        """
        vel = np.array(msg.data, dtype=np.float32)
        
        with self.lock:
            # Add velocity to plotter (stacks and calculates cumulative trajectory)
            self.plotter.add_velocity(vel)
        
        self.get_logger().debug(f'Received velocity: {vel}')
    
    def state_callback(self, msg):
        """
        Receive state changes
        """
        state = msg.data
        
        with self.lock:
            self.plotter.update_state(state)
        
        # Set pose index at start of new touch sequence
        if state == 'touch':
            with self.lock:
                self.plotter.current_touch_idx = self.plotter.n_touch
        
        # Reset trajectory when detaching
        if state == 'idle':
            with self.lock:
                self.plotter.reset()
            self.get_logger().info('Reset plotter (detach/idle)')
        elif state == 'detach':
            with self.lock:
                self.plotter.add_touch()
    
    def sensor_callback(self, msg):
        """
        Receive sensor data and update plots
        msg.data: [sensor1, sensor2, sensor3, sensor4]
        """
        data = np.array(msg.data, dtype=np.float32)
        
        with self.lock:
            # Update sensor buffer and time series for visualization
            self.plotter.callback(data)
        
        self.get_logger().debug(f'Received sensor data: {data}')
    
    def touch_pose_callback(self, msg):
        """
        Receive touch pose (alpha, beta) from state manager
        msg.data: [alpha, beta] - normalized sensor coordinates
        """
        pose = np.array(msg.data, dtype=np.float32)
        with self.lock:
            # Update current touch pose in plotter
            self.plotter.set_touch_pose(pose)
        # self.get_logger().debug(f'Received touch pose: alpha={pose[0]:.4f}, beta={pose[1]:.4f}')


def main(args=None):
    rclpy.init(args=args)
    
    # Create PyQt5 application and plotter
    qt_app = QtWidgets.QApplication([])
    plotter = AppPlotter()
    
    # Create ROS2 node
    node = AppNode(plotter)
    
    # Spin ROS2 in separate thread
    ros_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()
    
    # Show plotter and run Qt event loop
    plotter.show()
    qt_app.exec()
    
    # Cleanup
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
