import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore  # Updated import
import numpy as np
import time
import threading


class SensorPlotter(Node):
    def __init__(self):
        super().__init__('sensor_plotter')

        # Data buffer
        self.data = np.zeros((4, 5000))
        self.time = np.linspace(-50, 0, 5000)
        self.start_time = time.time()

        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/sensorT',
            self.sensor_callback,
            10
        ) # /sensorT or /sensorT_fake

        # Start ROS2 spinning in a separate thread
        self.ros_thread = threading.Thread(target=rclpy.spin, args=(self,), daemon=True)
        self.ros_thread.start()

        # PyQtGraph setup (as before)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.app = QtWidgets.QApplication([])
        self.win = pg.GraphicsLayoutWidget(show=True, title="Sensor Data Plot")
        self.win.resize(800, 600)
        self.plot1 = self.win.addPlot()
        self.plot2 = self.win.addPlot(row=1, col=0)
        self.plot3 = self.win.addPlot(row=2, col=0)
        self.plot4 = self.win.addPlot(row=3, col=0)
        for i, plot in enumerate([self.plot1, self.plot2, self.plot3, self.plot4]):
            plot.setLabel('left', f'Data{i}')
            plot.setLabel('bottom', 'Time', units='s')
            plot.setYRange(-1000, 1000)
        self.curve1 = self.plot1.plot(pen='r', name = 'data 0')
        self.curve2 = self.plot2.plot(pen='g', name = 'data 1')
        self.curve3 = self.plot3.plot(pen='b', name = 'data 2')
        self.curve4 = self.plot4.plot(pen='m', name = 'data 3')

        # Timer for updating the plot
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(10)


    def sensor_callback(self, msg):
        # self.get_logger().info(f"Received message in tribo_plot: {msg}")
        sensor_value = np.array(msg.data)

        self.data = np.roll(self.data, -1, axis=1)
        self.data[:, -1] = sensor_value

    def update_plot(self):
        current_time = time.time() - self.start_time
        x = np.linspace(current_time - 50, current_time, 5000) # 50 seconds
        
        self.curve1.setData(self.time, self.data[0, :])
        self.curve2.setData(self.time, self.data[1, :])
        self.curve3.setData(self.time, self.data[2, :])
        self.curve4.setData(self.time, self.data[3, :])
        QtWidgets.QApplication.processEvents()

    def spin(self):
        self.app.exec_()

def main(args=None):
    rclpy.init(args=args)
    node = SensorPlotter()
    try:
        node.spin()  # Ensure this runs
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

