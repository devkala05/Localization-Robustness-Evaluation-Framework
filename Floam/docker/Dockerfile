FROM ros:noetic-ros-base-focal
LABEL description="ALIVE FLOAM with E2O wrapper"

ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=noetic \
    CATKIN_WS=/root/catkin_ws

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    python3-catkin-tools \
    python3-rosdep \
    python3-pip \
    ros-noetic-pcl-ros \
    ros-noetic-pcl-conversions \
    ros-noetic-tf \
    ros-noetic-tf2 \
    ros-noetic-tf2-ros \
    ros-noetic-tf2-eigen \
    ros-noetic-tf2-geometry-msgs \
    ros-noetic-tf-conversions \
    ros-noetic-eigen-conversions \
    ros-noetic-rosbag \
    libceres-dev \
    libeigen3-dev \
    libpcl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir numpy pyyaml rospkg catkin-pkg

RUN mkdir -p ${CATKIN_WS}/src
COPY Floam/native/alive_msgs ${CATKIN_WS}/src/alive_msgs
COPY Floam/native/floam ${CATKIN_WS}/src/floam
COPY Floam/wrappers/floam_e2o ${CATKIN_WS}/src/floam_e2o

RUN chmod +x ${CATKIN_WS}/src/floam_e2o/scripts/*.py && \
    rosdep update --rosdistro=${ROS_DISTRO} || true

RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build alive_msgs floam floam_e2o --no-status -j4 -p4"

RUN mkdir -p /data/output && echo 'source /root/catkin_ws/devel/setup.bash' >> /root/.bashrc

COPY Floam/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
