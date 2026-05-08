import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import numpy as np

class SensorT_Publisher(Node):
    def __init__(self):
        super().__init__('sensorT_large_publisher')
        self.publisher_ = self.create_publisher(Float32MultiArray, 'sensorT_large', 10)
        timer_period = 0.0012 # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.count = 0

        self.data_size = 200  # Large data size # Try 10, 100, 300, 500, 1000

        self.msg = Float32MultiArray()
        self.msg.data = [0.0] * self.data_size

        self.buffer_len = 1024
        self.buffer = np.random.randint(
            0, 101, size=(self.buffer_len, self.data_size),
            dtype=np.int32
            )
        self.buf_idx = 0

    def timer_callback(self):
        row = self.buffer[self.buf_idx]

        # In-place update (NO new allocations)
        for i in range(self.data_size):
            self.msg.data[i] = float(row[i])

        self.publisher_.publish(self.msg)

        self.buf_idx = (self.buf_idx + 1) % self.buffer_len
        self.count += 1

def main(args=None):
    rclpy.init(args=args)
    node= SensorT_Publisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()