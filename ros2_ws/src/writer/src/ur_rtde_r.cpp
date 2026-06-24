#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32_multi_array.hpp>
#include <ur_rtde/rtde_receive_interface.h>

#include <memory>
#include <chrono>

using namespace ur_rtde;

class RTDEReceiveNode : public rclcpp::Node
{
public:
  explicit RTDEReceiveNode()
  : Node("rtde_receive_node")
  {
    // Parameters
    this->declare_parameter<std::string>("robot_ip", "192.168.10.2");
    const auto robot_ip = this->get_parameter("robot_ip").as_string();
    RCLCPP_INFO(this->get_logger(), "Connecting to UR at: %s ...", robot_ip.c_str());

    // Connect to UR Robot (receive only)
    try {
      rtde_receive_ = std::make_shared<RTDEReceiveInterface>(robot_ip);
      RCLCPP_INFO(this->get_logger(), "UR connection established (receive only)");
    } catch (const std::exception& e) {
      RCLCPP_FATAL(this->get_logger(), "UR connection failed: %s", e.what());
      rclcpp::shutdown();
      return;
    }

    // Create tcp publisher
    tcp_pub_ = this->create_publisher<std_msgs::msg::Float32MultiArray>(
      "/ur_rtde/tcp_pose", 10);
    ft_pub_ = this->create_publisher<std_msgs::msg::Float32MultiArray>(
      "/ur_rtde/tcp_force", 10);
    
    // Create timer for publishing TCP pose at 500 Hz
    auto period_pub = std::chrono::milliseconds(2);
    tcp_timer_ = this->create_wall_timer(
      period_pub, std::bind(&RTDEReceiveNode::publishTcpPose, this));
    
    RCLCPP_INFO(this->get_logger(), "RTDEReceiveNode started - Publishing TCP pose...");
  }

  ~RTDEReceiveNode() {
    RCLCPP_INFO(this->get_logger(), "Stopping RTDEReceiveNode");
  }

private:

  void publishTcpPose() {
    if (!rtde_receive_) return;

    std::vector<double> tcp = rtde_receive_->getActualTCPPose(); // X,Y,Z,RX,RY,RZ (Rotation vector)
    auto message = std_msgs::msg::Float32MultiArray();
    message.data.resize(tcp.size());

    std::vector<double> ft = rtde_receive_->getActualTCPForce();
    auto ft_message = std_msgs::msg::Float32MultiArray();
    ft_message.data.resize(ft.size());

    if (tcp.size() != 6 || ft.size() != 6) {
      RCLCPP_WARN(this->get_logger(), "Unexpected TCP pose size: %zu, FT size: %zu", tcp.size(), ft.size());
      return;
    }
    
    for (size_t i = 0; i < tcp.size(); ++i) {
      message.data[i] = static_cast<float>(tcp[i]);
      ft_message.data[i] = static_cast<float>(ft[i]);
    }
    
    tcp_pub_->publish(message);
    ft_pub_->publish(ft_message);
  }

private:

  rclcpp::Publisher<std_msgs::msg::Float32MultiArray>::SharedPtr tcp_pub_;
  rclcpp::Publisher<std_msgs::msg::Float32MultiArray>::SharedPtr ft_pub_;
  std::shared_ptr<RTDEReceiveInterface> rtde_receive_;
  rclcpp::TimerBase::SharedPtr tcp_timer_;

};

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<RTDEReceiveNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}