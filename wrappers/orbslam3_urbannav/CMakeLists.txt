cmake_minimum_required(VERSION 3.0.2)
project(orbslam3_urbannav)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  geometry_msgs
  nav_msgs
  tf2_ros
  tf2_geometry_msgs
  message_filters
  cv_bridge
  image_transport
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/orbslam3_wrapper_node.py
  scripts/tf_broadcaster_node.py
  scripts/pose_republisher_node.py
  scripts/verify_topics.py
  scripts/bag_player.py
  scripts/check_stereo_timestamps.py
  scripts/run_orbslam3_native.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)

install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
)
