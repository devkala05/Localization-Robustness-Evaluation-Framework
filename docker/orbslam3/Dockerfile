FROM ros:noetic-ros-base-focal

LABEL description="ORB-SLAM3 UrbanNav benchmark image"

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=noetic
ENV CATKIN_WS=/root/catkin_ws
ENV ORB_SLAM3_ROOT=/root/ORB_SLAM3

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git wget curl unzip pkg-config \
    python3-pip python3-dev python3-catkin-tools python3-rosdep \
    python3-rosinstall python3-rosinstall-generator python3-wstool \
    ros-noetic-sensor-msgs \
    ros-noetic-geometry-msgs \
    ros-noetic-nav-msgs \
    ros-noetic-std-msgs \
    ros-noetic-visualization-msgs \
    ros-noetic-tf2-ros \
    ros-noetic-tf2-geometry-msgs \
    ros-noetic-tf-conversions \
    ros-noetic-eigen-conversions \
    ros-noetic-rviz \
    ros-noetic-rosbuild \
    ros-noetic-rosbag \
    ros-noetic-message-filters \
    ros-noetic-image-transport \
    ros-noetic-cv-bridge \
    ros-noetic-image-proc \
    ros-noetic-compressed-image-transport \
    ros-noetic-robot-state-publisher \
    ros-noetic-joint-state-publisher \
    ros-noetic-xacro \
    ros-noetic-pcl-ros \
    ros-noetic-pcl-conversions \
    libeigen3-dev \
    libboost-all-dev \
    libssl-dev \
    libglew-dev \
    libopencv-dev \
    python3-opencv \
    libgl1-mesa-dev \
    libglfw3-dev \
    libegl1-mesa-dev \
    libepoxy-dev \
    python3-numpy python3-scipy \
    tmux vim htop tree \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir pyyaml numpy scipy transforms3d rospkg catkin-pkg

# Pangolin required by ORB-SLAM3 viewer/backend.
RUN cd /root && \
    git clone --depth 1 https://github.com/stevenlovegrove/Pangolin.git && \
    mkdir -p Pangolin/build && cd Pangolin/build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc) && make install && ldconfig

RUN cd /root && git clone --depth 1 https://github.com/UZ-SLAMLab/ORB_SLAM3.git ORB_SLAM3

# Ubuntu 20.04 / Noetic ships OpenCV 4.2. Patch ORB-SLAM3 CMake to accept it.
RUN sed -i 's/find_package(OpenCV 4\.4/find_package(OpenCV 4.2/' ${ORB_SLAM3_ROOT}/CMakeLists.txt && \
    sed -i 's/OpenCV > 4\.4 not found/OpenCV >= 4.2 not found/' ${ORB_SLAM3_ROOT}/CMakeLists.txt && \
    sed -i 's/find_package(OpenCV 3\.0 QUIET)/find_package(OpenCV 4.2 QUIET)/' ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3/CMakeLists.txt && \
    sed -i 's/OpenCV > 2\.4\.3 not found/OpenCV >= 4.2 not found/' ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3/CMakeLists.txt && \
    sed -i '/include\/CameraModels/a ${PROJECT_SOURCE_DIR}/../../../Thirdparty/Sophus' ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3/CMakeLists.txt && \
    sed -i '/# Node for monocular camera (Augmented Reality Demo)/,/# Node for stereo camera/c\# Node for stereo camera' ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3/CMakeLists.txt && \
    sed -i 's/std=c++11/std=c++14/g' ${ORB_SLAM3_ROOT}/CMakeLists.txt ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3/CMakeLists.txt

RUN cd ${ORB_SLAM3_ROOT}/Thirdparty/DBoW2 && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)
RUN cd ${ORB_SLAM3_ROOT}/Thirdparty/g2o && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)
RUN cd ${ORB_SLAM3_ROOT}/Thirdparty/Sophus && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)
RUN cd ${ORB_SLAM3_ROOT} && tar -xf Vocabulary/ORBvoc.txt.tar.gz -C Vocabulary/
RUN cd ${ORB_SLAM3_ROOT} && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release -DROS_BUILD_TYPE=Release && make -j$(nproc)

# Patch native ROS examples so they publish PoseStamped for benchmark recording.
COPY docker/orbslam3/patches/add_orbslam3_pose_publishers.py /tmp/add_orbslam3_pose_publishers.py
RUN python3 /tmp/add_orbslam3_pose_publishers.py

ENV ROS_PACKAGE_PATH=${ORB_SLAM3_ROOT}/Examples_old/ROS
RUN /bin/bash -c "source /opt/ros/noetic/setup.bash && \
    export ROS_PACKAGE_PATH=\${ROS_PACKAGE_PATH}:${ORB_SLAM3_ROOT}/Examples_old/ROS && \
    cd ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3 && \
    mkdir -p build && cd build && \
    cmake .. -DROS_BUILD_TYPE=Release -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc)"

RUN mkdir -p ${CATKIN_WS}/src
WORKDIR ${CATKIN_WS}

COPY wrappers/orbslam3_urbannav ${CATKIN_WS}/src/orbslam3_urbannav
COPY wrappers/localization_benchmark ${CATKIN_WS}/src/localization_benchmark
COPY wrappers/custom_localization_msgs ${CATKIN_WS}/src/custom_localization_msgs
COPY wrappers/fast-lio_urbannav ${CATKIN_WS}/src/fast_lio_urbannav

RUN rosdep update --rosdistro=${ROS_DISTRO} || true
RUN rosdep install --from-paths src --ignore-src -r -y --rosdistro=${ROS_DISTRO} || true

RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && \
    cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build custom_localization_msgs localization_benchmark fast_lio_urbannav orbslam3_urbannav -j4 -p4"

RUN mkdir -p /data /data/output /data/results/orb_slam3

RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc && \
    echo "source ${CATKIN_WS}/devel/setup.bash" >> /root/.bashrc && \
    echo "export ORB_SLAM3_ROOT=${ORB_SLAM3_ROOT}" >> /root/.bashrc && \
    echo "export ROS_PACKAGE_PATH=\${ROS_PACKAGE_PATH}:${ORB_SLAM3_ROOT}/Examples_old/ROS" >> /root/.bashrc && \
    echo "export ROS_MASTER_URI=http://localhost:11311" >> /root/.bashrc && \
    echo "export ROS_HOSTNAME=localhost" >> /root/.bashrc

COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
