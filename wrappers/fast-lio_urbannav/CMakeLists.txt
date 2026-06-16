cmake_minimum_required(VERSION 3.0.2)
project(fast_lio_urbannav)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  geometry_msgs
  nav_msgs
  tf2_ros
  tf2_geometry_msgs
  message_filters
  pcl_ros
  cv_bridge
  image_transport
)

catkin_package()

# Mark Python scripts as executable and install them
catkin_install_python(PROGRAMS
  scripts/urbannav_wrapper_node.py
  scripts/tf_broadcaster_node.py
  scripts/verify_topics.py
  scripts/bag_player.py
  scripts/ground_truth_path_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

# Install launch files
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)

# Install config files
install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
)
