# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3058**
- Robustness score, lower is better: **37.4419**
- Overall position RMSE: **29.2564 m**
- Overall max position error: **58.6154 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217132` → `1723528521.445432`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0828 m, x=0.2788 m, y=0.1625 m, z=1.0336 m, yaw=0.7508 deg, dominant=z, samples=1072 | pos=1.0828 m, x=0.2788 m, y=0.1625 m, z=1.0336 m, yaw=0.7508 deg, dominant=z, samples=1072 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2306 m, x=0.0198 m, y=0.0657 m, z=0.2202 m, yaw=0.4818 deg, dominant=yaw, samples=74 | pos=0.7708 m, x=0.2520 m, y=0.2009 m, z=0.7002 m, yaw=0.4176 deg, dominant=z, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3697 m, x=0.2463 m, y=0.2699 m, z=0.0566 m, yaw=1.3823 deg, dominant=yaw, samples=58 | pos=1.0072 m, x=0.1236 m, y=0.3156 m, z=0.9484 m, yaw=2.7433 deg, dominant=yaw, samples=58 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6700 m, x=0.6363 m, y=0.1092 m, z=0.1790 m, yaw=0.4286 deg, dominant=x, samples=128 | pos=1.0510 m, x=0.6325 m, y=0.1467 m, z=0.8264 m, yaw=0.3099 deg, dominant=z, samples=128 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.1808 m, x=0.0330 m, y=0.0700 m, z=0.1635 m, yaw=0.1531 deg, dominant=z, yaw, samples=102 | pos=0.5097 m, x=0.1083 m, y=0.1800 m, z=0.4644 m, yaw=0.3792 deg, dominant=z, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1993 m, x=0.1289 m, y=0.0410 m, z=0.1464 m, yaw=0.1796 deg, dominant=yaw, samples=72 | pos=0.4040 m, x=0.2449 m, y=0.2195 m, z=0.2347 m, yaw=0.2090 deg, dominant=x, z, samples=72 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2452 m, x=0.1863 m, y=0.0414 m, z=0.1539 m, yaw=0.4910 deg, dominant=yaw, samples=48 | pos=0.3390 m, x=0.2922 m, y=0.1272 m, z=0.1156 m, yaw=0.9016 deg, dominant=yaw, samples=48 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8491 m, x=0.0521 m, y=0.0668 m, z=0.8449 m, yaw=0.3852 deg, dominant=z, samples=208 | pos=1.0730 m, x=0.1046 m, y=0.1368 m, z=1.0591 m, yaw=0.2412 deg, dominant=z, samples=208 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.4156 m, x=0.0309 m, y=0.1008 m, z=0.4020 m, yaw=0.1262 deg, dominant=z, samples=102 | pos=2.1029 m, x=0.1857 m, y=0.1369 m, z=2.0902 m, yaw=0.1355 deg, dominant=z, samples=102 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9141 m, x=0.6970 m, y=0.5707 m, z=0.1551 m, yaw=4.7358 deg, dominant=yaw, samples=176 | pos=2.6412 m, x=0.6014 m, y=0.6182 m, z=2.4964 m, yaw=4.6593 deg, dominant=yaw, samples=176 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2513 m, x=0.2345 m, y=0.0767 m, z=0.0476 m, yaw=1.2886 deg, dominant=yaw, samples=18 | pos=2.7876 m, x=0.4932 m, y=1.4854 m, z=2.3067 m, yaw=9.2363 deg, dominant=yaw, samples=18 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5125 m, x=1.7647 m, y=4.0801 m, z=0.7754 m, yaw=9.7112 deg, dominant=yaw, samples=202 | pos=6.0706 m, x=2.0368 m, y=5.4543 m, z=1.7188 m, yaw=3.7855 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8350 m, x=2.7068 m, y=0.8298 m, z=0.1485 m, yaw=20.3098 deg, dominant=yaw, samples=52 | pos=10.3128 m, x=6.7097 m, y=7.7877 m, z=0.8267 m, yaw=27.7863 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8626 m, x=7.0265 m, y=3.4515 m, z=0.7321 m, yaw=24.4869 deg, dominant=yaw, samples=160 | pos=16.5233 m, x=16.1496 m, y=3.4749 m, z=0.3657 m, yaw=16.1947 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8626 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | yaw_gyro_bias | imu/bias | 1621218780.000000 → 1621218785.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 2 | forward_accel_bias | imu/bias | 1621218800.000000 → 1621218805.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
