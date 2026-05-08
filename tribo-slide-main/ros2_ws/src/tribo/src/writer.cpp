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
#include "std_msgs/msg/string.hpp"
#include "tf2_msgs/msg/tf_message.hpp"
#include "sensor_msgs/msg/joint_state.hpp"
#include "std_msgs/msg/float32_multi_array.hpp"

#include "geometry_msgs/msg/pose_stamped.hpp"
#include "tf2_ros/transform_listener.h"
#include "tf2_ros/buffer.h"

using namespace std;

#define sensorDataNum (4)
const int robotArmPosDataNum = 7; // x, y, z, qx, qy, qz, qw
const int robotArmJPosDataNum = 6;

// Global variables for TF
double tr_x, tr_y, tr_z, r_x, r_y, r_z, r_w;

// Global variables for joint states
double robotArmPos[robotArmPosDataNum];
double robotArmJPos[robotArmJPosDataNum];

// Global variables for Sensor and Force
float g_sensorData[sensorDataNum];
float g_force[6];

// Mutex to protect global variables
std::mutex data_mutex;

void memo()
{
    ofstream robot_pos, robot_jpos, loadcell, sensor_T;
    robot_pos.open("/home/kang/Documents/tribo-slide/data_collection/data/Log_Robot_Pos_.txt");
    robot_jpos.open("/home/kang/Documents/trib-slide/data_collection/data/Log_Robot_JPos_.txt");
    sensor_T.open("/home/kang/Documents/tribo-slide/data_collection/data/Log_Sensor_T_.txt");
    loadcell.open("/home/kang/Documents/tribo-slide/data_collection/data/Log_Loadcell_.txt");
    
    double temp_robotArmPos[robotArmPosDataNum];
    double temp_robotArmJPos[robotArmJPosDataNum];
    float temp_sensorData[sensorDataNum];
    float temp_force[6];

    auto start_time = std::chrono::steady_clock::now();

    while (rclcpp::ok())
    {
      {
        std::lock_guard<std::mutex> lock(data_mutex);
        std::copy(begin(g_sensorData), end(g_sensorData), begin(temp_sensorData));
        std::copy(begin(robotArmPos), end(robotArmPos), begin(temp_robotArmPos));
        std::copy(begin(robotArmJPos), end(robotArmJPos), begin(temp_robotArmJPos));
        std::copy(begin(g_force), end(g_force), begin(temp_force));
      }
      auto current_time = std::chrono::steady_clock::now();
      auto elapsed_time = std::chrono::duration_cast<std::chrono::duration<double>>(current_time - start_time).count();

      robot_pos << elapsed_time << ",";
      for (int i = 0; i < robotArmPosDataNum; ++i) {robot_pos << temp_robotArmPos[i] << ",";} robot_pos << endl;

      robot_jpos << elapsed_time << ","
                << robotArmJPos[5] << ","
                << robotArmJPos[0] << "," 
                << robotArmJPos[1] << "," 
                << robotArmJPos[2] << "," 
                << robotArmJPos[3] << "," 
                << robotArmJPos[4] << "," << endl;
      /* ROS2 order is different
        name:
          - shoulder_lift_joint
          - elbow_joint
          - wrist_1_joint
          - wrist_2_joint
          - wrist_3_joint
          - shoulder_pan_joint
      */
      
      sensor_T << elapsed_time << ",";
      for (int i = 0; i < sensorDataNum; ++i) {sensor_T << temp_sensorData[i] << ",";} sensor_T << endl;

      loadcell << elapsed_time << ",";
      for (int i = 0; i < 6; ++i) {loadcell << temp_force[i] << ",";} loadcell << endl;

      
      // std::this_thread::sleep_for(std::chrono::milliseconds(1));
      std::this_thread::sleep_for(std::chrono::microseconds(1200));
    }
    robot_pos.close();
    robot_jpos.close();
    sensor_T.close();
    loadcell.close();
} // memo()

