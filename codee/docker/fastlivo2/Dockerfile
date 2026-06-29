FROM ros:noetic-ros-base-focal
LABEL description="Pinned native FAST-LIVO2 with E2O-only external wrapper"
ENV DEBIAN_FRONTEND=noninteractive ROS_DISTRO=noetic CATKIN_WS=/root/catkin_ws
ARG FAST_LIVO2_REF=0d2c0346107b75b59934975adec9a6eeeb913c64
ARG RPG_VIKIT_REF=6c886c8e5d83997806e00294826d528cea3581dd
ARG SOPHUS_REF=a621ff
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git python3-catkin-tools python3-rosdep python3-pip \
    ros-noetic-pcl-ros ros-noetic-pcl-conversions ros-noetic-eigen-conversions \
    ros-noetic-cv-bridge \
    ros-noetic-image-transport ros-noetic-tf2-ros ros-noetic-rosbag \
    libeigen3-dev libpcl-dev libopencv-dev libboost-all-dev libyaml-cpp-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir numpy pyyaml rospkg catkin-pkg transforms3d
RUN cd /tmp && git clone https://github.com/strasdat/Sophus.git && cd Sophus && \
    git checkout ${SOPHUS_REF} && \
    sed -i 's/unit_complex_\.real() = 1\.;/unit_complex_.real(1.);/' sophus/so2.cpp && \
    sed -i 's/unit_complex_\.imag() = 0\.;/unit_complex_.imag(0.);/' sophus/so2.cpp && \
    mkdir build && cd build && cmake .. && make -j"$(nproc)" && make install && \
    mkdir -p /usr/local/lib/cmake/Sophus && \
    printf 'set(Sophus_FOUND TRUE)\nset(Sophus_INCLUDE_DIRS "/usr/local/include")\nset(Sophus_LIBRARIES "/usr/local/lib/libSophus.so")\n' \
      > /usr/local/lib/cmake/Sophus/SophusConfig.cmake && ldconfig && rm -rf /tmp/Sophus
RUN mkdir -p ${CATKIN_WS}/src && cd ${CATKIN_WS}/src && \
    git clone https://github.com/xuankuzcr/rpg_vikit.git && cd rpg_vikit && git checkout ${RPG_VIKIT_REF} && \
    cd .. && git clone https://github.com/hku-mars/FAST-LIVO2.git && cd FAST-LIVO2 && \
    git checkout ${FAST_LIVO2_REF} && git submodule update --init --recursive
COPY wrappers/fast_livo2_e2o ${CATKIN_WS}/src/fast_livo2_e2o
COPY docker/fastlivo2/patches/fix_fastlivo2_outputs.py /tmp/fix_fastlivo2_outputs.py
RUN python3 /tmp/fix_fastlivo2_outputs.py
RUN chmod +x ${CATKIN_WS}/src/fast_livo2_e2o/scripts/*.py && rosdep update --rosdistro=${ROS_DISTRO} || true
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build fast_livo fast_livo2_e2o --no-status -j4 -p4"
RUN mkdir -p /data/output && echo 'source /root/catkin_ws/devel/setup.bash' >> /root/.bashrc
COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
