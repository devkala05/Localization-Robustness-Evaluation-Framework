# Fixes Log

[2026-06-03] audit: existing scaffold used synthetic trajectories and host environment lacked ROS2/NVIDIA runtime evidence -> started real checklist audit and recorded blockers in docs/environment_audit.md
[2026-06-03] python-deps: host Python was missing rosbags and network was sandbox-restricted -> created workspace `.venv` and installed rosbags/google-generativeai/numpy/matplotlib/PyYAML/Pillow with approved network access
[2026-06-03] evaluator: full SE3 translation alignment erased known constant lateral offsets -> changed evaluator alignment to preserve translation error and emit status SUCCESS
[2026-06-03] docker-compose: service builds lacked explicit localization_eval image tags -> added image names for orchestrator/evaluator/injector and algorithm services
[2026-06-03] glim: configured koide3/glim_ros2:latest tag did not exist on Docker Hub -> changed GLIM image to koide3/glim_ros2:humble_cuda12.2
[2026-06-03] dataset: download script only printed instructions and no KITTI converter existed -> implemented KITTI S3 download plus rosbags-based raw KITTI to ROS2 bag conversion
[2026-06-03] dataset-converter: rosbags Writer failed because converter pre-created the output bag directory -> changed converter to create only the parent and let Writer create the bag
[2026-06-03] dataset-converter: ROS2 Humble CLI could not parse rosbags metadata version 9 type_description_hash entries -> changed writer metadata to version 8 and reconverted bags
[2026-06-03] fast_lio2: original Dockerfile cloned ROS1 hku-mars/FAST_LIO and did not build -> switched to Taeyoung96 FAST_LIO_ROS2 at pinned commit, added Livox ROS Driver 2 dependency, colcon build, and KITTI topic remaps
[2026-06-03] fast_lio2: first ROS2 Dockerfile created duplicate fast_lio and livox_ros_driver2 packages -> build now uses the fork's submodule packages directly
[2026-06-03] fast_lio2: livox_ros_driver2 build failed on missing liblivox_lidar_sdk_shared.so -> added pinned Livox-SDK2 source build and install before colcon
[2026-06-03] fast_lio2: livox_ros_driver2 Humble CMake reused unset generated-message include/link placeholders -> patched cloned CMake during Docker build to depend on ROSIDL generation and include rosidl_generator_cpp output
[2026-06-03] fast_lio2: launch wrapper passed remap syntax through ros2 launch and used set -u, which broke ROS setup scripts -> changed wrapper to ros2 run fastlio_mapping with params/remaps and set -eo pipefail
[2026-06-03] perturbation_injector: node only wrote a non-ROS demo JSON -> implemented rosbags-based real ROS2 bag perturbation for PointCloud2/Image/Imu/NavSatFix plus per-topic summary counts
[2026-06-03] evaluation: no extractor existed for recorded algorithm odometry bags -> added scripts/odom_bag_to_tum.py and evaluated real FAST-LIO2 rain trajectory against real baseline trajectory
[2026-06-03] dataset-converter: KITTI PointCloud2 lacked FAST-LIO2 ring/time fields -> added PCL-aligned x/y/z/intensity/time/ring layout and regenerated urban_01/highway_01 bags
[2026-06-03] perturbation_injector: perturbed PointCloud2 output stripped FAST-LIO2 ring/time fields -> parser now handles arbitrary field offsets and rewrites compatible 32-byte Velodyne records
[2026-06-03] dataset: shorter KITTI drive_0001 produced only 95 real FAST-LIO2 poses after initialization -> mapped longer drive_0005 to urban_01 and drive_0001 to highway_01 for the required >100-pose urban run
