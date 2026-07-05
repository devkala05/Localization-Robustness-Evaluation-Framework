cmake_minimum_required(VERSION 3.0.2)
project(fast_livo2_e2o)
find_package(catkin REQUIRED COMPONENTS geometry_msgs nav_msgs rospy)
catkin_package()
catkin_install_python(PROGRAMS scripts/odometry_alias_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
install(DIRECTORY launch/ config/ DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