class Writer : public rclcpp::Node
{
public:
  Writer()
  : Node("writer"), tf_buffer_(this->get_clock()), tf_listener_(tf_buffer_)
  {
    subscription_joint_ = this->create_subscription<sensor_msgs::msg::JointState>(
        "/joint_states", 10, std::bind(&Writer::joint_callback, this, std::placeholders::_1));
    subscription_tf_ = this->create_subscription<tf2_msgs::msg::TFMessage>(
        "/tf", 10, std::bind(&Writer::tf_callback, this, std::placeholders::_1));
    subscription_sensor_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "sensorT", 10, std::bind(&Writer::sensor_callback, this, std::placeholders::_1));
    subscription_RFT_ = this->create_subscription<std_msgs::msg::Float32MultiArray>(
        "sensorRFT", 10, std::bind(&Writer::RFT_callback, this, std::placeholders::_1));
    
    timer_ = this->create_wall_timer(std::chrono::milliseconds(2), std::bind(&Writer::tf2_callback, this));
  }

private:
  void joint_callback(const sensor_msgs::msg::JointState::SharedPtr msg) const
  {
    // std::lock_guard<std::mutex> lock(data_mutex);
    if (msg->position.size() >= 6) {
      robotArmJPos[0] = msg->position[0];
      robotArmJPos[1] = msg->position[1];
      robotArmJPos[2] = msg->position[2];
      robotArmJPos[3] = msg->position[3];
      robotArmJPos[4] = msg->position[4];
      robotArmJPos[5] = msg->position[5];
    }
  }
  void tf_callback(const tf2_msgs::msg::TFMessage::SharedPtr msg) const
  {
    // std::lock_guard<std::mutex> lock(data_mutex);
    if (!msg->transforms.empty()) {
      auto transform = msg->transforms[0];
      tr_x = transform.transform.translation.x;
      tr_y = transform.transform.translation.y;
      tr_z = transform.transform.translation.z;
      r_x = transform.transform.rotation.x;
      r_y = transform.transform.rotation.y;
      r_z = transform.transform.rotation.z;
      r_w = transform.transform.rotation.w;
    }
  }
  void tf2_callback()
  {
    try
    {
        auto transform = tf_buffer_.lookupTransform("base", "tool0_controller", tf2::TimePointZero);
        robotArmPos[0] = transform.transform.translation.x; // x
        robotArmPos[1] = transform.transform.translation.y; // y
        robotArmPos[2] = transform.transform.translation.z; // z
        robotArmPos[3] = transform.transform.rotation.x; // qx
        robotArmPos[4] = transform.transform.rotation.y; // qy
        robotArmPos[5] = transform.transform.rotation.z; // qz
        robotArmPos[6] = transform.transform.rotation.w; // qw
    }
    catch (tf2::TransformException &ex)
    {
        RCLCPP_ERROR(get_logger(), "Could not transform: %s", ex.what());
    }
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

  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr subscription_joint_;
  rclcpp::Subscription<tf2_msgs::msg::TFMessage>::SharedPtr subscription_tf_;
  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_sensor_;
  rclcpp::Subscription<std_msgs::msg::Float32MultiArray>::SharedPtr subscription_RFT_;

  tf2_ros::Buffer tf_buffer_;
  tf2_ros::TransformListener tf_listener_;
  rclcpp::TimerBase::SharedPtr timer_;
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
    printf("robotPos: [%5.3f, %5.3f, %5.3f, %5.3f, %5.3f, %5.3f]\n",
    robotArmPos[0], robotArmPos[1], robotArmPos[2],
    robotArmPos[3], robotArmPos[4], robotArmPos[5]);
    // printf("robotJPos: [%5.3f, %5.3f, %5.3f, %5.3f, %5.3f, %5.3f]\n",
    // robotArmJPos[0], robotArmJPos[1], robotArmJPos[2],
    // robotArmJPos[3], robotArmJPos[4], robotArmJPos[5]);

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