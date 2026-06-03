# Coding Agent Task: Localization Robustness Evaluation Pipeline

## Mission Statement

Build a fully automated, end-to-end **Localization Robustness Evaluation Pipeline** that:
1. Runs multiple SLAM/localization algorithms on a public multi-sensor dataset (LiDAR + Camera + IMU + GPS)
2. First produces a **golden reference** trajectory for each algorithm (clean, unperturbed data)
3. Then systematically injects sensor degradations (perturbations) based on the scenario library defined below
4. After every scenario run, computes deviation metrics vs. the golden reference and saves analysis files + plots
5. After all runs, calls the **Gemini Flash API** to produce a human-readable summary report

Everything must run inside **Docker** (Docker Compose with separate service containers). The system is designed to be fully unattended — one `docker compose up` triggers the entire pipeline from dataset download to final report.

---

## Target Hardware (Development Machine)

- **CPU:** Intel i5 (laptop)
- **RAM:** 12 GB DDR4
- **GPU:** NVIDIA RTX 4060 8 GB VRAM (CUDA 12.x)
- **OS:** Ubuntu 22.04 (assumed)

**Portability rule:** All resource limits (CPU threads, GPU memory fractions, parallelism) must be read from a single top-level `config/pipeline.yaml` file. If the pipeline is copied to a faster machine (e.g. 64 GB RAM, 24 GB GPU), editing that config file and re-running should automatically use more resources. Never hardcode thread counts or memory sizes inside scripts.

---

## Dataset Selection

### Decision Criteria
You (the agent) must evaluate and pick **one** dataset from the two candidates. Apply these criteria in order:

1. All four sensor modalities present: **LiDAR + Camera + IMU + GPS** in every sequence
2. Available as **ROS2 bags** or easily convertible (rosbags Python library or ros2 bag convert)
3. Sequence length ≥ 500 m (to show drift meaningfully)
4. Ground truth trajectory available (for golden standard comparison)
5. Download size manageable (prefer sequences under 10 GB each; download 2–3 sequences)

### Candidates
- **UrbanNavDataset** — `https://github.com/IPNL-POLYU/UrbanNavDataset`
  - Outdoor urban, Hong Kong, multiple sequences
  - Has LiDAR (Velodyne VLP-16 or Ouster), stereo cameras, IMU, RTK-GPS
  - Some sequences are ROS1 bags; conversion needed
  - Ground truth: RTK GPS at cm accuracy

- **KITTI Raw Dataset** — `https://www.cvlibs.net/datasets/kitti/raw_data.php`
  - Well-documented, city+highway+campus sequences
  - All four sensors (Velodyne HDL-64, cameras, IMU, GPS)
  - ROS1 bag wrappers widely available (kitti2bag / kitti_to_rosbag)
  - Ground truth: GPS/IMU oxts at ~0.1 m accuracy
  - Downside: 64-beam LiDAR (algorithms all support it, but heavier than VLP-16)

**Recommendation guidance:** KITTI is more universally tested with all five target algorithms. UrbanNavDataset has more realistic urban degradation (urban canyons, tunnels). Pick whichever has cleaner all-sensor ROS2 bag support and document your reasoning in `docs/dataset_choice.md`. Download at minimum **two sequences** (one urban/structured, one open/less-structured) so scenarios can show contrast.

---

## Algorithms to Evaluate

Run exactly these **five algorithms** as configurable pipeline entries. Each is treated as a **black box** — the pipeline does not modify algorithm internals, only sensor inputs.

| ID | Algorithm | Category | ROS2 Source |
|----|-----------|----------|-------------|
| `fast_livo2` | FAST-LIVO2 | LVIO #1 | `github.com/hku-mars/FAST-LIVO2` (ROS2 port: `github.com/VIS4ROB-lab/FAST-LIVO2-ROS2`) |
| `lio_sam` | LIO-SAM | LVIO #2 (LiDAR+GPS loop) | `github.com/TixiaoShan/LIO-SAM` branch `ros2` |
| `glim` | GLIM | LVIO #3 | `github.com/koide3/glim` (Docker: `koide3/glim_ros2`) |
| `fast_lio2` | FAST-LIO2 | LIO #1 | `github.com/hku-mars/FAST_LIO` (ROS2 port) |
| `orb_slam3` | ORB-SLAM3 | VIO #1 | `github.com/UZ-SLAMLab/ORB_SLAM3` (ROS2 wrapper) |

Each algorithm entry in `config/pipeline.yaml` has:
```yaml
algorithms:
  fast_livo2:
    enabled: true
    docker_image: "localization_eval/fast_livo2:latest"
    launch_file: "fast_livo2.launch.py"
    output_topic: "/fast_livo2/odometry"
    sensors_required: [lidar, camera, imu]
  lio_sam:
    enabled: true
    docker_image: "localization_eval/lio_sam:latest"
    launch_file: "lio_sam.launch.py"
    output_topic: "/lio_sam/odometry"
    sensors_required: [lidar, imu, gps]
  glim:
    enabled: true
    docker_image: "koide3/glim_ros2:latest"
    launch_file: "glim_ros2.launch.py"
    output_topic: "/glim/odometry"
    sensors_required: [lidar, imu]
  fast_lio2:
    enabled: true
    docker_image: "localization_eval/fast_lio2:latest"
    launch_file: "fast_lio2.launch.py"
    output_topic: "/fast_lio2/odometry"
    sensors_required: [lidar, imu]
  orb_slam3:
    enabled: true
    docker_image: "localization_eval/orb_slam3:latest"
    launch_file: "orb_slam3.launch.py"
    output_topic: "/orb_slam3/odometry"
    sensors_required: [camera, imu]
```

To run only specific algorithms: set `enabled: false` for others. To add a new algorithm later: add a new block — no other file should need changing.

