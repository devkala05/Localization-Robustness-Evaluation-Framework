cmake_minimum_required(VERSION 3.0.2)
project(orbslam3_e2o)
find_package(catkin REQUIRED COMPONENTS geometry_msgs nav_msgs rospy sensor_msgs std_msgs tf2_ros)
catkin_package()
catkin_install_python(PROGRAMS
  scripts/run_orbslam3_native.py
  scripts/pose_republisher_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
install(DIRECTORY launch/ config/ DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
