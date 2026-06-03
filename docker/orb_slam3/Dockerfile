FROM localization_eval/base:latest

ARG ORB_SLAM3_REPO=https://github.com/UZ-SLAMLab/ORB_SLAM3.git
ARG ORB_SLAM3_COMMIT=master
RUN mkdir -p /algo_ws/src && cd /algo_ws/src && \
    git clone --depth 1 "${ORB_SLAM3_REPO}" orb_slam3 || true
COPY docker/orb_slam3/launch.sh /launch_algorithm.sh
COPY docker/orb_slam3/orb_slam3.launch.py /algo_ws/orb_slam3.launch.py
RUN chmod +x /launch_algorithm.sh
CMD ["tail", "-f", "/dev/null"]