---

## Repository Structure

```
localization_eval/
├── config/
│   ├── pipeline.yaml              # master config (hardware, algorithms, scenarios, paths)
│   ├── perturbations/
│   │   ├── baseline.yaml          # all perturbations disabled
│   │   ├── low_light.yaml
│   │   ├── glare.yaml
│   │   ├── tunnel_transition.yaml
│   │   ├── rain.yaml
│   │   ├── fog.yaml
│   │   ├── foliage_occlusion.yaml
│   │   ├── partial_failure.yaml
│   │   ├── vibration.yaml
│   │   ├── imu_bias_drift.yaml
│   │   ├── combined_rain_low_light.yaml
│   │   └── combined_fog_vibration.yaml
│   └── topics/
│       ├── kitti_topics.yaml       # topic remapping for KITTI
│       └── urbannav_topics.yaml    # topic remapping for UrbanNavDataset
├── docker/
│   ├── base/
│   │   └── Dockerfile             # ROS2 Humble + common deps base image
│   ├── fast_livo2/
│   │   └── Dockerfile
│   ├── lio_sam/
│   │   └── Dockerfile
│   ├── fast_lio2/
│   │   └── Dockerfile
│   ├── orb_slam3/
│   │   └── Dockerfile
│   ├── perturbation_injector/
│   │   └── Dockerfile
│   ├── evaluator/
│   │   └── Dockerfile
│   └── orchestrator/
│       └── Dockerfile
├── docker-compose.yml
├── ros2_ws/
│   └── src/
│       ├── perturbation_injector/  # ROS2 package
│       ├── evaluator/              # ROS2 package
│       ├── topic_bridge/           # remapping & sync utilities
│       └── orchestrator/           # pipeline controller node
├── scripts/
│   ├── download_dataset.sh
│   ├── convert_bags.sh            # ROS1→ROS2 if needed
│   ├── run_pipeline.sh            # entrypoint: ./run_pipeline.sh --algo fast_livo2
│   └── generate_report.py         # calls Gemini API
├── data/
│   ├── raw/                       # downloaded dataset bags
│   ├── converted/                 # ROS2 bags after conversion
│   └── sequences/                 # symlinks per sequence used
├── results/
│   ├── golden/                    # per-algo golden trajectories
│   │   └── {algo}/{sequence}/trajectory.tum
│   ├── scenarios/
│   │   └── {algo}/{sequence}/{scenario}/
│   │       ├── trajectory.tum
│   │       ├── metrics.json
│   │       ├── deviation_report.txt
│   │       ├── plots/
│   │       │   ├── trajectory_comparison.png
│   │       │   ├── error_vs_time.png
│   │       │   ├── lateral_longitudinal_error.png
│   │       │   └── error_heatmap.png
│   │       └── gemini_summary.txt
│   └── final_report/
│       ├── cross_algo_comparison.png
│       ├── scenario_sensitivity_matrix.png
│       └── final_gemini_report.md
└── docs/
    ├── dataset_choice.md
    ├── architecture.md
    └── how_to_add_algorithm.md
```

---

## Docker Compose Architecture

```
┌─────────────────────────────────────────────────────┐
│                  docker-compose.yml                  │
│                                                      │
│  [orchestrator]  ──controls──►  [algorithm_N]       │
│       │                              │               │
│       │                         publishes /odom      │
│       ▼                              │               │
│  [perturbation_injector]             │               │
│       │ (replays bag with           │               │
│       │  modifications applied)      │               │
│       │                              ▼               │
│       └──────────────────►  [evaluator]              │
│                                  │                   │
│                          saves metrics,              │
│                          plots, txt reports          │
│                                  │                   │
│                          [generate_report.py]        │
│                          (Gemini API call)           │
└─────────────────────────────────────────────────────┘
```

All services share:
- A ROS2 DDS network (same `ROS_DOMAIN_ID`)
- A shared `/results` volume mount
- A shared `/data` volume mount (read-only for algorithm containers)
- GPU passthrough via `nvidia` runtime for algorithm containers that support CUDA

---

## Service Specifications

### 1. `orchestrator` service
**Language:** Python 3.10+
**Responsibilities:**
- Reads `config/pipeline.yaml` to determine which algorithms and scenarios to run
- For each `(algorithm, sequence, scenario)` triple:
  1. Signals `perturbation_injector` to start replaying the bag with the given perturbation YAML
  2. Signals the target algorithm container to launch
  3. Waits for algorithm `/odometry` topic to start publishing
  4. Waits for bag replay to finish (or timeout from config)
  5. Signals `evaluator` to compute metrics
  6. Calls `generate_report.py` with the metrics JSON for Gemini summary
  7. Advances to next triple
- Writes a `pipeline_state.json` so the pipeline can be **resumed** if interrupted (check each triple before starting it — skip if `results/{algo}/{seq}/{scenario}/metrics.json` already exists)
- Prints a live progress table to stdout: `Algorithm | Sequence | Scenario | Status | Elapsed`

### 2. `perturbation_injector` service
**Language:** Python 3.10 + ROS2 Humble
**Package name:** `perturbation_injector`
**Node name:** `sensor_perturbation_node`

This node reads a ROS2 bag file and re-publishes all topics **after applying the configured perturbations in real time**. It is NOT a bag replay tool — it is a transform layer sitting between the bag player and the algorithm.

Implementation approach:
- Use `rosbag2_py` to read the bag
- For each message, apply the relevant perturbation transform (see Perturbation Library below)
- Publish the modified message on the same topic
- Publish unmodified messages for sensors whose perturbation is disabled
- Respect the original message timestamps (do not change header stamps unless `global.time_offset` is set)
- Publish at the original rate (use `rclpy` rate control based on original timestamps)

