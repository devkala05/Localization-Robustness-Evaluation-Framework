# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3058**
- Robustness score, lower is better: **37.4369**
- Overall position RMSE: **29.2518 m**
- Overall max position error: **58.6046 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217077` → `1723528521.442227`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.1122 m, x=0.2795 m, y=0.1627 m, z=1.0641 m, yaw=0.7494 deg, dominant=z, samples=1072 | pos=1.1122 m, x=0.2795 m, y=0.1627 m, z=1.0641 m, yaw=0.7494 deg, dominant=z, samples=1072 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2305 m, x=0.0196 m, y=0.0660 m, z=0.2200 m, yaw=0.4836 deg, dominant=yaw, samples=74 | pos=0.7685 m, x=0.2520 m, y=0.1984 m, z=0.6984 m, yaw=0.4175 deg, dominant=z, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3712 m, x=0.2465 m, y=0.2717 m, z=0.0561 m, yaw=1.3824 deg, dominant=yaw, samples=58 | pos=1.0028 m, x=0.1244 m, y=0.3113 m, z=0.9451 m, yaw=2.7382 deg, dominant=yaw, samples=58 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6683 m, x=0.6347 m, y=0.1096 m, z=0.1782 m, yaw=0.4315 deg, dominant=x, samples=128 | pos=1.0490 m, x=0.6313 m, y=0.1440 m, z=0.8253 m, yaw=0.3098 deg, dominant=z, samples=128 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.1811 m, x=0.0334 m, y=0.0709 m, z=0.1633 m, yaw=0.1544 deg, dominant=z, yaw, samples=102 | pos=0.5090 m, x=0.1072 m, y=0.1799 m, z=0.4639 m, yaw=0.3837 deg, dominant=z, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1994 m, x=0.1297 m, y=0.0408 m, z=0.1458 m, yaw=0.1809 deg, dominant=yaw, samples=72 | pos=0.4047 m, x=0.2450 m, y=0.2206 m, z=0.2347 m, yaw=0.2062 deg, dominant=x, z, y, samples=72 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2473 m, x=0.1867 m, y=0.0424 m, z=0.1566 m, yaw=0.4907 deg, dominant=yaw, samples=48 | pos=0.3405 m, x=0.2920 m, y=0.1300 m, z=0.1174 m, yaw=0.8980 deg, dominant=yaw, samples=48 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8627 m, x=0.0543 m, y=0.0622 m, z=0.8587 m, yaw=0.3948 deg, dominant=z, samples=208 | pos=1.1050 m, x=0.1095 m, y=0.1434 m, z=1.0902 m, yaw=0.2465 deg, dominant=z, samples=208 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.4406 m, x=0.0346 m, y=0.1050 m, z=0.4265 m, yaw=0.1292 deg, dominant=z, samples=102 | pos=2.1773 m, x=0.1947 m, y=0.1511 m, z=2.1633 m, yaw=0.1415 deg, dominant=z, samples=102 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.8971 m, x=0.6839 m, y=0.5511 m, z=0.1827 m, yaw=4.6948 deg, dominant=yaw, samples=176 | pos=2.7334 m, x=0.5861 m, y=0.6086 m, z=2.5996 m, yaw=4.6124 deg, dominant=yaw, samples=176 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2537 m, x=0.2424 m, y=0.0631 m, z=0.0399 m, yaw=1.2691 deg, dominant=yaw, samples=18 | pos=2.7990 m, x=0.4549 m, y=1.4872 m, z=2.3271 m, yaw=9.2283 deg, dominant=yaw, samples=18 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5433 m, x=1.7639 m, y=4.0841 m, z=0.9220 m, yaw=9.7438 deg, dominant=yaw, samples=202 | pos=6.0332 m, x=2.0077 m, y=5.4509 m, z=1.6301 m, yaw=3.7982 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8482 m, x=2.7255 m, y=0.8169 m, z=0.1302 m, yaw=20.3379 deg, dominant=yaw, samples=52 | pos=10.2984 m, x=6.6922 m, y=7.8034 m, z=0.6159 m, yaw=27.8085 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8670 m, x=7.0414 m, y=3.4542 m, z=0.6144 m, yaw=24.4795 deg, dominant=yaw, samples=160 | pos=16.5203 m, x=16.1460 m, y=3.4850 m, z=0.2870 m, yaw=16.2128 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8670 m and dominant component(s): yaw.

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
