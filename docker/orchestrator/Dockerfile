FROM localization_eval/base:latest

WORKDIR /
COPY ros2_ws/src/evaluator /ros2_ws/src/evaluator
COPY ros2_ws/src/orchestrator /ros2_ws/src/orchestrator
COPY scripts /scripts
ENV PYTHONPATH=/ros2_ws/src/evaluator:/ros2_ws/src/orchestrator
