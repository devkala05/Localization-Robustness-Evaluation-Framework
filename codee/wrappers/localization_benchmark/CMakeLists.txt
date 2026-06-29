cmake_minimum_required(VERSION 3.0.2)
project(localization_benchmark)
find_package(catkin REQUIRED COMPONENTS geometry_msgs rospy sensor_msgs tf2_ros)
catkin_package()
catkin_install_python(PROGRAMS
  scripts/e2o_sensor_adapter.py
  scripts/e2o_static_tf_publisher.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
install(DIRECTORY launch/ config/ DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
