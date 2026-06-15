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
  scripts/dataset_tf_broadcaster.py
  scripts/localization_output_recorder.py
  scripts/standard_output_republisher.py
  scripts/output_selector.py
  scripts/gnss_solution_replayer.py
  scripts/gps_quality_gate.py
  scripts/simple_gps_fusion_node.py
  scripts/rtklib_pos_to_csv.py
  scripts/graphgnss_to_csv.py
  scripts/path_from_csv.py
  scripts/evaluate_run.py
  scripts/summarize_robustness.py
  scripts/bag_clock_marker.py
  scripts/time_sync_monitor.py
  scripts/trajectory_analysis.py
  scripts/offline_rviz_paths.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch/ config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