The node accepts a ROS2 parameter `perturbation_yaml_path` pointing to the active perturbation YAML.

### 3. Algorithm services (`fast_livo2`, `lio_sam`, `glim`, `fast_lio2`, `orb_slam3`)
Each is a separate Docker container built from its own Dockerfile. Each Dockerfile must:
- Start from the shared `base` image (ROS2 Humble + CUDA 12 + OpenCV 4.x + PCL 1.12 + Eigen 3.4)
- Clone the algorithm repo at a pinned commit hash (for reproducibility)
- Build the ROS2 workspace (`colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release`)
- Include a launch file `{algo}.launch.py` that:
  - Subscribes to the standard remapped topics (from `config/topics/{dataset}_topics.yaml`)
  - Publishes pose on `/localization/odometry` (nav_msgs/Odometry) — **all algorithms remap to this common output topic**
  - Also publishes `/localization/path` (nav_msgs/Path) for visualization

Algorithm containers are **idle by default** and started on-demand by the orchestrator via `docker exec` or a ROS2 lifecycle node pattern. Use **ROS2 lifecycle nodes** where the algorithm supports it; otherwise wrap with a shell script that launches on SIGCONT and kills on SIGTERM.

### 4. `evaluator` service
**Language:** Python 3.10 + ROS2 Humble
**Package name:** `evaluator`

Subscribes to `/localization/odometry` and records all poses to a TUM-format file during a run. After a run completes (signalled by orchestrator), performs:

**Trajectory alignment:**
- Load golden trajectory TUM file and current run TUM file
- Align by timestamp interpolation (golden poses interpolated to test timestamps)
- Apply SE3 alignment (Umeyama method) to remove initial pose offset

**Per-frame error computation:**
- Longitudinal error (along direction of travel, metres)
- Lateral error (perpendicular to travel, metres)  
- Vertical error (metres)
- Yaw error (degrees)
- Full 3D position error (metres)
- Full orientation error (degrees, axis-angle magnitude)

**Summary metrics (saved to `metrics.json`):**
```json
{
  "algorithm": "fast_livo2",
  "sequence": "kitti_urban_01",
  "scenario": "rain",
  "perturbation_params": { ... },
  "duration_seconds": 124.3,
  "num_poses": 1243,
  "rmse": {
    "longitudinal_m": 0.23,
    "lateral_m": 0.18,
    "vertical_m": 0.09,
    "yaw_deg": 1.2,
    "position_3d_m": 0.31
  },
  "mean": { ... },
  "median": { ... },
  "max": { ... },
  "p95": { ... },
  "drift_rate_m_per_s": 0.0018,
  "time_to_failure_s": null,
  "failure_threshold_m": 5.0,
  "tracking_lost": false,
  "tracking_loss_events": 0
}
```

**Deviation report (saved to `deviation_report.txt`):**
```
===========================================================
LOCALIZATION DEVIATION REPORT
===========================================================
Algorithm  : FAST-LIVO2
Sequence   : kitti_urban_01  
Scenario   : rain (intensity=0.4, point_drop=0.2)
Run date   : 2025-06-03 14:32:11 UTC
Duration   : 124.3 s  |  1243 pose estimates
===========================================================

GOLDEN REFERENCE COMPARISON
----------------------------
Baseline RMSE (no perturbation) :  pos=0.08m  yaw=0.4°
This run RMSE                   :  pos=0.31m  yaw=1.2°
Degradation factor              :  pos=3.9x   yaw=3.0x

ERROR BREAKDOWN
---------------
                  RMSE    Mean    Median   P95     Max
Longitudinal (m): 0.23    0.19    0.14     0.51    1.23
Lateral (m):      0.18    0.14    0.10     0.41    0.98
Vertical (m):     0.09    0.07    0.05     0.19    0.44
Yaw (deg):        1.20    0.98    0.72     2.81    5.44
3D Position (m):  0.31    0.24    0.18     0.68    1.47

TEMPORAL ANALYSIS
-----------------
Drift rate        : 0.0018 m/s
Time to 5m error  : not reached
Tracking losses   : 0

WORST PERIODS
-------------
[t=45.2s - t=52.1s]  Peak lateral error: 0.98m  (heavy rain streak window)
[t=89.0s - t=94.3s]  Peak yaw error: 5.44°      (GPS multipath event)

SENSOR CONTRIBUTION ESTIMATE
-----------------------------
Camera perturbation active  : YES (rain streaks, droplets)
LiDAR perturbation active   : YES (point_drop=0.20, intensity_scale=0.8)
IMU perturbation active     : NO
GPS perturbation active     : YES (multipath, drop_prob=0.1)
===========================================================
```

**Plots (saved to `plots/`):**

All plots use a dark theme (`matplotlib` style `dark_background`) for visual consistency. Save as PNG at 150 DPI minimum.

1. `trajectory_comparison.png` — 2D top-down XY plot: golden trajectory (white) + test trajectory (colored by error magnitude, colormap `plasma`). Add error ellipses at worst 5 points.

2. `error_vs_time.png` — 4-panel time series: longitudinal error, lateral error, yaw error, 3D position error. Shade the perturbation-active time windows. Mark tracking loss events with vertical red lines.

3. `lateral_longitudinal_error.png` — scatter plot of lateral vs longitudinal error per pose, colored by time. Add marginal histograms on each axis.

4. `error_heatmap.png` — the 2D XY path with a heatmap overlay where colour = 3D error magnitude at that location. Shows spatially where the algorithm struggles.

---

## Perturbation Library

Implement all perturbations as Python classes inheriting from a base `Perturbation` class. Each class has a `apply(msg, params)` method that takes a ROS2 message and returns a modified message (or `None` to drop it).

### Complete Perturbation Specifications

#### LIDAR Perturbations (input: `sensor_msgs/PointCloud2`)

