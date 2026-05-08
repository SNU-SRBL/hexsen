#!/usr/bin/env python3
"""
Launch all three nodes for the distributed Tribo Slide application

Usage:
    ros2 launch tribo_plot tribo_app.launch.py

This will start:
    1. state_manager_node - manages sensor buffer and state transitions
    2. inference_node - runs ML model inference
    3. app_node - visualization and plotter
    4. sensorT_fake - fake sensor data publisher (for testing)
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # Fake sensor publisher (for testing/development)
        Node(
            package='tribo_plot',
            executable='sensorT_fake',
            name='sensor_fake',
            output='screen',
        ),
        
        # State Manager Node
        Node(
            package='tribo_plot',
            executable='state_manager',
            name='state_manager',
            output='screen',
        ),
        
        # Inference Node
        Node(
            package='tribo_plot',
            executable='inference',
            name='inference',
            output='screen',
        ),
        
        # Application/Plotter Node
        Node(
            package='tribo_plot',
            executable='app_node',
            name='app',
            output='screen',
        ),
    ])
