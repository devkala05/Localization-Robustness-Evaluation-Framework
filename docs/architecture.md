# Architecture

The pipeline is controlled by `ros2_ws/src/orchestrator`. It reads `config/pipeline.yaml`, enumerates enabled algorithms, sequences, and scenarios, skips runs that already have `metrics.json`, and writes `results/pipeline_state.json` for resume visibility.

Main services:

- `orchestrator`: owns the run matrix and final report generation.
- `perturbation_injector`: contains sensor perturbation classes and the ROS/offline transform entrypoint.
- `evaluator`: aligns trajectories, computes error metrics, writes reports, and generates plots.
- algorithm services: idle containers with launch wrappers for FAST-LIVO2, LIO-SAM, GLIM, FAST-LIO2, and ORB-SLAM3.

For local smoke tests, the orchestrator uses deterministic synthetic trajectories. This keeps the pipeline verifiable before downloading multi-GB datasets and building external SLAM repositories. The Docker and launch structure is ready for replacing the synthetic trajectory source with real ROS2 bag replay and algorithm odometry capture.

Outputs follow the requested structure:

- golden trajectories: `results/golden/{algo}/{sequence}/trajectory.tum`
- scenario results: `results/scenarios/{algo}/{sequence}/{scenario}/`
- final comparison artifacts: `results/final_report/`