```python
class LidarGaussianNoise(Perturbation):
    """Add Gaussian noise to point XYZ coordinates."""
    params: noise_std: float  # metres, e.g. 0.02

class LidarPointDropout(Perturbation):
    """Randomly remove a fraction of points."""
    params: dropout_fraction: float  # 0.0-1.0, e.g. 0.1

class LidarIntensityScale(Perturbation):
    """Scale intensity/reflectivity channel."""
    params: intensity_scale: float  # <1.0 reduces reflectivity

class LidarBeamOcclusion(Perturbation):
    """Remove points in a spatial bounding box (simulates tree/wall occlusion)."""
    params: regions: list[list[float]]  # e.g. [[-1,1],[10,20]] = x in [-1,1], z in [10,20]

class LidarAzimuthOcclusion(Perturbation):
    """Remove points in an azimuth angle sector (simulates foliage blocking beams)."""
    params: azimuth_start: float  # degrees
            azimuth_end: float    # degrees
            point_drop_ratio: float

class LidarReflectiveGhosts(Perturbation):
    """In a reflective region: drop real points + add ghost points P' = P + N(0,σ²)."""
    params: x_min, x_max, y_min, y_max: float
            point_drop_ratio: float
            ghost_point_ratio: float
            noise_std: float

class LidarFogAttenuation(Perturbation):
    """Attenuate intensity of far points, remove some, add backscatter ghosts."""
    params: visibility_distance: float  # metres
            intensity_scale: float      # α < 1
            point_drop_ratio: float
            backscatter_ratio: float

class LidarVibration(Perturbation):
    """Apply random SE3 perturbation to entire point cloud frame."""
    params: position_sigma: float  # metres
            yaw_sigma_deg: float
```

#### Camera Perturbations (input: `sensor_msgs/Image`)

```python
class CameraBrightnessNoise(Perturbation):
    """Scale brightness then add Gaussian noise: I'' = αI + N(0,σ²)."""
    params: brightness_factor: float  # α, 0-1 for darkening
            noise_std: float          # 0-255 scale

class CameraGlare(Perturbation):
    """Saturate bright regions: I' = min(αI, 255) where I > threshold."""
    params: intensity_threshold: int   # e.g. 220
            brightness_scale: float    # α > 1

class CameraMotionBlur(Perturbation):
    """Apply linear motion blur kernel."""
    params: blur_kernel: int  # kernel size, odd number

class CameraExposureShift(Perturbation):
    """Shift exposure by N stops: I' = I * 2^stops."""
    params: exposure_shift: float  # negative = darker

class CameraRainDroplets(Perturbation):
    """Overlay synthetic rain streaks and droplet blur."""
    params: intensity: float       # 0-1
            streak_length: int     # pixels
            contrast_scale: float
            droplet_count: int
            droplet_blur_kernel: int

class CameraLensFlare(Perturbation):
    """Add synthetic lens flare bloom."""
    params: intensity: float

class CameraFoliageMask(Perturbation):
    """Replace image region with darkened mask (occlusion simulation)."""
    params: x_min, x_max, y_min, y_max: int  # pixel coords
            opacity: float

class CameraFogHaze(Perturbation):
    """Apply atmospheric attenuation: I' = I * e^(-β)."""
    params: density: float          # β coefficient
            overlay_opacity: float

class CameraTunnelTransition(Perturbation):
    """Linearly ramp brightness across a time window (exposure adaptation sim)."""
    params: start_time: float       # seconds from bag start
            end_time: float
            brightness_start: float
            brightness_end: float

class CameraFrozenFrames(Perturbation):
    """Replace N% of frames with previous frame (partial sensor failure)."""
    params: freeze_ratio: float
            start_time: float
            end_time: float

class CameraVibrationBlur(Perturbation):
    """Blur + random rotation per frame (camera shake)."""
    params: blur_kernel: int
            rotation_std_deg: float
```

#### IMU Perturbations (input: `sensor_msgs/Imu`)

```python
class ImuGyroBias(Perturbation):
    """Add constant bias to gyroscope axes."""
    params: gyro_bias: list[float]  # [x, y, z] rad/s

class ImuAccelNoise(Perturbation):
    """Add Gaussian noise to accelerometer."""
    params: accel_noise: float  # m/s² std

class ImuAccelBiasDrift(Perturbation):
    """Add random-walk bias to accelerometer."""
    params: accel_bias_drift: float  # m/s³

class ImuBiasDriftLinear(Perturbation):
    """Time-varying linear bias: M' = M + b*t."""
    params: gyro_drift_rate: float   # rad/s per second
            accel_drift_rate: float  # m/s² per second

class ImuTemperatureScaleFactor(Perturbation):
    """Scale factor error: M' = (1+ε)M + b*t."""
    params: scale_factor_error: float  # ε

class ImuVibrationNoise(Perturbation):
    """High-frequency Gaussian noise on both axes."""
    params: accel_noise_std: float
            gyro_noise_std: float

class ImuFrozen(Perturbation):
    """Freeze IMU at previous value: M'_t = M_{t-1}."""
    params: freeze_ratio: float
            start_time: float
            end_time: float
```

#### GPS Perturbations (input: `sensor_msgs/NavSatFix`)

```python
class GpsDropout(Perturbation):
    """Drop GPS messages randomly."""
    params: drop_probability: float  # fraction of messages to drop

class GpsMultipath(Perturbation):
    """Add sine-wave error to lat/lon (urban canyon reflection simulation)."""
    params: amplitude: float   # metres
            frequency: float   # Hz

class GpsPartialFailure(Perturbation):
    """Drop GPS messages in a time window."""
    params: start_time: float
            end_time: float
            message_drop_ratio: float
```

#### Global Perturbations

