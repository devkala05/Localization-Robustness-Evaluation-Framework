cmake_minimum_required(VERSION 3.0.2)
project(rtabmap_urbannav)

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  nav_msgs
  rospy
  sensor_msgs
  std_msgs
  tf
  tf2_ros
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/rtabmap_adapter_node.py
  scripts/rtabmap_output_adapter_node.py
  scripts/cloud_sanitizer_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/ config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
