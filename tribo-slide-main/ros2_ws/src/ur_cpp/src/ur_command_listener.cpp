#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <string>

class URCommandListener : public rclcpp::Node
{
public:
    URCommandListener() : Node("ur_command_listener")
    {
        subscription_ = this->create_subscription<std_msgs::msg::String>(
            "/urscript_interface/script_command", 10,
            std::bind(&URCommandListener::commandCallback, this, std::placeholders::_1));
    }

private:
    void commandCallback(const std_msgs::msg::String::SharedPtr msg) const
    {
        RCLCPP_INFO(this->get_logger(), "Received URScript command: '%s'", msg->data.c_str());
    }

    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<URCommandListener>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
