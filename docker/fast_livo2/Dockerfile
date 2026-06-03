FROM localization_eval/base:latest

ARG FAST_LIVO2_ROS2_REPO=https://github.com/VIS4ROB-lab/FAST-LIVO2-ROS2.git
ARG FAST_LIVO2_COMMIT=main
RUN mkdir -p /algo_ws/src && cd /algo_ws/src && \
    git clone --depth 1 "${FAST_LIVO2_ROS2_REPO}" fast_livo2 || true
COPY docker/fast_livo2/launch.sh /launch_algorithm.sh
COPY docker/fast_livo2/fast_livo2.launch.py /algo_ws/fast_livo2.launch.py
RUN chmod +x /launch_algorithm.sh
CMD ["tail", "-f", "/dev/null"]
