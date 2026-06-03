# Environment Audit

Generated: 2026-06-03 Asia/Kolkata

## GPU

Command:

```bash
nvidia-smi
```

Output:

```text
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver. Make sure that the latest NVIDIA driver is installed and running.
```

Status: **FAIL**. The checklist requires `nvidia-smi` to show the RTX 4060, but the host driver is currently unavailable.

Follow-up with approved host access:

```text
NVIDIA-SMI 580.159.03
Driver Version: 580.159.03
CUDA Version: 13.0
GPU 0: NVIDIA GeForce RTX 4060 Laptop/Mobile, 8188 MiB
```

Status: **PASS** for host GPU visibility outside the sandbox. The earlier failure is sandbox-related.

## Docker

Command:

```bash
docker --version
docker compose version
docker info
```

Output:

```text
Docker version 29.5.2, build 79eb04c
Docker Compose version v5.1.4
Runtimes: io.containerd.runc.v2 runc
Default Runtime: runc
```

Status: **FAIL** for NVIDIA runtime. Docker is installed, but `docker info` does not list `nvidia`.

Current built/pulled images:

```text
localization_eval/base:latest 5.12GB
localization_eval/perturbation_injector:latest 5.12GB
localization_eval/evaluator:latest 5.12GB
localization_eval/orchestrator:latest 5.12GB
localization_eval/fast_lio2:latest 6.04GB
localization_eval/fast_livo2:latest 5.22GB
localization_eval/lio_sam:latest 5.39GB
localization_eval/orb_slam3:latest 7.58GB
koide3/glim_ros2:humble_cuda12.2 14.6GB
```

Status: **PASS** for Docker image availability. **FAIL** remains for GPU runtime because Docker still reports only `io.containerd.runc.v2` and `runc`, with default runtime `runc`.

## NVIDIA Container Toolkit

Command:

```bash
dpkg -l | grep nvidia-container
```

Output: no packages matched.

Status: **FAIL**. NVIDIA Container Toolkit is not installed or not visible through `dpkg`.

## Disk

Command:

```bash
df -h /home/devil/Desktop/car/
```

Output:

```text
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p6  344G  224G  103G  69% /
```

Status: **PASS** for dataset download space.

## RAM

Command:

```bash
free -h
```

Output:

```text
               total        used        free      shared  buff/cache   available
Mem:            11Gi       6.9Gi       1.2Gi       851Mi       4.7Gi       4.5Gi
Swap:           11Gi       2.6Gi       9.4Gi
```

Status: available RAM is limited; keep `parallel_algos: 1`.

## ROS2

Command:

```bash
source /opt/ros/humble/setup.bash 2>/dev/null && echo "ROS2 Humble OK" || echo "ROS2 NOT FOUND"
```

Output:

```text
ROS2 NOT FOUND
```

Status: **FAIL** on host. ROS2 is currently only available through Docker base images already present locally.

## Python

Command:

```bash
python3 --version
pip3 show rosbags
pip3 show google-generativeai
```

Output:

```text
Python 3.13.11
Package(s) not found: rosbags
google-generativeai Version: 0.8.6
```

After creating a workspace virtual environment and installing dependencies:

```text
Successfully installed ... google-generativeai-0.8.6 ... matplotlib-3.10.9 numpy-2.4.6 pillow-12.2.0 pyyaml-6.0.3 rosbags-0.11.3 ...
```

Status: **PASS** for workspace Python dependencies via `.venv`.

## Real Run Evidence

KITTI ROS2 bags were created and validated with ROS2 inside Docker:

```text
urban_01: 540 messages, 5 topics, 108 messages/topic
highway_01: 770 messages, 5 topics, 154 messages/topic
```

Rain perturbation was applied to the real `urban_01` bag:

```text
Input:  /kitti/velo/pointcloud 108, left image 108, right image 108, IMU 108, GPS 108
Output: /kitti/velo/pointcloud 108, left image 108, right image 108, IMU 108, GPS 102
ROS2 bag info: 534 messages, 456.3 MiB, 5 topics
```

FAST-LIO2 real execution:

```text
baseline urban_01 odometry: 94 /localization/odometry messages
rain urban_01 odometry:     94 /localization/odometry messages
rain vs baseline metrics:   SUCCESS, 94 poses, 4.812 m 3D RMSE, 0.649 m lateral RMSE, 0.473 deg yaw RMSE, 0 tracking-loss events
```
