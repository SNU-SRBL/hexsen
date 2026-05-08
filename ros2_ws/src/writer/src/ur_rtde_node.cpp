#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32_multi_array.hpp>
#include <ur_rtde/rtde_control_interface.h>
#include <ur_rtde/rtde_receive_interface.h>

#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <memory>
#include <chrono>

using namespace ur_rtde;

class RTDECommandNode : public rclcpp::Node
{
public:
  explicit RTDECommandNode(const std::string& file_index="trajectory")
  : Node("rtde_command_node"), frequency_(50.0), current_index_(0), repeat_count_(0), max_repeats_(10)
  {
    // Parameters
    this->declare_parameter<std::string>("robot_ip", "192.168.10.2");
    this->declare_parameter<std::string>("file_dir",
      "/home/seunghoon/Documents/BYJ-6axis/data/basic"); // Adjust the default directory as needed !!
    const auto robot_ip = this->get_parameter("robot_ip").as_string();
    const auto file_dir = this->get_parameter("file_dir").as_string();
    RCLCPP_INFO(this->get_logger(), "Connecting to UR at: %s ...", robot_ip.c_str());

    // Connect to UR Robot
    try {
      rtde_control_ = std::make_shared<RTDEControlInterface>(robot_ip);
      rtde_receive_ = std::make_shared<RTDEReceiveInterface>(robot_ip);
      RCLCPP_INFO(this->get_logger(), "UR connection established");
    } catch (const std::exception& e) {
      RCLCPP_FATAL(this->get_logger(), "UR connection failed: %s", e.what());
      rclcpp::shutdown();
      return;
    }

    // Load the path data from the file
    std::string filename = file_dir + "/path_" + file_index + ".csv";

    if (!loadPathData(filename)) {
      RCLCPP_ERROR(this->get_logger(), "Error loading path data.");
      rclcpp::shutdown();
      return;
    }

    // Safely move to initial pose
    if (!moveToInitialPose()) {
      RCLCPP_ERROR(this->get_logger(), "Failed to move to initial pose.");
      rclcpp::shutdown();
      return;
    }

    // Create tcp publisher
    tcp_pub_ = this->create_publisher<std_msgs::msg::Float32MultiArray>(
      "/ur_rtde/tcp_pose", 10);
    
    auto period_pub = std::chrono::milliseconds(2); // 500 Hz
    tcp_timer_ = this->create_wall_timer(
      period_pub, std::bind(&RTDECommandNode::publishTcpPose, this));

    // Create command timer
    auto period_command = std::chrono::milliseconds(
      static_cast<int>(1000.0 / frequency_)); // 50 Hz -> 20 ms
    command_timer_ = this->create_wall_timer(
      period_command, std::bind(&RTDECommandNode::commandCallback, this));
    }

    ~RTDECommandNode() {
      RCLCPP_INFO(this->get_logger(), "Stopping RTDECommandNode");
      // if (rtde_control_) {
      //     rtde_control_->stopScript();
      // } // It makes robot stop abruptly !!
    }


private:

  bool loadPathData(const std::string& file_path) {
    std::ifstream file(file_path);
    if (!file.is_open()) {
      RCLCPP_ERROR(this->get_logger(), "Could not open the file: %s", file_path.c_str());
      return false;
    }
    std::string line;
    while (std::getline(file, line)) {
      if (!line.empty()) {
        path_data_.push_back(line);
        }
    }
    return true;
  }

  bool parsePose(const std::string& line, std::vector<double>& pose) {
    std::stringstream ss(line);
    std::string substr;
    pose.clear();
    while (std::getline(ss, substr, ',')) {
      try {
        pose.push_back(std::stod(substr));
      } catch (const std::invalid_argument& e) {
        RCLCPP_ERROR(this->get_logger(), "Error parsing pose data: %s", e.what());
        return false;
      }
    }
    return pose.size() == 6;
  }

  bool moveToInitialPose() {
    if (!rtde_receive_ || !rtde_control_) return false;
    std::vector<double> init_pose;
    if (!parsePose(path_data_.front(), init_pose)) {
      return false;
    }
    RCLCPP_INFO(this->get_logger(), "Moved to initial pose...");
    constexpr double speed = 0.05;
    constexpr double acceleration = 0.5;
    rtde_control_->moveL(init_pose, speed, acceleration);

    RCLCPP_INFO(this->get_logger(), "Robot moved to initial pose.");
    return true;
  }

  void commandCallback() {
    if (!rtde_receive_ || !rtde_control_) return;

    if (current_index_ >= path_data_.size()) {
      repeat_count_++;
      current_index_ = 0;
      // Check if we have reached the maximum number of repeats
      if (repeat_count_ >= max_repeats_) {
          RCLCPP_INFO(this->get_logger(), "Finished Path repeat %d times.", max_repeats_);
          rclcpp::shutdown();
          return;
      }
    }
    std::vector<double> target_pose;
    if (!parsePose(path_data_[current_index_], target_pose)) {
      current_index_++;
      return;
    }

    constexpr double speed = 0.05; // 0.10
    constexpr double acceleration = 0.5;
    const double dt = 1.0 / frequency_; // Must match timer: 1/50 = 0.02
    constexpr double lookahead = 0.1; // loadhead time
    constexpr double gain = 300.0;

    rtde_control_->servoL(
      target_pose,
      speed,
      acceleration,
      dt,
      lookahead,
      gain);

    if (current_index_ == 0) {
      RCLCPP_INFO(this->get_logger(), "Sending URScript command... %d of %d", repeat_count_ + 1, max_repeats_);
    }
    current_index_++; //  Move to the next time step
  }

  void publishTcpPose() {
    if (!rtde_receive_) return;

    std::vector<double> tcp = rtde_receive_->getActualTCPPose();
    auto message = std_msgs::msg::Float32MultiArray();
    message.data.resize(tcp.size());
    if (tcp.size() !=6) {
      RCLCPP_WARN(this->get_logger(), "Unexpected TCP pose size: %zu", tcp.size());
      return;
    }
    for (size_t i = 0; i < tcp.size(); ++i) {
      message.data[i] = static_cast<float>(tcp[i]);
    }
    tcp_pub_->publish(message);
  }


private:

  rclcpp::Publisher<std_msgs::msg::Float32MultiArray>::SharedPtr tcp_pub_;
  std::shared_ptr<RTDEControlInterface> rtde_control_;
  std::shared_ptr<RTDEReceiveInterface> rtde_receive_;
  rclcpp::TimerBase::SharedPtr command_timer_;
  rclcpp::TimerBase::SharedPtr tcp_timer_;

  double frequency_;
  std::vector<std::string> path_data_;
  size_t current_index_;
  int repeat_count_;  // To track the number of repeats
  int max_repeats_;   // Maximum number of repeats

};

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);

  std::string file_index = "trajectory"; // Default file index
  if (argc >= 2) {
    file_index = argv[1];
  } else {
    std::cerr << "Usage: ros2 run ur_cpp ur_rtde_node <file_index>" << std::endl;
  }

  auto node = std::make_shared<RTDECommandNode>(file_index);
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}