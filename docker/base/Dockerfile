FROM osrf/ros:humble-desktop

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    python3-pip \
    python3-colcon-common-extensions \
    python3-vcstool \
    python3-yaml \
    python3-numpy \
    python3-matplotlib \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-cv-bridge \
    ros-humble-pcl-ros \
    libopencv-dev \
    libpcl-dev \
    libeigen3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir rosbags google-generativeai

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
SHELL ["/bin/bash", "-c"]
