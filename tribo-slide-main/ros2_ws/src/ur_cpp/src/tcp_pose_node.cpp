#include <rclcpp/rclcpp.hpp>
#include <tf2_ros/transform_listener.h>
#include <tf2_ros/buffer.h>
#include <geometry_msgs/msg/transform_stamped.hpp>

// Roll-Pitch-Yaw
// #include <tf2/LinearMath/Quaternion.h>
// #include <tf2/LinearMath/Matrix3x3.h>

class TcpPoseNode : public rclcpp::Node
{
public:
    TcpPoseNode()
        : Node("tcp_pose_node"), tf_buffer_(get_clock()), tf_listener_(tf_buffer_)
    {
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(2), std::bind(&TcpPoseNode::timerCallback, this));
    }

private:
    void timerCallback()
    {
        try
        {
            // Look up the transform from the robot base to the tool0 (TCP) frame
            auto tf = tf_buffer_.lookupTransform("base", "tool0_controller", tf2::TimePointZero);

            const auto &t = tf.transform.translation;
            const auto &p = tf.transform.rotation;
            
            // Translation
            double x = t.x;
            double y = t.y;
            double z = t.z;

            // Rotation (Quaternion)
            double qx = p.x;
            double qy = p.y;
            double qz = p.z;
            double qw = p.w;

            // Rotation (Roll-Pitch-Yaw)
            // tf2::Quaternion quat(p.x, p.y, p.z, p.w);
            // double roll, pitch, yaw;
            // tf2::Matrix3x3(quat).getRPY(roll, pitch, yaw);

            RCLCPP_INFO(this->get_logger(), "TCP Pose: Translation [%.5f, %.5f, %.5f], Rotation [%.5f, %.5f, %.5f, %.5f]",
                        x, y, z, qx, qy, qz, qw);
            // RCLCPP_INFO(this->get_logger(), "TCP Pose: Rotation(RPY) [%.5f, %.5f, %.5f]",
            //             roll, pitch, yaw); // Not Accurate !!
        }
        catch (const tf2::TransformException &ex)
        {
            RCLCPP_WARN(this->get_logger(), "Could not get TCP pose: %s", ex.what());
        }
    }

    tf2_ros::Buffer tf_buffer_;
    tf2_ros::TransformListener tf_listener_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<TcpPoseNode>());
    rclcpp::shutdown();
    return 0;
}
