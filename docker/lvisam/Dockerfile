FROM fastlio2-benchmark:latest
LABEL description="Pinned native LVI-SAM with E2O-only external wrapper"
ENV DEBIAN_FRONTEND=noninteractive ROS_DISTRO=noetic CATKIN_WS=/root/catkin_ws
ARG LVI_SAM_REF=0d822f6dcac3378312f6703b4f45829e049f221a
ARG GTSAM_REF=4.0.2

RUN apt-get update && apt-get install -y --no-install-recommends \
    libceres-dev \
    && rm -rf /var/lib/apt/lists/*

RUN cd /tmp && git clone --depth 1 --branch ${GTSAM_REF} https://github.com/borglab/gtsam.git && \
    cd gtsam && mkdir build && cd build && \
    cmake .. -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF -DGTSAM_BUILD_TESTS=OFF \
      -DGTSAM_BUILD_EXAMPLES_ALWAYS=OFF -DGTSAM_BUILD_UNSTABLE=ON \
      -DGTSAM_BUILD_WRAP=OFF -DBoost_NO_BOOST_CMAKE=ON && \
    make -j4 && make install && ldconfig && rm -rf /tmp/gtsam

RUN mkdir -p ${CATKIN_WS}/src /tmp/lvisam-src && \
    curl -fL --retry 20 --retry-delay 2 --connect-timeout 15 \
      "https://codeload.github.com/TixiaoShan/LVI-SAM/tar.gz/${LVI_SAM_REF}" \
      -o /tmp/lvisam.tar.gz && \
    tar -xzf /tmp/lvisam.tar.gz --strip-components=1 -C /tmp/lvisam-src && \
    mv /tmp/lvisam-src ${CATKIN_WS}/src/LVI-SAM && rm /tmp/lvisam.tar.gz
COPY docker/lvisam/patches/patch_lvisam_noetic.py /tmp/patch_lvisam_noetic.py
RUN python3 /tmp/patch_lvisam_noetic.py

COPY wrappers/lvisam_e2o ${CATKIN_WS}/src/lvisam_e2o
RUN chmod +x ${CATKIN_WS}/src/lvisam_e2o/scripts/*.py
RUN /bin/bash -c "source /opt/ros/${ROS_DISTRO}/setup.bash && cd ${CATKIN_WS} && \
    catkin config --extend /opt/ros/${ROS_DISTRO} -DCMAKE_BUILD_TYPE=Release && \
    catkin build lvi_sam lvisam_e2o --no-status -j2 -p2"

RUN mkdir -p /data/output && echo 'source /root/catkin_ws/devel/setup.bash' >> /root/.bashrc
COPY .docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
