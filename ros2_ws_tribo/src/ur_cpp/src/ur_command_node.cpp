#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

class URCommandNode : public rclcpp::Node
{
public:
    URCommandNode(const std::string& file_index="01") : 
    Node("ur_command_node"), frequency_(20.0), current_index_(0), repeat_count_(0), max_repeats_(20)
    {
        publisher_ = this->create_publisher<std_msgs::msg::String>("/urscript_interface/script_command", 10);

        // Load the path data from the file
        std::string filename = "/home/kang/Documents/tribo-slide/data_collection/slide-shape/path_" + file_index + ".csv"; // Change the file Directory !!
        if (!loadPathData(filename)) {
            RCLCPP_ERROR(this->get_logger(), "Error loading path data.");
            rclcpp::shutdown();
            return;
        }
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(static_cast<int>(1000 / frequency_)),
            std::bind(&URCommandNode::publishCommand, this));
    }

private:
    bool loadPathData(const std::string &file_path) {
        std::ifstream file(file_path);
        if (!file.is_open()) {
            RCLCPP_ERROR(this->get_logger(), "Could not open the file: %s", file_path.c_str());
            return false;
        }
        std::string line;
        while (std::getline(file, line)) {
            path_data_.push_back(line);
        }
        file.close();
        return true;
    }

    void publishCommand() {
        if (current_index_ >= path_data_.size()) {
            
            repeat_count_++;
            // Check if we have reached the maximum number of repeats
            if (repeat_count_ >= max_repeats_) {
                RCLCPP_INFO(this->get_logger(), "All commands have been sent and repeated %d times.", max_repeats_);
                rclcpp::shutdown();
                return;
            }
            current_index_ = 0;
        }
        // Read the current line and convert it into a URScript command
        std::stringstream ss(path_data_[current_index_]);
        std::string substr;
        std::vector<std::string> values;

        while (std::getline(ss, substr, ',')) {
            values.push_back(substr);
        }
        if (values.size() == 6) {
            // Construct the URScript command // Check Velocity and Frequency !!!
            std::string command = "movep(p[" + values[0] + ", " + values[1] + ", " + values[2] +
                                  ", " + values[3] + ", " + values[4] + ", " + values[5] + 
                                  "], a=0.2, v=0.04)";
            auto message = std_msgs::msg::String();
            message.data = command;
            if (current_index_ == 0) {
                RCLCPP_INFO(this->get_logger(), "Sending URScript command... %d of %d", repeat_count_ + 1, max_repeats_);
            }
            
            publisher_->publish(message);

            current_index_++; //  Move to the next time step
        } else {
            RCLCPP_ERROR(this->get_logger(), "Invalid number of values in line %ld", current_index_ + 1);
        }
    }

    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    double frequency_;
    std::vector<std::string> path_data_;
    size_t current_index_;
    int repeat_count_; // To track the number of times the path has been repeated
    int max_repeats_;  // Maximum number of repetitions allowed
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);

    if (argc < 2) {
        std::cerr << "Usage: ros2 run ur_cpp ur_command_node <file_index>" << std::endl;
        return 1;
    }
    std::string file_index = argv[1];

    auto node = std::make_shared<URCommandNode>(file_index);
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
