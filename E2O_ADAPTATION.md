# E2O Dataset Adaptation Report

## Result

The framework is now dataset-selectable rather than UrbanNav-only. The seven existing integrations are preserved as black boxes and receive E2O data through a shared adapter layer:

1. FAST-LIO2
2. LVI-SAM
3. FAST-LIVO2
4. RTAB-Map
5. Adaptive-W LVIO wrapper
6. ORB-SLAM3
7. R3LIVE wrapper

UrbanNav remains available with `--dataset urbannav`; E2O is the default.

## E2O data contract used by the framework

| Interface | UrbanNav | E2O default | Adapter output |
|---|---|---|---|
| LiDAR | `/velodyne_points` | `/lidar103/velodyne_points` | algorithm-specific PointCloud2 topic |
| IMU | `/imu/data` | `/mavros/imu/data` | `/livox/imu` |
| Camera | `/zed2/camera/right/image_raw` | `/camera/color/image_raw` | `/camera/right/image_raw` and optional `/camera/image_raw` |
| Left camera | ZED2 left | unavailable | disabled on E2O |
| GPS | `/gps/fix_raw` or CSV | `/mavros/global_position/global` | shared GPS provider when explicitly enabled |
| Ground truth | UrbanNav INS text | TUM file | `/ground_truth_path`, `/ground_truth_odometry` |
| Body/world frames | `body`, `camera_init` | normalized aliases `body`, `camera_init` | shared standard output contract |

The middle LiDAR is the default because the supplied camera extrinsic is specifically `lidar103_to_front_camera`. The merged cloud can be selected with:

```bash
./run.sh --dataset e2o --algo fastlio2 --per 0 \
  --lidar-topic /merged/velodyne_points
```

That override is operational, but final calibration validity must be checked because the merged cloud’s exact preprocessing and per-point timing are not documented in the supplied archive.

## Adapter architecture

```text
E2O rosbag
  -> dataset_custom_bridge
       raw ROS messages -> custom benchmark messages
  -> custom_fastlio_adapter
       frame normalization
       perturbations
       CameraInfo publication
       point-time unit conversion
       optional Livox CustomMsg conversion
  -> unchanged localization algorithm
  -> standard_output_republisher
       /<algo>/odometry/local
       /<algo>/path/local
       /<algo>/odometry/output
       /<algo>/path/output
       /<algo>/status
  -> recorder + TUM/UrbanNav evaluator + RViz
```

No algorithm source code was changed for E2O. Configuration, launch arguments, topic adapters, TF publication, and evaluation logic were changed around the algorithms.

## Algorithm-specific adaptation

| Algorithm | E2O mode | Main changes | Important limitation |
|---|---|---|---|
| FAST-LIO2 | LiDAR + IMU | E2O topic adapter, 64-ring upper bound, dataset config, time normalization | IMU↔LiDAR transform and IMU noise are provisional |
| LVI-SAM | LiDAR + IMU | E2O LiDAR params; visual subsystem disabled | This remains LIO mode, not full visual LVI-SAM |
| FAST-LIVO2 | LiDAR + IMU + camera | E2O intrinsics and lidar103→camera transform | IMU extrinsic/time offsets remain provisional |
| RTAB-Map | FAST-LIO2 frontend + RTAB backend | Dataset-selectable FAST-LIO config | Result includes the existing FAST-LIO frontend design |
| Adaptive-W LVIO | existing FAST-LIO smoothing relay | Dataset-selectable frontend and E2O topics | Existing repo implementation is a relay/smoother, not the paper estimator |
| ORB-SLAM3 | monocular | E2O camera YAML, camera-body extrinsic, mono alias | Monocular scale is unobservable; evaluation uses Sim(2) alignment |
| R3LIVE | stable LIO fallback; optional visual mode | E2O camera/LiDAR config and PointCloud2→Livox CustomMsg adapter | Default output may come from FAST-LIO fallback; native visual mode is experimental |

Enable the existing R3LIVE visual attempt explicitly with:

```bash
./run.sh --dataset e2o --algo r3live --per 0 --r3live-vio on
```

## Calibration handling

### Verified values copied from the E2O archive

Front camera:

```text
fx = 668.02585977
fy = 658.80930843
cx = 657.26752359
cy = 363.16409155
D  = [-0.05078581, 0.08456123, -0.00046157, 0.00656211, -0.03406049]
```

The supplied transform is interpreted as:

```text
p_camera = R_camera_lidar103 * p_lidar103 + t_camera_lidar103
```

FAST-LIVO2 and R3LIVE receive that transform directly because their visual configuration uses LiDAR-to-camera projection. ROS TF and the ORB-SLAM3 body conversion use its inverse because a ROS `parent=body/lidar103, child=camera` transform stores the camera pose in the parent frame.

### Explicit provisional assumptions

The supplied files do **not** contain a verified IMU↔LiDAR transform, GNSS antenna lever arm, installed IMU noise model, LiDAR ring count, point-time unit, or sensor time offsets. The generated E2O files therefore declare rather than hide these assumptions:

```text
body origin                 = lidar103
IMU -> lidar103             = identity
GNSS lever arm              = zero
scan-line upper bound       = 64
point-time field            = time
point-time source unit      = auto-detect until bag inspection
camera resolution           = 1280x720
camera rate                 = 20.96 Hz
IMU/LiDAR and camera offsets= 0 s
```

