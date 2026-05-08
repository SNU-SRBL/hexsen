cmake_minimum_required(VERSION 3.8)
project(writer)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(ur_rtde REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(geometry_msgs REQUIRED)

include_directories(${ur_rtde_INCLUDE_DIRS})

# Add the executable
add_executable(ur_rtde_node src/ur_rtde_node.cpp)
add_executable(writer_v2 src/writer_v2.cpp)
add_executable(writer_sensor src/writer_sensor.cpp)

# Link libraries
ament_target_dependencies(ur_rtde_node
  rclcpp
  std_msgs
)
ament_target_dependencies(writer_v2
  rclcpp
  std_msgs
)
ament_target_dependencies(writer_sensor
  rclcpp
  std_msgs
)

# target_link_libraries(ur_rtde_node ur_rtde::rtde)
# target_link_libraries(ur_rtde_node ur_rtde)
# target_link_libraries(ur_rtde_node ${ur_rtde_LIBRARIES})
target_link_libraries(ur_rtde_node rtde)

# Install the executable
install(TARGETS ur_rtde_node writer_v2 writer_sensor
  DESTINATION lib/${PROJECT_NAME}
)


ament_package()
