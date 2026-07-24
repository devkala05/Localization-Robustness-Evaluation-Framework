FROM fastlio2-benchmark:latest
LABEL description="Pinned native ORB-SLAM3 RGB-D with E2O-only external wrapper"
ENV DEBIAN_FRONTEND=noninteractive ROS_DISTRO=noetic CATKIN_WS=/root/catkin_ws ORB_SLAM3_ROOT=/root/ORB_SLAM3
ARG ORB_SLAM3_REF=0df83dde1c85c7ab91a0d47de7a29685d046f637
ARG PANGOLIN_REF=v0.8
RUN cd /root && git clone --depth 1 --branch ${PANGOLIN_REF} \
      https://github.com/stevenlovegrove/Pangolin.git && cd Pangolin && \
    mkdir -p build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && make -j"$(nproc)" && make install && ldconfig
RUN git clone --depth 1 --filter=blob:none --no-checkout \
      https://github.com/UZ-SLAMLab/ORB_SLAM3.git ${ORB_SLAM3_ROOT} && \
    cd ${ORB_SLAM3_ROOT} && git fetch --depth 1 origin ${ORB_SLAM3_REF} && \
    git sparse-checkout set --no-cone '/*' '!/evaluation/' \
      '!/Examples/Monocular-Inertial/TUM_IMU/' \
      '!/Examples/Stereo-Inertial/TUM_IMU/' \
      '!/Examples_old/Monocular-Inertial/TUM_IMU/' \
      '!/Examples_old/Stereo-Inertial/TUM_IMU/' && \
    git checkout --detach FETCH_HEAD && \
    test "$(git rev-parse HEAD)" = "${ORB_SLAM3_REF}"
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
    mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j4
COPY docker/orbslam3/patches/add_orbslam3_pose_publishers.py /tmp/add_pose_publishers.py
COPY docker/orbslam3/patches/add_rgbd_inertial.py /tmp/add_rgbd_inertial.py
COPY docker/orbslam3/patches/add_mono_inertial_publishers.py /tmp/add_mono_inertial_publishers.py
# Patch 1: add read-only pose/map publishers to ros_rgbd.cc
RUN python3 /tmp/add_pose_publishers.py
# Patch 2: create ros_rgbd_inertial.cc (IMU_RGBD mode) and add CMakeLists target
RUN python3 /tmp/add_rgbd_inertial.py
# Patch 3: expose the native mono-inertial pose for the unchanged recorder.
RUN python3 /tmp/add_mono_inertial_publishers.py
ENV ROS_PACKAGE_PATH=/opt/ros/noetic/share:${ORB_SLAM3_ROOT}/Examples_old/ROS
RUN /bin/bash -c "source /opt/ros/noetic/setup.bash && \
    export ROS_PACKAGE_PATH=/opt/ros/noetic/share:${ORB_SLAM3_ROOT}/Examples_old/ROS && \
    cd ${ORB_SLAM3_ROOT}/Examples_old/ROS/ORB_SLAM3 && \
    mkdir -p build && cd build && cmake .. -DROS_BUILD_TYPE=Release -DCMAKE_BUILD_TYPE=Release && make -j4"
RUN mkdir -p ${CATKIN_WS}/src
COPY wrappers/orbslam3_e2o ${CATKIN_WS}/src/orbslam3_e2o
RUN chmod +x ${CATKIN_WS}/src/orbslam3_e2o/scripts/*.py
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build orbslam3_e2o --no-status -j4 -p4"
RUN mkdir -p /data/output && echo 'source /root/catkin_ws/devel/setup.bash' >> /root/.bashrc && \
    echo 'export ROS_PACKAGE_PATH=${ROS_PACKAGE_PATH}:/root/ORB_SLAM3/Examples_old/ROS' >> /root/.bashrc
COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