```python
class GlobalTimeOffset(Perturbation):
    """Add clock skew to all message headers."""
    params: time_offset: float  # seconds
```

---

## Scenario Library (Perturbation YAML Files)

Create all files in `config/perturbations/`. Each file is a complete perturbation spec; all unmentioned sensors default to `enabled: false`.

### `baseline.yaml`
```yaml
# All perturbations disabled — produces golden reference
perturbations:
  lidar: {}
  camera: {}
  imu: {}
  gps: {}
  global: {}
```

### `low_light.yaml`
```yaml
perturbations:
  camera:
    brightness_noise:
      enabled: true
      brightness_factor: 0.4
      noise_std: 10
  lidar:
    low_light:
      enabled: false   # VLP-16 unaffected by lighting
```

### `glare.yaml`
```yaml
perturbations:
  camera:
    glare:
      enabled: true
      intensity_threshold: 200
      brightness_scale: 1.8
    lens_flare:
      enabled: true
      intensity: 0.4
  lidar:
    reflective_ghosts:
      enabled: true
      x_min: 5
      x_max: 15
      y_min: -3
      y_max: 3
      point_drop_ratio: 0.2
      ghost_point_ratio: 0.1
      noise_std: 0.2
```

### `tunnel_transition.yaml`
```yaml
perturbations:
  camera:
    tunnel_transition:
      enabled: true
      start_time: 20.0
      end_time: 35.0
      brightness_start: 1.0
      brightness_end: 0.15
  lidar:
    tunnel_transition:
      enabled: false
```

### `rain.yaml`
```yaml
perturbations:
  camera:
    rain_droplets:
      enabled: true
      intensity: 0.4
      streak_length: 15
      contrast_scale: 0.8
      droplet_count: 20
      droplet_blur_kernel: 11
  lidar:
    point_dropout:
      enabled: true
      dropout_fraction: 0.20
    reflective_ghosts:
      enabled: true
      x_min: -20
      x_max: 20
      y_min: -20
      y_max: 20
      point_drop_ratio: 0.0
      ghost_point_ratio: 0.05
      noise_std: 0.1
    intensity_scale:
      enabled: true
      intensity_scale: 0.8
  gps:
    dropout:
      enabled: true
      drop_probability: 0.05
```

### `fog.yaml`
```yaml
perturbations:
  camera:
    fog_haze:
      enabled: true
      density: 0.5
      overlay_opacity: 0.3
  lidar:
    fog_attenuation:
      enabled: true
      visibility_distance: 30.0
      intensity_scale: 0.7
      point_drop_ratio: 0.15
      backscatter_ratio: 0.05
```

### `foliage_occlusion.yaml`
```yaml
perturbations:
  camera:
    foliage_mask:
      enabled: true
      x_min: 200
      x_max: 600
      y_min: 100
      y_max: 350
      opacity: 0.85
  lidar:
    azimuth_occlusion:
      enabled: true
      azimuth_start: 330
      azimuth_end: 30
      point_drop_ratio: 0.9
```

### `partial_failure.yaml`
```yaml
perturbations:
  camera:
    frozen_frames:
      enabled: true
      start_time: 30.0
      end_time: 50.0
      freeze_ratio: 0.4
  lidar:
    point_dropout:
      enabled: true
      dropout_fraction: 0.3
      start_time: 30.0
      end_time: 50.0
  imu:
    frozen:
      enabled: true
      start_time: 30.0
      end_time: 50.0
      freeze_ratio: 0.3
  gps:
    partial_failure:
      enabled: true
      start_time: 30.0
      end_time: 50.0
      message_drop_ratio: 0.6
```

### `vibration.yaml`
```yaml
perturbations:
  camera:
    vibration_blur:
      enabled: true
      blur_kernel: 9
      rotation_std_deg: 1.0
  lidar:
    vibration:
      enabled: true
      position_sigma: 0.05
      yaw_sigma_deg: 0.5
  imu:
    vibration_noise:
      enabled: true
      accel_noise_std: 0.2
      gyro_noise_std: 0.05
```

### `imu_bias_drift.yaml`
```yaml
perturbations:
  imu:
    bias_drift_linear:
      enabled: true
      gyro_drift_rate: 0.001
      accel_drift_rate: 0.01
    temperature_scale_factor:
      enabled: true
      scale_factor_error: 0.02
```

### `combined_rain_low_light.yaml`
```yaml
# Realistic night rain scenario
perturbations:
  camera:
    brightness_noise:
      enabled: true
      brightness_factor: 0.35
      noise_std: 12
    rain_droplets:
      enabled: true
      intensity: 0.5
      streak_length: 20
      contrast_scale: 0.75
      droplet_count: 30
      droplet_blur_kernel: 13
  lidar:
    point_dropout:
      enabled: true
      dropout_fraction: 0.25
    intensity_scale:
      enabled: true
      intensity_scale: 0.75
  gps:
    dropout:
      enabled: true
      drop_probability: 0.1
```

### `combined_fog_vibration.yaml`
```yaml
# Rough road in morning fog scenario
perturbations:
  camera:
    fog_haze:
      enabled: true
      density: 0.6
      overlay_opacity: 0.35
    vibration_blur:
      enabled: true
      blur_kernel: 7
      rotation_std_deg: 0.8
  lidar:
    fog_attenuation:
      enabled: true
      visibility_distance: 25.0
      intensity_scale: 0.65
      point_drop_ratio: 0.18
      backscatter_ratio: 0.06
    vibration:
      enabled: true
      position_sigma: 0.06
      yaw_sigma_deg: 0.6
  imu:
    vibration_noise:
      enabled: true
      accel_noise_std: 0.25
      gyro_noise_std: 0.06
```

---

## Pipeline Execution Flow

The complete execution for each `(algorithm, sequence, scenario)` triple:

