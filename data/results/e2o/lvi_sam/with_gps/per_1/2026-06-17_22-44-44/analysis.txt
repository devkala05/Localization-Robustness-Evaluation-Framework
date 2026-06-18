# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **1529**
- Robustness score, lower is better: **37.4237**
- Overall position RMSE: **29.3034 m**
- Overall max position error: **58.6064 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217105` → `1723528521.443912`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0626 m, x=0.2774 m, y=0.1634 m, z=1.0127 m, yaw=0.7468 deg, dominant=z, samples=536 | pos=1.0626 m, x=0.2774 m, y=0.1634 m, z=1.0127 m, yaw=0.7468 deg, dominant=z, samples=536 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2307 m, x=0.0198 m, y=0.0669 m, z=0.2199 m, yaw=0.4811 deg, dominant=yaw, samples=37 | pos=0.7688 m, x=0.2519 m, y=0.1989 m, z=0.6986 m, yaw=0.4148 deg, dominant=z, samples=37 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3703 m, x=0.2454 m, y=0.2715 m, z=0.0569 m, yaw=1.3790 deg, dominant=yaw, samples=29 | pos=1.0045 m, x=0.1245 m, y=0.3129 m, z=0.9464 m, yaw=2.7408 deg, dominant=yaw, samples=29 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6650 m, x=0.6326 m, y=0.1089 m, z=0.1739 m, yaw=0.4360 deg, dominant=x, samples=64 | pos=1.0496 m, x=0.6293 m, y=0.1453 m, z=0.8273 m, yaw=0.3102 deg, dominant=z, samples=64 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.2412 m, x=0.0307 m, y=0.0697 m, z=0.2289 m, yaw=0.1506 deg, dominant=z, samples=54 | pos=0.5006 m, x=0.1033 m, y=0.1789 m, z=0.4560 m, yaw=0.3949 deg, dominant=z, samples=54 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1863 m, x=0.1379 m, y=0.0387 m, z=0.1191 m, yaw=0.1775 deg, dominant=yaw, samples=33 | pos=0.4064 m, x=0.2469 m, y=0.2221 m, z=0.2343 m, yaw=0.2104 deg, dominant=x, z, samples=33 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2450 m, x=0.1850 m, y=0.0432 m, z=0.1548 m, yaw=0.4882 deg, dominant=yaw, samples=24 | pos=0.3368 m, x=0.2892 m, y=0.1355 m, z=0.1068 m, yaw=0.8950 deg, dominant=yaw, samples=24 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8450 m, x=0.0527 m, y=0.0660 m, z=0.8407 m, yaw=0.3917 deg, dominant=z, samples=104 | pos=1.0603 m, x=0.1067 m, y=0.1444 m, z=1.0450 m, yaw=0.2464 deg, dominant=z, samples=104 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.7430 m, x=0.0308 m, y=0.1167 m, z=0.7331 m, yaw=0.1294 deg, dominant=z, samples=51 | pos=2.0242 m, x=0.1927 m, y=0.1426 m, z=2.0100 m, yaw=0.1398 deg, dominant=z, samples=51 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9068 m, x=0.6938 m, y=0.5642 m, z=0.1506 m, yaw=4.7108 deg, dominant=yaw, samples=88 | pos=2.6092 m, x=0.5938 m, y=0.6139 m, z=2.4654 m, yaw=4.6252 deg, dominant=yaw, samples=88 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2513 m, x=0.2356 m, y=0.0741 m, z=0.0465 m, yaw=1.2890 deg, dominant=yaw, samples=9 | pos=2.7549 m, x=0.4825 m, y=1.4778 m, z=2.2743 m, yaw=9.2149 deg, dominant=yaw, samples=9 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.4334 m, x=1.6943 m, y=3.9961 m, z=0.9030 m, yaw=9.8464 deg, dominant=yaw, samples=101 | pos=5.9689 m, x=1.9617 m, y=5.3666 m, z=1.7260 m, yaw=3.8963 deg, dominant=y, samples=101 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8397 m, x=2.7138 m, y=0.8226 m, z=0.1495 m, yaw=20.3269 deg, dominant=yaw, samples=26 | pos=10.3290 m, x=6.7216 m, y=7.7907 m, z=0.9010 m, yaw=27.8112 deg, dominant=yaw, samples=26 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8609 m, x=7.0229 m, y=3.4448 m, z=0.7788 m, yaw=24.4951 deg, dominant=yaw, samples=80 | pos=16.5250 m, x=16.1513 m, y=3.4716 m, z=0.3977 m, yaw=16.1970 deg, dominant=yaw, x, samples=80 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8609 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | lidar_point_dropout_turn | lidar/point_dropout | 1621218790.000000 → 1621218795.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 2 | lidar_rain_noise | lidar/rain | 1621218805.000000 → 1621218810.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


## Generated files

- **trajectory CSV:** `trajectory.csv`
- **error over time CSV:** `error_timeseries.csv`
- **segment metrics CSV:** `segment_metrics.csv`
- **perturbation window metrics CSV:** `perturbation_window_metrics.csv`
- **segment per-window error CSV directory:** `segment_error_timeseries`
- **trajectory XY plot:** `trajectory_xy.png`
- **error over time plot:** `error_over_time.png`
- **yaw error over time plot:** `yaw_error_over_time.png`
- **segment position RMSE bar graph:** `segment_position_rmse_bar.png`
- **segment component RMSE bar graph:** `segment_component_rmse_bar.png`
- **machine-readable metrics JSON:** `metrics.json`
