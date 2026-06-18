FROM ros:noetic-ros-base-focal

LABEL maintainer="Adaptive-W LVIO UrbanNav Pipeline"
LABEL description="Native lvio_fusion / Adaptive-W LVIO integration for UrbanNav perturbation/evaluation pipeline"

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=noetic
ENV CATKIN_WS=/root/catkin_ws

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git wget curl unzip pkg-config \
    python3-pip python3-dev python3-catkin-tools python3-rosdep \
    python3-rosinstall python3-rosinstall-generator python3-wstool \
    ros-noetic-pcl-ros \
    ros-noetic-pcl-conversions \
    ros-noetic-sensor-msgs \
    ros-noetic-geometry-msgs \
    ros-noetic-nav-msgs \
    ros-noetic-std-msgs \
    ros-noetic-tf \
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
    ros-noetic-visualization-msgs \
    libeigen3-dev \
    libgflags-dev \
    libunwind-dev \
    libfmt-dev \
    libpcl-dev \
    libboost-all-dev \
    libopencv-dev \
    libceres-dev \
    libgoogle-glog-dev \
    libatlas-base-dev \
    libsuitesparse-dev \
    libgeographic-dev \
    python3-numpy python3-scipy python3-matplotlib \
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

# lvio_fusion requires Sophus as a CMake package.
# Do not build Sophus main on Ubuntu 20.04/ROS Noetic: current Sophus main
# requires CMake >= 3.24, while focal's apt CMake is 3.16.3.
# Sophus 1.22.10 is compatible with CMake 3.4+ and works with Noetic/focal.
ARG SOPHUS_TAG=1.22.10
RUN cd /opt && \
    git clone --depth 1 --branch ${SOPHUS_TAG} --single-branch https://github.com/strasdat/Sophus.git && \
    cd Sophus && mkdir -p build && cd build && \
    cmake .. \
      -DCMAKE_BUILD_TYPE=Release \
      -DBUILD_SOPHUS_TESTS=OFF \
      -DBUILD_SOPHUS_EXAMPLES=OFF \
      -DSOPHUS_USE_BASIC_LOGGING=ON && \
    make -j$(nproc) && make install && ldconfig && \
    cd /opt && rm -rf Sophus

RUN mkdir -p ${CATKIN_WS}/src
WORKDIR ${CATKIN_WS}

RUN cd ${CATKIN_WS}/src && \
    git clone --depth 1 https://github.com/Livox-SDK/livox_ros_driver.git && \
    git clone --depth 1 https://github.com/jypjypjypjyp/lvio_fusion.git lvio_fusion_upstream

COPY docker/adaptive_w_lvio/patch_lvio_fusion_cmake.py /tmp/patch_lvio_fusion_cmake.py
RUN python3 /tmp/patch_lvio_fusion_cmake.py ${CATKIN_WS}/src/lvio_fusion_upstream

COPY wrappers/fast-lio_urbannav/ ${CATKIN_WS}/src/fast_lio_urbannav/
COPY wrappers/localization_benchmark/ ${CATKIN_WS}/src/localization_benchmark/
COPY wrappers/custom_localization_msgs/ ${CATKIN_WS}/src/custom_localization_msgs/
COPY wrappers/adaptive_w_lvio_urbannav/ ${CATKIN_WS}/src/adaptive_w_lvio_urbannav/

RUN chmod +x ${CATKIN_WS}/src/adaptive_w_lvio_urbannav/scripts/*.py \
    ${CATKIN_WS}/src/localization_benchmark/scripts/*.py \
    ${CATKIN_WS}/src/fast_lio_urbannav/scripts/*.py || true

RUN rosdep update --rosdistro=${ROS_DISTRO} || true
RUN rosdep install --from-paths src --ignore-src -r -y --rosdistro=${ROS_DISTRO} || true

# Build the real upstream LVIO-Fusion packages plus the benchmark wrapper.
# Build lvio_fusion separately and print the package logs on failure; otherwise
# Docker only shows "Failed <<< lvio_fusion" and hides the useful compiler error.
RUN /bin/bash -c "set -e; \
    source /opt/ros/${ROS_DISTRO}/setup.bash; \
    cd ${CATKIN_WS}; \
    catkin config --extend /opt/ros/${ROS_DISTRO} --cmake-args -DCMAKE_BUILD_TYPE=Release; \
    catkin build livox_ros_driver custom_localization_msgs fast_lio_urbannav adaptive_w_lvio_urbannav -j4 -p4 --no-status; \
    catkin build lvio_fusion -j2 -p1 --no-status || \
      (echo '[build] lvio_fusion failed; dumping catkin logs'; \
       find ${CATKIN_WS}/logs/lvio_fusion -type f -name '*.log' -maxdepth 1 -print -exec sh -c 'echo ===== $1 =====; tail -n 240 $1' sh {} \; 2>/dev/null || true; \
       false); \
    catkin build lvio_fusion_node localization_benchmark -j2 -p1 --no-status || \
      (echo '[build] lvio_fusion_node/localization_benchmark failed; dumping catkin logs'; \
       find ${CATKIN_WS}/logs/lvio_fusion_node ${CATKIN_WS}/logs/localization_benchmark -maxdepth 1 -type f -name '*.log' -print -exec sh -c 'echo ===== $1 =====; tail -n 240 $1' sh {} \; 2>/dev/null || true; \
       false)"

RUN mkdir -p /data /data/results/analysis /data/results/e2o /data/results/urbannav /data/output

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc && \
    echo "source ${CATKIN_WS}/devel/setup.bash" >> /root/.bashrc && \
    echo "export ROS_MASTER_URI=http://localhost:11311" >> /root/.bashrc && \
    echo "export ROS_HOSTNAME=localhost" >> /root/.bashrc

COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /root
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