```
Step 1: Pre-check
  └─ Does results/{algo}/{seq}/{scenario}/metrics.json exist?
     └─ YES → skip (resumable pipeline)
     └─ NO  → proceed

Step 2: Start algorithm container (if not running)
  └─ docker compose start {algo}
  └─ Wait for ROS2 node to become active (ros2 node list | grep {algo}, timeout=60s)

Step 3: Start perturbation injector
  └─ docker compose exec perturbation_injector \
       ros2 run perturbation_injector sensor_perturbation_node \
         --ros-args -p perturbation_yaml:=/config/perturbations/{scenario}.yaml \
                    -p bag_path:=/data/sequences/{seq}/ \
                    -p playback_rate:=1.0

Step 4: Wait for bag replay to complete
  └─ Monitor /perturbation_injector/status topic
  └─ Timeout = bag_duration * 1.5 (from config)

Step 5: Signal evaluator to compute metrics
  └─ ros2 service call /evaluator/compute_metrics \
       evaluator_msgs/ComputeMetrics \
       {golden_tum: "/results/golden/{algo}/{seq}/trajectory.tum", \
        output_dir: "/results/scenarios/{algo}/{seq}/{scenario}/"}

Step 6: Wait for evaluator to finish (timeout=120s)

Step 7: Generate Gemini summary
  └─ python3 scripts/generate_report.py \
       --metrics /results/scenarios/{algo}/{seq}/{scenario}/metrics.json \
       --output  /results/scenarios/{algo}/{seq}/{scenario}/gemini_summary.txt

Step 8: Stop algorithm ROS2 node (keep container running for next scenario)
  └─ ros2 lifecycle set /{algo}_node shutdown
  └─ OR: send SIGTERM to algorithm launch process

Step 9: Log progress to pipeline_state.json
```

**Golden run** = Step 3 with `baseline.yaml` (no perturbations). Golden trajectory saved to `results/golden/{algo}/{seq}/trajectory.tum`. Golden metrics saved for baseline comparison.

---

## Gemini Flash API Integration

**Model:** `gemini-2.0-flash-exp` or `gemini-1.5-flash` (whichever is available on the free tier at time of implementation; check `https://ai.google.dev/pricing` and pick the most capable free model)

**API key:** Read from environment variable `GEMINI_API_KEY` (set in `.env` file, which is gitignored)

**Per-scenario call** (`generate_report.py --mode scenario`):

```python
prompt = f"""
You are an expert in robot localization and SLAM systems. Analyze the following 
localization performance metrics from a robustness test.

Algorithm: {metrics['algorithm']}
Sequence: {metrics['sequence']}  
Scenario: {metrics['scenario']}
Active perturbations: {json.dumps(metrics['perturbation_params'], indent=2)}

BASELINE (no perturbation) metrics:
{json.dumps(baseline_metrics, indent=2)}

THIS RUN metrics:
{json.dumps(metrics, indent=2)}

Write a 3-5 paragraph technical summary covering:
1. Overall impact: how much did this scenario degrade localization? (cite specific numbers)
2. Which error component was most affected (lateral, longitudinal, yaw) and why this makes 
   physical sense given the sensor perturbations applied
3. Any signs of catastrophic failure (tracking loss, sudden drift) vs graceful degradation
4. Which sensor degradation likely caused the most damage, and why
5. One concrete recommendation for making this algorithm more robust to this scenario

Be specific, cite numbers from the metrics, and write in a technical but readable style.
"""
```

**Final cross-algorithm call** (`generate_report.py --mode final`):

After all algorithms and scenarios are done, load all `metrics.json` files and call Gemini with a summary table asking for:
- Which algorithm was most robust overall across all scenarios
- Which scenario was most damaging across all algorithms
- Algorithm-scenario pairing recommendations (which algo to use when you expect fog, etc.)
- Surprising findings
- Recommended stack for the Jetson Orin Nano given all test results

Save as `results/final_report/final_gemini_report.md`.

---

## master `config/pipeline.yaml`

```yaml
# ================================================================
# Master Pipeline Configuration
# Edit this file to adapt to different hardware or run subsets
# ================================================================

hardware:
  cpu_threads: 6           # i5 has ~6 logical cores; set to nproc on faster machines
  gpu_vram_gb: 8           # RTX 4060 8GB; algorithms will respect this
  ram_gb: 12
  cuda_visible_devices: "0"
  # On faster hardware: increase threads, set parallel_algos: 2 to run two algos at once
  parallel_algos: 1        # number of algorithms to run simultaneously (set 1 for 12GB RAM)

ros:
  domain_id: 42
  ros_distro: humble

dataset:
  name: kitti              # or: urbannav — agent fills this in after evaluation
  sequences:
    - id: "urban_01"
      bag_path: "/data/sequences/urban_01"
      duration_s: 180      # filled in after download
      description: "Urban driving, intersections"
    - id: "highway_01"  
      bag_path: "/data/sequences/highway_01"
      duration_s: 120
      description: "Open highway, less occlusion"
  ground_truth_format: tum   # or: kitti, or: navsat

algorithms:
  fast_livo2:
    enabled: true
    priority: 1
  lio_sam:
    enabled: true
    priority: 2
  glim:
    enabled: true
    priority: 3
  fast_lio2:
    enabled: true
    priority: 4
  orb_slam3:
    enabled: true
    priority: 5

scenarios:
  # Set enabled: false to skip a scenario in a partial run
  baseline:        { enabled: true,  description: "Golden reference — no perturbations" }
  low_light:       { enabled: true,  description: "Night/tunnel low illumination" }
  glare:           { enabled: true,  description: "Direct sunlight / headlights" }
  tunnel_transition: { enabled: true, description: "Auto-exposure lag entering/exiting tunnel" }
  rain:            { enabled: true,  description: "Rain on lens and in air" }
  fog:             { enabled: true,  description: "Fog/dust/haze reducing visibility" }
  foliage_occlusion: { enabled: true, description: "Tree branches / parked vehicles" }
  partial_failure: { enabled: true,  description: "Intermittent sensor dropout across all sensors" }
  vibration:       { enabled: true,  description: "Rough terrain / engine vibration" }
  imu_bias_drift:  { enabled: true,  description: "IMU temperature drift" }
  combined_rain_low_light:  { enabled: true, description: "Night rain (combined)" }
  combined_fog_vibration:   { enabled: true, description: "Rough road in fog (combined)" }

evaluation:
  failure_threshold_m: 5.0         # position error above this = failure
  tracking_loss_threshold_m: 10.0  # sudden jump = tracking lost
  max_run_timeout_multiplier: 1.5  # timeout = bag_duration * this
  alignment_method: umeyama        # SE3 trajectory alignment before error computation

gemini:
  api_key_env: "GEMINI_API_KEY"
  model: "gemini-2.0-flash-exp"    # agent: update to latest free Flash model available
  mode: per_scenario_and_final     # options: per_scenario_only, final_only, per_scenario_and_final
  max_output_tokens: 1024

output:
  results_base: "/results"
  plot_dpi: 150
  plot_style: "dark_background"
  save_rosbags: false              # set true to save perturbed bags (uses lots of disk)
```

