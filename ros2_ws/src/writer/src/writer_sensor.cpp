/*
    2024-07-10 Seunghoon Kang | Soft Robotics & Bionics Lab
    Copyright (C) 2024 by SRBL, Seoul National University. All rights reserved.
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
float g_sensorData[sensorDataNum]; // [CH1, CH2, CH3, CH4, CH5, CH6]

// Mutex to protect global variables
std::mutex data_mutex;

void memo()
{
    ofstream sensor_T;
    sensor_T.open("/home/seunghoon/Documents/BYJ-6axis/data/Log_Sensor_Hex_.txt");

    float temp_sensorData[sensorDataNum];

    auto start_time = std::chrono::steady_clock::now();

    while (rclcpp::ok())
    {
      {
        // std::lock_guard<std::mutex> lock(data_mutex);
        std::copy(begin(g_sensorData), end(g_sensorData), begin(temp_sensorData));
      }
      
      auto current_time = std::chrono::steady_clock::now();
      auto elapsed_time = std::chrono::duration_cast<std::chrono::duration<double>>(current_time - start_time).count();
      
      // Log sensor data: elapsed_time, CH1, CH2, CH3, CH4, CH5, CH6
      sensor_T << elapsed_time << ",";
      for (int i = 0; i < sensorDataNum; ++i) {
        sensor_T << temp_sensorData[i] << ",";
      }
      sensor_T << endl;

      // std::this_thread::sleep_for(std::chrono::microseconds(1200));
      std::this_thread::sleep_for(std::chrono::milliseconds(5)); // 200 Hz
    }
    sensor_T.close();
} // memo()

class Writer : public rclcpp::Node
{
public:
  Writer()
  : Node("writer")
  {
    subscription_sensor_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "/sensor/data", 10, std::bind(&Writer::sensor_callback, this, std::placeholders::_1));
  }

private:

  void sensor_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
  {
    // std::lock_guard<std::mutex> lock(data_mutex);

    // Sensor message format: [ard_micros, CH1, CH2, CH3, CH4, CH5, CH6]
    if (msg->data.size() >= sensorDataNum) {
      for (int i = 0; i < sensorDataNum; ++i) {
        g_sensorData[i] = msg->data[i];
      }
    }
  }

  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_sensor_;
};


void print_log(){

  while (rclcpp::ok())
  {
    // std::lock_guard<std::mutex> lock(data_mutex);

    // cout << "===============================" << endl << endl;
    // printf("sensorH: [%7.4f, %7.4f, %7.4f, %7.4f, %7.4f, %7.4f] V\n",
    //   g_sensorData[0], g_sensorData[1], g_sensorData[2], 
    //   g_sensorData[3], g_sensorData[4], g_sensorData[5]);
    // printf("robotPos: [%6.4f, %6.4f, %6.4f, %6.4f, %6.4f, %6.4f]\n",
    //   robotArmPos[0], robotArmPos[1], robotArmPos[2],
    //   robotArmPos[3], robotArmPos[4], robotArmPos[5]);

    // std::this_thread::sleep_for(std::chrono::milliseconds(200));
  }
} // print_log()


int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto writer_node = std::make_shared<Writer>();
  thread ros_thread([&]() {
    rclcpp::spin(writer_node);
    rclcpp::shutdown();
  });

  thread writer_thread(memo);
  thread print_thread(print_log);

  ros_thread.join();
  writer_thread.join();
  print_thread.join();

  return 0;
}