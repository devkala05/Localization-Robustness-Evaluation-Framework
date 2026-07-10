cmake_minimum_required(VERSION 3.0.2)
project(floam_e2o)

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  nav_msgs
  rospy
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/initial_pose_publisher.py
  scripts/odometry_alias_node.py
  scripts/odometry_path_node.py
  scripts/odometry_tf_broadcaster.py
  scripts/trajectory_recorder.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
