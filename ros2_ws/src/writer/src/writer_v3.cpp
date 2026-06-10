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
#define forceDataNum (6)   // 6 forces (FX, FY, FZ, RX, RY, RZ)
const int robotArmPosDataNum = 6; // x, y, z, r, p, y
const int robotArmJPosDataNum = 6;

// Global variables for TF
double tr_x, tr_y, tr_z, r_x, r_y, r_z, r_w;

// Global variables for joint states
double robotArmPos[robotArmPosDataNum];
// double robotArmJPos[robotArmJPosDataNum];

// Global variables for Sensor and Force
float g_sensorData[sensorDataNum]; // [CH1, CH2, CH3, CH4, CH5, CH6]
float g_force[forceDataNum]; // [FX, FY, FZ, RX, RY, RZ]

// Mutex to protect global variables
std::mutex data_mutex;

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
    robot_pos.open("/home/seunghoon/Documents/BYJ-6axis/data/Log_Robot_Pos_.txt");
    sensor_T.open("/home/seunghoon/Documents/BYJ-6axis/data/Log_Sensor_Hex_.txt");
    robot_ft.open("/home/seunghoon/Documents/BYJ-6axis/data/Log_Robot_Force_.txt");
    robot_pos << "time,x,y,z,r,p,y," << endl; // Header for robot position data
    sensor_T << "time,CH1,CH2,CH3,CH4,CH5,CH6," << endl; // Header for sensor data
    robot_ft << "time,FX,FY,FZ,RX,RY,RZ," << endl; // Header for robot force data

    subscription_tcp_pose_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "/ur_rtde/tcp_pose", 10, std::bind(&Writer::tcp_pose_callback, this, std::placeholders::_1));
    subscription_tcp_force_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "/ur_rtde/tcp_force", 10, std::bind(&Writer::tcp_force_callback, this, std::placeholders::_1));
    subscription_sensor_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "/sensor/data", 10, std::bind(&Writer::sensor_callback, this, std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(), "Writer node initialized...");
  }

  ~Writer()
  {
    if (sensor_T.is_open()) {
      sensor_T.close();
      robot_pos.close();
    }
  }

private:

  void tcp_pose_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
  {
    std::lock_guard<std::mutex> lock(data_mutex);

    if (msg->data.size() >= robotArmPosDataNum) {
      for (int i = 0; i < robotArmPosDataNum; ++i) {
        robotArmPos[i] = msg->data[i];
      }
    }
  }

  void tcp_force_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
  {
    std::lock_guard<std::mutex> lock(data_mutex);

    if (msg->data.size() >= forceDataNum) {
      for (int i = 0; i < forceDataNum; ++i) {
        g_force[i] = msg->data[i];
      }
    }
  }

  void sensor_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
  {
    std::lock_guard<std::mutex> lock(data_mutex);
    std::copy(begin(robotArmPos), end(robotArmPos), begin(temp_robotArmPos));
    std::copy(begin(g_force), end(g_force), begin(temp_robotForce));

    // Sensor message format: [ard_micros, CH1, CH2, CH3, CH4, CH5, CH6]
    
    if (msg->data.size() >= sensorDataNum + 1) {
      elapsed_time = msg->data[0]; // ard_micros
      for (int i = 0; i < sensorDataNum + 1; ++i) {
        sensor_T << msg->data[i] << ",";
      }
      sensor_T << endl;
      sensor_T.flush();

      robot_pos << elapsed_time << ",";
      for (int i = 0; i < robotArmPosDataNum; ++i) {
        robot_pos << temp_robotArmPos[i] << ",";
      }
      robot_pos << endl;
      robot_pos.flush();      

      robot_ft << elapsed_time << ",";
      for (int i = 0; i < forceDataNum; ++i) {
        robot_ft << temp_robotForce[i] << ",";
      }
      robot_ft << endl;
      robot_ft.flush();
    }
  }

  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_tcp_pose_;
  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_tcp_force_;
  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_sensor_;

  std::ofstream robot_pos, sensor_T, robot_ft;

  double elapsed_time;

  double temp_robotArmPos[robotArmPosDataNum];
  float temp_sensorData[sensorDataNum];
  float temp_robotForce[forceDataNum];
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