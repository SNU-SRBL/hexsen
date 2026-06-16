// #include "serial.h"
#include <thread>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensorcpp/serial.hpp"

class IMUPublisher : public rclcpp::Node {
public:
  IMUPublisher() : Node("imu_publisher"), ID_IMU("/dev/ttyUSB0"), baudrate(115200) {
    serialIMU = new sensorcpp::serial(ID_IMU, baudrate);

    // Thread for IMU reading using readIMU()
    t_serialIMU = std::thread(&sensorcpp::serial::readIMU, serialIMU);

    imu_publisher_ = this->create_publisher<sensor_msgs::msg::Imu>("imu_data", 10);
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
    float imu_data[18];
    serialIMU->getData(imu_data);

    auto message = sensor_msgs::msg::Imu();
    
    // Fill in the message fields with imu_data
    message.linear_acceleration.x = imu_data[0];
    message.linear_acceleration.y = imu_data[1];
    message.linear_acceleration.z = imu_data[2];
    message.angular_velocity.x = imu_data[9];
    message.angular_velocity.y = imu_data[10];
    message.angular_velocity.z = imu_data[11];
    // message.magnetic_field.x = imu_data[6];
    // message.magnetic_field.y = imu_data[7];
    // message.magnetic_field.z = imu_data[8];
    imu_publisher_->publish(message);
  }

  const char* ID_IMU;
  const int baudrate;
  sensorcpp::serial* serialIMU;
  std::thread t_serialIMU;
  rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr imu_publisher_;
  rclcpp::TimerBase::SharedPtr timer_;

};  // End of IMUPublisher class


int main(int argc, char** argv){
    rclcpp::init(argc, argv);
    auto imu_publisher_node = std::make_shared<IMUPublisher>();
    rclcpp::spin(imu_publisher_node);
    rclcpp::shutdown();
    return 0;
}