cmake_minimum_required(VERSION 3.8)
project(ur_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ur_rtde REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

include_directories(${ur_rtde_INCLUDE_DIRS})

# Add the executable
add_executable(tcp_pose_node src/tcp_pose_node.cpp)
add_executable(ur_command_node src/ur_command_node.cpp)
add_executable(ur_command_listener src/ur_command_listener.cpp)
add_executable(ur_rtde_node src/ur_rtde_node.cpp)

# Link libraries
ament_target_dependencies(tcp_pose_node
  rclcpp
  tf2
  tf2_ros
  geometry_msgs
)

ament_target_dependencies(ur_command_node
  rclcpp
  std_msgs
)

ament_target_dependencies(ur_command_listener
  rclcpp
  std_msgs
)

ament_target_dependencies(ur_rtde_node
  rclcpp
  std_msgs
)
# target_link_libraries(ur_rtde_node ur_rtde::rtde)
# target_link_libraries(ur_rtde_node ur_rtde)
# target_link_libraries(ur_rtde_node ${ur_rtde_LIBRARIES})
target_link_libraries(ur_rtde_node rtde)

# Install the executable
install(TARGETS tcp_pose_node ur_command_node ur_command_listener ur_rtde_node
  DESTINATION lib/${PROJECT_NAME}
)


ament_package()
