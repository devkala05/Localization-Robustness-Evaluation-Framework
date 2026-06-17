FROM ros:noetic-ros-base-focal

LABEL description="R3LIVE UrbanNav benchmark image"

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
    ros-noetic-visualization-msgs \
    ros-noetic-tf \
    ros-noetic-tf2-ros \
    ros-noetic-tf2-geometry-msgs \
    ros-noetic-tf2-sensor-msgs \
    ros-noetic-tf-conversions \
    ros-noetic-eigen-conversions \
    ros-noetic-rviz \
    ros-noetic-rosbag \
    ros-noetic-robot-localization \
    ros-noetic-geographic-msgs \
    ros-noetic-message-filters \
    ros-noetic-image-transport \
    ros-noetic-cv-bridge \
    ros-noetic-compressed-image-transport \
    ros-noetic-robot-state-publisher \
    ros-noetic-joint-state-publisher \
    ros-noetic-xacro \
    libeigen3-dev \
    libpcl-dev \
    libboost-all-dev \
    libopencv-dev \
    libvtk7-dev \
    libyaml-cpp-dev \
    libceres-dev \
    libgoogle-glog-dev \
    libgflags-dev \
    libsuitesparse-dev \
    libatlas-base-dev \
    libomp-dev \
    libglew-dev \
    libgl1-mesa-dev \
    libcgal-dev \
    python3-numpy python3-scipy python3-matplotlib \
    tmux vim htop tree \
    && rm -rf /var/lib/apt/lists/*

# Optional renderer dependency when available in the Ubuntu/ROS apt mirror.
RUN apt-get update && \
    if apt-cache show libopenmvs-dev >/dev/null 2>&1; then \
      apt-get install -y --no-install-recommends libopenmvs-dev; \
    fi && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir pyyaml numpy scipy transforms3d pyproj rospkg catkin-pkg \
    geographiclib

RUN cd /tmp && \
    git clone https://github.com/strasdat/Sophus.git && \
    cd Sophus && \
    git checkout a621ff && \
    sed -i 's/unit_complex_\.real() = 1\.;/unit_complex_.real(1.);/' sophus/so2.cpp && \
    sed -i 's/unit_complex_\.imag() = 0\.;/unit_complex_.imag(0.);/' sophus/so2.cpp && \
    mkdir build && cd build && cmake .. && make -j"$(nproc)" && make install && \
    mkdir -p /usr/local/lib/cmake/Sophus && \
    printf 'set(Sophus_FOUND TRUE)\nset(Sophus_INCLUDE_DIRS "/usr/local/include")\nset(Sophus_LIBRARIES "/usr/local/lib/libSophus.so")\n' \
        > /usr/local/lib/cmake/Sophus/SophusConfig.cmake && \
    ldconfig && rm -rf /tmp/Sophus

RUN mkdir -p ${CATKIN_WS}/src
WORKDIR ${CATKIN_WS}

RUN cd ${CATKIN_WS}/src && \
    git clone --depth 1 https://github.com/xuankuzcr/rpg_vikit.git

RUN cd ${CATKIN_WS}/src && \
    git clone --depth 1 https://github.com/Livox-SDK/livox_ros_driver.git

RUN cd ${CATKIN_WS}/src && \
    git clone --depth 1 https://github.com/hku-mars/FAST_LIO.git && \
    cd FAST_LIO && \
    git submodule update --init --recursive

RUN cd ${CATKIN_WS}/src && \
    git clone --depth 1 https://github.com/hku-mars/r3live.git && \
    cd r3live && (git submodule update --init --recursive || true)

# Disable upstream R3LIVE OpenCV HighGUI windows (Control panel / save-map / pause)
# for benchmark runs. This keeps native odometry/VIO running headless while RViz
# remains available for visualization.
RUN python3 - <<'R3LIVE_HEADLESS_PATCH'
from pathlib import Path
root = Path('/root/catkin_ws/src/r3live')
needles = ('namedWindow', 'createTrackbar', 'imshow', 'setMouseCallback', 'destroyWindow', 'destroyAllWindows')
changed = []
for path in root.rglob('*'):
    if path.suffix not in {'.cpp', '.cc', '.cxx', '.h', '.hpp'}:
        continue
    text = path.read_text(errors='ignore')
    out = []
    touched = False
    for line in text.splitlines():
        stripped = line.strip()
        if any(('cv::' + n) in stripped or (n + '(') in stripped for n in needles):
            out.append('// [benchmark headless] ' + line)
            touched = True
        else:
            out.append(line)
    if touched:
        path.write_text('\n'.join(out) + '\n')
        changed.append(str(path.relative_to(root)))
print('Disabled R3LIVE HighGUI calls in:', ', '.join(changed) if changed else 'none')
R3LIVE_HEADLESS_PATCH

COPY wrappers/r3live_urbannav/ ${CATKIN_WS}/src/r3live_urbannav/
COPY wrappers/localization_benchmark/ ${CATKIN_WS}/src/localization_benchmark/
COPY wrappers/custom_localization_msgs/ ${CATKIN_WS}/src/custom_localization_msgs/
COPY wrappers/fast-lio_urbannav/ ${CATKIN_WS}/src/fast_lio_urbannav/

RUN chmod +x ${CATKIN_WS}/src/r3live_urbannav/scripts/*.py \
    ${CATKIN_WS}/src/localization_benchmark/scripts/*.py \
    ${CATKIN_WS}/src/fast_lio_urbannav/scripts/*.py || true

RUN rosdep update --rosdistro=${ROS_DISTRO} || true
RUN rosdep install --from-paths src --ignore-src -r -y --rosdistro=${ROS_DISTRO} || true

RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && \
    cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build livox_ros_driver vikit_common vikit_ros --no-status && \
    catkin build fast_lio --no-status && \
    catkin build r3live --no-status && \
    catkin build custom_localization_msgs localization_benchmark fast_lio_urbannav r3live_urbannav --no-status"

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
