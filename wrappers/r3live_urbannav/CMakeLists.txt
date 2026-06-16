cmake_minimum_required(VERSION 3.0.2)
project(r3live_urbannav)

find_package(catkin REQUIRED COMPONENTS rospy std_msgs sensor_msgs nav_msgs geometry_msgs tf2_ros)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/run_r3live_native.py
  scripts/trajectory_mux_node.py
  scripts/tf_broadcaster_node.py
  scripts/watchdog_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
