FROM osrf/ros:noetic-desktop-full
LABEL description="ROS Noetic RTAB-Map ICP odometry for the multi-dataset benchmark"
ENV DEBIAN_FRONTEND=noninteractive ROS_DISTRO=noetic CATKIN_WS=/root/catkin_ws
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-catkin-tools python3-rosdep ros-noetic-rtabmap-odom ros-noetic-rtabmap-slam ros-noetic-tf2-ros \
    ros-noetic-pcl-ros ros-noetic-pcl-conversions && rm -rf /var/lib/apt/lists/*
RUN mkdir -p ${CATKIN_WS}/src
COPY wrappers/rtabmap_benchmark ${CATKIN_WS}/src/rtabmap_benchmark
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build rtabmap_benchmark --no-status -j4 -p4"
RUN mkdir -p /data/output && echo 'source /root/catkin_ws/devel/setup.bash' >> /root/.bashrc
COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
