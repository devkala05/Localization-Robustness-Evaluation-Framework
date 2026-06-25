FROM ros:noetic-ros-base-focal
LABEL description="Pinned native LVI-SAM with E2O-only external wrapper"
ENV DEBIAN_FRONTEND=noninteractive ROS_DISTRO=noetic CATKIN_WS=/root/catkin_ws
ARG LVI_SAM_REF=0d822f6dcac3378312f6703b4f45829e049f221a
ARG GTSAM_REF=4.0.2

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git python3-catkin-tools python3-rosdep python3-pip \
    ros-noetic-cv-bridge ros-noetic-image-transport ros-noetic-pcl-ros \
    ros-noetic-pcl-conversions ros-noetic-tf ros-noetic-tf2-ros ros-noetic-rosbag \
    libatlas-base-dev libboost-all-dev libceres-dev libeigen3-dev \
    libopencv-dev libpcl-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir numpy pyyaml rospkg catkin-pkg

RUN cd /tmp && git clone --depth 1 --branch ${GTSAM_REF} https://github.com/borglab/gtsam.git && \
    cd gtsam && mkdir build && cd build && \
    cmake .. -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF -DGTSAM_BUILD_TESTS=OFF \
      -DGTSAM_BUILD_EXAMPLES_ALWAYS=OFF -DGTSAM_BUILD_UNSTABLE=ON \
      -DGTSAM_BUILD_WRAP=OFF -DBoost_NO_BOOST_CMAKE=ON && \
    make -j4 && make install && ldconfig && rm -rf /tmp/gtsam

RUN mkdir -p ${CATKIN_WS}/src && cd ${CATKIN_WS}/src && \
    git clone https://github.com/TixiaoShan/LVI-SAM.git && \
    cd LVI-SAM && git checkout ${LVI_SAM_REF}
COPY docker/lvisam/patches/patch_lvisam_noetic.py /tmp/patch_lvisam_noetic.py
RUN python3 /tmp/patch_lvisam_noetic.py

COPY wrappers/lvisam_e2o ${CATKIN_WS}/src/lvisam_e2o
RUN chmod +x ${CATKIN_WS}/src/lvisam_e2o/scripts/*.py && rosdep update --rosdistro=${ROS_DISTRO} || true
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build lvi_sam lvisam_e2o --no-status -j4 -p4"

RUN mkdir -p /data/output && echo 'source /root/catkin_ws/devel/setup.bash' >> /root/.bashrc
COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
