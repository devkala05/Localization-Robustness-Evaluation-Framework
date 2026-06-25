FROM ros:noetic-ros-base-focal
LABEL description="E2O sensor adapter, fusion supervisor, evaluation, diagnostics and RViz"
ENV DEBIAN_FRONTEND=noninteractive ROS_DISTRO=noetic CATKIN_WS=/root/catkin_ws
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-catkin-tools python3-rosdep python3-pip python3-numpy python3-scipy python3-matplotlib \
    ros-noetic-rosbag ros-noetic-cv-bridge ros-noetic-image-transport \
    ros-noetic-pcl-ros ros-noetic-pcl-conversions ros-noetic-tf2-ros \
    ros-noetic-tf2-tools ros-noetic-rviz ros-noetic-rqt-graph ros-noetic-diagnostic-msgs \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir pyyaml numpy scipy transforms3d rospkg catkin-pkg
RUN mkdir -p ${CATKIN_WS}/src
COPY wrappers/localization_benchmark ${CATKIN_WS}/src/localization_benchmark
COPY wrappers/e2o_localization_fusion ${CATKIN_WS}/src/e2o_localization_fusion
RUN chmod +x ${CATKIN_WS}/src/localization_benchmark/scripts/*.py ${CATKIN_WS}/src/e2o_localization_fusion/scripts/*.py && \
    rosdep update --rosdistro=${ROS_DISTRO} || true
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build localization_benchmark e2o_localization_fusion --no-status -j4 -p4"
RUN mkdir -p /data/output && echo 'source /root/catkin_ws/devel/setup.bash' >> /root/.bashrc
COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
