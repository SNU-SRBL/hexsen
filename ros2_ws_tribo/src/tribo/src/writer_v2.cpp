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

#define sensorDataNum (4)
const int robotArmPosDataNum = 6; // x, y, z, r, p, y
const int robotArmJPosDataNum = 6;

// Global variables for TF
double tr_x, tr_y, tr_z, r_x, r_y, r_z, r_w;

// Global variables for joint states
double robotArmPos[robotArmPosDataNum];
// double robotArmJPos[robotArmJPosDataNum];

// Global variables for Sensor and Force
float g_sensorData[sensorDataNum];
float g_force[6];

// Mutex to protect global variables
std::mutex data_mutex;

void memo()
{
    ofstream robot_pos, loadcell, sensor_T; // Omit robot_jpos
    robot_pos.open("/home/kang/Documents/tribo-slide/data_collection/data/Log_Robot_Pos_.txt");
    sensor_T.open("/home/kang/Documents/tribo-slide/data_collection/data/Log_Sensor_T_.txt");
    loadcell.open("/home/kang/Documents/tribo-slide/data_collection/data/Log_Loadcell_.txt");
    
    double temp_robotArmPos[robotArmPosDataNum];
    float temp_sensorData[sensorDataNum];
    float temp_force[6];

    auto start_time = std::chrono::steady_clock::now();

    while (rclcpp::ok())
    {
      {
        std::lock_guard<std::mutex> lock(data_mutex);
        std::copy(begin(g_sensorData), end(g_sensorData), begin(temp_sensorData));
        std::copy(begin(robotArmPos), end(robotArmPos), begin(temp_robotArmPos));
        std::copy(begin(g_force), end(g_force), begin(temp_force));
      }
      auto current_time = std::chrono::steady_clock::now();
      auto elapsed_time = std::chrono::duration_cast<std::chrono::duration<double>>(current_time - start_time).count();

      robot_pos << elapsed_time << ",";
      for (int i = 0; i < robotArmPosDataNum; ++i) {robot_pos << temp_robotArmPos[i] << ",";} robot_pos << endl;
      
      sensor_T << elapsed_time << ",";
      for (int i = 0; i < sensorDataNum; ++i) {sensor_T << temp_sensorData[i] << ",";} sensor_T << endl;

      loadcell << elapsed_time << ",";
      for (int i = 0; i < 6; ++i) {loadcell << temp_force[i] << ",";} loadcell << endl;

      
      // std::this_thread::sleep_for(std::chrono::milliseconds(1));
      std::this_thread::sleep_for(std::chrono::microseconds(1200));
    }
    robot_pos.close();
    sensor_T.close();
    loadcell.close();
} // memo()

class Writer : public rclcpp::Node
{
public:
  Writer()
  : Node("writer")
  {
    subscription_tcp_pose_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "/ur_rtde/tcp_pose", 10, std::bind(&Writer::tcp_pose_callback, this, std::placeholders::_1));
    subscription_sensor_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "sensorT", 10, std::bind(&Writer::sensor_callback, this, std::placeholders::_1));
    subscription_RFT_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "sensorRFT", 10, std::bind(&Writer::RFT_callback, this, std::placeholders::_1));
    
  }

private:

  void tcp_pose_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
  {
    // std::lock_guard<std::mutex> lock(data_mutex);

    robotArmPos[0] = msg->data[0];
    robotArmPos[1] = msg->data[1];
    robotArmPos[2] = msg->data[2];
    robotArmPos[3] = msg->data[3];
    robotArmPos[4] = msg->data[4];
    robotArmPos[5] = msg->data[5];
  }
  void sensor_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
  {
    // std::lock_guard<std::mutex> lock(data_mutex);

    g_sensorData[0] = msg->data[0];
    g_sensorData[1] = msg->data[1];
    g_sensorData[2] = msg->data[2];
    g_sensorData[3] = msg->data[3];
  }
  void RFT_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
  {
    // std::lock_guard<std::mutex> lock(data_mutex);

    g_force[0] = msg->data[0];
    g_force[1] = msg->data[1];
    g_force[2] = msg->data[2];
    g_force[3] = msg->data[3];
    g_force[4] = msg->data[4];
    g_force[5] = msg->data[5];

  }

  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_tcp_pose_;
  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_sensor_;
  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_RFT_;

};


void print_log(){

  while (rclcpp::ok())
  {
    // std::lock_guard<std::mutex> lock(data_mutex);

    cout << "===============================" << endl << endl;
    printf("sensorT: [%6.2f, %6.2f, %6.2f, %6.2f]\n",
    g_sensorData[0], g_sensorData[1], g_sensorData[2], g_sensorData[3]);
    printf("loadcell: [%5.3f, %5.3f, %5.3f, %5.3f, %5.3f, %5.3f]\n",
    g_force[0], g_force[1], g_force[2], g_force[3], g_force[4], g_force[5]);
    printf("robotPos: [%5.3f, %5.3f, %5.3f, %5.3f, %5.3f]\n",
    robotArmPos[0], robotArmPos[1], robotArmPos[2],
    robotArmPos[3], robotArmPos[4]);

    std::this_thread::sleep_for(std::chrono::milliseconds(200));
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