Machine-readable details are in:

```text
wrappers/localization_benchmark/config/datasets/e2o/assumptions.yaml
```

Run the strict bag preflight before trusting a trajectory:

```bash
./inspect_bag.sh --dataset e2o --strict
```

It verifies topic types, image dimensions/encoding, point-cloud fields, sampled ring range, point-time unit, IMU units, and bag/GT timestamp overlap. After inspection, replace `point_time_unit: auto` in `datasets.yaml` with `s`, `ms`, `us`, or `ns`.

## Ground-truth treatment

The included file contains 30,852 valid TUM rows from `1723528213.157124` to `1723528521.663703`, approximately **308.51 seconds**. The metadata claims a 571-second recording, so the GT does not cover that full duration unless the bag itself is also approximately 308 seconds.

The trajectory was generated from `/mavros/global_position/global` with orientation from `/mavros/imu/data`. It is appropriate for pipeline validation and approximate trajectory comparison, but it is not independent survey-grade RTK/INS truth.

Keep `--gps off` for fair scoring against this GT. Enabling GPS fusion while evaluating against a GPS-derived reference creates reference leakage.

## Perturbation timing

The original perturbation YAML files used absolute UrbanNav timestamps from 2021. E2O-specific `per_0` through `per_6` files were generated under:

```text
wrappers/localization_benchmark/config/perturbations/e2o/
```

Their event windows are shifted to the E2O GT clock. These are valid integration-test windows, but road-semantic labels remain approximate because the supplied integration archive did not include geofenced route annotations.

## File-by-file changes

### New top-level interfaces

- `build.sh` — builds one or all seven images; build no longer requires a dataset bag.
- `run.sh` — compatibility entry point for `run`.
- `inspect_bag.sh` — read-only E2O/UrbanNav preflight inside the ROS Docker image.
- `E2O_ADAPTATION.md` — this implementation report.

### Dataset registry and data

- `scripts/dataset_config.py` — exports dataset-specific paths, topics, frames, camera YAML, TF YAML, timing assumptions, perturbations, and road segments.
- `wrappers/localization_benchmark/config/datasets.yaml` — UrbanNav and E2O runtime contracts.
- `wrappers/localization_benchmark/config/datasets/e2o/e2o_sensor_calibration.yaml` — preserved supplied calibration.
- `.../front_camera_info.yaml` — ROS CameraInfo source.
- `.../static_transforms.yaml` — corrected ROS-direction TFs and explicit identity assumptions.
- `.../road_segments.yaml` — approximate E2O time ranges.
- `.../assumptions.yaml` — known/missing calibration inventory.
- `data/e2o/ground_truth/one_full_loop_gt.tum` — supplied E2O reference.
- `data/e2o/raw/.gitkeep` and `data/e2o/README.md` — bag placement contract.

### Shared adapter and evaluation layer

- `urbannav_custom_bridge.py` — retained historical filename but rewritten as a generic parameterized dataset bridge.
- `custom_bridge.launch` — source topics are launch arguments.
- `custom_fastlio_adapter.py` and launch — configurable frames, CameraInfo YAML, time field/unit normalization, mono alias, and optional Livox CustomMsg output.
- `dataset_tf_broadcaster.py` — publishes calibration from YAML rather than hard-coded UrbanNav transforms.
- `ground_truth_path_node.py` — auto-detects UrbanNav INS or TUM.
- `evaluate_run.py` — TUM support and `none`, `se2`, or `sim2` alignment.
- `trajectory_analysis.py` — TUM-compatible offline analysis.
- `offline_rviz_paths.py`, `plot.sh`, and `container_visualise.sh` — dataset-aware E2O/UrbanNav replay and trajectory visualization.
- `algorithms.yaml` and `algorithm_config.py` — per-dataset overrides for all seven integrations.
- `container_run_per.sh`, `container_run_summary.sh`, `run_algorithm_container.sh` — dataset-specific mounts, topics, frames, results, and evaluator alignment.
- `container_build_check.sh`, `build_fastlio2.sh` — dataset-independent build checks.

### Algorithm wrapper configuration

- `velodyne_e2o.yaml` — FAST-LIO2.
- `lvisam_e2o.yaml` and parameterized LVI launch.
- `fast_livo2_e2o.yaml` and parameterized FAST-LIVO2 launch path.
- `front_camera_e2o_orbslam3.yaml`, parameterized ORB launch, and YAML-driven body extrinsic.
- `r3live_e2o.yaml` and parameterized fallback config.
- RTAB-Map and Adaptive-W full-pipeline launches now accept the selected FAST-LIO config.

## Validation performed without the 30.79 GB bag

The supplied ZIP did not contain `one_full_loop.bag`, so full sensor playback and algorithm convergence could not be executed. The following static and numerical checks were completed:

- all shell scripts pass `bash -n`;
- all 49 project Python entry points compile;
- all 29 ROS launch files parse as XML;
- 37 standard YAML files parse successfully;
- all seven E2O algorithm registry entries expand to valid launch/config arguments;
- E2O GT parses to 30,852 samples;
- exact-trajectory evaluation returns zero RMSE;
- synthetic monocular trajectory recovers scale and pose under Sim(2) with near-zero RMSE;
- supplied rotation matrices are orthonormal with determinant approximately 1.

The final remaining validation step is real bag preflight and playback on the target laptop.
