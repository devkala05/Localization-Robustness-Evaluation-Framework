FROM ros:noetic-ros-base-focal

LABEL maintainer="FastLIO2-UrbanNav Pipeline"
LABEL description="Black-box testing pipeline for Fast-LIO2 with UrbanNav Medium Urban dataset"

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=noetic
ENV CATKIN_WS=/root/catkin_ws

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git wget curl \
    python3-pip python3-dev python3-catkin-tools python3-rosdep \
    python3-rosinstall python3-rosinstall-generator python3-wstool \
    ros-noetic-pcl-ros \
    ros-noetic-pcl-conversions \
    ros-noetic-sensor-msgs \
    ros-noetic-geometry-msgs \
    ros-noetic-nav-msgs \
    ros-noetic-tf2-ros \
    ros-noetic-tf2-geometry-msgs \
    ros-noetic-rviz \
    ros-noetic-rosbag \
    ros-noetic-robot-localization \
    ros-noetic-geographic-msgs \
    ros-noetic-message-filters \
    ros-noetic-image-transport \
    ros-noetic-cv-bridge \
    ros-noetic-eigen-conversions \
    ros-noetic-tf-conversions \
    ros-noetic-robot-state-publisher \
    ros-noetic-joint-state-publisher \
    ros-noetic-xacro \
    ros-noetic-rtabmap-ros \
    libeigen3-dev \
    libpcl-dev \
    libboost-all-dev \
    python3-numpy python3-scipy \
    python3-matplotlib \
    tmux vim htop tree \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    pyyaml \
    numpy \
    scipy \
    transforms3d \
    pyproj \
    rospkg \
    catkin-pkg \
    geographiclib

RUN mkdir -p ${CATKIN_WS}/src

WORKDIR ${CATKIN_WS}

RUN cd ${CATKIN_WS}/src && \
    git clone --depth 1 https://github.com/Livox-SDK/livox_ros_driver.git

RUN cd ${CATKIN_WS}/src && \
    git clone --depth 1 https://github.com/hku-mars/FAST_LIO.git && \
    cd FAST_LIO && \
    git submodule update --init --recursive

COPY wrappers/fast-lio_urbannav/ ${CATKIN_WS}/src/fast_lio_urbannav/
COPY wrappers/localization_benchmark/ ${CATKIN_WS}/src/localization_benchmark/
COPY wrappers/custom_localization_msgs/ ${CATKIN_WS}/src/custom_localization_msgs/
COPY wrappers/adaptive_w_lvio_urbannav/ ${CATKIN_WS}/src/adaptive_w_lvio_urbannav/

RUN chmod +x ${CATKIN_WS}/src/adaptive_w_lvio_urbannav/scripts/*.py \
    ${CATKIN_WS}/src/localization_benchmark/scripts/*.py \
    ${CATKIN_WS}/src/fast_lio_urbannav/scripts/*.py

RUN rosdep update --rosdistro=${ROS_DISTRO} || true
RUN rosdep install --from-paths src --ignore-src -r -y --rosdistro=${ROS_DISTRO} || true

RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && \
    cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build livox_ros_driver && \
    catkin build fast_lio && \
    catkin build custom_localization_msgs localization_benchmark fast_lio_urbannav adaptive_w_lvio_urbannav -DCMAKE_BUILD_TYPE=Release"

RUN mkdir -p /data /data/results/adaptive_w_lvio /data/output

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc && \
    echo "source ${CATKIN_WS}/devel/setup.bash" >> /root/.bashrc && \
    echo "export ROS_MASTER_URI=http://localhost:11311" >> /root/.bashrc && \
    echo "export ROS_HOSTNAME=localhost" >> /root/.bashrc

COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /root

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