---

## Docker Compose File Structure

```yaml
# docker-compose.yml (abbreviated — agent expands this fully)
version: "3.9"

x-ros-common: &ros-common
  environment:
    - ROS_DOMAIN_ID=42
    - RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  network_mode: host
  volumes:
    - ./config:/config:ro
    - ./results:/results
    - ./data:/data:ro

services:
  orchestrator:
    <<: *ros-common
    build: docker/orchestrator
    volumes:
      - ./config:/config:ro
      - ./results:/results
      - ./data:/data:ro
      - /var/run/docker.sock:/var/run/docker.sock  # to control other containers
    depends_on: [perturbation_injector, evaluator]
    command: python3 /app/orchestrator.py --config /config/pipeline.yaml
    env_file: .env

  perturbation_injector:
    <<: *ros-common
    build: docker/perturbation_injector
    volumes:
      - ./config:/config:ro
      - ./data:/data:ro

  evaluator:
    <<: *ros-common
    build: docker/evaluator
    volumes:
      - ./config:/config:ro
      - ./results:/results

  fast_livo2:
    <<: *ros-common
    build: docker/fast_livo2
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=all
      - ROS_DOMAIN_ID=42
    profiles: ["algo"]  # only started on demand

  lio_sam:
    <<: *ros-common
    build: docker/lio_sam
    runtime: nvidia
    profiles: ["algo"]

  glim:
    image: koide3/glim_ros2:latest
    <<: *ros-common
    runtime: nvidia
    profiles: ["algo"]

  fast_lio2:
    <<: *ros-common
    build: docker/fast_lio2
    runtime: nvidia
    profiles: ["algo"]

  orb_slam3:
    <<: *ros-common
    build: docker/orb_slam3
    runtime: nvidia
    profiles: ["algo"]
```

---

## Final Cross-Algorithm Comparison Outputs

After all algorithms and all scenarios complete, the evaluator generates:

### `cross_algo_comparison.png`
Grouped bar chart: X-axis = scenarios, Y-axis = RMSE position error (metres). One bar colour per algorithm. Show error bars (±1 std across sequences). Dark theme.

### `scenario_sensitivity_matrix.png`
Heatmap: rows = algorithms, columns = scenarios. Cell value = degradation factor (this_run_rmse / baseline_rmse). Colormap: `RdYlGn_r` (green=low degradation, red=high). Annotate each cell with the numeric value. Title: "Localization Degradation Factor by Algorithm and Scenario".

### `final_gemini_report.md`
Structure:
```markdown
# Localization Robustness Final Report
Generated: {date}  |  Algorithms: {list}  |  Sequences: {list}

## Executive Summary
{Gemini paragraph: 3-4 sentences on overall findings}

## Algorithm Rankings by Robustness
{Table: rank, algorithm, mean degradation factor, worst scenario}

## Scenario Impact Ranking  
{Table: rank, scenario, mean degradation across algos, most/least affected algo}

## Algorithm-Scenario Pairing Guide
{Gemini: when to use each algorithm given expected conditions}

## Key Findings
{Gemini: 5 bullet points of surprising or important findings}

## Recommended Stack for Jetson Orin Nano
{Gemini: recommendation with specific reasoning from the test data}

## Appendix: Full Metrics Table
{Auto-generated table of all metrics.json values}
```

---

## Implementation Notes and Edge Cases

### ROS1 Bag Conversion
If the chosen dataset uses ROS1 bags, use `rosbags` Python library (no ROS1 installation needed):
```bash
pip install rosbags
rosbags-convert --src input.bag --dst output/ --dst-typestore ros2_humble
```

### Topic Remapping
All algorithm-specific topic names must be remapped at launch time using `config/topics/{dataset}_topics.yaml`. Example KITTI mapping:
```yaml
remappings:
  lidar_in:  /kitti/velo/pointcloud  →  /localization/lidar/pointcloud
  camera_in: /kitti/camera/color/left/image_raw  →  /localization/camera/image_raw
  imu_in:    /kitti/oxts/imu  →  /localization/imu/data
  gps_in:    /kitti/oxts/gps/fix  →  /localization/gps/fix
  odom_out:  /{algo}/odometry  →  /localization/odometry
```

### Time Synchronization
The perturbation injector must publish all sensor topics with synchronized timestamps. Use `message_filters.ApproximateTimeSynchronizer` in the evaluator to align odometry output with ground truth.

