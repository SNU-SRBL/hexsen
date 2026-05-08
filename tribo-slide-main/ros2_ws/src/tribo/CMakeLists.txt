cmake_minimum_required(VERSION 3.8)
project(tribo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(geometry_msgs REQUIRED)

add_executable(sensorT src/sensor_T.cpp)
ament_target_dependencies(sensorT rclcpp std_msgs)

add_executable(sensorRFT src/sensor_RFT.cpp)
ament_target_dependencies(sensorRFT rclcpp std_msgs)

add_executable(writer src/writer.cpp)
ament_target_dependencies(writer 
  rclcpp 
  std_msgs 
  sensor_msgs 
  tf2_msgs 
  tf2 
  tf2_ros 
  geometry_msgs
)

add_executable(writer_v2 src/writer_v2.cpp)
ament_target_dependencies(writer_v2 
  rclcpp 
  std_msgs 
)

install(TARGETS
  sensorT
  sensorRFT
  writer
  writer_v2
  DESTINATION lib/${PROJECT_NAME})
  
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch)

ament_package()