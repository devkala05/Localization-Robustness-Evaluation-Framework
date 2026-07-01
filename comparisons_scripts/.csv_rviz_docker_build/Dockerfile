FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

# ROS1 Noetic targets Ubuntu 20.04 (Focal).
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      gnupg \
      locales \
      python3 \
      libgl1 \
      libgl1-mesa-dri \
      libgl1-mesa-glx \
      mesa-utils \
      xauth \
    && sed -i 's/^# *\(en_US.UTF-8 UTF-8\)/\1/' /etc/locale.gen \
    && locale-gen en_US.UTF-8 \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# Official ROS package repository signing key and Focal repository.
RUN curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
      -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros/ubuntu focal main" \
      > /etc/apt/sources.list.d/ros1.list

# Only install the ROS pieces required by the publisher and RViz.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-noetic-ros-base \
      ros-noetic-rospy \
      ros-noetic-rviz \
      ros-noetic-geometry-msgs \
      ros-noetic-nav-msgs \
      ros-noetic-visualization-msgs \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /opt/csv_compare/entrypoint.sh
COPY csv_compare.rviz /opt/csv_compare/csv_compare.rviz
RUN chmod +x /opt/csv_compare/entrypoint.sh

ENTRYPOINT ["/opt/csv_compare/entrypoint.sh"]
