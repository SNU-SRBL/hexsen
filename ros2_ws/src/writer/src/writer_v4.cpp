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
#define imuDataNum (9) // 9 IMU data points (3 angular velocities, 3 accelerations, 3 magnetic fields)

const int robotArmPosDataNum = 6; // x, y, z, rx, ry, rz (rotation vector)
const int robotArmJPosDataNum = 6;

// Global variables for TF
double tr_x, tr_y, tr_z, r_x, r_y, r_z, r_w;

// Global variables for joint states
double robotArmPos[robotArmPosDataNum];
// double robotArmJPos[robotArmJPosDataNum];

// Global variables for Sensor, Force, and IMU data
float g_sensorData[sensorDataNum]; // [CH1, CH2, CH3, CH4, CH5, CH6]
float g_force[forceDataNum]; // [FX, FY, FZ, RX, RY, RZ]
float g_imuData[imuDataNum]; // [CH1, CH2, CH3, CH4, CH5, CH6, CH7, CH8, CH9]

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

    robot_pos.open("/home/seunghoon/Documents/BYJ-hexsen/data/Log_Robot_Pos_.txt");
    sensor_T.open("/home/seunghoon/Documents/BYJ-hexsen/data/Log_Sensor_Hex_.txt");
    robot_ft.open("/home/seunghoon/Documents/BYJ-hexsen/data/Log_Robot_Force_.txt");
    sensor_imu.open("/home/seunghoon/Documents/BYJ-hexsen/data/Log_Sensor_IMU_.txt");
    robot_pos << "time,x,y,z,rx,ry,rz," << endl; // Header for robot position data
    sensor_T << "time,ardtime,CH1,CH2,CH3,CH4,CH5,CH6,idx," << endl; // Header for sensor data
    robot_ft << "time,FX,FY,FZ,RX,RY,RZ," << endl; // Header for robot force data
    sensor_imu << "time,z,y,x,w,angvel_x,angvel_y,angvel_z,acc_x,acc_y,acc_z,"
               << "z,y,x,w,angvel_x,angvel_y,angvel_z,acc_x,acc_y,acc_z," << endl; // Header for IMU data

    subscription_tcp_pose_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "/ur_rtde/tcp_pose", 10, std::bind(&Writer::tcp_pose_callback, this, std::placeholders::_1));
    subscription_tcp_force_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "/ur_rtde/tcp_force", 10, std::bind(&Writer::tcp_force_callback, this, std::placeholders::_1));
    subscription_sensor_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "/sensor/data", 10, std::bind(&Writer::sensor_callback, this, std::placeholders::_1));
    subscription_imu_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "/imu_data", 10, std::bind(&Writer::imu_callback, this, std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(), "Writer node initialized...");
  }

  ~Writer()
  {
    if (sensor_T.is_open()) {
      sensor_T.close();
      robot_pos.close();
      robot_ft.close();
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

  void tcp_pose_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
  {
    if (msg->data.size() < robotArmPosDataNum) {
      return;
    }

    std::lock_guard<std::mutex> lock(data_mutex);
    
    double elapsed = get_elapsed_time_unlocked();

    // Copy force data
    std::copy(begin(g_force), end(g_force), begin(temp_robotForce));

    // Write robot position data
    robot_pos << elapsed << ",";
    for (int i = 0; i < robotArmPosDataNum; ++i) {
      robot_pos << msg->data[i] << ",";
    }
    robot_pos << endl;
    robot_pos.flush();

    // Write robot force data
    robot_ft << elapsed << ",";
    for (int i = 0; i < forceDataNum; ++i) {
      robot_ft << temp_robotForce[i] << ",";
    }
    robot_ft << endl;
    robot_ft.flush();
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
    // Sensor message format: [ard_micros, CH1, CH2, CH3, CH4, CH5, CH6, index]
    if (msg->data.size() < sensorDataNum + 2) {
      return;
    }

    std::lock_guard<std::mutex> lock(data_mutex);

    double elapsed = get_elapsed_time_unlocked();

    sensor_T << elapsed << ",";
    for (int i = 0; i < sensorDataNum + 2; ++i) {
      sensor_T << msg->data[i] << ",";
    }
    sensor_T << endl;
    sensor_T.flush();
  }

  void imu_callback(const std_msgs::msg::Float32MultiArray::SharedPtr msg)
  {
    if (msg->data.size() < 20) {
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

  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_tcp_pose_;
  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_tcp_force_;
  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_sensor_;
  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_imu_;

  std::ofstream robot_pos, sensor_T, robot_ft, sensor_imu;

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