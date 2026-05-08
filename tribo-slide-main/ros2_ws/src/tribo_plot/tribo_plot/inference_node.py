#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String, Float32
import numpy as np
import torch
import threading
import os
import joblib
import csv
import time
from datetime import datetime

from tribo_plot.model.lstm import TouchNetwork, SlideNetwork
from tribo_plot.model.mlstm_fcn import MLSTM_FCN


class InferenceNode(Node):
    """
    Runs ML inference on window data.
    - Subscribes to: /tribo/window_buffer, /tribo/state, /tribo/touch_metric
    - Publishes to: /tribo/velocity
    - Only processes data when state is 'stay' or 'slide' (or needs touch inference)
    """
    
    def __init__(self):
        super().__init__('inference_node')
        
        # Load models
        # self.touchmodel = TouchNetwork()
        self.slidemodel = MLSTM_FCN()

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.slidemodel.to(self.device)

        # Load pretrained weights
        model_dir = './src/tribo_plot/tribo_plot/model/'
        ckpt_path = os.path.join(model_dir, 'model_ep_1000.pth')
        checkpoint = torch.load(ckpt_path, map_location=self.device, weights_only=False)
        self.slidemodel.load_state_dict(checkpoint['model_state_dict'])
        self.slidemodel.eval()

        # Load scalers
        self.scaler_X = joblib.load(os.path.join(model_dir, 'scaler_X.pkl'))
        self.scaler_y = joblib.load(os.path.join(model_dir, 'scaler_y.pkl'))

        # Model Warming up
        dummy_input = torch.zeros((1, 4, 50), dtype=torch.float32).to(self.device)
        with torch.no_grad():
            for _ in range(5):
                _ = self.slidemodel(dummy_input)
        self.get_logger().info('Models loaded and warmed up!!!!')
        
        # Pre-allocate buffers for real-time performance
        self._x_flat = np.empty((50, 4), dtype=np.float32)
        self._x_scaled = np.empty((50, 4), dtype=np.float32)
        self._x_tensor = torch.empty((1, 4, 50), dtype=torch.float32, device=self.device)
        
        # Current state
        self.current_state = 'idle'
        self.touch_metric = 0.0
        self.window_buffer = None
        self.touch_buffer = None
        
        # Subscribers
        self.state_sub = self.create_subscription(
            String,
            '/tribo/state',
            self.state_callback,
            10
        )
        
        self.window_sub = self.create_subscription(
            Float32MultiArray,
            '/tribo/window_buffer',
            self.window_callback,
            10
        )
        
        self.touch_metric_sub = self.create_subscription(
            Float32,
            '/tribo/touch_metric',
            self.touch_metric_callback,
            10
        )
        
        # Publisher
        self.velocity_pub = self.create_publisher(
            Float32MultiArray,
            '/tribo/velocity',
            10
        )
        
        # Logging setup for velocity data
        self.start_time = time.time()
        self.log_dir = '/home/kang/Documents/tribo-slide/data_collection/data/'
        os.makedirs(self.log_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file_path = os.path.join(self.log_dir, f'Log_Vel_{timestamp}.csv')
        self.csv_file = open(self.log_file_path, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['elapsed_time_ms', 'vel_x', 'vel_y'])
        self.csv_file.flush()
        self.get_logger().info(f'Velocity logging initialized: {self.log_file_path}')
        
        # Threading
        self.lock = threading.Lock()
        self.inference_thread = threading.Thread(
            target=self._inference_loop,
            daemon=True
        )
        self.inference_thread.start()
        
        self.get_logger().info('Inference Node initialized')
    
    def state_callback(self, msg):
        """Subscribe to state changes"""
        with self.lock:
            self.current_state = msg.data
    
    def touch_metric_callback(self, msg):
        """Subscribe to touch metric for touch state detection"""
        with self.lock:
            self.touch_metric = msg.data
    
    def window_callback(self, msg):
        """
        Receive window buffer when it's full
        Reshape from flat to (4, 50)
        """
        with self.lock:
            self.window_buffer = np.array(msg.data, dtype=np.float32).reshape(4, 50)
    
    def _inference_loop(self):
        """
        Inference loop - processes data when needed
        For 'stay'/'slide' states: runs when window is full (published by StateManager)
        For 'touch' state: would run on touch_buffer (can be triggered separately)
        """
        while rclpy.ok():
            with self.lock:
                state = self.current_state
                window_buf = self.window_buffer
                touch_metric = self.touch_metric
            
            # Process based on state
            if state == 'stay' or state == 'slide':
                if window_buf is not None:
                    # Check state to determine inference
                    if state == 'stay':
                        # Stay state: send zero velocity
                        vel = np.array([0.0, 0.0], dtype=np.float32)
                    else:  # state == 'slide'
                        # Slide state: run inference
                        vel = self._infer_slide(window_buf, state)
                    
                    if vel is not None:
                        self._publish_velocity(vel)
                    
                    # Clear buffer after processing
                    with self.lock:
                        self.window_buffer = None
            
            elif state == 'touch':
                # Touch state: infer touch location
                # You can trigger this based on a separate message or timeout
                pass
            
            # Prevent busy-waiting
            rclpy.spin_once(self, timeout_sec=0.001)
    
    def _infer_slide(self, window_data, state):
        """
        Run slide inference - optimized for real-time performance
        Input: (4, 50) window
        Output: (2,) velocity
        Uses pre-allocated buffers to avoid repeated memory allocation

        (N, C, T) = (N, 4, 50)
        → transpose → (N, 50, 4)
        → flatten  → (N*T, 4)
        → StandardScaler
        → reshape  → (N, 50, 4)
        → transpose → (N, 4, 50)
        """
        try:
            # Prepare input - reuse pre-allocated buffers
            assert window_data.shape == (4, 50)
            self._x_flat[:] = window_data.T  # (50, 4)
            
            # Scale features in-place
            self._x_scaled[:] = self.scaler_X.transform(self._x_flat)  # (50, 4)
            
            # Reshape to (1, 4, 50) by copying to pre-allocated tensor on GPU
            self._x_tensor[0] = torch.from_numpy(self._x_scaled.T).to(self.device) # (1, 4, 50)

            # Inference
            with torch.no_grad():
                y_scaled = self.slidemodel(self._x_tensor)  # (1, 2)
            
            # Convert back and inverse scale
            y_scaled_np = y_scaled.detach().cpu().numpy()
            y = self.scaler_y.inverse_transform(y_scaled_np)  # Inverse scale
            vel = y.flatten()  # (2,)
            
            self.get_logger().debug(f'Slide inference: vel={vel}, state={state}')
            return vel
        
        except Exception as e:
            self.get_logger().error(f'Error in slide inference: {e}')
            return None
    
    def _infer_touch(self, touch_data):
        """
        Run touch inference
        Input: (4, 1000) buffer
        Output: (2,) pose
        """
        try:
            # Prepare input
            input_arr = touch_data.reshape(1, 4, 1000).astype(np.float32)
            input_tensor = torch.from_numpy(input_arr)
            
            # Inference
            # with torch.no_grad():
            #     pose = self.touchmodel(input_tensor)  # (1, 2)
            
            pose = pose.detach().numpy().flatten()  # (2,)
            
            self.get_logger().debug(f'Touch inference: pose={pose}')
            return pose
        
        except Exception as e:
            self.get_logger().error(f'Error in touch inference: {e}')
            return None
    
    def _publish_velocity(self, vel):
        """
        Publish velocity result (or pose)
        vel/pose: (2,) numpy array
        """
        msg = Float32MultiArray(data=vel.tolist())
        self.velocity_pub.publish(msg)
        
        # Log velocity with elapsed time
        elapsed_ms = (time.time() - self.start_time) * 1000
        self.csv_writer.writerow([f'{elapsed_ms:.2f}', f'{vel[0]:.6f}', f'{vel[1]:.6f}'])
        self.csv_file.flush()
    
    def __del__(self):
        """Clean up resources when node is destroyed"""
        try:
            if hasattr(self, 'csv_file') and self.csv_file:
                self.csv_file.close()
                self.get_logger().info(f'Velocity log file closed: {self.log_file_path}')
        except Exception as e:
            print(f'Error closing CSV file: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = InferenceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
