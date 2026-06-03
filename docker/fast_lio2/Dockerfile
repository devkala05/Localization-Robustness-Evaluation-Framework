FROM localization_eval/base:latest

ARG FAST_LIO2_REPO=https://github.com/Taeyoung96/FAST_LIO_ROS2.git
ARG FAST_LIO2_COMMIT=373aa886402b6307db2995ca12b3f4596ef4f633
ARG LIVOX_SDK2_REPO=https://github.com/Livox-SDK/Livox-SDK2.git
ARG LIVOX_SDK2_COMMIT=f5d9375f84efe2b15bc0a052d3e18482ed13adf4

RUN mkdir -p /algo_ws/src && cd /algo_ws/src && \
    git clone --recursive "${FAST_LIO2_REPO}" fast_lio2_ros2 && \
    cd fast_lio2_ros2 && git checkout "${FAST_LIO2_COMMIT}" && \
    git submodule update --init --recursive && \
    cp livox_ros_driver2/package_ROS2.xml livox_ros_driver2/package.xml && \
    sed -i '/target_link_libraries(${PROJECT_NAME} "${cpp_typesupport_target}")/a\    set(LIVOX_INTERFACE_TARGET "${cpp_typesupport_target}")' livox_ros_driver2/CMakeLists.txt && \
    sed -i '/set(LIVOX_INTERFACE_TARGET "${cpp_typesupport_target}")/a\    add_dependencies(${PROJECT_NAME} ${LIVOX_INTERFACES})' livox_ros_driver2/CMakeLists.txt && \
    sed -i 's|${LIVOX_INTERFACES_INCLUDE_DIRECTORIES}   # for custom msgs|${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_cpp   # for custom msgs|' livox_ros_driver2/CMakeLists.txt && \
    sed -i '/${LIVOX_INTERFACE_TARGET}   # for custom msgs/d' livox_ros_driver2/CMakeLists.txt

RUN git clone "${LIVOX_SDK2_REPO}" /tmp/Livox-SDK2 && \
    cd /tmp/Livox-SDK2 && git checkout "${LIVOX_SDK2_COMMIT}" && \
    mkdir -p build && cd build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    ldconfig

RUN cd /algo_ws && \
    . /opt/ros/humble/setup.sh && \
    colcon build --packages-select livox_ros_driver2 fast_lio --cmake-args -DCMAKE_BUILD_TYPE=Release

COPY docker/fast_lio2/launch.sh /launch_algorithm.sh
COPY docker/fast_lio2/fast_lio2.launch.py /algo_ws/fast_lio2.launch.py
COPY docker/fast_lio2/fast_lio2_kitti.yaml /algo_ws/fast_lio2_kitti.yaml
RUN chmod +x /launch_algorithm.sh
CMD ["tail", "-f", "/dev/null"]
