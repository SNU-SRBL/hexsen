
# Sensor Callback - updates main buffer, passes new data to plotter, state manager
# StateManager - decides state, manages event flag
# Machine Loop - window, runs ML, updates plotter trajectory
# Plotter

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import numpy as np
import threading
import time

import torch

from PyQt5 import QtWidgets
from tribo_plot.utils.widget import AppPlotter
from tribo_plot.utils.state import StateManager
from tribo_plot.model.models import TouchNetwork, SlideNetwork

class AppNode(Node):
    def __init__(self, plotter):
        super().__init__('app1_node')
        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/sensorT_fake',
            self.sensor_callback,
            10
        )

        self.lock = threading.Lock()
        self.buffer_size = 1000    # Store 1 seconds * 1000 Hz
        self.window_size = 50      # 50 timesteps (ML window) (non-overlapping)
        self.buffer = np.zeros((4, self.buffer_size))
        self.window = np.zeros((4, self.window_size))
        self.window_cnt = 0

        self.touchmodel = TouchNetwork()
        self.slidemodel = SlideNetwork()

        self.plotter = plotter
        self.sm = StateManager() # STATE: idle, touch, stay, slide, detach

        self.machine_thread = threading.Thread(target=self.machine_loop, daemon=True)
        self.machine_thread.start()

    def sensor_callback(self, msg):
        # self.get_logger().info(f'Received: {msg.data}')
        data = np.array(msg.data)
        with self.lock:
            # 1. Main buffer rolling for history
            self.buffer = np.roll(self.buffer, -1, axis=1)
            self.buffer[:, -1] = data

            # 2. Callback with copy (last 200 frames)
            self.sm.callback(self.buffer) # self.buffer[:,-200:].copy()

            # 3. Non-overlapping ML window: fill sequentially
            if self.window_cnt < self.window_size:
                self.window[:, self.window_cnt] = data
                self.window_cnt += 1
            
            # 4. Pass to plotter (or let plotter read buffer directly)
            self.plotter.callback(data)
            
            # CHECK ELAPSED TIME!!!

    def machine_loop(self):
        while rclpy.ok():

            with self.lock:
                data_window = self.window.copy()
                state = self.sm.state

            if state == 'idle':
                if self.sm.metric_touch() > 150:
                    self.sm.state = 'touch'

            elif state =='touch':
                input_arr = self.sm.touch_buffer.copy()
                input_arr = input_arr.reshape(1, 4, 1000).astype(np.float32)
                input_tensor = torch.from_numpy(input_arr)
                pose = self.touchmodel(input_tensor) # (1, 2)
                pose = pose.detach().numpy
                self.plotter.pose = pose
                # self.sm.event = 1 # Turn on
                time.sleep(0.4) # 1 second
                with self.lock:
                    self.window_cnt = 0
                    self.window[:] = 0

                self.sm.state = 'stay'
                
            elif state == 'stay' or state == 'slide':
                metric1 = self.sm.metric_touch()
                if metric1 < -150:
                    self.sm.state = 'detach'
                    # continue
                elif metric1 > 150:
                    # self.sm.state = 'touch'
                    pass
                else:
                    # Only act if a window is full
                    if self.window_cnt == self.window_size:
                        with self.lock:
                            self.window_cnt = 0
                            self.window[:] = 0
                        if self.sm.metric_slide(data_window) < 20:
                            vel = np.zeros((2,))
                            self.plotter.trajectory = np.vstack([self.plotter.trajectory, vel])
                            self.sm.state = 'stay'
                        else:
                            input_arr = data_window.copy()
                            input_arr = input_arr.reshape(1, 4, 50).astype(np.float32)
                            input_tensor = torch.from_numpy(input_arr)
                            vel = self.slidemodel(input_tensor) # (1, 2)
                            vel = vel.detach().numpy()
                            self.plotter.trajectory = np.vstack((self.plotter.trajectory, vel))
                            self.sm.state = 'slide'
            else: # state == 'detach'
                self.plotter.reset()
                self.sm.state = 'idle'
            # plot state  
            if state != self.sm.state:
                print(f'STATE: {self.sm.state}')
            # time.sleep(0.001) # To reduce CPU use

    # TODO
    # Buffer Check & Lock Check

def main(args=None):
    rclpy.init(args=args)
    app = QtWidgets.QApplication([])
    plotter = AppPlotter()

    node = AppNode(plotter)
    node_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    node_thread.start()

    plotter.show()
    app.exec()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()