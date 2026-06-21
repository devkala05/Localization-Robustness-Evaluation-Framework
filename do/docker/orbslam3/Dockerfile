FROM ros:noetic-ros-base-focal
LABEL description="Pinned native ORB-SLAM3 monocular with E2O-only external wrapper"
ENV DEBIAN_FRONTEND=noninteractive ROS_DISTRO=noetic CATKIN_WS=/root/catkin_ws ORB_SLAM3_ROOT=/root/ORB_SLAM3
ARG ORB_SLAM3_REF=0df83dde1c85c7ab91a0d47de7a29685d046f637
ARG PANGOLIN_REF=v0.8
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git pkg-config python3-catkin-tools python3-rosdep python3-pip \
    ros-noetic-rosbuild ros-noetic-cv-bridge ros-noetic-image-transport \
    ros-noetic-geometry-msgs ros-noetic-nav-msgs ros-noetic-std-msgs \
    ros-noetic-tf ros-noetic-tf2-ros ros-noetic-rosbag libeigen3-dev libboost-all-dev \
    libssl-dev libglew-dev libopencv-dev libgl1-mesa-dev libglfw3-dev \
    libegl1-mesa-dev libepoxy-dev && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir numpy scipy pyyaml transforms3d rospkg catkin-pkg
RUN cd /root && git clone https://github.com/stevenlovegrove/Pangolin.git && cd Pangolin && \
    git checkout ${PANGOLIN_REF} && mkdir -p build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && make -j"$(nproc)" && make install && ldconfig
RUN cd /root && git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git ORB_SLAM3 && \
    cd ${ORB_SLAM3_ROOT} && git checkout ${ORB_SLAM3_REF}
RUN sed -i 's/find_package(OpenCV 4\.4/find_package(OpenCV 4.2/' ${ORB_SLAM3_ROOT}/CMakeLists.txt && \
    sed -i 's/OpenCV > 4\.4 not found/OpenCV >= 4.2 not found/' ${ORB_SLAM3_ROOT}/CMakeLists.txt && \
    sed -i 's/find_package(OpenCV 3\.0 QUIET)/find_package(OpenCV 4.2 QUIET)/' ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3/CMakeLists.txt && \
    sed -i '/include\/CameraModels/a ${PROJECT_SOURCE_DIR}/../../../Thirdparty/Sophus' ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3/CMakeLists.txt && \
    sed -i '/# Node for monocular camera (Augmented Reality Demo)/,/# Node for stereo camera/c\# Node for stereo camera' ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3/CMakeLists.txt && \
    sed -i 's/std=c++11/std=c++14/g' ${ORB_SLAM3_ROOT}/CMakeLists.txt ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3/CMakeLists.txt
RUN cd ${ORB_SLAM3_ROOT}/Thirdparty/DBoW2 && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j"$(nproc)" && \
    cd ${ORB_SLAM3_ROOT}/Thirdparty/g2o && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j"$(nproc)" && \
    cd ${ORB_SLAM3_ROOT}/Thirdparty/Sophus && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j"$(nproc)"
RUN cd ${ORB_SLAM3_ROOT} && tar -xf Vocabulary/ORBvoc.txt.tar.gz -C Vocabulary/ && \
    mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j"$(nproc)"
COPY docker/orbslam3/patches/add_orbslam3_pose_publishers.py /tmp/add_pose_publishers.py
RUN python3 /tmp/add_pose_publishers.py
ENV ROS_PACKAGE_PATH=/opt/ros/noetic/share:${ORB_SLAM3_ROOT}/Examples_old/ROS
RUN /bin/bash -c "source /opt/ros/noetic/setup.bash && \
    export ROS_PACKAGE_PATH=/opt/ros/noetic/share:${ORB_SLAM3_ROOT}/Examples_old/ROS && \
    cd ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3 && \
    mkdir -p build && cd build && cmake .. -DROS_BUILD_TYPE=Release -DCMAKE_BUILD_TYPE=Release && make -j\$(nproc)"
RUN mkdir -p ${CATKIN_WS}/src
COPY wrappers/orbslam3_e2o ${CATKIN_WS}/src/orbslam3_e2o
RUN chmod +x ${CATKIN_WS}/src/orbslam3_e2o/scripts/*.py && rosdep update --rosdistro=${ROS_DISTRO} || true
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build orbslam3_e2o --no-status -j4 -p4"
RUN mkdir -p /data/output && echo 'source /root/catkin_ws/devel/setup.bash' >> /root/.bashrc && \
    echo 'export ROS_PACKAGE_PATH=${ROS_PACKAGE_PATH}:/root/ORB_SLAM3/Examples_old/ROS' >> /root/.bashrc
COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
