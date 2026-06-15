FROM osrf/ros:noetic-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV E2O_EVAL_ROOT=/workspace/e2o_eval
ENV ROS_MASTER_URI=http://localhost:11311
ENV ROS_HOSTNAME=localhost
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash-completion \
    build-essential \
    cmake \
    git \
    nano \
    python3-catkin-tools \
    python3-matplotlib \
    python3-numpy \
    python3-pip \
    python3-yaml \
    ros-noetic-cv-bridge \
    ros-noetic-geometry-msgs \
    ros-noetic-image-transport \
    ros-noetic-nav-msgs \
    ros-noetic-rosbag \
    ros-noetic-roslaunch \
    ros-noetic-rospy \
    ros-noetic-rqt-image-view \
    ros-noetic-rviz \
    ros-noetic-sensor-msgs \
    ros-noetic-tf \
    ros-noetic-tf2-ros \
    ros-noetic-topic-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${E2O_EVAL_ROOT}
COPY . ${E2O_EVAL_ROOT}

RUN source /opt/ros/noetic/setup.bash \
    && catkin_make -C catkin_ws \
    && chmod +x scripts/entrypoint.sh

ENTRYPOINT ["/workspace/e2o_eval/scripts/entrypoint.sh"]
CMD ["shell"]
