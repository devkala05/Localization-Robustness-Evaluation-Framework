FROM osrf/ros:noetic-desktop-full
LABEL description="Pinned FAST-LIO2 for the multi-dataset localization benchmark"
ENV DEBIAN_FRONTEND=noninteractive ROS_DISTRO=noetic CATKIN_WS=/root/catkin_ws
ARG FAST_LIO_REF=7cc4175de6f8ba2edf34bab02a42195b141027e9
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git python3-catkin-tools python3-rosdep \
    ros-noetic-pcl-ros ros-noetic-pcl-conversions ros-noetic-eigen-conversions \
    ros-noetic-tf2-ros libeigen3-dev libpcl-dev && rm -rf /var/lib/apt/lists/*
RUN mkdir -p ${CATKIN_WS}/src && cd ${CATKIN_WS}/src && \
    git clone --depth 1 --filter=blob:none --no-checkout --branch main \
      https://github.com/hku-mars/FAST_LIO.git fast_lio && \
    cd fast_lio && test "$(git rev-parse HEAD)" = "${FAST_LIO_REF}" && \
    git sparse-checkout set --no-cone '/*' '!/doc/' && git checkout && \
    git submodule update --init --recursive --depth 1
ARG LIVOX_ROS_DRIVER_REF=3d240d5666129e1a3052e78ee8487a04b08fdda3
RUN cd ${CATKIN_WS}/src && \
    git clone --depth 1 --branch master https://github.com/Livox-SDK/livox_ros_driver.git && \
    cd livox_ros_driver && test "$(git rev-parse HEAD)" = "${LIVOX_ROS_DRIVER_REF}"
ARG LIVOX_SDK_REF=9306596a2bf15c1343bc023b497465ed0a32909d
RUN git clone --depth 1 --branch master https://github.com/Livox-SDK/Livox-SDK.git /tmp/livox-sdk && \
    test "$(git -C /tmp/livox-sdk rev-parse HEAD)" = "${LIVOX_SDK_REF}" && \
    cmake -S /tmp/livox-sdk -B /tmp/livox-sdk/build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build /tmp/livox-sdk/build -j4 && cmake --install /tmp/livox-sdk/build && \
    rm -rf /tmp/livox-sdk && ldconfig
COPY wrappers/fastlio2_benchmark ${CATKIN_WS}/src/fastlio2_benchmark
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build livox_ros_driver fast_lio fastlio2_benchmark --no-status -j4 -p4"
RUN mkdir -p /data/output && echo 'source /root/catkin_ws/devel/setup.bash' >> /root/.bashrc
COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
