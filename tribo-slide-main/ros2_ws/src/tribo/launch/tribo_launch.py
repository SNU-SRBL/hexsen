from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='tribo',  # Package name
            executable='writer',  # Executable name (binary from writer.cpp)
            name='writer',  # Optional name override
            output='screen'
        ),
        Node(
            package='tribo',
            executable='sensorT',  # Executable name (binary from sensor_T.cpp)
            name='sensorT_publisher',  # Optional name override
            output='screen'
        ),
        Node(
            package='tribo',
            executable='sensorRFT',  # Executable name (binary from sensor_RFT.cpp)
            name='sensorRFT_publisher',  # Matches the node name in the code
            output='screen'
        )
    ])
