cmake_minimum_required(VERSION 3.0.2)
project(e2o_localization_fusion)

find_package(catkin REQUIRED COMPONENTS
  diagnostic_msgs
  geometry_msgs
  nav_msgs
  rospy
  sensor_msgs
  std_msgs
  tf2_ros
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/fusion_math.py
  scripts/localization_health_monitor.py
  scripts/fusion_node.py
  scripts/cmd_vel_safety_gate.py
  scripts/multi_trajectory_recorder.py
  scripts/pose_fault_injector.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/ config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
