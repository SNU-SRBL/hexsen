// #include "serial.h"
#include <thread>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"
#include "sensorcpp/serial.hpp"

class IMUPublisher : public rclcpp::Node {
public:
  IMUPublisher() : Node("imu_publisher"), ID_IMU("/dev/ttyUSB0"), baudrate(115200) {
    serialIMU = new sensorcpp::serial(ID_IMU, baudrate);

    // Thread for IMU reading using readIMU()
    serialIMU->serialWrite("<00cmf>");
    sleep(2);
    serialIMU->serialWrite("<01cmf>");
    sleep(2);
    serialIMU->serialWrite("<00caf>");
    sleep(2);
    serialIMU->serialWrite("<01caf>");
    sleep(2);
    serialIMU->serialWrite("<00cg>");
    sleep(2);
    serialIMU->serialWrite("<01cg>");
    sleep(2);

    serialIMU->serialWrite("<sof2>"); // ZYXW
    sleep(3);
    RCLCPP_INFO_ONCE(this->get_logger(), "====IMU sensor is started ===");
    t_serialIMU = std::thread(&sensorcpp::serial::readIMU, serialIMU);

    imu_publisher_ = this->create_publisher<std_msgs::msg::Float32MultiArray>("imu_data", 10);
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(4),
      std::bind(&IMUPublisher::publishIMUData, this)
    );

    // Threading case
    // thread t_serialIMU(&sensorcpp::serial::readIMU, serialIMU);
  }
  ~IMUPublisher() {
    serialIMU->stopReading();
    if (t_serialIMU.joinable()) {
      t_serialIMU.join();
    }
    delete serialIMU;
  }

private:
  void publishIMUData() {
    float imu_data[20];
    serialIMU->getData(imu_data);

    auto message = std_msgs::msg::Float32MultiArray();
    message.data.resize(20);

    // Fill in the message fields with imu_data
    for (size_t i = 0; i < 20; ++i) {
      message.data[i] = imu_data[i];
    }
    imu_publisher_->publish(message);
  }

  const char* ID_IMU;
  const int baudrate;
  sensorcpp::serial* serialIMU;
  std::thread t_serialIMU;
  rclcpp::Publisher<std_msgs::msg::Float32MultiArray>::SharedPtr imu_publisher_;
  rclcpp::TimerBase::SharedPtr timer_;

};  // End of IMUPublisher class


int main(int argc, char** argv){
    rclcpp::init(argc, argv);
    auto imu_publisher_node = std::make_shared<IMUPublisher>();
    rclcpp::spin(imu_publisher_node);
    rclcpp::shutdown();
    return 0;
}