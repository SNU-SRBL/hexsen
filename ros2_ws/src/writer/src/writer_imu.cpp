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


// Mutex to protect global variables and timing
std::mutex data_mutex;
std::chrono::steady_clock::time_point g_start_time;
bool g_start_time_initialized = false;

void memo()
{
  // USELESS
} // memo()

class Writer : public rclcpp::Node
{
public:
  Writer()
  : Node("writer")
  {
    // Initialize start time with mutex protection
    {
      std::lock_guard<std::mutex> lock(data_mutex);
      g_start_time = std::chrono::steady_clock::now();
      g_start_time_initialized = true;
    }

    sensor_imu.open("/home/seunghoon/Documents/BYJ-hexsen/data/Log_Sensor_IMU_.txt");
    sensor_imu << "time,z,y,x,w,angvel_x,angvel_y,angvel_z,acc_x,acc_y,acc_z,"
               << "z,y,x,w,angvel_x,angvel_y,angvel_z,acc_x,acc_y,acc_z," << endl;

    subscription_imu_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "/imu_data", 10, std::bind(&Writer::imu_callback, this, std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(), "Writer node initialized...");
  }

  ~Writer()
  {
    if (sensor_imu.is_open()) {
      sensor_imu.close();
    }
  }

private:

  // Helper function to calculate elapsed time from start (must be called while holding data_mutex)
  double get_elapsed_time_unlocked()
  {
    if (!g_start_time_initialized) {
      return 0.0;
    }
    auto current_time = std::chrono::steady_clock::now();
    std::chrono::duration<double> elapsed = current_time - g_start_time;
    return elapsed.count();
  }

  void imu_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
  {
    if (msg->data.size() < 10) {
      return;
    }

    std::lock_guard<std::mutex> lock(data_mutex);

    double elapsed = get_elapsed_time_unlocked();

    sensor_imu << elapsed << ",";
    for (int i = 0; i < 20; ++i) {
      sensor_imu << msg->data[i] << ",";
    }
    sensor_imu << endl;
    sensor_imu.flush();
  }


  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_imu_;

  std::ofstream sensor_imu;

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

  // thread writer_thread(memo);
  thread print_thread(print_log);

  ros_thread.join();
  //writer_thread.join();
  print_thread.join();

  return 0;
}