### Tracking Loss Detection
In the evaluator, flag tracking loss if:
- Position jump between consecutive poses > `tracking_loss_threshold_m` (10m default)
- OR no odometry message received for > 2.0 seconds during active bag replay

### GPU Memory Management
- `fast_lio2` and `lio_sam`: CPU-primary, GPU not strictly required
- `fast_livo2`: GPU helps for dense map rendering
- `glim`: GPU-accelerated GICP (main beneficiary of GPU)
- `orb_slam3`: GPU optional (CUDA ORB detection faster)
On 8GB VRAM with `parallel_algos: 1`, only one algorithm uses GPU at a time — this is fine.

### Calibration Files
KITTI and UrbanNavDataset both provide factory calibration (camera intrinsics, LiDAR-camera extrinsics, IMU-LiDAR extrinsics). Package these into `config/calibration/{dataset}/` and mount into each algorithm container. Each algorithm's launch file reads from `/config/calibration/`.

### Error if Algorithm Fails to Start
If an algorithm fails to publish odometry within 60s of bag replay start:
- Log `ERROR: {algo} failed to initialize on {seq}/{scenario}`
- Write a `metrics.json` with `"status": "FAILED_TO_INIT"` and all numeric fields null
- Continue to the next triple (do not abort pipeline)
- Include failed runs in final report as failures

---

## Deliverables Checklist

The agent must produce all of the following before marking the task complete:

**Infrastructure:**
- [ ] `docker-compose.yml` — working, builds all images
- [ ] `docker/base/Dockerfile` — ROS2 Humble + CUDA 12 + OpenCV + PCL + Eigen
- [ ] `docker/fast_livo2/Dockerfile` — builds FAST-LIVO2 ROS2
- [ ] `docker/lio_sam/Dockerfile` — builds LIO-SAM ROS2 branch
- [ ] `docker/fast_lio2/Dockerfile` — builds FAST-LIO2 ROS2
- [ ] `docker/orb_slam3/Dockerfile` — builds ORB-SLAM3 ROS2 wrapper
- [ ] `docker/perturbation_injector/Dockerfile`
- [ ] `docker/evaluator/Dockerfile`
- [ ] `docker/orchestrator/Dockerfile`

**ROS2 Packages:**
- [ ] `ros2_ws/src/perturbation_injector/` — all perturbation classes implemented and tested
- [ ] `ros2_ws/src/evaluator/` — trajectory alignment, all metrics, all 4 plots
- [ ] `ros2_ws/src/orchestrator/` — full pipeline state machine

**Config:**
- [ ] `config/pipeline.yaml` — complete master config
- [ ] `config/perturbations/*.yaml` — all 12 scenario files
- [ ] `config/topics/kitti_topics.yaml` and/or `urbannav_topics.yaml`
- [ ] `config/calibration/{dataset}/` — calibration files or download instructions

**Scripts:**
- [ ] `scripts/download_dataset.sh` — downloads and organises chosen dataset
- [ ] `scripts/convert_bags.sh` — ROS1→ROS2 conversion if needed
- [ ] `scripts/run_pipeline.sh` — single entrypoint with `--algo` and `--scenario` flags for partial runs
- [ ] `scripts/generate_report.py` — Gemini API integration, both modes

**Documentation:**
- [ ] `docs/dataset_choice.md` — reasoning for dataset selection
- [ ] `docs/architecture.md` — system diagram and component descriptions
- [ ] `docs/how_to_add_algorithm.md` — step-by-step guide
- [ ] `README.md` — quickstart: prerequisites, setup, running the full pipeline

**`.env.example`:**
```
GEMINI_API_KEY=your_key_here
```

---

## Quickstart Commands (for README)

```bash
# 1. Prerequisites
# Install: Docker, Docker Compose v2, NVIDIA Container Toolkit

# 2. Clone and configure
git clone <this-repo> localization_eval
cd localization_eval
cp .env.example .env
# Edit .env: add your GEMINI_API_KEY
# Edit config/pipeline.yaml: set cpu_threads to your actual core count

# 3. Download dataset
./scripts/download_dataset.sh

# 4. Build all Docker images (takes 20-40 min first time)
docker compose build

# 5. Run full pipeline (runs for several hours — all 5 algos × 2 sequences × 12 scenarios)
docker compose up orchestrator

# 6. Run a single algorithm on a single scenario (for testing)
./scripts/run_pipeline.sh --algo fast_lio2 --scenario rain --sequence urban_01

# 7. View results
ls results/scenarios/
cat results/scenarios/fast_lio2/urban_01/rain/deviation_report.txt
cat results/scenarios/fast_lio2/urban_01/rain/gemini_summary.txt
open results/scenarios/fast_lio2/urban_01/rain/plots/

# 8. Final report (generated automatically at end, or manually)
python3 scripts/generate_report.py --mode final
cat results/final_report/final_gemini_report.md
```

---

## Success Criteria

The pipeline is considered complete and correct when:

1. `docker compose build` completes without errors on Ubuntu 22.04 with NVIDIA GPU
2. `./scripts/run_pipeline.sh --algo fast_lio2 --scenario baseline --sequence urban_01` produces a `trajectory.tum` file and `metrics.json` with non-null values
3. `./scripts/run_pipeline.sh --algo fast_lio2 --scenario rain --sequence urban_01` produces a `deviation_report.txt` showing higher errors than baseline
4. All 4 plots are generated and non-empty for the above run
5. `gemini_summary.txt` contains a coherent paragraph referencing specific metric values
6. After a full pipeline run, `results/final_report/scenario_sensitivity_matrix.png` shows a complete 5×12 grid
7. The pipeline can be interrupted and resumed without re-running completed triples

---

*End of agent task specification*
