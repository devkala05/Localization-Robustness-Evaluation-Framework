cmake_minimum_required(VERSION 3.0.2)
project(rtabmap_benchmark)
find_package(catkin REQUIRED)
catkin_package()
catkin_install_python(PROGRAMS scripts/optimized_pose_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
install(DIRECTORY launch config DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
