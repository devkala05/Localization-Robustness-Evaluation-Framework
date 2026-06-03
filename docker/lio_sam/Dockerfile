FROM localization_eval/base:latest

ARG LIO_SAM_REPO=https://github.com/TixiaoShan/LIO-SAM.git
ARG LIO_SAM_COMMIT=ros2
RUN mkdir -p /algo_ws/src && cd /algo_ws/src && \
    git clone --depth 1 --branch "${LIO_SAM_COMMIT}" "${LIO_SAM_REPO}" lio_sam || true
COPY docker/lio_sam/launch.sh /launch_algorithm.sh
COPY docker/lio_sam/lio_sam.launch.py /algo_ws/lio_sam.launch.py
RUN chmod +x /launch_algorithm.sh
CMD ["tail", "-f", "/dev/null"]
