
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import numpy as np

class SensorT_Publisher(Node):
    def __init__(self):
        super().__init__('sensorT_fake_publisher')

        self.publisher_ = self.create_publisher(Float32MultiArray, 'sensorT_fake', 10)
        timer_period = 0.0012 # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.count = 0
        self.offset_window_size  = 500

        # Load Sensor Data
        filename = "./src/tribo_plot/tribo_plot/data/Log_Sensor_T_.txt"
        try:
            raw = np.loadtxt(filename, delimiter=',', dtype=np.float32, usecols=(0, 1, 2, 3, 4))
        except Exception as e:
            self.get_logger().error(f'Error loading file {filename}: {e}')
            rclpy.shutdown()
            return
        
        self.data = raw[:, 1:5]   # shape (N, 4)
        offset = np.mean(self.data[:self.offset_window_size], axis=0)
        self.data -= offset # Zero offset

        self.length = self.data.shape[0]

        self.get_logger().info(
            f'Loaded {self.length} samples, offset={offset.tolist()}'
        )
    
        # Pre-allocate message
        self.msg = Float32MultiArray()
        self.msg.data = [0.0, 0.0, 0.0, 0.0]
    

    def timer_callback(self):
        if self.count >= self.length:
            self.get_logger().info('End of file reached.')
            self.timer.cancel()
            self.destroy_node()
            rclpy.shutdown()
            return

        row = self.data[self.count]
        self.msg.data[0] = float(row[0])
        self.msg.data[1] = float(row[1])
        self.msg.data[2] = float(row[2])
        self.msg.data[3] = float(row[3])
        self.publisher_.publish(self.msg)
        # self.get_logger().info(f'{self.msg.data}')
        self.count += 1

def main(args=None):
    rclpy.init(args=args)
    node= SensorT_Publisher()
    rclpy.spin(node)
    node.destropy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()