FROM ros:noetic-ros-base-focal

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=noetic
ENV CATKIN_WS=/root/catkin_ws

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git wget curl unzip \
    python3-pip python3-dev python3-catkin-tools python3-rosdep \
    python3-rosinstall python3-rosinstall-generator python3-wstool \
    ros-noetic-pcl-ros ros-noetic-pcl-conversions \
    ros-noetic-sensor-msgs ros-noetic-geometry-msgs \
    ros-noetic-nav-msgs ros-noetic-tf2-ros ros-noetic-tf2-geometry-msgs \
    ros-noetic-rviz ros-noetic-rosbag ros-noetic-message-filters \
    ros-noetic-robot-localization ros-noetic-geographic-msgs \
    ros-noetic-image-transport ros-noetic-cv-bridge \
    ros-noetic-eigen-conversions ros-noetic-tf-conversions \
    ros-noetic-robot-state-publisher ros-noetic-joint-state-publisher \
    ros-noetic-xacro \
    libeigen3-dev libpcl-dev libboost-all-dev \
    libatlas-base-dev libgoogle-glog-dev libsuitesparse-dev \
    python3-numpy python3-scipy python3-matplotlib \
    tmux vim htop \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir pyyaml numpy scipy transforms3d pyproj rospkg catkin-pkg \
    geographiclib

RUN mkdir -p /opt/thirdparty && cd /opt/thirdparty && \
    wget -q https://github.com/ceres-solver/ceres-solver/archive/refs/tags/1.14.0.tar.gz && \
    tar zxf 1.14.0.tar.gz && cd ceres-solver-1.14.0 && \
    mkdir build && cd build && \
    cmake -DCMAKE_BUILD_TYPE=Release .. && \
    make -j4 && make install && ldconfig && \
    cd /opt/thirdparty && rm -rf ceres-solver-1.14.0 1.14.0.tar.gz

RUN cd /opt/thirdparty && \
    wget -q -O gtsam.zip https://github.com/borglab/gtsam/archive/4.0.3.zip && \
    unzip -q gtsam.zip && cd gtsam-4.0.3 && \
    mkdir build && cd build && \
    cmake -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF \
          -DGTSAM_USE_SYSTEM_EIGEN=ON \
          -DGTSAM_BUILD_PYTHON=OFF \
          -DGTSAM_INSTALL_MATLAB_TOOLBOX=OFF \
          .. && \
    make -j4 && make install && ldconfig && \
    cd /opt/thirdparty && rm -rf gtsam-4.0.3 gtsam.zip

RUN mkdir -p ${CATKIN_WS}/src
WORKDIR ${CATKIN_WS}

COPY algorithms/lvi_sam/ ${CATKIN_WS}/src/lvi_sam/
COPY wrappers/localization_benchmark/ ${CATKIN_WS}/src/localization_benchmark/
COPY wrappers/custom_localization_msgs/ ${CATKIN_WS}/src/custom_localization_msgs/
COPY wrappers/fast-lio_urbannav/ ${CATKIN_WS}/src/fast_lio_urbannav/
COPY wrappers/lvi_sam_urbannav/ ${CATKIN_WS}/src/lvi_sam_urbannav/

RUN rosdep update --rosdistro=${ROS_DISTRO} || true
RUN rosdep install --from-paths src --ignore-src -r -y --rosdistro=${ROS_DISTRO} || true

RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && \
    catkin config --extend /opt/ros/${ROS_DISTRO} --cmake-args -DCMAKE_BUILD_TYPE=Release && \
    catkin build custom_localization_msgs -j4 && \
    catkin build lvi_sam -j4 && \
    catkin build localization_benchmark fast_lio_urbannav lvi_sam_urbannav -j4"

RUN mkdir -p /data

RUN echo 'source /opt/ros/noetic/setup.bash' >> /root/.bashrc && \
    echo 'source /root/catkin_ws/devel/setup.bash' >> /root/.bashrc && \
    echo 'export ROS_MASTER_URI=http://localhost:11311' >> /root/.bashrc && \
    echo 'export ROS_HOSTNAME=localhost' >> /root/.bashrc

WORKDIR /root
CMD ["bash"]
