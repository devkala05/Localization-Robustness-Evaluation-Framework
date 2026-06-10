FROM ros:noetic-ros-base-focal

LABEL maintainer="FAST-LIVO2 Black-Box Wrapper"
LABEL description="Complete ROS1 black-box testing pipeline for FAST-LIVO2 (LiDAR-IMU-Visual odometry) on UrbanNav dataset"

# ─── Environment ────────────────────────────────────────────────────────────────
ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=noetic
ENV CATKIN_WS=/root/catkin_ws

# ─── System & ROS dependencies ──────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    build-essential cmake git wget curl unzip \
    # Python 3
    python3-pip python3-dev python3-catkin-tools python3-rosdep \
    python3-rosinstall python3-rosinstall-generator python3-wstool \
    # ROS packages
    ros-noetic-pcl-ros \
    ros-noetic-pcl-conversions \
    ros-noetic-sensor-msgs \
    ros-noetic-geometry-msgs \
    ros-noetic-nav-msgs \
    ros-noetic-tf2-ros \
    ros-noetic-tf2-geometry-msgs \
    ros-noetic-rviz \
    ros-noetic-rosbag \
    ros-noetic-message-filters \
    ros-noetic-image-transport \
    ros-noetic-cv-bridge \
    ros-noetic-eigen-conversions \
    ros-noetic-tf-conversions \
    ros-noetic-robot-state-publisher \
    ros-noetic-joint-state-publisher \
    ros-noetic-xacro \
    ros-noetic-visualization-msgs \
    # C++ dependencies for FAST-LIVO2
    libeigen3-dev \
    libpcl-dev \
    libboost-all-dev \
    libopencv-dev \
    libvtk7-dev \
    libyaml-cpp-dev \
    # Python scientific stack
    python3-numpy python3-scipy \
    # Utilities
    tmux vim htop tree \
    && rm -rf /var/lib/apt/lists/*

# ─── Python pip packages ────────────────────────────────────────────────────────
RUN pip3 install --no-cache-dir \
    pyyaml \
    numpy \
    scipy \
    transforms3d \
    pyproj \
    rospkg \
    catkin-pkg

# ─── Catkin workspace ───────────────────────────────────────────────────────────
RUN mkdir -p ${CATKIN_WS}/src
WORKDIR ${CATKIN_WS}

# ─── FAST-LIVO2 upstream prerequisites ─────────────────────────────────────────
RUN cd /tmp && \
    git clone https://github.com/strasdat/Sophus.git && \
    cd Sophus && \
    git checkout a621ff && \
    sed -i 's/unit_complex_\.real() = 1\.;/unit_complex_.real(1.);/' sophus/so2.cpp && \
    sed -i 's/unit_complex_\.imag() = 0\.;/unit_complex_.imag(0.);/' sophus/so2.cpp && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j"$(nproc)" && \
    make install && \
    mkdir -p /usr/local/lib/cmake/Sophus && \
    printf 'set(Sophus_FOUND TRUE)\nset(Sophus_INCLUDE_DIRS "/usr/local/include")\nset(Sophus_LIBRARIES "/usr/local/lib/libSophus.so")\n' > /usr/local/lib/cmake/Sophus/SophusConfig.cmake && \
    ldconfig && \
    rm -rf /tmp/Sophus

RUN cd ${CATKIN_WS}/src && \
    git clone --depth 1 https://github.com/xuankuzcr/rpg_vikit.git

# ─── Clone Livox ROS driver (required by FAST-LIVO2 CMakeLists find_package) ───
# FAST-LIVO2 CMakeLists.txt has find_package(livox_ros_driver) — must be built
# before FAST-LIVO2 even though UrbanNav uses Velodyne (not Livox hardware).
RUN cd ${CATKIN_WS}/src && \
    git clone --depth 1 https://github.com/Livox-SDK/livox_ros_driver.git

# ─── Clone FAST-LIVO2 (black box — zero source modifications) ───────────────────
RUN cd ${CATKIN_WS}/src && \
    git clone --depth 1 https://github.com/hku-mars/FAST-LIVO2.git && \
    cd FAST-LIVO2 && \
    git submodule update --init --recursive

# ─── Copy wrapper package ───────────────────────────────────────────────────────
COPY wrappers/fast_livo2_wrapper ${CATKIN_WS}/src/fast_livo2_wrapper

# ─── rosdep ─────────────────────────────────────────────────────────────────────
RUN rosdep update --rosdistro=${ROS_DISTRO}
RUN rosdep install --from-paths src --ignore-src -r -y --rosdistro=${ROS_DISTRO} || true

# ─── Build workspace ────────────────────────────────────────────────────────────
# Step 1: Build livox_ros_driver first — FAST-LIVO2 find_package depends on it
# Step 2: Build FAST-LIVO2's catkin package (repo dir is FAST-LIVO2, package is fast_livo)
# Step 3: Build wrapper package (Python nodes — fast, no C++)
RUN /bin/bash -c "\
    source /opt/ros/${ROS_DISTRO}/setup.bash && \
    cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build livox_ros_driver --no-status && \
    catkin build fast_livo --no-status && \
    catkin build fast_livo2_wrapper --no-status"

# ─── Output directory ───────────────────────────────────────────────────────────
RUN mkdir -p /data/output

# ─── Shell setup ────────────────────────────────────────────────────────────────
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc && \
    echo "source ${CATKIN_WS}/devel/setup.bash" >> /root/.bashrc && \
    echo "export ROS_MASTER_URI=http://localhost:11311" >> /root/.bashrc && \
    echo "export ROS_HOSTNAME=localhost" >> /root/.bashrc

# ─── Entrypoint ─────────────────────────────────────────────────────────────────
COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
