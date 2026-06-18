cmake_minimum_required(VERSION 3.0.2)
project(fast_livo2_wrapper)

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
  visualization_msgs
)

catkin_package()

# ── Python scripts ────────────────────────────────────────────────────────────
catkin_install_python(PROGRAMS
  scripts/topic_bridge_node.py
  scripts/tf_broadcaster_node.py
  scripts/output_recorder_node.py
  scripts/trajectory_exporter.py
  scripts/bag_player.py
  scripts/verify_topics.py
  scripts/odometry_alias_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

# ── Launch files ──────────────────────────────────────────────────────────────
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)

# ── Config files ──────────────────────────────────────────────────────────────
install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
)
