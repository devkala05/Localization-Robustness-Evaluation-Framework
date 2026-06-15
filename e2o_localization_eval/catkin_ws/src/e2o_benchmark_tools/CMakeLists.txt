cmake_minimum_required(VERSION 3.0.2)
project(e2o_benchmark_tools)

find_package(catkin REQUIRED COMPONENTS
  rospy
  sensor_msgs
  nav_msgs
  geometry_msgs
  tf
  tf2_ros
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/camera_info_sync_publisher.py
  scripts/static_tf_from_yaml.py
  scripts/ground_truth_publisher.py
  scripts/odom_pose_to_tum.py
  scripts/topic_health_monitor.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
