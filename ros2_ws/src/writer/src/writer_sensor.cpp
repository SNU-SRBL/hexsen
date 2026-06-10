/*
 * 2024-07-10 Seunghoon Kang | Soft Robotics & Bionics Lab
 * Copyright (C) 2024 by SRBL, Seoul National University. All rights reserved.
 */

#include <memory>
#include <thread>
#include <mutex>
#include <chrono>
#include <fstream>
#include <iostream>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"

using namespace std;

#define sensorDataNum (6) // 6 voltages (CH1-CH6)

// Global variables for Sensor and Force
// float g_sensorData[sensorDataNum]; // [CH1, CH2, CH3, CH4, CH5, CH6]

// Mutex to protect global variables
std::mutex data_mutex;

class Writer : public rclcpp::Node
{
public:
  Writer()
  : Node("writer")
  {
    subscription_sensor_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "/sensor/data", 10, std::bind(&Writer::sensor_callback, this, std::placeholders::_1));
    
    sensor_file_.open("/home/seunghoon/Documents/BYJ-6axis/data/Log_Sensor_Hex_.txt");
    // start_time_ = std::chrono::steady_clock::now();
  }

  ~Writer()
  {
    if (sensor_file_.is_open()) {
      sensor_file_.close();
    }
  }

private:

  void sensor_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
  {
    // Sensor message format: [ard_micros, CH1, CH2, CH3, CH4, CH5, CH6]
    if (msg->data.size() >= sensorDataNum + 1) {

      // Log immediately when new data arrives
      // auto current_time = std::chrono::steady_clock::now();
      // auto elapsed_time = std::chrono::duration_cast<std::chrono::duration<double>>(current_time - start_time_).count();

      for (int i = 0; i < sensorDataNum + 1; ++i) {
        sensor_file_ << msg->data[i] << ",";
      }
      sensor_file_ << endl;
      sensor_file_.flush();
    }
  }

  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_sensor_;
  std::ofstream sensor_file_;
  // std::chrono::steady_clock::time_point start_time_;
};


int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto writer_node = std::make_shared<Writer>();
  rclcpp::spin(writer_node);
  rclcpp::shutdown();

  return 0;
}