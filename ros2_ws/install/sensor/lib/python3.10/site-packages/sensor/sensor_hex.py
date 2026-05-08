import asyncio
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from bleak import BleakClient, BleakScanner
import struct
import threading
import time

# BLE Configuration
CHARACTERISTIC_UUID = "6f42123f-62f9-49cc-a61f-9043dcf7ea12"
DEVICE_NAME = "NanoSense_ADS1256"
TARGET = "05:07:99:8D:11:B9"

# ADS1256 Conversion Constants
ADS1256_VREF = 2.5
MAX_24BIT_VAL = 8388607.0  # 2^23 - 1 for signed 24-bit

class SensorPublisher(Node):
    def __init__(self):
        super().__init__('sensor_6axis_publisher')
        self.publisher = self.create_publisher(Float32MultiArray, '/sensor/data', 10)
        self.ble_task = None
        self.loop = None
        self.client = None
        self.running = True

        self.first_arduino_time = None

    def publish_sensor_data(self, delta_seconds, i, voltages):
        """Publish 6 sensor values (without timestamp) as Float32MultiArray"""
        msg = Float32MultiArray()
        msg.data = [float(delta_seconds), float(i)] + [float(v) for v in voltages]
        self.publisher.publish(msg)
        self.get_logger().debug(f"Arduino µs: {delta_seconds} | Voltages: {[f'{v:.4f}' for v in voltages]}")

    def notification_handler(self, sender, data):
        """Handle BLE notifications"""
        if len(data) != 224:
            return

        for i in range(8):
            offset = i * 28
            sample_data = struct.unpack_from('<I6i', data, offset)

            ard_micros = sample_data[0]
            raw_adc = sample_data[1:7]

            if self.first_arduino_time is None:
                self.first_arduino_time = ard_micros

            delta_seconds = (ard_micros - self.first_arduino_time) / 1000000.0
            # formatted_time = f"{delta_seconds:.6f}"

            # Convert raw ADC values to voltages
            voltages = [(val / MAX_24BIT_VAL) * (2 * ADS1256_VREF) for val in raw_adc]

            # Clamp voltages to valid range
            # voltages = [max(-5.0, min(5.0, v)) for v in voltages]

            # Publish the data
            self.publish_sensor_data(delta_seconds, i, voltages)
            time.sleep(0.003) # sleep for 3 ms

    async def run_ble(self):
        """BLE connection and notification handling"""
        self.get_logger().info(f"Scanning for {DEVICE_NAME} ({TARGET})...")
        devices = await BleakScanner.discover(timeout=10.0)

        device = None
        if not devices:
            self.get_logger().info("No devices found.")
            return

        for d in devices:
            self.get_logger().info(f"Found device: {d.name} ({d.address})")
            if d.address == TARGET:
                device = d
                self.get_logger().info(f"Found target device: {device.name} ({device.address})")
                break

        if not device:
            self.get_logger().error(f"Could not find {DEVICE_NAME}.")
            return

        self.get_logger().info(f"Found {DEVICE_NAME}. Connecting...")
        
        try:
            self.client = BleakClient(device)
            await self.client.connect()
            self.get_logger().info("=== Connected to BLE device!")
            await self.client.start_notify(CHARACTERISTIC_UUID, self.notification_handler)
            self.get_logger().info("=== Listening for notifications...")
            
            # Keep the connection alive while running is True
            while self.running:
                await asyncio.sleep(0.1)
            
            await self.client.stop_notify(CHARACTERISTIC_UUID)
            await self.client.disconnect()
            
        except Exception as e:
            self.get_logger().error(f"BLE connection error: {e}")

    def start_ble_thread(self):
        """Start BLE in a separate thread"""
        def run_async_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self.run_ble())
            except KeyboardInterrupt:
                pass
            except Exception as e:
                self.get_logger().error(f"BLE thread error: {e}")
            finally:
                self.loop.close()

        ble_thread = threading.Thread(target=run_async_loop, daemon=False)
        ble_thread.start()

def main():
    rclpy.init()
    node = SensorPublisher()
    
    # Start BLE connection in background thread
    node.start_ble_thread()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down...")
        node.running = False
    finally:
        node.running = False
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()