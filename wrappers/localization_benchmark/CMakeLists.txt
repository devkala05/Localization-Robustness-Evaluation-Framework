cmake_minimum_required(VERSION 3.0.2)
project(localization_benchmark)

find_package(catkin REQUIRED COMPONENTS
  custom_localization_msgs
  geometry_msgs
  nav_msgs
  rospy
  rosgraph_msgs
  sensor_msgs
  std_msgs
  visualization_msgs
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/urbannav_custom_bridge.py
  scripts/custom_fastlio_adapter.py
  scripts/localization_output_recorder.py
  scripts/path_from_csv.py
  scripts/evaluate_run.py
  scripts/summarize_robustness.py
  scripts/bag_clock_marker.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/ config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
